#!/usr/bin/env python3
"""
为指定章节生成SKU内容（Facts、Skills、Eureka）
"""

import json
import os
from pathlib import Path

# 章节知识内容定义
CHAPTER_KNOWLEDGE = {
    "062": {
        "title": "管晏列传",
        "facts": [
            {
                "id": "001",
                "name": "管仲与鲍叔牙的知己之交",
                "description": "管仲早年贫困，常欺鲍叔，但鲍叔知其贤而善待之，后举荐管仲为齐相。管仲总结了鲍叔七次不误解自己的事迹，称'生我者父母，知我者鲍子也'。",
                "source": "管晏列传·知己之恩"
            },
            {
                "id": "002",
                "name": "管仲相齐的治国方略",
                "description": "管仲任齐相，主张'仓廪实而知礼节，衣食足而知荣辱'，通货积财，富国强兵，与俗同好恶，令顺民心。",
                "source": "管晏列传·相齐称霸"
            },
            {
                "id": "003",
                "name": "管仲的政治智慧",
                "description": "管仲善于'因祸而为福，转败而为功'，借桓公怒少姬而伐楚责包茅，借北征山戎令燕修召公之政，于柯之会劝桓公守信曹沫之约。",
                "source": "管晏列传·相齐称霸"
            },
            {
                "id": "004",
                "name": "晏子的节俭与正直",
                "description": "晏婴历事齐灵公、庄公、景公三世，以节俭力行重于齐。为相时'食不重肉，妾不衣帛'，在朝廷'国有道即顺命，无道即衡命'。",
                "source": "管晏列传·晏子事君"
            },
            {
                "id": "005",
                "name": "晏子赎越石父知礼",
                "description": "晏子赎越石父于缧绁之中却未行待客之礼，越石父要求断绝关系。晏子醒悟后延其为上客，体现'知己而有礼'的重要性。",
                "source": "管晏列传·赎士知礼"
            },
            {
                "id": "006",
                "name": "御者妻的智慧劝谏",
                "description": "晏子御者之妻见丈夫意气扬扬甚自得，对比晏子身高六尺却志念深远常自谦，劝丈夫自抑损。御者因此被晏子荐为大夫。",
                "source": "管晏列传·御者自省"
            }
        ],
        "skills": [
            {
                "id": "001",
                "name": "识人之术：鲍叔知人之道",
                "description": "如何识别他人的真实才能而非表面行为",
                "steps": [
                    "观察对方在困境中的行为动机，而非结果",
                    "理解时代和环境对个人选择的影响",
                    "区分道德小节与功业大节",
                    "敢于推荐才能在己之上者"
                ]
            },
            {
                "id": "002",
                "name": "治国之术：顺势而为",
                "description": "如何通过顺应民心和形势来实现政治目标",
                "steps": [
                    "确立基础原则：仓廪实→知礼节，衣食足→知荣辱",
                    "与俗同好恶：俗之所欲因而予之，俗之所否因而去之",
                    "善因祸而为福：将不利局面转化为战略机遇",
                    "贵轻重慎权衡：在关键时刻把握利益交换的尺度"
                ]
            },
            {
                "id": "003",
                "name": "自我修养：晏子式谦逊",
                "description": "如何在高位保持谦逊并影响他人",
                "steps": [
                    "物质节俭：身居高位而生活简朴（食不重肉，妾不衣帛）",
                    "态度谨慎：志念深远，常有以自下者",
                    "言行有度：国有道顺命，无道衡命",
                    "待士以礼：知己者必行待客之礼"
                ]
            }
        ],
        "eureka": [
            {
                "id": "001",
                "title": "真正的友谊是理解动机而非评判结果",
                "content": "管鲍之交的核心在于鲍叔理解管仲每次'失败'背后的深层原因：贪财是因为贫穷，谋事失败是时运不济，三仕三逐是不遭时，三战三走是有老母，被囚受辱是耻功名不显于天下。这种洞察力超越了对行为本身的道德评判。",
                "insight": "现代管理学中的'根因分析'（Root Cause Analysis）与此异曲同工——不要对表现打标签，要理解产生该表现的系统性原因。"
            },
            {
                "id": "002",
                "title": "最高级的政治智慧是把私利转化为公义",
                "content": "管仲将齐桓公的个人情绪（怒少姬、北征山戎、背曹沫之约）巧妙转化为'责楚包茅'、'令燕修政'、'守信诸侯'等正当行动。这是'知与之为取'——通过放弃眼前小利来获取长远大利。",
                "insight": "现代公关和战略沟通的精髓：将组织的实际动机包装成符合公众期待的叙事（narrative），从而获得合法性（legitimacy）。"
            },
            {
                "id": "003",
                "title": "经济基础决定道德水平",
                "content": "'仓廪实而知礼节，衣食足而知荣辱'揭示了物质条件与道德观念的因果关系。这与马斯洛需求层次理论一致——生理需求满足后才会追求尊重和自我实现。",
                "insight": "在设计社会政策或企业文化时，试图在基础需求未满足的情况下强调高层次价值观，往往徒劳无功。"
            },
            {
                "id": "004",
                "title": "知己的完整定义：理解+尊重",
                "content": "越石父的话揭示了'知己'的两个必要条件：理解（知我）和尊重（有礼）。晏子赎越石父体现了理解，但未行待客之礼则缺乏尊重。两者缺一不可。",
                "insight": "现代职场中的'认可'（recognition）需要'内在认可'（承认价值）和'外在认可'（给予资源/地位）双重维度。只有内在认可而无外在体现，往往导致人才流失。"
            },
            {
                "id": "005",
                "title": "自我认知的外部镜像",
                "content": "御者之妻通过对比晏子（身高六尺、志念深远）与丈夫（身高八尺、意气扬扬）让丈夫意识到自满的问题。外部观察者往往比当事人更清楚地看到反差。",
                "insight": "企业教练（coaching）和360度反馈的价值：提供他人视角，打破自我认知的盲区。"
            },
            {
                "id": "006",
                "title": "权力的最高境界是不彰显权力",
                "content": "晏子'身高不满六尺却名显诸侯'，'志念深矣常有以自下者'——真正的权力来自内在品质和战略思考，而非外在姿态。",
                "insight": "领导力研究中的'仆人式领导'（Servant Leadership）理念：最有影响力的领导者是那些将自己置于服务位置的人。"
            }
        ]
    },
    # 其他章节内容将逐个补充...
}


def generate_fact_md(chapter_num, fact):
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

- 《史记·{CHAPTER_KNOWLEDGE[chapter_num]['title']}》
- 章节：{fact['source']}
"""


def generate_skill_md(chapter_num, skill):
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

- 《史记·{CHAPTER_KNOWLEDGE[chapter_num]['title']}》
"""


def generate_eureka_md(chapter_num, eureka_list):
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

    return f"""# 灵感笔记 — {CHAPTER_KNOWLEDGE[chapter_num]['title']}

知识提取过程中发现的跨领域洞察和创意。

---

{''.join(eureka_sections)}

**洞察统计**：{len(eureka_list)}条
**来源章节**：{CHAPTER_KNOWLEDGE[chapter_num]['title']}
**版本**：v1.0
**创建日期**：2026-04-05
"""


def generate_chapter_sku(chapter_num):
    """为指定章节生成完整的SKU内容"""
    if chapter_num not in CHAPTER_KNOWLEDGE:
        print(f"章节 {chapter_num} 的内容尚未定义")
        return False

    base_dir = Path(f"/home/baojie/work/knowledge/shiji-kb/kg/ontology/ontology-v2/chapters/chapter_{chapter_num}")
    facts_dir = base_dir / "skus" / "facts"
    skills_dir = base_dir / "skus" / "skills"

    chapter_data = CHAPTER_KNOWLEDGE[chapter_num]

    # 生成Facts
    for fact in chapter_data['facts']:
        fact_file = facts_dir / f"fact_{fact['id']}.md"
        fact_content = generate_fact_md(chapter_num, fact)
        fact_file.write_text(fact_content, encoding='utf-8')
        print(f"✓ 生成: {fact_file}")

    # 生成Skills
    for skill in chapter_data['skills']:
        skill_file = skills_dir / f"skill_{skill['id']}.md"
        skill_content = generate_skill_md(chapter_num, skill)
        skill_file.write_text(skill_content, encoding='utf-8')
        print(f"✓ 生成: {skill_file}")

    # 生成Eureka
    eureka_file = base_dir / "eureka.md"
    eureka_content = generate_eureka_md(chapter_num, chapter_data['eureka'])
    eureka_file.write_text(eureka_content, encoding='utf-8')
    print(f"✓ 生成: {eureka_file}")

    return True


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        chapter = sys.argv[1].zfill(3)
        if generate_chapter_sku(chapter):
            print(f"\n✓ 章节 {chapter} 的SKU内容生成完成")
    else:
        print("用法: python generate_sku_content.py <章节号>")
        print("示例: python generate_sku_content.py 062")
