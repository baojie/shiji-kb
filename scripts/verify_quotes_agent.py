#!/usr/bin/env python3
"""
verify_quotes_agent.py — W6b 增量引文真实性核验

三层流水线（per quote）：
  L0: 缓存命中 → 跳过（节省重复 token）
  L1: find_pn 规则匹配 → score ≥ 0.90 直接通过
  L2: LLM (Claude Haiku) → 仅处理 L1 uncertain/fabricated 且有 cited PN 的案例

每次运行处理一个页面（butler 原子性），写 citation_issues.jsonl + 更新缓存。

用法：
  python3 scripts/verify_quotes_agent.py                 # 检查下一个未扫描页
  python3 scripts/verify_quotes_agent.py --page 郑当时   # 检查指定页
  python3 scripts/verify_quotes_agent.py --status        # 显示覆盖进度
  python3 scripts/verify_quotes_agent.py --fix           # 检查 + 自动修复高置信度问题
  python3 scripts/verify_quotes_agent.py --llm-off       # 禁用 LLM，只跑规则层
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from config import PROJECT_ROOT, DATA_ROOT, LOGS_ROOT
from find_pn_for_quote import load_index, find_pn

WIKI_PAGES_DIR  = PROJECT_ROOT / "wiki" / "public" / "pages"
ISSUES_LOG      = LOGS_ROOT / "wiki_butler" / "citation_issues.jsonl"
CACHE_FILE      = LOGS_ROOT / "wiki_butler" / "quote_cache.json"
STATE_FILE      = LOGS_ROOT / "wiki_butler" / "verify_state.json"
RECORD_REV_PY   = PROJECT_ROOT / "wiki" / "scripts" / "butler" / "record_revision.py"
ORIGINAL_DIR    = PROJECT_ROOT / "docs" / "original_text"

# --- 阈值 ---
L1_OK          = 0.90   # rule 直接通过
L1_UNCERTAIN   = 0.55   # rule 不确定下限，触发 LLM
MIN_LEN        = 8      # 引文最短字数
MAX_LLM_PER_RUN = 8     # 每次运行最多 LLM 调用数（控制成本）


# ─────────────────────────────────────────────
# 缓存 / 状态
# ─────────────────────────────────────────────

def _hash(text: str) -> str:
    """规范化后取 sha256[:16] 作缓存键。"""
    normalized = re.sub(r"[^一-鿿㐀-䶿\w]", "", text)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def load_cache() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"checked": [], "cursor": 0}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


# ─────────────────────────────────────────────
# 引文提取（带 cited PN）
# ─────────────────────────────────────────────

# 匹配页面内 (NNN-MMM) 或 (NNN-MMM意旨) 形式
_PN_IN_LINE = re.compile(r"（(\d{3})-(\d{3,4}(?:\.\d+)?)(?:意旨)?）")
# 去 markdown 标记
_MD_CLEAN = re.compile(r"\*+|_{1,2}|\[\[[^\]|]+(?:\|([^\]]+))?\]\]")


def _strip_md(text: str) -> str:
    def repl(m):
        # wikilink [[A|B]] → B；[[A]] → A；** __ → 空
        inner = m.group(1)
        if inner is not None:
            return inner
        raw = m.group(0)
        if raw.startswith("[["):
            return raw[2:].rstrip("]")
        return ""  # 去掉 * / _
    return _MD_CLEAN.sub(repl, text).strip()


def extract_quotes(md_text: str) -> list[dict]:
    """
    提取引文及其 cited PN。
    返回 [{raw, line_no, quote_type, cited_ch, cited_pn}]
    cited_ch/cited_pn 为 None 表示没有明确标注。
    """
    quotes: list[dict] = []
    lines = md_text.split("\n")

    # 1. blockquote 块（连续 > 行合并）
    buf: list[str] = []
    buf_start = 0
    buf_pn: tuple[str, str] | None = None

    def flush_bq(buf, start, pn_info):
        merged = " ".join(buf).strip()
        merged = _strip_md(merged)
        # 只验证含引号的直接引语
        if re.search(r'[""]', merged) and len(merged) >= MIN_LEN:
            ch, pn = pn_info if pn_info else (None, None)
            quotes.append({
                "raw": merged, "line_no": start, "quote_type": "blockquote",
                "cited_ch": ch, "cited_pn": pn,
            })

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(">"):
            content = stripped[1:].strip()
            m_pn = _PN_IN_LINE.search(content)
            if m_pn:
                if buf_pn is None:
                    buf_pn = (m_pn.group(1), m_pn.group(2))
                content = content[:m_pn.start()].strip()
            content = re.sub(r"\*+", "", content).strip()
            if content:
                if not buf:
                    buf_start = i + 1
                buf.append(content)
        else:
            if buf:
                flush_bq(buf, buf_start, buf_pn)
                buf, buf_pn = [], None

    if buf:
        flush_bq(buf, buf_start, buf_pn)

    # 2. 行内全角引号
    inline_re = re.compile(r'[""]([^""]{%d,})[""]' % MIN_LEN)
    for i, line in enumerate(lines):
        if line.startswith("---") or line.startswith("#"):
            continue
        m_pn = _PN_IN_LINE.search(line)
        ch = m_pn.group(1) if m_pn else None
        pn = m_pn.group(2) if m_pn else None
        for m in inline_re.finditer(line):
            txt = _strip_md(m.group(1))
            if len(txt) >= MIN_LEN:
                quotes.append({
                    "raw": txt, "line_no": i + 1, "quote_type": "inline_quote",
                    "cited_ch": ch, "cited_pn": pn,
                })
    return quotes


# ─────────────────────────────────────────────
# L1: 规则层
# ─────────────────────────────────────────────

def l1_check(quote: str, index: list) -> tuple[float, dict | None]:
    """
    返回 (best_score, best_entry)。
    best_entry 为 None 表示完全未命中。
    """
    results = find_pn(quote, index, top_n=3)
    if not results:
        return 0.0, None
    score, entry = results[0]
    return score, entry


def get_para_by_pn(chapter_num: str, pn_str: str, index: list) -> str | None:
    """在 PN 索引中按章号+段号查找原文段落。"""
    ch = chapter_num.lstrip("0") or "0"
    # pn_str 可能是 "011" → 需要尝试 "11", "11.0" 等形式
    pn_int = pn_str.lstrip("0") or "0"
    for entry in index:
        if entry["chapter_num"] != chapter_num:
            continue
        ep = entry["pn"]
        ep_int = ep.split(".")[0].lstrip("0") or "0"
        if ep_int == pn_int or ep == pn_str or ep == pn_int:
            return entry["text_raw"]
    return None


# ─────────────────────────────────────────────
# L2: LLM 层
# ─────────────────────────────────────────────

def _call_llm(prompt: str) -> str | None:
    """调用 Claude Haiku，返回 response text 或 None（失败）。"""
    try:
        import anthropic
    except ImportError:
        print("  [W6b] anthropic SDK 未安装，跳过 LLM 层", file=sys.stderr)
        return None

    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as e:
        print(f"  [W6b] LLM 调用失败: {e}", file=sys.stderr)
        return None


def l2_check(quote: str, original_para: str) -> dict:
    """
    让 LLM 判断引文是否准确引自原文段落。
    返回 {verdict, correct_quote, confidence, reason}。
    """
    prompt = (
        "你是《史记》文本核验专家。请判断wiki页面引文是否准确引自《史记》原文。\n\n"
        f"【引文】\n{quote}\n\n"
        f"【原文段落】\n{original_para}\n\n"
        "判断标准：\n"
        "- exact: 与原文完全匹配或省略后仍准确\n"
        "- paraphrase: 是原文释义，非直接引用\n"
        "- fabricated: 原文段落中找不到此内容\n"
        "- uncertain: 无法确定\n\n"
        "仅返回JSON，不要其他文字：\n"
        '{"verdict":"exact|paraphrase|fabricated|uncertain",'
        '"correct_quote":"（如需修正，填入原文正确引法，≤60字；无需修正则空字符串）",'
        '"confidence":0到100的整数}'
    )
    raw = _call_llm(prompt)
    if not raw:
        return {"verdict": "uncertain", "correct_quote": "", "confidence": 0}
    try:
        # 提取 JSON（防止 LLM 包裹额外文字）
        m = re.search(r"\{[^{}]+\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception:
        pass
    return {"verdict": "uncertain", "correct_quote": "", "confidence": 0}


# ─────────────────────────────────────────────
# 主验证逻辑
# ─────────────────────────────────────────────

def verify_page(
    page_path: Path,
    index: list,
    cache: dict,
    use_llm: bool = True,
) -> list[dict]:
    """
    验证单个页面，返回新 issues 列表（已在缓存中的跳过）。
    同时更新 cache（in-place）。
    """
    md_text = page_path.read_text(encoding="utf-8")
    page_id = page_path.stem
    quotes = extract_quotes(md_text)
    issues: list[dict] = []
    llm_calls = 0

    for q in quotes:
        raw = q["raw"]
        if len(raw) < MIN_LEN:
            continue

        key = _hash(raw)

        # L0: 缓存命中
        if key in cache:
            cached = cache[key]
            if cached["status"] in ("ok", "llm_ok"):
                print(f"  [L0-SKIP] {raw[:40]}…")
                continue
            # fabricated 缓存也跳过（避免重复写 issue）
            if cached["status"] in ("fabricated", "llm_fail"):
                print(f"  [L0-KNOWN-FAIL] {raw[:40]}…")
                continue

        # L1: 规则匹配
        score, best_entry = l1_check(raw, index)

        if score >= L1_OK:
            cache[key] = {
                "status": "ok", "method": "rule", "confidence": round(score, 3),
                "found_pn": f"{best_entry['chapter_num']}-{best_entry['pn']}",
                "checked_at": now_iso(),
            }
            print(f"  [L1-OK {score:.2f}] {raw[:40]}…")
            continue

        # 是否有 cited PN（wiki 页面中标注的出处）
        cited_ch = q.get("cited_ch")
        cited_pn = q.get("cited_pn")

        # L2: LLM（仅限有 cited PN 且有原文段落可供比对的案例）
        llm_result = None
        if use_llm and llm_calls < MAX_LLM_PER_RUN and cited_ch and cited_pn:
            original_para = get_para_by_pn(cited_ch, cited_pn, index)
            if original_para:
                llm_calls += 1
                print(f"  [L2-LLM] {raw[:40]}… (cited {cited_ch}-{cited_pn})")
                llm_result = l2_check(raw, original_para)

        # 决策
        if llm_result:
            verdict = llm_result.get("verdict", "uncertain")
            conf = llm_result.get("confidence", 0)
            correct = llm_result.get("correct_quote", "")

            if verdict == "exact" and conf >= 70:
                cache[key] = {
                    "status": "llm_ok", "method": "llm", "confidence": conf / 100,
                    "checked_at": now_iso(),
                }
                print(f"    → LLM: exact ({conf}%)")
                continue

            if verdict in ("fabricated", "paraphrase") and conf >= 60:
                status = "llm_fail"
                issue_type = "FABRICATED_QUOTE" if verdict == "fabricated" else "PARAPHRASE_QUOTE"
                cache[key] = {
                    "status": status, "method": "llm", "confidence": conf / 100,
                    "suggestion": correct, "checked_at": now_iso(),
                }
                issues.append({
                    "ts": now_iso(), "page": page_id,
                    "issue_type": issue_type, "severity": "critical",
                    "content": raw, "line_no": q["line_no"],
                    "quote_type": q["quote_type"],
                    "cited_pn": f"{cited_ch}-{cited_pn}" if cited_ch else None,
                    "suggestion": correct or None,
                    "grep_result": "not_found", "action": "delete_and_replace",
                    "status": "open",
                })
                print(f"    → LLM: {verdict} ({conf}%) → issue logged")
                continue

            # LLM uncertain → 记为 warning
            issues.append({
                "ts": now_iso(), "page": page_id,
                "issue_type": "UNVERIFIED_QUOTE", "severity": "warning",
                "content": raw, "line_no": q["line_no"],
                "quote_type": q["quote_type"],
                "cited_pn": f"{cited_ch}-{cited_pn}" if cited_ch else None,
                "grep_result": "uncertain", "action": "human_review",
                "status": "open",
            })
            print(f"    → LLM: uncertain → human_review")

        else:
            # 纯规则未命中（且无 LLM 结果）
            if score < L1_UNCERTAIN:
                cache[key] = {
                    "status": "fabricated", "method": "rule", "confidence": round(score, 3),
                    "checked_at": now_iso(),
                }
                issues.append({
                    "ts": now_iso(), "page": page_id,
                    "issue_type": "FABRICATED_QUOTE", "severity": "critical",
                    "content": raw, "line_no": q["line_no"],
                    "quote_type": q["quote_type"],
                    "cited_pn": f"{cited_ch}-{cited_pn}" if cited_ch else None,
                    "grep_result": "not_found", "action": "delete_and_replace",
                    "status": "open",
                })
                print(f"  [L1-FAIL {score:.2f}] {raw[:40]}… → FABRICATED")
            else:
                # L1 uncertain，但没有 LLM 可用（llm_off 或超限）
                issues.append({
                    "ts": now_iso(), "page": page_id,
                    "issue_type": "UNVERIFIED_QUOTE", "severity": "warning",
                    "content": raw, "line_no": q["line_no"],
                    "quote_type": q["quote_type"],
                    "cited_pn": f"{cited_ch}-{cited_pn}" if cited_ch else None,
                    "grep_result": f"partial_{score:.2f}", "action": "human_review",
                    "status": "open",
                })
                print(f"  [L1-UNCERTAIN {score:.2f}] {raw[:40]}… → needs LLM")

    return issues


# ─────────────────────────────────────────────
# 自动修复
# ─────────────────────────────────────────────

def auto_fix(page_path: Path, issues: list[dict], cache: dict) -> int:
    """
    修复两类问题：
    1. FABRICATED_QUOTE + LLM 提供了 suggestion → 替换为正确引文
    2. FABRICATED_QUOTE + 无 suggestion → 注释掉 + featured 降级
    """
    if not issues:
        return 0

    md_text = page_path.read_text(encoding="utf-8")
    lines = md_text.split("\n")
    fixed = 0

    # 按行号降序，避免修改后行号偏移
    critical = [i for i in issues if i["severity"] == "critical"]
    critical.sort(key=lambda x: x["line_no"], reverse=True)

    for iss in critical:
        idx = iss["line_no"] - 1
        if not (0 <= idx < len(lines)):
            continue

        suggestion = iss.get("suggestion") or ""
        if suggestion and len(suggestion) >= MIN_LEN:
            # 有 LLM 修正建议 → 替换引文内容
            orig_line = lines[idx]
            # 找到引号内容，替换为建议内容
            new_line = re.sub(
                r'[""][^""]{%d,}[""]' % MIN_LEN,
                f'"{suggestion}"',
                orig_line,
                count=1,
            )
            if new_line != orig_line:
                lines[idx] = new_line
                fixed += 1
                print(f"  ✏️  [fix-replace] 行{iss['line_no']}: {orig_line.strip()[:50]}…")
        else:
            # 无建议 → 注释掉
            lines[idx] = f"<!-- [W6b质检删除] 原文无法溯源: {lines[idx].strip()[:60]} -->"
            fixed += 1
            print(f"  🗑️  [fix-comment] 行{iss['line_no']} 已注释")

    if fixed:
        result = "\n".join(lines)
        result = re.sub(r"^featured:\s*true", "featured: false  # W6b降级", result, flags=re.MULTILINE)
        page_path.write_text(result, encoding="utf-8")

        # 写修订记录
        slug = page_path.stem
        summary = f"W6b/verify-quotes: 修复 {fixed} 处引文问题，页面降级 featured→false"
        try:
            subprocess.run(
                [sys.executable, str(RECORD_REV_PY), slug, "--summary", summary, "--author", "bot-verify"],
                check=True, capture_output=True, text=True, cwd=PROJECT_ROOT,
            )
            print(f"  📝 修订记录已写入")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  record_revision 失败: {e.stderr.strip()[:100]}", file=sys.stderr)

    return fixed


# ─────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────

def next_unchecked_page(state: dict) -> Path | None:
    """按字母序找下一个 state["checked"] 中没有的页面。"""
    all_pages = sorted(WIKI_PAGES_DIR.glob("*.md"))
    checked = set(state.get("checked", []))
    for p in all_pages:
        if p.stem not in checked:
            return p
    return None


def show_status(state: dict, cache: dict) -> None:
    all_pages = list(WIKI_PAGES_DIR.glob("*.md"))
    checked = state.get("checked", [])
    ok = sum(1 for v in cache.values() if v["status"] in ("ok", "llm_ok"))
    fail = sum(1 for v in cache.values() if v["status"] in ("fabricated", "llm_fail"))
    print(f"页面进度: {len(checked)}/{len(all_pages)} 已检查")
    print(f"引文缓存: {len(cache)} 条 ({ok} ok, {fail} fail)")
    issues_count = sum(1 for _ in open(ISSUES_LOG) if "open" in _) if ISSUES_LOG.exists() else 0
    print(f"待处理 issues: {issues_count} 条 (status=open)")


def append_issues(issues: list[dict]) -> None:
    if not issues:
        return
    ISSUES_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ISSUES_LOG.open("a", encoding="utf-8") as f:
        for iss in issues:
            f.write(json.dumps(iss, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="W6b 增量引文真实性核验")
    parser.add_argument("--page", help="检查指定页面（slug，不含 .md）")
    parser.add_argument("--status", action="store_true", help="显示覆盖进度")
    parser.add_argument("--fix", action="store_true", help="检查后自动修复高置信度问题")
    parser.add_argument("--llm-off", action="store_true", help="禁用 LLM 层，只跑规则")
    parser.add_argument("--reset-cache", action="store_true", help="清空缓存重建")
    args = parser.parse_args()

    cache = {} if args.reset_cache else load_cache()
    state = load_state()

    if args.status:
        show_status(state, cache)
        return

    # 确定要检查的页面
    if args.page:
        page_path = WIKI_PAGES_DIR / f"{args.page}.md"
        if not page_path.exists():
            print(f"❌ 页面不存在: {page_path}", file=sys.stderr)
            sys.exit(1)
    else:
        page_path = next_unchecked_page(state)
        if not page_path:
            print("✅ 所有页面已检查完毕")
            show_status(state, cache)
            return

    print(f"🔍 检查页面: {page_path.stem}")
    print("⏳ 加载 PN 索引…")
    index = load_index()
    print(f"  索引: {len(index)} 段落\n")

    issues = verify_page(page_path, index, cache, use_llm=not args.llm_off)

    if args.fix and issues:
        print(f"\n🔧 自动修复 {len(issues)} 个问题…")
        auto_fix(page_path, issues, cache)

    append_issues(issues)
    save_cache(cache)

    # 更新状态（记录已检查页面）
    slug = page_path.stem
    if slug not in state.get("checked", []):
        state.setdefault("checked", []).append(slug)
    save_state(state)

    # 汇总
    critical = [i for i in issues if i["severity"] == "critical"]
    print(f"\n📊 {page_path.stem}: {len(issues)} issues ({len(critical)} critical)")
    if critical:
        print("  Critical:")
        for iss in critical:
            print(f"    [{iss['line_no']}] {iss['issue_type']}: {iss['content'][:50]}…")
    if issues:
        print(f"  → 写入 {ISSUES_LOG.relative_to(PROJECT_ROOT)}")
    else:
        print("  ✅ 通过")


if __name__ == "__main__":
    main()
