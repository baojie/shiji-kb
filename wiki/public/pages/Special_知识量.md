---
id: "Special:知识量"
type: special
label: 知识量 (K)
canonical_name: "Special:知识量"
tags: [系统页面, 知识量, 度量]
---

# Special:知识量

本页解释《史记》知识库的**知识量（K）** 度量——一个衡量知识库信息密度与覆盖深度的综合指标。

---

## 定义

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

### 质量分 q

质量分由 [`build_registry.py`](../../scripts/build_registry.py) 自动计算，综合：

- 页面字节数（篇幅）
- wikilink 数（内部链接密度）
- frontmatter 完整性（birth_ce / death_ce / tags 等字段）
- 是否有生平叙述段落

质量分归一化为 $Q \in [1.0, 3.0]$，防止单一高质量页影响过大。

---

## 设计目标

**K 度量的目标**：

1. **反映知识深度**，而非单纯字数——通过链接密度奖励内联结构
2. **防止刷字数**——`log₂` 压缩使得无限扩张收益递减
3. **区分内容质量**——通过 $Q$ 乘子激励高质量页面
4. **章节存根不淹没实体页**——章节权重 0.4 是刻意压缩

---

## 当前快照

> 数据由 [`compute_knowledge.py`](../../scripts/compute_knowledge.py) 实时计算，
> 最新值见首页 K 面板或 [`data/knowledge_latest.json`](../data/knowledge_latest.json)。

---

## 历史演进

| 里程碑 | K 值 | 说明 |
|--------|------|------|
| 初始建立 | ~13,000 | 约 230 页，link_hit_rate 20.8% |
| 批量生成 130 章节存根 | ~13,800 | link_hit_rate 升至 81% |
| 持续扩写精品页 | ~14,470 | 28 篇 featured，link_hit_rate ~79% |

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

---

*本页为系统特殊页面（`Special:` 前缀），不计入 K 值。*
