# 历史事件 (Events)

从130篇标注文件中提取的3,185个历史事件，含公元纪年标注和跨章事件关系。

## 数据文件

| 文件 | 说明 |
|------|------|
| `data/{NNN}_{章名}_事件索引.md` | 各章事件（概览表+详情记录） |
| `data/event_relations.json` | 事件关系（7,637条，9种类型） |
| `data/event_relations_summary.md` | 关系统计摘要 |
| `events_summary.json` | 事件汇总统计 |
| `事件时间索引.md` | 按时间排列的全局索引 |

## 事件关系

| 类型 | 来源 | 说明 |
|------|------|------|
| concurrent | 自动 | 同年+共同人物 |
| co_person | 自动 | 跨章共享≥2人物 |
| co_location | 自动 | 共享地点+人物 |
| cross_ref | 自动 | 不同章节记述同一事件 |
| sequel | LLM | 时间延续 |
| causal | LLM | 因果关系 |
| cross_causal | LLM | 跨章因果 |
| part_of | LLM | 包含关系 |
| opposition | LLM | 对立关系 |

## 年代标记格式

- `（公元前XXX年）` — 精确年份
- `[公元前XXX年]` — 推算年份
- `[约公元前XXX年]` — 近似年份

## 脚本

| 脚本 | 功能 |
|------|------|
| `extract_event_relations.py` | 事件关系推理（`--auto-only` / `--llm-only`） |
| `run_review_pipeline.py` | 年代反思审查管线（`--prompt`/`--ingest`/`--report`） |
| `annotate_ce_years.py` | 公元纪年标注 |
| `lint_ce_years.py` | 纪年质检 |
| `build_metro_map_data.py` | 地铁图可视化数据 |

## 常用操作

```bash
python kg/events/scripts/extract_event_relations.py --auto-only  # 重建自动关系
python kg/events/scripts/lint_ce_years.py                        # 纪年质检
python kg/events/scripts/lint_ce_years.py 047                    # 指定章节
```
