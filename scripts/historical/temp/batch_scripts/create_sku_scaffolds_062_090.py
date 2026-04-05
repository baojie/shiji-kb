#!/usr/bin/env python3
"""
为《史记》062-090章节创建SKU框架

由于完整的知识提取需要深度阅读和分析每章内容，本脚本创建基本的目录结构和模板文件，
供后续手工或AI辅助完善。

框架包括：
- 目录结构：skus/facts/, skus/skills/
- 模板文件：mapping.md, eureka.md, README.md
- 基础fact和skill模板
"""

import os
import json
from pathlib import Path

# 配置
BASE_DIR = Path("/home/baojie/work/knowledge/shiji-kb")
CHAPTER_MD_DIR = BASE_DIR / "chapter_md"
OUTPUT_BASE_DIR = BASE_DIR / "kg/ontology/ontology-v2/chapters"

# 章节信息（手动整理的062-090章节）
CHAPTERS = [
    (62, "管晏列传"),
    (63, "老子韩非列传"),
    (64, "司马穰苴列传"),
    (65, "孙子吴起列传"),
    (66, "伍子胥列传"),
    (67, "仲尼弟子列传"),
    (68, "商君列传"),
    (69, "苏秦列传"),
    (70, "张仪列传"),
    (71, "樗里子甘茂列传"),
    (72, "穰侯列传"),
    (73, "白起王翦列传"),
    (74, "孟子荀卿列传"),
    (75, "孟尝君列传"),
    (76, "平原君虞卿列传"),
    (77, "魏公子列传"),
    (78, "春申君列传"),
    (79, "范睢蔡泽列传"),
    (80, "乐毅列传"),
    (81, "廉颇蔺相如列传"),
    (82, "田单列传"),
    (83, "鲁仲连邹阳列传"),
    (84, "屈原贾生列传"),
    (85, "吕不韦列传"),
    (86, "刺客列传"),
    (87, "李斯列传"),
    (88, "蒙恬列传"),
    (89, "张耳陈馀列传"),
    (90, "魏豹彭越列传"),
]


def create_scaffold(chapter_num, chapter_title):
    """为单章创建SKU框架"""
    print(f"创建 {chapter_num:03d}_{chapter_title} 的框架...")

    # 创建目录
    chapter_dir = OUTPUT_BASE_DIR / f"chapter_{chapter_num:03d}"
    facts_dir = chapter_dir / "skus/facts"
    skills_dir = chapter_dir / "skus/skills"

    facts_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    # 创建README.md
    readme_content = f"""# {chapter_title} — 知识图谱

本目录包含《史记·{chapter_title}》章节的结构化知识提取。

---

## 目录结构

```
chapter_{chapter_num:03d}/
├── skus/
│   ├── facts/          # 事实性知识单元
│   │   ├── fact_001.json    # [待补充]
│   │   └── fact_002.md      # [待补充]
│   └── skills/         # 程序性知识单元
│       └── skill_001.md     # [待补充]
├── mapping.md          # SKU使用场景映射
├── eureka.md           # 跨领域洞察
└── README.md           # 本文件
```

---

## 知识单元概览

### 事实性知识（Facts）

**待提取**：人物生平、核心事迹、思想主张、历史评价

### 程序性知识（Skills）

**待提取**：处事方法、策略应用、思想体系

---

## 跨领域洞察（Eureka）

**待提取**：跨领域启发性洞察

---

## 提取方法

**使用工具**：Anything2Ontology Lite (a2o-lite)

**提取原则**：
- MECE原则（相互独立，完全穷尽）
- 列传特点：重点提取人物生平、核心事迹、思想主张
- 事实与技能分离
- 质量重于数量

**数据来源**：
- 原始文本：`/home/baojie/work/knowledge/shiji-kb/chapter_md/{chapter_num:03d}_{chapter_title}.tagged.md`

---

**版本**：v1.0（框架）
**创建日期**：2026-04-05
**状态**：待完善
"""

    readme_path = chapter_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    # 创建mapping.md
    mapping_content = f"""# SKU 映射 — {chapter_title}

本文件将《史记·{chapter_title}》的所有标准知识单元（SKU）映射到其使用场景。

---

## 待补充

请根据本章内容，为每个知识单元添加：
1. 描述（该SKU包含什么内容）
2. 使用场景（什么情况下应该调用这个SKU）

---

**本章SKU统计**：
- 事实性知识单元（facts）：[待统计]
- 程序性知识单元（skills）：[待统计]
- 总计：[待统计]

**版本**：v1.0（框架）
**创建日期**：2026-04-05
"""

    mapping_path = chapter_dir / "mapping.md"
    with open(mapping_path, 'w', encoding='utf-8') as f:
        f.write(mapping_content)

    # 创建eureka.md
    eureka_content = f"""# 灵感笔记 — {chapter_title}

知识提取过程中发现的跨领域洞察和创意。

---

## 待提取

请根据本章内容，提取具有跨领域启发性的洞察。

标准：
- 必须具有跨时代、跨领域的普遍性
- 能够对现代场景提供启发
- 避免简单的"古为今用"

---

**洞察统计**：[待统计]
**来源章节**：{chapter_title}
**版本**：v1.0（框架）
**创建日期**：2026-04-05
"""

    eureka_path = chapter_dir / "eureka.md"
    with open(eureka_path, 'w', encoding='utf-8') as f:
        f.write(eureka_content)

    # 创建示例fact_001.json
    fact_template = {
        "name": "placeholder",
        "description": f"{chapter_title}的核心人物与事迹（待补充）",
        "data": {
            "说明": "此为模板文件，请根据章节内容填充"
        }
    }

    fact_path = facts_dir / "fact_001.json"
    with open(fact_path, 'w', encoding='utf-8') as f:
        json.dump(fact_template, f, ensure_ascii=False, indent=2)

    # 创建示例fact_002.md
    fact_md_content = f"""---
name: placeholder
description: {chapter_title}的重要内容（待补充）
---

# [标题待补充]

## 概述

[待补充]

## 核心内容

[待补充]
"""

    fact_md_path = facts_dir / "fact_002.md"
    with open(fact_md_path, 'w', encoding='utf-8') as f:
        f.write(fact_md_content)

    # 创建示例skill_001.md
    skill_content = f"""---
name: placeholder
description: {chapter_title}的方法论（待补充）
---

## 概述

[待补充：本技能的简要说明]

## 步骤

### 1. [步骤一]

[待补充]

### 2. [步骤二]

[待补充]

## 决策点

[待补充：关键决策点]

## 预期结果

[待补充：使用本方法的预期效果]

## 适用场景

[待补充：何时使用本方法]
"""

    skill_path = skills_dir / "skill_001.md"
    with open(skill_path, 'w', encoding='utf-8') as f:
        f.write(skill_content)

    print(f"  ✓ 已创建框架：{chapter_dir}")


def main():
    """主函数"""
    print("=" * 80)
    print("《史记》062-090章节 SKU框架生成工具")
    print("=" * 80)
    print()
    print(f"将为 {len(CHAPTERS)} 个章节创建基本框架")
    print()

    for chapter_num, chapter_title in CHAPTERS:
        create_scaffold(chapter_num, chapter_title)

    print()
    print("=" * 80)
    print("框架创建完成！")
    print("=" * 80)
    print()
    print("后续步骤：")
    print("1. 阅读每章原文")
    print("2. 补充facts（人物生平、事迹、评价）")
    print("3. 补充skills（方法论、策略）")
    print("4. 提取eureka（跨领域洞察）")
    print("5. 完善mapping（使用场景）")
    print("6. 更新README统计信息")
    print()


if __name__ == "__main__":
    main()
