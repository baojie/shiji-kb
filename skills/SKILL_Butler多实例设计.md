---
name: butler-multi-instance
title: Butler 多实例并发设计
description: 史记 Wiki 管家多实例并发架构，含两层锁机制、命名实例体系和 JSONL 日志规范
---

# Butler 多实例并发设计

> 当前生产架构。单实例运行时不需要关注本文；并发启动多实例时必须遵守本文。

---

## 一、设计目标

多个命名实例（太史令 / 列传家 / 注疏者 / 索隐者 / 刊行者）可**完全并发**运行，
互不干扰——前提是同一轮内不操作同一页面。

---

## 二、两层锁架构

### 层 1：轮次锁（round-level）

由 `claim_round.py` 管理，保证每个轮次编号全局唯一、不重复分配。

```bash
ROUND=$(python3 wiki/scripts/butler/claim_round.py --instance 注疏者)
```

底层：`lock_manager.py` 使用自旋 `O_CREAT|O_EXCL` 创建 `round_counter.lock`（极短持有），
原子递增 `round_counter.txt`，创建 `round_<N>.lock` 文件。
两个实例并发调用时，计数器互斥，各拿到不同轮号，不阻塞。

**锁文件示例**（`wiki/logs/butler/round_10813.lock`）：
```json
{"round": 10813, "instance": "注疏者", "pid": 12345,
 "ts": "2026-04-28T10:00:00Z", "pages": ["韩信", "项羽"]}
```

### 层 2：页面锁（page-level）

候选准备完成后、执行写入前，为每个候选页面注册并检测冲突：

```bash
# 注册：把 slug 写入本轮 lock 文件的 pages 列表
python3 wiki/scripts/butler/lock_manager.py set-page --round $ROUND --page 韩信

# 检测：扫描所有活跃 round_*.lock，若其他轮次已注册同页 → exit 1（冲突）
python3 wiki/scripts/butler/lock_manager.py check-page --page 韩信 --round $ROUND
```

冲突处理：从候选列表移除该页，从缓冲池补充，**不重新搜索**。

---

## 三、轮次锁生命周期

```
claim_round.py              → 创建 round_N.lock（pages=[]）
lock_manager set-page       → pages 追加候选 slug（步骤5候选准备后批量调用）
lock_manager check-page     → 每个候选写前检测（exit 1=冲突）
add_page.py / edit_page.py  → 实际写入页面
record_revision.py          → 更新 history/*.jsonl + recent.jsonl
record_action.py            → 写 actions.jsonl（内部调用 assert_owner 验证锁仍有效）
release_round.py <ROUND>    → 删除 round_N.lock（即使本轮 fail/skip 也必须调用）
```

**严格规则**：持锁期间禁止新的搜索（候选必须在领锁前全部确定）。

---

## 四、命名实例体系

| 实例名 | `--instance` | `--focus` | 职责 | 角色隐喻 |
|--------|-------------|-----------|------|----------|
| **太史令** | 太史令 | `all` | 通用，领取任意任务 | 太史令总领史馆，无参数默认身份 |
| **列传家** | 列传家 | `create` | 新建人物/事件词条 | 执笔列传，留传后世 |
| **注疏者** | 注疏者 | `enrich` | 丰富内容，升级档位 | 三家注精研，裴骃/司马贞/张守节 |
| **索隐者** | 索隐者 | `housekeeping` | 清链接、修质量、内务 | 索隐考据，辨正讹误 |
| **刊行者** | 刊行者 | `publish` | 定期 `/wiki` 发布 | 刊刻流传，广布天下 |

### 并发启动示例

```bash
# 单独启动（太史令模式）
/butler

# 并发两实例（各专一项）
/butler --focus enrich --instance 注疏者      # agent A
/butler --focus create --instance 列传家      # agent B（同时启动）

# 全四实例
/butler --focus create       --instance 列传家
/butler --focus enrich       --instance 注疏者
/butler --focus housekeeping --instance 索隐者
/butler --focus publish      --instance 刊行者
```

---

## 五、重复实例检测

同一实例名不应同时运行两个副本。启动时必须检测：

```bash
python3 wiki/scripts/butler/claim_round.py --check-only --instance 注疏者
# exit 0 → 无同名实例，可启动
# exit 1 → stdout 输出 "DUPLICATE"，立即停止
```

---

## 六、周期任务的锁豁免

`/wiki` 发布、W5 反思等周期任务不走 claim_round → release 流程：

```bash
ROUND=$(python3 wiki/scripts/butler/increment_round.py)
# ... 执行 /wiki 或 W5 ...
python3 wiki/scripts/butler/record_action.py \
    --round $ROUND --action publish --page wiki \
    --status accept --skip-lock-check \
    --note "R10790→10813 wiki更新 × 23页 commit abc123"
```

原因：周期任务不写 `pages/*.md`，无需页面锁；
强制持轮次锁会阻塞其他并发实例。

---

## 七、并发安全矩阵

| 场景 | 安全 | 原因 |
|------|------|------|
| 两实例同时 `claim_round.py` | ✅ | 计数器互斥锁保证唯一轮号 |
| 两实例操作不同页面 | ✅ | check-page 扫描无冲突 |
| 两实例操作同一页面 | ✅（冲突检测） | check-page exit 1，后者跳过该页 |
| `record_revision.py` 并发写 | ✅ | history/*.jsonl 用 flock；recent.jsonl 用 O_APPEND |
| `actions.jsonl` 并发写 | ✅ | open('a') 原子追加 |
| 同名实例同时启动 | ✅（启动检测） | --check-only 在步骤1阻止重复启动 |
| 周期任务与普通轮次并发 | ✅ | 周期任务用 --skip-lock-check，不争锁 |

---

## 八、JSONL 日志体系（已实现）

| 文件 | 格式 | 并发保护 |
|------|------|----------|
| `wiki/logs/butler/actions.jsonl` | 每行一条动作记录 | open('a') 原子追加 |
| `wiki/public/history/<slug>.jsonl` | per-page 修订历史 | fcntl.flock 排他锁 |
| `wiki/public/recent.jsonl` | 全局修订日志（滚动1000行） | open('a') 原子追加 |
| `wiki/logs/recent/recent.N.jsonl` | 归档批次（永久保留） | 不并发写 |

**actions.jsonl 字段规范**：
```json
{
  "round":    10813,
  "ts":       "2026-04-28T10:00:00Z",
  "action":   "enrich-biography",
  "page":     "韩信",
  "status":   "accept",
  "note":     "补全战役年表与陈仓/垓下引文，散文2节",
  "instance": "注疏者",
  "reflect":  "淮阴侯列传篇幅长，引文命中率极高"
}
```

可选字段：`instance`（命名实例）、`reflect`（一句话观察，供 W5 扫描）

---

## 九、已知限制

1. **周期任务多实例重复触发**：多实例同时到达 `round % 23 == 0` 时均会尝试发布。
   靠 `/wiki` skill 检查 git 状态跳过空提交。
2. **W5 反思各自独立**：多实例的 W5 结论不共享，全局视角时应由太史令单独执行。
3. **锁超时（10min）**：`round_N.lock` 超过 600 秒被视为超时，自动清理。
   持锁时间超出此值时，`record_action.py` 报锁失效，需加 `--skip-lock-check` 补录。

---

## 十、关键脚本速查

| 脚本 | 用途 |
|------|------|
| `lock_manager.py` | 统一锁 API（Python 模块 + CLI） |
| `claim_round.py` | 并发安全领取轮次锁 |
| `release_round.py` | 释放轮次锁（每轮末尾必调） |
| `increment_round.py` | 周期任务专用（W5/publish，不创建持久锁） |
| `record_action.py` | 带锁验证的 actions.jsonl 记账 |
| `record_revision.py` | 带 flock 的 per-page 修订历史记录 |
