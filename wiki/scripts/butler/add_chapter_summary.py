#!/usr/bin/env python3
"""
add_chapter_summary.py — 为130个章节wiki页面添加/更新"章节综述"

来源优先级:
  1. 太史公自序 中的章节自述（最权威）
  2. 各轮反思报告中的内容描述（补充）
  3. 分节标题来自 chapter_md/*.tagged.md

用法:
    python3 wiki/scripts/butler/add_chapter_summary.py [--dry] [章节编号...]
"""

import os, re, sys, glob, subprocess, json
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
TAGGED_DIR = BASE / 'chapter_md'
WIKI_DIR = BASE / 'wiki/public/pages'
R3_DIR = BASE / 'doc/entities/第三轮按章实体反思'
R4_DIR = BASE / 'doc/entities/第四轮按章实体反思'
R5_DIR = BASE / 'doc/entities/第五轮按章实体反思'
RECORD_REV = BASE / 'wiki/scripts/butler/record_revision.py'
TAISHIGONG_JSON = BASE / 'wiki/data/taishigong_descs.json'

# ── 文本清洗 ──────────────────────────────────────────────────────────────────
TYPE_CHARS = r'[@&#;◆+!%~^_=?:•$\*\.\/\s]'

def strip_annot(text: str) -> str:
    def _entity(m):
        inner = m.group(1)
        return re.sub(r'^' + TYPE_CHARS + r'+', '', inner)
    text = re.sub(r'〖([^〗]+?)(?:\|[^〗]*)?\〗', _entity, text)
    text = re.sub(r'〘[※◈◆◉○●]*([^〙]*)\〙', r'\1', text)
    text = re.sub(r'⟦[◈◆◉○●]*([^⟧]*)\⟧', r'\1', text)
    text = re.sub(r'^\[[\d.]+\]\s*', '', text)
    text = re.sub(r'^[-*>\s]+', '', text)
    text = re.sub(r'\{[^}]+\}', '', text)
    text = re.sub(r':::.*', '', text)
    text = re.sub(r'\{', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ── 提取分节结构 ──────────────────────────────────────────────────────────────
def extract_sections(tagged_path: Path):
    sections = []
    cur_level = cur_title = None
    cur_lines: list[str] = []

    def flush():
        nonlocal cur_level, cur_title, cur_lines
        if not cur_title:
            return
        summary = ''
        for raw in cur_lines:
            s = strip_annot(raw.strip())
            if not s or len(s) < 3:
                continue
            if re.match(r'^[，。；！？\s·\[\]]+$', s):
                continue
            m = re.search(r'^(.{3,35}?)[，。；！？]', s)
            summary = (m.group(0) if m else s[:35]).strip()
            break
        sections.append((cur_level, cur_title, summary))
        cur_lines = []

    with open(tagged_path, encoding='utf-8') as f:
        for raw in f:
            line = raw.rstrip()
            if line.startswith('## ') and not re.match(r'^## \[', line):
                flush()
                cur_level, cur_title = '##', line[3:].strip()
            elif line.startswith('### '):
                flush()
                cur_level, cur_title = '###', line[4:].strip()
            elif cur_title:
                cur_lines.append(line)
    flush()
    return sections

# ── 加载太史公自序描述 ────────────────────────────────────────────────────────
def load_taishigong_descs() -> dict[str, str]:
    if TAISHIGONG_JSON.exists():
        return json.loads(TAISHIGONG_JSON.read_text(encoding='utf-8'))
    return {}

# ── 提取反思报告描述（补充） ──────────────────────────────────────────────────
ANNOT_WORDS = re.compile(
    r'反思|标注|修正|聚焦|轮次|处修|规律|漏标|消歧|格式|类型|补标|'
    r'lint|旧格式|数量|统计|典型案例|L\d+|`〖|脚注'
)

def extract_report_descs(num: str) -> list[str]:
    descs = []
    for fp in sorted(R3_DIR.glob(f'{num}_*.md')):
        text = fp.read_text(encoding='utf-8')
        m = re.search(r'\*\*章节特性\*\*[：:]\s*(.+)', text)
        if m:
            d = m.group(1).strip()
            if d and not ANNOT_WORDS.search(d):
                descs.append(d)
    for fp in sorted(R4_DIR.glob(f'{num}_*.md')):
        text = fp.read_text(encoding='utf-8')
        m = re.search(r'(本章为[^。\n]{5,80}类[^。\n]{0,40}[。])', text)
        if m:
            d = m.group(1).strip()
            if not ANNOT_WORDS.search(d):
                descs.append(d)
    seen, result = set(), []
    for d in descs:
        if d not in seen:
            seen.add(d)
            result.append(d)
    return result

# ── 生成综述 Markdown ──────────────────────────────────────────────────────────
def build_summary_section(sections, overview: list[str]) -> str:
    lines = ['', '## 章节综述', '']
    if overview:
        for d in overview:
            lines.append(d)
        lines.append('')
    lines.append('**章节结构**')
    lines.append('')
    for level, title, summary in sections:
        bullet = f'- **{title}**' if level == '##' else f'  - {title}'
        if summary:
            bullet += f'：{summary}'
        lines.append(bullet)
    lines.append('')
    return '\n'.join(lines)

# ── 主流程 ─────────────────────────────────────────────────────────────────────
def process_chapter(num: str, tsg_descs: dict, dry_run: bool = False) -> bool:
    wiki_files = sorted(WIKI_DIR.glob(f'{num}_*.md'))
    if not wiki_files:
        print(f'[{num}] ✗ 找不到wiki页面')
        return False
    wiki_file = wiki_files[0]
    slug = wiki_file.stem

    tagged_files = sorted(TAGGED_DIR.glob(f'{num}_*.tagged.md'))
    sections = extract_sections(tagged_files[0]) if tagged_files else []

    # 构建 overview：太史公自序 + 反思报告补充
    overview = []
    if num in tsg_descs and tsg_descs[num]:
        overview.append(tsg_descs[num])
    report_descs = extract_report_descs(num)
    for d in report_descs:
        if d not in overview:
            overview.append(d)

    if not sections and not overview:
        print(f'[{num}] ✗ 无内容可生成')
        return False

    summary_md = build_summary_section(sections, overview)

    current = wiki_file.read_text(encoding='utf-8')
    if '## 章节综述' in current:
        new_content = re.sub(
            r'\n## 章节综述\n.*?(?=\n## |\Z)',
            summary_md, current, flags=re.DOTALL
        )
    else:
        new_content = current.rstrip('\n') + '\n' + summary_md

    if new_content == current:
        print(f'[{num}] = 无变化')
        return False

    if dry_run:
        print(f'[{num}] DRY {slug}: {len(sections)}节 / overview={bool(overview)}')
        print(summary_md[:300])
        return True

    wiki_file.write_text(new_content, encoding='utf-8')
    result = subprocess.run(
        [sys.executable, str(RECORD_REV), slug,
         '--summary', f'butler/add-chapter-summary: 添加太史公自序综述（{len(sections)}节）',
         '--author', 'butler'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f'[{num}] ⚠ record_revision失败: {result.stderr.strip()}')
    else:
        print(f'[{num}] ✓ {slug} | {result.stdout.strip()}')
    return True

def main():
    args = sys.argv[1:]
    dry_run = '--dry' in args
    args = [a for a in args if not a.startswith('--')]

    tsg_descs = load_taishigong_descs()
    print(f'已加载太史公自序描述 {len(tsg_descs)} 章')

    if args:
        targets = args
    else:
        all_wiki = sorted(WIKI_DIR.glob('[0-9][0-9][0-9]_*.md'))
        targets = [p.stem[:3] for p in all_wiki]

    ok = skip = 0
    for num in targets:
        if process_chapter(num, tsg_descs, dry_run=dry_run):
            ok += 1
        else:
            skip += 1

    print(f'\n完成: {ok} 更新, {skip} 跳过')

if __name__ == '__main__':
    main()

