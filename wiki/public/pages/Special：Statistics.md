---
id: "Special：Statistics"
type: special
label: 统计 (Statistics)
canonical_name: "Special：Statistics"
tags: [系统页面, 统计, 度量]
quality: standard
---

# Special:Statistics

本页展示《史记》知识库的全量统计数据，由 [`compute_knowledge.py`](../../scripts/compute_knowledge.py) 自动生成。

---

## 页面质量分布

五级质量体系（由 [`compute_quality.py`](../../scripts/compute_quality.py) 自动计算）：

| 级别 | 中文 | 标准 | 当前数量 |
|------|------|------|----------|
| `premium` | 旗舰 | 有图 + ≥5节 + 散文≥1000字 + (PN≥10 或引文≥10 或散文≥2500) | 见下方快照 |
| `featured` | 精品 | 有图 + ≥3节 + (PN≥3 或引文≥5) + 散文≥200字 | 见下方快照 |
| `standard` | 标准 | 内容≥500字且有结构，但未达精品门槛 | 见下方快照 |
| `basic` | 基础 | 内容＜500字，或节数/引注不足 | 见下方快照 |
| `stub` | 存根 | 有 stub 注释、内容＜100字、或无节结构 | 见下方快照 |

> 只有 `premium` 页面可出现在首页。

---

## 当前快照

> 数据由 [`compute_knowledge.py`](../../scripts/compute_knowledge.py) 实时计算，
> 最新值见首页 K 面板或 [`data/knowledge_latest.json`](../data/knowledge_latest.json)。

---

## 知识量（K）定义

$$K = \sum_{\text{page}} k_{\text{page}}$$

每一页的贡献值：

$$k_{\text{page}} = \log_2(1 + B) \times (1 + D) \times W \times Q$$

| 变量 | 含义 | 说明 |
|------|------|------|
| $B$ | 页面正文字节数 | 去除 frontmatter 后的 UTF-8 字节数 |
| $D$ | 链接密度（封顶 5.0） | $\min\!\left(\dfrac{\text{wikilink数}}{B/1000},\ 5.0\right)$ |
| $W$ | 类型权重 | 见下表 |
| $Q$ | 质量归一化（1.0 — 3.0） | $\text{clamp}(q/30,\ 1.0,\ 3.0)$，$q$ 为质量分 |

### 类型权重 W

| 类型 | 权重 | 理由 |
|------|------|------|
| `person` / `event` / `place` / `state` | 1.0 | 核心知识实体 |
| `topic` | 0.8 | 主题词条，略低 |
| `surface` | 0.5 | 表面索引页，内容稀薄 |
| `chapter` | 0.4 | 章节存根，体量虚低，权重压缩 |
| 其他 | 0.6 | 默认 |

---

## 历史演进

| 里程碑 | K 值 | 说明 |
|--------|------|------|
| 初始建立 | ~13,000 | 约 230 页，link_hit_rate 20.8% |
| 批量生成 130 章节存根 | ~13,800 | link_hit_rate 升至 81% |
| 持续扩写精品页 | ~14,470 | 28 篇 featured，link_hit_rate ~79% |
| 引入五级质量体系 | ~837,000 | premium=20，featured=68，quality字段全覆盖 |

---

## 局限性

- K 不衡量**正确性**——错误内容也会贡献 K
- K 不区分**独创性**——重复信息与新增信息同等计分
- 章节存根大量存在时，link_hit_rate 虚高
- **K 是内部追踪指标**，非学术度量

---

## 相关页面

- [[Special:Settings]] — 插件开关（启用数学公式渲染）
- [[Special:Plugins]] — 已安装插件列表
- [[Special:All]] — 所有特殊页面索引
- [[Special：WantedPages]] — 被链接但尚未创建的页面
- [[Special：知识量]] — 旧链接（已重定向至本页）

---

*本页为系统特殊页面（`Special:` 前缀），不计入 K 值。*
