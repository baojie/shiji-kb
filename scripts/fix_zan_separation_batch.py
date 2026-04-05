#!/usr/bin/env python3
"""
批量分离太史公曰区块中的韵文赞
"""

import re
from pathlib import Path

# 需要处理的章节及其韵文行数（从检测脚本输出）
CHAPTERS_TO_FIX = {
    '113': 7,  # 南越列传
    '114': 3,  # 东越列传
    '115': 8,  # 朝鲜列传
    '116': 3,  # 西南夷列传
    '118': 5,  # 淮南衡山列传
    '120': 8,  # 汲郑列传
    '122': 5,  # 酷吏列传
    '123': 5,  # 大宛列传
    '124': 5,  # 游侠列传
}

def clean_text(text):
    """移除标注符号"""
    text = re.sub(r'〖[@=#%;:&^~•!?+{_$\[\]]([^〗|]+)(?:\|[^〗]+)?〗', r'\1', text)
    text = re.sub(r'⟦[◈◉\[]([^⟧|]+)(?:\|[^⟧]+)?⟧', r'\1', text)
    return text

def split_taishigong_block(chapter_file):
    """分离太史公曰中的韵文"""
    content = chapter_file.read_text(encoding='utf-8')

    # 查找太史公曰区块
    pattern = r'(:::太史公曰\n+)(.*?)(^:::$)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

    if not match:
        print(f"  未找到太史公曰区块")
        return False

    block_start = match.group(1)
    block_content = match.group(2)
    block_end = match.group(3)

    # 分析区块内容，找到韵文起始位置
    lines = block_content.split('\n')
    verse_start_idx = None
    consecutive_verses = 0

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # 移除段落编号
        line = re.sub(r'^\[\d+\]\s*', '', line)
        clean = clean_text(line)

        # 检查是否为韵文（4-6字句）
        if re.match(r'^[\u4e00-\u9fff]{4,6}[，。：；！？]', clean):
            if verse_start_idx is None:
                verse_start_idx = idx
            consecutive_verses += 1
        else:
            # 如果已经找到韵文但遇到非韵文，停止
            if verse_start_idx is not None and consecutive_verses >= 3:
                break
            else:
                verse_start_idx = None
                consecutive_verses = 0

    if verse_start_idx is None or consecutive_verses < 3:
        print(f"  未检测到韵文")
        return False

    # 分离散文和韵文
    prose_lines = lines[:verse_start_idx]
    verse_lines = lines[verse_start_idx:]

    # 移除prose末尾空行
    while prose_lines and not prose_lines[-1].strip():
        prose_lines.pop()

    # 移除verse开头空行
    while verse_lines and not verse_lines[0].strip():
        verse_lines.pop(0)

    # 提取段落编号（假设韵文第一行有编号，需要增加）
    first_verse_line = verse_lines[0].strip()
    para_match = re.match(r'^\[(\d+)\]', first_verse_line)
    if para_match:
        old_para_num = int(para_match.group(1))
        new_para_num = old_para_num + 1
    else:
        # 如果没有编号，从prose最后一行提取并加1
        for line in reversed(prose_lines):
            para_match = re.match(r'^\[(\d+)\]', line.strip())
            if para_match:
                new_para_num = int(para_match.group(1)) + 1
                break
        else:
            new_para_num = 999  # 默认值

    # 为韵文第一行添加新段落编号
    if re.match(r'^\[\d+\]', verse_lines[0]):
        verse_lines[0] = re.sub(r'^\[\d+\]', f'[{new_para_num}]', verse_lines[0])
    else:
        verse_lines[0] = f'[{new_para_num}] ' + verse_lines[0]

    # 重构内容
    new_prose = '\n'.join(prose_lines)
    new_verse = '\n'.join(verse_lines)

    new_block = f"{block_start}{new_prose}\n\n:::\n\n::: 赞\n\n{new_verse}\n\n{block_end}"

    # 替换原内容
    new_content = content[:match.start()] + new_block + content[match.end():]

    # 保存
    chapter_file.write_text(new_content, encoding='utf-8')
    print(f"  ✓ 分离韵文成功，新段落编号: [{new_para_num}]")
    return True

def main():
    project_root = Path(__file__).parent.parent
    chapter_dir = project_root / "chapter_md"

    fixed_count = 0

    for chapter_num in CHAPTERS_TO_FIX:
        chapter_files = list(chapter_dir.glob(f"{chapter_num}_*.tagged.md"))
        if not chapter_files:
            print(f"❌ 章节 {chapter_num} 未找到")
            continue

        chapter_file = chapter_files[0]
        print(f"\n处理: {chapter_file.name}")

        if split_taishigong_block(chapter_file):
            fixed_count += 1

    print(f"\n完成！共修复 {fixed_count}/{len(CHAPTERS_TO_FIX)} 个章节")

if __name__ == "__main__":
    main()
