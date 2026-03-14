# 纪年数据 (Chronology)

历史年表与纪年映射数据，为事件公元纪年标注提供基础。

## 数据文件

| 文件 | 说明 |
|------|------|
| `reign_periods.json` | 君主在位年（年表解析，ruler→state/start_bce/end_bce） |
| `year_ce_map.json` | 按章节的叙事年份→公元年映射 |
| `史记编年表.md` | 编年对照表（前2700年～前87年） |
| `[中国历史大事年表].pdf` | 参考文献 |

## 数据来源

- `reign_periods.json`：从十表章节（013-022）和本纪解析
- `year_ce_map.json`：由 `kg/events/scripts/build_year_map.py` 生成

纯数据模块，无独立脚本。
