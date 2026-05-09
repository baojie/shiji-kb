#!/usr/bin/env python3
"""审计页面内容错填：扫描所有页面，找到 filename != frontmatter id 的页面。
输出详细报告，含文件名、当前 ID、文件名推测的正确实体。

用法：
  python3 scripts/audit_content_mismatch.py              # 扫描全部
  python3 scripts/audit_content_mismatch.py --csv        # 输出 CSV 报告
  python3 scripts/audit_content_mismatch.py --restored   # 只扫描近期恢复的文件

指定近期恢复文件列表：
  --restored-list /tmp/deleted_pages_20260509.txt
"""
import os, re, sys, json

PAGES_DIR = 'docs/wiki/pages'

def load_registry():
    import json
    try:
        with open('docs/wiki/pages.json') as f:
            data = json.load(f)
        return data.get('pages', {})
    except:
        return {}

def get_restored_files():
    """Get list of files that were recently restored from git."""
    restored = set()
    for arg in sys.argv:
        if arg.startswith('--restored-list='):
            path = arg.split('=', 1)[1]
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        fname = os.path.basename(line)
                        restored.add(fname)
    return restored

def scan_all_pages():
    """Scan all pages for content mismatches."""
    registry = load_registry()
    restored_only = '--restored' in sys.argv
    restored_files = get_restored_files()

    mismatches = []
    errors = []
    ok_count = 0

    for fname in sorted(os.listdir(PAGES_DIR)):
        if not fname.endswith('.md'):
            continue

        # If --restored flag, only check restored files
        if restored_only and restored_files:
            if fname not in restored_files:
                continue

        fp = os.path.join(PAGES_DIR, fname)
        if not os.path.isfile(fp):
            continue

        try:
            content = open(fp, encoding='utf-8').read()
        except Exception as e:
            errors.append((fname, f'READ_ERROR: {e}'))
            continue

        # Parse frontmatter id
        id_m = re.search(r'^id:\s*(.+)', content, re.MULTILINE)
        if not id_m:
            errors.append((fname, 'NO_ID'))
            continue

        fid = id_m.group(1).strip().strip('"\'')

        # Parse frontmatter label (for display)
        label_m = re.search(r'^label:\s*(.+)', content, re.MULTILINE)
        flabel = label_m.group(1).strip().strip('"\'') if label_m else ''

        # Parse description
        desc_m = re.search(r'^description:\s*(.+)', content, re.MULTILINE)
        fdesc = desc_m.group(1).strip().strip('"\'') if desc_m else ''

        # Parse type
        type_m = re.search(r'^type:\s*(.+)', content, re.MULTILINE)
        ftype = type_m.group(1).strip().strip('"\'') if type_m else ''

        stem = fname[:-3]  # Remove .md
        expected = fid.replace('/', '_') + '.md'

        if stem == fid:
            ok_count += 1
            continue

        # It's a mismatch: filename != id
        in_registry = fid in registry
        reg_info = registry.get(fid, {})
        reg_path = reg_info.get('path', '')

        # Check if filename is a legitimate name (i.e., should exist)
        # by looking at whether the filename itself appears as id or label elsewhere
        mismatches.append({
            'filename': fname,
            'stem': stem,
            'current_id': fid,
            'current_label': flabel,
            'current_description': fdesc,
            'type': ftype,
            'expected_filename': expected,
            'in_registry': in_registry,
            'registry_path': reg_path,
            'restored': fname in restored_files if restored_files else None,
        })

    return mismatches, errors, ok_count

def print_report(mismatches, errors, ok_count):
    print(f'正确页面: {ok_count}')
    print(f'内容错填: {len(mismatches)}')
    print(f'读取错误: {len(errors)}')
    print()

    # Group by type
    for m in mismatches:
        status = 'RESTORED' if m.get('restored') else 'EXISTING'
        print(f'  {status} {m["filename"]}')
        print(f'        当前 id={m["current_id"]} label={m["current_label"]}')
        print(f'        文件名应表示: {m["stem"]}')
        if m['current_description']:
            print(f'        当前描述: {m["current_description"][:80]}')
        print()

def output_csv(mismatches):
    import csv
    import io
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['filename', 'current_id', 'current_label', 'expected_entity', 'type', 'current_description'])
    for m in mismatches:
        w.writerow([m['filename'], m['current_id'], m['current_label'], m['stem'], m['type'], m['current_description']])
    print(out.getvalue())

def main():
    mismatches, errors, ok_count = scan_all_pages()

    if '--csv' in sys.argv:
        output_csv(mismatches)
        return

    print_report(mismatches, errors, ok_count)

    # Also list errors
    if errors:
        print(f'\n=== 读取错误 ({len(errors)}个) ===')
        for fname, err in errors[:20]:
            print(f'  {fname}: {err}')

if __name__ == '__main__':
    main()
