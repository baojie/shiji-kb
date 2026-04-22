#!/usr/bin/env python3
"""
Bot Lint Agent — Wiki 引文 PN 核验

扫描 wiki/public/pages/ 中的 NNN-MMM 格式 PN 引用，
用 find_pn_for_quote 逆向核验引文与 PN 的对应关系。
  置信度 >= AUTOFIX_THRESHOLD → 自动修正 + 记录 butler revision
  < AUTOFIX_THRESHOLD        → 写入 queue.md 待人工审查

所有编辑通过 wiki/scripts/butler/record_revision.py 留下 revision 记录
（author=bot-lint），同时追加到 logs/wiki_butler/actions.jsonl。

用法：
    python scripts/bot_lint_agent.py                 # 扫描所有 wiki 页面
    python scripts/bot_lint_agent.py --page 晁错     # 只检查单页
    python scripts/bot_lint_agent.py --dry-run       # 预览，不写任何文件
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from config import BASE_COPY, DATA_ROOT, PROJECT_ROOT

WIKI_PAGES_DIR = PROJECT_ROOT / 'wiki' / 'public' / 'pages'
ACTIONS_LOG    = PROJECT_ROOT / 'logs' / 'wiki_butler' / 'actions.jsonl'
QUEUE_FILE     = PROJECT_ROOT / 'logs' / 'wiki_butler' / 'queue.md'
RECORD_REV_PY  = PROJECT_ROOT / 'wiki' / 'scripts' / 'butler' / 'record_revision.py'

AUTOFIX_THRESHOLD = 0.95   # 低于此分数不自动修复，送 queue
BOT_AUTHOR = 'bot-lint'

# --- citation 正则 ---
# 匹配 NNN-MMM 或 NNN-MMM.K，可选 意旨 后缀，可包在 [[...]] 里
_CITE_INNER = r'(\d{3})-(\d{3}(?:\.\d+)?)'
_CITE_RE = re.compile(
    r'（(?:\[\[[^\]]*\|)?' + _CITE_INNER + r'(?:\]\])?(?:意旨)?）'
)

# 匹配 blockquote 行 + 行末引用：> quote text（NNN-MMM）
_BLOCKQUOTE_CITE_RE = re.compile(
    r'^>\s+(.*?)（(?:\[\[[^\]]*\|)?' + _CITE_INNER + r'(?:\]\])?(?:意旨)?）\s*$',
    re.MULTILINE,
)


# ─────────────────────────────────────────────
# 数据模型
# ─────────────────────────────────────────────

@dataclass
class CitationIssue:
    page: str           # wiki slug
    line_num: int
    old_cite: str       # 原始引用文字 "（101-013意旨）"
    chapter_num: str    # "101"
    pn: str             # "13"
    quote: str          # 前置引文（可能为空）
    issue_type: str     # "missing_pn" | "quote_mismatch"
    suggested_pn: str   # 建议替换的 PN（可能为空）
    confidence: float   # 0.0-1.0


@dataclass
class BotAction:
    ts: str
    agent: str
    action: str
    target: str
    issue: str
    old_text: str
    new_text: str
    confidence: float
    verdict: str        # "accept" | "queue" | "skip"
    dry_run: bool


# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def log_action(action: BotAction, dry_run: bool) -> None:
    if dry_run:
        return
    ACTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(ACTIONS_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(asdict(action), ensure_ascii=False) + '\n')


def record_revision(page: str, summary: str, dry_run: bool) -> bool:
    """调用 record_revision.py，返回是否成功。"""
    if dry_run:
        print(f'  [dry-run] record_revision {page}: {summary}')
        return True
    result = subprocess.run(
        [sys.executable, str(RECORD_REV_PY), page,
         '--summary', summary, '--author', BOT_AUTHOR],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f'  ✗ record_revision failed: {result.stderr.strip()}')
        return False
    return True


def pn_str_to_int(pn_str: str) -> str:
    """'013' → '13'，保留小数部分 '4.1' 不变。"""
    if '.' in pn_str:
        parts = pn_str.split('.')
        return '.'.join(str(int(p)) for p in parts)
    return str(int(pn_str))


# ─────────────────────────────────────────────
# Wiki 引文 PN 核验（可自动修复）
# ─────────────────────────────────────────────

def scan_page_citations(page_path: Path) -> list[CitationIssue]:
    """扫描单个 wiki 页面，提取所有引文+PN对，返回需要核验的条目列表。"""
    content = page_path.read_text(encoding='utf-8')
    page = page_path.stem
    issues: list[CitationIssue] = []

    for m in _BLOCKQUOTE_CITE_RE.finditer(content):
        quote_raw = m.group(1).strip()
        ch_num = m.group(2)      # "101"
        pn_raw = m.group(3)      # "018" or "4.1"
        pn = pn_str_to_int(pn_raw)

        line_num = content[:m.start()].count('\n') + 1
        old_cite = m.group(0)[m.group(0).index('（'):]

        issues.append(CitationIssue(
            page=page,
            line_num=line_num,
            old_cite=old_cite,
            chapter_num=ch_num,
            pn=pn,
            quote=quote_raw,
            issue_type='unverified',
            suggested_pn='',
            confidence=0.0,
        ))

    return issues


def verify_citations(
    issues: list[CitationIssue],
    pn_index: list,
) -> list[CitationIssue]:
    """用 find_pn 核验每条引文，填充 issue_type / suggested_pn / confidence。"""
    from find_pn_for_quote import find_pn as _find_pn

    # 按章节分组索引，提高效率
    ch_index: dict[str, list] = {}
    for entry in pn_index:
        ch_index.setdefault(entry['chapter_num'], []).append(entry)

    verified: list[CitationIssue] = []
    for issue in issues:
        ch_entries = ch_index.get(issue.chapter_num, [])

        # 检查 PN 是否存在
        pn_exists = any(e['pn'] == issue.pn for e in ch_entries)

        if not pn_exists:
            # PN 不存在 → 用引文文字找正确 PN
            results = _find_pn(issue.quote, ch_entries, top_n=1)
            if results:
                score, best = results[0]
                issue.issue_type = 'missing_pn'
                issue.suggested_pn = best['pn']
                issue.confidence = score
            else:
                issue.issue_type = 'missing_pn'
                issue.confidence = 0.0
            verified.append(issue)

        elif issue.quote:
            # PN 存在 → 用引文文字交叉验证
            pn_entry = next((e for e in ch_entries if e['pn'] == issue.pn), None)
            if pn_entry:
                from find_pn_for_quote import _clean
                q_clean = _clean(issue.quote)
                p_clean = pn_entry['text_clean']
                if q_clean and q_clean not in p_clean:
                    # 引文不在声称的 PN 里 → 可能 PN 写错
                    results = _find_pn(issue.quote, ch_entries, top_n=1)
                    if results:
                        score, best = results[0]
                        if best['pn'] != issue.pn:
                            issue.issue_type = 'quote_mismatch'
                            issue.suggested_pn = best['pn']
                            issue.confidence = score
                            verified.append(issue)

    return verified


def build_new_cite(old_cite: str, new_pn: str, chapter_num: str) -> str:
    """把 old_cite 里的 PN 替换成 new_pn，保留原格式（链接/意旨等）。"""
    # 从 old_cite 提取章节+旧PN，替换为新PN
    padded = f'{int(new_pn):03d}' if '.' not in new_pn else new_pn
    new_cite = re.sub(
        r'(\d{3})-(\d{3}(?:\.\d+)?)',
        lambda m: f'{m.group(1)}-{padded}',
        old_cite,
    )
    return new_cite


def apply_fix(page_path: Path, issue: CitationIssue, dry_run: bool) -> bool:
    """把 old_cite 替换成修正后的引用，写回文件。"""
    content = page_path.read_text(encoding='utf-8')
    new_cite = build_new_cite(issue.old_cite, issue.suggested_pn, issue.chapter_num)

    if issue.old_cite == new_cite:
        return False

    new_content = content.replace(issue.old_cite, new_cite, 1)
    if new_content == content:
        return False

    if dry_run:
        print(f'  [dry-run] {issue.page} L{issue.line_num}: {issue.old_cite} → {new_cite}')
        return True

    page_path.write_text(new_content, encoding='utf-8')
    return True


def append_to_queue(issues: list[CitationIssue], dry_run: bool) -> None:
    """把低置信度问题追加到 queue.md。"""
    if not issues:
        return
    lines = [f'\n### bot-lint 待审 ({now_iso()[:10]})\n']
    for iss in issues:
        lines.append(
            f'- [ ] `{iss.page}` L{iss.line_num} '
            f'{iss.old_cite} → PN {iss.suggested_pn or "?"} '
            f'(conf={iss.confidence:.2f}, {iss.issue_type})\n'
        )
    if dry_run:
        print(f'  [dry-run] queue.md +{len(issues)} 条待审')
        return
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_FILE, 'a', encoding='utf-8') as f:
        f.writelines(lines)
    print(f'  queue.md +{len(issues)} 条待审')


def run_citation_lint(page_filter: str | None, dry_run: bool) -> None:
    """扫描 wiki 页面引文，核验 PN，自动修复高置信度问题。"""
    from find_pn_for_quote import load_index as _load_index

    print('[bot-lint] 加载 PN 索引...', end=' ', flush=True)
    pn_index = _load_index()
    print(f'{len(pn_index)} 段落')

    if page_filter:
        pages = list(WIKI_PAGES_DIR.glob(f'{page_filter}.md'))
    else:
        pages = sorted(WIKI_PAGES_DIR.glob('*.md'))

    total_issues = 0
    auto_fixed = 0
    queued = 0

    for page_path in pages:
        raw_issues = scan_page_citations(page_path)
        if not raw_issues:
            continue

        verified = verify_citations(raw_issues, pn_index)
        if not verified:
            continue

        to_queue: list[CitationIssue] = []
        for issue in verified:
            total_issues += 1
            confidence = issue.confidence

            action = BotAction(
                ts=now_iso(), agent=BOT_AUTHOR,
                action=f'citation-{issue.issue_type}',
                target=f'wiki/public/pages/{issue.page}.md',
                issue=f'{issue.old_cite} (L{issue.line_num})',
                old_text=issue.old_cite,
                new_text=build_new_cite(issue.old_cite, issue.suggested_pn, issue.chapter_num)
                         if issue.suggested_pn else '',
                confidence=confidence,
                verdict='',
                dry_run=dry_run,
            )

            if confidence >= AUTOFIX_THRESHOLD and issue.suggested_pn:
                fixed = apply_fix(page_path, issue, dry_run)
                if fixed:
                    summary = (
                        f'bot-lint/citation-fix: '
                        f'{issue.page} {issue.old_cite}→{issue.suggested_pn} '
                        f'(conf={confidence:.2f})'
                    )
                    record_revision(issue.page, summary, dry_run)
                    action.verdict = 'accept'
                    auto_fixed += 1
                    print(
                        f'  ✓ {issue.page} L{issue.line_num}: '
                        f'{issue.old_cite} → {issue.suggested_pn} '
                        f'[{confidence:.2f}]'
                    )
                else:
                    action.verdict = 'skip'
            else:
                action.verdict = 'queue'
                to_queue.append(issue)
                queued += 1

            log_action(action, dry_run)

        append_to_queue(to_queue, dry_run)

    print(
        f'[bot-lint] 完成：{total_issues} 个问题，'
        f'{auto_fixed} 个自动修复，{queued} 个待审'
    )


# ─────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description='Bot Lint Agent — Wiki 引文 PN 核验')
    ap.add_argument('--dry-run', action='store_true', help='预览，不写入任何文件')
    ap.add_argument('--page', help='只检查指定 wiki 页面 slug')
    args = ap.parse_args()

    if args.dry_run:
        print('[bot-lint] DRY-RUN 模式，不会写入任何文件\n')

    run_citation_lint(page_filter=args.page, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
