---
name: enrich
description: 升级 shiji-kb wiki 页面质量一档（stub→basic→standard→featured→premium），或升至用户指定档。诊断页面当前指标缺口，执行对应补充操作（补引文、写散文、加节、加图）。当用户说 /enrich PAGE 或 /enrich PAGE 目标档 时触发。
---

# /enrich — 页面质量升级

## 用法

```
/enrich PAGE              → 升一档（当前质量 → 下一档）
/enrich PAGE featured     → 升至 featured
/enrich PAGE premium      → 升至 premium
```

## 质量五档门槛

| 档位 | 关键指标 |
|------|---------|
| **stub** | 内容 < 100 字，或无 H2 且 < 300 字 |
| **basic** | 内容 < 500 字，或（节 < 2 且 PN < 2） |
| **standard** | 其余（未达 featured） |
| **featured** | ≥3节 + (PN≥3 或 引文行≥5) + 散文≥200字 |
| **premium** | 有图 + ≥5节 + 散文≥1000字 + (PN≥10 或 引文行≥10 或 散文≥2500字) |

指标定义（来自 `wiki/scripts/compute_quality.py`）：
- **节**：正文 `## ` 数量
- **PN**：`（NNN-N）` 格式的段落引用数
- **引文行**：以 `> ` 开头的行数
- **散文**：≥50字、非引文/列表/标题/表格的段落总字数
- **有图**：frontmatter 含 `image:` 或 `images:`

## 执行步骤

### 第一步：诊断

读页面，运行诊断：

```bash
python3 wiki/scripts/compute_quality.py --dry-run PAGE
```

同时手动统计：节数、PN数、引文行数、散文字数、是否有图。与目标档门槛对比，列出缺口。

### 第二步：确定目标档

- 若用户未指定 → 当前档 +1
- 若已是 premium → 告知无需升档

### 第三步：按缺口执行操作

| 缺口 | 操作 |
|------|------|
| **节不足** | 按页面 type 添加标准节（见 references/section_templates.md） |
| **散文不足** | 根据已有引文写叙述性段落；补充背景、影响、历史意义等 |
| **PN/引文不足** | 运行 `/quote PAGE`，取相关度高的候选添加到 `## 史记引文` |
| **有图缺失（place）** | 运行 `/map PAGE`，把生成的 images 写入 frontmatter |
| **有图缺失（state/侯国/邦国）** | 若 frontmatter 有 `coords` → 运行 `/map PAGE`；若无 coords，先在 `## 地理位置` 末补 `<!-- TODO: 待补 coords -->`，鼓励后续补充 |
| **有图缺失（其他 type）** | 在 `## 相关页面` 后标注 `<!-- TODO: 需配图 -->`，不强行补 |

**操作优先级（同时有多个缺口时）**：
1. 先补引文（引文是散文的素材来源）
2. 再写散文（基于引文内容）
3. 再加节（补充结构）
4. 最后补图

### 第四步：验证

```bash
python3 wiki/scripts/compute_quality.py PAGE
```

确认 `quality` 已升至目标档。若未达到，检查哪个指标仍不足，继续补。

### 第五步：记录修订（必须）

```bash
python3 wiki/scripts/butler/record_revision.py PAGE \
    --summary "enrich: <旧档>→<新档>，<一句话说明做了什么>" \
    --author enrich
```

**这一步不得省略**。它将修改写入 `wiki/public/history/PAGE.json` 和 `wiki/public/recent.json`，使页面历史和最近修改视图可见。summary 格式示例：
- `enrich: basic→standard，新增侯国概况散文，补立国时间/人物/国祚`
- `enrich: standard→featured，补引文5条，扩散文至300字`

## 内容质量要求

- **引文取舍**：该实体在段落中是叙述主角，不是路过性提及（参见 `/quote` skill 的取舍标准）
- **散文风格**：叙述性、有观点，非列表堆砌；第一段应是对该实体的完整定位句
- **节标题**：简洁、与页面 type 匹配（见 references/section_templates.md）
- **⚠️史料矛盾节**：若原始引文之间有矛盾（时间/数字/说法），必须明确指出，不要回避
- **Append-only**：所有操作只能追加，不覆盖已有内容

## 快速参考：各档升级所需操作

| 升级路径 | 典型工作量 |
|---------|-----------|
| stub → basic | 写200字散文，加2节，找1-2条PN |
| basic → standard | 扩散文到500字，补节到2+，PN到2+ |
| standard → featured | 加节到3+，补引文到5行或PN到3+，散文200字+ |
| featured → premium | 加图，扩到5+节，散文1000字+，引文/PN到10+ |

详细节模板见 [references/section_templates.md](references/section_templates.md)
