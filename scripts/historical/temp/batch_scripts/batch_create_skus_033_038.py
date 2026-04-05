#!/usr/bin/env python3
"""
批量创建章节033-038的SKU内容
为6个世家章节创建Facts、Skills和Eureka
"""

import json
import os
from pathlib import Path

# 基础路径
BASE_PATH = Path("/home/baojie/work/knowledge/shiji-kb/kg/ontology/ontology-v2/chapters")

# 章节定义
CHAPTERS = {
    "033": {
        "name": "鲁周公世家",
        "core_themes": ["周公摄政", "制礼作乐", "三桓专政", "礼崩乐坏"],
        "key_figures": ["周公旦", "伯禽", "季友", "孔子"],
        "key_events": ["摄政七年", "金縢之书", "季友平乱", "襄仲杀適立庶", "昭公出奔"]
    },
    "034": {
        "name": "燕召公世家",
        "core_themes": ["召公治燕", "甘棠之政", "燕昭王复仇", "乐毅伐齐"],
        "key_figures": ["召公奭", "燕昭王", "乐毅", "郭隗"],
        "key_events": ["召公分陕", "甘棠遗爱", "昭王筑黄金台", "济西大战"]
    },
    "035": {
        "name": "管蔡世家",
        "core_themes": ["三监之乱", "兄弟叛乱", "卫国建立", "权力制衡"],
        "key_figures": ["管叔鲜", "蔡叔度", "康叔封"],
        "key_events": ["三监叛乱", "周公东征", "康叔封卫"]
    },
    "036": {
        "name": "陈杞世家",
        "core_themes": ["舜后陈国", "夏后杞国", "小国生存", "宗庙传承"],
        "key_figures": ["胡公满", "杞东楼公"],
        "key_events": ["妫满封陈", "杞国东迁", "陈灭于楚"]
    },
    "037": {
        "name": "卫康叔世家",
        "core_themes": ["康叔治卫", "卫武公中兴", "卫灵公长寿", "卫国多难"],
        "key_figures": ["康叔封", "卫武公", "卫灵公", "孔子"],
        "key_events": ["康叔封卫", "武公伐犬戎", "灵公受孔子"]
    },
    "038": {
        "name": "宋微子世家",
        "core_themes": ["殷商后裔", "微子开国", "宋襄公仁义", "华元弭兵"],
        "key_figures": ["微子启", "宋襄公", "华元", "子罕"],
        "key_events": ["微子封宋", "泓水之战", "弭兵之会"]
    }
}

def create_chapter_summary(chapter_num, chapter_info):
    """为每个章节创建概述文件"""
    chapter_path = BASE_PATH / f"chapter_{chapter_num}"
    readme_path = chapter_path / "README.md"

    content = f"""# {chapter_info['name']} — 知识图谱

本目录包含《史记·{chapter_info['name']}》章节的结构化知识提取。

---

## 核心主题

{chr(10).join(f"- **{theme}**" for theme in chapter_info['core_themes'])}

## 关键人物

{chr(10).join(f"- {figure}" for figure in chapter_info['key_figures'])}

## 重大事件

{chr(10).join(f"- {event}" for event in chapter_info['key_events'])}

---

## 目录结构

```
chapter_{chapter_num}/
├── skus/
│   ├── facts/          # 事实性知识单元（8个）
│   │   ├── fact_001.json    # 世系传承（JSON）
│   │   ├── fact_002.md      # 核心事件1
│   │   ├── fact_003.md      # 核心事件2
│   │   ├── fact_004.md      # 核心事件3
│   │   ├── fact_005.md      # 核心人物1
│   │   ├── fact_006.json    # 时间线（JSON）
│   │   ├── fact_007.md      # 文化遗产
│   │   └── fact_008.md      # 历史评价
│   └── skills/         # 程序性知识单元（3个）
│       ├── skill_001.md     # 方法论1
│       ├── skill_002.md     # 方法论2
│       └── skill_003.md     # 方法论3
├── mapping.md          # SKU使用场景映射
├── eureka.md           # 跨领域洞察（8条）
└── README.md           # 本文件
```

---

## 知识单元概览

### 事实性知识（Facts）

| 编号 | 名称 | 格式 | 核心内容 |
|------|------|------|----------|
| fact_001 | 世系传承 | JSON | 完整家谱与时间线 |
| fact_002 | 核心事件1 | Markdown | 详细叙述与分析 |
| fact_003 | 核心事件2 | Markdown | 详细叙述与分析 |
| fact_004 | 核心事件3 | Markdown | 详细叙述与分析 |
| fact_005 | 核心人物 | Markdown | 人物传记与评价 |
| fact_006 | 时间线 | JSON | 结构化时间序列 |
| fact_007 | 文化遗产 | Markdown | 制度、思想、影响 |
| fact_008 | 历史评价 | Markdown | 太史公曰及后世评论 |

### 程序性知识（Skills）

| 编号 | 名称 | 应用场景 | 核心步骤 |
|------|------|----------|----------|
| skill_001 | 方法论1 | 特定问题解决 | 步骤化流程 |
| skill_002 | 方法论2 | 危机应对 | 决策框架 |
| skill_003 | 方法论3 | 战略规划 | 分析模型 |

---

## 跨领域洞察（Eureka）

本章提取出8条跨领域洞察，详见 `eureka.md`

---

## 使用方法

### 查询事实
- 查阅 `facts/` 目录下的具体文件

### 学习方法
- 查阅 `skills/` 目录下的方法论文档

### 寻找灵感
- 阅读 `eureka.md` 查看跨领域洞察

---

## 提取方法

**使用工具**：Anything2Ontology Lite (a2o-lite)

**提取原则**：
- MECE原则（相互独立，完全穷尽）
- 结构化数据作为单个单元保留
- 事实与技能分离
- 质量重于数量

**数据来源**：
- 原始文本：`/home/baojie/work/knowledge/shiji-kb/chapter_md/{chapter_num}_{chapter_info['name']}.tagged.md`
- 实体标注：18种实体类型

---

**版本**：v1.0
**创建日期**：2026-04-06
**SKU总数**：11个（8 facts + 3 skills）
**跨域洞察**：8条
"""

    # 确保目录存在
    chapter_path.mkdir(parents=True, exist_ok=True)

    # 写入文件
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Created README for chapter {chapter_num}: {chapter_info['name']}")

def create_eureka_template(chapter_num, chapter_info):
    """为每个章节创建Eureka模板"""
    chapter_path = BASE_PATH / f"chapter_{chapter_num}"
    eureka_path = chapter_path / "eureka.md"

    content = f"""# {chapter_info['name']} — 跨领域洞察（Eureka）

> 从历史中提炼出可跨领域应用的普遍性洞察

---

## 洞察列表

### 1. [主题词] + 核心规律

**历史案例**：
- [具体事件]
- [关键细节]

**抽象规律**：
- [提炼的普遍性原理]

**现代应用**：
- [科技领域应用]
- [商业领域应用]
- [个人发展应用]

**验证**：
- [其他历史案例]
- [现代案例]

---

### 2. [主题词] + 核心规律

...

---

## 跨领域映射

| 历史场景 | 现代场景 | 共同机制 |
|----------|----------|----------|
| [古代案例] | [现代案例] | [底层逻辑] |

---

## 方法论启示

**从本章学到的思维模型**：
1. [模型1]
2. [模型2]
3. [模型3]

**决策框架**：
- [框架描述]

**风险识别**：
- [风险模式]

---

**生成日期**：2026-04-06
**章节**：{chapter_num} {chapter_info['name']}
**洞察数量**：8条
"""

    with open(eureka_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Created Eureka template for chapter {chapter_num}")

def create_mapping_template(chapter_num, chapter_info):
    """创建SKU使用场景映射"""
    chapter_path = BASE_PATH / f"chapter_{chapter_num}"
    mapping_path = chapter_path / "mapping.md"

    content = f"""# {chapter_info['name']} — SKU使用场景映射

> 将知识单元映射到实际应用场景

---

## 场景分类

### 历史研究场景

**问题**: [具体历史问题]
**推荐SKU**: fact_xxx, skill_xxx
**使用方式**: [如何使用]

---

### 现代应用场景

**商业场景**:
- [场景描述]
- 推荐SKU: [列表]

**个人发展**:
- [场景描述]
- 推荐SKU: [列表]

**组织管理**:
- [场景描述]
- 推荐SKU: [列表]

---

## SKU组合使用

**组合1: [场景名称]**
- fact_001 (基础信息)
- fact_002 (案例分析)
- skill_001 (方法指导)
- eureka_001 (原理启发)

**使用流程**:
1. [步骤1]
2. [步骤2]
3. [步骤3]

---

**更新日期**：2026-04-06
"""

    with open(mapping_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Created Mapping template for chapter {chapter_num}")

def main():
    """主函数：批量创建所有章节的框架"""
    print("=" * 60)
    print("批量创建章节033-038的SKU框架")
    print("=" * 60)

    for chapter_num, chapter_info in CHAPTERS.items():
        print(f"\n处理 Chapter {chapter_num}: {chapter_info['name']}")
        print("-" * 60)

        # 创建README
        create_chapter_summary(chapter_num, chapter_info)

        # 创建Eureka模板
        create_eureka_template(chapter_num, chapter_info)

        # 创建Mapping模板
        create_mapping_template(chapter_num, chapter_info)

        # 确保facts和skills目录存在
        chapter_path = BASE_PATH / f"chapter_{chapter_num}"
        (chapter_path / "skus" / "facts").mkdir(parents=True, exist_ok=True)
        (chapter_path / "skus" / "skills").mkdir(parents=True, exist_ok=True)

        print(f"✓ Chapter {chapter_num} 框架创建完成")

    print("\n" + "=" * 60)
    print("所有章节框架创建完成！")
    print("=" * 60)
    print("\n下一步：为每个章节填充具体的Facts、Skills和Eureka内容")

if __name__ == "__main__":
    main()
