# Skill 修改日志
（由 W5 反思流程产生。每条一行。）


2026-04-22  proposal-1  generate_entity_page.py  stub 模板 59→20 行, 移除基本属性 (与 infobox 重复), 章节表改单行压缩, 与 W0 ≤20 行不变量对齐. [reflections/2026-04-22.md]
2026-04-22  proposal-2  discover_kg.py  加 canonical 质量过滤: LEGEND_SINGLE_CHARS / KNOWN_REDUNDANT_PATTERNS / TITLE_CANONICALS. 跳过的记 stderr, 供 KG 侧审. [reflections/2026-04-22.md]
2026-04-22  proposal-3  SKILL_W1 §三  2:1 配比 → 动态配比 (按 P1 队列规模: >10 为 3:1, 5-10 为 2:1, <5 为 1:1, 0 为纯 explore). [reflections/2026-04-22.md]
2026-04-22  proposal-4  PROMPT.md + record_revision.py  butler 改页后必须调 record_revision.py 写入 history/<slug>/<rev_id>.md + 更新 recent.json, 否则前端 #?recent 不可见. 触发点: 用户反馈 + 21 条遗漏补录. [ad-hoc reflection]
2026-04-22  proposal-5  seed.js findLikelyDuplicates  检测共享强别名的 canonical 对, 写 wiki/data/duplicate_candidates.json 供人工审. [reflections/2026-04-22-v2.md]
2026-04-22  proposal-6  tags_vocabulary.json + discover_tags.py  era (按 birth_ce 区间) + identity (按章节前缀分布) + theme (种子列表) 自动推标签. [reflections/2026-04-22-v2.md]
2026-04-22  proposal-7  SKILL_W1 §三.3  源耗尽降权 (连续 5 次空探索 weight*=0.5), 配 source_access.json 扩展字段. [reflections/2026-04-22-v2.md]
