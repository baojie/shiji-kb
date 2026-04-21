#!/usr/bin/env python3
"""
白话翻译JSON生成脚本

从 doc/translation/NNN_章节名_白话.md 生成 docs/translations/NNN.json
在生成过程中完成语义标注的HTML渲染，确保前端直接使用渲染后的HTML

用法:
    python scripts/generate_translation_json.py 001
    python scripts/generate_translation_json.py 001 002 003  # 批量生成
    python scripts/generate_translation_json.py --all  # 生成所有已有的翻译
"""

import sys
import re
import json
from pathlib import Path

# 导入语义标签处理模块
sys.path.insert(0, str(Path(__file__).parent))
from semantic_tags import render_tags_to_html


def parse_translation_markdown(md_path: Path) -> dict:
    """
    解析翻译Markdown文件，提取PN段落和翻译内容

    参数:
        md_path: 翻译Markdown文件路径

    返回:
        {
            "chapter": "001",
            "title": "章节名",
            "translations": {
                "1": {"title": "段落标题", "text": "译文（HTML渲染后）"},
                "1.1": {"title": "段落标题", "text": "译文（HTML渲染后）"},
                ...
            }
        }
    """
    if not md_path.exists():
        raise FileNotFoundError(f"翻译文件不存在: {md_path}")

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取章节编号和标题
    filename = md_path.name
    match = re.match(r'(\d{3})_(.+)_白话\.md', filename)
    if not match:
        raise ValueError(f"文件名格式错误: {filename}")

    chapter_num = match.group(1)
    chapter_title = match.group(2)

    # 只提取"---"分隔符之前的内容（简洁版翻译）
    # 跳过"原文与译文对照"部分
    parts = content.split('\n---\n', 1)
    main_content = parts[0]

    # 解析段落
    translations = {}

    # 匹配格式: ## [PN编号] 段落标题\n\n译文内容
    # 支持多行译文（包括列表项），直到下一个 ## 或文件结束
    pattern = r'## \[([^\]]+)\] (.+?)\n\n((?:(?!^##).)+)'
    matches = re.finditer(pattern, main_content, re.MULTILINE | re.DOTALL)

    for match in matches:
        pn_num = match.group(1).strip()
        title = match.group(2).strip()
        text = match.group(3).strip()

        # 处理列表项：保留列表结构或合并为文本
        # 如果译文是列表格式，保留列表结构
        if text.startswith('- '):
            # 保留列表，每行前添加空格以保持格式
            lines = text.split('\n')
            text = ' '.join(line[2:].strip() if line.startswith('- ') else line for line in lines)
        else:
            # 移除多余的换行，合并为单个段落
            text = ' '.join(text.split())

        # 关键：使用semantic_tags模块进行HTML渲染
        # prefer_canonical=True：白话上下文，消歧格式 〖@籍|项籍〗 显示"项籍"（规范名）
        # 详见 SKILL_01h §消歧语法（白话上下文）
        text_html = render_tags_to_html(text, prefer_canonical=True)

        translations[pn_num] = {
            "title": title,
            "text": text_html
        }

    return {
        "chapter": chapter_num,
        "title": chapter_title,
        "translations": translations
    }


def generate_translation_json(chapter_num: str, output_dir: Path = None):
    """
    为指定章节生成翻译JSON文件

    参数:
        chapter_num: 章节编号（如 "001"）
        output_dir: 输出目录（默认为 docs/translations/）
    """
    # 确保章节编号是三位数
    chapter_num = chapter_num.zfill(3)

    # 查找对应的翻译Markdown文件
    translation_dir = Path('doc/translation')
    md_files = list(translation_dir.glob(f'{chapter_num}_*_白话.md'))

    if not md_files:
        print(f"⚠️  未找到章节 {chapter_num} 的翻译文件")
        return False

    if len(md_files) > 1:
        print(f"⚠️  章节 {chapter_num} 有多个翻译文件: {[f.name for f in md_files]}")
        return False

    md_path = md_files[0]

    try:
        # 解析Markdown并生成JSON
        data = parse_translation_markdown(md_path)

        # 输出JSON文件
        if output_dir is None:
            output_dir = Path('docs/translations')
        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir / f'{chapter_num}.json'

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✓ 已生成: {json_path}")
        print(f"  - {len(data['translations'])} 个段落")
        print(f"  - 语义标注已渲染为HTML")

        return True

    except Exception as e:
        print(f"❌ 生成失败: {md_path.name}")
        print(f"   错误: {e}")
        return False


def main():
    """主函数：处理命令行参数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scripts/generate_translation_json.py 001")
        print("  python scripts/generate_translation_json.py 001 002 003")
        print("  python scripts/generate_translation_json.py --all")
        sys.exit(1)

    if sys.argv[1] == '--all':
        # 生成所有已有的翻译
        translation_dir = Path('doc/translation')
        md_files = sorted(translation_dir.glob('*_白话.md'))

        if not md_files:
            print("未找到任何翻译文件")
            sys.exit(1)

        print(f"找到 {len(md_files)} 个翻译文件")
        success_count = 0

        for md_file in md_files:
            match = re.match(r'(\d{3})_', md_file.name)
            if match:
                chapter_num = match.group(1)
                if generate_translation_json(chapter_num):
                    success_count += 1

        print(f"\n完成: 成功生成 {success_count}/{len(md_files)} 个JSON文件")

    else:
        # 生成指定的章节
        chapter_nums = sys.argv[1:]
        success_count = 0

        for chapter_num in chapter_nums:
            if generate_translation_json(chapter_num):
                success_count += 1

        print(f"\n完成: 成功生成 {success_count}/{len(chapter_nums)} 个JSON文件")


if __name__ == '__main__':
    main()
