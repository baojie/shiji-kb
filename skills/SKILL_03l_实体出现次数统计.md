---
name: skill-03l
description: 按规范实体 (canonical) 统计其在 130 篇《史记》中的出现次数与章节分布。三层聚合策略: canonical 合并表 + 每 surface 单一来源 + (ch,paragraph) 去重。当需要给 wiki / 统计页 / API 提供"某人物出现多少次"这类数字时使用。避免 entity_index 与 entity_aliases 粒度混用造成的虚胖 (如"袁盎 118 次""韩王信 135 次"这类早先 bug)。
---

# SKILL 03l: 实体出现次数统计 — 三层聚合策略

> 从 wiki/server/api/seed.js 的数据修复中提炼。主要针对**人名**，但 place/state/official 等同类实体均适用。

---

## 一、问题

"某个实体在史记中出现多少次" 看似简单, 实际有三个陷阱:

**陷阱 1: 多 canonical 并存**
`entity_aliases.json` 同一人常有多个 canonical (历史遗留 + 多人校对):
- `刘邦` 与 `汉高祖`
- `项羽` 与 `西楚霸王`
- `秦始皇` 与 `秦始皇帝`
- `汉文帝` 与 `刘恒` 与 `孝文帝`

直接按 canonical 分桶统计, 一个人被拆成两三份, 数字偏低.

**陷阱 2: 两份数据粒度不一致**
- `kg/entities/data/entity_aliases.json` 的 refs 是 **段落级**: `["101_袁盎晁错列传", "13"]`
- `kg/entities/data/entity_index.json` 的 refs 是 **子句级**: `["101_袁盎晁错列传", "13.3"]`

若两份同时取并去重, 段落 `13` 与子句 `13.1 / 13.3 / 13.5` 被视为 4 条不同 ref → 同一段被计 4 次. 袁盎从真实 81 次虚高到 118 次就是此 bug.

**陷阱 3: 数据源快照不同步**
项目有两个同名文件:
- `kg/entity_index.json` (根目录, 旧快照)
- `kg/entities/data/entity_index.json` (标准, 随 tagged.md 更新)

若 seed 读了旧的, 部分 PN 会指向已改段落号的空位, 有些段落本不含此人名却被计入.

---

## 二、三层策略

### L1: canonical 合并表

统一不同 canonical 写法到单一规范名. 放在代码里, 按需扩展:

```js
const CANONICAL_MERGE = {
  '汉高祖': '刘邦',      '高祖': '刘邦',
  '西楚霸王': '项羽',
  '秦始皇帝': '秦始皇',
  '刘恒': '汉文帝',      '孝文帝': '汉文帝',
  '刘启': '汉景帝',      '孝景帝': '汉景帝',
  '卫鞅': '商鞅',
  '黥布': '英布',
  '范睢': '范雎',
  '秦昭王': '秦昭襄王',
};
function canonicalize(name) {
  return CANONICAL_MERGE[name] || name;
}
```

**为什么不写到 JSON**: 目前 ~12 条, 代码里肉眼可审更安全. 大于 100 条时迁出.

### L2: 每个 surface 只取一个来源

对 canonical C 的每个 surface S, 选**一条**数据源:

| S 情况 | 判定 | 取 refs 来源 |
| --- | --- | --- |
| aliases 表里只指向 C (合并后) | 无歧义 | `entity_index[S].refs` (子句级, 最准) |
| aliases 表无 S 的行, 且 S == C | 无歧义 (标准写法) | `entity_index[S].refs` |
| aliases 表里指向多个 canonical | 歧义 | 只取 aliases 里 `(surface=S, canonical-after-merge=C)` 那几行的 refs |

**关键**: 永远不要同一 surface 两边都取. 粒度不同 → 去重不过 → 双重计数.

### L3: (chapter, paragraph-id) 去重

所有来源的 refs 合并后, 按 `(chapter, paragraph)` 键去重:

```js
function dedupeRefs(refs) {
  const seen = new Set();
  return refs.filter((r) => {
    const k = r[0] + '|' + r[1];
    if (seen.has(k)) return false;
    seen.add(k); return true;
  });
}
```

需要 mention 级计数 (如"某段出现 3 次") 时, 用 `13.1 / 13.3 / 13.5` 形式的子句 id, 自然会被区分.

---

## 三、数据源

| 文件 | 用途 | 粒度 | 更新触发 |
| --- | --- | --- | --- |
| `chapter_md/*.tagged.md` | 原文 + 标注 (单一事实源) | 子句 | 手工 / 反思 |
| `kg/entities/data/entity_aliases.json` | surface↔canonical + 消歧 refs | 段落 | `extract_aliases*.py` |
| `kg/entities/data/entity_index.json` | surface → 全部 refs (未消歧) | 子句 | `build_entity_index.py` |
| ~~`kg/entity_index.json`~~ | **旧快照, 勿用** | — | — |

**两个 `entity_index.json` 陷阱**: 根目录的是旧版 (前次运行留下的). 正确路径是 `kg/entities/data/entity_index.json`. 如发现 PN 对不上章节, 先核对这一步.

---

## 四、脚本与落点

**主脚本**: [`wiki/server/api/seed.js`](../wiki/server/api/seed.js)
- 读 aliases + entity_index + lifespans
- 应用 L1/L2/L3
- 产出 `wiki/data/semantic.json`: `{ entities: {canonical: {id, aliases, lifespan, total_refs, total_chapters, chapters[]}}, stats, generated }`

**生成 wiki 页面**: [`wiki/scripts/generate_entity_page.py`](../wiki/scripts/generate_entity_page.py)
- 从 semantic.json 按规范名生成 `.md` 页, 带章节分布表

**API**: `GET /api/query?kind=entity_facts&id=<canonical>` — 返回单个实体记录

---

## 五、验证

每次 seed 完成后, 抽查 3-5 个知名实体:

```bash
python3 -c "
import json, re
d = json.load(open('wiki/data/semantic.json'))
for name in ['刘邦', '项羽', '孔子', '司马迁']:
    e = d['entities'][name]
    print(f'{name}: refs={e[\"total_refs\"]} 章={e[\"total_chapters\"]}')
    print(f'  top 3: {e[\"chapters\"][:3]}')
"
```

**抽查 PN 是否真的在段落里** (关键反常检查):

```python
# 抽 10 个 ref, 回原文 chapter_md/<ch>.tagged.md 验证段落含此人
idx = json.load(open('kg/entities/data/entity_index.json'))
refs = idx['person']['袁盎']['refs'][:10]
text = open('chapter_md/101_袁盎晁错列传.tagged.md').read()
for ch, para in refs:
    pat = re.compile(r'\[' + re.escape(para) + r'\]([^\n]+)')
    m = pat.search(text)
    assert '袁盎' in m.group(1) or '盎' in m.group(1), \
        f'{ch}#{para} 段落不含袁盎: {m.group(1)[:50]}'
```

若发现不匹配, **立即**检查 entity_index 是否过期 (cp 日期 vs tagged.md).

---

## 六、已知限界 (v0)

1. **歧义 surface 下的 mention 级计数缺失**
   歧义 surface 只能用 aliases 段落级 refs. 若某段有 3 次"信"都指韩信, 算 1 次. 要精确需要回标 tagged.md 的子句 id — v0 不做.

2. **CANONICAL_MERGE 手工维护**
   新增合并须改代码重跑 seed. 可以用 lifespan 作合并线索 (同生卒年), 但伪阳性多 (如蒙恬/秦始皇同生卒), 不自动化.

3. **不含 "太史公曰" 的隐性指称**
   司马迁出现 159 次 / 129 章 里, "太史公"这一身份称谓的绝大多数都是他本人, 目前已合并. 但"吾"、"余"之类第一人称不计.

4. **外部引用过滤**
   某些 ref 带 `baojie_md` / `rulers.json` 之类非章节源, `filterChapterRefs()` 用 `/^\d{3}_/` 正则过滤掉, 只保留 `001_五帝本纪` ~ `130_太史公自序`.

---

## 七、扩展

**其他实体类型**: place / state / official 聚合逻辑完全相同 (同一 seed.js 可复用), 只需把 `aliases.person` 换成 `aliases.place` 等, 并给对应类型写 CANONICAL_MERGE.

**其他统计维度**:
- 共现 (co-occurrence): 在 dedup 后 refs 基础上, 按 (ch, paragraph) groupby, 得同段人物对.
- 事件关联: join `kg/events/data/*_事件索引.md` 的主要人物列.
- 章节身份 (主角/配角): 按 refs 占该章总 refs 比例划分.

---

## 八、反常清单 (调试时先查这几条)

1. 某人数字突然很高 → 检查 canonical 是否被拆 (L1 漏项), 或 surface 歧义未妥善处理 (L2 取错源)
2. 某人数字 0 → canonical 写错 (如 `刘恒` 没合并到 `汉文帝`), semantic.json 里不存在该 canonical
3. PN 乱 → `entity_index.json` 用错路径 (根目录 vs entities/data)
4. 同人页章节列表显示两个近似章 → 是 surface 合并产生的. 正常.
5. 某章重复 x2 → dedup 漏了 (检查 refs 元素是否都是 [str, str])

---

## 九、相关 SKILL

- [SKILL_03a_实体标注](SKILL_03a_实体标注.md) — tagged.md 里如何打标注
- [SKILL_03b_人名消歧](SKILL_03b_人名消歧.md) — aliases 表的结构与消歧语法
- [SKILL_03c_按章反思](SKILL_03c_按章反思.md) — 反思流程, PN 修订通常发生在这里
- [SKILL_03d_渲染与发布](SKILL_03d_渲染与发布.md) — docs/entities/*.html 的生成
