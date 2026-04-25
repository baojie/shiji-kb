---
name: SKILL_W10h_精品页增补
title: Wiki 内务整理 H7：精品页候选识别
description: 扫描 quality_score 低且未标记 featured 的页面，识别有潜力成为精品页的候选，写入队列交由 W8 执行建设。W10h 只负责识别，不执行精品页建设。
---

# SKILL W10h: 精品页增补（H7）

> "精品页是知识库的门面。H7 是星探，不是导演——发现潜力股，交给 W8 去打磨。"

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
# 扫描低质量页面（若 pages.json 有 quality_score 字段）
python3 -c "
import json
data = json.load(open('wiki/public/pages.json'))
candidates = [
    p for p in data.get('pages', [])
    if p.get('quality_score', 1) < 0.4
    and not p.get('featured', False)
    and p.get('type') in ('person', 'concept')
    and not p.get('stub', False)
]
for p in sorted(candidates, key=lambda x: x.get('quality_score', 0))[:10]:
    print(f\"{p['quality_score']:.2f}\t{p['id']}\")
"
```

**候选条件**：
- `quality_score < 0.4`
- `featured: false` 或字段不存在
- `type: person` 或 `type: concept`
- `stub: false`（stub 的问题交 H18 先解决）
- 页面行数 ≥ 10 行（有足够基础内容）

---

## 三、执行步骤

### Step 1：运行扫描，获得候选列表

最多取前 5 个候选（按 quality_score 升序）。

### Step 2：快速评估每个候选

```bash
# 快速看候选页内容和现状
cat wiki/public/pages/候选页.md | head -30
```

评估标准：
| 检查项 | 达到精品页潜力的条件 |
|---|---|
| 人物重要性 | 本纪/世家/主要列传的核心人物 |
| 现有内容 | 有基本生平信息，不是空壳 |
| 可扩展性 | 史记原文中有丰富相关内容 |
| 独特性 | 不与其他精品页重复主题 |

### Step 3：写入 W8 精品页建设队列

```markdown
<!-- 在 housekeeping_queue.md 中追加 H7 条目 -->
- [ ] H7 | P2 | [[候选页]] | quality=0.XX，type=person，建议由 W8 建设精品页
  - 现状：有基本生平，缺深度分析/多角度引文
  - W8 任务：enrich-infobox + 增补史记引文节 + 添加洞察节
```

**注意**：条目要写清楚"现状"和"W8 需要做什么"，让 W8 执行时有方向。

---

## 四、成功标准 / 完成条件

- [ ] 扫描完成，获得候选列表
- [ ] 每次识别写入 ≤ 5 个 H7 队列条目
- [ ] 每个条目包含：quality_score、type、现状描述、W8 任务建议
- [ ] 本轮未执行任何精品页建设操作（那是 W8 的工作）

---

## 五、工具与脚本

| 工具 | 用途 |
|---|---|
| `pages.json` 的 `quality_score` 字段 | 获取候选列表 |
| `wiki/logs/butler/housekeeping_queue.md` | 写入 H7 队列条目 |

---

## 六、与 W8 的职责分工

| 职责 | 负责方 |
|---|---|
| 识别精品页候选，评估潜力 | **H7（本文）** |
| 执行精品页建设（enrich/引文/洞察） | W8（`SKILL_W8_精品页建设方法论.md`）|
| 维护 featured 页面列表 | W8 |

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — H7 任务队列（写入后由 W8 消费）
- `skills/SKILL_W8_精品页建设方法论.md` — 执行精品页建设的 SKILL
