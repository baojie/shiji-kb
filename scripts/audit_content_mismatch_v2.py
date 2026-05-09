#!/usr/bin/env python3
"""精细分类审计：区分引号编码问题 / 方法论改名 / 真正内容错填"""

import os, re, sys, csv, json, io

PAGES_DIR = 'docs/wiki/pages'

FULLWIDTH_QUOTES = '“”‘’'
HALFWIDTH_QUOTES = "\"'"

def normalize_quotes(s):
    """Normalize fullwidth and halfwidth quotes for comparison."""
    s = s.replace('“', '"').replace('”', '"')
    s = s.replace('‘', "'").replace('’', "'")
    return s

def classify_mismatch(pid, label, stem, fname, desc):
    """Classify the type of mismatch."""
    # Case 1: Same content, just quote encoding differences
    pid_norm = normalize_quotes(pid)
    stem_norm = normalize_quotes(stem)
    label_norm = normalize_quotes(label) if label else ''

    if pid_norm == stem_norm or (label and label_norm == stem_norm):
        return 'QUOTE_ENCODING'

    # Case 2: Methodology rename - filename is short version of a long id
    # e.g. filename=围魏救赵.md, id=围魏救赵完整方法论：批亢捣虚六步法...
    if pid_norm.startswith(stem_norm + '完整') or \
       pid_norm.startswith(stem_norm + '整合') or \
       pid_norm.startswith(stem_norm + '风险') or \
       pid_norm.startswith(stem_norm + '模式') or \
       stem_norm + '三' in pid_norm or \
       stem_norm + '四' in pid_norm or \
       stem_norm + '五' in pid_norm or \
       stem_norm + '六' in pid_norm or \
       stem_norm + '七' in pid_norm or \
       stem_norm + '八' in pid_norm or \
       stem_norm in pid_norm and len(pid_norm) > len(stem_norm) * 1.5:
        return 'METHODOLOGY_RENAME'

    # Case 2b: id is completely contained in a method-description-style id
    # e.g. id=商鞅变法八步推行完整方法论..., stem=商鞅变法八步推行法
    # These are not real mismatches
    if pid_norm.startswith(stem_norm) or stem_norm.startswith(pid_norm):
        return 'SHORT_NAME_MISMATCH'

    # Case 3: id starts with "帝" but filename doesn't → 帝X series corruption
    if pid.startswith('帝') and not stem.startswith('帝'):
        return 'REAL_MISMATCH_帝系列错填'

    # Case 4: filename starts with "帝" but id doesn't
    if stem.startswith('帝') and not pid.startswith('帝'):
        return 'REAL_MISMATCH_帝系列错填'

    # Case 5: Pure entity mismatch (content is about completely different entity)
    return 'REAL_MISMATCH'

def scan():
    categories = {
        'QUOTE_ENCODING': [],
        'METHODOLOGY_RENAME': [],
        'SHORT_NAME_MISMATCH': [],
        'REAL_MISMATCH_帝系列错填': [],
        'REAL_MISMATCH': [],
    }
    errors = []
    ok_count = 0
    total = 0

    for fname in sorted(os.listdir(PAGES_DIR)):
        if not fname.endswith('.md'):
            continue
        fp = os.path.join(PAGES_DIR, fname)
        if not os.path.isfile(fp):
            continue

        total += 1
        try:
            content = open(fp, encoding='utf-8').read()
        except:
            errors.append(fname)
            continue

        id_m = re.search(r'^id:\s*(.+)', content, re.MULTILINE)
        if not id_m:
            errors.append(fname)
            continue
        pid = id_m.group(1).strip().strip('"\'')

        label_m = re.search(r'^label:\s*(.+)', content, re.MULTILINE)
        flabel = label_m.group(1).strip().strip('"\'') if label_m else ''

        desc_m = re.search(r'^description:\s*(.+)', content, re.MULTILINE)
        fdesc = desc_m.group(1).strip().strip('"\'') if desc_m else ''

        stem = fname[:-3]
        expected = pid.replace('/', '_') + '.md'

        if stem == pid:
            ok_count += 1
            continue

        cat = classify_mismatch(pid, flabel, stem, fname, fdesc)
        categories[cat].append({
            'filename': fname,
            'stem': stem,
            'current_id': pid,
            'current_label': flabel,
            'description': fdesc[:100] if fdesc else '',
            'expected_filename': expected,
        })

    return categories, errors, ok_count, total

def main():
    cats, errors, ok_count, total = scan()

    print(f'总计页面: {total}')
    print(f'正确(id==filename): {ok_count}')
    print(f'错误: {len(errors)}')
    print()

    for cat_name, items in cats.items():
        print(f'{cat_name}: {len(items)} 个')
        for m in items[:5]:
            print(f'    {m["filename"]}')
            print(f'        当前 id={m["current_id"][:80]}')
        if len(items) > 5:
            print(f'    ... 还有 {len(items)-5} 个')
        print()

    # Detail for REAL_MISMATCH
    for cat_name in ['REAL_MISMATCH_帝系列错填', 'REAL_MISMATCH']:
        items = cats[cat_name]
        if not items:
            continue
        print(f'\n=== {cat_name} 详情 ({len(items)}个) ===')
        for m in items:
            desc_short = m['description'][:60] if m['description'] else '(无描述)'
            print(f'  {m["filename"]}  → 当前id={m["current_id"][:40]}')

    print(f'\n=== 读取错误 ({len(errors)}个) ===')
    for e in errors[:20]:
        print(f'  {e}')

if __name__ == '__main__':
    main()
