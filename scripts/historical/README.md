# scripts/historical/ - 历史性一次性脚本

本目录存放项目发展过程中使用的**一次性批处理脚本**。

这些脚本已完成其历史使命，保留用于：
- 记录项目演进过程
- 作为类似问题的参考实现
- Git历史溯源

---

## 目录说明

**脚本总数**: 76个（已将18个被SKILL引用的脚本移回scripts/）
**分类**: 10大类

| 分类 | 数量 | 说明 |
|------|------|------|
| fix_*.py | 26 | 一次性修复脚本（标注修复、格式修复等） |
| migrate_*.py | 2 | 格式迁移脚本（v1→v2版本迁移） |
| batch_*.py | 6 | 批量处理脚本（反思、标注等） |
| renumber_*.py | 5 | 编号重排脚本 |
| add_*.py | 4 | 功能添加脚本 |
| remove_*/clean*.py | 5 | 清理脚本 |
| tag_*.py | 1 | 标注脚本 |
| restore_*.py | 1 | 恢复脚本 |
| 其他历史脚本 | 9 | 早期工具脚本 |
| temp/batch_scripts/ | 18 | 早期批量处理脚本（2024年1-3月） |
| temp/tools/ | 17 | 早期临时工具（2024年1-3月） |

**注意**: 原有59个从scripts/迁移的脚本中，有18个被SKILL文档引用，已移回scripts/目录。

---

## 主要脚本列表

### 格式迁移 (migrate_*.py, 5个)
- `migrate_footnotes.py` - 迁移脚注格式
- `migrate_v1_to_v2.py` - v1→v2版本迁移
- `migrate_v2_to_v3.py` - v2→v3版本迁移
- `migrate_to_shiji_md_v2.py` - 迁移到shiji.md v2格式
- `migrate_to_v4.py` - 迁移到v4格式

### 一次性修复 (fix_*.py, 33个)
涵盖标注修复、格式修复、实体修复、引号修复等多个方面。

代表性脚本：
- `fix_nested_tags.py` - 修复嵌套标注
- `fix_halfwidth_quotes.py` - 修复半角引号
- `fix_person_name_simplification.py` - 修复人名简称标注
- `fix_place_name_tags.py` - 修复地名标注
- `fix_book_title_tags.py` - 修复书名标注
- `fix_time_expression_format.py` - 修复时间表达式格式

### 批量处理 (batch_*.py, 6个)
- `batch_reflect_liezhuan.py` - 批量反思列传章节
- `batch_add_war_tags.py` - 批量添加战争标注
- `batch_tag_official_titles.py` - 批量标注官职
- `batch_tag_dynasties.py` - 批量标注朝代
- `batch_update_frontmatter.py` - 批量更新frontmatter
- `batch_process_chapters.py` - 批量处理章节

### 编号重排 (renumber_*.py, 5个)
- `renumber_paragraphs.py` - 重新编号段落
- `renumber_footnotes.py` - 重新编号脚注
- `renumber_all_chapters.py` - 重新编号所有章节
- `renumber_sections.py` - 重新编号小节
- `renumber_subsections.py` - 重新编号子节

### 功能添加 (add_*.py, 5个)
- `add_paragraph_numbers.py` - 添加段落编号
- `add_frontmatter.py` - 添加frontmatter
- `add_war_events.py` - 添加战争事件
- `add_cross_references.py` - 添加交叉引用
- `add_dynasty_markers.py` - 添加朝代标记

### 清理脚本 (remove_*/clean*.py, 6个)
- `remove_duplicate_tags.py` - 删除重复标注
- `remove_empty_tags.py` - 删除空标注
- `remove_footnote_markers.py` - 删除脚注标记
- `clean_whitespace.py` - 清理空白字符
- `clean_punctuation.py` - 清理标点
- `clean_annotations.py` - 清理标注

### 标注脚本 (tag_*.py, 4个)
- `tag_person_names.py` - 标注人名
- `tag_place_names.py` - 标注地名
- `tag_book_titles.py` - 标注书名
- `tag_official_titles.py` - 标注官职

### 恢复脚本 (restore_*.py, 1个)
- `restore_from_backup.py` - 从备份恢复

---

## temp/ 目录脚本（35个，已迁移）

**迁移时间**: 2026-04-05
**原路径**: `temp/batch_scripts/` 和 `temp/tools/`
**创建时期**: 2024年1-3月（项目早期）

这些脚本是项目早期的临时性批处理工具，已完成历史使命。

### temp/batch_scripts/ - 早期批量处理脚本（18个）

用于批量处理特定章节范围的标注工作：

| 脚本 | 说明 |
|------|------|
| `batch_process_chapters.py` | 批量处理章节（通用框架） |
| `batch_tag_chapters_021_040.py` | 批量标注021-040章 |
| `batch_tag_033_040.py` | 批量标注033-040章 |
| `batch_tag_088_095.py` | 批量标注088-095章 |
| `batch_tag_remaining.py` | 批量标注剩余章节 |
| `process_033_040.py` | 处理033-040章 |
| `process_chapters_031_042.py` | 处理031-042章（本纪） |
| `process_chapters_081_100.py` | 处理081-100章 |
| `process_chapters_084_095.py` | 处理084-095章 |
| `process_chapters_096_110.py` | 处理096-110章 |
| `process_096_110.py` | 处理096-110章（简化版） |
| `process_096_110_manual.py` | 处理096-110章（手动版） |
| `process_chapters_101_130.py` | 处理101-130章 |
| `process_chapters_101_130_robust.py` | 处理101-130章（健壮版） |
| `process_chapters_111_130.py` | 处理111-130章 |
| `process_shijia_043_050.py` | 处理043-050章（世家） |
| `process_shijia_051_060.py` | 处理051-060章（世家） |
| `process_liezhuan_061_080.py` | 处理061-080章（列传） |

**使用场景**：
- 项目早期尚未建立统一的批量处理框架
- 针对不同章节类型（本纪、世家、列传）使用不同的处理策略
- 这些脚本已被 `scripts/` 下的统一工具替代

### temp/tools/ - 早期临时工具（17个）

早期实验性标注工具和格式转换工具：

| 脚本 | 说明 |
|------|------|
| `annotate_entities.py` | 实体标注工具（v1） |
| `annotate_entities_v2.py` | 实体标注工具（v2） |
| `annotate_entities_v3.py` | 实体标注工具（v3） |
| `semantic_tagger.py` | 语义标注器（基于词表） |
| `tag_002_entities.py` | 标注第002章实体 |
| `split_dialogues.py` | 对话分割工具（v1） |
| `split_dialogues_v2.py` | 对话分割工具（v2） |
| `split_shiji.py` | 史记文本分割工具 |
| `add_numbering.py` | 添加编号工具 |
| `convert_spans_to_simple.py` | HTML span转简化格式 |
| `fix_sections.py` | 修复章节结构（v1） |
| `fix_sections2.py` | 修复章节结构（v2） |
| `fix_zan_format.py` | 修复赞文格式 |
| `check_zan_format.py` | 检查赞文格式 |
| `generate_html_051_060.py` | 生成051-060章HTML |
| `improve_readability.py` | 提升可读性工具 |
| `replace_place_tokens.py` | 替换地名标记 |

**历史价值**：
- 记录了项目标注体系的演进过程（v1→v2→v3）
- 对话分割、赞文格式等早期探索
- 这些功能已整合到 `scripts/` 下的统一工具中

---

## 使用建议

1. **不要直接运行**：这些脚本已完成历史任务，直接运行可能导致数据不一致
2. **参考实现**：遇到类似问题时，可以参考脚本思路
3. **Git历史**：使用 `git log --follow scripts/historical/<script>` 查看脚本演进历史

---

## 活跃脚本位置

当前活跃使用的脚本仍在 `scripts/` 根目录，包括：
- `lint_*.py` - 检查脚本
- `generate_*.py` - 生成脚本
- `extract_*.py` - 提取脚本
- `convert_*.py` - 转换脚本
- `update_*.py` - 更新脚本
- `validate_*.py` - 验证脚本

---

**创建日期**: 2026-04-05
**脚本来源**:
- 41个脚本从 `scripts/` 根目录迁移（59个中有18个被SKILL引用，已移回）
- 35个脚本从 `temp/` 目录迁移
**迁移原因**: 保持活跃目录整洁，突出常用脚本

**已移回scripts/的18个脚本** (被SKILL引用):
- `migrate_official_to_identity.py` (4次引用)
- `migrate_dynasty_to_feudal.py` (3次引用)
- `fix_missing_parent_pn.py` (2次引用)
- `migrate_to_lenticular.py` (2次引用)
- `tag_new_entity_types.py` (2次引用)
- `add_table_row_pn.py`, `cleanup_zero_token_logs.py`, `fix_all_halfwidth_symbols.py`, `fix_entity_boundary_errors.py`, `fix_halfwidth_quotes.py`, `fix_heading_numbers.py`, `fix_misplaced_fullwidth_quotes.py`, `fix_nested_annotations.py`, `fix_section_position.py`, `fix_square_quotes.py`, `tag_identity_words.py`, `tag_kinship_words.py`, `tag_quantity_entities.py` (各1次引用)

---

## 目录结构

```
scripts/historical/
├── README.md                          # 本文件
├── fix_*.py                          # 26个修复脚本（已移出7个到scripts/）
├── migrate_*.py                      # 2个迁移脚本（已移出3个到scripts/）
├── batch_*.py                        # 6个批量处理脚本
├── renumber_*.py                     # 5个编号脚本
├── add_*.py                          # 4个添加脚本（已移出1个到scripts/）
├── remove_*.py, clean*.py            # 5个清理脚本（已移出1个到scripts/）
├── tag_*.py                          # 1个标注脚本（已移出3个到scripts/）
├── restore_*.py                      # 1个恢复脚本
├── 其他历史脚本                       # 9个早期工具
└── temp/                             # 早期临时脚本（35个）
    ├── batch_scripts/                # 18个早期批量处理脚本
    └── tools/                        # 17个早期临时工具
```
