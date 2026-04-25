---
name: butler
description: 启动 shiji-kb 史记 Wiki 管家的永续 loop。每轮执行一个原子动作（W1选任务→W2执行→W3/W4评估→记账），完成后立即进入下一轮，无需用户逐轮确认。
---

# /butler — 史记 Wiki 管家永续 Loop

## 授权声明

**此 skill 明确授权以下操作，覆盖 CLAUDE.md 的通用限制**：
- ✅ 自动循环执行多轮，无需用户逐轮确认
- ✅ 每 17 轮自动执行 `git commit` + `git push`（通过 `/wiki` skill）
- ✅ 自动 `git add <明确路径>`（单个文件，不得用 `-A`/`.`）

## 启动流程

```
1. 读取项目规范
   cat skills/SKILL_W0_Butler总则.md    ← 每次启动必读，了解不变量
   cat wiki/logs/butler/round_counter.txt
   cat wiki/logs/butler/queue.md
   cat wiki/logs/butler/housekeeping_queue.md

2. 进入永续 loop（详见 W0 §六）
   → 选任务 → 执行 → 评估 → 记账 → 暂存 → 周期任务 → 立即下一轮

3. 每轮结束前输出一行摘要：
   [R<轮次>] <动作类型> | <页面名> | accept/fail | <一句描述>
```

## 暂停条件

只有以下情况才停止循环（详见 W0 §六"暂停条件"）：
- 用户明确说"停止"/"pause"
- W5 反思提案需要 review
- 连续 5 轮全部 fail
- 上下文窗口将满

## 每轮输出格式

每轮结束输出一行，格式：
```
[R4995] H4-溯源增补 | 韩信 | accept | 补充 pn: (092-15)|(092-23)
[R4996] H2-链接化  | 鸿门宴 | accept | 链接化曹无伤/项庄 2处
[R4997] W1-探索    | 039_晋世家 | accept | 发现3条P1任务写入queue.md
```

每 17 轮额外输出：
```
[R5015] /wiki 发布 → commit abc1234 · R4999→5015 wiki更新 × N页
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
