---
name: SKILL_W10_Butler内务整理
title: Wiki 内务整理（Housekeeping）队列与流程
description: 发现并修复 wiki 结构性缺陷：重复/冗余页面合并、链接补全、重定向页创建。维护 logs/wiki_butler/housekeeping_queue.md，每 10 轮处理一条高优先级条目。
---

# SKILL W10: 内务整理（Housekeeping）

> "知识库的质量 = 内容正确性 × 结构整洁性"。W3-W9 保证内容，W10 保证结构。

---

## 一、三类内务任务

### 类型 H1：重复/冗余页面合并

**现象**：两个或多个页面描述同一主题，内容部分重叠——
如 `司马谈论六家要指`、`司马谈论六家要旨`、`司马谈六家论` 三页共存。

**发现方法**：
```bash
# 检测相似标题（编辑距离或关键词重叠）
python3 wiki/scripts/butler/discover_kg.py --mode dup-titles

# 查看 alias_conflicts.json 中同 surface 指向多页的情况
python3 wiki/scripts/butler/reflection_scan.py --aspect alias
```

**处理流程**：
1. 阅读所有候选重复页，判断内容关系：
   - 完全重复 → 删除一个，保留链接（用 REDIRECT 指向保留页）
   - 部分重叠 → 合并内容到主页，删除次页，改 REDIRECT
   - 上下级关系 → 保留两页，但在各自开头互链说明关系
2. 合并时，保留内容更丰富的版本，将另一版本的独特信息补入
3. 被删除/合并的页面改为 REDIRECT 页（见 §三）
4. 更新所有链接到旧页面的反向链接

**优先级**：
- P0：同 canonical_name 的重复页（同一人/事/概念两个 md 文件）
- P1：标题高度相似（编辑距离 ≤ 3，或含相同关键词）
- P2：内容 Jaccard 相似度 > 0.6（需脚本检测）

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
| **每 10 轮**一次（与 W5 反思错开）| 扫描一次重复页面候选，更新 housekeeping_queue.md 的 P0 列表 |
| **每轮末尾**（轻量）| 检查当轮新建页面是否触发 H3（新页面的 aliases 是否已有 REDIRECT） |
| **用户指出**（即时）| 将用户报告的问题直接加入 P0 |
| **butler 执行 H 任务**| 每次 trail 队列无 P0/P1 时，检查 housekeeping_queue.md，处理一条 P0 |

---

## 四、合并操作规范（H1 详细步骤）

1. **读取所有候选页**，列出各自独有的内容
2. **确定主页**（canonical）：通常选内容更丰富、质量分更高的页面
3. **内容合并**：
   - 将次页独有内容逐条补入主页适当位置
   - 保持主页的结构风格
   - 如内容有冲突，以主页为准并在评析节注明分歧
4. **修改次页为 REDIRECT**：
   - 完全替换 frontmatter（type 改为 redirect，加 redirect_to）
   - body 改为两行简短说明
5. **更新反向链接**：用 `grep -rl "[[次页名]]"` 找到所有链接到次页的 md，
   逐一改为指向主页（必要时加消歧语法）
6. **record_revision**：主页和次页（REDIRECT）各一次
7. **不得删除文件**：改为 REDIRECT 而非 rm，保持 URL 有效

---

## 五、注意事项

- ❌ **禁止批量替换链接**（会超过 20 行 diff 不变量）——每次只改一个文件
- ❌ **禁止合并内容差异很大的页面**（超过 50 行内容差异 → 人工裁决）
- ✅ **合并后必须 W6 检查主页**（合并后可能引入新的引文问题）
- ✅ **REDIRECT 页格式固定**，前端渲染器依赖 `type: redirect` 字段

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
- `wiki/data/alias_conflicts.json` — 自动检测的 alias 冲突
- `wiki/data/duplicate_candidates.json` — 潜在重复页候选
- `wiki/scripts/butler/reflection_scan.py` — 扫描工具
- `skills/SKILL_W5_Butler反思与自改.md` — 系统级反思（互补）
- `skills/SKILL_W9_Butler页面图式反思.md` — 内容级反思（互补）
