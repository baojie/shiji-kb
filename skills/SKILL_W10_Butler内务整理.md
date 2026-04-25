---
name: SKILL_W10_Butler内务整理
title: Wiki 质量迭代主循环（Housekeeping Master Loop）
description: W10 是 wiki 质量迭代的总调度循环。每 10 轮为一个迭代周期：评估健康度指标→按优先级取任务→委托子 SKILL 执行→记录结果→更新队列。每 30 轮执行元反思（H14）。
---

# SKILL W10: Wiki 质量迭代主循环

> "知识库的质量 = 内容正确性 × 结构整洁性 × 文本覆盖完整性。W3-W9 保证内容，W10 保证结构与完整性的持续改善。"

---

## 一、定位与职责

**W10 是总调度循环，不包含各 H 类型的执行细节。**

- W10 负责：评估健康度、优先级排序、任务分配、结果记录
- 子 SKILL 负责：具体的扫描、判断、修改操作

---

## 二、Wiki 健康度指标体系

每个迭代周期开始时，评估以下指标：

| 指标 | 说明 | 目标值 | 计算方式 |
|---|---|---|---|
| **K（知识量）** | 总字符数 | 持续增长 | `wc -c wiki/public/pages/*.md \| tail -1` |
| **link_density** | 有 wikilink 的页面占比 | > 80% | pages 中 wikilink_count > 0 的比例 |
| **stub_ratio** | stub 页面占比 | < 10% | stub=true 页面 / 总页面数 |
| **source_coverage** | 有 PN 引注的页面占比 | > 60% | pn 字段非空的页面 / 总页面数 |
| **citation_error_rate** | 引文核验 issue 数 / 总引文数 | < 2% | citation_issues.jsonl open 条目数 |
| **disambiguation_coverage** | 多义词有消歧义页的占比 | > 90% | type=disambiguation 覆盖高频多义词比例 |

```bash
# 快速健康度快照
echo "=== Wiki 健康度快照 $(date +%Y-%m-%d) ==="
echo "总页面数: $(ls wiki/public/pages/*.md | wc -l)"
echo "Stub 页面: $(grep -rl '^stub: true' wiki/public/pages/ | wc -l)"
echo "有 PN 的页面: $(grep -rl '^\(pn:\|pn: \)' wiki/public/pages/ | wc -l)"
echo "待处理 citations: $(grep -c '"status": "open"' wiki/logs/butler/citation_issues.jsonl 2>/dev/null || echo 0)"
echo "待处理 housekeeping: $(grep -c '^\- \[ \]' wiki/logs/butler/housekeeping_queue.md 2>/dev/null || echo 0)"
```

---

## 三、子 SKILL 索引（H1–H20）

| 类型 | 名称 | 优先级 | 子 SKILL 文件 |
|---|---|---|---|
| **H1** | 重复/冗余页面融合 | P0 | `SKILL_W10a_Butler去重合并.md` |
| **H2** | 词汇链接化 | P1 | `SKILL_W10c_词汇链接化.md` |
| **H3** | 重定向页管理 | P1 | `SKILL_W10d_重定向页管理.md` |
| **H4** | 原文溯源增补 | P1 | `SKILL_W10e_原文溯源增补.md` |
| **H5** | 断链新建条目 | P1 | `SKILL_W10f_断链新建条目.md` |
| **H6** | 随机页面优化诊断 | P2 | `SKILL_W10g_随机页面优化.md` |
| **H7** | 精品页候选识别 | P2 | `SKILL_W10h_精品页增补.md` → 委托 W8 |
| **H8** | 标签分类增补 | P2 | `SKILL_W10i_标签分类增补.md` |
| **H9** | 列表页候选识别 | P2 | `SKILL_W10j_列表页建设.md` → 委托 W12 |
| **H10** | 页面错误反思分诊 | P0/P1 | `SKILL_W10k_页面错误反思.md` → 委托 W9 |
| **H11** | 引文 PN 一致性发现 | P1 | `SKILL_W10l_引文PN一致性.md` → 委托 W7 |
| **H12** | 节级重复内容整合 | P1 | `SKILL_W10m_重复内容整合.md` |
| **H13** | 史记全文覆盖查验 | P1 | → 委托 W13（`SKILL_W13_史记全文覆盖查验.md`）|
| **H14** | 元反思（每30轮） | P2 | → 委托 W5（`SKILL_W5_Butler反思与自改.md`）|
| **H15** | 语法标注符号清理 | P1 | `SKILL_W10p_语法标注清理.md` |
| **H16** | 消歧义页改造 | P1 | `SKILL_W10b_消歧义页改造.md` |
| **H17** | 章节概览语义块建设 | P2 | `SKILL_W10q_章节语义块.md` |
| **H18** | Stub 扩展反思 | P2 | `SKILL_W10r_Stub扩展反思.md` |
| **H19** | 正文断言 PN 核验 | P1 | `SKILL_W10s_正文断言核验.md` |
| **H20** | 洞察探索队列管理 | P2 | `SKILL_W10t_洞察探索.md` → 委托 W14 |
| **H21** | 首页精品页全面升级 | P1 | `SKILL_W10u_首页精品页升级.md` |

---

## 四、迭代周期节奏（每 10 轮）

### 轮次 1–2：健康度评估 + 队列补充

```bash
# 1. 快照健康度指标
# 2. 运行扫描器补充队列
python3 wiki/scripts/butler/discover_duplicates.py --max-new 5       # H1
python3 wiki/scripts/butler/find_unsourced.py --max 10 --write-queue  # H4
python3 wiki/scripts/butler/reflection_scan.py --aspect alias          # H3
grep -rl '〖\|⟦' wiki/public/pages/ | head -5  # H15 候选
python3 wiki/scripts/butler/discover_homepage_new.py                  # H21 新晋首页
```

### 轮次 3–8：执行任务

按优先级顺序从队列取任务：

```
P0 优先：
  → H1（去重合并）→ 委托 W10a
  → H10（错误分诊）→ 委托 W10k

P1 次之（按 H 编号顺序）：
  → H2（链接化）→ W10c
  → H3（重定向）→ W10d
  → H4（溯源）→ W10e
  → H5（断链）→ W10f
  → H11（引文）→ W10l → W7
  → H15（标注清理）→ W10p
  → H16（消歧义）→ W10b
  → H19（断言核验）→ W10s

P2 填充（队列空时）：
  → H6（随机诊断）→ W10g
  → H8（标签）→ W10i
  → H17（章节概览）→ W10q
  → H18（stub扩展）→ W10r
```

**每轮只处理一条任务**，完成后记录，再取下一条。

### 轮次 9：记录结果

```bash
# 记录本周期操作到 actions.jsonl
echo '{"cycle": N, "completed": [...], "added_to_queue": [...], "date": "YYYY-MM-DD"}' \
    >> wiki/logs/butler/actions.jsonl
```

### 轮次 10：更新队列 + 下周期准备

```bash
# 清理已完成（[x]）条目，统计各类任务完成数
grep -c '^\- \[x\]' wiki/logs/butler/housekeeping_queue.md

# 写入周期小结
# 决定下周期优先事项
```

---

## 五、特殊节奏

| 频率 | 触发的任务 |
|---|---|
| **每 10 轮** | 健康度快照 + 批量扫描（H1/H3/H4）+ H21 新晋首页扫描 |
| **每 20 轮** | H7（精品页识别）+ H9（列表页识别）|
| **每 30 轮** | H14（元反思，委托 W5）|
| **每 10 轮最后 1-2 轮** | H6（随机诊断，5页抽样）|
| **每 10 轮第 5 轮** | H18（Stub 扩展，5个一批）|

> H21 新晋首页扫描：`python3 wiki/scripts/butler/discover_homepage_new.py`
> 找出在首页但未打「首页精品」tag 的页面，加入 H21 升级队列。
> H21 升级完成后，必须在该页面 tags 追加「首页精品」作为认证标志。

---

## 六、队列格式

文件：`wiki/logs/butler/housekeeping_queue.md`

```markdown
# Housekeeping 队列

最后更新: YYYY-MM-DD

## P0（立即处理）

- [ ] H1 | 司马谈论六家要指 + 司马谈论六家要旨 | 三页同文，需合并
  发现: 2026-04-25 用户报告
- [ ] H10 | [[某页]] | W9扫描：frontmatter 缺 label 字段
  发现: 2026-04-25 W9扫描

## P1（本周内处理）

- [ ] H2 | [[鸿门宴]] | 正文3处人名未链（曹无伤/项庄/靳彊）
- [ ] H4 | [[韩王成]] | 缺溯源，建议pn: (007-96) | (055-7)
- [ ] H15 | [[某章节页]] | 残留 〖◆〗 标注符号 12 处

## P2（积压）

- [ ] H8 | [[白马之盟]] | tags 为空
- [ ] H18 | [[靳彊]] | stub 建于 2026-04-10，至今未扩展
```

---

## 七、队列为空时的兜底策略

当 P0/P1 队列为空时，按以下顺序触发扫描补充队列：

```
H1 → H15 → H16 → H19 → H13 → H5 → H11 → H14 → H20 → H6
```

每次只触发一类扫描，生成 ≤5 个新条目，不立即执行。

---

## 八、各 Agent 对 W10 的输出接口

| Agent | 产出 | W10 接收为 |
|---|---|---|
| W5 | 反思建议，skill 修订 | H14 执行结果 |
| W7 | 引文核验 issues | H11 来源；H10 P0 条目 |
| W9 | 结构异常 issues | H10 来源 |
| W13 | 覆盖率地图，未覆盖段落 | H13 → P2 队列 |
| W14 | 洞察假设 | H20 接收 → insight_queue.md |

---

## 相关路径

| 路径 | 说明 |
|---|---|
| `wiki/logs/butler/housekeeping_queue.md` | 主任务队列 |
| `wiki/logs/butler/actions.jsonl` | 操作历史记录 |
| `wiki/logs/butler/citation_issues.jsonl` | 引文 issues（H11/H10）|
| `wiki/logs/butler/insight_queue.md` | 洞察队列（H20）|
| `wiki/logs/butler/failures.jsonl` | 无法处理的记录 |
| `wiki/scripts/butler/discover_duplicates.py` | H1 扫描 |
| `wiki/scripts/butler/find_unsourced.py` | H4 扫描 |
| `wiki/scripts/butler/reflection_scan.py` | H3/H10 扫描 |
| `wiki/scripts/butler/edit_page.py` | 页面编辑（各子 SKILL 使用）|
| `wiki/scripts/butler/record_revision.py` | revision 记录 |
