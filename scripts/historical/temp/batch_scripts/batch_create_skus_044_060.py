#!/usr/bin/env python3
"""
批量创建章节044-046和048-060的SKU框架

功能：
1. 创建完整的目录结构
2. 生成README.md模板
3. 生成eureka.md模板
4. 生成mapping.md模板
5. 创建facts和skills子目录
"""

import os
import json
from pathlib import Path

# 章节信息配置
CHAPTERS_INFO = {
    '044': {
        'title': '魏世家',
        'core_themes': ['三家分晋', '魏文侯变法', '李悝变法', '吴起治军', '魏武卒'],
        'key_figures': ['魏文侯', '李悝', '吴起', '魏武侯', '魏惠王'],
        'major_events': ['三家分晋', '李悝变法', '吴起西河之守', '魏惠王东迁大梁'],
        'insights_focus': ['变法改革的条件', '人才战略的得失', '地缘政治的制约', '盛极而衰的规律']
    },
    '045': {
        'title': '韩世家',
        'core_themes': ['三家分晋', '申不害变法', '韩非子法家', '地缘困境'],
        'key_figures': ['韩昭侯', '申不害', '韩非子', '韩王安'],
        'major_events': ['三家分晋', '申不害变法', '韩非入秦被杀', '韩国被秦灭'],
        'insights_focus': ['小国生存策略', '法家思想的演进', '地理劣势的致命性', '改革的局限性']
    },
    '046': {
        'title': '田敬仲完世家',
        'core_themes': ['田氏代齐', '齐威王强盛', '稷下学宫', '五国伐齐'],
        'key_figures': ['田完', '田成子', '齐威王', '齐宣王', '孟尝君'],
        'major_events': ['田氏代齐', '齐威王烹阿大夫', '马陵之战', '孟尝君相齐', '五国伐齐'],
        'insights_focus': ['权力更替的渐进性', '文化建设的战略价值', '人才政策的效果', '霸权的维持成本']
    },
    '048': {
        'title': '陈涉世家',
        'core_themes': ['大泽乡起义', '首倡反秦', '陈胜称王', '起义失败'],
        'key_figures': ['陈胜', '吴广', '武臣', '周文'],
        'major_events': ['大泽乡起义', '陈胜称王', '周文攻秦', '陈胜被杀'],
        'insights_focus': ['革命的发动机制', '群众运动的规律', '首义者的悲剧', '历史评价的标准']
    },
    '049': {
        'title': '外戚世家',
        'core_themes': ['外戚干政', '吕后专权', '窦太后', '王太后'],
        'key_figures': ['吕后', '吕产', '吕禄', '窦太后', '王太后'],
        'major_events': ['吕氏之乱', '周勃灌婴平乱', '窦太后立武帝', '王太后干政'],
        'insights_focus': ['外戚权力的来源', '制度漏洞的利用', '女性政治的空间', '权力制衡的失效']
    },
    '050': {
        'title': '楚元王世家',
        'core_themes': ['刘交封楚', '楚王世系', '儒家治国', '七国之乱'],
        'key_figures': ['刘交', '楚夷王', '楚王戊', '刘向'],
        'major_events': ['刘交封楚', '楚王戊参与七国之乱', '刘向校书'],
        'insights_focus': ['宗室封国的治理', '儒学的政治作用', '地方与中央的张力', '文化世家的传承']
    },
    '051': {
        'title': '荆燕世家',
        'core_themes': ['刘贾封荆', '刘泽封燕', '燕王世系', '诸侯王的命运'],
        'key_figures': ['刘贾', '刘泽', '燕王旦', '刘建'],
        'major_events': ['刘贾死于黥布之乱', '刘泽建燕国', '燕王旦谋反'],
        'insights_focus': ['边疆封国的困境', '宗室忠诚的考验', '谋反的动机与结果', '中央集权的进程']
    },
    '052': {
        'title': '齐悼惠王世家',
        'core_themes': ['刘肥封齐', '齐王世系', '七国之乱', '诸侯王削弱'],
        'key_figures': ['刘肥', '齐悼惠王', '齐王将闾', '齐孝王'],
        'major_events': ['刘肥封齐', '吕后险害刘肥', '七国之乱齐国观望'],
        'insights_focus': ['长子未立的心理', '强藩的自保策略', '坐观成败的风险', '藩国的终结过程']
    },
    '053': {
        'title': '萧相国世家',
        'core_themes': ['萧何功臣第一', '收秦图籍', '关中供给', '自污保身'],
        'key_figures': ['萧何', '曹参', '刘邦'],
        'major_events': ['收秦图籍', '举荐韩信', '关中供给', '自污以免祸'],
        'insights_focus': ['后勤的战略价值', '识人荐才的眼光', '功臣的生存智慧', '制度建设的贡献']
    },
    '054': {
        'title': '曹相国世家',
        'core_themes': ['随何功臣', '攻城略地', '齐相国', '萧规曹随'],
        'key_figures': ['曹参', '萧何', '刘邦'],
        'major_events': ['随刘邦起沛', '攻取齐地', '为齐相国', '继萧何为相'],
        'insights_focus': ['执行力的价值', '制度继承的智慧', '无为而治的适用性', '二号人物的定位']
    },
    '055': {
        'title': '留侯世家',
        'core_themes': ['张良世家', '博浪沙刺秦', '鸿门宴', '四皓立太子'],
        'key_figures': ['张良', '黄石公', '刘邦', '吕后'],
        'major_events': ['博浪沙刺秦', '鸿门宴救刘邦', '烧绝栈道', '四皓立太子'],
        'insights_focus': ['谋略的艺术', '退隐的智慧', '辅佐的分寸', '功成身退的境界']
    },
    '056': {
        'title': '陈丞相世家',
        'core_themes': ['陈平世家', '六出奇计', '反间计', '厚葬薄葬'],
        'key_figures': ['陈平', '刘邦', '周勃', '吕后'],
        'major_events': ['六出奇计', '白登之围解围', '吕氏之乱', '与周勃诛吕'],
        'insights_focus': ['谋略的底线', '权力斗争的手腕', '君臣信任的建立', '临机应变的能力']
    },
    '057': {
        'title': '绛侯周勃世家',
        'core_themes': ['周勃世家', '军功起家', '平定吕氏', '冤狱平反'],
        'key_figures': ['周勃', '陈平', '吕后', '文帝'],
        'major_events': ['从高祖起兵', '平定吕氏之乱', '为相', '下狱后平反'],
        'insights_focus': ['功臣的命运', '政治斗争的残酷', '君臣关系的脆弱', '自保的代价']
    },
    '058': {
        'title': '梁孝王世家',
        'core_themes': ['刘武封梁', '窦太后偏爱', '欲立梁王', '诛袁盎'],
        'key_figures': ['梁孝王刘武', '窦太后', '景帝', '袁盎'],
        'major_events': ['七国之乱守梁', '窦太后欲立梁王', '诛袁盎等大臣', '梁王郁郁而卒'],
        'insights_focus': ['母爱的危险性', '继承制的刚性', '权力欲望的膨胀', '宗室悲剧的根源']
    },
    '059': {
        'title': '五宗世家',
        'core_themes': ['景帝五子', '长沙王', '河间王', '临江王', '中山王'],
        'key_figures': ['长沙王发', '河间献王德', '临江王阏', '中山靖王胜'],
        'major_events': ['河间王求古书', '临江王自杀', '中山王好酒色'],
        'insights_focus': ['宗室子弟的出路', '文化传承的贡献', '藩国的式微', '皇室的分化']
    },
    '060': {
        'title': '三王世家',
        'core_themes': ['武帝三子封王', '封国制度改革', '推恩令', '元鼎建策'],
        'key_figures': ['齐怀王闳', '燕刺王旦', '广陵厉王胥'],
        'major_events': ['三子同日封王', '燕王旦谋反', '广陵王胥亦谋反', '诸侯国彻底虚化'],
        'insights_focus': ['封建制的终结', '推恩令的效果', '宗室的异化', '中央集权的完成']
    }
}

BASE_DIR = Path('/home/baojie/work/knowledge/shiji-kb/kg/ontology/ontology-v2/chapters')

def create_readme(chapter_num: str, info: dict) -> str:
    """生成README.md内容"""
    return f"""# {info['title']} — 知识图谱

本目录包含《史记·{info['title']}》章节的结构化知识提取。

---

## 核心主题

{chr(10).join(f'- **{theme}**' for theme in info['core_themes'])}

## 关键人物

{chr(10).join(f'- {fig}' for fig in info['key_figures'])}

## 重大事件

{chr(10).join(f'- {evt}' for evt in info['major_events'])}

---

## 目录结构

```
chapter_{chapter_num}/
├── skus/
│   ├── facts/          # 事实性知识单元（6-8个）
│   │   ├── fact_001.json    # 世系传承（JSON）
│   │   ├── fact_002.md      # 核心事件1
│   │   ├── fact_003.md      # 核心事件2
│   │   ├── fact_004.md      # 核心事件3
│   │   ├── fact_005.md      # 核心人物
│   │   └── fact_006.md      # 历史评价
│   └── skills/         # 程序性知识单元（2-3个）
│       ├── skill_001.md     # 方法论1
│       ├── skill_002.md     # 方法论2
│       └── skill_003.md     # 方法论3
├── mapping.md          # SKU使用场景映射
├── eureka.md           # 跨领域洞察（6-8条）
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
| fact_006 | 历史评价 | Markdown | 太史公曰及后世评论 |

### 程序性知识（Skills）

| 编号 | 名称 | 应用场景 | 核心步骤 |
|------|------|----------|----------|
| skill_001 | 方法论1 | 特定问题解决 | 步骤化流程 |
| skill_002 | 方法论2 | 危机应对 | 决策框架 |
| skill_003 | 方法论3 | 战略规划 | 分析模型 |

---

## 跨领域洞察（Eureka）

本章提取出6-8条跨领域洞察，详见 `eureka.md`

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
- 原始文本：`/home/baojie/work/knowledge/shiji-kb/chapter_md/{chapter_num}_{info['title']}.tagged.md`
- 实体标注：18种实体类型

---

**版本**：v1.0
**创建日期**：2026-04-06
**SKU总数**：待补充（目标：8-11个）
**跨域洞察**：待补充（目标：6-8条）
"""

def create_eureka(chapter_num: str, info: dict) -> str:
    """生成eureka.md内容"""
    return f"""# {info['title']} — 跨领域洞察（Eureka）

> 从历史中提炼出可跨领域应用的普遍性洞察

---

## 洞察维度

本章聚焦以下维度的跨领域洞察：

{chr(10).join(f'- **{focus}**' for focus in info['insights_focus'])}

---

## 洞察列表

### 1. [待提取] + 核心规律

**历史案例**：
- [从原文中提取具体事件]
- [关键细节和数据]

**抽象规律**：
- [提炼的普遍性原理]
- [跨时空适用的机制]

**现代应用**：
- **科技领域**：[具体应用场景]
- **商业领域**：[具体应用场景]
- **个人发展**：[具体应用场景]

**验证**：
- **其他历史案例**：[举例]
- **现代案例**：[举例]

---

### 2. [待提取] + 核心规律

...（重复结构，共6-8条）

---

## 跨领域映射表

| 历史场景 | 现代场景 | 共同机制 | 应用价值 |
|----------|----------|----------|----------|
| [古代案例1] | [现代案例1] | [底层逻辑] | [实践指导] |
| [古代案例2] | [现代案例2] | [底层逻辑] | [实践指导] |
| [古代案例3] | [现代案例3] | [底层逻辑] | [实践指导] |

---

## 方法论启示

**从本章学到的思维模型**：
1. [模型1：名称与描述]
2. [模型2：名称与描述]
3. [模型3：名称与描述]

**决策框架**：
- [框架名称]：[如何使用]

**风险识别模式**：
- [风险类型]：[识别方法]

---

## 生成说明

**数据来源**：《史记·{info['title']}》原文及标注
**提取方法**：跨领域抽象 + 现代映射
**验证标准**：历史案例 + 现代案例双重验证

---

**生成日期**：2026-04-06
**章节**：{chapter_num} {info['title']}
**洞察数量**：待完成（目标：6-8条）
**更新状态**：框架已建立，内容待补充
"""

def create_mapping(chapter_num: str, info: dict) -> str:
    """生成mapping.md内容"""
    return f"""# {info['title']} — SKU使用场景映射

> 将知识单元映射到实际应用场景

---

## 场景分类

### 历史研究场景

#### 研究问题1：[待定义]
**推荐SKU**: fact_001, fact_002
**使用方式**:
1. 先阅读fact_001了解基本世系和时间线
2. 结合fact_002深入理解关键事件
3. 交叉验证其他章节的相关记载

#### 研究问题2：[待定义]
**推荐SKU**: fact_003, skill_001
**使用方式**:
1. 通过fact_003了解具体案例
2. 用skill_001提炼方法论
3. 寻找可类比的其他历史案例

---

### 现代应用场景

#### 商业场景

**场景1：[待定义]**
- 问题描述：[具体业务问题]
- 推荐SKU：skill_001, eureka_001
- 应用步骤：
  1. [步骤1]
  2. [步骤2]
  3. [步骤3]

**场景2：[待定义]**
- 问题描述：[具体业务问题]
- 推荐SKU：fact_004, skill_002
- 应用步骤：
  1. [步骤1]
  2. [步骤2]
  3. [步骤3]

#### 个人发展场景

**场景1：[待定义]**
- 问题描述：[具体个人问题]
- 推荐SKU：skill_002, eureka_002
- 应用步骤：
  1. [步骤1]
  2. [步骤2]
  3. [步骤3]

#### 组织管理场景

**场景1：[待定义]**
- 问题描述：[具体管理问题]
- 推荐SKU：fact_005, skill_003, eureka_003
- 应用步骤：
  1. [步骤1]
  2. [步骤2]
  3. [步骤3]

---

## SKU组合使用方案

### 方案1：全面理解本章

**目标**：完整掌握本章历史内容和深层规律

**使用组合**：
1. fact_001 → 建立时空框架
2. fact_002, fact_003, fact_004 → 理解关键事件
3. fact_005 → 分析核心人物
4. skill_001, skill_002 → 提炼方法论
5. eureka.md → 跨领域启发

**预期效果**：对本章建立结构化认知，能够讲述完整故事，提炼深层规律

---

### 方案2：针对性问题解决

**目标**：用历史案例解决现代具体问题

**使用流程**：
1. 明确现代问题 → 在mapping.md中找到类似场景
2. 阅读推荐的facts → 了解历史案例细节
3. 学习推荐的skills → 提炼可操作方法
4. 参考eureka洞察 → 获得跨领域启发
5. 调整适配 → 应用到实际问题

**预期效果**：从历史中找到可借鉴的解决方案，避免重复历史错误

---

### 方案3：教学与传播

**目标**：用历史故事进行教育和传播

**使用组合**：
1. fact_002, fact_003（选择戏剧性强的事件）→ 吸引注意力
2. fact_005（选择有代表性的人物）→ 建立情感连接
3. eureka洞察 → 提炼现代意义
4. skills方法论 → 给出实践指导

**预期效果**：历史故事生动易懂，现代意义明确，听众有行动指南

---

## 跨章节联合使用

### 与其他世家章节联合

**比较研究**：
- 与chapter_033（鲁周公世家）比较：[待补充]
- 与chapter_034（燕召公世家）比较：[待补充]
- 与chapter_035（管蔡世家）比较：[待补充]

**综合分析**：
- [待补充跨章节的综合洞察]

---

## 更新记录

**2026-04-06**：创建框架，待补充具体场景和SKU组合

---

**更新日期**：2026-04-06
**章节**：{chapter_num} {info['title']}
**映射场景数**：待完成
"""

def create_fact_template(chapter_num: str, fact_num: int, info: dict) -> str:
    """生成fact模板（Markdown格式）"""
    if fact_num == 1:
        # fact_001是JSON格式的世系传承
        return None  # JSON模板单独处理

    fact_titles = {
        2: '核心事件1',
        3: '核心事件2',
        4: '核心事件3',
        5: '核心人物',
        6: '历史评价与影响'
    }

    return f"""# Fact {fact_num:03d}: {fact_titles.get(fact_num, '待定义')}

## 基本信息

- **章节**: {chapter_num} {info['title']}
- **类型**: {'重大历史事件' if fact_num <= 4 else '人物传记' if fact_num == 5 else '历史评价'}
- **时间**: [待补充]
- **主角**: [待补充]
- **标签**: `#待补充`

---

## 事件背景

### 历史情境

[描述事件发生的历史背景]

### 关键因素

1. **因素1**: [说明]
2. **因素2**: [说明]
3. **因素3**: [说明]

---

## 详细叙述

### 阶段一：[阶段名称]

[详细描述]

> 原文引用：[关键原文] [位置]

### 阶段二：[阶段名称]

[详细描述]

### 阶段三：[阶段名称]

[详细描述]

---

## 历史意义

### 直接影响

1. [影响1]
2. [影响2]

### 长远影响

1. [影响1]
2. [影响2]

---

## 现代启示

### 可借鉴之处

1. [启示1]
2. [启示2]

### 需警惕之处

1. [警示1]
2. [警示2]

---

## 延伸阅读

**相关章节**：
- [相关章节1]
- [相关章节2]

**相关人物**：
- [人物1]
- [人物2]

**参考文献**：
- [文献1]
- [文献2]

---

**创建日期**：2026-04-06
**状态**：框架已建立，内容待补充
"""

def create_fact_json_template(chapter_num: str, info: dict) -> dict:
    """生成fact_001的JSON模板（世系传承）"""
    return {
        "id": f"fact_001_{info['title'].lower()}",
        "chapter": chapter_num,
        "title": f"{info['title']}世系传承",
        "type": "structured_data",
        "format": "json",
        "summary": f"记录{info['title']}的完整世系传承和重要历史节点。",
        "content": {
            "founding": {
                "founder": "[待补充]",
                "time": "[待补充]",
                "context": "[待补充]"
            },
            "lineage": [
                {
                    "name": "[待补充]",
                    "title": "[待补充]",
                    "years": "[待补充]",
                    "events": "[待补充]",
                    "note": "[待补充]"
                }
            ],
            "statistics": {
                "总世数": "[待补充]",
                "建国年代": "[待补充]",
                "终结年代": "[待补充]",
                "存续时长": "[待补充]"
            }
        },
        "sources": [
            {
                "text": "[原文引用]",
                "location": "[位置]"
            }
        ],
        "insights": [
            "[从世系中提炼的洞察1]",
            "[从世系中提炼的洞察2]",
            "[从世系中提炼的洞察3]"
        ],
        "tags": ["世系", "传承", "结构化数据"]
    }

def create_skill_template(chapter_num: str, skill_num: int, info: dict) -> str:
    """生成skill模板"""
    skill_titles = {
        1: '方法论1：待定义',
        2: '方法论2：待定义',
        3: '方法论3：待定义'
    }

    return f"""# Skill {skill_num:03d}: {skill_titles[skill_num]}

## 基本信息

- **章节**: {chapter_num} {info['title']}
- **类型**: 程序性知识
- **难度**: [初级/中级/高级]
- **适用场景**: [待补充]
- **标签**: `#方法论` `#待补充`

---

## 技能概述

### 核心问题

本技能解决的核心问题：[一句话描述]

### 历史来源

从本章的[具体历史案例]中提炼而来。

---

## 方法步骤

### 步骤1：[步骤名称]

**目标**：[本步骤要达成的目标]

**操作**：
1. [具体操作1]
2. [具体操作2]
3. [具体操作3]

**注意事项**：
- [注意点1]
- [注意点2]

### 步骤2：[步骤名称]

**目标**：[本步骤要达成的目标]

**操作**：
1. [具体操作1]
2. [具体操作2]

**注意事项**：
- [注意点1]
- [注意点2]

### 步骤3：[步骤名称]

**目标**：[本步骤要达成的目标]

**操作**：
1. [具体操作1]
2. [具体操作2]

---

## 应用场景

### 历史案例分析

**案例**：[本章中的具体案例]

**应用过程**：
1. [如何应用步骤1]
2. [如何应用步骤2]
3. [如何应用步骤3]

**结果**：[历史案例的结果]

### 现代应用示例

#### 场景1：[商业/个人/组织]

**问题**：[具体问题描述]

**应用**：
1. [应用步骤1]
2. [应用步骤2]
3. [应用步骤3]

**预期效果**：[预期结果]

#### 场景2：[商业/个人/组织]

**问题**：[具体问题描述]

**应用**：
1. [应用步骤1]
2. [应用步骤2]

**预期效果**：[预期结果]

---

## 成功标准

### 过程指标

- [ ] [指标1]
- [ ] [指标2]
- [ ] [指标3]

### 结果指标

- [ ] [指标1]
- [ ] [指标2]

---

## 常见错误

### 错误1：[错误名称]

**表现**：[如何表现]
**原因**：[为什么会犯这个错误]
**纠正**：[如何纠正]

### 错误2：[错误名称]

**表现**：[如何表现]
**原因**：[为什么会犯这个错误]
**纠正**：[如何纠正]

---

## 进阶技巧

1. **技巧1**：[描述]
2. **技巧2**：[描述]
3. **技巧3**：[描述]

---

## 延伸阅读

**相关SKU**：
- fact_XXX：[说明关联]
- skill_XXX：[说明关联]

**相关章节**：
- [其他章节]

---

**创建日期**：2026-04-06
**状态**：框架已建立，内容待补充
"""

def create_chapter_structure(chapter_num: str):
    """创建单个章节的完整目录结构和模板文件"""
    info = CHAPTERS_INFO[chapter_num]
    chapter_dir = BASE_DIR / f'chapter_{chapter_num}'

    # 创建主目录
    chapter_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ 创建目录: {chapter_dir}")

    # 创建skus子目录
    facts_dir = chapter_dir / 'skus' / 'facts'
    skills_dir = chapter_dir / 'skus' / 'skills'
    facts_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ 创建子目录: skus/facts, skus/skills")

    # 生成README.md
    readme_path = chapter_dir / 'README.md'
    readme_path.write_text(create_readme(chapter_num, info), encoding='utf-8')
    print(f"  ✓ 生成文件: README.md")

    # 生成eureka.md
    eureka_path = chapter_dir / 'eureka.md'
    eureka_path.write_text(create_eureka(chapter_num, info), encoding='utf-8')
    print(f"  ✓ 生成文件: eureka.md")

    # 生成mapping.md
    mapping_path = chapter_dir / 'mapping.md'
    mapping_path.write_text(create_mapping(chapter_num, info), encoding='utf-8')
    print(f"  ✓ 生成文件: mapping.md")

    # 生成fact_001.json（世系传承）
    fact_001_path = facts_dir / 'fact_001_lineage.json'
    fact_001_data = create_fact_json_template(chapter_num, info)
    fact_001_path.write_text(json.dumps(fact_001_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"  ✓ 生成文件: skus/facts/fact_001_lineage.json")

    # 生成fact_002-006的Markdown模板
    for i in range(2, 7):
        fact_path = facts_dir / f'fact_{i:03d}_placeholder.md'
        fact_content = create_fact_template(chapter_num, i, info)
        fact_path.write_text(fact_content, encoding='utf-8')
        print(f"  ✓ 生成文件: skus/facts/fact_{i:03d}_placeholder.md")

    # 生成skill_001-003的模板
    for i in range(1, 4):
        skill_path = skills_dir / f'skill_{i:03d}_placeholder.md'
        skill_content = create_skill_template(chapter_num, i, info)
        skill_path.write_text(skill_content, encoding='utf-8')
        print(f"  ✓ 生成文件: skus/skills/skill_{i:03d}_placeholder.md")

    print(f"✓ 章节{chapter_num}（{info['title']}）结构创建完成\n")

def main():
    """主函数：批量创建所有章节"""
    print("=" * 60)
    print("批量创建章节044-046和048-060的SKU框架")
    print("=" * 60)
    print()

    # Group 1: 044-046
    print(">>> Group 1: 处理章节044-046（3个重要世家）\n")
    for chapter_num in ['044', '045', '046']:
        create_chapter_structure(chapter_num)

    # Group 2: 048-060
    print(">>> Group 2: 处理章节048-060（13个世家）\n")
    for chapter_num in ['048', '049', '050', '051', '052', '053', '054',
                        '055', '056', '057', '058', '059', '060']:
        create_chapter_structure(chapter_num)

    print("=" * 60)
    print("✓ 所有章节框架创建完成！")
    print("=" * 60)
    print()
    print("下一步：")
    print("1. 阅读各章原文（chapter_md/NNN_*.tagged.md）")
    print("2. 补充eureka.md的具体洞察")
    print("3. 填充facts的详细内容")
    print("4. 编写skills的方法论")
    print("5. 完善mapping.md的场景映射")

if __name__ == '__main__':
    main()
