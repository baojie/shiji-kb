---
name: SKILL_W10r_Stub扩展反思
title: Wiki 内务整理 H18：Stub 扩展反思
description: 对长期未更新的 stub 页面进行扩展评估：能扩展的执行 W2 enrich-infobox，确实无源的去掉 stub 标记并加说明注记，每10轮处理一批5个。
---

# SKILL W10r: Stub 扩展反思（H18）

> "Stub 是承诺，不是终点。定期检查 stub 是对读者的负责。"

---

## 一、何时执行

| 触发场景 | 说明 |
|---|---|
| 每 10 轮迭代周期执行一次 | 处理 5 个最久未动的 stub |
| H5（断链新建）建立新 stub 后 7 天 | 加入 H18 队列 |
| 用户报告某 stub 需要扩展 | 立即处理 |

---

## 二、发现候选（扫描方法）

```bash
# 找所有 stub 页面，按最后修改时间升序（最久未动的排前面）
grep -rl "^stub: true" wiki/public/pages/*.md | \
    xargs ls -lt --time=mtime 2>/dev/null | sort -k6,7 | head -20

# 或通过 pages.json
python3 -c "
import json
data = json.load(open('wiki/public/pages.json'))
stubs = [p for p in data.get('pages', []) if p.get('stub') and not p.get('stub_reviewed')]
for p in sorted(stubs, key=lambda x: x.get('last_modified', ''))[:10]:
    print(f\"{p.get('last_modified', '?')}\t{p['id']}\")
"
```

**过滤条件**：
- `stub: true`
- `stub_reviewed` 字段不存在或为 false（防止重复扫描）
- 按 `last_modified` 升序（最久未动的优先）

---

## 三、执行步骤（每批 5 个）

### Step 1：读取候选 stub 页面内容

```bash
cat wiki/public/pages/stub页.md
```

### Step 2：评估可扩展性

| 评估项 | 评估结果 |
|---|---|
| 在史记中是否有相关记载？ | 有 → 可扩展 |
| 是否已有 H4 溯源数据可用？ | 有 → 可扩展 |
| 是否是边缘人物/地名，记载极少？ | 是 → 确实无源 |

### Step 3A：可扩展 → 执行 W2 enrich-infobox

```bash
# 委托 W2 执行 enrich（参考 SKILL_W2 规范）
# 最低要求：
# 1. 补充 frontmatter 核心字段（birth/death/role等）
# 2. 补充 2-3 条史记引文
# 3. 去掉 stub: true 标记
python3 wiki/scripts/butler/edit_page.py "stub页" /tmp/expanded.md \
    --summary "w10r: H18 扩展stub（补充生平/引文）" \
    --author "butler"
```

### Step 3B：确实无源 → 添加说明，去掉 stub 标记

修改 frontmatter：
```yaml
# 删除：stub: true
# 改为：
note: "《史记》中仅有极少记载，暂无更多可确认信息。"
stub_reviewed: true
```

并在正文添加一行说明：
```markdown
（《史记》中对此人/地/事的记载极为有限，本页内容即为已知全部信息。）
```

### Step 4：记录处理结果

```bash
# 记录 revision
python3 wiki/scripts/butler/record_revision.py "stub页" \
    --summary "w10r: H18 stub审查-[已扩展/无源标记]" \
    --author butler

# 在 actions.jsonl 记录
echo '{"action": "stub_review", "page": "stub页", "result": "expanded/no_source", "date": "2026-04-25"}' \
    >> wiki/logs/butler/actions.jsonl
```

---

## 四、防止重复扫描

处理完毕后，无论结果如何，都在 frontmatter 中加入：

```yaml
stub_reviewed: true
```

下次扫描时过滤掉 `stub_reviewed: true` 的页面。

---

## 五、成功标准 / 完成条件

- [ ] 每轮处理 5 个 stub（不多不少）
- [ ] 可扩展的 stub 已补充基本内容并去掉 stub 标记
- [ ] 无源的 stub 已加 note 并标记 stub_reviewed
- [ ] 所有处理的 stub 写入 actions.jsonl
- [ ] 处理后页面无孤立 `stub: true`（要么扩展，要么变 stub_reviewed）

---

## 六、工具与脚本

| 工具 | 用途 |
|---|---|
| `grep -rl "^stub: true"` | 扫描 stub 页面 |
| `wiki/scripts/butler/edit_page.py` | 扩展 stub 内容 |
| `wiki/scripts/butler/record_revision.py` | 记录处理 |
| `wiki/logs/butler/actions.jsonl` | 批量操作记录 |

---

## 七、与 H5 的关系

H5（W10f）建立 stub → 自动加入 H18 队列 → H18 在后续轮次扩展

| 阶段 | 负责方 |
|---|---|
| 建立占位 stub | H5（W10f）|
| 扩展或标记无源 | **H18（本文）** |

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — H18 任务队列
- `wiki/logs/butler/actions.jsonl` — 批量操作记录
- `skills/SKILL_W10f_断链新建条目.md` — H5，stub 来源
