#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量补标 〖#X〗 身份词。

策略：
1. 逐行处理，只在 〖...〗 标注区域外替换
2. 部分词需检查前缀，避免把专名后缀误标
   （例：吕太后→已是人名，不应再标 太后）
3. 诸侯：后接 相/主客/年表 时跳过（那是官职）
"""

import re
from pathlib import Path

# 词 → (前缀黑名单正则, 后缀黑名单正则)
# None 表示不限制
IDENTITY_RULES = {
    # 诸侯：不标 诸侯相 / 诸侯主客 / 诸侯年表
    '诸侯': (None, r'[相主年]'),
    # 陛下：无限制
    '陛下': (None, None),
    # 外戚：无限制
    '外戚': (None, None),
    # 太子：不标 已有专名前缀（2字+太子 通常是人名）
    # 前缀黑名单：悼/卫/栗/义/戾/孝/胶东/常山…；简单策略：前面紧跟汉字则跳过
    '太子': (r'[\u4e00-\u9fff]', None),
    # 太后：同上
    '太后': (r'[\u4e00-\u9fff]', None),
    # 公主：前面有专名则跳过
    '公主': (r'[\u4e00-\u9fff]', None),
    # 皇帝：无限制
    '皇帝': (None, None),
    # 大臣：无限制
    '大臣': (None, None),
    # 皇太后：无限制
    '皇太后': (None, None),
    # 妃：前面有专名前缀则跳过
    '妃': (r'[\u4e00-\u9fff]', None),
}

# 已标注区域正则（〖...〗 或 〚〛 等所有类型）
TAGGED = re.compile(r'〖[^〗]*〗|〚[^〛]*〛|〘[^〙]*〙|《[^》]*》|〈[^〉]*〉|【[^】]*】|〔[^〕]*〕')


def tag_line(line: str, word: str, prefix_re, suffix_re) -> str:
    """在 line 中，只在非标注区域内替换裸露的 word → 〖#word〗"""
    # 收集所有已标注区间
    protected = []
    for m in TAGGED.finditer(line):
        protected.append((m.start(), m.end()))

    def in_protected(pos, length):
        for s, e in protected:
            if pos < e and pos + length > s:
                return True
        return False

    result = []
    i = 0
    wlen = len(word)
    while i < len(line):
        # 若当前位置在保护区，直接输出
        skip = False
        for s, e in protected:
            if s <= i < e:
                result.append(line[i:e])
                i = e
                skip = True
                break
        if skip:
            continue

        # 尝试匹配 word
        if line[i:i+wlen] == word:
            # 检查前缀
            if prefix_re:
                prev_char = line[i-1] if i > 0 else ''
                if prev_char and re.match(prefix_re, prev_char):
                    result.append(line[i])
                    i += 1
                    continue
            # 检查后缀
            if suffix_re:
                next_char = line[i+wlen] if i+wlen < len(line) else ''
                if next_char and re.match(suffix_re, next_char):
                    result.append(line[i])
                    i += 1
                    continue
            result.append(f'〖#{word}〗')
            i += wlen
        else:
            result.append(line[i])
            i += 1

    return ''.join(result)


def process_file(path: Path, rules: dict) -> dict:
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)
    counts = {w: 0 for w in rules}
    new_lines = []
    for line in lines:
        for word, (pre, suf) in rules.items():
            before = line.count(f'〖#{word}〗')
            line = tag_line(line, word, pre, suf)
            after = line.count(f'〖#{word}〗')
            counts[word] += after - before
        new_lines.append(line)
    new_text = ''.join(new_lines)
    if new_text != text:
        path.write_text(new_text, encoding='utf-8')
    return counts


def main():
    chapter_dir = Path('chapter_md')
    files = sorted(chapter_dir.glob('*.tagged.md'))
    totals = {w: 0 for w in IDENTITY_RULES}
    changed = 0
    for f in files:
        counts = process_file(f, IDENTITY_RULES)
        file_total = sum(counts.values())
        if file_total:
            detail = ' '.join(f'{w}:{n}' for w, n in counts.items() if n)
            print(f'  {f.name}: {file_total}处  [{detail}]')
            changed += 1
        for w, n in counts.items():
            totals[w] += n
    print(f'\n合计：{changed}个文件')
    for w, n in totals.items():
        if n:
            print(f'  {w}: +{n}')


if __name__ == '__main__':
    main()
