# 纪年数据 (Chronology)

历史年表与纪年映射数据，为事件公元纪年标注提供基础。

## 数据文件

| 文件 | 条目数 | 说明 |
|------|--------|------|
| `reign_periods.json` | rulers×382 / eras×32 / aliases×48 | 君主在位年、年号分期、人名别称映射 |
| `year_ce_map.json` | 93章 / 2090条 | 按章节×段落ID的叙事年份→公元年消歧映射 |
| `year_state_map.json` | 635个公元年 | 公元年→各诸侯国当年在位君主及纪年 |
| `史记编年表.md` | — | 编年对照表（前2700年～前87年） |
| `中国历史大事年表.md` | — | 参考资料（文字版） |
| `[中国历史大事年表（古代）].沈起炜.扫描版.pdf` | — | 参考文献（扫描版） |

## 数据结构

### reign_periods.json

```json
{
  "rulers": { "秦穆公": {"state": "秦", "start_bce": 659, "end_bce": 620}, ... },
  "eras":   { "孝文后": {"ruler": "孝文", "state": "汉", "start_bce": 163, "end_bce": 157}, ... },
  "aliases": { "高祖": "高皇帝", "高帝": "高皇帝", ... }
}
```

- `rulers`：382位君主，覆盖商周至西汉
- `eras`：32个年号分期（汉代前元/中元/后元等）
- `aliases`：48条人名别称，统一指向 rulers 键

### year_ce_map.json

```json
{
  "005": {
    "6.1": { "元年": {"ruler": "秦襄公", "method": "nearby_ruler", "ce_year": -777} },
    ...
  }
}
```

- 按章节编号（001-130）→ 段落ID → 年份词 → 消歧结果
- `method`：`raw_nearby`（就近君主）/ `nearby_ruler`（精确锚定）
- `ce_year`：对应公元年（负数为公元前）

### year_state_map.json

```json
{ "-841": {"周": ["周共和", 1], "鲁": ["鲁真公", 15], ...} }
```

- 公元年（字符串）→ 各诸侯国当年在位君主及年数

## 数据来源与生成脚本

| 数据文件 | 生成脚本 | 来源 |
|----------|----------|------|
| `reign_periods.json` | `kg/events/scripts/build_year_map.py --extract-reigns` | 十表（013-022）+ 本纪章节 |
| `year_ce_map.json` | `kg/events/scripts/build_year_map.py` | 全部 tagged.md 年份实体消歧 |
| `year_state_map.json` | `kg/events/scripts/build_year_map.py` | 由 reign_periods 派生 |
