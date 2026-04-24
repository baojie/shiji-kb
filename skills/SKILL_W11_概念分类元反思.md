---
name: SKILL_W11
title: Butler 概念分类元反思
description: 每10轮执行一次的顶级反思——审查所有页面是否在正确分类，发现需要新建的概念页
---

# SKILL_W11 — 概念分类元反思

## 何时触发

`round_counter.txt` 中当前轮次 **mod 10 == 0** 时，在本轮正常原子动作之前执行。
输出日志写入 `wiki/logs/butler/type_audits/YYYY-MM-DD-R<N>.md`。

## 执行步骤

### Step 1 — 类型分布快照

```bash
python3 - << 'PYEOF'
import json
from collections import Counter, defaultdict
with open('wiki/public/pages.json') as f:
    pages = json.load(f)['pages']
types = Counter(p.get('type','(无)') for p in pages.values())
for t, n in types.most_common():
    print(f'{t:15} {n}')
PYEOF
```

记录各类型数量，与上次审计对比变化。

### Step 2 — 错误分类候选扫描

扫描以下可疑情形：

| 情形 | 检查方法 |
|------|---------|
| `type: event` 但内容是方法论/综述 | 标题含"方法论/完整分析/框架" |
| `type: concept` 但内容是事件叙述 | 内容含具体年份/战役/人名 ≥5 |
| `type: overview` 但应升级为 `concept` | 单一抽象概念，无具体史事 |
| `type: topic` 残余（已废弃） | 全部迁移至 overview 或 concept |
| 无 `type` 字段 | 补充 overview（默认）或具体类型 |

```bash
python3 - << 'PYEOF'
import json, os, re
with open('wiki/public/pages.json') as f:
    pages = json.load(f)['pages']

suspects = []
for pid, meta in pages.items():
    t = meta.get('type','')
    label = meta.get('label', pid)
    path = f'wiki/public/pages/{pid}.md'
    if not os.path.exists(path):
        continue
    with open(path, encoding='utf-8') as f:
        content = f.read(500)
    
    # 事件页但标题含方法论关键词
    if t == 'event' and any(kw in label for kw in ['方法论','完整分析','框架','步骤','策略']):
        suspects.append(('event→overview', pid, label))
    # topic 残余
    elif t == 'topic':
        suspects.append(('topic→?', pid, label))
    # 无类型
    elif not t:
        suspects.append(('无类型→overview', pid, label))

for reason, pid, label in suspects[:30]:
    print(f'{reason:20} {label[:50]}')
print(f'\n总计 {len(suspects)} 个可疑页面')
PYEOF
```

### Step 3 — 新概念发现

从以下来源寻找应补充的概念页：

1. **高频被引用但无独立页的词**：
   ```bash
   python3 wiki/scripts/build_wanted_pages.py --top 20
   ```

2. **overview 页中反复出现的抽象主题**：
   - 浏览最近 20 篇 overview 的标题，提取跨篇反复出现的主题词
   - 若 ≥3 篇 overview 涉及同一抽象概念（如"功高震主"、"刎颈之交"）且无独立 concept 页 → 列为候选

3. **现有 concept 页应拆分的**：
   - concept 页正文 > 2000 字且涵盖多个独立子概念 → 候选拆分

### Step 4 — 产出审计报告

写入 `wiki/logs/butler/type_audits/YYYY-MM-DD-R<N>.md`，格式：

```markdown
# 类型审计 R<N> — YYYY-MM-DD

## 类型分布快照
（各类型数量表格）

## 错误分类候选（≤10条，按优先级排）
| 页面 | 当前类型 | 建议类型 | 理由 |
|------|---------|---------|------|

## 新概念候选（≤5条）
| 候选概念 | 依据（哪几篇 overview 提到） |
|---------|--------------------------|

## 本轮行动
- [ ] 执行 N 条分类修正（下 N 轮每轮1条）
- [ ] 创建 M 条新概念页（加入 queue.md P1）
```

### Step 5 — 分类修正执行规则

- 每条分类修正 = 1 个原子动作（改 frontmatter 中的 `type` 字段）
- diff ≤ 3 行，作为正常 trail action 计数
- action 名称：`reclassify`，commit message：`butler/reclassify: <slug> event→overview`
- 新发现的概念候选加入 `wiki/logs/butler/queue.md` P1 段

## 成功标准

- 审计报告已写入 type_audits/
- 错误分类候选 < 5 条（或全部计划修正）
- 本轮内完成 ≥1 条分类修正（若有候选的话）

---

## KB 写入规则

W11 审计确认某分类规则后，将定论写入 `wiki/logs/butler/kb/w11_taxonomy.md`：

- **写什么**：已在多页验证的类型判断规则、已完成的批量分类修正记录
- **不写什么**：单页特例、仍有争议的分类
- **格式**：`- [R<N> 确认] <条件> → <类型>` 追加到对应类型分组
- **用途**：reclassify 动作前必读，确保分类修正与已有规则一致
