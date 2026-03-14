#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量补标亲属关系身份词 〖#X〗。

策略：
1. 只在 〖...〗 保护区外替换
2. 长子/少子/庶子/世子/嗣子：后接人名汉字时跳过（通常是"长子太伯"这类）
3. 姬：不标（多为姬氏/人名成分）
4. 孤：不标（多为孤竹地名 或 单字，歧义大）
"""

import re
from pathlib import Path

# 词 → (前缀黑名单正则, 后缀黑名单正则, 说明)
KIN_RULES = {
    # 安全词：直接标注
    '兄弟':   (None, None),
    '子孙':   (None, None),
    '宗室':   (None, None),
    '诸子':   (None, None),
    '妻子':   (None, None),
    '亲戚':   (None, None),
    '苗裔':   (None, None),
    '宗族':   (None, None),
    '人子':   (None, None),
    '母子':   (None, None),
    '夫妇':   (None, None),
    '妻妾':   (None, None),
    '寡妇':   (None, None),
    '宗亲':   (None, None),
    '后裔':   (None, None),
    # 需要前缀检查：当前面没有汉字限定词时才标
    # （避免 "长子太伯" 中的 "长子" 被独立标注——但实际上这种情况 "长子" 是泛指角色描述）
    # 实测原文中"长子X"多为 〖@长子X〗 person名，若裸露则是泛指
    '长子':   (None, r'[\u4e00-\u9fff]'),   # 后接汉字（即人名）则跳过
    '少子':   (None, r'[\u4e00-\u9fff]'),
    '庶子':   (None, r'[\u4e00-\u9fff]'),
    '世子':   (None, r'[\u4e00-\u9fff]'),
    '嗣子':   (None, None),
    '庶孽':   (None, None),
    '质子':   (None, None),   # 裸露的（已有标注的已在上面处理）
    '父子':   (None, None),
    '妾':     (None, r'[\u4e00-\u9fff]'),   # 后接汉字（如妾X = 妾身）
    '外孙':   (None, None),
    '人父':   (None, None),
}

TAGGED = re.compile(r'〖[^〗]*〗|〚[^〛]*〛|〘[^〙]*〙|《[^》]*》|〈[^〉]*〉|【[^】]*】|〔[^〕]*〕')


def tag_line(line: str, word: str, prefix_re, suffix_re) -> str:
    protected = [(m.start(), m.end()) for m in TAGGED.finditer(line)]

    def in_protected(pos):
        return any(s <= pos < e for s, e in protected)

    result = []
    i = 0
    wlen = len(word)
    while i < len(line):
        skip = False
        for s, e in protected:
            if s <= i < e:
                result.append(line[i:e])
                i = e
                skip = True
                break
        if skip:
            continue

        if line[i:i+wlen] == word:
            if prefix_re:
                prev = line[i-1] if i > 0 else ''
                if prev and re.match(prefix_re, prev):
                    result.append(line[i]); i += 1; continue
            if suffix_re:
                nxt = line[i+wlen] if i+wlen < len(line) else ''
                if nxt and re.match(suffix_re, nxt):
                    result.append(line[i]); i += 1; continue
            result.append(f'〖#{word}〗')
            i += wlen
        else:
            result.append(line[i])
            i += 1
    return ''.join(result)


def process_file(path: Path) -> dict:
    text = path.read_text('utf-8')
    lines = text.splitlines(keepends=True)
    counts = {w: 0 for w in KIN_RULES}
    new_lines = []
    for line in lines:
        for word, (pre, suf) in KIN_RULES.items():
            before = line.count(f'〖#{word}〗')
            line = tag_line(line, word, pre, suf)
            counts[word] += line.count(f'〖#{word}〗') - before
        new_lines.append(line)
    new_text = ''.join(new_lines)
    if new_text != text:
        path.write_text(new_text, 'utf-8')
    return counts


def main():
    files = sorted(Path('chapter_md').glob('*.tagged.md'))
    totals = {w: 0 for w in KIN_RULES}
    changed = 0
    for f in files:
        counts = process_file(f)
        n = sum(counts.values())
        if n:
            detail = ' '.join(f'{w}:{c}' for w, c in counts.items() if c)
            print(f'  {f.name}: {n}处  [{detail}]')
            changed += 1
        for w, c in counts.items():
            totals[w] += c
    print(f'\n合计：{changed}个文件')
    for w, n in totals.items():
        if n:
            print(f'  {w}: +{n}')


if __name__ == '__main__':
    main()
