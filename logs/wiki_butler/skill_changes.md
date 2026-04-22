# Skill 修改日志
（W5 反思流程 + 用户紧急反馈 共同产出。每条一行。）

格式: `YYYY-MM-DD  [w5-vN-n | user-req-N]  <文件/skill>  <摘要>  [source]`
- `w5-vN-n`: 第 N 次 W5 反思的第 n 条提案 (e.g., w5-v3-8)
- `user-req-N`: 用户紧急反馈的第 N 项


2026-04-22  proposal-1  generate_entity_page.py  stub 模板 59→20 行, 移除基本属性 (与 infobox 重复), 章节表改单行压缩, 与 W0 ≤20 行不变量对齐. [reflections/2026-04-22.md]
2026-04-22  proposal-2  discover_kg.py  加 canonical 质量过滤: LEGEND_SINGLE_CHARS / KNOWN_REDUNDANT_PATTERNS / TITLE_CANONICALS. 跳过的记 stderr, 供 KG 侧审. [reflections/2026-04-22.md]
2026-04-22  proposal-3  SKILL_W1 §三  2:1 配比 → 动态配比 (按 P1 队列规模: >10 为 3:1, 5-10 为 2:1, <5 为 1:1, 0 为纯 explore). [reflections/2026-04-22.md]
2026-04-22  proposal-4  PROMPT.md + record_revision.py  butler 改页后必须调 record_revision.py 写入 history/<slug>/<rev_id>.md + 更新 recent.json, 否则前端 #?recent 不可见. 触发点: 用户反馈 + 21 条遗漏补录. [ad-hoc reflection]
2026-04-22  proposal-5  seed.js findLikelyDuplicates  检测共享强别名的 canonical 对, 写 wiki/data/duplicate_candidates.json 供人工审. [reflections/2026-04-22-v2.md]
2026-04-22  proposal-6  tags_vocabulary.json + discover_tags.py  era (按 birth_ce 区间) + identity (按章节前缀分布) + theme (种子列表) 自动推标签. [reflections/2026-04-22-v2.md]
2026-04-22  proposal-7  SKILL_W1 §三.3  源耗尽降权 (连续 5 次空探索 weight*=0.5), 配 source_access.json 扩展字段. [reflections/2026-04-22-v2.md]
2026-04-22  user-req-1  record_revision.py + renderRecent  recent.json 不再 limit 50 截断, UI 每页 50 条分页.
2026-04-22  user-req-2  build_registry.py + renderHome  加 quality_score (多因子), featured 改按质量降序.
2026-04-22  user-req-3  renderAll + router #?all + homeHome  全部页面单独 /all 页, 按 type 分组组内按质量降序.
2026-04-22  w5-v3-8     build_registry.py  narrative_bonus: `<!-- stub:` -5, 散文段落 ≥2 +8. stub 和有内容页明确区分. [reflections/2026-04-22-v3.md]
2026-04-22  w5-v3-10    discover_tags.py   era_tag 改优先 death_ce, 修刘邦'战国'误推. [reflections/2026-04-22-v3.md]
2026-04-22  w5-v4-11    record_revision.py  recent.json 上限 500, 超出写 recent-archive/YYYY-MM.json. [reflections/2026-04-22-v4.md]
2026-04-22  w5-v4-12    build_registry.py   alias_conflicts.json 输出冲突详情. [reflections/2026-04-22-v4.md]
2026-04-22  w5-v4-13    discover_doc.py     新脚本扫 doc/lifespan_inference 输出 P2 cite-doc-report 候选. [reflections/2026-04-22-v4.md]
2026-04-22  user-req-4  SKILL_W1 §3.4 + build_registry.py  median quality < 10 时优先深度 (enrich > create-stub); cite-doc 加 +3 narrative_bonus. 响应用户反馈"基本都是空骨架". [ad-hoc]
2026-04-22  w5-v5-15    clean-stub 条件扩展  tags≥3 OR cite OR timeline → 清 stub 标记. [reflections/2026-04-22-v5.md]
2026-04-22  w5-v5-16    link-external-docs  批量给 151 页加 docs/entities/person.html 索引链 (topic 页 rollback). [reflections/2026-04-22-v5.md]
2026-04-22  user-req-5  enrich_timeline.py  strip_annotations: 清 〖TYPE value〗/⟦TYPE verb⟧ 保 value, clean_field 去括号噪音, 146 页 timeline 全量重写. [ad-hoc · user feedback]
2026-04-22  user-req-6  history 存储升级  1159 小文件 → 166 (content inlined 到 per-page JSON). record_revision.py 不再写 rev .md. renderer.js renderRevision 从 JSON content 字段取. 文件数 -86%, 体积 -72%. [ad-hoc · user feedback]
2026-04-22  user-req-7  record_revision.py + renderer.js  归档 index.json + renderRecent 穿透归档, 所有历史都能翻页看到. [ad-hoc · user feedback]
2026-04-22  user-req-8  renderer.js + router.js + css  新 #?diff=<page>&rev=<id> 视图, LCS 行级 diff 展示. renderHistory/Revision 加 diff 入口. [ad-hoc · user feedback]
2026-04-22  w5-v6-17    reflection_scan.py  新工具自动扫 alias_conflicts / duplicate_candidates / no-timeline / quality-bottom, W5 反思引用. [reflections/2026-04-22-v6.md]
2026-04-22  w5-v6       CANONICAL_MERGE 扩  汉孝景帝/汉孝文帝/汉孝武帝/项籍/秦二世 纳入合并. 3 个重复 canonical 消失. [reflections/2026-04-22-v6.md]
2026-04-22  bug-fix-v7  enrich_timeline.py  抽取用 〖@〗 严格正则, 单字别名禁用于匹配. 195 页 timeline 全量重写消除误伤. [reflections/2026-04-22-v7-bug.md · user 报告 鲁桓公]
