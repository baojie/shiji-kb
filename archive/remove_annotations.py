#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去除史记三家注中的注释，只保留正文

三家注标记格式：
- (【集解】...)
- (【索隐】...)（或【索隱】）
- (【正义】...)（或【正義】）
"""

import re
import sys
from pathlib import Path


def remove_annotations(text):
    """
    去除三家注中的注释部分

    注释格式：(【集解】...) (【索隐】...) (【正义】...)
    注释可能嵌套多层括号
    """

    # 策略：从最内层到最外层逐步删除注释
    # 注释总是以 (【 开头，以 】....) 结尾

    result = text
    max_iterations = 200  # 增加迭代次数以处理深层嵌套

    # 第一步：删除所有形如 (【标记】...) 的注释块
    # 使用非贪婪匹配，从最内层开始
    # 注释标记：集解、索隐、索隱、正义、正義

    for iteration in range(max_iterations):
        # 匹配模式：(【标记】 后跟任意非括号字符或单层嵌套的括号，直到 )
        # 这会逐层剥离嵌套的注释
        pattern = r'\(【(?:集解|索隐|索隱|正义|正義)】(?:[^()【】]+|\([^()【】]*\))*?\)'

        new_result = re.sub(pattern, '', result)

        if new_result == result:
            # 如果没有变化，说明已经处理完毕
            break
        result = new_result

    # 第二步：清理可能残留的空括号和多余空格
    result = re.sub(r'\(\s*\)', '', result)

    # 第三步：删除任何残留的【标记】标记（不在括号内的）
    # 这种情况可能是格式损坏导致
    result = re.sub(r'【(?:集解|索隐|索隱|正义|正義)】[^【〖\n]*', '', result)

    # 第四步：删除形如 (【(集解】...) 的畸形标记（括号在内部）
    for iteration in range(max_iterations):
        pattern = r'\(【\((?:集解|索隐|索隱|正义|正義)】(?:[^()]+|\([^()]*\))*?\)'
        new_result = re.sub(pattern, '', result)
        if new_result == result:
            break
        result = new_result

    # 第五步：处理单独的括号注释（没有【】标记的注释性内容）
    # 例如 (右述贊之體...) 这种
    # 但要小心不要删除正文中的括号内容
    # 识别特征：括号内是长段文字且包含特定词汇

    # 识别"述贊""索隱"等注释性关键词
    annotation_keywords = [
        r'\(右述贊', r'\(【述贊', r'\(述贊',
        r'\(索隱述贊', r'\(右索隱'
    ]

    for keyword_pattern in annotation_keywords:
        # 匹配从关键词开始到段落结束的内容
        pattern = keyword_pattern + r'[^)]*\)'
        for _ in range(10):
            new_result = re.sub(pattern, '', result)
            if new_result == result:
                break
            result = new_result

    return result


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

    # 去除注释
    print("正在去除三家注...")
    cleaned_content = remove_annotations(content)

    print(f"处理后大小: {len(cleaned_content)} 字符")
    print(f"删除了 {len(content) - len(cleaned_content)} 字符 ({(len(content) - len(cleaned_content)) / len(content) * 100:.1f}%)")

    # 检查残留的注释标记
    remaining_markers = re.findall(r'【(?:集解|索隐|索隱|正义|正義)】', cleaned_content)
    if remaining_markers:
        print(f"\n警告：仍有 {len(remaining_markers)} 个注释标记未清除")
        print(f"前10个残留标记的上下文：")
        for marker in remaining_markers[:10]:
            pos = cleaned_content.find(marker)
            context = cleaned_content[max(0, pos-20):min(len(cleaned_content), pos+50)]
            print(f"  ...{context}...")
    else:
        print("\n✓ 所有注释标记已清除")

    # 保存结果
    print(f"\n保存到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

    print("完成！")


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
