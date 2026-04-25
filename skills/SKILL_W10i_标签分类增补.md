---
name: SKILL_W10i_标签分类增补
title: Wiki 内务整理 H8：标签分类增补
description: 为 tags 字段为空或标签数不足2个的页面批量补充时代/类型/主题标签，每轮最多处理10个页面。
---

# SKILL W10i: 标签分类增补（H8）

> "标签是知识的索引。没有标签的页面是孤岛，有了标签才能被归类、被发现、被列表聚合。"

---

## 一、何时执行

| 触发场景 | 优先级 |
|---|---|
| 页面 tags 为空（`tags: []`） | P2 |
| 页面 tags 数量 < 2 | P2 |
| 新建 stub 页面未加标签 | P2 |

H8 是 P2 级别，在 P0/P1 任务处理完后才执行。

---

## 二、发现候选（扫描方法）

```bash
# 扫描 tags 为空的页面
grep -l "^tags: \[\]" wiki/public/pages/*.md | head -20

# 或通过 pages.json
python3 -c "
import json
data = json.load(open('wiki/public/pages.json'))
for p in data.get('pages', []):
    tags = p.get('tags', [])
    if len(tags) < 2:
        print(f\"{len(tags)}\t{p['id']}\")
" | sort -n | head -30
```

---

## 三、标签体系

补充标签时，只能从以下已确立的标签中选择，**不自创新标签**：

### 时代标签
`春秋` `战国` `秦` `汉初` `西汉` `东汉` `上古` `夏` `商` `周`

### 类型标签（通常与 type 字段对应，可以不重复加）
`人物` `地名` `事件` `概念` `官职` `邦国` `制度`

### 主题标签
`军事` `外交` `礼制` `经济` `思想` `文学` `法制` `宫廷` `刺客` `游侠` `商贾`

### 地域标签
`秦地` `楚地` `齐地` `燕地` `赵地` `魏地` `韩地` `中原` `江南` `北方`

---

## 四、执行步骤

### Step 1：读页面内容，判断适用标签

```bash
cat wiki/public/pages/页面名.md | head -20
```

根据：
- `type` 字段（person/place/concept/event）
- 正文内容提及的时代、地域、主题
- 页面名中的关键词

### Step 2：确定 2-5 个标签

**选标签原则**：
- `type` 已明确（如 `type: person`）时，`人物` 标签可以加也可以省略
- 时代标签优先（几乎每页都应有时代标签）
- 主题标签看内容，不强行凑数
- 不超过 5 个

### Step 3：用 edit_page.py 修改 frontmatter

```bash
# 只修改 tags 字段，其他字段不动
python3 wiki/scripts/butler/edit_page.py "页面名" \
    --set-tags "战国,人物,军事" \
    --summary "w10i: 补充分类标签" \
    --author "butler"
```

若 edit_page.py 不支持 --set-tags，手动修改 frontmatter：

```yaml
# 修改前
tags: []
# 修改后
tags: [战国, 人物, 军事]
```

### Step 4：批量处理

每轮最多处理 10 个页面，diff 总量 ≤ 50 行。

---

## 五、成功标准 / 完成条件

- [ ] 每个处理的页面 tags ≥ 2 个
- [ ] 所有标签来自已确立的标签体系（无自创标签）
- [ ] `type` 字段已有时，不重复加相同含义的类型标签
- [ ] 每轮处理 ≤ 10 个页面
- [ ] **tags 只能写在 frontmatter（`---` 包围的区块）内，绝不插入正文**

---

## ⛔ 严禁：在正文插入 tags 行

**这是最常见的错误**：将 `tags: [...]` 插入正文（frontmatter 结束的 `---` 之后）。

```yaml
# ✅ 正确：tags 在 frontmatter 内
---
title: 六国合纵盟约
type: event
tags: [史记, 事件]
---

# 六国合纵盟约
...正文内容...
```

```yaml
# ❌ 错误：tags 出现在正文中间
---
title: 六国合纵盟约
type: event
tags: [史记, 事件]
---

# 六国合纵盟约
...正文内容...

tags: [史记, 事件]   ← 绝对禁止！这行无效且污染页面
---
```

**验证命令**（执行后每行输出都代表一个错误）：
```bash
python3 - <<'EOF'
import os, re
for fname in sorted(os.listdir('wiki/public/pages')):
    if not fname.endswith('.md'):
        continue
    lines = open(f'wiki/public/pages/{fname}').read().split('\n')
    if not lines[0].strip() == '---':
        continue
    fm_end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == '---'), None)
    if fm_end is None:
        continue
    for i, line in enumerate(lines[fm_end+1:], fm_end+1):
        if re.match(r'^tags:\s*\[', line):
            print(f"ERROR {fname}:{i+1} tags in body: {line.strip()}")
EOF
```

---

## 六、工具与脚本

| 工具 | 用途 |
|---|---|
| `wiki/scripts/butler/edit_page.py` | 修改 frontmatter tags |
| `discover_tags.py`（若存在） | 批量推荐标签 |
| `grep -l "tags: \[\]"` | 手动扫描空标签页面 |

---

## 七、与 W2 的关系

W2 的 `add-tag` 原子动作是单页操作。H8 是批量工序，使用相同的底层工具（edit_page.py），但按队列批量执行。

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — H8 任务队列
- `skills/SKILL_W10j_列表页建设.md` — H9，标签充足后才能有效建列表页
