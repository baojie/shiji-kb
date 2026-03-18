#!/usr/bin/env python3
"""
从元技能文档中删除目录部分
"""

import re
from pathlib import Path


def remove_toc(file_path: Path) -> bool:
    """删除文档中的目录部分"""
    content = file_path.read_text(encoding='utf-8')

    # 查找目录开始位置
    toc_pattern = r'\n## 目录\n.*?\n---\n'

    # 尝试匹配并删除（非贪婪匹配到下一个---）
    new_content, count = re.subn(toc_pattern, '\n---\n', content, flags=re.DOTALL)

    if count > 0:
        file_path.write_text(new_content, encoding='utf-8')
        print(f"✓ {file_path.name}: 已删除目录")
        return True
    else:
        print(f"- {file_path.name}: 未找到目录或已删除")
        return False


def main():
    skills_dir = Path('skills')
    meta_files = sorted(skills_dir.glob('00-META-*.md'))

    # 跳过已手动处理的01文件
    processed_count = 0

    for file_path in meta_files:
        if '01_反思' in file_path.name:
            print(f"⊙ {file_path.name}: 已手动处理，跳过")
            continue

        if remove_toc(file_path):
            processed_count += 1

    print(f"\n总计处理: {processed_count} 个文档")


if __name__ == '__main__':
    main()
