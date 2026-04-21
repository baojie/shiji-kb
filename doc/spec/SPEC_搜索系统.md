# 搜索系统规范（SPEC）

**版本**：1.0
**日期**：2026-04-22
**相关代码**：[scripts/build_search_index.py](../../scripts/build_search_index.py) · [docs/js/search.js](../../docs/js/search.js) · [docs/search.html](../../docs/search.html)
**相关技能**：[SKILL_09d 语义搜索和探索](../../skills/SKILL_09d_语义搜索和探索.md)

---

## 一、定位

docs/ 静态站的客户端全文检索。**纯前端、零服务器**：索引一次构建、浏览器懒加载、AND 子串匹配。

覆盖的入口：
- [docs/index.html](../../docs/index.html) 顶栏下拉（即时反馈，前 30 条）
- [docs/search.html](../../docs/search.html) 结果页（全量 + 分页 50/页）

---

## 二、索引构建

### 2.1 输入与输出

- 输入：`chapter_md/*.tagged.md`（130 章标注文件）
- 输出：`docs/data/search-index.json`（当前约 2.3 MB、8,283 段）
- 命令：`python scripts/build_search_index.py`

### 2.2 索引结构

```json
{
  "chapters": [{"n": 1, "f": "001_五帝本纪", "t": "五帝本纪"}, ...],
  "entries":  [{"c": 1, "p": "1",   "x": "黄帝者..."}, ...]
}
```

- `c`：章号（int），用于回查 chapters 中的 `f`（文件名 stem）/`t`（标题）。
- `p`：紫色编号 `[N]` / `[N.M]` / `[N.M.K]` 字符串，拼成段落锚 `#pn-{p}`。
- `x`：段落正文（已去除全部标注符号、已合并多行、已去除中文空格）。

段落 URL 契约：`chapters/{f}.html#pn-{p}`。

### 2.3 strip_markup 规则

参见 `scripts/build_search_index.py::strip_markup`。需严格维持与 `scripts/lint_text_integrity.py` 的标注前缀集 `_ENTITY_PFX` 一致。关键处理：

- 名词实体 `〖@X〗` / `〖@X|Y〗` → `X`（只留显示文本，不留规范名）
- 动词实体 `⟦◈X⟧` / `⟦◈X|Y⟧` → `X`
- 修辞 `〘※shiji|modern〙` → `shiji`（保留原文形式）
- 去掉 Markdown 标题、`:::` 围栏、`> ` 引用前缀、`- ` 列表前缀、`**bold**`、分隔线、表格分隔行

### 2.4 段落切分

- 以 `[N]` / `[N.M]` / `[N.M.K]` 行首编号为边界切分，多行合并为一段。
- 段内用 `re.sub(r'\s+', '', text)` 去掉空白（中文文本不靠空格分词）。

---

## 三、客户端 API

定义于 [docs/js/search.js](../../docs/js/search.js)，以 `window.ShijiSearch` 暴露。

### 3.1 懒加载

```js
window.ShijiSearchBase = ''   // 可选：子目录部署时设置根路径
ShijiSearch.loadIndex()       // 返回 Promise<data>，内部仅请求一次
ShijiSearch.getData()         // 返回 data 或 null
```

- `data.chapterMap[n]` 由客户端加载后构造（`n → chapter`），用于 O(1) 回查。

### 3.2 搜索语义

```js
ShijiSearch.searchAll(query)
// → { hits: entry[], tokens: string[] }
```

- **Tokenize**：`query.trim().split(/\s+/)`，空格分隔多个关键字。
- **匹配语义**：AND（全部 token 都必须命中）× 子串（`lowerHay.indexOf(lowerToken) !== -1`）× 大小写不敏感（`toLowerCase()`）。
- **排序**：当前按 `entries` 原始顺序（章节序 + 段落序）。**未按相关度排序**。
- **不截断**：`searchAll` 返回全部命中；截断由调用方（下拉前 30、结果页分页 50）决定。

### 3.3 片段与高亮

```js
ShijiSearch.makeSnippet(text, tokens, radius = 24)
// → string（HTML，已 escape，命中处包 <mark>）
```

- 取"最早命中的 token"为中心，左右各 `radius`/`radius*2` 字节取片段（中文按字符长度）。
- 所有 token 在片段中均会被 `<mark>` 包裹（大小写不敏感）。

### 3.4 URL 构造

```js
ShijiSearch.chapterUrl(ch, pid, basePrefix = '')
// → '{basePrefix}chapters/{f}.html#pn-{p}'

ShijiSearch.searchPageUrl(query, basePrefix = '')
// → '{basePrefix}search.html?q={q}'
```

---

## 四、UI 契约

### 4.1 首页下拉（docs/index.html）

- 容器：`#shiji-search-input` + `#shiji-search-results`。
- 防抖 120 ms，焦点时触发懒加载。
- `DROPDOWN_MAX = 30`；超过时追加"查看全部 N 个结果 →"跳转到 search.html。
- 快捷键：Enter 跳全量结果页，Esc 清空并失焦。

### 4.2 结果页（docs/search.html）

- URL 参数：`q`（查询）、`page`（页码，默认 1）。
- 分页 `PER_PAGE = 50`；翻页栏显示 `« ‹ [start..end] › »`，当前页 ±4。
- 渲染：章号 3 位补零 + 篇名 + 段落号，下一行片段高亮。
- `popstate` 支持浏览器前进后退。

---

## 五、别名模糊搜索（规划中）

**目的**：用户搜索一个词时，同时命中它的所有别名。例如搜"黄帝"也命中"轩辕"，搜"荆"也命中"楚"（春秋战国国名别名）。

### 5.1 数据基础

别名来源双源合并：
- `kg/entities/data/entity_aliases.json`：(surface, canonical) 边表。person 类 3,322 条最丰富。
- `kg/entities/data/entity_index.json`：canonical → {aliases, refs}。覆盖类型更广（含 mythical/concept/astronomy/verb-* 等 entity_aliases 未覆盖的类型），但每条 aliases 较 sparse。

**类型黑名单**：`identity`（如 `君王` 指刘邦）是上下文指代而非正式别名，**整类排除**。

**多义冲突现状**（需感知）：
- 不同 canonical 指同一人（如 `刘邦` / `汉高祖` 在 person 类下是两条独立条目，共享 `汉王` / `沛公` / `高祖` 等 surface）。通过 surface 共享在查询时**自然合并**。
- 同 surface 跨类型（如 `轩辕` → person/黄帝 + astronomy/轩辕；`楚` → feudal-state/楚 + person/子楚）。查询时会一并展开——噪声本地化到该 surface 查询，不会污染其他查询。
- 高频共享别名（`上` / `王` / `帝`）会把多个皇帝合在一起。搜索"上"展开 17 项；**但搜索"刘邦"只得 10 项**，不会被"上"反向污染。

### 5.2 别名索引 `docs/data/alias-index.json`

```json
{
  "version": 3,
  "sources": [
    "kg/entities/data/entity_aliases.json",
    "kg/entities/data/entity_index.json"
  ],
  "excluded_types": ["identity"],
  "variants": {
    "刘邦":  ["刘邦", "上", "刘季", "汉王", "汉高祖", "沛公", "邦", "高帝", "高皇帝", "高祖"],
    ...
  }
}
```

**构建算法**（见 [scripts/build_alias_index.py](../../scripts/build_alias_index.py)）：

1. 为每个 `(type, canonical)` 聚合别名集合 `alias_set[(t,c)]`：合并两份源里所有指向该 canonical 的 surface（含 canonical 本身）。
2. **数据驱动的"称谓检测"**：若 surface S 出现在多个 canonical 的别名集里、且这些 canonical 彼此之间没有其它共享 surface 可以把他们串成同一人，则 S 是 title-like，从所有别名集中**剔除**。判定步骤：
   - 取 S 的 rich owner（除 S 外还有 ≥1 个 surface 的 canonical）
   - 对 rich owner 做 per-surface 并查集，通过共享非-S surface 连通
   - 聚合每个连通分量的非-S surface 集合；"强分量"= |集合| ≥ 2
   - **≥2 个强分量 → S 是称谓** → 排除
   - 样例：`上` 在 (person, 汉高祖) 与 (person, 汉景帝) 中均出现，除"上"外毫无交集 → 剔除。`汉王` 在 (person, 刘邦) 与 (person, 汉高祖) 中均出现，还共享 刘季/沛公/高祖 等 → 保留为真别名
3. 对每个 surface S，`variants[S] = ⋃ { alias_set[(t,c)] : S ∈ alias_set[(t,c)] }`（剔除称谓后）。
4. 过滤 `|variants| < 2` 的 surface；排除 type=identity。

**不做全局并查集合并**——否则"上"、"帝"等高频共享别名会把多个皇帝合为一簇，让搜"刘邦"也命中汉武帝。直接查表使污染只发生在查询共享别名本身时。

**当前规模**（2026-04）：
- canonical 簇 16,824
- 剔除称谓 surface: ~200
- 可扩展 surface ~3,500
- 索引体积 ~700 KB

**已知数据质量限制**：
- `帝` 仍出现在"汉景帝 / 帝舜"簇里。因"帝舜"数据稀疏（只含 `{帝舜, 帝}`），无法构成强分量，检测失效。
- `韩信` 整体被剔除。因淮阴侯韩信 + 韩王信 + `person/王` 三个强分量并存，属真实数据歧义。搜索"淮阴侯"不会展开出"韩信"——用户可直接搜"韩信"（退化为精确匹配）。

### 5.3 典型查询效果

| 查询 | 精确 hits | 模糊 hits | 展开变体（去除称谓后） |
|------|---------:|---------:|---------|
| 刘邦 | 0 | ~1,100 | 刘季 / 汉王 / 汉高祖 / 沛公 / 邦 / 高帝 / 高皇帝 / 高祖 |
| 沛公 | 140 | 同上 | 同上 |
| 汉王 | 191 | 同上 | 同上 |
| 黄帝 | 84 | 90 | 轩辕 / 公孙轩辕 / 帝鸿氏 / 有熊氏 等 |
| 秦始皇 | — | — | 嬴政 / 政 / 秦王政 / 始皇 / 始皇帝 / 赵政 等 |
| 楚 | — | — | 荆 / 子楚 |

### 5.4 客户端扩展

```js
ShijiSearch.loadAliasIndex()        // 仅在 fuzzy=true 时懒加载
ShijiSearch.searchAll(q, { fuzzy: true })
// → { hits, tokens, expandedTokens: { [token]: string[] } }
```

- 语义：每个 token 展开为变体集合，**OR 于组内 / AND 于组间**。
- 原始 token 不在 variants 表时，退化为自身。
- `makeSnippet` 用展开后的所有变体做高亮。

### 5.5 UI 契约

- search.html 增加复选框「包含别名」。
- URL 参数 `fuzzy=1` 持久化；浏览器前进后退保留。
- 概要行新增："已展开：黄帝 = {黄帝, 轩辕}"（透明展示消除用户困惑）。
- 首页下拉暂不加选项（保持轻量）。

### 5.6 已知取舍

| 取舍点 | 选择 | 理由 |
|-------|------|------|
| `identity` 类型（"君王"/"大王"/"中宗"） | 整类排除 | 上下文指代，非正式别名 |
| 多 canonical 同指一人（刘邦 / 汉高祖） | 通过 surface 共享自然合并 | 不做全局并查集，避免高频别名污染 |
| 称谓 surface（"上"/"王"/"帝"/"主"） | 数据驱动检测，强分量 ≥2 时整体剔除 | 保证搜"刘邦"不展开到"上"或"王" |
| 真实歧义名（"韩信" 指两个人） | 同上机制下也被剔除 | 搜"韩信"退化为精确匹配；属数据本身限制 |
| 跨类型歧义（`楚`：国 / 人`子楚`） | 照展开，透明展示 | 类型过滤属分面搜索，不在本 phase |
| 拼音/错别字容错 | 不做 | 另起炉灶（见 SKILL_09d 未来阶段） |
| 相关度排序 | 不做 | 全文 AND 场景下顺序≈章节序，符合阅读习惯 |

---

## 六、非目标

以下场景**不由本系统负责**，设计时不为其让步：

- **语义搜索**（向量/自然语言描述 → 实体） — 参见 SKILL_09d
- **分面过滤**（按类型/时代/籍贯组合） — 参见 SKILL_09d
- **图浏览**（人物关系图、时间轴、地图） — 参见 SKILL_09d
- **原文之外的字段检索**（标注符号本身、白话译文、注释） — 若将来支持，需在 `strip_markup` 之外另建索引

---

## 七、维护

- **索引重建**：两份索引（全文 + 别名）已挂到 [publish_to_docs.sh](../../publish_to_docs.sh) 第 7 步，发布时自动刷新。手动重建：`python scripts/build_search_index.py && python scripts/build_alias_index.py`。
- **strip_markup 同步**：若新增标注符号前缀，须同步更新 `_ENTITY_PFX` 并在此 SPEC 的 §2.3 追加一行。
- **别名索引失配**：`entity_index.json` 变化后必须重跑 `scripts/build_alias_index.py`（发布脚本会自动处理，脱离发布流程单独改 KG 时需手动）。
- **验证方法**：索引生成后 `jq '.entries | length'` 核对段数；抽查含冷僻字 / 消歧别名的段落是否可被搜到。
