#!/usr/bin/env python3
"""
批量处理史记章节的a2o-lite知识提取
用于021-030章节的SKU生成
"""

import os
import json
from pathlib import Path

# 章节配置
CHAPTERS = {
    "021": {
        "title": "建元已来王子侯者年表",
        "type": "表",
        "facts_count": 3,
        "skills_count": 1,
    },
    "022": {
        "title": "汉兴以来将相名臣年表",
        "type": "表",
        "facts_count": 3,
        "skills_count": 1,
    },
    "023": {
        "title": "礼书",
        "type": "书",
        "facts_count": 5,
        "skills_count": 2,
    },
    "024": {
        "title": "乐书",
        "type": "书",
        "facts_count": 5,
        "skills_count": 2,
    },
    "025": {
        "title": "律书",
        "type": "书",
        "facts_count": 5,
        "skills_count": 2,
    },
    "026": {
        "title": "历书",
        "type": "书",
        "facts_count": 6,
        "skills_count": 3,
    },
    "027": {
        "title": "天官书",
        "type": "书",
        "facts_count": 8,
        "skills_count": 2,
    },
    "028": {
        "title": "封禅书",
        "type": "书",
        "facts_count": 6,
        "skills_count": 2,
    },
    "029": {
        "title": "河渠书",
        "type": "书",
        "facts_count": 5,
        "skills_count": 3,
    },
    "030": {
        "title": "平准书",
        "type": "书",
        "facts_count": 6,
        "skills_count": 2,
    },
}

BASE_DIR = Path("/home/baojie/work/knowledge/shiji-kb")
OUTPUT_DIR = BASE_DIR / "kg/ontology/ontology-v2/chapters"


def create_chapter_structure(chapter_num: str, chapter_info: dict):
    """创建章节目录结构"""
    chapter_dir = OUTPUT_DIR / f"chapter_{chapter_num}"

    # 创建目录
    chapter_dir.mkdir(parents=True, exist_ok=True)
    (chapter_dir / "skus" / "facts").mkdir(parents=True, exist_ok=True)
    (chapter_dir / "skus" / "skills").mkdir(parents=True, exist_ok=True)

    return chapter_dir


def generate_fact_template(chapter_num: str, fact_num: int, chapter_info: dict):
    """生成fact模板"""
    if chapter_info["type"] == "表":
        # 年表类使用JSON格式
        return {
            "name": f"chapter-{chapter_num}-fact-{fact_num:03d}",
            "description": f"{chapter_info['title']}的事实性知识单元{fact_num}",
            "data": {
                "note": "此处填充从年表中提取的结构化数据"
            }
        }
    else:
        # 书类使用Markdown格式
        return f"""---
name: chapter-{chapter_num}-fact-{fact_num:03d}
description: {chapter_info['title']}的事实性知识单元{fact_num}
---

## 概述

<!-- 简要说明这个fact包含什么内容 -->

## 详细内容

<!-- 具体的事实性知识 -->

## 来源

- 《史记·{chapter_info['title']}》
"""


def generate_skill_template(chapter_num: str, skill_num: int, chapter_info: dict):
    """生成skill模板"""
    return f"""---
name: chapter-{chapter_num}-skill-{skill_num:03d}
description: {chapter_info['title']}的程序性知识单元{skill_num}
---

## 概述

<!-- 简要说明这个skill是什么方法/技能 -->

## 步骤

### 1. 第一步

### 2. 第二步

### 3. 第三步

## 决策点

<!-- 关键决策点和考虑因素 -->

## 预期结果

<!-- 执行这个skill预期达到什么效果 -->

## 来源

- 《史记·{chapter_info['title']}》
"""


def generate_mapping(chapter_num: str, chapter_info: dict):
    """生成mapping.md"""
    facts_count = chapter_info["facts_count"]
    skills_count = chapter_info["skills_count"]

    facts_list = "\n".join([
        f"- **[factual] skus/facts/fact_{i:03d}{'json' if chapter_info['type'] == '表' else '.md'}**\n"
        f"  - **描述**：{chapter_info['title']}的事实性知识单元{i}\n"
        f"  - **使用场景**：待补充"
        for i in range(1, facts_count + 1)
    ])

    skills_list = "\n".join([
        f"- **[procedural] skus/skills/skill_{i:03d}.md**\n"
        f"  - **描述**：{chapter_info['title']}的程序性知识单元{i}\n"
        f"  - **使用场景**：待补充"
        for i in range(1, skills_count + 1)
    ])

    return f"""# SKU 映射 — {chapter_info['title']}

本文件将《史记·{chapter_info['title']}》的所有标准知识单元（SKU）映射到其使用场景。

---

## 事实性知识（Facts）

{facts_list}

## 程序性知识（Skills）

{skills_list}

---

**本章SKU统计**：
- 事实性知识单元（facts）：{facts_count}个
- 程序性知识单元（skills）：{skills_count}个
- 总计：{facts_count + skills_count}个SKU

**版本**：v1.0
**创建日期**：2026-04-05
"""


def generate_eureka(chapter_num: str, chapter_info: dict):
    """生成eureka.md"""
    return f"""# 灵感笔记 — {chapter_info['title']}

知识提取过程中发现的跨领域洞察和创意。

---

## 洞察1：标题待补充

内容待补充。[{chapter_info['title']}]

## 洞察2：标题待补充

内容待补充。[{chapter_info['title']}]

## 洞察3：标题待补充

内容待补充。[{chapter_info['title']}]

---

**洞察统计**：待补充
**来源章节**：{chapter_info['title']}
**版本**：v1.0
**创建日期**：2026-04-05
"""


def generate_readme(chapter_num: str, chapter_info: dict):
    """生成README.md"""
    facts_count = chapter_info["facts_count"]
    skills_count = chapter_info["skills_count"]
    total_count = facts_count + skills_count

    return f"""# {chapter_info['title']} — 知识图谱

本目录包含《史记·{chapter_info['title']}》章节的结构化知识提取。

---

## 目录结构

```
chapter_{chapter_num}/
├── skus/
│   ├── facts/          # 事实性知识单元（{facts_count}个）
│   └── skills/         # 程序性知识单元（{skills_count}个）
├── mapping.md          # SKU使用场景映射
├── eureka.md           # 跨领域洞察
└── README.md           # 本文件
```

---

## 知识单元概览

### 事实性知识（Facts）

| 编号 | 名称 | 格式 | 核心内容 |
|------|------|------|----------|
{chr(10).join([f"| fact_{i:03d} | 待补充 | {'JSON' if chapter_info['type'] == '表' else 'Markdown'} | 待补充 |" for i in range(1, facts_count + 1)])}

### 程序性知识（Skills）

| 编号 | 名称 | 应用场景 | 核心步骤 |
|------|------|----------|----------|
{chr(10).join([f"| skill_{i:03d} | 待补充 | 待补充 | 待补充 |" for i in range(1, skills_count + 1)])}

---

## 提取方法

**使用工具**：Anything2Ontology Lite (a2o-lite)

**提取原则**：
- MECE原则（相互独立，完全穷尽）
- 结构化数据作为单个单元保留（不拆分表格/列表）
- 事实与技能分离
- 质量重于数量

**数据来源**：
- 原始文本：`/home/baojie/work/knowledge/shiji-kb/chapter_md/{chapter_num}_{chapter_info['title']}.tagged.md`

---

**版本**：v1.0
**创建日期**：2026-04-05
**SKU总数**：{total_count}个（{facts_count} facts + {skills_count} skills）
**章节类型**：{chapter_info['type']}
"""


def process_chapter(chapter_num: str, chapter_info: dict):
    """处理单个章节"""
    print(f"处理章节 {chapter_num}: {chapter_info['title']}")

    # 创建目录结构
    chapter_dir = create_chapter_structure(chapter_num, chapter_info)

    # 生成facts
    for i in range(1, chapter_info["facts_count"] + 1):
        if chapter_info["type"] == "表":
            fact_file = chapter_dir / "skus" / "facts" / f"fact_{i:03d}.json"
            content = json.dumps(
                generate_fact_template(chapter_num, i, chapter_info),
                ensure_ascii=False,
                indent=2
            )
        else:
            fact_file = chapter_dir / "skus" / "facts" / f"fact_{i:03d}.md"
            content = generate_fact_template(chapter_num, i, chapter_info)

        fact_file.write_text(content, encoding="utf-8")

    # 生成skills
    for i in range(1, chapter_info["skills_count"] + 1):
        skill_file = chapter_dir / "skus" / "skills" / f"skill_{i:03d}.md"
        content = generate_skill_template(chapter_num, i, chapter_info)
        skill_file.write_text(content, encoding="utf-8")

    # 生成mapping.md
    mapping_file = chapter_dir / "mapping.md"
    mapping_file.write_text(generate_mapping(chapter_num, chapter_info), encoding="utf-8")

    # 生成eureka.md
    eureka_file = chapter_dir / "eureka.md"
    eureka_file.write_text(generate_eureka(chapter_num, chapter_info), encoding="utf-8")

    # 生成README.md
    readme_file = chapter_dir / "README.md"
    readme_file.write_text(generate_readme(chapter_num, chapter_info), encoding="utf-8")

    print(f"  ✓ 章节 {chapter_num} 处理完成")
    return {
        "chapter_num": chapter_num,
        "title": chapter_info["title"],
        "facts": chapter_info["facts_count"],
        "skills": chapter_info["skills_count"],
        "total": chapter_info["facts_count"] + chapter_info["skills_count"],
    }


def main():
    """主函数"""
    print("开始批量处理章节...")
    print(f"输出目录: {OUTPUT_DIR}")
    print()

    results = []
    for chapter_num, chapter_info in CHAPTERS.items():
        result = process_chapter(chapter_num, chapter_info)
        results.append(result)

    print()
    print("=" * 60)
    print("处理完成统计报告")
    print("=" * 60)
    print()
    print(f"{'章节':<6} {'标题':<20} {'Facts':<8} {'Skills':<8} {'总计':<8}")
    print("-" * 60)

    total_facts = 0
    total_skills = 0
    total_skus = 0

    for r in results:
        print(f"{r['chapter_num']:<6} {r['title']:<20} {r['facts']:<8} {r['skills']:<8} {r['total']:<8}")
        total_facts += r["facts"]
        total_skills += r["skills"]
        total_skus += r["total"]

    print("-" * 60)
    print(f"{'总计':<6} {'':<20} {total_facts:<8} {total_skills:<8} {total_skus:<8}")
    print()
    print(f"已处理章节数: {len(results)}")
    print(f"总SKU数: {total_skus} ({total_facts} facts + {total_skills} skills)")
    print()


if __name__ == "__main__":
    main()
