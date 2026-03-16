#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件索引文件标注格式迁移：v1 → v2.1

将 kg/events/data/*.md 中的旧格式标注迁移为统一的〖TYPE content〗格式。

v1 → v2.1 映射：
  @X@    → 〖@X〗   人名
  =X=    → 〖=X〗   地名
  $X$    → 〖;X〗   官职（符号从$变为;）
  %X%    → 〖%X〗   时间
  &X&    → 〖&X〗   朝代
  ^X^    → 〖^X〗   制度
  ~X~    → 〖~X〗   族群
  *X*    → 〖•X〗   器物（需区分markdown粗体**X**）
  !X!    → 〖!X〗   天文

嵌套模式处理：
  $@X@$          → 〖@X〗         人名优先
  $title@X@$     → 〖;title〗〖@X〗  拆分官职+人名
  $title@X@suffix$ → 〖;title〗〖@X〗〖;suffix〗

用法：
    python scripts/migrate_event_index_tags.py --dry-run
    python scripts/migrate_event_index_tags.py
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

EVENT_DIR = Path('kg/events/data')

# 统计
stats = defaultdict(int)


def migrate_nested_dollar_at(text):
    """处理嵌套的 $...@X@...$ 模式"""
    # 模式1: $@X@$ → 〖@X〗（最常见：人名在官职标记内）
    def replace_simple_nested(m):
        person = m.group(1)
        stats['$@X@$'] += 1
        return f'〖@{person}〗'

    text = re.sub(r'\$@([^@\n]+)@\$', replace_simple_nested, text)

    # 模式2: $title@X@$ → 〖;title〗〖@X〗
    def replace_title_person(m):
        title = m.group(1)
        person = m.group(2)
        stats['$title@X@$'] += 1
        return f'〖;{title}〗〖@{person}〗'

    text = re.sub(r'\$([^@$\n]+)@([^@\n]+)@\$', replace_title_person, text)

    # 模式3: $title@X@suffix$ (rare) → 〖;title〗〖@X〗〖;suffix〗
    # Already handled by pattern 2 if no suffix

    return text


def migrate_at(text):
    """@X@ → 〖@X〗 人名"""
    def replace(m):
        stats['@X@'] += 1
        return f'〖@{m.group(1)}〗'
    # (?<!〖) 防止匹配已转换的v2.1标注中的@（如〖@始皇〗中的@）
    return re.sub(r'(?<!〖)@([^@\n]+)@', replace, text)


def migrate_equal(text):
    """=X= → 〖=X〗 地名"""
    def replace(m):
        stats['=X='] += 1
        return f'〖={m.group(1)}〗'
    return re.sub(r'(?<!〖)=([^=\n]+)=', replace, text)


def migrate_dollar(text):
    """$X$ → 〖;X〗 官职（剩余的简单$标记）"""
    def replace(m):
        content = m.group(1)
        # 跳过已转换的〖@〗内容
        if '〖' in content or '〗' in content:
            return m.group(0)
        stats['$X$'] += 1
        return f'〖;{content}〗'
    return re.sub(r'(?<!〖)\$([^$\n]+)\$', replace, text)


def migrate_percent(text):
    """%X% → 〖%X〗 时间"""
    def replace(m):
        stats['%X%'] += 1
        return f'〖%{m.group(1)}〗'
    return re.sub(r'(?<!〖)%([^%\n]+)%', replace, text)


def migrate_ampersand(text):
    """&X& → 〖&X〗 朝代"""
    def replace(m):
        stats['&X&'] += 1
        return f'〖&{m.group(1)}〗'
    return re.sub(r'(?<!〖)&([^&\n]+)&', replace, text)


def migrate_caret(text):
    """^X^ → 〖^X〗 制度"""
    def replace(m):
        stats['^X^'] += 1
        return f'〖^{m.group(1)}〗'
    return re.sub(r'(?<!〖)\^([^^\n]+)\^', replace, text)


def migrate_tilde(text):
    """~X~ → 〖~X〗 族群"""
    def replace(m):
        stats['~X~'] += 1
        return f'〖~{m.group(1)}〗'
    return re.sub(r'(?<!〖)~([^~\n]+)~', replace, text)


def migrate_asterisk(text):
    """*X* → 〖•X〗 器物（排除markdown粗体 **X**）"""
    def replace(m):
        stats['*X*'] += 1
        return f'〖•{m.group(1)}〗'
    # (?<!〖) 防止匹配已转换标注; (?<!\*)/(?!\*) 排除markdown粗体
    return re.sub(r'(?<!〖)(?<!\*)\*([^*\n]{1,12})\*(?!\*)', replace, text)


def migrate_exclamation(text):
    """!X! → 〖!X〗 天文（仅匹配短内容，避免匹配感叹号标点）"""
    def replace(m):
        stats['!X!'] += 1
        return f'〖!{m.group(1)}〗'
    # 限制1-10个CJK字符，排除标点/空格/引号等，避免匹配感叹号
    return re.sub(r'(?<!〖)!([\u4e00-\u9fff]{1,10})!', replace, text)


def has_v1_tags(text):
    """检查文本是否包含v1格式标注"""
    # 检查各种v1模式（排除markdown和已迁移的v2.1）
    patterns = [
        r'@[^@\n]+@',           # 人名
        r'(?<!=)=[^=\n]+=(?!=)', # 地名（排除==）
        r'\$[^$\n]+\$',         # 官职
        r'%[^%\n]+%',           # 时间
        r'&[^&\n]+&',           # 朝代
        r'\^[^^\n]+\^',         # 制度
        r'~[^~\n]+~',           # 族群
        r'(?<!\*)\*[^*\n]{1,12}\*(?!\*)',  # 器物
    ]
    for p in patterns:
        if re.search(p, text):
            return True
    return False


def migrate_file(fpath, dry_run=False):
    """迁移单个文件"""
    text = fpath.read_text(encoding='utf-8')
    original = text

    if not has_v1_tags(text):
        return False

    # 按顺序迁移（先处理嵌套，再处理简单模式）
    text = migrate_nested_dollar_at(text)  # $@X@$ 先处理
    text = migrate_at(text)                 # @X@
    text = migrate_equal(text)              # =X=
    text = migrate_dollar(text)             # $X$（剩余）
    text = migrate_percent(text)            # %X%
    text = migrate_ampersand(text)          # &X&
    text = migrate_caret(text)              # ^X^
    text = migrate_tilde(text)              # ~X~
    text = migrate_asterisk(text)           # *X*
    text = migrate_exclamation(text)        # !X!

    if text == original:
        return False

    if not dry_run:
        fpath.write_text(text, encoding='utf-8')
    return True


def main():
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print('=== DRY RUN（不写入文件）===\n')
    else:
        print('=== 迁移事件索引标注格式 v1 → v2.1 ===\n')

    files = sorted(EVENT_DIR.glob('*_事件索引.md'))
    print(f'发现 {len(files)} 个事件索引文件\n')

    changed = 0
    for fpath in files:
        if migrate_file(fpath, dry_run):
            changed += 1
            print(f'  ✓ {fpath.name}')

    print(f'\n迁移文件数: {changed}/{len(files)}')
    print(f'\n替换统计:')
    for pattern, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f'  {pattern:20s} → {count:5d} 次')
    print(f'  {"总计":20s} → {sum(stats.values()):5d} 次')

    if dry_run:
        print('\n（dry-run模式，未写入任何文件）')


if __name__ == '__main__':
    main()
