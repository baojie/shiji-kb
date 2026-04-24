---
name: SKILL_W10a_Butler去重合并
title: Wiki 重复页面去重合并（H1 操作规范）
description: 将同一主题的多个重复页面反思融合为一个规范页，原始页改为 REDIRECT 保留历史。核心原则：先 union 内容，再反思剪裁，最后 REDIRECT。
---

# SKILL W10a: 重复页面去重合并

> "去重不是删除，是升华。合并后的规范页应比任何单个版本都更完整、更有洞见。"

---

## 一、何时执行

| 触发场景 | 动作 |
|---|---|
| `housekeeping_queue.md` 有 P0 H1 条目 | 每 10 轮执行一条 |
| 用户报告重复页 | 加入 P0，优先处理 |
| W10 扫描发现新重复 | 写入队列，等待执行 |

---

## 二、核心原则

### 2.1 内容优先 Union
**不是"选一个留下"，而是"读所有版本，取各自精华"：**
- 读完所有候选页，列出每页的**独有内容**（独有视角、案例、引文、步骤）
- 以最丰富版本为骨架
- 逐一将其他版本的独有内容**有机整合**进合适章节
- 最终规范页 = 所有版本的超集，内容比任何单版都更完整

### 2.2 反思剪裁
Union 后再**反思去重**：
- 去除重复段落，保留最好的表述
- 合并相似案例，不重复列举
- 统一术语，保持内部一致性

### 2.3 REDIRECT 而非删除
❌ **绝对禁止 `rm` 删除文件**
✅ 冗余页**必须**改为 REDIRECT 页，保留 URL 有效性和历史记录

---

## 三、操作步骤（逐条执行）

```
读取 → 判断 → 确定规范页 → Union → 反思剪裁 → 写入 → record_revision → REDIRECT → 更新反向链接
```

### Step 1：读取所有候选页

```bash
# 先读内容最丰富的（行数最多的）
cat "wiki/public/pages/规范页候选.md"
cat "wiki/public/pages/冗余页1.md"
cat "wiki/public/pages/冗余页2.md"
```

列出每页的**独有内容块**（其他页没有的视角、案例、引文）。

### Step 2：判断是否真重复

| 情形 | 处理 |
|---|---|
| 同一主题，内容有 >30% 重叠 | ✅ 继续合并 |
| 独立事件系列（过秦论上/中/下，张仪说X王）| ⏭ 跳过，从队列删除 |
| 人物页 vs 其事件子页 | ⏭ 跳过，互链说明关系 |
| 上下级关系（人物页 vs 其文书） | ⏭ 跳过，保留两页 |

### Step 3：确定规范页（canonical）

**选择规范页的优先级：**
1. 短简洁名优先（`围魏救赵.md` > `围魏救赵完整战术框架：批亢捣虚...md`）
2. 若短名内容很薄而长名内容丰富：以长名内容写入短名文件
3. 若两者内容相当：选行数更多的

### Step 4：Union 合并内容

逐一检视冗余页，提取**独有内容**整合进规范页：

```markdown
# 检视清单（每个冗余页）
□ 独有视角/论点（规范页没有的角度）
□ 独有案例/史料引文（不同来源）
□ 独有步骤/框架结构
□ 独有参见链接
```

整合后的规范页**应包含所有版本的精华**，但不重复。

#### 字段独立性铁律（必读）

**`event_ids` 与 `pn` 是完全独立的两套体系，绝不联动修改：**

| 字段 | 含义 | 示例 |
|---|---|---|
| `event_ids` | 事件结构化编号，有自己的命名规则 | `[094-010, 097-003]` |
| `pn` | 史记原文段落引用号（Purple Numbers） | `(094-10) \| (097-6)` |

两者表面数字相近，但语义完全不同。修改其中一个时**绝对禁止**推断"相关"而联动修改另一个。

#### PN 字段合并规范（必读）

冗余页若有 `:::meta` 块中的 `pn:` 字段，合并时须遵守以下格式：

| 情形 | 格式 | 示例 |
|---|---|---|
| 单个 PN | `(章节-段号)` | `(031-23.7)` |
| 同章节多个 PN | 各自独立括号，第二个省略章节前缀 | `(031-41.1) (41.4)` |
| 不同章节 PN | 管道符分隔 | `(031-23.7) \| (086-2.4)` |

**❌ 严禁括号内连字符连接多个段号**：`(031-41.1-41.4)` 是错误格式，正确为 `(031-41.1) (41.4)`。

合并脚本或手动合并时，若两页的 pn 均非空，必须先解析各自格式，再按上述规则拼接。

### Step 5：写入规范页

```bash
# 直接用 Write 工具写入（或 edit_page.py）
python3 wiki/scripts/butler/edit_page.py "规范页名" --content-file /tmp/merged.md
```

### Step 6：记录 revision

```bash
python3 wiki/scripts/butler/record_revision.py "规范页名" \
    --summary "butler/dedup: 融合N个版本（页名1、页名2），保留全部独有内容" \
    --author butler
```

### Step 7：冗余页改为 REDIRECT

```bash
# 每个冗余页执行一次
python3 wiki/scripts/butler/edit_page.py "冗余页名" --redirect-to "规范页名"
```

若 edit_page.py 不支持 redirect，手动写入以下格式：

```markdown
---
id: 冗余页名
type: redirect
label: 冗余页名
redirect_to: 规范页名
---

# 冗余页名

> **重定向**：本页重定向至 [[规范页名]]。
>
> 本页内容已融合入 [[规范页名]]。
```

然后 `record_revision.py` 记录：

```bash
python3 wiki/scripts/butler/record_revision.py "冗余页名" \
    --summary "butler/dedup: 转为REDIRECT→规范页名" \
    --author butler
```

### Step 8：更新反向链接（每次只改一个文件）

```bash
# 找所有引用旧名的页面
grep -rl "[[冗余页名]]" wiki/public/pages/

# 逐文件替换（每次一个，diff ≤ 20 行）
```

---

## 四、每轮限制（防止超范围）

| 限制项 | 值 |
|---|---|
| 每轮处理条目 | 1 条 P0 H1 |
| 每条最多合并页数 | 5 页 |
| 每次反向链接替换 | 1 个文件 |
| 单次 diff 不变量 | ≤ 20 行 |
| 超过 50 行内容差异 | 需人工裁决，不自动合并 |

---

## 五、REDIRECT 页格式规范

```markdown
---
id: 冗余页名
type: redirect
label: 显示名（通常与 id 相同）
redirect_to: 规范页名
---

# 冗余页名

> **重定向**：本页重定向至 [[规范页名]]。
>
> 简短说明为何重定向（如"同一事件的不同命名"）。
```

**注意**：前端渲染器依赖 `type: redirect` 和 `redirect_to` 字段，格式必须精确。

---

## 六、常见误判（不应合并的情形）

### 6.1 事件系列（保留为独立页）
- `过秦论上`、`过秦论中`、`过秦论下` → 同一文章的三篇，各自独立
- `张仪说楚王连横`、`张仪说燕王连横`、`张仪说赵王连横` → 不同事件，不合并
- `济北王兴居反`、`济北王志徙菑川`、`济北王献泰山` → 不同年份的事件

### 6.2 人物页 + 事件子页（保留两页，互链）
- `白起.md` + `白起伊阙破魏韩.md` → 不合并，保留事件子页，在人物页中链接
- `公孙弘.md` + `公孙弘临终上书.md` → 不合并

### 6.3 概念页 + 子话题（保留，互为参见）
- `功高震主.md` + `功高震主四策决策树.md` → 可保留为独立精品页，在主页中 `## 参见` 互链

---

## 七、脚本工具

| 脚本 | 用途 |
|---|---|
| `wiki/scripts/butler/discover_duplicates.py` | 自动扫描重复候选，写入队列 |
| `wiki/scripts/butler/record_revision.py` | 写入 revision（合并后必须调用）|
| `wiki/scripts/butler/edit_page.py` | 编辑/创建页面（含 --redirect-to 选项）|
| `scripts/fix_pn_range_syntax.py` | 扫描/修复 `(NNN-X.Y-Z.W)` 错误 PN 格式 |

```bash
# 每 10 轮运行一次扫描（max-new 限制写入数量）
python3 wiki/scripts/butler/discover_duplicates.py --max-new 10

# 处理一条 P0 H1（读取后手动决策）
cat wiki/logs/butler/housekeeping_queue.md | grep -A5 "P0" | head -20
```

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — 任务队列（去重条目在 H1 标签下）
- `skills/SKILL_W10_Butler内务整理.md` — 上级 SKILL（包含 H2/H3 任务）
- `wiki/scripts/butler/discover_duplicates.py` — 重复检测脚本
