---
name: SKILL_W8_精品页建设方法论
title: 高质量精品页建设方法论
description: 基于8个featured页面深化实践总结的wiki精品页建设流程、资源利用优先级和质量标准
---

# 高质量精品页建设方法论

## 快速开始

**适用场景**：对已有基础结构的wiki人物页进行深度强化，达到Wikipedia首页特色文章质量。

**成功标准**：
- 所有重要生平事件均有PN引用
- 多角度他人评价（≥3人）
- 原文引用占比>30%（不只是叙述）
- 相关事件页互联
- 太史公曰独立呈现并分析

---

## 核心资源利用优先级

### 优先级 1：Ontology v2 facts（最高价值）

**位置**：`kg/ontology/ontology-v2/chapters/chapter_NNN/skus/facts/`

**为什么是最高优先级**：
- 每个fact文件对应一个历史场景的结构化深度分析
- 包含原文引用、人物动机、战略意义等多层信息
- 是原始文本与wiki页面之间**最好的桥梁**
- 每章一般有5-15个fact文件

**使用方法**：
```python
import json, os
facts_dir = f'kg/ontology/ontology-v2/chapters/chapter_{NNN}/skus/facts/'
for fname in sorted(os.listdir(facts_dir)):
    d = json.load(open(facts_dir + fname))
    print(f'{fname}: {d.get("description", "")}')
```

**实践发现**：chapter_007（项羽）13个fact文件，提供了：
- 完整分封十八王表
- 丁公放行→被杀的完整故事
- 广武对峙三个场景
- 死后尾声文化意义

### 优先级 2：实体索引与频率数据

**位置**：`kg/entities/data/entity_index.json`、`kg/taxonomy/person.ttl`

**使用方法**：
```python
import json
with open('kg/entities/data/entity_index.json') as f:
    ei = json.load(f)
person = ei['person']['人名']
refs = person['refs']
from collections import Counter
ch_counts = Counter(r[0] for r in refs)
# 按章节统计出现次数
```

**使用场景**：
- 计算人物在史记中的地位（总引用次数、最重要章节）
- 识别跨章节的重要互见关系

### 优先级 3：相关事件页面

**位置**：`wiki/public/pages/` 中type=event的页面

**使用场景**：检查已有独立事件页（如鸿门宴.md、巨鹿之战.md），添加双向链接。

```bash
ls wiki/public/pages/ | xargs grep -l "type: event" | head -20
```

### 优先级 4：Ontology v1 skus

**位置**：`kg/ontology/ontology-v1/skus/`

**评估**：v1数据已被v2基本覆盖，且以英文写作，利用价值低于v2。

### 优先级 5：pn_text_index

**位置**：`data/pn_text_index.pkl`

**限制**：仅包含章节001-030，覆盖秦本纪/项羽本纪/高祖本纪等前期内容，不适用于列传。

**使用方法**：
```python
import pickle
with open('data/pn_text_index.pkl', 'rb') as f:
    idx = pickle.load(f)
ch_segs = [x for x in idx if x['chapter_num'] == '007']
# 搜索包含特定词的段落
hits = [x for x in ch_segs if '某词' in x.get('text_raw', '')]
```

---

## 编辑流程

### 步骤1：资源扫描（5分钟）

并行执行：
1. 读取当前页面，记录已有内容和结构
2. 列出ontology v2 facts，了解可用材料
3. 查询entity_index，获取出现频率统计
4. 检查相关事件页面是否已建

```bash
# 快速扫描
python3 -c "
import json, os
facts_dir = 'kg/ontology/ontology-v2/chapters/chapter_NNN/skus/facts/'
for f in sorted(os.listdir(facts_dir)):
    try:
        d = json.load(open(facts_dir + f))
        print(f'{f}: {d.get(\"description\",\"\")}')
    except: pass
"
```

### 步骤2：缺口识别（重要！）

对照当前页面内容，从资源中找出**已有页面没有**的内容：
- 重要场景是否有原文引用（不只是叙述）
- 跨章节视角（其他人对此人的评价）
- 相关事件页链接
- 量化数据（出现频率、史记地位）

**8次实践中最常见的缺口**：

| 缺口类型 | 频率 | 案例 |
| --- | --- | --- |
| 重要场景细节（有场景名但无细节）| 高 | 刘邦为义帝发丧、汉文帝入继五阶段 |
| 跨章节评价缺失 | 高 | 刘邦评项羽"有范增而不能用"在项羽页缺失 |
| 史记出现频率未注明 | 高 | 所有8个页面原先均未注 |
| 相关事件页未链接 | 中 | 鸿门宴.md/巨鹿之战.md在项羽/刘邦页未链接 |
| 量化/统计数据 | 中 | 分封表格、战役数字等 |

### 步骤3：内容写作标准

**原文引用规范**：
- 使用`> *"原文"*（PN编号）`格式
- 每个重要事件至少1处原文
- 引文后要分析其意义（不只是列出）

**PN编号引用规范**：
- 格式：`（007-141）`
- 重要事件必须有PN
- 允许区间：`（007-183~007-186）`

**段落结构**：每个重要事件：
1. 背景/时间
2. 原文引用
3. 意义/影响

### 步骤4：编辑报告

每个页面编辑完成后写 `logs/wiki_butler/reflections/edit_report_姓名.md`，包含：
1. 资源收集情况（7类资源，各有多少可用）
2. 主要编辑内容表格
3. 质量评估（原页优点 + 缺口 + 未来可改进点）

---

## 质量标准

### Wikipedia精品页标准（6维度）

| 维度 | 最低要求 | 优秀标准 |
| --- | --- | --- |
| 完整性 | 覆盖主要生平事件 | 无重要事件遗漏，含死后尾声 |
| 原文引用 | 每章节≥1处 | 关键场景均有原文，>30%内容为引文 |
| 多角度 | ≥3人他人评价 | 包含对手、友军、史官多方 |
| 结构化信息 | infobox + 生平大事 | 相关表格（家庭/制度/分封等） |
| 知识图联通 | 主要人物有链接 | 相关事件页互联，典故有PN |
| 史学分析 | 有太史公曰 | 分析司马迁评价逻辑，含矛盾/悖论讨论 |

### 典型精品页结构

```markdown
# 人名
[infobox]
[一段话定位：身份/地位/结局/司马迁评价]
[史记出现频率统计]

## 生平
[分阶段，每阶段有原文引用和PN]

## 家庭 [表格]

## 他人眼中的XX
[多角度评价，含对手评语]

## 太史公曰
[原文+分析]

## 性格分析/制度贡献/XX特论 [可选，视人物特点]

## 典故与成语 [清单+PN]

## 相关事件 [event页面链接]

## 相关人物

## 相关章节

## 生平大事 [年表，含PN]
```

---

## 不同类型人物的重点

| 人物类型 | 重点关注资源 | 特殊内容 |
| --- | --- | --- |
| 军事人物（韩信、项羽）| 战役fact文件 | 兵法分析、战前战后态势 |
| 政治人物（刘邦、陈平）| 政策/谋略fact文件 | 制度贡献、计谋详情 |
| 思想人物（孔子）| 弟子/思想fact文件 | 思想要点、弟子关系 |
| 帝王（秦始皇、汉文帝）| 制度/巡游fact文件 | 制度创立、与后世关系 |
| 谋士（张良）| 决策场景fact文件 | 关键决策节点、功成身退 |

---

## 工具与脚本

| 工具 | 用途 | 命令 |
| --- | --- | --- |
| entity_index | 跨章统计 | `kg/entities/data/entity_index.json` |
| taxonomy | 全文频率 | `kg/taxonomy/person.ttl` |
| pn_text_index | 原文查找（前30章）| `data/pn_text_index.pkl` |
| ontology v2 | 场景结构化数据 | `kg/ontology/ontology-v2/chapters/` |

---

## Bot接口与Revision规范

**铁律：所有直接 wiki 页面编辑必须留下 revision 记录。**

任何非 butler 自动化反思生成的页面编辑（包括精品页深化、手动修订、Claude 辅助编辑等），在页面内容写入后必须调用：

```bash
python3 wiki/scripts/butler/record_revision.py <页面slug> \
    --summary "claude/featured-deepdive: 深化精品页 <人名>" \
    --author claude
```

**summary 命名规范**：
- 精品页深化：`claude/featured-deepdive: 深化精品页 <人名>`
- 链接强化：`claude/link-enhance: 添加事件页链接`
- 内容补充：`claude/content-patch: 补充 <具体内容>`
- 修正错误：`claude/fix: 修正 <描述>`

此命令会同步更新：
1. `wiki/public/history/<slug>.json` — 页面级 revision 历史
2. `wiki/public/recent.json` — 全局最近编辑列表

**Revision 文件需随页面一起 git add 和 commit。**

```bash
git add wiki/public/pages/<slug>.md wiki/public/history/<slug>.json wiki/public/recent.json
```

---

## 执行前/中/后检查清单

**执行前**：
- [ ] 读取当前页面，了解已有内容
- [ ] 列出ontology v2 facts，标记优先阅读的
- [ ] 查询entity_index出现频率

**执行中**：
- [ ] 每个新增场景有原文引用和PN
- [ ] 相关事件页已添加链接
- [ ] 不删改原有正确内容，只新增

**执行后**：
- [ ] 写edit_report_姓名.md
- [ ] **调用 record_revision.py 留下 revision 记录**（必须）
- [ ] 检查PN格式是否正确（NNN-NNN）
- [ ] 确认引文使用全角引号

---

## 附：8个精品页质量评估汇总

| 人物 | 基础行数 | 编辑后 | 主要补充内容 | 底线质量 |
| --- | --- | --- | --- | --- |
| 项羽 | 290 | ~430 | 18王表、丁公故事、广武中箭、刘邦评、性格矛盾表 | ⭐⭐⭐⭐⭐ |
| 刘邦 | 271 | ~330 | 龙种神话、为义帝发丧、知人善任章节 | ⭐⭐⭐⭐⭐ |
| 孔子 | 229 | ~250 | 闻韶三月、路线图、颜回"子在回何敢死"、子路死 | ⭐⭐⭐⭐⭐ |
| 汉文帝 | 125 | ~175 | 入继五阶段、缇萦上书原文、节俭原文 | ⭐⭐⭐⭐ |
| 陈平 | 200+ | ~210 | "多阴谋道家所禁"自言 | ⭐⭐⭐⭐⭐ |
| 韩信 | 296 | ~310 | 蒯通被召自辩、频率统计 | ⭐⭐⭐⭐⭐ |
| 张良 | 267 | ~272 | 频率统计 | ⭐⭐⭐⭐⭐ |
| 秦始皇 | 271 | ~280 | 沙丘密谋详情（赵高说辞）| ⭐⭐⭐⭐⭐ |

**关键发现**：
1. 项羽、刘邦、汉文帝是收益最大的（相对底子弱，v2资料丰富）
2. 韩信、张良、陈平、孔子底子极好，主要补漏和量化
3. **Ontology v2是最高价值资源**，每次深化首先应穷尽这个来源
4. 跨章节引用（如刘邦在项羽页缺失）是系统性缺口，需刻意检查

---

*SKILL创建：wiki_butler，2026-04-23*
*依据：项羽/刘邦/孔子/汉文帝/陈平/韩信/张良/秦始皇8份编辑报告*
