#!/usr/bin/env python3
"""
为《史记》章节创建a2o-lite知识提取的脚手架结构。

这个脚本只创建目录结构和模板文件，不执行实际的知识提取。
知识提取需要人工或通过Claude API逐章完成。

用法:
    python scripts/create_chapter_scaffolds.py 091 120
"""

import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
CHAPTER_MD_DIR = PROJECT_ROOT / "chapter_md"
OUTPUT_BASE_DIR = PROJECT_ROOT / "kg" / "ontology" / "ontology-v2" / "chapters"

def get_chapter_info(chapter_num):
    """获取章节信息"""
    pattern = f"{chapter_num:03d}_*.tagged.md"
    files = list(CHAPTER_MD_DIR.glob(pattern))
    if not files:
        return None

    # 提取章节名称
    title = files[0].stem.replace('.tagged', '').replace(f'{chapter_num:03d}_', '')
    return title

def create_scaffold(chapter_num):
    """为单个章节创建脚手架"""
    title = get_chapter_info(chapter_num)
    if not title:
        print(f"  ✗ 章节 {chapter_num:03d} 未找到")
        return False

    chapter_dir = OUTPUT_BASE_DIR / f"chapter_{chapter_num:03d}"
    facts_dir = chapter_dir / "skus" / "facts"
    skills_dir = chapter_dir / "skus" / "skills"

    # 创建目录
    facts_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    # 创建README.md模板
    readme_path = chapter_dir / "README.md"
    if not readme_path.exists():
        readme_content = f"""# {title} — 知识图谱

本目录包含《史记·{title}》章节的结构化知识提取。

---

## 目录结构

```
chapter_{chapter_num:03d}/
├── skus/
│   ├── facts/          # 事实性知识单元
│   └── skills/         # 程序性知识单元
├── mapping.md          # SKU使用场景映射
├── eureka.md           # 跨领域洞察
└── README.md           # 本文件
```

---

## 知识单元概览

### 事实性知识（Facts）

待提取

### 程序性知识（Skills）

待提取

---

## 跨领域洞察（Eureka）

待提取

---

**版本**：v1.0 (scaffold)
**创建日期**：2026-04-05
**状态**：待完成
**原文位置**：`chapter_md/{chapter_num:03d}_{title}.tagged.md`

---

## 提取指南

本章为列传类章节，重点提取：

1. **Facts（事实性知识）**：
   - 人物生平轨迹
   - 核心历史事件
   - 重要人物关系
   - 思想主张与评价
   - 结构化数据（家族、官职、战役等）

2. **Skills（程序性知识）**：
   - 可复用的策略方法
   - 决策过程分析
   - 历史经验提炼

3. **Eureka（跨领域洞察）**：
   - 只包含真正跨领域的深刻洞察
   - 质量重于数量
"""
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

    # 创建mapping.md模板
    mapping_path = chapter_dir / "mapping.md"
    if not mapping_path.exists():
        mapping_content = f"""# SKU 映射 — {title}

本文件将《史记·{title}》的所有标准知识单元（SKU）映射到其使用场景。

---

## 使用说明

在完成知识提取后，在此处按主题分组列出所有SKU及其使用场景。

格式示例：

## 主题名称

- **[factual] skus/facts/fact_001.json**
  - **描述**：xxx
  - **使用场景**：当用户询问xxx时调用

- **[procedural] skus/skills/skill_001.md**
  - **描述**：xxx
  - **使用场景**：当用户询问xxx时调用

---

**待补充**
"""
        with open(mapping_path, 'w', encoding='utf-8') as f:
            f.write(mapping_content)

    # 创建eureka.md模板
    eureka_path = chapter_dir / "eureka.md"
    if not eureka_path.exists():
        eureka_content = f"""# 灵感笔记 — {title}

知识提取过程中发现的跨领域洞察和创意。

---

## 洞察提取指南

跨领域洞察应当满足以下条件：
1. **跨领域性**：可应用于现代组织管理、决策、人际关系等领域
2. **深刻性**：揭示了某种普遍规律或悖论
3. **可迁移性**：能够启发现代场景的思考

每条洞察包含：
- **标题**：简明扼要的主题
- **内容**：详细阐述洞察内容及其现代应用场景

---

**待补充**

---

**洞察统计**：待补充
**来源章节**：{title}
"""
        with open(eureka_path, 'w', encoding='utf-8') as f:
            f.write(eureka_content)

    # 创建示例fact和skill模板（供参考）
    example_fact_path = facts_dir / "_TEMPLATE_fact.md"
    if not example_fact_path.exists():
        example_fact = """---
name: 简短名称（kebab-case）
description: 详细描述此知识单元的内容
---

## 概述

简要说明这个事实性知识的核心内容。

## 详细内容

### 小节1

内容...

### 小节2

内容...

## 相关引用

引用原文中的关键段落（可选）。
"""
        with open(example_fact_path, 'w', encoding='utf-8') as f:
            f.write(example_fact)

    example_skill_path = skills_dir / "_TEMPLATE_skill.md"
    if not example_skill_path.exists():
        example_skill = """---
name: 简短名称（kebab-case）
description: 详细描述此程序性知识的应用场景和核心内容
---

## 概述

说明这个方法/策略的背景和适用场景。

## 步骤

### 1. 步骤名称

详细说明...

### 2. 步骤名称

详细说明...

### 3. 步骤名称

详细说明...

## 决策点

在执行过程中需要注意的关键决策点：
- 决策点1
- 决策点2

## 预期结果

说明正确执行此方法后的预期效果。

## 现代应用

这个古代方法在现代场景中的应用（可选）。
"""
        with open(example_skill_path, 'w', encoding='utf-8') as f:
            f.write(example_skill)

    print(f"  ✓ 章节 {chapter_num:03d}: {title}")
    return True

def main():
    if len(sys.argv) != 3:
        print("用法: python scripts/create_chapter_scaffolds.py <起始章节> <结束章节>")
        print("示例: python scripts/create_chapter_scaffolds.py 091 120")
        sys.exit(1)

    start_chapter = int(sys.argv[1])
    end_chapter = int(sys.argv[2])

    print(f"为章节 {start_chapter:03d} 到 {end_chapter:03d} 创建脚手架")
    print(f"总共 {end_chapter - start_chapter + 1} 个章节\n")

    success_count = 0

    for chapter_num in range(start_chapter, end_chapter + 1):
        if create_scaffold(chapter_num):
            success_count += 1

    print(f"\n{'='*60}")
    print(f"脚手架创建完成：{success_count}/{end_chapter - start_chapter + 1} 个章节")
    print(f"{'='*60}")
    print(f"\n输出目录: {OUTPUT_BASE_DIR}")
    print(f"\n下一步：")
    print(f"1. 逐章阅读原文：chapter_md/NNN_*.tagged.md")
    print(f"2. 提取知识单元到：kg/ontology/ontology-v2/chapters/chapter_NNN/skus/")
    print(f"3. 删除模板文件：_TEMPLATE_*.md")
    print(f"4. 更新README.md、mapping.md、eureka.md")

if __name__ == "__main__":
    main()
