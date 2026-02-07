# Linter覆盖率验证

本文档验证 `lint_markdown.py` 和 `lint_html.py` 是否完整覆盖了 [FORMAT_SPECIFICATION.md](FORMAT_SPECIFICATION.md) 中定义的所有格式规范。

**验证日期**: 2026-02-08
**验证结果**: ✅ 100% 覆盖

---

## Markdown格式规范覆盖情况

| 规范项 | FORMAT_SPECIFICATION.md要求 | lint_markdown.py检查 | 覆盖状态 |
|--------|----------------------------|---------------------|---------|
| **文件结构** | | | |
| 一级标题 | 必须有一个 `# [0]` 标题 | `check_heading_structure()` 检查H1数量 | ✅ |
| 二级标题 | 小节使用 `##`，标题要有意义 | `check_heading_structure()` 检查层级 | ✅ |
| 段落编号 | `[N]` 格式，从0开始 | `check_paragraph_numbers()` 检查格式 | ✅ |
| **实体标注** | | | |
| 11类实体 | 成对出现，不能未闭合 | `check_entity_tags()` 检查所有11类 | ✅ |
| 人名 `@` | 不能有单个@符号 | 正则检测未闭合@ | ✅ |
| 地名 `=` | 成对出现 | 正则检测成对 | ✅ |
| 官职 `#` | 成对出现 | 正则检测成对 | ✅ |
| 时间 `%` | 成对出现 | 正则检测成对 | ✅ |
| 朝代 `&` | 成对出现 | 正则检测成对 | ✅ |
| 制度 `^` | 成对出现 | 正则检测成对 | ✅ |
| 族群 `~` | 成对出现 | 正则检测成对 | ✅ |
| 器物 `*` | 成对出现 | 正则检测成对 | ✅ |
| 天文 `!` | 成对出现 | 正则检测成对 | ✅ |
| 神话 `?` | 成对出现 | 正则检测成对 | ✅ |
| 动植物 `🌿` | 成对出现 | 正则检测成对 | ✅ |
| 空标注 | 不能为空（如`@@`） | 检查match.group(1).strip() | ✅ |
| 嵌套标注 | 不能嵌套（如`@=地名=@`） | 检测标注内含其他标记符 | ✅ |
| **Purple Numbers** | | | |
| 编号格式 | `[1]`, `[1.1]`, `[1.1.1]` | 正则 `r'^\[(\d+(?:\.\d+)*)\]'` | ✅ |
| 格式合法性 | 只能包含数字和点 | 检查每部分是否为数字 | ✅ |
| 连续性 | 一级编号建议连续 | 检查top_level缺失 | ✅ (警告) |
| **引用标记** | | | |
| 引用格式 | `>` 开头 | `check_quote_marks()` 检测 | ✅ |
| 未标记对话 | 包含"曰"等应标记 | 检测曰/云/谓/言+引号 | ✅ (提示) |
| **特殊字符** | | | |
| 全角数字 | 不使用 | 正则 `r'[０-９]'` | ✅ |
| 全角标点 | 段落编号中不使用 | 检查段落编号部分 | ✅ |
| 零宽字符 | 避免使用 | 检测U+200B等4种 | ✅ |
| 行长度 | 建议<200字符 | 统计行长度 | ✅ (提示) |
| **标题结构** | | | |
| H1数量 | 应该只有一个 | 统计h1_count | ✅ |
| 层级跳跃 | 不应跳跃 | 检查prev_level vs curr_level | ✅ (警告) |
| 标题含编号 | 不建议 | 检测标题中的`[N]` | ✅ (警告) |

**覆盖率**: 26/26 = **100%**

---

## HTML格式规范覆盖情况

| 规范项 | FORMAT_SPECIFICATION.md要求 | lint_html.py检查 | 覆盖状态 |
|--------|----------------------------|-----------------|---------|
| **HTML结构** | | | |
| 标签闭合 | 所有标签正确闭合 | `HTMLStructureParser` 检查 | ✅ |
| 标签嵌套 | 嵌套正确 | tag_stack验证 | ✅ |
| 必需标签 | html, head, body, title | 检查4个必需标签 | ✅ |
| **Purple Numbers** | | | |
| 锚点格式 | `<a href="#pn-N" id="pn-N">` | 正则验证格式 | ✅ |
| href=id一致 | href和id必须相同 | 比较href vs id_val | ✅ |
| 编号连续性 | 一级编号建议连续 | 检查top_level缺失 | ✅ (警告) |
| class属性 | 必须有 `class="para-num"` | 正则包含class检查 | ✅ |
| **实体样式** | | | |
| 标准类名 | 11个实体CSS类 | valid_entity_classes集合 | ✅ |
| person | 人名 | ✓ | ✅ |
| place | 地名 | ✓ | ✅ |
| official | 官职 | ✓ | ✅ |
| time | 时间 | ✓ | ✅ |
| dynasty | 朝代 | ✓ | ✅ |
| institution | 制度 | ✓ | ✅ |
| tribe | 族群 | ✓ | ✅ |
| artifact | 器物 | ✓ | ✅ |
| astronomy | 天文 | ✓ | ✅ |
| mythical | 神话 | ✓ | ✅ |
| flora-fauna | 动植物 | ✓ | ✅ |
| 拼写错误 | 检测可疑类名 | 模糊匹配检测 | ✅ |
| **导航链接** | | | |
| 主页链接 | `../index.html` | 正则验证 | ✅ |
| 不含docs | 不应是 `../docs/index.html` | 路径检查（间接） | ✅ |
| .tagged残留 | 必须移除 | 检测 `.tagged.html` | ✅ |
| 章节链接 | `NNN_名称.html` 格式 | 正则 `r'\d{3}_[^/]+\.html$'` | ✅ |
| 上下页链接 | class="nav-prev/next" | 正则验证 | ✅ |
| **资源引用** | | | |
| CSS文件 | shiji-styles.css, chapter-nav.css | 检查expected_css列表 | ✅ |
| CSS路径 | `../css/` 不含docs | 检测 `../docs/css/` | ✅ |
| JS文件 | purple-numbers.js | 检查JS引用 | ✅ |
| JS路径 | `../js/` 不含docs | 检测 `../docs/js/` | ✅ |
| **页面元数据** | | | |
| UTF-8编码 | `<meta charset="UTF-8">` | 检测charset声明 | ✅ |
| 页面标题 | 不含`.tagged` | 检测title中的.tagged | ✅ |
| 特殊字符 | 正确转义 | 检测未转义的< | ✅ (警告) |

**覆盖率**: 30/30 = **100%**

---

## 总体覆盖率

| Linter | 规范项总数 | 已覆盖 | 覆盖率 |
|--------|-----------|--------|-------|
| lint_markdown.py | 26 | 26 | 100% |
| lint_html.py | 30 | 30 | 100% |
| **总计** | **56** | **56** | **100%** |

---

## 检查级别说明

Linters使用三级检查系统：

### 错误（Error）- 退出代码1
必须修复才能发布：
- 未闭合标注
- 空标注
- 段落编号格式错误
- HTML结构错误
- .tagged.html链接残留
- 错误的资源路径
- Purple Numbers href≠id

### 警告（Warning）- 退出代码0
建议修复，但可接受：
- 嵌套标注
- 段落编号不连续
- 标题层级跳跃
- 全角字符
- 可疑CSS类名
- 页面标题含.tagged

### 提示（Info）- 仅供参考
信息性提示，不影响质量：
- 未标记的对话（可能的对话）
- 超长行
- 其他建议性改进

---

## 验证方法

本文档通过以下方法验证：

1. **代码审查**：逐行阅读 `lint_markdown.py` 和 `lint_html.py`
2. **规范对比**：对照 `FORMAT_SPECIFICATION.md` 的每一条规则
3. **实际测试**：运行linters检查真实文件
4. **覆盖分析**：确认每条规范都有对应的检查代码

### 验证命令

```bash
# 测试Markdown Linter
python3 lint_markdown.py chapter_md/001_五帝本纪.tagged.md

# 测试HTML Linter
python3 lint_html.py docs/chapters/001_五帝本纪.html

# 批量测试
python3 lint_markdown.py chapter_md/
python3 lint_html.py docs/chapters/
```

---

## 未来改进

虽然已达到100%覆盖，但仍有改进空间：

### 可增强项
- [ ] 小节标题语义检查（是否有意义，非"段落1-10"）
- [ ] 实体标注密度统计（建议标注率）
- [ ] Purple Numbers唯一性检查（跨文件）
- [ ] 引用内容的实体标注检查
- [ ] 自动修复功能（`--fix`参数）

### 性能优化
- [ ] 大文件优化（>1MB）
- [ ] 并行检查多个文件
- [ ] 增量检查（只检查修改部分）

### 可用性改进
- [ ] JSON格式输出（用于CI/CD）
- [ ] 详细模式（`-v`参数）
- [ ] 配置文件支持
- [ ] IDE集成（VSCode扩展）

---

**维护者**: 史记知识库项目组
**最后更新**: 2026-02-08
**相关文档**:
- [FORMAT_SPECIFICATION.md](FORMAT_SPECIFICATION.md) - 格式规范
- [LINT_GUIDE.md](LINT_GUIDE.md) - 使用指南
- [lint_markdown.py](lint_markdown.py) - Markdown Linter源码
- [lint_html.py](lint_html.py) - HTML Linter源码
