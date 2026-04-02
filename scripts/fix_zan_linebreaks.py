#!/usr/bin/env python3
"""
修正赞块中的韵文排版格式

规范：赞作为韵文，每句（8字）必须独立成行
问题：某些章节的赞块中，多个句子挤在一行里

使用方法：
    python scripts/fix_zan_linebreaks.py [章节文件]
    python scripts/fix_zan_linebreaks.py --all  # 批量处理所有章节
"""

import re
import sys
from pathlib import Path


def is_verse_text(text):
    """
    判断文本是否像韵文

    韵文特征：
    - 4-8字为主的短句
    - 句子整齐

    散文特征：
    - 长句（平均>=10字）
    - 句子长度不整齐
    """
    # 去除标注符号
    clean = re.sub(r'〖[^〗]+〗|⟦[^⟧]+⟧', '', text)
    # 按标点分割句子
    segments = re.split(r'[。？！]', clean)
    segments = [s.strip() for s in segments if s.strip()]

    if not segments:
        return False

    # 计算平均字数
    avg_len = sum(len(s) for s in segments) / len(segments)

    # 韵文：短句为主（平均<10字），散文：长句为主（平均>=10字）
    return avg_len < 10


def split_zan_sentences(text):
    """
    将赞块中的句子按标点分割，每句独立成行

    规则：
    - 以。？！为句子结束标志
    - 保留标注符号〖〗和⟦⟧
    - 每个句子独立成行
    """
    # 按句子标点分割
    sentences = re.split(r'([。？！])', text)

    # 重新组合句子和标点
    result = []
    for i in range(0, len(sentences) - 1, 2):
        if sentences[i].strip():
            sentence = sentences[i] + sentences[i + 1]
            result.append(sentence)

    # 处理最后一个句子（如果没有标点）
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        result.append(sentences[-1])

    return result


def fix_zan_block(block_text):
    """
    修正一个赞块的换行格式

    参数:
        block_text: 赞块内容（去除::: 赞和:::）

    返回:
        修正后的赞块内容
    """
    # 先判断整个块是否为韵文
    if not is_verse_text(block_text):
        # 散文，不修改
        return block_text

    lines = block_text.split('\n')
    fixed_lines = []

    for line in lines:
        line = line.strip()

        # 跳过空行和编号行
        if not line or re.match(r'^\[\d+(\.\d+)?\]$', line):
            fixed_lines.append(line)
            continue

        # 去除段落编号前缀
        pn_match = re.match(r'^(\[\d+(\.\d+)?\]\s*)(.*)', line)
        if pn_match:
            pn_prefix = pn_match.group(1)
            content = pn_match.group(3)
        else:
            pn_prefix = ''
            content = line

        # 检查是否包含多个句子标点
        clean_content = re.sub(r'〖[^〗]+〗|⟦[^⟧]+⟧', '', content)
        punct_count = len(re.findall(r'[。？！]', clean_content))

        if punct_count > 1:
            # 分割句子
            sentences = split_zan_sentences(content)

            # 第一句保留编号前缀
            if sentences:
                fixed_lines.append(pn_prefix + sentences[0])
                fixed_lines.extend(sentences[1:])
        else:
            # 单句，保持原样
            fixed_lines.append(pn_prefix + content if pn_prefix else line)

    return '\n'.join(fixed_lines)


def fix_chapter_file(file_path):
    """
    修正一个章节文件中的所有赞块

    参数:
        file_path: 章节文件路径

    返回:
        (是否有修改, 修改数量)
    """
    content = Path(file_path).read_text()
    original_content = content

    # 查找所有赞块
    def replace_zan(match):
        block_content = match.group(1)
        fixed_content = fix_zan_block(block_content)
        return f'::: 赞\n{fixed_content}\n:::'

    content = re.sub(
        r'^::: 赞\n(.*?)\n:::$',
        replace_zan,
        content,
        flags=re.MULTILINE | re.DOTALL
    )

    if content != original_content:
        Path(file_path).write_text(content)
        return True, 1

    return False, 0


def check_zan_problems(file_path):
    """
    检查章节文件中赞块的排版问题

    返回:
        问题列表
    """
    content = Path(file_path).read_text()
    problems = []

    # 查找所有赞块
    zan_blocks = re.finditer(r'^::: 赞\n(.*?)\n:::$', content, re.MULTILINE | re.DOTALL)

    for match in zan_blocks:
        block_content = match.group(1)

        # 先判断是否为韵文
        if not is_verse_text(block_content):
            # 散文，跳过
            continue

        lines = [l for l in block_content.split('\n')
                if l.strip() and not re.match(r'^\[\d+(\.\d+)?\]$', l.strip())]

        for line in lines:
            # 去除标注符号
            clean = re.sub(r'〖[^〗]+〗|⟦[^⟧]+⟧', '', line)

            # 计算标点数量
            punct_count = len(re.findall(r'[。？！]', clean))

            if punct_count > 1:
                problems.append({
                    'file': Path(file_path).name,
                    'line': line.strip()[:80],
                    'punct_count': punct_count
                })

    return problems


def main():
    import argparse

    parser = argparse.ArgumentParser(description='修正赞块中的韵文排版格式')
    parser.add_argument('files', nargs='*', help='要处理的章节文件')
    parser.add_argument('--all', action='store_true', help='处理所有章节文件')
    parser.add_argument('--check', action='store_true', help='只检查问题，不修改文件')

    args = parser.parse_args()

    # 确定要处理的文件
    if args.all:
        files = sorted(Path('chapter_md').glob('*.tagged.md'))
    elif args.files:
        files = [Path(f) for f in args.files]
    else:
        parser.print_help()
        sys.exit(1)

    if args.check:
        # 检查模式
        all_problems = []
        for file_path in files:
            problems = check_zan_problems(file_path)
            all_problems.extend(problems)

        if all_problems:
            print(f"发现 {len(all_problems)} 处赞排版问题:\n")
            for p in all_problems:
                print(f"文件: {p['file']}")
                print(f"  标点数: {p['punct_count']} (应该每句独立成行)")
                print(f"  内容: {p['line']}...")
                print()
        else:
            print("所有赞块格式正确！")
    else:
        # 修正模式
        total_files = 0
        total_fixes = 0

        for file_path in files:
            changed, count = fix_chapter_file(file_path)
            if changed:
                total_files += 1
                total_fixes += count
                print(f"✓ {file_path.name}: 修正 {count} 个赞块")

        if total_files > 0:
            print(f"\n总计: 修正 {total_files} 个文件，{total_fixes} 个赞块")
        else:
            print("无需修正")


if __name__ == '__main__':
    main()
