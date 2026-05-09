#!/usr/bin/env python3
"""批量补全史记引文：为有 sources 但缺「史记引文」章节的页面批量添加引文。

流程：
1. 从 quality_audit.csv 读取 A1_NO_QUOTE_SECTION 且无 B4_NO_SOURCES 的页面
2. 对每页运行 quote_page.py 获取候选引文
3. 格式化后追加到页面

用法：
  python3 scripts/batch_add_quotes.py                  # 处理全部 5841 页
  python3 scripts/batch_add_quotes.py --dry-run        # 仅预览
  python3 scripts/batch_add_quotes.py --limit 100      # 只处理前 100 页
  python3 scripts/batch_add_quotes.py --resume         # 从上次中断处继续
"""
import csv, os, re, subprocess, sys, json, time

PAGES_DIR = 'docs/wiki/pages'
QUOTE_SCRIPT = '.claude/skills/quote/scripts/quote_page.py'
PROGRESS_FILE = 'logs/batch_quotes_progress.json'

def get_candidates(page_id: str) -> list[str]:
    """Run quote_page.py and extract suggested citation lines."""
    try:
        result = subprocess.run(
            [sys.executable, QUOTE_SCRIPT, page_id, '--max', '20'],
            capture_output=True, text=True, timeout=30
        )
    except subprocess.TimeoutExpired:
        return []
    except FileNotFoundError:
        return []

    output = result.stdout

    # Parse the "建议格式" section at the end
    lines = output.splitlines()
    in_suggestion = False
    suggestions = []
    for line in lines:
        if '建议格式' in line:
            in_suggestion = True
            continue
        if in_suggestion:
            line = line.strip()
            if line.startswith('> 出自') or (line.startswith('>') and '出自' in line):
                suggestions.append(line)
            elif line.startswith('=') and len(line) > 10:
                break

    return suggestions

def page_has_quote_section(page_path: str) -> bool:
    """Check if page already has a 史记引文 section."""
    if not os.path.exists(page_path):
        return False
    content = open(page_path, encoding='utf-8').read()
    return '## 史记引文' in content or '## 引文' in content or '# 史记引文' in content

def append_quote_section(page_path: str, quotes: list[str]) -> bool:
    """Append 史记引文 section to page. Returns True if modified."""
    with open(page_path, encoding='utf-8') as f:
        content = f.read()

    # Avoid duplicate
    if '## 史记引文' in content:
        return False

    # Append at the end
    quote_section = '\n\n## 史记引文\n\n' + '\n'.join(quotes) + '\n'
    with open(page_path, 'w', encoding='utf-8') as f:
        f.write(content.rstrip() + quote_section)
    return True

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {'processed': [], 'added': 0, 'skipped': 0, 'errors': 0}

def save_progress(progress):
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def main():
    dry_run = '--dry-run' in sys.argv
    resume = '--resume' in sys.argv
    limit = None
    for arg in sys.argv:
        if arg.startswith('--limit='):
            limit = int(arg.split('=')[1])
        elif arg == '--limit' and len(sys.argv) > sys.argv.index(arg) + 1:
            limit = int(sys.argv[sys.argv.index(arg) + 1])

    progress = load_progress() if resume else {'processed': [], 'added': 0, 'skipped': 0, 'errors': 0}
    processed_set = set(progress['processed'])

    # Read target pages from CSV
    target_pages = []
    with open('labs/analysis/quality_audit.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            summary = row.get('issues_summary', '')
            if 'A1_NO_QUOTE_SECTION' in summary and 'B4_NO_SOURCES' not in summary:
                pid = row['page_id']
                if pid not in processed_set:
                    target_pages.append(pid)

    total = len(target_pages)
    if limit:
        target_pages = target_pages[:limit]
        total = limit

    print(f'待处理页面: {total}')
    if dry_run:
        print('=== DRY RUN — 不执行修改 ===\n')
        for pid in target_pages[:5]:
            fp = os.path.join(PAGES_DIR, f'{pid}.md')
            if os.path.exists(fp):
                has_q = page_has_quote_section(fp)
                print(f'  {pid}: 引文节={has_q}')
        if total > 5:
            print(f'  ... 还有 {total-5} 页')
        return

    # Process pages
    start = time.time()
    for i, pid in enumerate(target_pages):
        fp = os.path.join(PAGES_DIR, f'{pid}.md')
        if not os.path.exists(fp):
            progress['errors'] += 1
            progress['processed'].append(pid)
            continue
        if page_has_quote_section(fp):
            progress['skipped'] += 1
            progress['processed'].append(pid)
            continue

        candidates = get_candidates(pid)
        if not candidates:
            progress['skipped'] += 1
            progress['processed'].append(pid)
            continue

        if append_quote_section(fp, candidates):
            progress['added'] += 1
        else:
            progress['skipped'] += 1

        progress['processed'].append(pid)

        # Progress every 100 pages
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            remaining = (total - i - 1) / rate if rate > 0 else 0
            print(f'  [{i+1}/{total}] 已添加 {progress["added"]} 页, '
                  f'跳过 {progress["skipped"]}, 错误 {progress["errors"]}, '
                  f'速率 {rate:.1f} 页/秒, 预计剩余 {remaining:.0f} 秒')
            save_progress(progress)

    # Final
    elapsed = time.time() - start
    print(f'\n完成: 添加 {progress["added"]}, 跳过 {progress["skipped"]}, '
          f'错误 {progress["errors"]}, 耗时 {elapsed:.0f} 秒')
    save_progress(progress)

if __name__ == '__main__':
    main()
