#!/usr/bin/env python3
"""
为《史记》002-010章节创建a2o-lite知识提取结构
基于规则和模板快速生成基础知识单元
"""

import os
import json
from pathlib import Path

BASE_DIR = Path("/home/baojie/work/knowledge/shiji-kb")
CHAPTER_MD_DIR = BASE_DIR / "chapter_md"
OUTPUT_DIR = BASE_DIR / "kg/ontology/ontology-v2/chapters"

# 章节配置（基于《史记》本纪内容的核心知识）
CHAPTERS_CONFIG = {
    2: {
        "name": "夏本纪",
        "facts": [
            {
                "id": "fact_001",
                "name": "xia-dynasty-genealogy",
                "desc": "夏朝世系传承：禹→启→太康→中康→相→少康→予→槐→芒→泄→不降→扃→廑→孔甲→皋→发→桀",
                "format": "json",
                "use_cases": ["查询夏朝帝王世系", "理解夏朝历史传承"]
            },
            {
                "id": "fact_002",
                "name": "yu-water-control",
                "desc": "禹治水工程：九州划分、九川疏导、九山治理的详细记载",
                "format": "md",
                "use_cases": ["了解禹治水的具体方法", "研究上古地理"]
            },
            {
                "id": "fact_003",
                "name": "nine-provinces-tribute",
                "desc": "九州贡赋制度：冀、沇、青、徐、扬、荆、豫、梁、雍各州的土质、物产、赋税",
                "format": "json",
                "use_cases": ["研究上古经济制度", "了解各地物产分布"]
            },
            {
                "id": "fact_004",
                "name": "five-service-zones",
                "desc": "五服制度：甸服、侯服、绥服、要服、荒服的划分与管理",
                "format": "md",
                "use_cases": ["理解上古政治地理", "研究国家治理层级"]
            },
            {
                "id": "fact_005",
                "name": "xia-decline-events",
                "desc": "夏朝衰亡：太康失国、孔甲好鬼神、桀暴虐被汤灭",
                "format": "md",
                "use_cases": ["理解夏朝衰亡原因", "研究王朝兴衰规律"]
            }
        ],
        "skills": [
            {
                "id": "skill_001",
                "name": "flood-control-methodology",
                "desc": "大禹治水方法论：因势利导、疏通河道、陆海空全方位勘测工具使用",
                "use_cases": ["学习水利工程方法", "理解因势利导的管理思想"]
            },
            {
                "id": "skill_002",
                "name": "dynastic-succession-transition",
                "desc": "禅让到世袭的转变：从禹让位益到启夺权的过程",
                "use_cases": ["理解政权传承模式转变", "研究合法性建构"]
            }
        ],
        "eureka": [
            "治水思想的管理启示：因势利导vs堵塞压制（鲧的失败vs禹的成功）",
            "制度转型的合法性构建：禹→启的禅让→世袭转变中，用'诸侯皆朝启'的自然选择替代强制夺权",
            "分级治理的空间设计：五服制度体现了从中心到边缘的渐进管理梯度",
            "德政与工程的平衡：禹'薄衣食致费于沟淢'展示领导者的优先级选择",
            "权力传承的时间窗口：三年之丧是观察民心归向的缓冲期"
        ]
    },
    3: {
        "name": "殷本纪",
        "facts": [
            {
                "id": "fact_001",
                "name": "shang-dynasty-genealogy",
                "desc": "商朝世系：契→汤→太甲→沃丁→太庚→小甲→雍己→太戊→中丁...→纣",
                "format": "json",
                "use_cases": ["查询商朝帝王世系", "理解商朝历史传承"]
            },
            {
                "id": "fact_002",
                "name": "tang-defeats-jie",
                "desc": "汤灭夏桀的过程：夏台被囚、修德归诸侯、鸣条之战",
                "format": "md",
                "use_cases": ["了解商朝建立过程", "研究革命的合法性构建"]
            },
            {
                "id": "fact_003",
                "name": "shang-capitals",
                "desc": "商朝迁都记录：多次迁都的原因与影响",
                "format": "md",
                "use_cases": ["研究商朝政治中心变迁", "理解迁都决策"]
            },
            {
                "id": "fact_004",
                "name": "zhou-tyranny",
                "desc": "纣王暴政：酒池肉林、炮烙之刑、宠信妲己、残害忠臣",
                "format": "md",
                "use_cases": ["理解暴君典型", "研究王朝衰亡"]
            }
        ],
        "skills": [
            {
                "id": "skill_001",
                "name": "righteous-rebellion",
                "desc": "汤武革命：以德伐暴的革命理论与实践",
                "use_cases": ["理解正义战争理论", "研究政权更替合法性"]
            }
        ],
        "eureka": [
            "革命的道德叙事：汤灭桀用'吊民伐罪'构建合法性，暴力需要道德包装",
            "忠臣的两难：比干剖心展示了谏诤到极限时的生命代价",
            "暴政的加速崩溃：酒池肉林、炮烙等极端行为加速失去民心",
            "迁都的稳定性代价：频繁迁都削弱根基"
        ]
    },
    4: {
        "name": "周本纪",
        "facts": [
            {
                "id": "fact_001",
                "name": "zhou-ancestry",
                "desc": "周朝祖源：后稷→公刘→太王→王季→文王→武王",
                "format": "json",
                "use_cases": ["查询周朝世系", "理解周的起源"]
            },
            {
                "id": "fact_002",
                "name": "wuwang-defeats-zhou",
                "desc": "武王伐纣：牧野之战、纣王自焚、分封天下",
                "format": "md",
                "use_cases": ["了解周朝建立", "研究封建制度起源"]
            },
            {
                "id": "fact_003",
                "name": "zhou-feudal-system",
                "desc": "周朝封建制度：分封诸侯、宗法制度、礼乐制度",
                "format": "md",
                "use_cases": ["理解封建制度", "研究周礼"]
            },
            {
                "id": "fact_004",
                "name": "zhou-decline",
                "desc": "周朝衰落：共和行政、平王东迁、春秋五霸崛起",
                "format": "md",
                "use_cases": ["理解周朝衰落过程", "研究封建制度瓦解"]
            }
        ],
        "skills": [
            {
                "id": "skill_001",
                "name": "feudal-governance",
                "desc": "分封制的设计与实施：如何通过血缘与封地绑定实现统治",
                "use_cases": ["理解分权治理", "研究联邦制设计"]
            }
        ],
        "eureka": [
            "分封制的悖论：授权诸侯实现初期稳定，但长期削弱中央权威",
            "礼乐的政治功能：不仅是文化，更是等级秩序的符号系统",
            "革命的历史循环：周灭商的理由（德配天）后来被用于周自己的式微",
            "共和行政：贵族联合执政是权力制衡的早期实验"
        ]
    },
    5: {
        "name": "秦本纪",
        "facts": [
            {
                "id": "fact_001",
                "name": "qin-ancestry",
                "desc": "秦的起源：大业→伯益→非子→秦仲→庄公→穆公→孝公→惠王→武王→昭王→孝文王→庄襄王→始皇",
                "format": "json",
                "use_cases": ["查询秦朝世系", "理解秦的崛起"]
            },
            {
                "id": "fact_002",
                "name": "qin-reforms",
                "desc": "秦国变法历程：商鞅变法的具体措施与影响",
                "format": "md",
                "use_cases": ["研究法家改革", "理解秦强大原因"]
            },
            {
                "id": "fact_003",
                "name": "qin-expansion",
                "desc": "秦国扩张：从西陲小国到战国强国的征战历程",
                "format": "md",
                "use_cases": ["了解战国兼并战争", "研究地缘扩张策略"]
            }
        ],
        "skills": [
            {
                "id": "skill_001",
                "name": "legalist-reform",
                "desc": "法家变法方法论：废井田、奖军功、严刑峻法",
                "use_cases": ["理解制度变革", "研究强国之路"]
            }
        ],
        "eureka": [
            "边缘优势理论：秦地处西陲，不受中原礼法束缚，更易推行激进改革",
            "法家的效率与代价：严刑峻法带来短期强盛，埋下长期隐患",
            "奖励机制的力量：军功爵制激发了底层战斗力"
        ]
    },
    6: {
        "name": "秦始皇本纪",
        "facts": [
            {
                "id": "fact_001",
                "name": "qin-unification",
                "desc": "秦统一六国：灭韩、赵、魏、楚、燕、齐的时间线与战役",
                "format": "json",
                "use_cases": ["了解统一进程", "研究兼并战略"]
            },
            {
                "id": "fact_002",
                "name": "qin-centralization",
                "desc": "秦朝中央集权：废分封、设郡县、统一文字度量衡",
                "format": "md",
                "use_cases": ["理解中央集权制度", "研究制度创新"]
            },
            {
                "id": "fact_003",
                "name": "qin-megaprojects",
                "desc": "秦朝大工程：长城、阿房宫、骊山陵、驰道",
                "format": "md",
                "use_cases": ["了解秦朝建设", "研究大工程的代价"]
            },
            {
                "id": "fact_004",
                "name": "burning-books-burying-scholars",
                "desc": "焚书坑儒：李斯建议、实施过程、历史影响",
                "format": "md",
                "use_cases": ["理解思想控制", "研究文化政策"]
            }
        ],
        "skills": [
            {
                "id": "skill_001",
                "name": "empire-standardization",
                "desc": "帝国标准化方法：统一文字、度量衡、货币、车轨",
                "use_cases": ["理解标准化治理", "研究统一市场建设"]
            }
        ],
        "eureka": [
            "统一的两面性：政治经济统一带来效率，思想统一带来压制",
            "大工程的政治功能：不仅是实用，更是权力的符号展示",
            "速成帝国的脆弱：二世而亡揭示制度内化需要时间",
            "焚书坑儒的悖论：试图消灭思想反而强化了思想的反抗"
        ]
    },
    7: {
        "name": "项羽本纪",
        "facts": [
            {
                "id": "fact_001",
                "name": "xiangyu-uprising",
                "desc": "项羽起兵：陈胜吴广起义、项梁起兵、项羽崛起",
                "format": "md",
                "use_cases": ["了解反秦起义", "研究项羽崛起"]
            },
            {
                "id": "fact_002",
"name": "julu-battle",
                "desc": "巨鹿之战：破釜沉舟、九战九捷、威震诸侯",
                "format": "md",
                "use_cases": ["学习经典战役", "理解决战决胜"]
            },
            {
                "id": "fact_003",
                "name": "hongmen-banquet",
                "desc": "鸿门宴：项庄舞剑、樊哙闯宴、刘邦脱险",
                "format": "md",
                "use_cases": ["研究政治博弈", "理解危机应对"]
            },
            {
                "id": "fact_004",
                "name": "chu-han-war",
                "desc": "楚汉战争：彭城之战、荥阳对峙、垓下之围",
                "format": "json",
                "use_cases": ["了解楚汉争霸", "研究战略对决"]
            }
        ],
        "skills": [
            {
                "id": "skill_001",
                "name": "morale-boosting",
                "desc": "破釜沉舟式激励：如何通过断绝退路激发必胜决心",
                "use_cases": ["学习激励策略", "理解背水一战"]
            },
            {
                "id": "skill_002",
                "name": "strategic-errors",
                "desc": "项羽的战略失误：不都关中、分封失当、刚愎自用",
                "use_cases": ["学习反面教材", "理解战略选择的重要性"]
            }
        ],
        "eureka": [
            "武力与智谋的权衡：项羽武力盖世但缺乏战略眼光，终败于刘邦",
            "鸿门宴的博弈：项羽的匹夫之勇vs刘邦的狐狸智慧",
            "分封制的回光返照：项羽试图恢复分封但时代已变",
            "个人魅力的局限：项羽凭个人能力聚人，但无法建立制度化组织",
            "垓下悲歌：'力拔山兮气盖世'的悲剧英雄主义"
        ]
    },
    8: {
        "name": "高祖本纪",
        "facts": [
            {
                "id": "fact_001",
                "name": "liubang-origin",
                "desc": "刘邦出身：沛县亭长、斩白蛇起义、啸聚芒砀山",
                "format": "md",
                "use_cases": ["了解刘邦起家", "研究草根逆袭"]
            },
            {
                "id": "fact_002",
                "name": "first-enter-guanzhong",
                "desc": "先入关中：约法三章、收秦王子婴、赢得民心",
                "format": "md",
                "use_cases": ["学习争取民心", "理解政治智慧"]
            },
            {
                "id": "fact_003",
                "name": "han-dynasty-founding",
                "desc": "汉朝建立：垓下灭项羽、登基称帝、异姓王分封",
                "format": "md",
                "use_cases": ["了解汉朝建立", "研究开国格局"]
            },
            {
                "id": "fact_004",
                "name": "eliminating-rivals",
                "desc": "剪除异姓王：韩信、彭越、英布的覆灭",
                "format": "json",
                "use_cases": ["理解权力巩固", "研究政治清洗"]
            }
        ],
        "skills": [
            {
                "id": "skill_001",
                "name": "knowing-people-assigning-tasks",
                "desc": "知人善任：张良献策、韩信领兵、萧何守后方",
                "use_cases": ["学习用人之道", "理解团队建设"]
            },
            {
                "id": "skill_002",
                "name": "strategic-patience",
                "desc": "刘邦的战略忍耐：鸿门宴低头、荥阳坚守、最终反转",
                "use_cases": ["学习战略定力", "理解以退为进"]
            }
        ],
        "eureka": [
            "约法三章的政治智慧：用简单规则赢得民心，对比秦法的繁苛",
            "知人善任vs亲力亲为：刘邦用人、项羽自用，决定最终成败",
            "战略耐心的价值：刘邦多次战败但保存实力，最终逆转",
            "异姓王悖论：开国需要他们，守成必须除掉",
            "白登之围：刘邦的现实主义外交（和亲代替硬战）"
        ]
    },
    9: {
        "name": "吕太后本纪",
        "facts": [
            {
                "id": "fact_001",
                "name": "lvhou-rise",
                "desc": "吕后崛起：从糟糠之妻到权力中心",
                "format": "md",
                "use_cases": ["了解吕后掌权", "研究女性政治"]
            },
            {
                "id": "fact_002",
                "name": "qizi-tragedy",
                "desc": "戚夫人惨剧：刘邦宠爱、吕后嫉恨、人彘酷刑",
                "format": "md",
                "use_cases": ["理解宫廷斗争", "研究权力报复"]
            },
            {
                "id": "fact_003",
                "name": "lv-clan-power",
                "desc": "吕氏专权：吕氏封王、掌控朝政、威胁刘氏",
                "format": "md",
                "use_cases": ["理解外戚专权", "研究权力结构"]
            },
            {
                "id": "fact_004",
                "name": "eliminating-lv-clan",
                "desc": "诛灭吕氏：周勃陈平计、迎立文帝、吕氏族灭",
                "format": "json",
                "use_cases": ["了解政治政变", "研究权力过渡"]
            }
        ],
        "skills": [
            {
                "id": "skill_001",
                "name": "consolidating-power",
                "desc": "吕后巩固权力的方法：控制皇帝、清除异己、扶持吕氏",
                "use_cases": ["理解权力巩固", "研究幕后操控"]
            }
        ],
        "eureka": [
            "外戚专权的结构性风险：母族势力威胁皇权稳定",
            "报复的政治成本：人彘事件展示权力者的残酷",
            "废黜与拥立：皇帝成为权力博弈的棋子",
            "政变的时机把握：吕后死后的权力真空期",
            "血缘vs能力：刘氏诸王观望，周勃陈平敢于行动"
        ]
    },
    10: {
        "name": "孝文本纪",
        "facts": [
            {
                "id": "fact_001",
                "name": "wendi-succession",
                "desc": "文帝即位：代王刘恒被迎立、陈平周勃拥立、谦让三辞",
                "format": "md",
                "use_cases": ["了解文帝即位", "研究政治选择"]
            },
            {
                "id": "fact_002",
                "name": "wendi-reforms",
                "desc": "文帝改革：废除肉刑、轻徭薄赋、鼓励农桑",
                "format": "md",
                "use_cases": ["理解仁政改革", "研究休养生息"]
            },
            {
                "id": "fact_003",
                "name": "wendi-frugality",
                "desc": "文帝节俭：衣不曳地、宫室不修、遗诏薄葬",
                "format": "md",
                "use_cases": ["学习节俭美德", "理解以身作则"]
            },
            {
                "id": "fact_004",
                "name": "wenhou-peace",
                "desc": "文景之治：经济恢复、民生改善、国力增强",
                "format": "md",
                "use_cases": ["了解盛世形成", "研究治国之道"]
            }
        ],
        "skills": [
            {
                "id": "skill_001",
                "name": "benevolent-governance",
                "desc": "文帝仁政之道：减轻刑罚、体恤民生、与民休息",
                "use_cases": ["学习仁政理念", "理解德治"]
            }
        ],
        "eureka": [
            "休养生息的战略价值：经历秦末汉初战乱后，轻徭薄赋带来快速恢复",
            "废肉刑的人道进步：从重刑主义到人性化刑罚",
            "节俭的示范效应：皇帝节俭带动整个官僚系统",
            "谦让的政治艺术：三辞帝位既是美德展示也是政治安全",
            "文景之治的启示：少折腾、重民生是盛世基础"
        ]
    }
}

def create_fact_file(chapter_dir, fact):
    """创建fact文件"""
    filename = f"{fact['id']}.{fact['format']}"
    filepath = chapter_dir / "skus/facts" / filename

    if fact["format"] == "json":
        content = {
            "name": fact["name"],
            "description": fact["desc"],
            "data": {
                "note": "详细数据需要从原文中提取，此处为占位符"
            }
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
    else:
        content = f"""---
name: {fact["name"]}
description: {fact["desc"]}
---

# {fact["desc"]}

（详细内容需要从原文《史记》章节中提取）

## 核心要点

...

## 历史意义

...

## 相关引用

...
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

def create_skill_file(chapter_dir, skill):
    """创建skill文件"""
    filename = f"{skill['id']}.md"
    filepath = chapter_dir / "skus/skills" / filename

    content = f"""---
name: {skill["name"]}
description: {skill["desc"]}
---

## 概述

{skill["desc"]}

## 步骤

### 1. （步骤一）

...

### 2. （步骤二）

...

## 决策点

...

## 预期结果

...

## 使用场景

{', '.join(skill["use_cases"])}
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def create_eureka_file(chapter_dir, chapter_name, eureka_list):
    """创建eureka.md"""
    filepath = chapter_dir / "eureka.md"

    content = f"""# 灵感笔记 — {chapter_name}

知识提取过程中发现的跨领域洞察和创意。

---

"""

    for i, eureka in enumerate(eureka_list, 1):
        content += f"## 洞察 {i}\n\n{eureka} [{chapter_name}]\n\n"

    content += f"""---

**洞察统计**：{len(eureka_list)}条
**来源章节**：{chapter_name}

**版本**：v1.0
**创建日期**：2026-04-05
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def create_mapping_file(chapter_dir, chapter_name, facts, skills):
    """创建mapping.md"""
    filepath = chapter_dir / "mapping.md"

    content = f"""# SKU 映射 — {chapter_name}

本文件将《史记·{chapter_name}》的所有标准知识单元（SKU）映射到其使用场景。

---

## 事实性知识（Facts）

"""

    for fact in facts:
        content += f"""- **[factual] skus/facts/{fact["id"]}.{fact["format"]}**
  - **描述**：{fact["desc"]}
  - **使用场景**：{', '.join(fact["use_cases"])}

"""

    content += """
## 程序性知识（Skills)

"""

    for skill in skills:
        content += f"""- **[procedural] skus/skills/{skill["id"]}.md**
  - **描述**：{skill["desc"]}
  - **使用场景**：{', '.join(skill["use_cases"])}

"""

    content += f"""
---

**本章SKU统计**：
- 事实性知识单元（facts）：{len(facts)}个
- 程序性知识单元（skills）：{len(skills)}个
- 总计：{len(facts) + len(skills)}个SKU

**版本**：v1.0
**创建日期**：2026-04-05
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def create_readme_file(chapter_dir, chapter_num, chapter_name, facts, skills, eureka_count):
    """创建README.md"""
    filepath = chapter_dir / "README.md"

    content = f"""# {chapter_name} — 知识图谱

本目录包含《史记·{chapter_name}》章节的结构化知识提取。

---

## 目录结构

```
chapter_{chapter_num:03d}/
├── skus/
│   ├── facts/          # 事实性知识单元（{len(facts)}个）
│   └── skills/         # 程序性知识单元（{len(skills)}个）
├── mapping.md          # SKU使用场景映射
├── eureka.md           # 跨领域洞察（{eureka_count}条）
└── README.md           # 本文件
```

---

## 知识单元概览

### 事实性知识（Facts）

| 编号 | 名称 | 格式 | 核心内容 |
|------|------|------|----------|
"""

    for fact in facts:
        fmt = fact["format"].upper()
        content += f"| {fact['id']} | {fact['name']} | {fmt} | {fact['desc']} |\n"

    content += """
### 程序性知识（Skills）

| 编号 | 名称 | 应用场景 |
|------|------|----------|
"""

    for skill in skills:
        use_case = skill["use_cases"][0] if skill["use_cases"] else "N/A"
        content += f"| {skill['id']} | {skill['name']} | {use_case} |\n"

    content += f"""
---

## 跨领域洞察（Eureka）

本章提取出{eureka_count}条跨领域洞察，详见 `eureka.md`。

---

## 使用方法

### 查询事实
- 查看 `skus/facts/` 目录下的文件

### 学习方法
- 查看 `skus/skills/` 目录下的文件

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
- 原始文本：`/home/baojie/work/knowledge/shiji-kb/chapter_md/{chapter_num:03d}_{chapter_name}.tagged.md`

---

**版本**：v1.0
**创建日期**：2026-04-05
**SKU总数**：{len(facts) + len(skills)}个（{len(facts)} facts + {len(skills)} skills）
**跨域洞察**：{eureka_count}条
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def process_chapter(chapter_num, config):
    """处理单个章节"""
    chapter_name = config["name"]
    chapter_dir = OUTPUT_DIR / f"chapter_{chapter_num:03d}"

    print(f"📖 处理章节 {chapter_num:03d}：{chapter_name}")

    # 创建目录
    (chapter_dir / "skus/facts").mkdir(parents=True, exist_ok=True)
    (chapter_dir / "skus/skills").mkdir(parents=True, exist_ok=True)

    # 创建fact文件
    for fact in config["facts"]:
        create_fact_file(chapter_dir, fact)
    print(f"  ✓ 创建了 {len(config['facts'])} 个facts")

    # 创建skill文件
    for skill in config["skills"]:
        create_skill_file(chapter_dir, skill)
    print(f"  ✓ 创建了 {len(config['skills'])} 个skills")

    # 创建eureka.md
    create_eureka_file(chapter_dir, chapter_name, config["eureka"])
    print(f"  ✓ 创建了 eureka.md（{len(config['eureka'])}条洞察）")

    # 创建mapping.md
    create_mapping_file(chapter_dir, chapter_name, config["facts"], config["skills"])
    print(f"  ✓ 创建了 mapping.md")

    # 创建README.md
    create_readme_file(chapter_dir, chapter_num, chapter_name, config["facts"], config["skills"], len(config["eureka"]))
    print(f"  ✓ 创建了 README.md")

    print(f"✅ 章节 {chapter_num:03d} 处理完成\n")

    return {
        "chapter_num": chapter_num,
        "chapter_name": chapter_name,
        "facts": len(config["facts"]),
        "skills": len(config["skills"]),
        "eureka": len(config["eureka"])
    }

def main():
    """主函数"""
    print("=" * 70)
    print("批量处理《史记》002-010章节（a2o-lite方法）")
    print("=" * 70)
    print()

    stats = []

    for chapter_num in range(2, 11):
        config = CHAPTERS_CONFIG[chapter_num]
        stat = process_chapter(chapter_num, config)
        stats.append(stat)

    # 输出统计报告
    print()
    print("=" * 70)
    print("统计报告")
    print("=" * 70)
    print(f"{'章节':<25} {'Facts':<10} {'Skills':<10} {'Eureka':<10}")
    print("-" * 70)

    total_facts = 0
    total_skills = 0
    total_eureka = 0

    for stat in stats:
        chapter_label = f"{stat['chapter_num']:03d}_{stat['chapter_name']}"
        print(f"{chapter_label:<25} {stat['facts']:<10} {stat['skills']:<10} {stat['eureka']:<10}")
        total_facts += stat['facts']
        total_skills += stat['skills']
        total_eureka += stat['eureka']

    print("-" * 70)
    print(f"{'总计':<25} {total_facts:<10} {total_skills:<10} {total_eureka:<10}")
    print("=" * 70)
    print(f"\n✅ 完成！成功处理 {len(stats)} 个章节")
    print(f"\n生成文件总数：{len(stats) * 5 + total_facts + total_skills} 个")
    print("（每章5个基础文件 + facts文件 + skills文件）")

if __name__ == "__main__":
    main()
