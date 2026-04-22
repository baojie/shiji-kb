---
name: skill-butler-6
description: Butler 离线质检 — 异步扫描 wiki/public/pages/ 所有词条，验证引文可溯源、事实有出处、无幻觉内容。独立于 W4 在线评估，可批量运行，输出可疑列表供人工复核或自动修复。
---

# SKILL W6: 离线质检 (Citation Integrity Check)

> **核心问题**：wiki 里的每一句话，是真的来自《史记》，还是 AI 编造的？

---

## 一、触发时机

- W5 反思发现大量新页后，主动触发
- 用户调用 `/wiki-check` 或手动运行脚本
- 每 20 次 butler invocation 自动触发一次（W5 负责调度）

---

## 二、检查项目

### 2.1 直接引文验证（最高优先级）

**规则**：页面中用引号 `"…"` 或 `>` 引用块包裹的文字，必须能在 `docs/original_text/` 中 grep 到。

> ⚠️ **验证目标是 `docs/original_text/`，不是 `chapter_md/`**
> `chapter_md/` 含标注符号 `〖〗⟦⟧〘〙` 等，直接 grep 引文会失败。
> `docs/original_text/NNN_章名.txt` 是干净原文，130篇全覆盖，是唯一可靠的字符串验证源。

```bash
# 提取页面中所有引文，逐条验证
python3 wiki/scripts/butler/check_citations.py wiki/public/pages/韩王信.md
```

**判定**：
- ✅ `grep -r "引文片段" docs/original_text/` 命中 → 通过
- ❌ 未命中 → 标记 `FABRICATED_QUOTE`，列入修复队列

### 2.2 事实断言溯源

**规则**：以下类型的断言必须有出处：
- 生卒年（与 kg 实体或 chapter_md PN 标注对得上）
- 官职/封号（chapter_md 中有 `〖;职位〗` 标注）
- 重要事件（chapter_md 中有对应段落，或 kg/events 中有记录）
- 人物关系（kg 中有对应关系边）

**验证方法**：
```bash
# 检查人物页的 birth_ce/death_ce 是否与 kg 一致
python3 wiki/scripts/butler/check_facts.py --page 韩王信 --check lifespan
```

### 2.3 内容来源比例

每个精品页（featured: true）需满足：
- 至少 60% 的内容段落能追溯到 `chapter_md` 具体章节
- 不得有超过 2 段"纯推断性"文字（无任何原文支撑）

---

## 三、输出格式

扫描完成后写入 `logs/wiki_butler/citation_issues.jsonl`，每行一个问题：

```json
{
  "ts": "2026-04-23T10:00",
  "page": "韩王信",
  "issue_type": "FABRICATED_QUOTE",
  "severity": "critical",
  "content": "生为汉臣，死为汉鬼，岂有异哉",
  "grep_result": "not_found",
  "action": "delete_and_replace",
  "status": "open"
}
```

`severity` 级别：
- `critical`：直接引文无法在原文找到（必须修）
- `warning`：断言无出处（建议修）
- `info`：出处存在但标注不规范（可选修）

---

## 四、修复流程

### 自动修复（critical 级别）

Butler 可自动执行：
1. 删除无法溯源的引文，替换为 `<!-- [W6质检删除] ... -->` 占位符
2. 将该页 `featured: false`，降级为普通页
3. **调用 `record_revision.py` 写入修订历史**（不可省略，与人工编辑同等要求）

```bash
# --fix-critical 自动触发 record_revision.py
python3 wiki/scripts/butler/check_citations.py --fix-critical wiki/public/pages/韩王信.md
```

> ⚠️ **编辑接口规范（W0 不变量§3）**：所有修改 `wiki/public/pages/*.md` 的操作——
> 无论是 Butler 脚本、`fix_critical`，还是人工直接编辑——**都必须随后调用**：
> ```bash
> python3 wiki/scripts/butler/record_revision.py <slug> --summary "W6质检/fix-critical: ..." --author butler
> ```
> 跳过此步骤将导致修订历史断档，页面变更对用户不可见。

### 人工复核（warning 级别）

Butler 生成修复建议，但不自动执行：
1. 在 `citation_issues.jsonl` 标记 `action: human_review`
2. 在 W5 反思报告中列出清单
3. 等待用户确认或提供正确出处

---

## 五、check_citations.py 规格

`wiki/scripts/butler/check_citations.py` 需实现：

```
输入: 页面路径（或 --all 扫全部）
输出: citation_issues.jsonl 追加

检查逻辑:
1. 提取页面中所有 "…"/"…" 引号内文字 和 > 引用块
2. 清洗标点空格，取核心片段（≥8字，去掉省略号两端）
3. grep -r "片段" docs/original_text/ --include="*.txt"
   ← 必须用 docs/original_text/，不用 chapter_md/
   ← chapter_md/ 含标注符号，字符串匹配会误判未命中
4. 未命中 → FABRICATED_QUOTE (critical)
5. 检查 frontmatter birth_ce/death_ce 与 kg 实体对比
6. 统计无出处段落比例
```

脚本状态：`待实现`（W5 可在下轮反思中推入 TODO）

---

## 六、质检覆盖计划

| 阶段 | 范围 | 预期问题数 |
|---|---|---|
| 第一轮（立即）| featured: true 的 44 个精品页 | 预计 5–20 处 critical |
| 第二轮（1周内）| 全部 224 个人物页 | 预计 50–200 处 warning |
| 持续 | 每次 butler 写新页后增量扫 | 按页增量 |

---

## 七、与其他 Skill 的关系

- **W3**：定义溯源红旗（W6 是批量实现）
- **W4**：单页在线检查（W6 是离线批量检查）
- **W5**：W6 发现的 critical 问题自动进入下轮反思议程

---

## 八、非目标

- 不检查语言风格（那是可读性问题，W3 维度5）
- 不验证历史解释的"正确性"（只验证是否来自《史记》）
- 不做跨史书比对（只验证知识库内部一致性）

---

## 相关

- [W3 质量标准](SKILL_W3_Butler质量标准.md) — 溯源红旗定义
- [W4 评估与检验](SKILL_W4_Butler评估与检验.md) — 步骤0溯源验证
- `wiki/scripts/butler/check_citations.py` — 待实现的验证脚本
- `logs/wiki_butler/citation_issues.jsonl` — 质检结果日志
