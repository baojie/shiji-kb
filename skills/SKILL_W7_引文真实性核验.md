---
name: skill-butler-6b
description: W7 增量引文真实性核验 — 三层流水线（缓存→规则→LLM），每次检查一个页面，已验证的句子不重复检查。与 W6 离线质检互补：W6 批量扫描，W7 增量精查+自动修复。
---

# SKILL W7: 增量引文真实性核验

> **核心问题**: 每个 wiki 引文是真实来自《史记》，还是 AI 编造/改写的？
> **与 W6 的分工**: W6 批量全扫（detect-only），W7 增量精查（detect+fix，用 LLM 二审）。

---

## 一、流水线

```
L0: 缓存命中（quote_cache.json，key = sha256[:16]）
      ok/llm_ok → 跳过 L1/L2，仍做 PN 比对
      fabricated/llm_fail → 完全跳过
      ↓ 未命中
L1: find_pn 规则匹配
      score ≥ 0.90 → ✅ ok，写缓存 → PN 比对
      score 0.55–0.90 → 近似命中（情况 A）→ L2 修复
      score < 0.55   → 未命中（情况 B/C）

PN 比对（quote 存在 + 有 cited PN）
      cited PN ≠ actual PN → ⚠️ WRONG_PN (warning, fix_pn)
      cited PN = actual PN → ✅

L2: l2_repair（Claude Haiku，≤8次/轮）
  情况 A：近似命中 → 提供 L1 best_entry 段落 + wiki 上下文
  情况 B：未命中 + 有 cited PN → 提供 cited PN 段落 + wiki 上下文
  情况 C：未命中 + 无 cited PN → 直接 FABRICATED，不调 LLM

  l2_repair 返回：
    replacement   → 从原文提取的正确引文（≤60字，原文字面）
    context_ok    → "yes|partial|no"（周围解释文字是否含义匹配）
    context_issue → 解释文字存在的问题描述（≤30字）

  决策：
    replacement 有效 (conf≥60%) → ⚠️ NEAR_MATCH (warning, replace_quote)
                                   若 context_ok≠yes → 附加 context_issue
    replacement 为空            → ❌ FABRICATED (critical)
```

**token 控制**：每次运行最多 8 次 LLM 调用（`MAX_LLM_PER_RUN = 8`）。

---

## 二、触发时机（在 butler 周期中的位置）

### 主触发：每 10 次 trail/explore action 后

在 `wiki/scripts/butler/PROMPT.md` 中，W5 反思计数器同时触发 W7：

```
- 若累计 atomic action ≥ 10 条未做 W7 → 插入一次 verify-citations
```

### 补充触发：queue 为空时

当 `queue.md` 无 P0/P1 任务时，butler 优先跑 W7 而非 explore。

### 手动触发

```bash
# 检查下一个未扫描页（butler 每轮调用一次即可）
python3 scripts/verify_quotes_agent.py

# 检查指定页 + 自动修复
python3 scripts/verify_quotes_agent.py --page 郑当时 --fix

# 查看覆盖进度
python3 scripts/verify_quotes_agent.py --status

# 只跑规则层（不用 LLM，速度快）
python3 scripts/verify_quotes_agent.py --llm-off
```

---

## 三、持久化文件

| 文件 | 作用 |
|------|------|
| `wiki/logs/butler/quote_cache.json` | 引文验证缓存；key = sha256(标准化引文)[:16] |
| `wiki/logs/butler/verify_state.json` | 页面扫描进度；记录已检查的页面列表 |
| `wiki/logs/butler/citation_issues.jsonl` | 问题输出；与 W6 共用（追加写） |

缓存 value 结构：
```json
{
  "status": "ok|fabricated|llm_ok|llm_fail",
  "method": "rule|llm",
  "confidence": 0.95,
  "found_pn": "120-11",
  "suggestion": "原文正确引法（LLM 提供）",
  "checked_at": "2026-04-23T..."
}
```

---

## 四、butler 动作记录

W7 运行后需写 `actions.jsonl`：

```json
{
  "ts": "2026-04-23T...",
  "mode": "observe",
  "action": "verify-citations",
  "target": "wiki/public/pages/郑当时.md",
  "rationale": "W7 增量引文核验",
  "score_before": null,
  "score_after": null,
  "red_flags": [],
  "diff_lines": 0,
  "verdict": "accept",
  "commit": null
}
```

若 `--fix` 产生了修改，需额外调用 `record_revision.py`（脚本已内置）。

---

## 五、与 W2 动作目录的集成

在 `SKILL_W2_Butler原子行动目录.md` 的 D 组（数据校验）中追加：

| 动作 | 前置 | 做什么 | 后置检查 | diff |
|---|---|---|---|---|
| `verify-citations` | 有未检查页面（verify_state.json 中 checked 未覆盖全部页面）| 跑 `verify_quotes_agent.py`，处理下一个页面 | issues 写入 citation_issues.jsonl | 0 行（仅 log）或修复行数 |

---

## 六、错误处理

- **LLM 不可用**（SDK 未装 / 网络故障）：自动降级为 L1 规则层，uncertain 案例写 `UNVERIFIED_QUOTE (warning)` 待人工复查
- **PN 索引缓存过期**：`load_index()` 自动检测 `chapter_md/` 变更并重建
- **页面路径不存在**：脚本以非零退出码报错，butler 写 failures.jsonl

---

## 七、非目标

- 不验证语言风格或文学质量
- 不做跨史书比对（仅验证《史记》+扩展文本 `corpus/other/`）
- 不处理已有 `status: fixed/rejected/skipped` 的 issues（由缓存机制覆盖）

---

## KB 写入规则

每次核验完成一个页面后，将结论写入 `wiki/logs/butler/kb/w7_citations.md`：

- **写什么**：已验证的真实直引、已确认的转述、章节可信度评级、已知常见误引
- **不写什么**：未完成核验的页面、存疑待确认的引文
- **格式**：`- [R<N> 确认] <slug>/<引文前20字> → <结论>` 追加到对应分组
- **用途**：下次核验同一引文前先查此文件，避免重复核验已确认内容
