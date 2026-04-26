#!/usr/bin/env python3
"""
check_citation_count.py
扫描所有 wiki 页面，检查"《史记》中出现 N 次"与实际引文摘录数量是否一致。
输出不一致的页面列表，可写入 housekeeping_queue.md。
"""
import re
import os
import sys
import json
import argparse
from pathlib import Path

PAGES_DIR = Path('wiki/public/pages')
QUEUE_FILE = Path('wiki/logs/butler/housekeeping_queue.md')

# 匹配"出现 N 次"的声明
RE_CLAIM = re.compile(r'《史记》中出现\s*\*\*(\d+)\*\*\s*次')
# 匹配每条引文摘录（> **出自 ...：** 开头的行）
RE_QUOTE = re.compile(r'^>\s*\*\*出自')


def check_page(path: Path):
    text = path.read_text(encoding='utf-8')
    m = RE_CLAIM.search(text)
    if not m:
        return None
    claimed = int(m.group(1))

    # 找 ## 史记引文 节
    cite_start = text.find('## 史记引文')
    if cite_start == -1:
        return None
    cite_section = text[cite_start:]

    # 数实际引文条数
    actual = sum(1 for line in cite_section.splitlines() if RE_QUOTE.match(line))

    if actual == claimed:
        return None

    slug = path.stem
    return {
        'slug': slug,
        'claimed': claimed,
        'actual': actual,
        'diff': claimed - actual,
    }


def write_queue_entries(issues):
    if not issues:
        return
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)

    new_items = []
    for iss in issues:
        sign = '+' if iss['diff'] > 0 else ''
        new_items.append(
            f"- [ ] H19 | [[{iss['slug']}]] | 引文数量不符：声称{iss['claimed']}次，"
            f"实有{iss['actual']}条（差{sign}{iss['diff']}）\n"
            f"  发现: 2026-04-26 check_citation_count.py"
        )

    if not QUEUE_FILE.exists():
        QUEUE_FILE.write_text('# Housekeeping 队列\n\n## P1（本周内处理）\n\n', encoding='utf-8')

    content = QUEUE_FILE.read_text(encoding='utf-8')
    # 追加到 P1 节
    insertion = '\n'.join(new_items) + '\n'
    if '## P1（本周内处理）' in content:
        content = content.replace('## P1（本周内处理）\n', '## P1（本周内处理）\n\n' + insertion)
    else:
        content += '\n## P1（本周内处理）\n\n' + insertion
    QUEUE_FILE.write_text(content, encoding='utf-8')
    print(f'✓ 已写入 {len(issues)} 条到 {QUEUE_FILE}')


def main():
    parser = argparse.ArgumentParser(description='检查引文数量与声称次数是否一致')
    parser.add_argument('--write-queue', action='store_true', help='将问题写入 housekeeping_queue.md')
    parser.add_argument('--max', type=int, default=0, help='最多报告 N 个问题（0=不限）')
    args = parser.parse_args()

    issues = []
    pages = sorted(PAGES_DIR.glob('*.md'))
    for p in pages:
        result = check_page(p)
        if result:
            issues.append(result)

    if not issues:
        print('✓ 所有页面引文数量一致，无问题')
        return

    # 按差值绝对值排序
    issues.sort(key=lambda x: abs(x['diff']), reverse=True)
    if args.max:
        issues = issues[:args.max]

    print(f'发现 {len(issues)} 个引文数量不一致的页面：\n')
    print(f'{"页面":20} {"声称":6} {"实有":6} {"差":6}')
    print('-' * 42)
    for iss in issues:
        sign = '+' if iss['diff'] > 0 else ''
        print(f"{iss['slug']:20} {iss['claimed']:6} {iss['actual']:6} {sign}{iss['diff']:5}")

    if args.write_queue:
        write_queue_entries(issues)


if __name__ == '__main__':
    main()
