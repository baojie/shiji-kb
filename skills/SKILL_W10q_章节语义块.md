---
name: SKILL_W10q_章节语义块
title: Wiki 内务整理 H17：章节概览语义块建设
description: 为 type=chapter 的章节页面补充"章节概览"表格节，包含类型/时段/主角/核心主题/关键事件/段落数/字数等结构化信息。
---

# SKILL W10q: 章节语义块（H17）

> "章节概览是 130 篇《史记》的导航地图。读者一眼看到结构，研究者一眼看到数据。"

---

## 一、何时执行

| 触发场景 | 优先级 |
|---|---|
| type=chapter 页面缺 `## 章节概览` 节 | P2 |
| 每 20 轮迭代周期扫描一次 | P2 |
| 用户要求完善某章节页 | P1 |

**优先级**：本纪 > 世家 > 列传 > 表 > 书（表类最后处理）

---

## 二、发现候选（扫描方法）

```bash
# 找 type=chapter 但无 ## 章节概览 的页面
for f in wiki/public/pages/*.md; do
    if grep -q "^type: chapter" "$f" && ! grep -q "## 章节概览" "$f"; then
        echo "$f"
    fi
done | head -20

# 优先本纪（通常命名含"本纪"）
ls wiki/public/pages/ | grep "本纪" | head -12
```

---

## 三、章节概览节格式

```markdown
## 章节概览

| 属性 | 内容 |
|---|---|
| **篇章类型** | 本纪 / 世家 / 列传 / 表 / 书 |
| **时段** | 起止年代（如"前770—前221年"）|
| **主角** | 主要人物（1-3 人）|
| **核心主题** | 一句话概括（不超过20字）|
| **关键事件** | 3-5 个关键事件名（可加链接）|
| **段落数** | N 段 |
| **字数** | 约 N 字 |
| **对应章节** | `[[NNN_X列传]]` |
```

**示例**（以某列传为例）：

```markdown
## 章节概览

| 属性 | 内容 |
|---|---|
| **篇章类型** | 列传 |
| **时段** | 前338—前284年 |
| **主角** | [[苏秦]]、[[张仪]] |
| **核心主题** | 合纵连横，战国外交博弈的缩影 |
| **关键事件** | [[苏秦合纵六国]]、[[张仪连横]]、[[秦破合纵]] |
| **段落数** | 47 段 |
| **字数** | 约 6800 字 |
| **对应章节** | `[[069_苏秦列传]]` |
```

---

## 四、数据来源

| 数据项 | 来源 |
|---|---|
| 篇章类型 | 页面名/frontmatter type 字段 |
| 时段 | kg/events 中该章节事件的时间范围 |
| 主角 | frontmatter 或正文首段 |
| 核心主题 | 基于引文内容概括（需理解后手写）|
| 关键事件 | kg/events 筛选该章节高权重事件 |
| 段落数 | `wc -l chapter_md/NNN_*.md` 估算 |
| 字数 | `wc -c chapter_md/NNN_*.md` 估算 |

```bash
# 查询章节事件数据
ls kg/ontology/ontology-v2/chapters/chapter_NNN/

# 统计段落数（粗估）
grep -c "^[0-9]\+\." data/chapters/NNN_*.md 2>/dev/null || echo "未找到"
```

---

## 五、执行步骤

### Step 1：找到目标章节页

```bash
cat wiki/public/pages/NNN_X列传.md | head -30
```

### Step 2：收集概览数据

按数据来源表，逐项收集填入表格的数据。**核心主题**需要读完引文内容后手写，不能自动生成。

### Step 3：在正文开头（frontmatter 后第一节位置）插入概览表

**位置规范**：`## 章节概览` 应位于页面正文的**第一节**（frontmatter 之后、其他内容之前）。

### Step 4：写入

```bash
python3 wiki/scripts/butler/edit_page.py "NNN_X列传" /tmp/with_overview.md \
    --summary "w10q: H17 补充章节概览节（段落数/时段/主题）" \
    --author "butler"
```

---

## 六、成功标准 / 完成条件

- [ ] 概览表格格式正确（7 行数据，各字段有值）
- [ ] 关键事件加了 wikilink（若有对应页面）
- [ ] 核心主题是有意义的概括（非空洞描述）
- [ ] 每轮处理 ≤ 3 个章节页
- [ ] 本纪类完成后才处理世家，世家完成后才处理列传

---

## 七、工具与脚本

| 工具 | 用途 |
|---|---|
| `kg/ontology/ontology-v2/chapters/` | 章节 SKU 事件数据 |
| `data/chapters/NNN_*.md` | 原文字数/段落统计 |
| `wiki/scripts/butler/edit_page.py` | 写入页面 |

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — H17 任务队列
- `wiki/public/pages/` — 章节页面存储位置
