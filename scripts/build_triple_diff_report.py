#!/usr/bin/env python3
"""
Phase 2：把 data/translation_alignment/NNN.json 转成可读的三栏对照 Markdown 报告。

输出：
  reports/translation_diff/NNN_章节名.md

每个 PN 一段，格式：
  ## [PN]

  **原文**：...
  **本库**：...
  **hunterhug**（conf=x.xx）：...
  **白话史记**（proportional）：...

用法：
  python scripts/build_triple_diff_report.py               # 全库
  python scripts/build_triple_diff_report.py 002 007       # 指定章节
"""

import json
import sys
from pathlib import Path

ALIGN_DIR = Path('data/translation_alignment')
OUTPUT_DIR = Path('reports/translation_diff')


def format_chapter(data: dict) -> str:
    lines = [
        f"# {data['chapter']} {data['title']} — 三栏白话对照",
        '',
        f"- **PN 数**：{data['n_pns']}",
        f"- **hunterhug 段数**：{data['hunterhug_paragraphs']}",
        f"- **白话史记 句数**：{data['baihua_sentences']}",
        '',
        '> **说明**：',
        '> - `原文` 为 `chapter_md` 去除实体标注后的文言正文',
        '> - `本库` 为 `labs/translation` 去除实体标注后的译文',
        '> - `hunterhug` 为 `corpus/shiji/段译/` 对应段；一段可能覆盖多 PN（则多 PN 共享）',
        '> - `白话史记` 为 `corpus/shiji/白话史记.txt` 按章内比例估算的对应区段（粗粒度）',
        '',
        '---',
        '',
    ]
    for r in data['records']:
        lines.append(f"## [{r['pn']}]")
        lines.append('')
        lines.append(f"**原文**：{r['source']}")
        lines.append('')
        lines.append(f"**本库**：{r['ours']}")
        lines.append('')
        hh_conf = r['hunterhug_conf']
        if r['hunterhug']:
            lines.append(f"**hunterhug**（conf={hh_conf}）：{r['hunterhug']}")
        else:
            lines.append(f"**hunterhug**（未匹配）")
        lines.append('')
        if r['baihua']:
            lines.append(f"**白话史记**（{r['baihua_conf']}）：{r['baihua']}")
        else:
            lines.append(f"**白话史记**（未匹配）")
        lines.append('')
        lines.append('---')
        lines.append('')
    return '\n'.join(lines)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    args = sys.argv[1:]
    files = sorted(ALIGN_DIR.glob('*.json'))
    if args:
        wanted = {a.zfill(3) for a in args}
        files = [f for f in files if f.stem in wanted]
    for f in files:
        data = json.load(open(f))
        ch = data['chapter']
        title = data['title']
        out = OUTPUT_DIR / f'{ch}_{title}.md'
        out.write_text(format_chapter(data))
    print(f'生成 {len(files)} 份报告 → {OUTPUT_DIR}')


if __name__ == '__main__':
    main()
