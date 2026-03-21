#!/usr/bin/env python3
"""
为skills目录下的所有SKILL_*.md文件添加YAML frontmatter

Frontmatter格式：
---
name: skill-name-in-kebab-case
description: 从第一行标题提取的简短描述
---
"""

import re
import os
from pathlib import Path

def extract_title_and_description(content):
    """从文件内容提取标题和描述"""
    lines = content.strip().split('\n')

    # 查找第一个标题行 (# SKILL XX: ...)
    title = ""
    description = ""

    for line in lines:
        if line.startswith('# SKILL'):
            # 提取标题，格式如: # SKILL 01: 古籍校勘 — 从底本到定本的文字审校
            match = re.match(r'# SKILL\s+(\S+):\s*(.+?)(?:\s*—\s*(.+))?$', line)
            if match:
                skill_num = match.group(1)
                title = match.group(2).strip()
                description = match.group(3).strip() if match.group(3) else title
                break

    return title, description

def title_to_name(title, skill_num):
    """将标题转换为name字段（kebab-case）"""
    # 移除特殊字符，转换为拼音或英文（简化版：直接使用数字+简化标题）
    # 由于中文转拼音复杂，这里先用skill编号作为name
    name = f"skill-{skill_num.replace('_', '-').lower()}"
    return name

def add_frontmatter(file_path):
    """为单个文件添加frontmatter"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已有frontmatter
    if content.startswith('---'):
        print(f"  ⏭️  {file_path.name} 已有frontmatter，跳过")
        return False

    # 从文件名提取skill编号
    filename = file_path.stem  # 如 SKILL_01_古籍校勘
    match = re.match(r'SKILL_(\S+?)(?:_.*)?$', filename)
    if not match:
        print(f"  ⚠️  {file_path.name} 文件名格式不匹配，跳过")
        return False

    skill_num = match.group(1)

    # 提取标题和描述
    title, description = extract_title_and_description(content)
    if not title:
        print(f"  ⚠️  {file_path.name} 无法提取标题，跳过")
        return False

    # 生成name字段
    name = title_to_name(title, skill_num)

    # 构建frontmatter
    frontmatter = f"""---
name: {name}
title: {title}
description: {description}
---

"""

    # 添加frontmatter到文件开头
    new_content = frontmatter + content

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  ✅ {file_path.name}")
    print(f"      name: {name}")
    print(f"      title: {title}")
    print(f"      description: {description[:50]}..." if len(description) > 50 else f"      description: {description}")

    return True

def main():
    skills_dir = Path('/home/baojie/work/shiji-kb/skills')
    skill_files = sorted(skills_dir.glob('SKILL_*.md'))

    print(f"找到 {len(skill_files)} 个SKILL文件\n")

    processed = 0
    skipped = 0

    for file_path in skill_files:
        if add_frontmatter(file_path):
            processed += 1
        else:
            skipped += 1

    print(f"\n总结:")
    print(f"  ✅ 处理: {processed} 个")
    print(f"  ⏭️  跳过: {skipped} 个")
    print(f"  📝 总计: {len(skill_files)} 个")

if __name__ == '__main__':
    main()
