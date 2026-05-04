---
name: butler
description: 启动 shiji-kb 史记 Wiki 管家的永续 loop。每轮执行一个原子动作（W1选任务→W2执行→W3/W4评估→记账），完成后立即进入下一轮，无需用户逐轮确认。支持多实例并行（--instance/--focus）。
---

# /butler — 史记 Wiki 管家永续 Loop

## 授权声明

**此 skill 明确授权以下操作，覆盖 CLAUDE.md 的通用限制**：
- ✅ 自动循环执行多轮，无需用户逐轮确认
- ✅ 每 23 轮自动执行 `git commit` + `git push`（通过 `/wiki` skill）
- ✅ 自动 `git add <明确路径>`（单个文件，不得用 `-A`/`.`）

## 启动参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--instance <名>` | 命名实例（太史令/列传家/注疏者/索隐者/刊行者） | `--instance 注疏者` |
| `--focus <类型>` | 专注任务类型（all/create/enrich/housekeeping/publish） | `--focus enrich` |

无参数启动 = 太史令模式（all，领取任意任务）。

**多实例并发示例**：
```bash
/butler --focus enrich --instance 注疏者      # agent A
/butler --focus create --instance 列传家      # agent B（同时启动）
```

## 启动流程

```
1. 读取项目规范
   cat skills/SKILL_W0_Butler总则.md    ← 每次启动必读，了解不变量
   cat wiki/logs/butler/round_counter.txt
   cat wiki/logs/butler/queue.md
   cat wiki/logs/butler/housekeeping_queue.md

2. ⚠️ 启动强制检查（在做任何工作前）：
   # 重复实例检测（有 --instance 时必须检查）
   python3 wiki/scripts/butler/claim_round.py --check-only --instance <实例名>
   若输出 DUPLICATE → 立即停止，勿启动

   grep '"reflect-w5"' wiki/logs/butler/actions.jsonl | tail -1   ← 读 round 字段
   cat wiki/logs/butler/round_counter.txt                         ← 当前 round
   若 (当前 round - 上次 W5 round) > 50 → 立即执行 W5 反思，再进入工作循环
   若未超 50 → 直接进入工作循环

3. 进入永续 loop（详见 W0 §六）
   → 领锁 → 选任务 → 注册页面 → 执行 → 评估 → 记账 → 释放锁 → 暂存 → 周期任务 → 立即下一轮

4. 每轮结束前输出一行摘要：
   [R<轮次>][实例] <动作类型> | <页面名> | accept/fail | <一句描述>
```

## 每轮锁操作规范

```bash
# 步骤3a：领取轮次锁（每轮开始时必须调用）
ROUND=$(python3 wiki/scripts/butler/claim_round.py --instance <实例名>)

# 步骤3b：候选确定后注册目标页面
python3 wiki/scripts/butler/lock_manager.py set-page --round $ROUND --page <页面名>

# 步骤3c：写入前检测冲突
python3 wiki/scripts/butler/lock_manager.py check-page --page <页面名> --round $ROUND
# exit 1 = 冲突，跳过此页，换下一个候选

# 步骤3d：写入（add_page.py / edit_page.py）+ 记账
python3 wiki/scripts/butler/record_action.py \
    --round $ROUND --action <类型> --page <页面名> --status accept \
    --instance <实例名> --note "<描述>" --reflect "<观察>"

# 步骤3e：释放锁（每轮末尾必须调用，即使 fail/skip）
python3 wiki/scripts/butler/release_round.py $ROUND
```

**周期任务（W5/publish）用 increment_round + --skip-lock-check**：
```bash
ROUND=$(python3 wiki/scripts/butler/increment_round.py)
# ... 执行 W5 或 /wiki ...
python3 wiki/scripts/butler/record_action.py --round $ROUND --action publish \
    --page wiki --status accept --skip-lock-check --note "R...→... × N页"
```

## 暂停条件

只有以下情况才停止循环（详见 W0 §六"暂停条件"）：
- 用户明确说"停止"/"pause"
- W5 反思提案需要 review
- 连续 5 轮全部 fail
- 上下文窗口将满

## 每轮输出格式

每轮结束输出一行，格式（有实例名时带方括号标注）：
```
[R10813][注疏者] enrich-biography | 韩信 | accept | 补全战役年表，散文2节
[R10814][列传家] create-page      | 苏武 | accept | 从匈奴列传创建人物页
[R10815][索隐者] fix-links        | 鸿门宴 | accept | 链接化曹无伤/项庄 2处
```

每 23 轮额外输出：
```
[R10823][刊行者] /wiki 发布 → commit abc1234 · R10801→10823 wiki更新 × 23页
```

## 工作目录

```
/home/baojie/work/knowledge/shiji-kb
```

所有路径均相对于此目录。

## 相关 Skill

- [W0 总则](../../../skills/SKILL_W0_Butler总则.md) — 不变量、闭环哲学、暂停条件
- [W1 食物收集](../../../skills/SKILL_W1_Butler探索与食物收集.md) — 三队列选取算法
- [W2 原子行动](../../../skills/SKILL_W2_Butler原子行动目录.md) — 具体动作执行
- [W10 内务整理](../../../skills/SKILL_W10_Butler内务整理.md) — H1-H20 调度
- [多实例设计](../../../skills/SKILL_Butler多实例设计.md) — 并发锁机制、命名实例体系、并发安全矩阵

## 可用工具 Skill（执行动作时可调用）

| Skill | 触发方式 | 用途 |
|-------|----------|------|
| `/map PAGE [时代]` | 页面 type=place 且 frontmatter 有 `coords`，需配谭图 | 自动裁切《中国历史地图集》；**调用时必须加 `--write`**（自动写 frontmatter + 记 revision），否则 Special:Recent 不可见 |
| `/quote PAGE` | 需要补全 `## 史记引文` 节 | 扫描实体标注文件，找实体级引用（非裸字符匹配），精确到年表行 |
| `/enrich PAGE [目标档]` | 需要升级页面质量档位 | 诊断质量缺口（节/散文/引文/图），执行补充操作并验证 |

**Butler 何时调用这些 Skill**：
- `add-war-map`：改为调用 `map_page.py PAGE --write`（若页面有 `coords`），否则走原有手动流程
- `enrich-biography` / `premium-upgrade`：先调用 `/quote PAGE` 收集引文候选，再写散文；或直接调用 `/enrich PAGE featured/premium`
- `fetch-image` 已确认无 Wikimedia 图，页面 type=place：调用 `map_page.py PAGE --write` 作为替代配图方案
