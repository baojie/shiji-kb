---
name: SKILL_W10c_词汇链接化
title: Wiki 内务整理 H2：词汇链接化
description: 扫描页面正文中未加 [[]] 的人名/地名/概念词，为首次出现的词补充 wikilink，每轮最多补 5 个链接。
---

# SKILL W10c: 词汇链接化（H2）

> "链接是知识图谱的血脉。每补一条链接，就多一条知识流动的通道。"

---

## 一、何时执行

| 触发场景 | 优先级 |
|---|---|
| 主传记页面提及重要人物/地名但无 `[[]]` | P0 |
| 高频人名在多页均无链接 | P1 |
| 普通页面有未链接的概念词 | P2 |

---

## 二、发现候选（扫描方法）

```bash
# 扫描缺失链接（若脚本存在）
python3 wiki/scripts/butler/discover_kg.py --mode missing-links --max 20

# 手动扫描：找正文中出现但无 [[]] 的高频词
grep -h '.\+' wiki/public/pages/*.md | grep -v '^\[\[' | grep -v '^---' | head -200
```

或在处理单页时，逐段检查段落中出现的人名/地名/概念是否已有 wikilink。

**优先级排序**：
- P0：本纪、世家、列传主角在彼此传记中互相未链
- P1：pages.json 中 wikilink_count = 0 且类型为 person/place 的页面
- P2：其他页面中随机发现的未链词

---

## 三、执行步骤

### Step 1：确认目标词存在对应页面

```bash
ls wiki/public/pages/ | grep "目标词"
```

- 页面存在 → 可以加链接
- 页面不存在 → 先进入 H5（断链新建条目）队列，**不加红链**

### Step 2：确认是否已有链接

```bash
grep "目标词" wiki/public/pages/待处理页.md
```

- 已有 `[[目标词]]` → 跳过
- 仅首次出现未加 → 补链接

### Step 3：处理消歧义情形

| 情形 | 处理 |
|---|---|
| 词与页面名完全一致 | `[[词]]` |
| 页面名是 `词（限定词）` | `[[词（限定词）\|词]]` |
| 有消歧义页 | `[[词（限定词）\|词]]` 指向具体义项 |

### Step 4：只链第一次出现

同一页面中同一词汇**只补一个链接**（首次出现处），后续重复出现不加。

### Step 5：用 edit_page.py 写入

```bash
python3 wiki/scripts/butler/edit_page.py "页面名" /tmp/updated.md \
    --summary "w10c: 补充词汇链接（补X个）" \
    --author "butler"
```

---

## 四、成功标准 / 完成条件

- [ ] 每个新增链接的目标页均存在（无红链）
- [ ] 只链首次出现，未重复链接同一词
- [ ] 原文字符未被修改（只添加了 `[[]]`）
- [ ] diff ≤ 20 行
- [ ] 每轮补链接 ≤ 5 个

---

## 五、工具与脚本

| 工具 | 用途 |
|---|---|
| `wiki/scripts/butler/discover_kg.py --mode missing-links` | 批量扫描缺链候选 |
| `wiki/scripts/butler/edit_page.py` | 写入修改后的页面 |
| `grep -rl "词" wiki/public/pages/` | 手动查找词汇出现位置 |

---

## 六、常见误判

| 误判 | 说明 |
|---|---|
| 目标页不存在就加红链 | ❌ 先加 H5 队列，本轮跳过 |
| 链接了第二次、第三次出现 | ❌ 只链首次 |
| 把标题或 frontmatter 中的词也加链接 | ❌ 只处理正文段落 |
| 消歧义词直接用 `[[词]]` 不指向具体义项 | ⚠️ 视情况，若有消歧义页可保留指向消歧义页 |

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — H2 任务队列
- `skills/SKILL_W10_Butler内务整理.md` — 上级调度文件
- `skills/SKILL_W10f_断链新建条目.md` — 目标页不存在时转 H5
