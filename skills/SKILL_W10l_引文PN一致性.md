---
name: SKILL_W10l_引文PN一致性
title: Wiki 内务整理 H11：引文 PN 一致性核查
description: 发现页面史记引文节中引文内容与原文不符、或 PN 编号指向错误段落的 issues，写入核验队列交由 W7 修复。W10l 只负责发现，不执行引文修改。
---

# SKILL W10l: 引文 PN 一致性（H11）

> "引文是知识库的信用。一个错误的引文比没有引文危害更大——它以权威的姿态传播错误。"

---

## 一、何时执行

| 触发场景 | 优先级 |
|---|---|
| W7 核验脚本报告 issues 后，汇总到 H11 队列 | P1 |
| 用户报告某页引文与原文不符 | P0 |
| 精品页建设（W8）前的前置检查 | P1 |
| 每 30 轮迭代周期做一次全量扫描 | P2 |

**重要**：H11 只负责**发现候选**并写入核验队列，**修复由 W7 执行**。

---

## 二、发现候选（来源渠道）

### 渠道1：check_citations 脚本

```bash
# 若脚本存在
python3 wiki/scripts/butler/check_citations.py --max 20

# 输出：引文文本与原文段落的相似度分数
# 低于阈值（< 0.8）的视为疑似不一致
```

### 渠道2：W7 运行后的标记

```bash
# 查看 W7 产生的 issues 文件
cat wiki/logs/butler/citation_issues.jsonl | python3 -c "
import json, sys
for line in sys.stdin:
    d = json.loads(line)
    if d.get('status') == 'open':
        print(f\"{d['severity']}\t{d['page']}\t{d['detail']}\")
"
```

### 渠道3：人工发现

在浏览页面时，发现引文内容与直觉不符 → 记录待核验。

---

## 三、执行步骤（H11 的职责范围）

### Step 1：收集疑似 issues

从上述渠道收集疑似引文不一致的条目。

### Step 2：快速初判（去噪）

```bash
# 读取疑似 issue 页面的引文节
grep -A5 "## 史记引文" wiki/public/pages/疑似页.md
```

| 初判结果 | 处理 |
|---|---|
| 引文明显与上下文不符（人名/事件对不上） | 保留，写入 W7 队列 |
| 引文有细微用字差异（可能是版本差异） | 保留，标注"可能是版本差异" |
| 引文看起来合理 | 移出 issues 列表，标记为 `false_positive` |

### Step 3：写入 W7 执行队列

```bash
# 在 wiki/logs/butler/citation_issues.jsonl 中追加条目
echo '{"page": "页面名", "pn": "052-23", "issue": "引文文本与原文不符", "severity": "P1", "status": "pending_w7", "discovered": "2026-04-25"}' \
    >> wiki/logs/butler/citation_issues.jsonl
```

同时在 `housekeeping_queue.md` 写入 H11 条目：

```markdown
- [ ] H11 | P1 | [[页面名]] | 引文PN(052-23)疑似不准确，待W7核验
```

---

## 四、成功标准 / 完成条件

- [ ] 扫描完成，issues 列表更新
- [ ] 每条 issue 有：page/pn/issue描述/severity/status 字段
- [ ] 初判去噪后，false_positive 标记正确
- [ ] 写入 W7 队列，等待 W7 执行修复
- [ ] 本轮未直接修改任何引文内容

---

## 五、工具与脚本

| 工具 | 用途 |
|---|---|
| `check_citations.py` | 批量检测引文与原文相似度 |
| `wiki/logs/butler/citation_issues.jsonl` | issues 存储与 W7 队列 |
| `wiki/scripts/butler/record_revision.py` | W7 修复后的 revision 记录（W7 使用）|

---

## 六、与 H4 和 W7 的区分

| 场景 | 归属 |
|---|---|
| 页面有断言但完全没有 PN 引注 | H4（W10e）：溯源增补 |
| 页面有 PN 引注但引文内容与原文不符 | **H11（本文）**：发现 → W7 核验修复 |
| W7 执行核验和修复 | W7（`SKILL_W7_引文真实性核验.md`）|

---

## 相关路径

- `wiki/logs/butler/citation_issues.jsonl` — issues 存储（H11 写入，W7 消费）
- `wiki/logs/butler/housekeeping_queue.md` — H11 任务队列
- `skills/SKILL_W7_引文真实性核验.md` — 执行引文核验和修复
- `skills/SKILL_W10e_原文溯源增补.md` — H4，缺 PN 时走此流程
