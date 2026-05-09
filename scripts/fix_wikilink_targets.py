#!/usr/bin/env python3
"""批量修复 wiki 页面中断链：将 [[错误名称]] 替换为 [[正确文件名]]。

映射来自 pages.json registry 中的 id/label ↔ 实际文件名的对应关系。

用法：
  python3 scripts/fix_wikilink_targets.py --dry-run    # 预览
  python3 scripts/fix_wikilink_targets.py              # 执行
"""
import os, re, json, sys

PAGES_DIR = 'docs/wiki/pages'

def load_registry():
    with open('docs/wiki/pages.json') as f:
        data = json.load(f)
    return data.get('pages', {})

def build_mapping():
    """Build mapping: known names (id, label) -> correct filename stem."""
    mapping = {}
    for fname in os.listdir(PAGES_DIR):
        if not fname.endswith('.md'):
            continue
        stem = fname[:-3]
        content = open(f'{PAGES_DIR}/{fname}', encoding='utf-8').read()
        id_m = re.search(r'^id:\s*(.+)', content, re.MULTILINE)
        label_m = re.search(r'^label:\s*(.+)', content, re.MULTILINE)
        if id_m:
            pid = id_m.group(1).strip().strip('"\'')
            mapping[pid] = stem
        if label_m:
            pl = label_m.group(1).strip().strip('"\'')
            mapping[pl] = stem
        # Also map stem without number prefix
        m = re.match(r'^\d{3}_(.+)$', stem)
        if m and m.group(1) not in mapping:
            mapping[m.group(1)] = stem
    return mapping

def collect_broken_links(mapping):
    """Find all broken links and check if they're fixable."""
    existing = {f.replace('.md', '') for f in os.listdir(PAGES_DIR) if f.endswith('.md')}
    fixable = {}  # bad target -> correct stem
    sources = {}  # file -> [(old_link, new_link), ...]

    for fname in sorted(os.listdir(PAGES_DIR)):
        if not fname.endswith('.md'):
            continue
        fp = f'{PAGES_DIR}/{fname}'
        content = open(fp, encoding='utf-8').read()
        links = re.findall(r'\[\[([^\[\]]+?)(?:\|([^\[\]]*))?\]\]', content)
        for l, d in links:
            target = l.strip()
            if target in existing:
                continue
            if target in mapping:
                correct = mapping[target]
                if correct in existing:
                    if target not in fixable:
                        fixable[target] = correct
                    sources.setdefault(fname, []).append((target, correct))
    return fixable, sources

def fix_file(fp, fix_map, dry_run=False):
    """Fix all known broken links in a file."""
    with open(fp, encoding='utf-8') as f:
        content = f.read()

    changes = []
    def replace_link(m):
        full = m.group(0)
        target_raw = m.group(1)
        target = target_raw.strip()
        if target in fix_map:
            correct = fix_map[target]
            new_link = full.replace(f'[[{target_raw}', f'[[{correct}', 1)
            changes.append((target, correct))
            return new_link
        return full

    new_content = re.sub(r'\[\[([^\[\]]+?)(?:\|([^\[\]]*))?\]\]', replace_link, content)

    if not changes:
        return 0

    if dry_run:
        return len(changes)

    with open(fp, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return len(changes)

def main():
    dry_run = '--dry-run' in sys.argv

    print('建立名称→文件名映射...')
    mapping = build_mapping()
    print(f'  映射条目: {len(mapping)}')

    print('扫描断链...')
    fixable, sources = collect_broken_links(mapping)
    print(f'  可修复断链类型: {len(fixable)}')

    total_instances = sum(len(v) for v in sources.values())
    print(f'  可修复断链总次数: {total_instances}')
    print(f'  涉及文件数: {len(sources)}')

    if dry_run:
        print('\n=== 预览（前30条）===')
        count = 0
        for fname, changes in sorted(sources.items()):
            for old, new in changes:
                if count >= 30:
                    break
                print(f'  {fname}: [[{old}]] → [[{new}]]')
                count += 1
            if count >= 30:
                break
        if len(sources) > 30:
            print(f'  ... 还有 {len(sources)-30} 个文件的修改未显示')
        print(f'\n[Dry-run] 未执行修改')
        return

    # Execute
    total_fixed = 0
    fixed_files = 0
    for fname in sorted(sources.keys()):
        fp = f'{PAGES_DIR}/{fname}'
        n = fix_file(fp, fixable)
        if n > 0:
            total_fixed += n
            fixed_files += 1
            print(f'  {fname}: 修复 {n} 处')

    print(f'\n完成: 修复 {total_fixed} 处断链, 涉及 {fixed_files} 个文件')

if __name__ == '__main__':
    main()
