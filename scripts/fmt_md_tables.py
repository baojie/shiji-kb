"""格式化Markdown文件中的表格，使列对齐（支持中文等宽字符）。

用法：
  python scripts/fmt_md_tables.py file.md          # 原地格式化
  python scripts/fmt_md_tables.py file.md --dry-run # 只输出不写入
"""
import sys, unicodedata, re

def char_width(c):
    ea = unicodedata.east_asian_width(c)
    return 2 if ea in ('W', 'F') else 1

def str_width(s):
    return sum(char_width(c) for c in s)

def pad(s, width):
    return s + ' ' * (width - str_width(s))

def fmt_table(lines):
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        rows.append(cells)
    ncols = max(len(r) for r in rows)
    col_widths = [0] * ncols
    for r in rows:
        for i, c in enumerate(r):
            if i < ncols:
                col_widths[i] = max(col_widths[i], str_width(c))
    result = []
    for r in rows:
        if r and all(set(c.strip()) <= {'-', ':'} for c in r if c.strip()):
            result.append('| ' + ' | '.join('-' * w for w in col_widths) + ' |')
        else:
            cells = [pad(r[i] if i < len(r) else '', col_widths[i]) for i in range(ncols)]
            result.append('| ' + ' | '.join(cells) + ' |')
    return result

def process_file(path, dry_run=False):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    out = []
    table_buf = []
    in_table = False
    changed = False
    
    for line in lines:
        stripped = line.strip()
        is_table = stripped.startswith('|') and stripped.endswith('|')
        
        if is_table:
            table_buf.append(stripped)
            in_table = True
        else:
            if in_table and table_buf:
                formatted = fmt_table(table_buf)
                original = table_buf
                if formatted != original:
                    changed = True
                for fl in formatted:
                    out.append(fl + '\n')
                table_buf = []
                in_table = False
            out.append(line)
    
    if table_buf:
        formatted = fmt_table(table_buf)
        if formatted != table_buf:
            changed = True
        for fl in formatted:
            out.append(fl + '\n')
    
    if dry_run:
        sys.stdout.writelines(out)
    elif changed:
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(out)
        print(f'格式化: {path}')
    else:
        print(f'无变化: {path}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    dry_run = '--dry-run' in sys.argv
    files = [a for a in sys.argv[1:] if a != '--dry-run']
    for f in files:
        process_file(f, dry_run)
