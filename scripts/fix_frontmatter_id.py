#!/usr/bin/env python3
"""批量修复 frontmatter id 不匹配问题（非真实内容错填的页面）。

只修复三类：
1. QUOTE_ENCODING: 文件名和 id 只是引号编码不同（半角 vs 全角）
2. METHODOLOGY_RENAME: id 是过长的方法论描述名
3. OTHER_ID_DIVERGE: 其他 id 偏离但内容正确的情况

修复方法：将 id（和 label）设为文件名（去掉 .md）

用法：
  python3 scripts/fix_frontmatter_id.py --dry-run   # 预览
  python3 scripts/fix_frontmatter_id.py --execute   # 执行修复
"""
import os, re, sys

PAGES_DIR = 'docs/wiki/pages'

def normalize_quotes(s):
    s = s.replace('"', "'")  # normalize all quotes to single type for comparison
    s = s.replace('“', "'").replace('”', "'")
    s = s.replace('‘', "'").replace('’', "'")
    return s.strip("'\" \t")

def classify(stem, pid, label, desc):
    """Return fix_type if file should be auto-fixed, None if real mismatch."""
    stem_clean = stem.strip('"\'\\u201c\\u201d\\u2018\\u2019 ')
    pid_clean = pid.strip('"\'\\u201c\\u201d\\u2018\\u2019 ')
    label_clean = label.strip('"\'\\u201c\\u201d\\u2018\\u2019 ') if label else ''

    # Same after quote normalization
    if normalize_quotes(stem) == normalize_quotes(pid):
        return 'QUOTE_ENCODING'
    if label and normalize_quotes(stem) == normalize_quotes(label):
        return 'QUOTE_ENCODING'

    # Methodology rename: pid is long form containing stem
    pid_norm = normalize_quotes(pid)
    stem_norm = normalize_quotes(stem)
    if stem_norm in pid_norm and len(pid_norm) > len(stem_norm) * 1.3:
        return 'METHODOLOGY_RENAME'
    if pid_norm in stem_norm and len(stem_norm) > len(pid_norm) * 1.3:
        return 'METHODOLOGY_RENAME'

    # Description check: does desc mention stem but not pid?
    desc_text = desc if desc else ''
    stem_kw = stem_norm[:4]
    pid_kw = pid_norm[:4]

    if stem_kw and stem_kw in desc_text and (not pid_kw or pid_kw not in desc_text):
        return 'OTHER_ID_DIVERGE'

    return None  # Real mismatch, needs human review

def fix_file(fp, new_id):
    """Replace id and label in frontmatter with new_id."""
    with open(fp, encoding='utf-8') as f:
        content = f.read()

    # Replace id: line
    content = re.sub(
        r'^id:\s*.+$',
        f'id: {new_id}',
        content,
        count=1,
        flags=re.MULTILINE
    )

    # Replace label: line
    content = re.sub(
        r'^label:\s*.+$',
        f'label: {new_id}',
        content,
        count=1,
        flags=re.MULTILINE
    )

    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    dry_run = '--dry-run' in sys.argv
    execute = '--execute' in sys.argv

    if not dry_run and not execute:
        print('请指定 --dry-run (预览) 或 --execute (执行)')
        return

    to_fix = []  # (filename, stem, current_id, fix_type)
    real_mismatches = []

    for fname in sorted(os.listdir(PAGES_DIR)):
        if not fname.endswith('.md'):
            continue
        fp = os.path.join(PAGES_DIR, fname)
        if not os.path.isfile(fp):
            continue
        try:
            content = open(fp, encoding='utf-8').read()
        except:
            continue

        id_m = re.search(r'^id:\s*(.+)', content, re.MULTILINE)
        if not id_m:
            continue
        pid = id_m.group(1).strip()
        stem = fname[:-3]
        if stem == pid:
            continue

        label_m = re.search(r'^label:\s*(.+)', content, re.MULTILINE)
        flabel = label_m.group(1).strip() if label_m else ''

        desc_m = re.search(r'^description:\s*(.+)', content, re.MULTILINE)
        fdesc = desc_m.group(1).strip() if desc_m else ''

        fix_type = classify(stem, pid, flabel, fdesc)
        if fix_type:
            to_fix.append((fname, stem, pid, fix_type))
        else:
            real_mismatches.append((fname, stem, pid, flabel))

    # Report
    print(f'可自动修复: {len(to_fix)}')
    print(f'真实内容错填(需手动处理): {len(real_mismatches)}')
    print()

    # Show samples
    for fix_type in ['QUOTE_ENCODING', 'METHODOLOGY_RENAME', 'OTHER_ID_DIVERGE']:
        items = [i for i in to_fix if i[3] == fix_type]
        print(f'--- {fix_type}: {len(items)}个 ---')
        for fname, stem, pid, _ in items[:5]:
            print(f'  {fname}')
            print(f'    id: {pid[:60]} → {stem}')
        if len(items) > 5:
            print(f'    ... 还有 {len(items) - 5} 个')
        print()

    if dry_run:
        print('=== DRY RUN — 未执行修改 ===')
        return

    if not execute:
        return

    # Execute fixes
    fixed = 0
    errors = 0
    for fname, stem, pid, fix_type in to_fix:
        fp = os.path.join(PAGES_DIR, fname)
        try:
            fix_file(fp, stem)
            fixed += 1
            if fixed % 500 == 0:
                print(f'  已修复 {fixed} 个...')
        except Exception as e:
            print(f'  ERROR: {fname}: {e}')
            errors += 1

    print(f'\n完成: 修复 {fixed}, 错误 {errors}')

    # Save real mismatches list
    if real_mismatches:
        import json
        report = [{'filename': f, 'stem': s, 'id': p, 'label': l}
                  for f, s, p, l in real_mismatches]
        with open('/tmp/real_mismatches_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f'真实错填列表已保存到 /tmp/real_mismatches_report.json')
        print(f'共 {len(real_mismatches)} 个文件需手动审核')

if __name__ == '__main__':
    main()
