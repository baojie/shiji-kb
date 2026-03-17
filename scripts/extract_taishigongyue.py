#!/usr/bin/env python3
"""
提取所有章节的"太史公曰"内容
创建专项索引：太史公曰
"""

import re
from pathlib import Path
import json


def extract_taishigongyue(chapter_file):
    """从单个章节提取太史公曰内容"""
    content = chapter_file.read_text(encoding='utf-8')

    # 提取章节编号和标题
    match = re.match(r'(\d+)_(.+)\.tagged\.md', chapter_file.name)
    if not match:
        return None

    chapter_num = match.group(1)
    chapter_title = match.group(2)

    # 方法1：查找带::: 标记的太史公曰块（最常见格式）
    # 支持多种标题格式：## 太史公曰 或 ## [25] 太史公曰
    pattern1 = r'##\s*(?:\[\d+\])?\s*太史公曰.*?\n.*?::: 太史公曰\s*\n(.*?)\n:::'
    matches = re.findall(pattern1, content, re.DOTALL)

    if matches:
        taishigongyue_text = matches[0].strip()
        return {
            'chapter_num': chapter_num,
            'chapter_title': chapter_title,
            'content': taishigongyue_text
        }

    # 方法2：查找段落中的太史公曰（如001章格式，无::: 标记）
    # 支持 [27] 或 [27.1] 格式的段落编号
    pattern2 = r'\[(\d+(?:\.\d+)?)\] 〖@太史公〗曰：([^\n]+(?:\n(?!\[|\n|##)[^\n]+)*)'
    matches = re.findall(pattern2, content, re.MULTILINE)

    if matches:
        # 合并所有匹配的段落
        taishigongyue_text = '\n\n'.join([f"[{m[0]}] 〖@太史公〗曰：{m[1]}" for m in matches])
        return {
            'chapter_num': chapter_num,
            'chapter_title': chapter_title,
            'content': taishigongyue_text.strip()
        }

    return None


def main():
    chapter_dir = Path(__file__).parent.parent / "chapter_md"
    output_dir = Path(__file__).parent.parent / "docs" / "special"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("正在提取太史公曰...")

    # 收集所有太史公曰
    taishigongyue_list = []

    chapter_files = sorted(chapter_dir.glob("*.tagged.md"))

    for chapter_file in chapter_files:
        result = extract_taishigongyue(chapter_file)
        if result:
            taishigongyue_list.append(result)
            print(f"  ✓ {result['chapter_num']}_{result['chapter_title']}")

    print(f"\n共提取 {len(taishigongyue_list)} 篇太史公曰\n")

    # 保存为JSON
    json_file = output_dir / "taishigongyue.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(taishigongyue_list, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON已保存: {json_file}")

    # 生成Markdown文件
    md_file = output_dir / "taishigongyue.md"

    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# 太史公曰\n\n")
        f.write(f"史记中共有 {len(taishigongyue_list)} 篇太史公曰。\n\n")
        f.write("---\n\n")

        for item in taishigongyue_list:
            f.write(f"## {item['chapter_num']} {item['chapter_title']}\n\n")
            f.write(f"{item['content']}\n\n")
            f.write("---\n\n")

    print(f"✅ Markdown已保存: {md_file}")

    return taishigongyue_list


if __name__ == "__main__":
    main()
