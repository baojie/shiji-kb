#!/usr/bin/env python3
"""
将 chapter_md/*.tagged.md 中的9类对称符号实体标注迁移到 〖TYPE content〗 格式。

旧格式（9类对称符号）：
    @人名@  =地名=  $官职$  %时间%  &朝代&  ^制度^  ~族群~  *器物*  !天文!

新格式（〖〗统一包裹，第一字符为类型标记）：
    〖@人名〗  〖=地名〗  〖$官职〗  〖%时间〗  〖&朝代〗
    〖^制度〗  〖~族群〗  〖*器物〗  〖!天文〗

嵌套处理（拍平，方案C）：
    @$天子$@ → 〖@天子〗   （外层人名保留，内层官职标记去除）
    $@安国君@$ → 〖$安国君〗  （外层官职保留，内层人名标记去除）

不变的6类：〚〛 〖+〗 《》 〈〉 【】 〔〕

用法：
    python scripts/migrate_to_lenticular.py --test 001      # 测试单章，打印diff
    python scripts/migrate_to_lenticular.py --test 001 042  # 测试多章
    python scripts/migrate_to_lenticular.py --all           # 全量迁移（含备份）
    python scripts/migrate_to_lenticular.py --check         # 检查旧格式残留数量
"""

import re
import sys
import shutil
import argparse
import difflib
from pathlib import Path

# ─── 项目路径 ───
PROJECT_ROOT = Path(__file__).parent.parent
CHAPTER_DIR = PROJECT_ROOT / 'chapter_md'
BACKUP_DIR = PROJECT_ROOT / 'chapter_md_backup'

# ─── 9类对称符号定义 ───
# 顺序：从右到左替换时不影响结果，但影响嵌套的"外层优先"判定
# 由于采用"所有匹配收集后右到左替换"，嵌套情况会由 strip_inner 处理
SYMMETRIC = [
    ('@', re.compile(r'@([^@\n]+)@')),
    ('=', re.compile(r'=([^=\n]+)=')),
    (';', re.compile(r'\$([^$\n]+)\$')),
    ('%', re.compile(r'%([^%\n]+)%')),
    ('&', re.compile(r'&([^&\n]+)&')),
    ('^', re.compile(r'\^([^\^\n]+)\^')),
    ('~', re.compile(r'~([^~\n]+)~')),
    # *器物* 需排除 **粗体**
    ('*', re.compile(r'(?<!\*)\*(?!\*)([^*\n]+)\*(?!\*)')),
    ('!', re.compile(r'!([^!\n]+)!')),
]

# 用于剥离内层对称标记的组合 pattern（内容中可能包含其他类型的标记）
_STRIP_INNER_PAT = re.compile(
    r'@([^@\n]+)@'
    r'|=([^=\n]+)='
    r'|\$([^$\n]+)\$'
    r'|%([^%\n]+)%'
    r'|&([^&\n]+)&'
    r'|\^([^\^\n]+)\^'
    r'|~([^~\n]+)~'
    r'|(?<!\*)\*(?!\*)([^*\n]+)\*(?!\*)'
    r'|!([^!\n]+)!'
)


def strip_inner(text: str) -> str:
    """从 text 中剥离所有对称标记，只保留内容文字。迭代直到稳定（处理多层嵌套）。"""
    for _ in range(5):  # 最多5轮，应对极深嵌套
        new = _STRIP_INNER_PAT.sub(
            lambda m: next(g for g in m.groups() if g is not None), text
        )
        if new == text:
            break
        text = new
    return text


def migrate_text(text: str) -> str:
    """
    将文本中所有9类对称标记迁移为 〖TYPE content〗 格式。
    收集所有匹配，保留最外层（嵌套时内层拍平），右到左替换。
    """
    # 收集所有匹配：(start, end, marker, raw_content)
    matches = []
    for marker, pat in SYMMETRIC:
        for m in pat.finditer(text):
            matches.append((m.start(), m.end(), marker, m.group(1)))

    if not matches:
        return text

    # 按 (起始位置升序, 结束位置降序) 排序：最外层（跨度最大）的匹配排在前面
    matches.sort(key=lambda x: (x[0], -x[1]))

    # 贪心选取：保留最外层，跳过被外层包含的内层匹配
    filtered = []
    covered: list[tuple[int, int]] = []  # 已选取匹配的区间

    for start, end, marker, content in matches:
        # 若当前匹配被已选区间包含（内层），跳过
        is_inner = any(s <= start and end <= e for s, e in covered)
        if is_inner:
            continue
        # 若当前匹配与已选区间部分重叠（不包含关系），也跳过（实践中极少出现）
        partially_overlaps = any(s < end and start < e for s, e in covered)
        if partially_overlaps:
            continue
        filtered.append((start, end, marker, content))
        covered.append((start, end))

    # 从右到左替换（避免替换后位置偏移）
    filtered.sort(key=lambda x: x[0], reverse=True)
    for start, end, marker, content in filtered:
        clean = strip_inner(content)
        text = text[:start] + f'〖{marker}{clean}〗' + text[end:]

    return text


def migrate_file(path: Path, dry_run: bool = False) -> tuple[str, str]:
    """读取并迁移单个文件，返回 (old_text, new_text)。dry_run=True 时不写入。"""
    old_text = path.read_text(encoding='utf-8')
    new_text = migrate_text(old_text)
    if not dry_run and new_text != old_text:
        path.write_text(new_text, encoding='utf-8')
    return old_text, new_text


def find_chapter_files(nums: list[str] | None = None) -> list[Path]:
    """返回 chapter_md/ 下的 tagged.md 文件列表。nums 为章节号列表（如 ['001','042']）。"""
    all_files = sorted(CHAPTER_DIR.glob('*.tagged.md'))
    if not nums:
        return all_files
    result = []
    for num in nums:
        matched = [f for f in all_files if f.name.startswith(num + '_') or f.name.startswith(num.zfill(3) + '_')]
        if not matched:
            # 宽松匹配：文件名包含该数字前缀
            matched = [f for f in all_files if f.stem.startswith(num)]
        result.extend(matched)
    return result


# 验证用：带负向回顾的旧格式检测（排除〖TYPE〗新格式内的误匹配）
_VERIFY_PATTERNS = [
    ('@', re.compile(r'(?<!〖)@([^@\n]+)@')),
    ('=', re.compile(r'(?<!〖)=([^=\n]+)=')),
    (';', re.compile(r'(?<!〖)\$([^$\n]+)\$')),
    ('%', re.compile(r'(?<!〖)%([^%\n]+)%')),
    ('&', re.compile(r'(?<!〖)&([^&\n]+)&')),
    ('^', re.compile(r'(?<!〖)\^([^\^\n]+)\^')),
    ('~', re.compile(r'(?<!〖)~([^~\n]+)~')),
    ('*', re.compile(r'(?<!〖)(?<!\*)\*(?!\*)([^*\n]+)\*(?!\*)')),
    ('!', re.compile(r'(?<!〖)!([^!\n]+)!')),
]


def count_old_format(text: str) -> dict[str, int]:
    """统计文本中各类旧格式的剩余数量（用于验证，排除新格式内的假阳性）。"""
    counts = {}
    for marker, pat in _VERIFY_PATTERNS:
        counts[marker] = len(pat.findall(text))
    return counts


def count_new_format(text: str) -> int:
    """统计文本中新格式 〖...〗 的数量。"""
    return len(re.findall(r'〖[^〖〗]+〗', text))


# ─── CLI ───

def cmd_test(nums: list[str]):
    """测试模式：打印diff但不写入文件。"""
    files = find_chapter_files(nums)
    if not files:
        print(f'未找到章节：{nums}')
        sys.exit(1)

    for path in files:
        print(f'\n{"="*60}')
        print(f'章节：{path.name}')
        old_text, new_text = migrate_file(path, dry_run=True)

        if old_text == new_text:
            print('  无变化')
            continue

        # 统计
        old_counts = count_old_format(old_text)
        new_old_counts = count_old_format(new_text)
        new_fmt_count = count_new_format(new_text)

        print(f'  旧格式（迁移前）：{sum(old_counts.values())} 处')
        print(f'  旧格式（迁移后残留）：{sum(new_old_counts.values())} 处')
        print(f'  新格式 〖〗：{new_fmt_count} 处')

        # 显示部分diff（前50行）
        diff = list(difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f'{path.name} (旧)',
            tofile=f'{path.name} (新)',
            n=2,
        ))
        if diff:
            print('  --- diff 前50行 ---')
            for line in diff[:50]:
                print('  ' + line, end='')
            if len(diff) > 50:
                print(f'\n  ... 共 {len(diff)} 行diff，已截断 ...')


def cmd_all():
    """全量迁移所有130章，先备份。"""
    files = find_chapter_files()
    print(f'找到 {len(files)} 个 tagged.md 文件')

    # 备份
    if BACKUP_DIR.exists():
        print(f'备份目录已存在：{BACKUP_DIR}（跳过备份，如需重新备份请手动删除）')
    else:
        print(f'备份到 {BACKUP_DIR} ...')
        shutil.copytree(CHAPTER_DIR, BACKUP_DIR)
        print('  备份完成')

    # 迁移
    changed = 0
    unchanged = 0
    errors = []

    for path in files:
        try:
            old_text, new_text = migrate_file(path, dry_run=False)
            if old_text != new_text:
                changed += 1
            else:
                unchanged += 1
        except Exception as e:
            errors.append((path.name, str(e)))
            print(f'  错误 {path.name}: {e}')

    print(f'\n迁移完成：{changed} 章有变化，{unchanged} 章无变化')
    if errors:
        print(f'错误 {len(errors)} 个：{[e[0] for e in errors]}')

    # 全局验证
    print('\n验证旧格式残留...')
    total_old = 0
    for path in files:
        text = path.read_text(encoding='utf-8')
        counts = count_old_format(text)
        s = sum(counts.values())
        if s > 0:
            detail = {k: v for k, v in counts.items() if v > 0}
            print(f'  ⚠️  {path.name}：残留 {s} 处 {detail}')
            total_old += s
    if total_old == 0:
        print('  ✓ 无旧格式残留')
    else:
        print(f'  共残留 {total_old} 处（详见上方）')


def cmd_check():
    """检查所有文件中旧格式和新格式的数量。"""
    files = find_chapter_files()
    total_old = {marker: 0 for marker, _ in SYMMETRIC}
    total_new = 0

    for path in files:
        text = path.read_text(encoding='utf-8')
        counts = count_old_format(text)
        for k, v in counts.items():
            total_old[k] += v
        total_new += count_new_format(text)

    print('旧格式统计（9类对称符号）：')
    labels = {'@': '人名', '=': '地名', ';': '官职', '%': '时间', '&': '朝代',
              '^': '制度', '~': '族群', '*': '器物', '!': '天文'}
    for marker, count in total_old.items():
        print(f'  {marker} ({labels[marker]}): {count:,}')
    print(f'  合计: {sum(total_old.values()):,}')
    print(f'\n新格式 〖〗 统计：{total_new:,}')


def main():
    parser = argparse.ArgumentParser(description='迁移实体标注格式：对称符号 → 〖TYPE content〗')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--test', nargs='+', metavar='NNN',
                       help='测试指定章节（如 --test 001 042），打印diff不写入')
    group.add_argument('--all', action='store_true',
                       help='全量迁移所有章节（先备份到 chapter_md_backup/）')
    group.add_argument('--check', action='store_true',
                       help='统计旧格式/新格式数量（只读）')

    args = parser.parse_args()

    if args.test:
        cmd_test(args.test)
    elif args.all:
        cmd_all()
    elif args.check:
        cmd_check()


if __name__ == '__main__':
    main()
