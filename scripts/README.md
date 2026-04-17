# Scripts 目录说明

本目录包含 **133** 个Python脚本，涵盖文本处理、质量检查、数据分析等功能。

- **63** 个被SKILL文档引用（活跃使用中）
- **70** 个未被引用（实验性或待整合）

## 目录

- [质量检查工具 (lint)](#质量检查工具-lint)
- [修复工具 (fix)](#修复工具-fix)
- [生成工具 (generate)](#生成工具-generate)
- [提取工具 (extract)](#提取工具-extract)
- [分析工具 (analyze)](#分析工具-analyze)
- [验证工具 (validate)](#验证工具-validate)
- [迁移工具 (migrate)](#迁移工具-migrate)
- [渲染工具 (render)](#渲染工具-render)
- [转换工具 (convert)](#转换工具-convert)
- [更新工具 (update)](#更新工具-update)
- [章节处理 (section)](#章节处理-section)
- [格式化工具 (fmt)](#格式化工具-fmt)
- [标注工具 (tag)](#标注工具-tag)
- [构建工具 (build)](#构建工具-build)
- [测试工具 (test)](#测试工具-test)
- [其他工具](#其他工具)
- [使用指南](#使用指南)
- [历史脚本](#历史脚本)
- [规划中的脚本（待实现）](#规划中的脚本待实现)

---

## 质量检查工具 (lint)

检查和验证脚本，确保数据质量。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `lint_heading_numbers.py` | 1次 | SKILL_02a_章节切分与编号.md | 终端输出/错误列表 |
| `lint_html.py` | 2次 | SKILL_03d_渲染与发布.md<br>SKILL_09a_语法高亮辅助阅读.md | 终端输出/错误列表 |
| **`lint_markdown.py`** | **6次** | 00-META-08_标注体系设计.md<br>00-META-10_质量控制.md<br>SKILL_03c_按章反思.md<br>SKILL_03d_渲染与发布.md<br>SKILL_03e_按类型反思.md<br>SKILL_03f_实体边界错误综合反思.md | 终端输出/错误列表 |
| `lint_purple_numbers.py` | 2次 | SKILL_02a_章节切分与编号.md<br>references/SKILL_02a1_Purple_Numbers编号详细规范.md | 终端输出/错误列表 |
| `lint_section_position.py` | 1次 | SKILL_02a_章节切分与编号.md | 终端输出/错误列表 |
| `lint_skills.py` | 1次 | archive/SKILL_10f_Skill的提炼与转化_20260402.md | 终端输出/错误列表 |
| `lint_symbol_conflicts.py` | 2次 | SKILL_01f_句读和标点校勘.md<br>SKILL_01g_标注符号集合原则.md | 终端输出/错误列表 |
| **`lint_text_integrity.py`** | **15次** | 00-META-10_质量控制.md<br>SKILL_01_古籍校勘.md<br>SKILL_01a_标注完整性维护.md<br>SKILL_01b_多版本互校底本.md<br>SKILL_01c_表格校勘规范.md<br>SKILL_01d_正音与拼音标注.md<br>SKILL_01g_标注符号集合原则.md<br>SKILL_03a_实体标注.md<br>SKILL_03c_按章反思.md<br>SKILL_04f_动词标注.md<br>SKILL_10_项目管理.md<br>SKILL_10a_TODO和Issue管理.md<br>draft/META-SKILL-批量反思管线.md<br>references/SKILL_03c1-rules.md<br>references/SKILL_10c1_禁止命令清单.md | 终端输出/错误列表 |

---

## 修复工具 (fix)

自动修复各类问题。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `fix_all_halfwidth_symbols.py` | 1次 | SKILL_01f_句读和标点校勘.md | chapter_md/*.tagged.md |
| `fix_entity_boundary_errors.py` | 1次 | SKILL_03f_实体边界错误综合反思.md | data/**/*.md |
| `fix_halfwidth_quotes.py` | 1次 | SKILL_01f_句读和标点校勘.md | chapter_md/*.tagged.md |
| `fix_heading_numbers.py` | 1次 | SKILL_02a_章节切分与编号.md | data/**/*.md |
| `fix_misplaced_fullwidth_quotes.py` | 1次 | SKILL_01f_句读和标点校勘.md | chapter_md/*.tagged.md |
| `fix_missing_parent_pn.py` | 2次 | SKILL_02a_章节切分与编号.md<br>references/SKILL_02a1_Purple_Numbers编号详细规范.md | chapter_md/*.tagged.md |
| `fix_nested_annotations.py` | 1次 | SKILL_01f_句读和标点校勘.md | data/**/*.md |
| `fix_section_position.py` | 1次 | SKILL_02a_章节切分与编号.md | data/**/*.md |
| `fix_square_quotes.py` | 1次 | SKILL_01f_句读和标点校勘.md | chapter_md/*.tagged.md |

---

## 生成工具 (generate)

生成各类报告、日志、目录等。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `generate_chinese_catalog.py` | - | - | kg/ontology/ontology-v1/CATALOG_CN.md |
| `generate_cost_report.py` | 1次 | SKILL_10g_项目成本与时间统计.md | logs/cost_reports/*.md |
| `generate_custom_variants.py` | - | - | docs/data/custom-variants.json |
| `generate_daily_log.py` | - | - | logs/daily/YYYY-MM-DD.md |
| `generate_detailed_catalog.py` | - | - | kg/ontology/ontology-v1/CATALOG_DETAIL.md |
| `generate_pdf.py` | - | - | output/shiji_*.pdf |
| `generate_pn_mapping.py` | - | - | data/pn_mapping.json |
| `generate_time_report.py` | 1次 | SKILL_10g_项目成本与时间统计.md | logs/time_reports/*.md |
| `generate_variants_from_comparison.py` | - | - | data/variants/comparison.json |

---

## 提取工具 (extract)

从文本中提取各类信息。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `extract_chengyu.py` | 1次 | SKILL_02h_词表构建.md | data/chengyu/*.json |
| `extract_epub_to_html.py` | - | - | output/*.html |
| `extract_paragraph_structure.py` | - | - | 终端输出（段落结构） |
| `extract_polyphone_contexts.py` | 1次 | SKILL_01d_正音与拼音标注.md | data/polyphone_contexts/*.json |
| `extract_pronunciation.py` | - | - | data/pronunciation/*.json |
| `extract_pronunciation_v2.py` | - | - | data/pronunciation/*.json |
| `extract_pronunciation_v3.py` | - | - | data/pronunciation/*.json |
| `extract_special_pronunciations.py` | 1次 | references/SKILL_01d2_史记正义提取方法.md | docs/data/special-pronunciation.json |
| `extract_special_pronunciations_v2.py` | - | - | docs/data/special-pronunciation-v2.json |
| `extract_taishigongyue.py` | 1次 | SKILL_02b_区块与韵文处理.md | data/taishigongyue/*.txt |
| `extract_variants_fuzzy.py` | 2次 | SKILL_01e_繁简体处理.md<br>archive/SKILL_01f_繁简词库构造分析.md | data/variants/*.json |
| `extract_yunwen.py` | - | - | data/yunwen/*.txt |
| `extract_zheng_words.py` | - | - | data/zheng_words.json |

---

## 分析工具 (analyze)

统计分析和数据挖掘。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `analyze_claude_token_usage.py` | 1次 | SKILL_10g_项目成本与时间统计.md | logs/analysis/*.md |
| `analyze_error_patterns.py` | - | - | logs/analysis/*.md |
| `analyze_paragraph_relations.py` | - | - | logs/analysis/*.md |
| `analyze_pn_changes.py` | - | - | logs/analysis/*.md |
| `analyze_polyphone_distribution.py` | - | - | logs/analysis/*.md |
| `analyze_polyphone_statistics.py` | 1次 | SKILL_01d_正音与拼音标注.md | logs/analysis/*.md |
| `analyze_pronunciation_candidates.py` | - | - | logs/analysis/*.md |
| `analyze_pronunciation_rules.py` | - | - | logs/analysis/*.md |
| `analyze_simp_trad_mapping.py` | 1次 | SKILL_01e_繁简体处理.md | logs/analysis/*.md |
| `analyze_tagged.py` | 可用 | 字频 + n-gram + 词表模式匹配（覆盖率统计已转至 `compute_annotation_coverage.py`） | doc/analysis/未标注实体分析报告.md |
| `compute_annotation_coverage.py` | 月度 | SKILL_02f_文本统计.md<br>SKILL_08b1_标注完成情况统计.md | doc/analysis/汉字标注覆盖率统计报告_{YYYYMMDD}.md |
| `pos_analysis.py` | 按需 | SKILL_08b1_标注完成情况统计.md | doc/analysis/pos/*.json<br>doc/analysis/pos_summary.md |
| `find_candidate_entities.py` | 按需 | SKILL_08b1_标注完成情况统计.md | doc/analysis/candidates/*.tsv |
| `analyze_time_investment.py` | 1次 | SKILL_10g_项目成本与时间统计.md | logs/analysis/*.md |
| `analyze_word_frequency.py` | 2次 | SKILL_02e_词法分析.md<br>SKILL_02f_文本统计.md | logs/analysis/*.md |

---

## 验证工具 (validate)

验证数据完整性和正确性。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `validate_opencc_conversion.py` | 1次 | SKILL_01e_繁简体处理.md | 终端输出/验证报告 |
| `validate_pronunciation_dict.py` | - | - | 终端输出/验证报告 |
| `validate_skill_frontmatter.py` | - | - | 终端输出/验证报告 |

---

## 迁移工具 (migrate)

数据格式迁移和转换。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| **`migrate_dynasty_to_feudal.py`** | **3次** | 00-META-08_标注体系设计.md<br>SKILL_03a_实体标注.md<br>SKILL_03e_按类型反思.md | chapter_md/*.tagged.md |
| **`migrate_official_to_identity.py`** | **4次** | 00-META-08_标注体系设计.md<br>SKILL_03a_实体标注.md<br>SKILL_03e_按类型反思.md<br>references/SKILL_10c1_禁止命令清单.md | chapter_md/*.tagged.md |
| `migrate_to_lenticular.py` | 2次 | 00-META-08_标注体系设计.md<br>SKILL_03a_实体标注.md | chapter_md/*.tagged.md |

---

## 渲染工具 (render)

将标注文本渲染为各种格式。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `render_chengyu_html.py` | 1次 | SKILL_02h_词表构建.md | docs/chapters/*.html |
| `render_structure_html.py` | - | - | 终端输出 |
| `render_structure_html_enhanced.py` | - | - | 终端输出 |
| `render_structure_knowledge_graph.py` | - | - | 终端输出 |
| `render_taishigongyue_html.py` | 1次 | SKILL_02b_区块与韵文处理.md | docs/chapters/*.html |
| `render_wars_html.py` | - | - | 终端输出 |
| `render_yunwen_html.py` | - | - | 终端输出 |

---

## 转换工具 (convert)

格式转换工具。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `convert_pronunciation_to_json.py` | 1次 | references/SKILL_01d2_史记正义提取方法.md | data/**/*.json |

---

## 更新工具 (update)

更新和维护各类数据文件。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `update_docspec_references.py` | - | - | 终端输出 |
| `update_index_sections.py` | - | - | 终端输出 |
| `update_skill_frontmatter.py` | 2次 | archive/SKILL_10f_Skill的提炼与转化_20260402.md<br>references/SKILL_10f3_更新维护指南.md | skills/*.md |
| `update_table_event_links.py` | - | - | 终端输出 |
| `update_timeline_pn.py` | - | - | 终端输出 |

---

## 章节处理 (section)

章节级别的操作。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `section_add_ids_to_html.py` | - | - | 终端输出 |
| `section_add_to_chapter.py` | 1次 | SKILL_02a_章节切分与编号.md | chapter_md/*.tagged.md |
| `section_auto_generate.py` | 1次 | SKILL_02a_章节切分与编号.md | chapter_md/*.tagged.md |
| `section_extract.py` | - | - | 终端输出 |
| `section_extract_all.py` | 1次 | SKILL_02a_章节切分与编号.md | chapter_md/*.tagged.md |
| `section_update_index.py` | 1次 | SKILL_02a_章节切分与编号.md | chapter_md/*.tagged.md |

---

## 格式化工具 (fmt)

代码和文本格式化。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `fmt_convert_quotes.py` | - | - | 终端输出 |
| `fmt_convert_quotes_batch.py` | - | - | 终端输出 |
| `fmt_fix_quotes.py` | - | - | 终端输出 |
| `fmt_fix_verse.py` | - | - | 终端输出 |
| `fmt_fix_zan.py` | - | - | 终端输出 |
| `fmt_md_tables.py` | - | - | 终端输出 |
| `fmt_split_dialogues.py` | - | - | 终端输出 |

---

## 标注工具 (tag)

自动标注工具。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `tag_identity_words.py` | 1次 | SKILL_02e_词法分析.md | chapter_md/*.tagged.md |
| `tag_kinship_words.py` | 1次 | SKILL_02e_词法分析.md | chapter_md/*.tagged.md |
| `tag_new_entity_types.py` | 2次 | SKILL_03a_实体标注.md<br>SKILL_03e_按类型反思.md | chapter_md/*.tagged.md |
| `tag_quantity_entities.py` | 1次 | SKILL_03a_实体标注.md | chapter_md/*.tagged.md |

---

## 构建工具 (build)

构建知识图谱等复杂结构。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `build_complete_pn_mapping.py` | - | - | 终端输出 |
| `build_complete_word_variants.py` | 1次 | SKILL_01e_繁简体处理.md | output/**/* |

---

## 测试工具 (test)

测试脚本和验证工具。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `test_du_pronunciation.py` | - | - | 终端输出/测试报告 |
| `test_inline_disambig.py` | - | - | 终端输出/测试报告 |
| `test_real_api_call.py` | - | - | 终端输出/测试报告 |
| `test_token_tracker.py` | - | - | 终端输出/测试报告 |

---

## 其他工具

配置文件和通用工具。

| 脚本 | 被引用 | 引用者SKILL | 产出物 |
|------|--------|-----------|--------|
| `add_table_row_pn.py` | 1次 | SKILL_02a_章节切分与编号.md | chapter_md/*.tagged.md（添加表格行编号） |
| `apply_annotation_patches.py` | - | - | 终端输出 |
| `apply_manual_fixes.py` | 1次 | SKILL_02h_词表构建.md | chapter_md/*.tagged.md（应用手动修复） |
| `audit_changelog_commits.py` | - | - | 终端输出 |
| `check_missing_parent_pn.py` | 1次 | SKILL_02a_章节切分与编号.md | data/**/* 或 终端输出 |
| `cleanup_zero_token_logs.py` | 1次 | SKILL_10g_项目成本与时间统计.md | data/**/* 或 终端输出 |
| `compare_with_wikisource.py` | 2次 | SKILL_01e_繁简体处理.md<br>archive/SKILL_01f_繁简词库构造分析.md | data/**/* 或 终端输出 |
| `config.py` | - | - | N/A (配置文件) |
| `create_v3_final.py` | 1次 | SKILL_01e_繁简体处理.md | data/**/* 或 终端输出 |
| `create_v3_variants.py` | - | - | 终端输出 |
| `demo_real_token_tracking.py` | - | - | 终端输出 |
| `detect_entity_boundary_errors.py` | 1次 | SKILL_03f_实体边界错误综合反思.md | data/**/* 或 终端输出 |
| `example_token_tracking.py` | - | - | 终端输出 |
| `expand_pronunciation_dict.py` | - | - | 终端输出 |
| `expand_single_char_rules.py` | - | - | 终端输出 |
| `export_wars_special.py` | - | - | 终端输出 |
| `find_actual_errors.py` | 1次 | SKILL_01e_繁简体处理.md | data/**/* 或 终端输出 |
| `find_pn_by_text.py` | - | - | 终端输出 |
| `find_real_boundary_errors.py` | 1次 | SKILL_03f_实体边界错误综合反思.md | data/**/* 或 终端输出 |
| `find_remaining_errors.py` | - | - | 终端输出 |
| `infer_entity_type.py` | - | - | 终端输出 |
| `infer_single_char_names.py` | 2次 | SKILL_02e_词法分析.md<br>SKILL_03c_按章反思.md | data/**/* 或 终端输出 |
| `parse_sanjia_notes.py` | - | - | 终端输出 |
| `parse_sanjia_notes_v2.py` | - | - | 终端输出 |
| `parse_sanjia_notes_v3.py` | - | - | 终端输出 |
| `polyphone_list.py` | - | - | 终端输出 |
| `pos_analysis.py` | 1次 | SKILL_02e_词法分析.md | data/**/* 或 终端输出 |
| `publish_tables_data.py` | 1次 | draft/META-SKILL-增量式数据更新.md | data/**/* 或 终端输出 |
| `publish_xingshi_data.py` | - | - | 终端输出 |
| `reflect_time_entity_types.py` | - | - | 终端输出 |
| `replace_with_unified_imports.py` | - | - | 终端输出 |
| `scan_biology_reflect.py` | 1次 | SKILL_02e_词法分析.md | data/**/* 或 终端输出 |
| `scan_untagged_aliases.py` | 1次 | SKILL_02e_词法分析.md | data/**/* 或 终端输出 |
| `semantic_tags.py` | 1次 | SKILL_05d_事实发现.md | data/**/* 或 终端输出 |
| `token_tracker.py` | 1次 | SKILL_10g_项目成本与时间统计.md | data/**/* 或 终端输出 |
| `unify_meta_titles.py` | - | - | 终端输出 |
| `verify_settings_panel.py` | - | - | 终端输出 |
| `verify_table_links.py` | - | - | 终端输出 |
| `verify_timeline_pn_content.py` | - | - | 终端输出 |
| `verify_v3_coverage.py` | 1次 | SKILL_01e_繁简体处理.md | data/**/* 或 终端输出 |

---

## 使用指南

### 脚本命名规范

- `lint_*.py` - 质量检查脚本，验证数据完整性
- `fix_*.py` - 自动修复脚本，修改源文件
- `generate_*.py` - 生成报告、日志等
- `extract_*.py` - 从文本中提取信息
- `analyze_*.py` - 统计分析工具
- `validate_*.py` - 验证工具
- `migrate_*.py` - 数据迁移工具
- `render_*.py` - 渲染输出工具
- `convert_*.py` - 格式转换工具
- `update_*.py` - 更新维护工具
- `section_*.py` - 章节处理工具
- `tag_*.py` - 标注工具
- `build_*.py` - 构建复杂结构
- `test_*.py` - 测试脚本

### 通用配置

所有脚本使用 `scripts/config.py` 中定义的路径常量：

```python
from scripts.config import CHAPTER_DIR, BASE_COPY, DATA_DIR
```

### 脚本生命周期

1. **开发阶段**: 新脚本在 `scripts/` 中开发
2. **活跃使用**: 被SKILL文档引用，定期运行
3. **归档阶段**: 完成使命后移至 `scripts/historical/`
4. **文档化**: 在本README和相关SKILL中记录用途

---

## 历史脚本

已完成使命的一次性脚本已移至 [scripts/historical/](historical/README.md)（76个）。

---

## 规划中的脚本（待实现）

以下脚本在SKILL文档中提及但尚未实现，按优先级排列。

### 高优先级（≥3次引用）

| 脚本 | 被引用 | 引用者SKILL |
|------|--------|-----------|
| `build_year_map.py` | 4次 | SKILL_03g_时间实体消歧.md<br>SKILL_04_事件构建.md<br>SKILL_04c_事件年代推断.md<br>SKILL_05a_事件关系发现.md |
| `migrate_verb_tags.py` | 4次 | SKILL_03c_按章反思.md<br>SKILL_04f_动词标注.md<br>references/SKILL_03c1-rules.md<br>references/SKILL_02e1_动词标注规范.md |
| `apply_reflect_fixes.py` | 3次 | 00-META-02_迭代工作流.md<br>SKILL_03e_按类型反思.md<br>SKILL_04d_事件年代审查.md |
| `build_metro_map_data.py` | 3次 | 00-META-11_数据体感培养.md<br>SKILL_05a_事件关系发现.md<br>SKILL_09a_语法高亮辅助阅读.md |
| `extract_events.py` | 3次 | SKILL_04_事件构建.md<br>SKILL_04a_事件识别.md<br>SKILL_05a_事件关系发现.md |
| `lint_ce_years.py` | 3次 | 00-META-10_质量控制.md<br>SKILL_04_事件构建.md<br>SKILL_05a_事件关系发现.md |
| `validate_events.py` | 3次 | SKILL_04_事件构建.md<br>SKILL_04a_事件识别.md<br>SKILL_05a_事件关系发现.md |

### 中优先级（2次引用）

| 脚本 | 被引用 | 引用者SKILL |
|------|--------|-----------|
| `annotate_ce_years.py` | 2次 | SKILL_04_事件构建.md<br>SKILL_05a_事件关系发现.md |
| `build_entity_index.py` | 2次 | SKILL_04c_事件年代推断.md<br>references/SKILL_10c1_禁止命令清单.md |
| `check_skill_freshness.py` | 2次 | archive/SKILL_10f_Skill的提炼与转化_20260402.md<br>references/SKILL_10f3_更新维护指南.md |
| `generate_review_prompts.py` | 2次 | 00-META-02_迭代工作流.md<br>SKILL_04d_事件年代审查.md |
| `lint.py` | 2次 | SKILL_10f_Skill的提炼与转化.md<br>archive/SKILL_10f_Skill的提炼与转化_20260402.md |
| `markdown_to_json.py` | 2次 | SKILL_05d_事实发现.md<br>references/SKILL_05d1_rules.md |
| `query_verbs_by_type.py` | 2次 | SKILL_04f_动词标注.md<br>references/SKILL_02e1_动词标注规范.md |
| `run_review_pipeline.py` | 2次 | SKILL_04_事件构建.md<br>SKILL_04d_事件年代审查.md |
| `validate_verb_tagging.py` | 2次 | SKILL_04f_动词标注.md<br>references/SKILL_02e1_动词标注规范.md |
| `xxx.py` | 2次 | archive/SKILL_10f_Skill的提炼与转化_20260402.md<br>references/SKILL_10f1_模板库.md |
| `yyy.py` | 2次 | archive/SKILL_10f_Skill的提炼与转化_20260402.md<br>references/SKILL_10f1_模板库.md |

### 低优先级（1次引用）

| 脚本 | 被引用 | 引用者SKILL |
|------|--------|-----------|
| `add_confidence_field.py` | 1次 | draft/META-SKILL-建设逻辑留痕.md |
| `analyze_qin_dates.py` | 1次 | 00-META-11_数据体感培养.md |
| `apply_coreference_tags.py` | 1次 | SKILL_02i_指代消解.md |
| `apply_date_fixes.py` | 1次 | draft/META-SKILL-批量反思管线.md |
| `apply_entity_fixes.py` | 1次 | draft/META-SKILL-批量反思管线.md |
| `audit_traditional.py` | 1次 | SKILL_09c_个性化阅读支持.md |
| `auto_generate_reasoning_log.py` | 1次 | draft/META-SKILL-建设逻辑留痕.md |
| `batch_fix_collapsed_dates.py` | 1次 | SKILL_04c_事件年代推断.md |
| `batch_reflect_dates.py` | 1次 | draft/META-SKILL-批量反思管线.md |
| `batch_reflect_entities.py` | 1次 | draft/META-SKILL-批量反思管线.md |
| `build_causal_relations.py` | 1次 | SKILL_05a_事件关系发现.md |
| `build_diming_vocab.py` | 1次 | SKILL_02h_词表构建.md |
| `build_epub.py` | 1次 | SKILL_09m_排版和电子书构造.md |
| `build_family_tree.py` | 1次 | SKILL_05c_人物关系构建.md |
| `build_geo_network.py` | 1次 | SKILL_05b_实体关系构建.md |
| `build_guanzhi_vocab.py` | 1次 | SKILL_02h_词表构建.md |
| `build_office_hierarchy.py` | 1次 | SKILL_05b_实体关系构建.md |
| `build_pinyin_dict.py` | 1次 | SKILL_09c_个性化阅读支持.md |
| `build_shihao_index.py` | 1次 | SKILL_07a_人物生卒年推断.md |
| `build_taxonomy.py` | 1次 | SKILL_06a_实体到本体.md |
| `build_traditional_dict.py` | 1次 | SKILL_09c_个性化阅读支持.md |
| `calculate_pmi.py` | 1次 | SKILL_05c_人物关系构建.md |
| `check_convergence.py` | 1次 | 00-META-02_迭代工作流.md |
| `check_markdown_links.py` | 1次 | archive/SKILL_10f_Skill的提炼与转化_20260402.md |
| `check_single_char_names.py` | 1次 | 00-META-11_数据体感培养.md |
| `check_XXX.py` | 1次 | 00-META-11_数据体感培养.md |
| `convert_to_luatex.py` | 1次 | SKILL_09m_排版和电子书构造.md |
| `convert_to_pandoc_latex.py` | 1次 | SKILL_09m_排版和电子书构造.md |
| `cross_validate_dates.py` | 1次 | 00-META-10_质量控制.md |
| `cross_validate_entities.py` | 1次 | 00-META-10_质量控制.md |
| `extract_blocks.py` | 1次 | SKILL_02b_区块与韵文处理.md |
| `extract_cooccurrence.py` | 1次 | SKILL_05c_人物关系构建.md |
| `extract_entity_relations.py` | 1次 | SKILL_05b_实体关系构建.md |
| `extract_event_relations.py` | 1次 | SKILL_05a_事件关系发现.md |
| `extract_family_relations.py` | 1次 | SKILL_05c_人物关系构建.md |
| `extract_geo_relations.py` | 1次 | SKILL_05b_实体关系构建.md |
| `extract_imperial_genealogy.py` | 1次 | SKILL_05c_人物关系构建.md |
| `extract_office_relations.py` | 1次 | SKILL_05b_实体关系构建.md |
| `extract_political_relations.py` | 1次 | SKILL_05c_人物关系构建.md |
| `extract_social_relations.py` | 1次 | SKILL_05c_人物关系构建.md |
| `extract_wars.py` | 1次 | SKILL_05e_战争事件识别.md |
| `fanqie_to_pinyin.py` | 1次 | references/SKILL_01d2_史记正义提取方法.md |
| `filter_candidate_relations.py` | 1次 | SKILL_05c_人物关系构建.md |
| `find_unmarked_animals.py` | 1次 | 00-META-11_数据体感培养.md |
| `fix_broken_tags.py` | 1次 | SKILL_03b_人名消歧.md |
| `fix_by_pattern.py` | 1次 | 00-META-11_数据体感培养.md |
| `fix_chapter_026_pn.py` | 1次 | references/SKILL_02a1_Purple_Numbers编号详细规范.md |
| `fix_nested_legal.py` | 1次 | references/SKILL_03c1-rules.md |
| `fix_undated_known_events.py` | 1次 | SKILL_04c_事件年代推断.md |
| `fix_verb_nesting.py` | 1次 | references/SKILL_02e1_动词标注规范.md |
| `generate_all_formats.py` | 1次 | SKILL_09m_排版和电子书构造.md |
| `generate_boundary_review.py` | 1次 | SKILL_03f_实体边界错误综合反思.md |
| `generate_date_review_prompts.py` | 1次 | draft/META-SKILL-批量反思管线.md |
| `generate_entity_review_prompts.py` | 1次 | draft/META-SKILL-批量反思管线.md |
| `generate_fix_script.py` | 1次 | draft/META-SKILL-批量反思管线.md |
| `generate_iteration_report.py` | 1次 | 00-META-02_迭代工作流.md |
| `generate_quality_report.py` | 1次 | 00-META-10_质量控制.md |
| `generate_smart_segments.py` | 1次 | SKILL_09c_个性化阅读支持.md |
| `infer_indirect_relations.py` | 1次 | SKILL_05c_人物关系构建.md |
| `infer_xingshi_batch.py` | 1次 | draft/META-SKILL-建设逻辑留痕.md |
| `ingest_review_results.py` | 1次 | 00-META-02_迭代工作流.md |
| `inspect_template.py` | 1次 | 00-META-11_数据体感培养.md |
| `lint_all.py` | 1次 | 00-META-11_数据体感培养.md |
| `lint_coreference.py` | 1次 | SKILL_02i_指代消解.md |
| `lint_typeset.py` | 1次 | SKILL_09m_排版和电子书构造.md |
| `lint_verb_tagging.py` | 1次 | references/SKILL_02e1_动词标注规范.md |
| `migrate_old_biology.py` | 1次 | SKILL_03e_按类型反思.md |
| `migrate_to_v2.py` | 1次 | 00-META-08_标注体系设计.md |
| `migrate_TYPE_fixes.py` | 1次 | SKILL_03e_按类型反思.md |
| `migrate_type_symbols.py` | 1次 | SKILL_01g_标注符号集合原则.md |
| `migrate_v1_to_v2.py` | 1次 | 00-META-07_可读性.md |
| `plot_event_timeline.py` | 1次 | 00-META-11_数据体感培养.md |
| `pre_annotate.py` | 1次 | archive/SKILL_10f_Skill的提炼与转化_20260402.md |
| `prepare_data.py` | 1次 | archive/SKILL_10f_Skill的提炼与转化_20260402.md |
| `quick_stats.py` | 1次 | 00-META-11_数据体感培养.md |
| `render_blocks_html.py` | 1次 | SKILL_02b_区块与韵文处理.md |
| `report_differences.py` | 1次 | 00-META-11_数据体感培养.md |
| `resolve_coreference_llm.py` | 1次 | SKILL_02i_指代消解.md |
| `resolve_coreference_rules.py` | 1次 | SKILL_02i_指代消解.md |
| `run_batch_review.py` | 1次 | 00-META-02_迭代工作流.md |
| `run_r10_r14.py` | 1次 | draft/META-SKILL-建设逻辑留痕.md |
| `scan_coreference_candidates.py` | 1次 | SKILL_02i_指代消解.md |
| `sync_todo_issue.py` | 1次 | SKILL_10a_TODO和Issue管理.md |
| `test_pinyin.py` | 1次 | SKILL_10e_文件组织与目录结构.md |
| `update_entity_stats.py` | 1次 | SKILL_10_项目管理.md |
| `update_skill_stats.py` | 1次 | archive/SKILL_10f_Skill的提炼与转化_20260402.md |
| `update_xingshi_from_md.py` | 1次 | draft/META-SKILL-增量式数据更新.md |
| `validate_after_iteration.py` | 1次 | 00-META-02_迭代工作流.md |
| `validate_family_tree.py` | 1次 | SKILL_05c_人物关系构建.md |
| `validate_tagging.py` | 1次 | 00-META-10_质量控制.md |
| `validate_wars.py` | 1次 | SKILL_05e_战争事件识别.md |
| `verify_in_shiji.py` | 1次 | references/SKILL_01d2_史记正义提取方法.md |
| `verify_semantic_integrity.py` | 1次 | SKILL_09m_排版和电子书构造.md |
| `verify_traditional.py` | 1次 | SKILL_09c_个性化阅读支持.md |
| `war_statistics.py` | 1次 | SKILL_05e_战争事件识别.md |
| `write_inferred_years.py` | 1次 | SKILL_04c_事件年代推断.md |

