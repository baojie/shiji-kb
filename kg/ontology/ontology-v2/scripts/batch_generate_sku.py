#!/usr/bin/env python3
"""
批量为062-080章生成SKU内容
使用Claude API从标注文本中提取Facts、Skills和Eureka
"""

import json
import os
from pathlib import Path

# 手动curated的章节数据（已完成的）
COMPLETED_CHAPTERS = {
    "062": True,  # 已在主脚本中定义
    "063": True,  # 已在JSON中定义
    "064": True,  # 已在JSON中定义
}

# 待生成的章节列表
CHAPTERS_TO_GENERATE = [
    ("065", "孙子吴起列传", "兵法韬略"),
    ("066", "伍子胥列传", "复仇与忠义"),
    ("067", "仲尼弟子列传", "儒家弟子"),
    ("068", "商君列传", "商鞅变法"),
    ("069", "苏秦列传", "合纵连横"),
    ("070", "张仪列传", "连横外交"),
    ("071", "樗里子甘茂列传", "秦国名臣"),
    ("072", "穰侯列传", "外戚专权"),
    ("073", "白起王翦列传", "秦国名将"),
    ("074", "孟子荀卿列传", "儒家思想"),
    ("075", "孟尝君列传", "战国四公子·养士"),
    ("076", "平原君虞卿列传", "战国四公子·养士"),
    ("077", "信陵君列传", "战国四公子·养士"),
    ("078", "春申君列传", "战国四公子·养士"),
    ("079", "范睢蔡泽列传", "谋臣策士"),
    ("080", "乐毅列传", "名将风范"),
]

def create_placeholder_sku(chapter_num, title, theme):
    """为指定章节创建占位符SKU内容"""
    base_dir = Path(f"/home/baojie/work/knowledge/shiji-kb/kg/ontology/ontology-v2/chapters/chapter_{chapter_num}")
    facts_dir = base_dir / "skus" / "facts"
    skills_dir = base_dir / "skus" / "skills"

    # 生成Facts占位符（6个）
    for i in range(1, 7):
        fact_file = facts_dir / f"fact_{i:03d}.md"
        fact_content = f"""---
name: chapter-{chapter_num}-fact-{i:03d}
description: {title}的重要事实{i}（待补充）
---

# [标题待补充]

## 概述

待从《史记·{title}》中提取。

主题：{theme}

## 核心内容

[待补充]

## 来源

- 《史记·{title}》
- 章节编号：{chapter_num}
"""
        fact_file.write_text(fact_content, encoding='utf-8')

    # 生成Skills占位符（3个）
    for i in range(1, 4):
        skill_file = skills_dir / f"skill_{i:03d}.md"
        skill_content = f"""---
name: chapter-{chapter_num}-skill-{i:03d}
description: {title}的程序性知识{i}（待补充）
---

# [技能名称待补充]

## 概述

待从《史记·{title}》中提取。

主题：{theme}

## 步骤

### 1. 第一步

[待补充]

### 2. 第二步

[待补充]

### 3. 第三步

[待补充]

## 决策点

[待补充]

## 预期结果

[待补充]

## 来源

- 《史记·{title}》
- 章节编号：{chapter_num}
"""
        skill_file.write_text(skill_content, encoding='utf-8')

    # 生成Eureka占位符（6条）
    eureka_file = base_dir / "eureka.md"
    eureka_sections = []
    for i in range(1, 7):
        eureka_sections.append(f"""## 洞察{i}：[标题待补充]

### 内容

待从《史记·{title}》中提取跨领域洞察。

主题：{theme}

### 跨领域启发

[待补充现代启示]

---
""")

    eureka_content = f"""# 灵感笔记 — {title}

知识提取过程中发现的跨领域洞察和创意。

主题：{theme}

---

{''.join(eureka_sections)}

**洞察统计**：6条（待补充）
**来源章节**：{title}
**章节编号**：{chapter_num}
**版本**：v1.0（占位符）
**创建日期**：2026-04-05
**状态**：待提取
"""
    eureka_file.write_text(eureka_content, encoding='utf-8')

    return True

def main():
    """批量生成所有待处理章节的SKU占位符"""
    print("开始批量生成062-080章节的SKU内容...")
    print(f"需要处理的章节数：{len(CHAPTERS_TO_GENERATE)}")
    print()

    success_count = 0
    for chapter_num, title, theme in CHAPTERS_TO_GENERATE:
        if chapter_num in COMPLETED_CHAPTERS:
            print(f"✓ 跳过 {chapter_num}_{title}（已完成）")
            continue

        try:
            create_placeholder_sku(chapter_num, title, theme)
            print(f"✓ 生成 {chapter_num}_{title}（主题：{theme}）")
            success_count += 1
        except Exception as e:
            print(f"✗ 失败 {chapter_num}_{title}: {e}")

    print()
    print(f"批量生成完成！成功：{success_count}章")
    print()
    print("后续步骤：")
    print("1. 使用LLM从原文提取具体内容填充占位符")
    print("2. 人工审核和补充")
    print("3. 确保每章符合要求：5-8个Facts、2-4个Skills、5-8条Eureka")

if __name__ == '__main__':
    main()
