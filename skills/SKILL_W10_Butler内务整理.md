---
name: SKILL_W10_Butler内务整理
title: Wiki 内务整理（Housekeeping）队列与流程
description: 发现并修复 wiki 结构性缺陷：重复/冗余页面合并、链接补全、重定向页创建。维护 logs/wiki_butler/housekeeping_queue.md，每 10 轮处理一条高优先级条目。
---

# SKILL W10: 内务整理（Housekeeping）

> "知识库的质量 = 内容正确性 × 结构整洁性"。W3-W9 保证内容，W10 保证结构。

---

## 一、四类内务任务

### 类型 H1：重复/冗余页面融合

**完整操作规范见** → [`SKILL_W10a_Butler去重合并.md`](SKILL_W10a_Butler去重合并.md)

**核心原则**（摘要）：
1. **先 Union**：读完所有候选页，取各自独有内容，合并为超集
2. **再反思剪裁**：去除重复段落，统一术语
3. **REDIRECT 而非删除**：冗余页必须改为 `type: redirect` 页，❌ 绝对禁止 `rm`

**发现方法**：
```bash
# W10 标准扫描（每 10 轮运行）：基于前缀 + Jaccard 相似度，写入队列
python3 wiki/scripts/butler/discover_duplicates.py --max-new 10
# 自动过滤假阳性：人物页+事件子页、系列页（张仪说X王）、已有 REDIRECT 的页
```

**处理流程**（简版，详见 W10a）：
1. 读取所有候选页 → 判断是否真重复
2. 确定规范页（短名优先）→ Union 内容 → 反思剪裁 → 写入
3. 调用 `record_revision.py` → 冗余页改 REDIRECT → 更新反向链接

**优先级**：
- P0：同主题两个以上页面，Jaccard > 0.4
- P1：标题相似但内容差异较大，需人工判断
- P2：长标题 vs 短标题变体（如功能相同但命名不同）

---

### 类型 H2：链接补全（Wikilink 织网）

**现象**：页面正文中提及人名/事件/概念，但未用 `[[]]` 语法链接。

**发现方法**：
```bash
# 扫描页面，找未链接但已有对应页面的词汇
python3 wiki/scripts/butler/discover_kg.py --mode missing-links --target <slug>

# 或批量扫描 quality_score 低且 resolved_wikilinks 少的页面
# 从 pages.json 筛选 link_density 维度低的页面
```

**处理规则**：
1. **只加第一次出现的链接**：同一词汇在页面内只链第一次
2. **确认目标页存在**：`[[XX]]` 前先确认 `wiki/public/pages/XX.md` 存在
3. **消歧语法**：多义词用 `[[规范名|显示名]]`，如 `[[汉武帝|孝武帝]]`
4. **不改原文**：只加 `[[]]` 括号，不修改任何文字内容
5. **每次最多补 5 个链接**：控制 diff 大小（≤ 20 行不变量）

**优先级**：
- P0：主要传记章节的人物互链（同传中互相出现的人物）
- P1：高频人物（刘邦、项羽、孔子等）在非人物页中未链
- P2：已有精品页的事件/概念，在相关人物页中未链

---

### 类型 H3：重定向页创建（REDIRECT）

**现象**：同一人物/概念有多种称呼，不同页面用法不一，用户搜索某种叫法找不到页面。

**典型例子**：
- `辟阳侯` ↔ `审食其`（同一人，两种常用称呼）
- `黥布` ↔ `英布`（同一人，《史记》内前后异称）
- `司马谈论六家要旨` ↔ `司马谈论六家要指`（同一文章名，旨/指之异）

**发现方法**：
```bash
# 查看 alias_conflicts.json（自动检测别名冲突）
python3 wiki/scripts/butler/reflection_scan.py --aspect alias

# 检查 pages.json 中有 aliases 字段但无对应 REDIRECT 页的情况
python3 -c "
import json
pages = json.load(open('wiki/public/pages.json'))['pages']
import os
for pid, p in pages.items():
    for alias in p.get('aliases', []):
        if alias != pid and not os.path.exists(f'wiki/public/pages/{alias}.md'):
            print(f'MISSING REDIRECT: {alias} → {pid}')
" 2>/dev/null | head -20
```

**REDIRECT 页格式**：

```markdown
---
id: 辟阳侯
type: redirect
label: 辟阳侯
redirect_to: 审食其
---

# 辟阳侯

> **重定向**：本页重定向至 [[审食其]]。
> 
> 辟阳侯为[[审食其]]的封号，详见 [[审食其]] 页面。
```

**处理优先级**：
- P0：aliases 字段已有但无 REDIRECT 页的情况（自动可检测）
- P1：alias_conflicts.json 中同 surface 指向多页的高冲突项
- P2：用户报告找不到的页面

---

### 类型 H4：史记原文溯源增补

**现象**：person/concept/overview 等页面有内容，但缺少 `sources`、`event_ids`、`pn` 等溯源字段，无法追溯到《史记》原文具体段落。

**发现方法**：
```bash
# 扫描缺少溯源字段的页面，在原文中查找对应 PN
python3 wiki/scripts/butler/find_unsourced.py --max 20
# 只处理指定页面（调试用）
python3 wiki/scripts/butler/find_unsourced.py --target 韩王成
# 批量写入 housekeeping_queue.md
python3 wiki/scripts/butler/find_unsourced.py --max 50 --write-queue
```

**匹配规则**：
- canonical_name **≥ 3 字**才做自动匹配（1-2 字误链风险太高）
- 只返回 score ≥ 0.8 的原文段落（精确子串匹配优先）
- 工具内部调用 `find_pn_for_quote.py`，直接从 `chapter_md/*.tagged.md` 取 PN

**处理步骤**：
1. 对队列中的 H4 条目，读取建议的 `sources` / `pn` 列表
2. 人工或 butler 确认 PN 确实与页面内容相关
3. 用 `edit_page.py` 在 frontmatter 补充 `sources:` / `event_ids:`，正文加行内 PN 引注
4. 调用 W2 中的 `source-with-pn` 原子动作

**优先级**：
- P1：person 页有3行以上内容但无任何溯源字段
- P2：concept/overview 页缺溯源

---

## 二、Housekeeping 队列格式

文件：`logs/wiki_butler/housekeeping_queue.md`

```markdown
# Housekeeping 队列

最后更新: YYYY-MM-DD

## P0（立即处理）

- [ ] H1 合并 司马谈论六家要指 + 司马谈论六家要旨 + 司马谈六家论
      → 三页均指同一篇文章，需合并为一页，其余改 REDIRECT
      → 发现于: 2026-04-23 用户报告
- [ ] H3 创建 REDIRECT: 辟阳侯 → 审食其
      → 发现于: alias_conflicts 2026-04-23

## P1（本周内处理）

- [ ] H2 补链: 鸿门宴.md 中 曹无伤/项庄/靳彊 未全部链接
- [ ] H3 创建 REDIRECT: 黥布 → 英布（或反向）
- [ ] **H4** 溯源增补：`韩王成`
      建议 sources: [项羽本纪, 留侯世家]
      建议 pn: [(007-96.1), (007-105.1), (055-7), (055-11)]
      → 发现: find_unsourced 扫描

## P2（积压）

- [ ] H1 检查 七国之乱 / 吴楚七国之乱 / 七国叛乱 是否重复
```

**队列字段说明**：
- `H1/H2/H3`：任务类型
- `[ ]`/`[x]`：未完成/已完成
- 发现方式和时间（便于追溯）

---

## 三、触发时机

| 时机 | 行动 |
|---|---|
| **每 10 轮**一次（与 W5 反思错开）| ① `discover_duplicates.py` 扫描，写入最多 10 条 H1 候选到 housekeeping_queue.md P0/P1<br>② `find_unsourced.py --max 20 --write-queue` 扫描溯源缺失，写入 H4 条目<br>③ 处理队列里最老的一条 P0 H1 任务（读取→反思融合→写入→REDIRECT→record_revision） |
| **每轮末尾**（轻量）| 检查当轮新建页面是否触发 H3（新页面的 aliases 是否已有 REDIRECT） |
| **用户指出**（即时）| 将用户报告的问题直接加入 P0 |
| **butler 执行 H 任务**| 每次 trail 队列无 P0/P1 时，检查 housekeeping_queue.md，处理一条 P0 |

---

## 四、H1 融合操作规范

**完整步骤（8步）详见 [`SKILL_W10a_Butler去重合并.md`](SKILL_W10a_Butler去重合并.md)**

**核心禁忌**：
- ❌ **禁止 `rm` 删除文件**——冗余页必须改为 REDIRECT（URL 有效 + 历史保留）
- ❌ **禁止批量替换链接**——每次只改一个文件（diff ≤ 20 行）
- ❌ **禁止合并内容差异 >50 行的页面**——需人工裁决
- ✅ **REDIRECT 页格式固定**，`type: redirect` + `redirect_to` 字段缺一不可

---

## 六、首次扫描（初始化 Housekeeping 队列）

首次运行时，执行以下扫描建立初始队列：

```bash
# 1. 重复标题扫描
python3 wiki/scripts/butler/reflection_scan.py --aspect dup > /tmp/dup_scan.txt

# 2. alias 冲突扫描
python3 wiki/scripts/butler/reflection_scan.py --aspect alias > /tmp/alias_scan.txt

# 3. 生成缺失 REDIRECT 列表
python3 -c "..." 2>/dev/null | head -50 > /tmp/missing_redirects.txt
```

将扫描结果分类后填入 `logs/wiki_butler/housekeeping_queue.md`。

---

## 相关路径

- `logs/wiki_butler/housekeeping_queue.md` — 任务队列
- `wiki/scripts/butler/discover_duplicates.py` — **标题相似度扫描，每 10 轮运行**（含假阳性过滤）
- `wiki/scripts/butler/find_unsourced.py` — **溯源缺失扫描，每 10 轮运行**（调用 find_pn_for_quote 在原文中取 PN）
- `wiki/data/alias_conflicts.json` — 自动检测的 alias 冲突
- `wiki/scripts/butler/reflection_scan.py` — 扫描工具（--aspect dup/alias）
- `wiki/scripts/butler/record_revision.py` — 写入 revision（融合后必须调用）
- `skills/SKILL_W10a_Butler去重合并.md` — **H1 详细操作规范（Union→反思→REDIRECT）**
- `skills/SKILL_W5_Butler反思与自改.md` — 系统级反思（互补）
- `skills/SKILL_W9_Butler页面图式反思.md` — 内容级反思（互补）
