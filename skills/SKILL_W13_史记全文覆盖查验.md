---
name: skill-w13
title: 史记全文 Wiki 覆盖查验（句子级）
description: 为《史记》每一个句子（含表格单元格）建立唯一编号，构建"句子→wiki页面"双向映射表，系统性发现未覆盖的原文知识缺口，驱动 W10 任务队列补全。
---

# SKILL W13: 史记全文 Wiki 覆盖查验（句子级）

> 《史记》约 **30 万字**，切分为约 **8–10 万个句子单元**。每个单元都应当映射到至少一个 wiki 页面——否则这段知识在知识库中"不存在"。

---

## 一、句子单元定义与编号

### 1.1 句子 ID 格式

```
{chapter_id}.{para_id}.s{n}
```

示例：
- `001_五帝本纪.1.s2` = 第001章，段落1，第2句
- `001_五帝本纪.r15.c3` = 第001章，表格行15，第3列单元格
- `070_张仪列传.39.s1` = 第070章，段落39，第1句

**约定**：
- `chapter_id` = tagged.md 的文件名去掉 `.tagged.md` 后缀（如 `001_五帝本纪`）
- `para_id` = 现有 `[N]`/`[N.M]`/`[rN]` 体系中的段落编号（不改原文件）
- `s{n}` 从 1 开始递增，按句子在段落内出现顺序
- 表格行用 `.c{col}` 替代 `.s{n}`，col 从 1 开始

### 1.2 分句规则

**普通段落**（文字段落）：
1. 以 `。` `！` `？` 为主句界（保留句号在句尾）
2. `；` 且后面≥10字时，视为独立句
3. 引号内的 `。` 不切分（`"…。"` 整体为一句的一部分，直到外层结束符）
4. 切分后 < 3 字的碎片合并到前一句
5. 最终每个"句"包含完整语义单位（如对话`曰："…。"`算一句）

**表格行**（`[rN]`）：
- 每个非空单元格（`|` 分隔）为一个 `c{col}` 单元
- 空白/纯数字/`---` 单元格豁免（不计入覆盖目标）

**示例**：
```
段落原文: 黄帝者，少典之子，姓公孙，名曰轩辕。生而神灵，弱而能言，幼而徇齐，长而敦敏，成而聪明。
→ s1: 黄帝者，少典之子，姓公孙，名曰轩辕。
→ s2: 生而神灵，弱而能言，幼而徇齐，长而敦敏，成而聪明。
```

---

## 二、数据文件布局

```
wiki/logs/butler/
├── sentence_index/
│   ├── 001_五帝本纪.jsonl    每行一个句子单元（静态，由原文生成，不随 wiki 变化）
│   ├── 002_夏本纪.jsonl
│   └── …（130 个文件）
├── coverage_map/
│   ├── 001_五帝本纪.jsonl    每行一个句子的覆盖状态（动态，随 wiki 更新）
│   ├── 002_夏本纪.jsonl
│   └── …
└── coverage_summary.json     汇总统计（总覆盖率、分章覆盖率、里程碑状态）
```

### sentence_index JSONL 格式（每行）

```json
{"sid": "001_五帝本纪.1.s1", "chapter": "001_五帝本纪", "para": "1", "seq": 1,
 "text": "黄帝者，少典之子，姓公孙，名曰轩辕。", "len": 16}
```

### coverage_map JSONL 格式（每行）

```json
{"sid": "001_五帝本纪.1.s1",
 "pages": ["黄帝", "公孙轩辕"],
 "cover_type": "quote",
 "status": "covered",
 "updated": "2026-04-25"}
```

**cover_type 枚举**：
| 值 | 含义 |
|---|---|
| `quote` | wiki 页面 `## 史记引文` 节包含该句文本（≥10字子串命中） |
| `para` | wiki 页面 `pn` 字段引用了该句所在段落（段落级覆盖） |
| `entity` | 该句包含已有 wiki 页面的实体名，且实体页链接到本章 |
| `gap` | 以上均无 |
| `exempt` | 豁免（空白/数字单元格/六国年表年份列） |

**status**：`covered`（cover_type ≠ gap/exempt）/ `gap` / `exempt`

---

## 三、覆盖判定算法（优先级从高到低）

```
for each sentence S in chapter C, paragraph P:

  1. [quote]  扫描所有 wiki 页面的 ## 史记引文 节及正文引号段落：
              若 S.text 的任意连续 10 字在页面文本中出现 → cover_type=quote

  2. [para]   若 wiki 页面 frontmatter pn 字段含 "CCC-P"（章节+段落ID）
              或正文含 "(CCC-P)" 或 "§P" 后跟章节链 → cover_type=para

  3. [entity] 若 S.text 含实体 E（来自 entity_index.json），
              且 E 有 wiki 页面，且该页面 wikilink 了本章 → cover_type=entity

  4. [gap]    以上全无 → gap，需补全
```

> **精度说明**：quote > para > entity > gap。`entity` 覆盖属于弱覆盖，只代表"有相关页面存在"，不代表该句知识已被充分wiki化。W10 任务队列应优先处理 `gap`，再关注 `entity`-only 的句子。

---

## 四、脚本体系

### 4.1 `build_sentence_index.py`（一次性，原文静态）

```bash
# 从 chapter_md/*.tagged.md 生成 sentence_index/
python3 wiki/scripts/butler/build_sentence_index.py \
    --chapter-dir chapter_md \
    --out wiki/logs/butler/sentence_index

# 单章调试
python3 wiki/scripts/butler/build_sentence_index.py --chapter 001_五帝本纪
```

输出：`sentence_index/001_五帝本纪.jsonl`（约 200-500 行/章）

**核心逻辑**：

```python
def split_sentences(text: str) -> list[str]:
    """古文分句：以 。！？ 为主界，引号内不切，短碎片合并。"""
    result = []
    buf = ""
    in_quote = False
    for ch in text:
        buf += ch
        if ch in ('"', '「', '『'):
            in_quote = True
        elif ch in ('"', '」', '』'):
            in_quote = False
        if not in_quote and ch in ('。', '！', '？'):
            if len(buf.strip()) >= 3:
                result.append(buf.strip())
            buf = ""
    if buf.strip():
        result.append(buf.strip())
    return result
```

### 4.2 `build_coverage_map.py`（全量 + 增量）

```bash
# 全量构建（约 10-20 分钟）
python3 wiki/scripts/butler/build_coverage_map.py --full

# 增量（只重算被修改过的 wiki 页面涉及的章节）
python3 wiki/scripts/butler/build_coverage_map.py --incremental

# 生成缺口报告
python3 wiki/scripts/butler/build_coverage_map.py --report > /tmp/coverage_report.md

# 写入 housekeeping_queue（高分缺口段）
python3 wiki/scripts/butler/build_coverage_map.py --write-queue --max-new 20
```

### 4.3 `coverage_report.py`（统计与查询）

```bash
# 全局覆盖率概览
python3 wiki/scripts/butler/coverage_report.py --summary

# 某章覆盖详情
python3 wiki/scripts/butler/coverage_report.py --chapter 070_张仪列传

# 按段落输出所有 gap 句子（排优先级）
python3 wiki/scripts/butler/coverage_report.py --gaps --top 50
```

---

## 五、缺口优先级

```
gap_score = chapter_weight × para_type_weight × text_density × entity_density
```

| 因子 | 规则 |
|---|---|
| `chapter_weight` | 本纪 1.0，世家 0.9，列传 0.8，书 0.6，表 0.3 |
| `para_type_weight` | 普通段落 1.0，表格单元 0.4 |
| `text_density` | min(len / 20, 1.0) |
| `entity_density` | 句中实体数 / 3（上限 1.0）|

- `gap_score ≥ 0.6` → P1（本周处理）
- `gap_score 0.3–0.6` → P2（积压队列）
- `gap_score < 0.3` → P3（暂豁免）

**housekeeping_queue 条目格式**：

```markdown
- [ ] H13 句子缺口: `070_张仪列传.39.s3`
      文本: 「今秦楚嫁女娶妇，为昆弟之国…」（39字）
      → 建议动作: enrich-infobox 张仪 / embed-sku-excerpt
      → 发现于: W13 增量扫描 2026-04-25, gap_score=0.81
```

---

## 六、覆盖率里程碑

| 里程碑 | 句子覆盖率 | 侧重 |
|---|---|---|
| M1 | 20% | 本纪全覆盖（quote/para 级） |
| M2 | 40% | 世家人物主段落覆盖 |
| M3 | 60% | 列传核心叙事段落 |
| M4 | 75% | entity 级覆盖大幅提升（实体页补 pn） |
| M5 | 90%+ | 书/表非数字单元覆盖 |

**豁免不计入目标**：
- 六国年表中纯年份/数字格（< 5 字无实体）
- 太史公曰等评语段已另有专题页时可标 `exempt-covered`

---

## 七、与其他 Skill 的关系

| Skill | 交互方式 |
|---|---|
| **W1** | 高分缺口段直接作为 W1 候选，优先选 entity_density 高的缺口 |
| **W2** | 修复动作：`source-with-pn`（补段落引用）、`embed-sku-excerpt`（补引文）、`create-stub` |
| **W7** | W7 核验已有引注是否正确；W13 发现哪里还没有引注 |
| **W8** | M3 阶段对覆盖率 < 30% 的列传主角，触发精品页建设 |
| **W10** | 缺口以 H13 写入 housekeeping_queue.md；W13 是 W10 的内容供给方 |

---

## 八、实施路线图

```
阶段 0（当前）：设计阶段，build_sentence_index.py 待实现
阶段 1：实现 build_sentence_index.py，生成 sentence_index/（静态）
阶段 2：实现 build_coverage_map.py，支持 quote/para 两种覆盖信号
阶段 3：加入 entity 覆盖信号，连接 entity_index.json
阶段 4：实现 --incremental，集成到每 10 轮 W10 触发
阶段 5：coverage_report.py + 里程碑仪表盘（wiki 页面展示）
```

**阶段 1 启动检查**：
```bash
ls wiki/scripts/butler/build_sentence_index.py 2>/dev/null || \
  echo "⚠ 尚未实现，W13 处于设计阶段（见 TODO.md）"

# 临时统计：用现有 pn 字段粗估段落级覆盖
python3 -c "
import json, glob, re, yaml
pn_re = re.compile(r'(\d{3})-([^\s\)]+)')
covered = set()
for f in glob.glob('wiki/public/pages/*.md'):
    txt = open(f).read()
    for m in pn_re.finditer(txt):
        covered.add((m.group(1), m.group(2)))
print(f'段落级 pn 引用: {len(covered)} 条（句子级覆盖估算需 build_sentence_index）')
"
```

---

## 相关路径

- `wiki/logs/butler/sentence_index/` — 静态句子索引（原文分句，一次生成）
- `wiki/logs/butler/coverage_map/` — 动态覆盖映射（随 wiki 更新）
- `wiki/logs/butler/coverage_summary.json` — 汇总统计
- `wiki/scripts/butler/build_sentence_index.py` — 分句索引构建（**待实现**）
- `wiki/scripts/butler/build_coverage_map.py` — 覆盖映射构建（**待实现**）
- `wiki/scripts/butler/coverage_report.py` — 报告与查询（**待实现**）
- `wiki/logs/butler/housekeeping_queue.md` — H13 条目写入处
- `skills/SKILL_W10_Butler内务整理.md` — H13 在内务体系中的位置
