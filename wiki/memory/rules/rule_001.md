---
id: rule_001
confidence: high
source: failures.jsonl 2026-04-24（修改 pn 时错误联动修改了 event_ids）
created: 2026-04-24
last_updated: 2026-04-24
---

修改 `pn` 字段时不得联动修改 `event_ids`，反之亦然。两者是完全独立的体系：
- `event_ids`：事件结构化编号（如 `[094-010, 097-003]`），有自己的命名规则
- `pn`：史记原文段落引用号 Purple Numbers（如 `(094-10) | (097-6)`），用于定位原文

**Evidence:** 2026-04-24 将 pn `(097-3.1)` 改为 `(097-6)` 时错误地将 event_ids `097-003` 改成了 `097-006`
**Scope:** 所有 wiki 页面 :::meta 块编辑操作
