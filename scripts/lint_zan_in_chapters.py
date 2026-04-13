#!/usr/bin/env python3
"""
检查chapter_md/中"赞"的格式规范

规范要求:
1. 赞文必须是四字句为主
2. 每句独立成行(不得连写在一行)
3. 使用全角标点符号
4. 不得使用半角逗号、分号等
"""

import re
import sys
from pathlib import Path


def check_zan_format(file_path: Path) -> list[str]:
    """检查单个文件的赞文格式"""
    errors = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找"::: 赞"段落
    pattern = r'::: 赞\n(.*?)\n:::'
    matches = re.findall(pattern, content, re.DOTALL)

    if not matches:
        return errors

    for i, zan_text in enumerate(matches, start=1):
        lines = [line.strip() for line in zan_text.strip().split('\n') if line.strip()]

        # 检查每行
        for j, line in enumerate(lines, start=1):
            # 移除Purple Numbers (如 [1] [1.1])
            line_clean = re.sub(r'\[\d+(?:\.\d+)?\]\s*', '', line)

            # 移除所有标注符号 (〖...〗 和 ⟦...⟧)
            line_clean = re.sub(r'〖[^〗]*〗', '', line_clean)
            line_clean = re.sub(r'⟦[^⟧]*⟧', '', line_clean)

            # 检查1: 不得使用半角标点
            halfwidth_punctuation = re.findall(r'[,;:!?]', line_clean)
            if halfwidth_punctuation:
                errors.append(f"  ❌ 第{i}段第{j}行: 发现半角标点 {set(halfwidth_punctuation)}")
                errors.append(f"     行: {line}")

            # 检查2: 如果一行包含多个句子(有多个句号/逗号/分号),可能需要分行
            # 检测模式: "四字，四字；四字，四字。" 这种应该是4行
            full_stops = line_clean.count('。') + line_clean.count('！') + line_clean.count('？')
            if full_stops > 1:
                errors.append(f"  ⚠️  第{i}段第{j}行: 包含{full_stops}个句子,可能需要分行")
                errors.append(f"     行: {line}")

            # 检查3: 检测"四字X四字X四字X四字。"模式(X为标点)
            # 这种应该拆成多行
            hanzi = re.sub(r'[^\u4e00-\u9fff]', '', line_clean)
            if len(hanzi) >= 16:  # 4句或以上
                # 检查是否是连续的四字句模式
                pattern_4char = r'[\u4e00-\u9fff]{4}[，、；]'
                matches_4char = re.findall(pattern_4char, line_clean)
                if len(matches_4char) >= 2:
                    errors.append(f"  ⚠️  第{i}段第{j}行: 连续四字句({len(matches_4char)+1}句)未分行")
                    errors.append(f"     行: {line}")

    return errors


def main():
    """主函数"""
    chapter_dir = Path(__file__).parent.parent / 'chapter_md'

    # 获取所有标注文件
    chapter_files = sorted(chapter_dir.glob('*.tagged.md'))

    all_errors = {}
    for chapter_file in chapter_files:
        errors = check_zan_format(chapter_file)
        if errors:
            all_errors[chapter_file.name] = errors

    # 输出结果
    if all_errors:
        print("🔍 发现赞文格式问题:\n")
        for filename, errors in all_errors.items():
            print(f"📄 {filename}:")
            for error in errors:
                print(error)
            print()

        print(f"\n❌ 共 {len(all_errors)} 个文件存在格式问题")
        return 1
    else:
        print("✅ 所有赞文格式检查通过")
        return 0


if __name__ == '__main__':
    sys.exit(main())
