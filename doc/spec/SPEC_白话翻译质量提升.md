# SPEC：借助外部白话版本迭代反思翻译 Agent 提示词

**状态**：规划中（2026-04-22）
**关联**：[`SKILL_01h_白话翻译.md`](../../skills/SKILL_01h_白话翻译.md)

---

## 0. 最终产物与北极星

**最终产物**：一份经过多轮实证迭代的**翻译 Agent 提示词**（即 `SKILL_01h §Translation Agent提示词` 章节），其质量在独立抽检中显著优于当前版本。

**北极星指标**：给定新章节或重译旧章节，使用新提示词生成的译文，与当前版本相比：
- 与外部参考的分歧率下降 ≥30%
- 术语一致率上升 ≥15 个百分点
- 高危 issue 数下降 ≥50%
- 人工抽检评分平均分提升 ≥0.5（1-5 分制）

**核心循环**：
```
  Phase 1-4（诊断）
        ↓
  发现本库译文的系统性缺陷
        ↓
  归纳为提示词可表述的规则
        ↓
  更新 SKILL_01h 提示词
        ↓
  挑 5-10 章用新提示词重译
        ↓
  对同样指标再测
        ↓  收敛？→ 发布 | 未收敛 → 回到归纳
```

所有其他阶段（对齐、报告、分歧检测、术语表、译文修订）都是**喂给这个迭代循环的证据**。译文修订本身不是终点；**写进提示词的规则**才是。

---

## 1. 背景

本库白话译文（`doc/translation/NNN_*_白话.md`）由大模型逐章生成。虽已做多轮校对、消歧继承与 surface 翻译规范化，仍存在：

- **LLM 幻觉**：个别句意偏离原文
- **术语不一致**：同一人/地/官在不同章译法不统一
- **细节漏译/添译**：少量细节可能丢失或被补充
- **文风参差**：多 agent 分工翻译，风格不完全一致

目前项目获取了两部外部参考版本：

| 版本 | 路径 | 特点 |
|------|------|------|
| **hunterhug 段译** | `corpus/shiji/段译/NNN_*_段译.txt` | 130 章，**段级原文—白话对照**，空行分段 |
| **白话史记（整本）** | `corpus/shiji/白话史记.txt` | 整本白话，**仅白话无原文对齐** |
| **点校本繁体** | `corpus/shiji/点校本/NNN_*_点校本.txt` | 120 章繁体原文，用于原文勘误（不是白话源） |

目标：**系统利用这两部白话参考，把本库译文提升到接近学术校勘级的质量**，且过程可审计、可回退、可度量。

---

## 2. 设计原则

1. **我们的版本是主版本**：外部参考仅作辅助，最终权威仍是本库带标注的译文
2. **PN 级可追溯**：所有改进都落在 PN 粒度，保证可对照回原文与标注
3. **先审后改**：自动检测仅产出候选，真正修改需人工审阅或显式批准的规则
4. **实体标注不被破坏**：任何自动修改都必须通过 `sync_translation_disambig.py` 审核
5. **演化友好**：外部源会更新，脚本幂等可重跑

---

## 3. 三版本资产的结构映射

| 资产 | 粒度 | 对齐锚点 | 备注 |
|------|------|---------|------|
| 本库 `doc/translation/NNN_*_白话.md` | PN（`## [N]` / `## [N.M]`） | 与 `chapter_md/NNN.tagged.md` 严格对齐 | 含实体标注 |
| 段译 `corpus/shiji/段译/` | 段落（`【原文】`/`【译文】` 对） | 原文字面匹配 | 无标注 |
| 整本 `corpus/shiji/白话史记.txt` | 段落/句 | 需通过文本相似度匹配 | 分章边界明显（目录+章名标题） |

**对齐策略**：
- hunterhug 段译：把每个 `【原文】` 段与 `chapter_md` 的 PN 文本做**最长公共子串**匹配，同一章内贪心吸附
- 白话史记整本：先按章名切分为 130 段；再在每章内用**原文段落 → 对应位置**的启发式（目前只能对齐到"章内某处"的模糊区间）

---

## 4. 六阶段路线图

### Phase 1 — 对齐基础设施（2 天，脚本优先）

**产出**：
- `scripts/align_external_translations.py`
  - 输入：`chapter_md/NNN*.tagged.md` + `corpus/shiji/段译/NNN_*_段译.txt` + `corpus/shiji/白话史记.txt`
  - 输出：`data/translation_alignment/NNN.json`，结构：
    ```json
    {
      "pn": "1.1",
      "source": "在帝尧的时候，洪水...",
      "ours":     "在〖@帝尧〗的时候，...",
      "hunterhug": "当尧帝在位的时候，...",
      "baihua":   "尧帝在位时...",
      "alignment_confidence": 0.92
    }
    ```
- `data/translation_alignment/STATS.md`：每章对齐率、平均置信度

**算法**：
- hunterhug 已按"原文段"切好；用 `difflib.SequenceMatcher` 将每段匹配到覆盖最长的 PN
- 白话史记无原文；按章名切分 → 章内用"句数比例"粗估 PN 区间

### Phase 2 — 三栏对照审阅表（1 天）

**产出**：
- `scripts/build_triple_diff_report.py`
- 输出：`reports/translation_diff/NNN_章节名.md`
  ```
  ## [1.1]

  **原文**：在帝尧的时候，洪水滔天...
  **本库**：〖@帝尧〗时候，洪水...
  **hunterhug**：当尧帝在位的时候，洪水...
  **白话史记**：尧帝在位时，洪水...

  ---
  ```

**用途**：
- 人工挑章抽检
- 作为 GitHub Pages 发布，供读者参与纠错

### Phase 3 — 自动分歧检测（3 天，LLM 辅助）

**产出**：
- `scripts/detect_translation_disagreement.py`（Claude API 批量调用）
  - Prompt：三版本比对，输出 `{category, severity, suggested_fix}` 之一：
    - `no_issue`
    - `terminology`（术语分歧，如官名译法）
    - `factual_divergence`（事实性分歧，一方可能错）
    - `missing_detail`（本库漏译）
    - `extra_detail`（本库添译）
  - 严重度：low / medium / high
- 输出：`reports/translation_issues/NNN.md`，按 severity 排序，包含 PN 与建议修正

**成本控制**：
- 默认使用 Haiku；high severity 触发 Sonnet 复审
- 缓存结果，仅重新检测变更的 PN

### Phase 4 — 术语一致性表（2 天）

**产出**：
- `scripts/extract_terminology_from_external.py`
  - 从外部两版本提取"文言 surface → 白话 surface"的统计分布
  - 输出：`data/terminology_external.json`
    ```json
    {
      "@": {
        "籍": {"ours": "羽", "hunterhug": "项籍/项羽", "baihua": "项羽"}
      },
      "=": {
        "江": {"ours": "长江", "hunterhug": "长江", "baihua": "长江"}
      }
    }
    ```
- `scripts/audit_terminology.py`
  - 与 `data/terminology_external.json` 对比本库用法
  - 报告本库有争议译法的条目，供决策

### Phase 5 — 从证据到提示词规则（迭代核心，3-5 天 / 轮）

**这是最关键的一步**——把 Phase 3/4 发现的系统性问题"压缩"成提示词可执行的规则。

**输入**：
- Phase 3 的 `reports/translation_issues/NNN.md`（分歧条目）
- Phase 4 的 `data/terminology_external.json`（术语分布）
- Phase 2 的三栏对照（抽样细读）

**产出**：`doc/translation_quality/vN_分析.md`，包含：
- **模式归纳**：把 issue 聚类为 5-15 类典型问题（如"官职过度意译"、"时间 surface 未规范化"、"原文代词未补全为人名"）
- **根因判断**：每一类是提示词缺指令 / 指令被忽视 / 指令冲突 / 本质无法通过提示词解决
- **规则草稿**：可直接插入 SKILL_01h 的提示词片段（含正反例）

**提示词更新**：
- 改动 [`SKILL_01h_白话翻译.md §Translation Agent 提示词`](../../skills/SKILL_01h_白话翻译.md)
- 每次改动记 `v1 → v2 → ...`，diff 贴进 `doc/translation_quality/vN_diff.md`
- **保留旧版本**：通过 git history 可回溯

**示例迭代**（设想）：
> v1 发现：40% issue 源于"代词未显化"（文言"帝"白话该译"帝尧"）
> v2 在提示词加入："代词和隐去的主语必须补全为明确的实体名，引用已出现过的实体"
> v2 重译 5 章，该类 issue 降至 8% ✓

### Phase 6 — 提示词验证与回归（每轮 2 天）

**流程**：
1. 选 5-10 章作为**评估集**（覆盖本纪/世家/列传/书，含短/中/长）
2. 用 vN+1 提示词重译这些章
3. 跑 Phase 3 分歧检测，对比 vN 译文的指标：
   - 分歧率
   - 高危 issue 数
   - 术语一致率
   - 新引入问题数（重要：避免过拟合某类，牺牲另一类）
4. 人工抽检 50 个 PN，双盲评分 vN vs vN+1
5. 记 `doc/translation_quality/vN+1_evaluation.md`

**判决**：
- **接受**：指标全面改善 → merge 到 SKILL_01h，更新主版本
- **条件接受**：部分改善 → 发 PR 征求评审，记录权衡
- **拒绝**：退化或某维度大幅退步 → rollback，回 Phase 5 分析为何规则未起效

**发布**：
- 每次接受后在 CHANGELOG 记录：提示词版本号、指标变化、核心规则变动
- 累计 3-5 轮迭代后，考虑用新提示词**全量重译**（运行成本高，择时）

---

## 5. 目录与文件约定

```
corpus/shiji/
├── 段译/                   # hunterhug 原文-白话对照
├── 白话史记.txt            # 整本白话
└── 点校本/                 # 点校本繁体原文

data/translation_alignment/  # Phase 1 产物（机读）
├── NNN.json
└── STATS.md

reports/                     # 供人阅读的报告
├── translation_diff/NNN_章节名.md    # Phase 2 三栏对照
└── translation_issues/NNN.md         # Phase 3 分歧候选

scripts/
├── align_external_translations.py     # Phase 1
├── build_triple_diff_report.py        # Phase 2
├── detect_translation_disagreement.py # Phase 3 (需 Claude API)
├── extract_terminology_from_external.py # Phase 4
├── audit_terminology.py               # Phase 4
└── fix_terminology.py                 # Phase 5（可选）

logs/translation_improvements/YYYY-MM-DD.md  # 译文改动日志
doc/translation_quality/                      # 提示词迭代日志（核心产物）
├── v1_baseline.md       # 当前提示词的基线指标
├── v2_分析.md            # 从 Phase 3 证据归纳的问题模式
├── v2_diff.md            # SKILL_01h 提示词的具体改动
├── v2_evaluation.md      # 评估集上的回归测试
└── vN_...
```

---

## 6. 风险与边界

| 风险 | 缓解 |
|------|------|
| 外部版本自身有错 | 多数票 + 原文文意 + 人工裁决；永不盲信单一外部版本 |
| 对齐错误导致错报 | 记录 `alignment_confidence`，低置信条目不进入 Phase 3 |
| LLM 检测成本膨胀 | 默认 Haiku + 缓存；仅增量检测变更 PN |
| 实体标注被误伤 | 所有改动后必跑 `sync_translation_disambig.py --all` 审核 |
| 外部版权与引用合规 | 外部白话在 `corpus/shiji/` 仅作内部参考，GitHub Pages 发布前需与原作者确认许可 |

---

## 7. 里程碑

| 里程碑 | 预计 | 验收标准 |
|--------|------|---------|
| M1：对齐基础 | D+2 | 130 章 PN 与 hunterhug 段译对齐率 >85%；`STATS.md` 生成 |
| M2：三栏对照 | D+3 | 10 章样本报告通过人工检视 |
| M3：分歧扫描一轮 | D+7 | 全库扫描完成，每章 issue 报告产出；**v1 基线指标写入 `doc/translation_quality/v1_baseline.md`** |
| M4：术语表 | D+9 | `terminology_external.json` 覆盖 >1000 条 surface |
| M5：**提示词 v2** | D+12 | 归纳出 5-10 条规则写入 SKILL_01h；评估集回归测试指标全面不退化 |
| M6：**提示词 v3** | D+18 | 对 v2 遗留问题再迭代；累计分歧率较 v1 降 ≥30% |
| M7：全量重译 | 择时 | 用稳定提示词重译全 130 章；最终版本发布 |

---

## 8. 开放问题

1. **白话史记整本的 PN 对齐**：仅靠句数比例粗估可能漂移。是否需要人工标章内锚点？
2. **分歧裁决的权威**：当两部外部版本都与本库不同时，谁是权威？默认策略建议：**以原文文意为准**，人工裁决写入 `data/terminology_decisions.json`
3. **是否发布三栏对照页**：涉及外部内容版权；需先与源作者确认

---

**最后更新**：2026-04-22
**待办**：根据反馈修订后进入 Phase 1 开发
