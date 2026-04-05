#!/usr/bin/env python3
"""
批量生成092-110章节的SKU内容
"""

import os
import json
from pathlib import Path

BASE_DIR = Path("/home/baojie/work/knowledge/shiji-kb")
CHAPTERS_DIR = BASE_DIR / "kg/ontology/ontology-v2/chapters"
TAGGED_MD_DIR = BASE_DIR / "chapter_md"

# 章节配置：章节号 -> (标题, Facts数量, Skills数量, Eureka数量, 重点主题)
CHAPTER_CONFIG = {
    92: ("淮阴侯列传", 7, 3, 8, ["背水一战", "萧何月下追韩信", "韩信兵法", "功高震主"]),
    93: ("韩信卢绾列传", 5, 2, 5, ["韩王信降匈奴", "卢绾叛汉"]),
    94: ("田儋列传", 5, 2, 5, ["齐国田氏复国"]),
    95: ("樊郦滕灌列传", 6, 3, 6, ["功臣集传", "樊哙勇武", "灌婴骑兵"]),
    96: ("张丞相列传", 5, 3, 6, ["张苍历法", "周昌直谏"]),
    97: ("郦生陆贾列传", 6, 3, 7, ["郦食其说齐", "陆贾使南越"]),
    98: ("傅靳蒯成列传", 5, 2, 5, ["汉初功臣"]),
    99: ("刘敬叔孙通列传", 6, 3, 7, ["刘敬建议迁都", "叔孙通制礼仪"]),
    100: ("季布栾布列传", 6, 3, 7, ["季布一诺", "栾布哭彭越"]),
    101: ("袁盎晁错列传", 7, 3, 8, ["削藩政治", "袁盎晁错矛盾", "七国之乱"]),
    102: ("张释之冯唐列传", 6, 3, 7, ["张释之执法", "冯唐论将"]),
    103: ("万石张叔列传", 5, 2, 6, ["万石君家规", "孝谨家风"]),
    104: ("田叔列传", 5, 2, 5, ["田叔节义"]),
    105: ("扁鹊仓公列传", 8, 4, 8, ["扁鹊医术", "仓公医案", "古代诊断"]),
    106: ("吴王濞列传", 6, 2, 6, ["七国之乱全景"]),
    107: ("魏其武安侯列传", 7, 3, 7, ["窦婴田蚡争斗", "外戚斗争"]),
    108: ("韩长孺列传", 6, 3, 6, ["汉匈和亲", "外交谈判"]),
    109: ("李将军列传", 7, 3, 8, ["李广难封", "飞将军", "边塞战争"]),
    110: ("匈奴列传", 8, 4, 8, ["汉匈关系", "匈奴社会", "和亲政策", "马邑之谋"]),
}

def generate_fact_template(chapter_num, fact_num, title, theme=""):
    """生成Fact模板"""
    return f"""---
name: {title.lower().replace(' ', '-')}-fact-{fact_num:03d}
description: {title}第{fact_num}个事实性知识单元（{theme}）
---

# {theme or f"事实单元 {fact_num}"}

## 概述

待补充：简要说明这个事实性知识的核心内容。

## 详细内容

### 小节1

内容...

### 小节2

内容...

## 相关引用

引用原文中的关键段落（可选）。
"""

def generate_skill_template(chapter_num, skill_num, title, theme=""):
    """生成Skill模板"""
    return f"""---
name: {title.lower().replace(' ', '-')}-skill-{skill_num:03d}
description: {title}第{skill_num}个程序性知识单元（{theme}）
---

## 概述

待补充：说明这个方法/策略的背景和适用场景。

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

def generate_eureka_template(chapter_num, title, themes):
    """生成Eureka模板"""
    theme_list = "\n".join([f"- {t}" for t in themes])
    return f"""# 灵感笔记 — {title}

知识提取过程中发现的跨领域洞察和创意。

---

## 洞察提取指南

跨领域洞察应当满足以下条件：
1. **跨领域性**：可应用于现代组织管理、决策、人际关系等领域
2. **深刻性**：揭示了某种普遍规律或悖论
3. **可迁移性**：能够启发现代场景的思考

每条洞察包含：
- **标题**：简明扼要的主题
- **内容**：详细阐述洞察内容及其现代应用场景（参考五帝本纪示例）

---

## 主题方向

本章可能的洞察主题：
{theme_list}

---

## 洞察1：标题

待补充洞察内容...

## 洞察2：标题

待补充洞察内容...

## 洞察3：标题

待补充洞察内容...

## 洞察4：标题

待补充洞察内容...

## 洞察5：标题

待补充洞察内容...

---

**洞察统计**：待补充
**来源章节**：{title}
**版本**：v1.0
**创建日期**：2026-04-05
"""

def generate_readme_template(chapter_num, title, fact_count, skill_count, eureka_count):
    """生成README模板"""
    return f"""# {title} — 知识图谱

本目录包含《史记·{title}》章节的结构化知识提取。

---

## 目录结构

```
chapter_{chapter_num:03d}/
├── skus/
│   ├── facts/          # 事实性知识单元（{fact_count}个）
│   └── skills/         # 程序性知识单元（{skill_count}个）
├── mapping.md          # SKU使用场景映射
├── eureka.md           # 跨领域洞察（{eureka_count}条）
└── README.md           # 本文件
```

---

## 知识单元概览

### 事实性知识（Facts）

| 编号 | 名称 | 核心内容 |
|------|------|----------|
待补充

### 程序性知识（Skills）

| 编号 | 名称 | 应用场景 | 核心步骤 |
|------|------|----------|----------|
待补充

---

## 跨领域洞察（Eureka）

本章提取出{eureka_count}条跨领域洞察，涵盖以下主题：

待补充

---

## 使用方法

### 查询事实
- 查阅 `skus/facts/` 目录下的Markdown文件

### 学习方法
- 查阅 `skus/skills/` 目录下的Markdown文件

### 寻找灵感
- 阅读 `eureka.md` 查看跨领域洞察

---

**版本**：v1.0
**创建日期**：2026-04-05
**SKU总数**：{fact_count + skill_count}个（{fact_count} facts + {skill_count} skills）
**跨域洞察**：{eureka_count}条
"""

def main():
    """主函数"""
    print("开始批量生成SKU框架...")

    for chapter_num, (title, fact_count, skill_count, eureka_count, themes) in CHAPTER_CONFIG.items():
        print(f"\n处理 {chapter_num:03d}_{title}...")

        chapter_dir = CHAPTERS_DIR / f"chapter_{chapter_num:03d}"
        facts_dir = chapter_dir / "skus" / "facts"
        skills_dir = chapter_dir / "skus" / "skills"

        # 确保目录存在
        facts_dir.mkdir(parents=True, exist_ok=True)
        skills_dir.mkdir(parents=True, exist_ok=True)

        # 生成Facts（仅生成模板，不覆盖已存在的文件）
        for i in range(1, fact_count + 1):
            fact_file = facts_dir / f"fact_{i:03d}.md"
            if not fact_file.exists():
                content = generate_fact_template(chapter_num, i, title, themes[0] if i == 1 and themes else "")
                fact_file.write_text(content, encoding='utf-8')
                print(f"  创建 {fact_file.name}")

        # 生成Skills
        for i in range(1, skill_count + 1):
            skill_file = skills_dir / f"skill_{i:03d}.md"
            if not skill_file.exists():
                content = generate_skill_template(chapter_num, i, title, themes[0] if i == 1 and themes else "")
                skill_file.write_text(content, encoding='utf-8')
                print(f"  创建 {skill_file.name}")

        # 生成Eureka（仅当文件为空或仅有指南时）
        eureka_file = chapter_dir / "eureka.md"
        if eureka_file.exists():
            content = eureka_file.read_text(encoding='utf-8')
            # 如果是待补充状态，则覆盖
            if "**待补充**" in content or len(content.strip()) < 500:
                content = generate_eureka_template(chapter_num, title, themes)
                eureka_file.write_text(content, encoding='utf-8')
                print(f"  更新 eureka.md")
        else:
            content = generate_eureka_template(chapter_num, title, themes)
            eureka_file.write_text(content, encoding='utf-8')
            print(f"  创建 eureka.md")

        # 生成README（如果不存在或内容简单）
        readme_file = chapter_dir / "README.md"
        if not readme_file.exists() or readme_file.stat().st_size < 500:
            content = generate_readme_template(chapter_num, title, fact_count, skill_count, eureka_count)
            readme_file.write_text(content, encoding='utf-8')
            print(f"  创建 README.md")

    print("\n✅ SKU框架生成完成！")
    print("\n下一步：")
    print("1. 根据tagged.md文件填充每个fact的具体内容")
    print("2. 提取程序性知识填充skill文件")
    print("3. 生成跨领域洞察填充eureka.md")

if __name__ == "__main__":
    main()
