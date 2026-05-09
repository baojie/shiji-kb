#!/usr/bin/env python3
"""修复真实内容错填页面：id/label/heading 设为文件名，保留引文部分（通常是正确的）。

修复逻辑：
1. 读取 frontmatter 和正文
2. 将 id、label 设为文件名（去 .md）
3. 将正文中的 `# {旧实体}` 标题改为 `# {新实体}`
4. 修正 description 行（去掉错填实体的标注信息）
5. 保留引文部分（通常已正确标注文件名实体）
6. 保留其他所有结构

用法：
  python3 scripts/fix_real_mismatches.py --dry-run   # 预览
  python3 scripts/fix_real_mismatches.py --execute   # 执行
  python3 scripts/fix_real_mismatches.py --auto-stub-only  # 只处理自动生成的stub
"""
import os, re, sys, json

PAGES_DIR = 'docs/wiki/pages'

def load_mismatches():
    with open('/tmp/real_mismatches_report.json') as f:
        return json.load(f)

def is_auto_stub(content):
    """Check if file is an auto-generated stub (minimal content, wrong entity)."""
    # Auto stubs have "出现于《史记》**N** 处" pattern
    return '出现于《史记》' in content

def fix_page(fp, new_id):
    """Fix frontmatter id, label, and heading to match filename."""
    with open(fp, encoding='utf-8') as f:
        content = f.read()

    old_id_m = re.search(r'^id:\s*(.+)', content, re.MULTILINE)
    if not old_id_m:
        return False, 'NO_ID'
    old_id = old_id_m.group(1).strip()

    # 1. Fix id:
    content = re.sub(r'^id:\s*.+$', f'id: {new_id}', content, count=1, flags=re.MULTILINE)

    # 2. Fix label:
    content = re.sub(r'^label:\s*.+$', f'label: {new_id}', content, count=1, flags=re.MULTILINE)

    # 3. Fix canonical_name if present:
    content = re.sub(r'^canonical_name:\s*.+$', f'canonical_name: {new_id}', content, count=1, flags=re.MULTILINE)

    # 4. Fix # heading (main title):
    # Find the first # heading after frontmatter (---)
    fm_end = content.find('---', 3)  # second ---
    if fm_end > 0:
        body = content[fm_end+3:]
        heading_match = re.match(r'\s*#\s+(.+)', body)
        if heading_match:
            old_heading = heading_match.group(1).strip()
            if old_heading != new_id:
                # Replace just the first # heading
                body = re.sub(r'^#\s+.*', f'# {new_id}', body, count=1)
                content = content[:fm_end+3] + body

    # 5. Fix description if it contains wrong entity info
    desc_m = re.search(r'^description:\s*(.+)', content, re.MULTILINE)
    if desc_m:
        old_desc = desc_m.group(1).strip()
        # If description has "〖@wrong_entity〗", update it
        # Generate a generic description
        new_desc = f'{new_id}，《史记》中记载的历史人物/事件。'
        content = re.sub(r'^description:\s*.+$', f'description: {new_desc}', content, count=1, flags=re.MULTILINE)

    # 6. Fix tags if they don't match (e.g., [帝王] for a wrong 帝X entity)
    tag_m = re.search(r'^tags:\s*\[(.+)\]', content, re.MULTILINE)
    if tag_m and new_id.startswith('帝'):
        # Keep [帝王] for 帝X
        pass

    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)

    return True, 'FIXED'

def main():
    dry_run = '--dry-run' in sys.argv
    execute = '--execute' in sys.argv
    auto_stub_only = '--auto-stub-only' in sys.argv

    if not dry_run and not execute:
        print('请指定 --dry-run (预览) 或 --execute (执行)')
        return

    items = load_mismatches()
    total = len(items)

    auto_stubs = []
    substantive = []

    for item in items:
        fp = os.path.join(PAGES_DIR, item['filename'])
        if not os.path.exists(fp):
            continue
        content = open(fp, encoding='utf-8').read()
        if is_auto_stub(content):
            auto_stubs.append(item)
        else:
            substantive.append(item)

    print(f'全部真实错填: {total}')
    print(f'  自动stub(需完全修复): {len(auto_stubs)}')
    print(f'  有内容页面(可能只需修frontmatter): {len(substantive)}')
    print()

    if auto_stub_only:
        items = auto_stubs
        print('仅处理 auto stub 页面')

    if dry_run:
        print('=== DRY RUN — 预览 ===')
        for item in items[:10]:
            fp = os.path.join(PAGES_DIR, item['filename'])
            content = open(fp, encoding='utf-8').read()
            id_m = re.search(r'^id:\s*(.+)', content, re.MULTILINE)
            heading_m = re.search(r'^#\s+(.+)', content, re.MULTILINE)

            old_id = id_m.group(1).strip() if id_m else '?'
            old_heading = heading_m.group(1).strip() if heading_m else '?'
            new_id = item['filename'][:-3]

            print(f'  {item["filename"]}')
            print(f'    id: {old_id} → {new_id}')
            print(f'    heading: {old_heading} → {new_id}')

        if len(items) > 10:
            print(f'    ... 还有 {len(items) - 10} 个')

        print(f'\n=== 有内容页面 ===')
        for item in substantive[:5]:
            fp = os.path.join(PAGES_DIR, item['filename'])
            content = open(fp, encoding='utf-8').read()
            id_m = re.search(r'^id:\s*(.+)', content, re.MULTILINE)
            old_id = id_m.group(1).strip() if id_m else '?'
            new_id = item['filename'][:-3]
            print(f'  {item["filename"]}  id: {old_id} → {new_id}')
        return

    if execute:
        fixed = 0
        skipped = 0
        errors = 0

        for item in items:
            if auto_stub_only and item not in auto_stubs:
                continue

            fp = os.path.join(PAGES_DIR, item['filename'])
            if not os.path.exists(fp):
                skipped += 1
                continue

            new_id = item['filename'][:-3]
            success, status = fix_page(fp, new_id)

            if success:
                fixed += 1
            else:
                errors += 1

            if fixed % 100 == 0:
                print(f'  已修复 {fixed} 个...')

        print(f'\n完成: 修复 {fixed}, 跳过 {skipped}, 错误 {errors}')

if __name__ == '__main__':
    main()
