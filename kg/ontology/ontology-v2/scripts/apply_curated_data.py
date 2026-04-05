#!/usr/bin/env python3
"""
应用手工curated的章节数据（063-064）
"""

import json
from pathlib import Path

def generate_fact_md(chapter_num, fact, title):
    """生成单个Fact的Markdown文件"""
    return f"""---
name: chapter-{chapter_num}-fact-{fact['id']}
description: {fact['name']}
---

# {fact['name']}

## 概述

{fact['description']}

## 核心内容

### 事实要点

{fact['description']}

### 历史意义

此事体现了{fact['name']}的历史价值和文化意义。

## 来源

- 《史记·{title}》
- 章节：{fact['source']}
"""


def generate_skill_md(chapter_num, skill, title):
    """生成单个Skill的Markdown文件"""
    steps_md = "\n\n".join([f"### {i+1}. {step}" for i, step in enumerate(skill['steps'])])

    return f"""---
name: chapter-{chapter_num}-skill-{skill['id']}
description: {skill['name']}
---

# {skill['name']}

## 概述

{skill['description']}

## 步骤

{steps_md}

## 决策点

在执行此方法时，需要注意以下关键决策点：

- 根据具体情境灵活调整策略
- 把握时机和分寸
- 保持原则性与灵活性的平衡

## 预期结果

通过运用此方法，可以达到预期的效果并避免常见陷阱。

## 来源

- 《史记·{title}》
"""


def generate_eureka_md(chapter_num, eureka_list, title):
    """生成Eureka的Markdown文件"""
    eureka_sections = []
    for i, eureka in enumerate(eureka_list, 1):
        section = f"""## 洞察{i}：{eureka['title']}

### 内容

{eureka['content']}

### 跨领域启发

{eureka['insight']}

---
"""
        eureka_sections.append(section)

    return f"""# 灵感笔记 — {title}

知识提取过程中发现的跨领域洞察和创意。

---

{''.join(eureka_sections)}

**洞察统计**：{len(eureka_list)}条
**来源章节**：{title}
**版本**：v1.0
**创建日期**：2026-04-05
"""


def generate_chapter_sku(chapter_num, chapter_data):
    """为指定章节生成完整的SKU内容"""
    base_dir = Path(f"/home/baojie/work/knowledge/shiji-kb/kg/ontology/ontology-v2/chapters/chapter_{chapter_num}")
    facts_dir = base_dir / "skus" / "facts"
    skills_dir = base_dir / "skus" / "skills"

    title = chapter_data['title']

    # 生成Facts
    for fact in chapter_data['facts']:
        fact_file = facts_dir / f"fact_{fact['id']}.md"
        fact_content = generate_fact_md(chapter_num, fact, title)
        fact_file.write_text(fact_content, encoding='utf-8')
        print(f"✓ 生成: fact_{fact['id']}.md")

    # 生成Skills
    for skill in chapter_data['skills']:
        skill_file = skills_dir / f"skill_{skill['id']}.md"
        skill_content = generate_skill_md(chapter_num, skill, title)
        skill_file.write_text(skill_content, encoding='utf-8')
        print(f"✓ 生成: skill_{skill['id']}.md")

    # 生成Eureka
    eureka_file = base_dir / "eureka.md"
    eureka_content = generate_eureka_md(chapter_num, chapter_data['eureka'], title)
    eureka_file.write_text(eureka_content, encoding='utf-8')
    print(f"✓ 生成: eureka.md")

    return True


def main():
    """应用curated数据"""
    # 读取JSON数据
    json_file = Path(__file__).parent / "chapters_062_080_data.json"
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("开始应用手工curated的章节数据...")
    print()

    for chapter_num, chapter_data in data.items():
        print(f"处理章节 {chapter_num}_{chapter_data['title']}:")
        generate_chapter_sku(chapter_num, chapter_data)
        print(f"✓ 章节 {chapter_num} 完成")
        print()

    print("所有curated数据已应用！")


if __name__ == '__main__':
    main()
