---
name: SKILL_W10d_重定向页管理
title: Wiki 内务整理 H3：重定向页管理
description: 为实体的别名/异称建立 REDIRECT 页，确保搜索任何称呼都能找到规范页。核心：扫描 aliases 字段，为无对应 REDIRECT 页的别名批量建立重定向。
---

# SKILL W10d: 重定向页管理（H3）

> "每一个别名背后，都是一个用户可能用来搜索的词。让每条路都通向罗马。"

---

## 一、何时执行

| 触发场景 | 优先级 |
|---|---|
| 页面 `aliases` 字段有值，但无对应 REDIRECT 页 | P0 |
| 用户搜索某称呼找不到页面，而该词是已知别名 | P0 |
| 批量扫描发现 aliases 覆盖率低 | P1 |

---

## 二、发现候选（扫描方法）

```bash
# 扫描 aliases 字段中缺 REDIRECT 的情况
python3 wiki/scripts/butler/reflection_scan.py --aspect alias

# 手动检查：读某页面的 aliases 字段
grep -A3 "^aliases:" wiki/public/pages/人物名.md

# 检查对应别名是否有页面
ls wiki/public/pages/ | grep "别名"
```

**判断逻辑**：
1. 读页面 frontmatter 中的 `aliases:` 列表
2. 对每个别名，检查 `wiki/public/pages/{别名}.md` 是否存在
3. 不存在则加入 H3 队列

---

## 三、执行步骤

### Step 1：读取候选页面的 aliases

```bash
grep -B1 -A10 "^aliases:" wiki/public/pages/规范页名.md
```

列出所有别名，逐一检查哪些缺少 REDIRECT 页。

### Step 2：确认规范页存在

```bash
ls wiki/public/pages/规范页名.md
```

若规范页不存在，先解决规范页问题（可能需要 H1 去重），再建 REDIRECT。

### Step 3：建立 REDIRECT 页

```bash
# 为每个缺失别名建立 REDIRECT 页
python3 wiki/scripts/butler/edit_page.py "别名" /tmp/redirect.md \
    --summary "w10d: 为规范页名建立别名REDIRECT（别名）" \
    --author "butler"
```

REDIRECT 页格式（参考 SKILL_W10a 第五节）：

```markdown
---
id: 别名
type: redirect
label: 别名
redirect_to: 规范页名
---

# 别名

> **重定向**：本页重定向至 [[规范页名]]。
>
> "别名"是"规范页名"的别称/异名。
```

### Step 4：处理别名冲突

若别名已被另一实体占用（如 "子胥" 既是伍子胥别名，也可能指他人）：

| 情形 | 处理 |
|---|---|
| 别名唯一对应规范页 | 直接建 REDIRECT |
| 别名有歧义（对应多个实体） | 建消歧义页（转 H16/W10b），不建 REDIRECT |
| 别名已有内容页 | 不覆盖，加 hatnote 互链 |

### Step 5：记录处理结果

```bash
python3 wiki/scripts/butler/record_revision.py "别名" \
    --summary "w10d: REDIRECT→规范页名" \
    --author butler
```

---

## 四、成功标准 / 完成条件

- [ ] 规范页 aliases 字段中的所有别名均有对应 REDIRECT 页或消歧义页
- [ ] REDIRECT 页格式正确（type: redirect + redirect_to 字段）
- [ ] 无别名冲突（同一别名不指向两个不同规范页）
- [ ] 每轮处理别名数 ≤ 10 个

---

## 五、工具与脚本

| 工具 | 用途 |
|---|---|
| `reflection_scan.py --aspect alias` | 批量扫描 aliases 缺 REDIRECT |
| `wiki/scripts/butler/edit_page.py` | 建立 REDIRECT 页 |
| `wiki/scripts/butler/record_revision.py` | 记录 revision |

---

## 六、与 H1/H16 的区分

| 场景 | 归属 |
|---|---|
| 两页内容重复，一页改 REDIRECT | H1（W10a）|
| 多义词，原内容页改消歧义页 | H16（W10b）|
| aliases 字段中的别名无对应页面 | **H3（本文）** |

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — H3 任务队列
- `skills/SKILL_W10a_Butler去重合并.md` — REDIRECT 格式规范参考
- `skills/SKILL_W10b_消歧义页改造.md` — 别名有歧义时转 H16
