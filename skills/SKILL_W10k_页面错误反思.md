---
name: SKILL_W10k_页面错误反思
title: Wiki 内务整理 H10：页面错误反思与分诊
description: 汇集 W9 图式扫描、用户报告、引文核验等来源的页面错误 issues，按严重程度分诊，P0 立即修复，P1 加入队列等待批量处理。
---

# SKILL W10k: 页面错误反思（H10）

> "错误的发现比错误的修复更难。H10 是分诊台，确保每个 issue 进入正确的处理通道。"

---

## 一、何时执行

| 触发场景 | 优先级 |
|---|---|
| W9 图式扫描报告结构异常 | P1 |
| 用户报告某页内容错误 | P0 |
| W7 引文核验发现引文与原文不符 | P0 |
| 每 10 轮迭代周期运行一次 W9 扫描 | P1 |

**注意**：H10 汇集 issues 并分诊，具体修复委托给 W9（结构问题）或 W7（引文问题）。

---

## 二、发现候选（来源渠道）

### 渠道1：W9 图式扫描

```bash
# 运行 W9 扫描器（若脚本存在）
python3 wiki/scripts/butler/reflection_scan.py --full --max 10
```

输出结构异常：节顺序错误、frontmatter 缺字段、链接格式错误等。

### 渠道2：引文核验 issues

```bash
# 查看 citation_issues.jsonl
cat wiki/logs/butler/citation_issues.jsonl | tail -20
```

### 渠道3：用户报告

用户在对话中直接指出某页有错误 → 立即加入 P0 队列。

---

## 三、分诊规则

| Issue 类型 | 严重程度 | 处理方式 |
|---|---|---|
| 引文与史记原文不符（内容错误） | P0 | 立即委托 W7 修复 |
| 事实性错误（年代/人物关系错误） | P0 | 立即修复（edit_page.py）|
| 节顺序错误（如引文节在前言前） | P1 | 加队列，W9 批量处理 |
| frontmatter 缺必要字段 | P1 | 加队列，edit_page.py 修复 |
| 链接格式错误（如 `[[` 未闭合） | P1 | 加队列，可批量处理 |
| 标注符号泄漏（〖◆〗残留） | P1 | 加 H15（W10p）队列 |
| 格式问题（空行过多/标题级别错） | P2 | 积累后批量处理 |

### P0 立即修复流程

```bash
# 1. 读取有问题的页面
cat wiki/public/pages/问题页.md

# 2. 确认错误位置和正确内容
# 3. 用 edit_page.py 修复
python3 wiki/scripts/butler/edit_page.py "问题页" /tmp/fixed.md \
    --summary "w10k: P0修复-[错误类型描述]" \
    --author "butler"

# 4. 记录 revision
python3 wiki/scripts/butler/record_revision.py "问题页" \
    --summary "w10k: 修复[错误描述]" \
    --author butler
```

---

## 四、Issues 存储格式

```bash
# 写入 wiki/logs/butler/page_issues.jsonl
echo '{"page": "页面名", "type": "frontmatter_missing", "severity": "P1", "detail": "缺 label 字段", "discovered": "2026-04-25", "status": "open"}' \
    >> wiki/logs/butler/page_issues.jsonl
```

---

## 五、成功标准 / 完成条件

- [ ] P0 issues 在当轮修复（不拖延）
- [ ] P1/P2 issues 写入 `page_issues.jsonl` 和 `housekeeping_queue.md`
- [ ] 每轮处理 P0 issues ≤ 3 个（避免超范围）
- [ ] 分诊记录完整（每条 issue 有 page/type/severity/detail 四个字段）

---

## 六、工具与脚本

| 工具 | 用途 |
|---|---|
| `reflection_scan.py --full` | W9 图式扫描 |
| `wiki/logs/butler/citation_issues.jsonl` | 引文核验 issues 来源 |
| `wiki/logs/butler/page_issues.jsonl` | H10 汇集的 issues 存储 |
| `wiki/scripts/butler/edit_page.py` | P0 立即修复 |
| `wiki/scripts/butler/record_revision.py` | 记录修复 revision |

---

## 七、与 W7/W9 的职责分工

| 职责 | 负责方 |
|---|---|
| 图式结构扫描（发现结构 issues） | W9 |
| 引文真实性核验（发现引文 issues） | W7 |
| **汇集所有 issues，统一分诊调度** | **H10（本文）** |
| P0 内容/事实错误修复 | H10 直接处理 |
| P1 结构问题批量修复 | W9 执行 |
| P1 引文修复 | W7 执行 |

---

## 相关路径

- `wiki/logs/butler/page_issues.jsonl` — issues 存储文件
- `wiki/logs/butler/housekeeping_queue.md` — H10 任务队列
- `skills/SKILL_W9_Butler页面图式反思.md` — 结构问题修复
- `skills/SKILL_W7_引文真实性核验.md` — 引文问题修复
