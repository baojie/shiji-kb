#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去除史记三家注中的注释，只保留正文

三家注标记格式：(【集解】...) (【索隐】...) (【正义】...)
使用状态机方法，逐字符扫描处理
"""

import sys
from pathlib import Path


def remove_annotations_stateful(text):
    """
    使用状态机方法去除注释

    状态：
    - NORMAL: 正常文本
    - IN_ANNOTATION: 在注释内部
    """

    result = []
    i = 0
    length = len(text)

    # 注释标记
    annotation_markers = ['【集解】', '【索隐】', '【索隱】', '【正义】', '【正義】']

    while i < length:
        # 检查是否是注释开始标记 (【
        if i < length - 3 and text[i] == '(' and text[i+1] == '【':
            # 检查是否是三家注标记之一
            is_annotation = False
            for marker in annotation_markers:
                if text[i+1:i+1+len(marker)] == marker:
                    is_annotation = True
                    break

            if is_annotation:
                # 找到匹配的右括号
                depth = 1
                j = i + 1
                while j < length and depth > 0:
                    if text[j] == '(':
                        depth += 1
                    elif text[j] == ')':
                        depth -= 1
                    j += 1
                # 跳过整个注释块
                i = j
                continue

        # 正常字符，添加到结果
        result.append(text[i])
        i += 1

    return ''.join(result)


def clean_remaining_markers(text):
    """清理残留的注释标记"""
    markers = ['【集解】', '【索隐】', '【索隱】', '【正义】', '【正義】']

    for marker in markers:
        # 删除单独出现的标记（可能是格式损坏导致）
        text = text.replace(marker, '')

    # 删除特定的注释段落标记
    annotation_starts = [
        '(右述贊', '(【述贊', '(述贊',
        '(索隱述贊', '(右索隱'
    ]

    for start in annotation_starts:
        while start in text:
            pos = text.find(start)
            if pos != -1:
                # 找到对应的右括号
                depth = 1
                j = pos + 1
                while j < len(text) and depth > 0:
                    if text[j] == '(':
                        depth += 1
                    elif text[j] == ')':
                        depth -= 1
                    j += 1
                text = text[:pos] + text[j:]
            else:
                break

    return text


def process_file(input_file, output_file):
    """
    处理文件，去除三家注

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
    """
    print(f"读取文件: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"原文件大小: {len(content)} 字符")

    # 去除注释（使用状态机方法）
    print("正在去除三家注（第一遍：括号标记）...")
    cleaned_content = remove_annotations_stateful(content)

    print(f"第一遍处理后: {len(cleaned_content)} 字符")

    # 清理残留标记
    print("正在清理残留标记（第二遍）...")
    cleaned_content = clean_remaining_markers(cleaned_content)

    print(f"最终大小: {len(cleaned_content)} 字符")
    print(f"删除了 {len(content) - len(cleaned_content)} 字符 ({(len(content) - len(cleaned_content)) / len(content) * 100:.1f}%)")

    # 检查残留的注释标记
    remaining_count = 0
    for marker in ['【集解】', '【索隐】', '【索隱】', '【正义】', '【正義】']:
        count = cleaned_content.count(marker)
        remaining_count += count

    if remaining_count > 0:
        print(f"\n警告：仍有 {remaining_count} 个注释标记未清除")
    else:
        print("\n✓ 所有注释标记已清除")

    # 保存结果
    print(f"\n保存到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

    print("完成！")

    # 显示统计信息
    print(f"\n统计信息：")
    print(f"  原文：{len(content):,} 字符")
    print(f"  正文：{len(cleaned_content):,} 字符")
    print(f"  注释：{len(content) - len(cleaned_content):,} 字符")
    print(f"  注释占比：{(len(content) - len(cleaned_content)) / len(content) * 100:.1f}%")


def main():
    """主函数"""
    # 设置输入输出文件路径
    script_dir = Path(__file__).parent
    input_file = script_dir / '史記三家注.txt'
    output_file = script_dir / '史記正文.txt'

    if not input_file.exists():
        print(f"错误：输入文件不存在: {input_file}")
        sys.exit(1)

    process_file(input_file, output_file)


if __name__ == '__main__':
    main()
