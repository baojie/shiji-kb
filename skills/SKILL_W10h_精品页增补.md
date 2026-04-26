---
name: SKILL_W10h_精品页增补
title: Wiki 内务整理 H7：premium 候选识别
description: 扫描 quality=standard 或 featured 但有潜力晋级的页面，识别 premium 候选，写入队列交由 W8 执行建设。W10h 只负责识别，不执行精品页建设。
---

# SKILL W10h: 精品页增补（H7）

> "旗舰页是知识库的门面。H7 是星探，不是导演——发现潜力股，交给 W8 去打磨。"

---

## 一、何时执行

| 触发场景 | 说明 |
|---|---|
| 每 20 轮迭代周期执行一次识别扫描 | 常规识别 |
| 用户指定某个领域需要精品页 | 定向识别 |
| W8 精品页建设队列为空 | 补充候选 |

**重要**：H7 只做识别和分诊，**不执行精品页建设**。建设任务委托给 `SKILL_W8_精品页建设方法论.md`。

---

## 二、发现候选（扫描方法）

```bash
# 扫描有晋级潜力的页面（quality=standard 或 featured，refs > 0）
python3 -c "
import json
data = json.load(open('wiki/public/pages.json'))
pages = data.get('pages', {})
candidates = [
    {'id': k, **v} for k, v in pages.items()
    if v.get('quality') in ('standard', 'featured')
    and v.get('type') in ('person', 'concept', 'overview', 'story', 'sanwen')
    and (v.get('total_refs') or 0) > 0
]
for p in sorted(candidates, key=lambda x: -(x.get('total_refs') or 0))[:10]:
    print(f\"{p.get('quality'):10} refs={p.get('total_refs',0):4d}  {p['id']}\")
"
```

**候选优先级**：
1. `quality=featured`（已有图和结构，缺深度内容达 premium）— 最高优先
2. `quality=standard`，`total_refs` 高（在史记中出现频繁，有丰富原材料）— 次之
3. `type` 为 `person`/`overview`（最容易建成 premium）

**排除**：
- `quality=stub` 或 `quality=basic`（太薄，交 H18 先扩展）
- `quality=premium`（已是最高级）

---

## 三、执行步骤

### Step 1：运行扫描，获得候选列表

最多取前 5 个候选（按 total_refs 降序）。

### Step 2：快速评估每个候选

```bash
head -30 wiki/public/pages/候选页.md
```

评估标准：
| 检查项 | 晋级 premium 的潜力条件 |
|---|---|
| 人物/事件重要性 | 本纪/世家/主要列传的核心内容 |
| 现有 quality 级 | featured → premium 路径最短 |
| 可扩展性 | ontology-v2 facts 丰富，史记原文有深度 |
| 缺口类型 | 缺图/缺 PN/缺分析/缺太史公曰 → W8 明确任务 |

### Step 3：写入 W8 精品页建设队列

```markdown
<!-- 在 housekeeping_queue.md 中追加 H7 条目 -->
- [ ] H7 | P2 | [[候选页]] | quality=featured，type=person，refs=NN，建议由 W8 升级为 premium
  - 现状：有图有基本结构，缺太史公曰分析/多角度引文/PN不足
  - W8 任务：补太史公曰节 + 增补史记引文(PN≥10) + 跨章节评价
```

**注意**：条目要写清楚"当前 quality 级别"和"W8 需要做什么才能达到 premium"。

---

## 四、成功标准 / 完成条件

- [ ] 扫描完成，获得候选列表
- [ ] 每次识别写入 ≤ 5 个 H7 队列条目
- [ ] 每个条目包含：当前 quality、type、total_refs、现状描述、W8 任务建议
- [ ] 本轮未执行任何精品页建设操作（那是 W8 的工作）

---

## 五、工具与脚本

| 工具 | 用途 |
|---|---|
| `pages.json` 的 `quality` 字段 | 获取候选列表 |
| `python3 wiki/scripts/compute_quality.py <slug>` | 重新评估单页 quality |
| `wiki/logs/butler/housekeeping_queue.md` | 写入 H7 队列条目 |

---

## 六、与 W8 的职责分工

| 职责 | 负责方 |
|---|---|
| 识别 premium 候选，评估晋级路径 | **H7（本文）** |
| 执行精品页建设（enrich/引文/洞察） | W8（`SKILL_W8_精品页建设方法论.md`）|
| 编辑后重评 quality 标签 | W3 §八（调用 compute_quality.py）|

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — H7 任务队列（写入后由 W8 消费）
- `skills/SKILL_W8_精品页建设方法论.md` — 执行精品页建设的 SKILL
- `wiki/scripts/compute_quality.py` — 自动评定质量级别
