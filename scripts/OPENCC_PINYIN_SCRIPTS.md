# OpenCC词库和拼音词库相关脚本清单

本文档列出所有与OpenCC词库（繁简转换）和拼音词库相关的脚本，这些脚本暂不进行分类移动。

## 一、OpenCC词库相关脚本

### 1. 词库生成与构建

| 脚本名 | 状态 | 功能说明 |
|--------|------|----------|
| `create_v3_final.py` | M | 创建最终的v3.0词库（移除错误规则，添加新规则） |
| `create_v3_variants.py` | M | 创建v3.0自定义词库变体 |
| `build_complete_word_variants.py` | - | 构建完整的词组变体规则 |
| `generate_custom_variants.py` | - | 生成custom-variants.json |
| `generate_variants_from_comparison.py` | - | 通过比较简繁版本生成词库 |
| `expand_single_char_rules.py` | M | 扩展单字规则 |

### 2. 词库验证与检查

| 脚本名 | 状态 | 功能说明 |
|--------|------|----------|
| `verify_v3_coverage.py` | M | 验证v3.0词库覆盖率（模拟OpenCC最长匹配） |
| `validate_opencc_conversion.py` | - | 验证OpenCC转换结果 |
| `find_actual_errors.py` | M | 找出真实的OpenCC错误 |
| `find_remaining_errors.py` | M | 找出OpenCC转换中剩余的错误用例 |

### 3. 词库提取与分析

| 脚本名 | 状态 | 功能说明 |
|--------|------|----------|
| `compare_with_wikisource.py` | - | 逐字比较简繁版本，提取OpenCC转换差异 |
| `extract_variants_fuzzy.py` | - | 忽略校勘差异，只关注OpenCC未覆盖的繁简转换 |
| `analyze_simp_trad_mapping.py` | - | 分析简繁字映射关系 |

### 4. 词库工具脚本

| 脚本名 | 状态 | 功能说明 |
|--------|------|----------|
| `add_converter_scripts.py` | - | 添加转换器脚本 |
| `replace_with_unified_imports.py` | - | 替换为统一的导入语句 |

## 二、拼音词库相关脚本

### 1. 拼音提取

| 脚本名 | 状态 | 功能说明 |
|--------|------|----------|
| `extract_pronunciation.py` | - | 提取拼音标注（v1） |
| `extract_pronunciation_v2.py` | - | 提取拼音标注（v2） |
| `extract_pronunciation_v3.py` | - | 提取拼音标注（v3，当前版本） |
| `extract_special_pronunciations.py` | - | 提取特殊读音 |
| `extract_special_pronunciations_v2.py` | - | 提取特殊读音（v2） |

### 2. 拼音词库构建

| 脚本名 | 状态 | 功能说明 |
|--------|------|----------|
| `expand_pronunciation_dict.py` | - | 扩展拼音词典 |
| `convert_pronunciation_to_json.py` | - | 转换拼音数据为JSON格式 |

### 3. 拼音分析与验证

| 脚本名 | 状态 | 功能说明 |
|--------|------|----------|
| `analyze_polyphone_distribution.py` | - | 分析多音字分布 |
| `analyze_pronunciation_candidates.py` | - | 分析拼音候选 |
| `validate_pronunciation_dict.py` | - | 验证拼音词典 |
| `test_du_pronunciation.py` | - | 测试"都"字读音 |

## 三、其他相关脚本

### 文档引用更新

| 脚本名 | 状态 | 功能说明 |
|--------|------|----------|
| `update_docspec_references.py` | ?? | 更新doc/spec下文件引用（包含词库文档） |

## 状态说明

- `M`: 已修改但未暂存
- `??`: 新增未跟踪
- `-`: 已提交到版本库

## 统计

- **OpenCC词库相关**: 13个脚本
- **拼音词库相关**: 11个脚本
- **共计**: 24个脚本

## 注意事项

1. 这些脚本暂不进行目录分类移动
2. 保留在 `scripts/` 根目录
3. 待OpenCC和拼音相关工作稳定后再考虑整理
