---
name: SKILL_W10e_原文溯源增补
title: Wiki 内务整理 H4：原文溯源增补
description: 为有内容但缺乏史记原文溯源字段（sources/event_ids/pn）的页面补充 PN 引注，确保每个断言都有原文出处。
---

# SKILL W10e: 原文溯源增补（H4）

> "无源之水不长久。每个关于《史记》的断言，都应该能追溯到具体的段落。"

---

## 一、何时执行

| 触发场景 | 优先级 |
|---|---|
| person 页有 ≥3 行描述内容，但 frontmatter 无 `pn` 且正文无 PN 引注 | P1 |
| concept 页有内容但无任何溯源字段 | P2 |
| W7 引文核验脚本标记为 unsourced | P1 |

**不处理的情形**：
- 页面只有 stub 一行描述（内容太少，等 H18 Stub扩展后再溯源）
- 页面已有充足 PN 引注

---

## 二、发现候选（扫描方法）

```bash
# 扫描缺溯源的页面（若脚本存在）
python3 wiki/scripts/butler/find_unsourced.py --max 20 --write-queue

# 手动扫描：找有内容但无 PN 引注的 person 页
grep -L "(0[0-9][0-9]-" wiki/public/pages/*.md | \
    xargs grep -l "^type: person" | head -20
```

**筛选条件**：
- `canonical_name` 长度 ≥ 3 字（太短的词自动匹配精度低）
- 页面行数 ≥ 5 行（有足够内容才值得溯源）
- `quality` 不为 `stub`（stub 另有 H18 处理）

---

## 三、执行步骤

### Step 1：读页面内容，列出断言句

```bash
cat wiki/public/pages/人物名.md
```

找出正文中的事实性断言句，如：
- "公元前XXX年，X出任Y"
- "X参与了Z事件"

### Step 2：用 find_pn 脚本或人工查找原文段落

```bash
# 若脚本存在
python3 wiki/scripts/butler/find_pn_for_quote.py "断言关键词" --person "人物名"

# 手动查找：在章节标注文件中搜索
grep -n "关键词" data/chapters/NNN_*.md | head -10
```

**匹配标准**：
- 自动匹配：相似度 score ≥ 0.8 才采用
- 低于 0.8：记入 `failures.jsonl`，不强行附注

### Step 3：人工确认匹配正确性

对照原文段落，确认：
1. 该段落确实记载了页面中的断言
2. PN 编号格式正确（如 `(052-23)` 表示第52篇第23段）

### Step 4：补充 frontmatter 的 pn 字段

```yaml
# 在 frontmatter 中补充
pn: (052-23)
# 多个来源：
pn: (052-23) | (065-7)
```

格式规范（参考 SKILL_W10a §2.2）：
- 单个：`(章节-段号)`
- 同章多个：`(052-23) (52)`
- 跨章：`(052-23) | (065-7)`

### Step 5：正文行内 PN 引注（可选，精品页要求）

在断言句末尾追加行内引注：

```markdown
X于某年出任某职（052-23）。
# 或详细格式
X于某年出任某职（见 [[052_X列传]] §23）。
```

### Step 6：写入并记录

```bash
python3 wiki/scripts/butler/edit_page.py "人物名" /tmp/sourced.md \
    --summary "w10e: 补充PN溯源引注（来自NNN章第N段）" \
    --author "butler"
```

---

## 四、成功标准 / 完成条件

- [ ] 补充的 PN 经人工核实指向正确段落
- [ ] frontmatter pn 字段格式符合规范
- [ ] 每轮处理 ≤ 5 个页面
- [ ] 无法确认的断言记入 `wiki/logs/butler/failures.jsonl`（不强行附注）

---

## 五、工具与脚本

| 工具 | 用途 |
|---|---|
| `find_unsourced.py --max 20 --write-queue` | 批量发现缺溯源页面并写入队列 |
| `find_pn_for_quote.py` | 根据关键词搜索对应 PN |
| `wiki/scripts/butler/edit_page.py` | 写入修改 |
| `wiki/logs/butler/failures.jsonl` | 记录无法匹配的断言 |

---

## 六、与其他 H 类型的区分

| 场景 | 归属 |
|---|---|
| 引文内容与原文不符（引文本身错误） | H11（W10l）→ 转 W7 |
| 页面完全无内容（stub） | H18（W10r）→ 先扩展再溯源 |
| 页面有引文节但 PN 为空 | **H4（本文）** |

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — H4 任务队列
- `wiki/logs/butler/failures.jsonl` — 无法匹配的断言记录
- `skills/SKILL_W7_引文真实性核验.md` — 引文准确性核验（不同于溯源）
