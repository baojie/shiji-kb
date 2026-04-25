---
name: SKILL_W10f_断链新建条目
title: Wiki 内务整理 H5：断链新建条目
description: 统计 wiki 中被多个页面引用但目标页不存在的断链（红链），优先为高频断链建立最小可用 stub 页面。
---

# SKILL W10f: 断链新建条目（H5）

> "红链是未来的蓝链。高频红链说明知识库缺少一块重要拼图。"

---

## 一、何时执行

| 触发场景 | 优先级 |
|---|---|
| 同一链接目标在 ≥3 个页面中出现，但目标页不存在 | P1 |
| H2（词汇链接化）发现词汇无对应页 | P1 |
| 1-2 个页面的引用红链 | P2 |

---

## 二、发现候选（扫描方法）

```bash
# 从 pages.json 统计高频断链（若字段存在）
python3 -c "
import json
data = json.load(open('wiki/public/pages.json'))
broken = {}
for p in data.get('broken_wikilinks', []):
    broken[p['target']] = broken.get(p['target'], 0) + 1
for t, cnt in sorted(broken.items(), key=lambda x: -x[1])[:20]:
    print(f'{cnt}\t{t}')
"

# 手动扫描：找 [[词]] 格式但无对应文件
grep -roh '\[\[[^\]|]*\]\]' wiki/public/pages/*.md | \
    sed 's/.*\[\[\(.*\)\]\]/\1/' | sort | uniq -c | sort -rn | \
    while read cnt name; do
        [ ! -f "wiki/public/pages/${name}.md" ] && echo "$cnt $name"
    done | head -20
```

---

## 三、执行步骤

### Step 1：统计并排序断链频率

列出目标页不存在的链接，按被引用次数降序排列。

### Step 2：判断类型

| 链接格式特征 | 推断类型 |
|---|---|
| 人名（单字或两字姓名） | person |
| 以"之战"、"之盟"结尾 | event |
| 以"郡"、"县"、"国"结尾 | place |
| 抽象概念词 | concept |
| 章节名（NNN_X列传/本纪） | chapter |

### Step 3：建立 stub 页面

**最小 stub 模板**：

```markdown
---
id: 页面名
type: person  # 或 place/concept/event
label: 页面名
stub: true
tags: []
---

# 页面名

（待补充）

## 史记引文

（待补充原文引文）
```

```bash
python3 wiki/scripts/butler/add_page.py "页面名" /tmp/stub.md \
    --summary "w10f: 新建stub（高频断链，N处引用）" \
    --author "butler"
```

### Step 4：确认建立成功

```bash
ls wiki/public/pages/页面名.md
```

### Step 5：更新队列

在 `housekeeping_queue.md` 中将该条目标记为 `done`，并可顺手加入 H18 队列（等待 Stub 扩展）。

---

## 四、成功标准 / 完成条件

- [ ] 每轮最多建 3 个 stub
- [ ] stub 必须包含：id、type、label、stub: true、一行描述占位、`## 史记引文` 节
- [ ] 建立后原有红链变为有效蓝链
- [ ] 新建的 stub 同步加入 H18（Stub扩展反思）队列

---

## 五、工具与脚本

| 工具 | 用途 |
|---|---|
| `pages.json` 的 `broken_wikilinks` 字段 | 系统级断链统计 |
| `wiki/scripts/butler/add_page.py` | 建立新页面 |
| `grep -roh '\[\[.*\]\]'` | 手动扫描链接 |

---

## 六、常见误判

| 误判 | 说明 |
|---|---|
| 把章节引用（`[[052_X列传]]`）视为断链 | 章节页有自己的路径，确认前先检查 `type: chapter` 页 |
| 为极低频（1次）红链建 stub | P2 级别，优先处理 ≥3 次引用的 |
| stub 内容写太多 | stub 就是占位，内容扩展是 H18 的任务 |

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — H5 任务队列
- `skills/SKILL_W10r_Stub扩展反思.md` — H18，stub 建立后转入此队列
- `skills/SKILL_W10c_词汇链接化.md` — H2，发现词汇无页面时触发 H5
