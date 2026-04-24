#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 chapter_md/*.tagged.md 提取各小节标题的首段 PN，保存到 data/section_pn_index.json。

输出格式:
{
  "007_项羽本纪": {
    "项羽早年": "1",       // ## L2 标题 → 首段 PN
    "项氏家世": "1",       // ### L3 标题 → 首段 PN
    "少年项籍": "3",
    ...
  },
  ...
}
"""

import re
import json
from pathlib import Path


ENTITY_RE = re.compile(r'〖[@=;%&\'^~•!#\+\$\?\{\:\[\_]([^〖〗\n]+?)〗')
SKIP_TITLES = {'太史公曰', '赞', '论', '索隐', '集解', '正义'}


def clean_title(text: str) -> str:
    return ENTITY_RE.sub(r'\1', text).strip()


def extract(md_file: Path) -> dict[str, str]:
    """返回 {title: first_pn} 映射（L2 和 L3 各自的首段 PN）。"""
    lines = md_file.read_text(encoding='utf-8').split('\n')
    result: dict[str, str] = {}
    # pending: list of titles waiting for their first PN
    pending: list[str] = []

    for line in lines:
        line = line.rstrip()

        # PN 行: [N] 或 [N.N] 等
        pn_m = re.match(r'^\[(\d+(?:\.\d+)*)\]', line)
        if pn_m and pending:
            pn = pn_m.group(1)
            for title in pending:
                if title not in result:
                    result[title] = pn
            pending.clear()
            continue

        # ## L2 标题 (不带编号)
        m2 = re.match(r'^## (.+)$', line)
        if m2:
            title = clean_title(m2.group(1))
            if title and title not in SKIP_TITLES and len(title) >= 2:
                pending = [title]  # 新 L2 节，清空旧 pending
            continue

        # ## [N] 标题 (自带编号)
        m2n = re.match(r'^## \[(\d+)\] (.+)$', line)
        if m2n:
            title = clean_title(m2n.group(2))
            pn = m2n.group(1)
            if title and len(title) >= 2:
                result[title] = pn
            pending = []
            continue

        # ### L3 标题
        m3 = re.match(r'^### (.+)$', line)
        if m3:
            title = clean_title(m3.group(1))
            if title and title not in SKIP_TITLES and len(title) >= 2:
                # 追加到 pending（L3 在当前 L2 节内等待同一个 PN）
                pending.append(title)
            continue

    return result


def main():
    root = Path(__file__).parent.parent
    chapter_dir = root / 'chapter_md'
    out_path = root / 'data' / 'section_pn_index.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)

    tagged_files = sorted(chapter_dir.glob('*.tagged.md'))
    print(f'找到 {len(tagged_files)} 个章节文件')

    index: dict[str, dict[str, str]] = {}
    for f in tagged_files:
        chapter_id = f.stem.replace('.tagged', '')
        mapping = extract(f)
        if mapping:
            index[chapter_id] = mapping

    out_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    total = sum(len(v) for v in index.values())
    print(f'共 {len(index)} 章 / {total} 条小节 PN → {out_path}')


if __name__ == '__main__':
    main()
