#!/usr/bin/env python3
"""
verify_quotes_agent.py — W7 增量引文真实性核验

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
    pn_int = pn_str.lstrip("0") or "0"
    for entry in index:
        if entry["chapter_num"] != chapter_num:
            continue
        ep = entry["pn"]
        ep_int = ep.split(".")[0].lstrip("0") or "0"
        if ep_int == pn_int or ep == pn_str or ep == pn_int:
            return entry["text_raw"]
    return None


def _pn_matches(found_pn: str, cited_ch: str, cited_pn: str) -> bool:
    """
    检查 find_pn 找到的 'NNN-PP' 是否与页面标注的 cited_ch/cited_pn 一致。
    只比较章号整数 + 段号整数部分（忽略小数细分和前导零）。
    """
    parts = found_pn.split("-", 1)
    if len(parts) != 2:
        return False
    found_ch, found_pp = parts
    if found_ch.lstrip("0") != cited_ch.lstrip("0"):
        return False
    found_pp_int = found_pp.split(".")[0].lstrip("0") or "0"
    cited_pn_int = cited_pn.split(".")[0].lstrip("0") or "0"
    return found_pp_int == cited_pn_int


# ─────────────────────────────────────────────
# L2: LLM 层
# ─────────────────────────────────────────────

def _call_llm(prompt: str, max_tokens: int = 512) -> str | None:
    """调用 Claude Haiku，返回 response text 或 None（失败）。"""
    try:
        import anthropic
    except ImportError:
        print("  [W7] anthropic SDK 未安装，跳过 LLM 层", file=sys.stderr)
        return None

    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as e:
        print(f"  [W7] LLM 调用失败: {e}", file=sys.stderr)
        return None


def get_wiki_context(md_lines: list[str], line_no: int, window: int = 4) -> str:
    """
    提取 wiki 页面中引文周围的解释文字（去掉引文行本身）。
    window: 引文前后各取多少行。
    """
    total = len(md_lines)
    idx = line_no - 1  # 0-indexed
    start = max(0, idx - window)
    end = min(total, idx + window + 1)
    context_lines = []
    for i in range(start, end):
        if i == idx:
            continue  # 跳过引文行本身
        line = md_lines[i].strip()
        # 跳过空行、frontmatter、标题
        if not line or line.startswith("---") or line.startswith("#"):
            continue
        # 跳过其他引文行（以 > 开头）
        if line.startswith(">"):
            continue
        context_lines.append(line)
    return "\n".join(context_lines)


def l2_repair(quote: str, original_para: str, wiki_context: str) -> dict:
    """
    两合一 LLM 调用：
    1. 从原文段落提取最贴切的替换引文（保持原文字面，不改写）
    2. 检查 wiki 解释文字是否与原文含义一致

    Returns:
        replacement: str      — 原文中最贴切引文（空 = 原文段落无关内容）
        context_ok: str       — "yes" | "partial" | "no"
        context_issue: str    — 解释文字存在的问题（若无则空）
        confidence: int       — 0-100
    """
    ctx_section = f"\n\n【wiki页面引文附近的解释文字】\n{wiki_context}" if wiki_context.strip() else ""
    prompt = (
        "你是《史记》文本核验专家。请完成以下两项任务。\n\n"
        f"【wiki页面引文】（已知与原文不完全一致）\n{quote}\n\n"
        f"【《史记》原文段落】\n{original_para}"
        f"{ctx_section}\n\n"
        "任务一：从原文段落中提取最贴切的直接引文（≤60字，必须是原文原字，不得改写）。\n"
        "  若原文段落与引文内容完全无关，replacement 填空字符串。\n\n"
        "任务二：检查 wiki 解释文字是否与原文段落含义一致（若无解释文字则填 yes）。\n"
        "  yes=准确 | partial=有细节偏差 | no=有误或夸大\n"
        "  若非 yes，context_issue 填问题描述（≤30字）。\n\n"
        "仅返回JSON，不要其他文字：\n"
        '{"replacement":"原文中最贴切引文或空字符串",'
        '"context_ok":"yes|partial|no",'
        '"context_issue":"问题描述或空字符串",'
        '"confidence":0到100的整数}'
    )
    raw_resp = _call_llm(prompt, max_tokens=512)
    default = {"replacement": "", "context_ok": "yes", "context_issue": "", "confidence": 0}
    if not raw_resp:
        return default
    try:
        m = re.search(r"\{[^{}]+\}", raw_resp, re.DOTALL)
        if m:
            result = json.loads(m.group())
            return {**default, **result}
    except Exception:
        pass
    return default


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
    md_lines = md_text.split("\n")
    page_id = page_path.stem
    quotes = extract_quotes(md_text)
    issues: list[dict] = []
    llm_calls = 0

    def _make_issue(issue_type, severity, action, q_info, extra=None):
        iss = {
            "ts": now_iso(), "page": page_id,
            "issue_type": issue_type, "severity": severity,
            "content": q_info["raw"], "line_no": q_info["line_no"],
            "quote_type": q_info["quote_type"],
            "action": action, "status": "open",
        }
        if extra:
            iss.update(extra)
        return iss

    for q in quotes:
        raw = q["raw"]
        if len(raw) < MIN_LEN:
            continue

        key = _hash(raw)
        cited_ch = q.get("cited_ch")
        cited_pn = q.get("cited_pn")

        # ── L0: 缓存（ok/llm_ok 仍需做 PN 比对，fabricated 直接跳过）──
        quote_exists = False
        found_pn: str | None = None

        if key in cache:
            cached = cache[key]
            if cached["status"] in ("fabricated", "llm_fail"):
                print(f"  [L0-KNOWN-FAIL] {raw[:40]}…")
                continue
            if cached["status"] in ("ok", "llm_ok"):
                quote_exists = True
                found_pn = cached.get("found_pn")
                print(f"  [L0-CACHE-OK] {raw[:40]}… → PN check")

        # ── L1: 规则匹配（仅在未缓存时运行）──
        score, best_entry = (0.0, None)
        if not quote_exists:
            score, best_entry = l1_check(raw, index)

            if score >= L1_OK:
                found_pn = f"{best_entry['chapter_num']}-{best_entry['pn']}"
                cache[key] = {
                    "status": "ok", "method": "rule", "confidence": round(score, 3),
                    "found_pn": found_pn, "checked_at": now_iso(),
                }
                quote_exists = True
                print(f"  [L1-OK {score:.2f}] {raw[:40]}…")

        # ── PN 比对（引文存在 + 有标注 PN）──
        if quote_exists and cited_ch and cited_pn and found_pn:
            if not _pn_matches(found_pn, cited_ch, cited_pn):
                issues.append(_make_issue("WRONG_PN", "warning", "fix_pn", q, {
                    "cited_pn": f"{cited_ch}-{cited_pn}",
                    "correct_pn": found_pn,
                    "grep_result": f"found_in_{found_pn}",
                }))
                print(f"  [PN-MISMATCH] cited {cited_ch}-{cited_pn} → actual {found_pn}")
            else:
                print(f"  [PN-OK] {cited_ch}-{cited_pn} ✓")

        if quote_exists:
            continue  # 引文存在，已处理 PN，无需 L2

        # ── 以下是引文未找到（score < L1_OK）的路径 ──

        can_llm = use_llm and llm_calls < MAX_LLM_PER_RUN

        # 情况 A：L1 近似命中（0.55 ≤ score < 0.90）→ near match，用该段落做修复
        if score >= L1_UNCERTAIN and best_entry is not None:
            original_para = best_entry["text_raw"]
            near_pn = f"{best_entry['chapter_num']}-{best_entry['pn']}"
            if can_llm:
                llm_calls += 1
                context = get_wiki_context(md_lines, q["line_no"])
                print(f"  [L2-NEAR {score:.2f}] {raw[:40]}… → repair+context")
                result = l2_repair(raw, original_para, context)
                replacement = result.get("replacement", "")
                ctx_ok = result.get("context_ok", "yes")
                ctx_issue = result.get("context_issue", "")
                conf = result.get("confidence", 0)

                if replacement and conf >= 60:
                    cache[key] = {
                        "status": "ok", "method": "llm_repair", "confidence": conf / 100,
                        "found_pn": near_pn, "checked_at": now_iso(),
                    }
                    iss = _make_issue("NEAR_MATCH", "warning", "replace_quote", q, {
                        "grep_result": f"near_{score:.2f}",
                        "replacement": replacement,
                        "correct_pn": near_pn,
                        "cited_pn": f"{cited_ch}-{cited_pn}" if cited_ch else None,
                    })
                    if ctx_ok != "yes" and ctx_issue:
                        iss["context_issue"] = ctx_issue
                        iss["context_ok"] = ctx_ok
                    issues.append(iss)
                    ctx_flag = f" [ctx:{ctx_ok}]" if ctx_ok != "yes" else ""
                    print(f"    → replacement found ({conf}%){ctx_flag}: {replacement[:40]}…")
                else:
                    # LLM 无法从近似段落提取合适引文 → 标为需人工审查
                    issues.append(_make_issue("UNVERIFIED_QUOTE", "warning", "human_review", q, {
                        "grep_result": f"near_{score:.2f}",
                        "cited_pn": f"{cited_ch}-{cited_pn}" if cited_ch else None,
                    }))
                    print(f"    → no replacement found → human_review")
            else:
                issues.append(_make_issue("UNVERIFIED_QUOTE", "warning", "human_review", q, {
                    "grep_result": f"near_{score:.2f}",
                    "cited_pn": f"{cited_ch}-{cited_pn}" if cited_ch else None,
                }))
                print(f"  [L1-NEAR {score:.2f}] {raw[:40]}… → needs LLM")
            continue

        # 情况 B：L1 完全未命中（score < 0.55）→ 用 cited PN 段落做修复尝试
        if can_llm and cited_ch and cited_pn:
            original_para = get_para_by_pn(cited_ch, cited_pn, index)
            if original_para:
                llm_calls += 1
                context = get_wiki_context(md_lines, q["line_no"])
                print(f"  [L2-CITED {cited_ch}-{cited_pn}] {raw[:40]}…")
                result = l2_repair(raw, original_para, context)
                replacement = result.get("replacement", "")
                ctx_ok = result.get("context_ok", "yes")
                ctx_issue = result.get("context_issue", "")
                conf = result.get("confidence", 0)

                if replacement and conf >= 60:
                    cache[key] = {
                        "status": "ok", "method": "llm_repair", "confidence": conf / 100,
                        "found_pn": f"{cited_ch}-{cited_pn}", "checked_at": now_iso(),
                    }
                    iss = _make_issue("NEAR_MATCH", "warning", "replace_quote", q, {
                        "grep_result": f"found_in_cited_pn",
                        "replacement": replacement,
                        "correct_pn": f"{cited_ch}-{cited_pn}",
                        "cited_pn": f"{cited_ch}-{cited_pn}",
                    })
                    if ctx_ok != "yes" and ctx_issue:
                        iss["context_issue"] = ctx_issue
                        iss["context_ok"] = ctx_ok
                    issues.append(iss)
                    ctx_flag = f" [ctx:{ctx_ok}]" if ctx_ok != "yes" else ""
                    print(f"    → replacement in cited PN ({conf}%){ctx_flag}: {replacement[:40]}…")
                else:
                    # 引文与 cited PN 段落内容无关 → 确认为伪造
                    cache[key] = {
                        "status": "llm_fail", "method": "llm", "confidence": conf / 100,
                        "checked_at": now_iso(),
                    }
                    issues.append(_make_issue("FABRICATED_QUOTE", "critical", "delete_and_replace", q, {
                        "grep_result": "not_found",
                        "cited_pn": f"{cited_ch}-{cited_pn}",
                        "context_issue": ctx_issue if ctx_ok != "yes" else None,
                    }))
                    print(f"    → FABRICATED (conf {conf}%)")
                continue

        # 情况 C：L1 未命中 + 无 LLM / 无 cited PN → 直接标为 FABRICATED
        cache[key] = {
            "status": "fabricated", "method": "rule", "confidence": round(score, 3),
            "checked_at": now_iso(),
        }
        issues.append(_make_issue("FABRICATED_QUOTE", "critical", "delete_and_replace", q, {
            "grep_result": "not_found",
            "cited_pn": f"{cited_ch}-{cited_pn}" if cited_ch else None,
        }))
        print(f"  [L1-FAIL {score:.2f}] {raw[:40]}… → FABRICATED")

    # 去重：同一页面内，content+issue_type 相同的只保留第一条
    seen: set[tuple] = set()
    deduped: list[dict] = []
    for iss in issues:
        key_dedup = (iss["issue_type"], iss["content"][:60])
        if key_dedup not in seen:
            seen.add(key_dedup)
            deduped.append(iss)
    return deduped


# ─────────────────────────────────────────────
# 自动修复
# ─────────────────────────────────────────────

def _replace_quote_in_line(line: str, replacement: str) -> str:
    """在单行中把全角引号内容替换为 replacement。"""
    return re.sub(r'[""][^""]{4,}[""]', f'"{replacement}"', line, count=1)


def _fix_pn_in_line(line: str, old_pn: str, new_pn: str) -> str:
    """把行中的 (old_ch-old_pn) 改为 (new_ch-new_pp)。"""
    old_ch, old_pp = old_pn.split("-", 1) if "-" in old_pn else (None, None)
    new_ch, new_pp = new_pn.split("-", 1) if "-" in new_pn else (None, None)
    if not (old_ch and new_ch):
        return line
    # 匹配 （old_ch-任意格式段号）
    pattern = rf"（{re.escape(old_ch)}-\d{{3,4}}(?:\.\d+)?(?:意旨)?）"
    replacement_pn = f"（{new_ch}-{int(new_pp):03d}）" if new_pp.isdigit() else f"（{new_pn}）"
    return re.sub(pattern, replacement_pn, line, count=1)


def auto_fix(page_path: Path, issues: list[dict], cache: dict) -> int:
    """
    修复三类问题（按行号降序处理，避免行号偏移）：
      NEAR_MATCH      → 用 replacement 替换引文文字，更新 PN；若 context_issue 存在则加注释
      WRONG_PN        → 仅更新 PN，不改引文
      FABRICATED_QUOTE → 有 suggestion 则替换，无则注释掉 + featured 降级
    """
    if not issues:
        return 0

    md_text = page_path.read_text(encoding="utf-8")
    lines = md_text.split("\n")
    fixed = 0
    need_downgrade = False

    # 只处理可自动修复的 issue，按行号降序
    fixable_types = {"NEAR_MATCH", "WRONG_PN", "FABRICATED_QUOTE"}
    to_fix = [i for i in issues if i["issue_type"] in fixable_types]
    to_fix.sort(key=lambda x: x["line_no"], reverse=True)

    for iss in to_fix:
        idx = iss["line_no"] - 1
        if not (0 <= idx < len(lines)):
            continue

        itype = iss["issue_type"]
        orig_line = lines[idx]

        if itype == "NEAR_MATCH":
            replacement = iss.get("replacement", "")
            correct_pn = iss.get("correct_pn", "")
            cited_pn = iss.get("cited_pn", "")
            new_line = orig_line
            if replacement:
                new_line = _replace_quote_in_line(new_line, replacement)
            if correct_pn and cited_pn and correct_pn != cited_pn:
                new_line = _fix_pn_in_line(new_line, cited_pn, correct_pn)
            if new_line != orig_line:
                lines[idx] = new_line
                fixed += 1
                print(f"  ✏️  [near-match→replace] 行{iss['line_no']}")
            # 上下文问题 → 在下一行插入注释提示
            ctx_issue = iss.get("context_issue", "")
            if ctx_issue:
                comment = f"<!-- [W7上下文警告] {ctx_issue} -->"
                lines.insert(idx + 1, comment)
                print(f"  ⚠️  [context-note] 行{iss['line_no']+1}: {ctx_issue}")

        elif itype == "WRONG_PN":
            correct_pn = iss.get("correct_pn", "")
            cited_pn = iss.get("cited_pn", "")
            if correct_pn and cited_pn:
                new_line = _fix_pn_in_line(orig_line, cited_pn, correct_pn)
                if new_line != orig_line:
                    lines[idx] = new_line
                    fixed += 1
                    print(f"  🔢 [fix-pn] 行{iss['line_no']}: {cited_pn} → {correct_pn}")

        elif itype == "FABRICATED_QUOTE":
            suggestion = iss.get("suggestion") or iss.get("replacement") or ""
            if suggestion and len(suggestion) >= MIN_LEN:
                new_line = _replace_quote_in_line(orig_line, suggestion)
                if new_line != orig_line:
                    lines[idx] = new_line
                    fixed += 1
                    print(f"  ✏️  [fabricated→replace] 行{iss['line_no']}")
            else:
                lines[idx] = f"<!-- [W7质检删除] 原文无法溯源: {orig_line.strip()[:60]} -->"
                fixed += 1
                need_downgrade = True
                print(f"  🗑️  [fix-comment] 行{iss['line_no']} 已注释")

    if fixed:
        result = "\n".join(lines)
        if need_downgrade:
            result = re.sub(r"^featured:\s*true", "featured: false  # W7降级",
                            result, flags=re.MULTILINE)
        page_path.write_text(result, encoding="utf-8")

        slug = page_path.stem
        summary = f"W7/verify-quotes: 修复 {fixed} 处引文问题"
        if need_downgrade:
            summary += "，页面降级 featured→false"
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
    parser = argparse.ArgumentParser(description="W7 增量引文真实性核验")
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
