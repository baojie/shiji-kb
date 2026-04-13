#!/usr/bin/env python3
"""
检查章节标注文件(chapter_md/*.tagged.md)中"赞"的格式规范

规范要求:
1. 每行是两个四字句(去除标注符号和PN后每行8个汉字)
2. 使用全角标点符号
3. 不得使用半角逗号、分号等
"""

import re
import sys
from pathlib import Path


def check_zan_format(file_path: Path) -> list[str]:
    """检查单个文件的赞文格式"""
    errors = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找赞文块（::: 赞 ... :::）
    pattern = r'::: 赞\n(.*?)\n:::'
    matches = re.findall(pattern, content, re.DOTALL)

    if not matches:
        return errors

    for i, zan_text in enumerate(matches, start=1):
        lines = [line.strip() for line in zan_text.strip().split('\n') if line.strip()]

        # 检查1: 每行应该是两个四字句(去除标注符号、PN、标点后应有8个汉字)
        for j, line in enumerate(lines, start=1):
            # 移除Purple Number [数字]
            text_no_pn = re.sub(r'\[\d+\]\s*', '', line)
            # 处理消歧语法 〖TYPE显示名|规范名〗 → 显示名
            # 〖@成|周成王〗 → @成 → 成
            # 先去掉|规范名部分
            text_no_disambig = re.sub(r'\|[^〗⟧]+', '', text_no_pn)
            # 移除标注符号的类型标记，保留内容文本
            # 〖@少典〗 → 少典, ⟦◈擒⟧ → 擒, 〖@成〗 → 成
            text_no_tags = re.sub(r'[〖⟦][^〗⟧\u4e00-\u9fff]+', '', text_no_disambig)
            text_no_tags = re.sub(r'[〗⟧]', '', text_no_tags)
            # 移除标点,只保留汉字
            hanzi = re.sub(r'[^\u4e00-\u9fff]', '', text_no_tags)
            if len(hanzi) != 8:
                errors.append(f"  ❌ 赞文第{i}段第{j}行: 应为8字,实际{len(hanzi)}字")
                errors.append(f"     原文: {line}")
                errors.append(f"     去标注后: {text_no_tags}")
                errors.append(f"     汉字: {hanzi}")

        # 检查2: 不得使用半角标点（但标注符号内部的类型标记不算）
        # 先移除所有标注符号（包括其内容）
        text_for_punct_check = re.sub(r'[〖⟦][^〗⟧]*[〗⟧]', '', zan_text)
        halfwidth_punctuation = re.findall(r'[,;:!?]', text_for_punct_check)
        if halfwidth_punctuation:
            errors.append(f"  ❌ 赞文第{i}段: 发现半角标点 {set(halfwidth_punctuation)}")
            # 显示具体位置
            for line in lines:
                if re.search(r'[,;:!?]', line):
                    errors.append(f"     行: {line}")

    return errors


def main():
    """主函数"""
    chapter_dir = Path(__file__).parent.parent / 'chapter_md'

    # 获取所有章节标注文件
    log_files = sorted(chapter_dir.glob('*.tagged.md'))

    all_errors = {}
    for log_file in log_files:
        errors = check_zan_format(log_file)
        if errors:
            all_errors[log_file.name] = errors

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
