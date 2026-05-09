#!/usr/bin/env python3
"""清理孤儿文件：磁盘上 filename ≠ frontmatter id 的 .md 文件。

流程：
1. 扫描 docs/wiki/pages/*.md
2. 读 frontmatter id 字段
3. 若 filename != id.md:
   a. 若正确名称的文件已存在 → 删除孤儿（旧版本残存）
   b. 若正确名称的文件不存在 → 重命名孤儿

安全模式：
  --dry-run  仅列出，不修改
  --delete   允许删除确认安全的孤儿
  --rename   允许重命名

用法：
  python3 scripts/cleanup_orphan_files.py --dry-run
  python3 scripts/cleanup_orphan_files.py --delete --rename
"""

import os, re, sys, shutil

PAGES_DIR = 'docs/wiki/pages'
REGISTRY = 'docs/wiki/pages.json'

def load_registry():
    import json
    with open(REGISTRY) as f:
        data = json.load(f)
    return data.get('pages', {})

def get_files_to_clean():
    """Find orphan files where filename != frontmatter id."""
    issues = []
    pages = load_registry()

    for fname in sorted(os.listdir(PAGES_DIR)):
        if not fname.endswith('.md'):
            continue
        fp = os.path.join(PAGES_DIR, fname)
        if not os.path.isfile(fp):
            continue

        try:
            content = open(fp, encoding='utf-8').read()
        except Exception as e:
            issues.append((fname, 'READ_ERROR', str(e)))
            continue

        id_m = re.search(r'^id:\s*(.+)', content, re.MULTILINE)
        if not id_m:
            continue

        fid = id_m.group(1).strip().strip('"\'')
        expected = fid.replace('/', '_') + '.md'

        if fname == expected:
            continue  # Name matches ID, all good

        # Check if the proper file exists
        proper_path = os.path.join(PAGES_DIR, expected)
        proper_exists = os.path.exists(proper_path)

        # Check registry
        in_registry = fid in pages

        if proper_exists:
            # Orphan: stale copy, proper file exists
            proper_size = os.path.getsize(proper_path)
            this_size = os.path.getsize(fp)
            issues.append((fname, 'STALE_COPY',
                          f'id="{fid}" proper={expected}({proper_size}B) '
                          f'stale_size={this_size}B'))
        elif in_registry:
            # Proper file doesn't exist but registry knows this ID
            reg_path = pages[fid].get('path', '?')
            issues.append((fname, 'NAME_MISMATCH_IN_REG',
                          f'id="{fid}" reg_path={reg_path} renaming needed'))
        else:
            # Neither proper file nor registry entry exists
            sz = os.path.getsize(fp)
            issues.append((fname, 'ORPHAN_NO_REG',
                          f'id="{fid}" not in registry, size={sz}B'))

    return issues

def main():
    dry_run = '--dry-run' in sys.argv
    do_delete = '--delete' in sys.argv
    do_rename = '--rename' in sys.argv

    if dry_run:
        print('=== DRY RUN — no files will be modified ===')

    issues = get_files_to_clean()

    # Group by type
    stale = [i for i in issues if i[1] == 'STALE_COPY']
    name_mismatch = [i for i in issues if i[1] == 'NAME_MISMATCH_IN_REG']
    orphans = [i for i in issues if i[1] == 'ORPHAN_NO_REG']

    print(f'\n总计孤儿文件: {len(issues)}')
    print(f'  STALE_COPY (可安全删除): {len(stale)}')
    print(f'  NAME_MISMATCH_IN_REG (需重命名): {len(name_mismatch)}')
    print(f'  ORPHAN_NO_REG (无注册信息): {len(orphans)}')

    # Show samples
    for label, group in [('STALE_COPY — 可删除', stale),
                          ('NAME_MISMATCH_IN_REG — 需重命名', name_mismatch),
                          ('ORPHAN_NO_REG — 待审查', orphans)]:
        print(f'\n--- {label} ({len(group)}个) ---')
        for fname, issue_type, detail in group[:10]:
            print(f'  {fname}  {detail}')
        if len(group) > 10:
            print(f'  ... 还有 {len(group)-10} 个')

    # Execute
    if dry_run:
        print('\n[Dry-run] 未执行任何修改')
        return

    deleted = 0
    renamed = 0
    errors = 0

    for fname, issue_type, detail in issues:
        fp = os.path.join(PAGES_DIR, fname)

        if issue_type == 'STALE_COPY' and do_delete:
            try:
                os.remove(fp)
                print(f'  DELETE {fname}  ({detail})')
                deleted += 1
            except Exception as e:
                print(f'  ERROR deleting {fname}: {e}')
                errors += 1

        elif issue_type == 'NAME_MISMATCH_IN_REG' and do_rename:
            # Extract expected name from detail
            import json
            pages = load_registry()
            content = open(fp, encoding='utf-8').read()
            id_m = re.search(r'^id:\s*(.+)', content, re.MULTILINE)
            if id_m:
                fid = id_m.group(1).strip().strip('"\'')
                expected = fid.replace('/', '_') + '.md'
                new_path = os.path.join(PAGES_DIR, expected)
                if os.path.exists(new_path):
                    print(f'  SKIP rename {fname} → {expected}: target exists')
                    continue
                try:
                    shutil.move(fp, new_path)
                    print(f'  RENAME {fname} → {expected}')
                    renamed += 1
                except Exception as e:
                    print(f'  ERROR renaming {fname}: {e}')
                    errors += 1

        elif issue_type == 'ORPHAN_NO_REG' and do_delete:
            # Only delete if very small (stub) and no registry entry
            try:
                os.remove(fp)
                print(f'  DELETE ORPHAN {fname}')
                deleted += 1
            except Exception as e:
                print(f'  ERROR deleting {fname}: {e}')
                errors += 1

    print(f'\n完成: 删除 {deleted}, 重命名 {renamed}, 错误 {errors}')


if __name__ == '__main__':
    main()
