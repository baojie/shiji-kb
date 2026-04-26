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
# 找所有 quality=stub 页面，按最后修改时间升序（最久未动的排前面）
python3 -c "
import json
data = json.load(open('wiki/public/pages.json'))
pages = data.get('pages', {})
stubs = [{'id': k, **v} for k, v in pages.items() if v.get('quality') == 'stub']
for p in sorted(stubs, key=lambda x: x.get('id', ''))[:10]:
    print(f\"{p.get('type','?'):12} {p['id']}\")
"
```

**过滤条件**：
- `quality: stub`（由 compute_quality.py 自动评定）
- 按类型+字母排序（优先处理 person/place 类型）

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
# 2. 补充 2-3 条史记引文（使 content ≥ 500 字且有节结构）
# 3. 扩展后运行 compute_quality.py 重评（应升至 basic 或 standard）
python3 wiki/scripts/butler/edit_page.py "stub页" /tmp/expanded.md \
    --summary "w10r: H18 扩展stub（补充生平/引文）" \
    --author "butler"
python3 wiki/scripts/compute_quality.py "stub页"
```

### Step 3B：确实无源 → 添加说明，quality 维持 stub

在正文添加一行说明（frontmatter 不需要额外字段，quality 自动保持 stub）：
```markdown
（《史记》中对此人/地/事的记载极为有限，本页内容即为已知全部信息。）
```

**注**：不再使用 `stub_reviewed` 字段，`quality=stub` 本身即表示已被评估为最低级别。

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

## 四、处理后验证

```bash
# 处理完毕后，重新评估 quality（应从 stub 晋级为 basic 或更高）
python3 wiki/scripts/compute_quality.py <slug>

# 若仍为 stub，说明扩展不够，检查内容是否 < 100 字或无节结构
```

---

## 五、成功标准 / 完成条件

- [ ] 每轮处理 5 个 quality=stub 页面（不多不少）
- [ ] 可扩展的 stub 已补充基本内容，compute_quality.py 重评后升至 basic 或以上
- [ ] 确实无源的 stub 已加说明注记，quality 维持 stub（可接受）
- [ ] 所有处理的 stub 写入 actions.jsonl

---

## 六、工具与脚本

| 工具 | 用途 |
|---|---|
| `python3 wiki/scripts/compute_quality.py --dry-run` | 扫描并统计各级 quality 分布 |
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
