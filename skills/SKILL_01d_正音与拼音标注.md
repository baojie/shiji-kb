---
name: skill-01d
title: 正音与拼音标注
description: 为《史记》文本添加准确的拼音注释，特别处理古代人名、地名等特殊读音。基于上下文分析的v4.0工作流程，通过Ruby标注实现拼音与汉字精确对齐。
---

# SKILL_01d 正音与拼音标注

> **核心理念**：准确的读音标注基于上下文分析，而非猜测。特殊词表只收录pinyin-pro无法正确处理的词条。

---

## 快速开始

### 何时使用

- 为章节HTML添加拼音注释
- 处理多音字、古地名、人名的特殊读音
- 维护特殊读音词表（`docs/data/special-pronunciation.json`）
- 分析多音字的上下文规律

### 核心步骤（3步）

```bash
# 1. 生成带拼音的HTML
python render_shiji_html.py chapter_md/001_五帝本纪.tagged.md docs/chapters/001_五帝本纪.html

# 2. 查看效果（浏览器打开HTML，点击设置图标控制拼音显示）
open docs/chapters/001_五帝本纪.html

# 3. Lint检查词表质量（确保只保留必要词条）
node scripts/lint_pronunciation_dict.js
```

### 成功标准

- [ ] HTML中所有汉字都有拼音标注（使用 `<ruby>` 标签）
- [ ] 特殊读音（地名、人名）显示正确
- [ ] Lint检查通过：所有词条都是pinyin-pro无法正确处理的
- [ ] 词表版本号更新，描述清晰

---

## 工具与脚本

### 核心工具

| 工具 | 用途 | 示例 |
|------|------|------|
| `render_shiji_html.py` | 渲染HTML并集成拼音脚本 | `python render_shiji_html.py input.md output.html` |
| `scripts/lint_pronunciation_dict.js` | 检查词表质量 | `node scripts/lint_pronunciation_dict.js` |
| `scripts/test_pinyin_pro.js` | 测试pinyin-pro输出 | `node scripts/test_pinyin_pro.js` |
| `scripts/extract_polyphone_contexts.py` | 提取多音字上下文 | `python scripts/extract_polyphone_contexts.py 王` |
| `scripts/analyze_polyphone_statistics.py` | 分析多音字统计 | `python scripts/analyze_polyphone_statistics.py` |

### 前端资源

| 文件 | 功能 |
|------|------|
| `docs/js/heading-pinyin.js` | 前端拼音标注核心逻辑 |
| `docs/js/settings-panel.js` | 拼音开关控制 |
| `docs/css/shiji-styles.css` (L245-298) | Ruby标注CSS样式 |

### 数据文件

| 文件 | 说明 |
|------|------|
| `docs/data/special-pronunciation.json` | 特殊读音词表（当前v3.12，119词条） |
| `data/pronunciation_templates/*_pronunciation.md` | 多音字标注模板 |
| `data/polyphone_contexts/*_contexts.json` | 多音字上下文数据 |

---

## 多音字正音工作流（v4.0）

### 工作流程图

```
1. 提取上下文 → 2. 人工标注 → 3. 测试词条 → 4. 更新词表 → 5. 验证完整性
    ↓                ↓               ↓              ↓               ↓
 contexts.json  *_annotated.md  lint_dict.js  special-pron.json  文本完整性
```

### 详细步骤

#### 步骤1: 提取上下文

```bash
# 提取指定多音字的所有上下文（左右各2字，遇标点停止）
python scripts/extract_polyphone_contexts.py 王
# 输出: data/polyphone_contexts/王_contexts.json
#       data/polyphone_contexts/王_contexts.txt
```

#### 步骤2: 分析统计数据

```bash
# 分析多音字的频率分布和上下文模式
python scripts/analyze_polyphone_statistics.py
# 查看: data/polyphone_contexts/王_contexts.json
```

#### 步骤3: 人工标注

编辑模板文件，为每个词组标注正确读音：

```markdown
| 词组 | 拼音 | 频率 | 说明 |
|------|------|------|------|
| 王曰 | wáng | 90 | 国王说（名词） |
| 王天下 | wàng | 3 | 统治天下（动词） |
```

**重要原则**：
- **查证权威**：不确定的读音必须查Wiktionary
- **只标注必要项**：能组词就组词，不要添加单字词条
- **验证原文**：结合《史记》原文判断语境

#### 步骤4: 测试词条必要性 ⚠️ 关键步骤

```bash
# 测试pinyin-pro输出
node scripts/test_pinyin_pro.js

# 示例
const {pinyin} = require('pinyin-pro');
console.log('称王:', pinyin('称王', {toneType: 'symbol', type: 'array'}));
# 输出: ['chēng', 'wáng']
# 如果输出正确 → 不添加到词表
# 如果输出错误 → 添加到词表
```

**判断标准**：
- ✅ pinyin-pro输出错误 → 添加词条
- ❌ pinyin-pro输出正确 → 不添加（即使看起来"应该"标注）

#### 步骤5: 更新special-pronunciation.json

```json
{
  "version": "3.12",
  "description": "...",
  "lastUpdate": "2026-04-04",
  "entries": [
    {
      "text": "王天下",
      "pinyin": ["wàng", "tiān", "xià"],
      "context": "动词",
      "note": "统治天下，'王'读wàng（去声），动词"
    }
  ]
}
```

#### 步骤6: Lint验证

```bash
# 检查词表质量
node scripts/lint_pronunciation_dict.js

# 期望输出:
# ✓ 需要保留: 119 (pinyin-pro处理错误)
# ✗ 应该删除: 0 (pinyin-pro已正确处理)
```

#### 步骤7: 文本完整性验证

```bash
# 验证标注文件没有改变原文
python scripts/lint_text_integrity.py chapter_md/001_*.tagged.md
```

---

## 特殊读音词表设计原则（v3.0）

### 核心铁律

**原则1: 最小化原则**
- 只收录pinyin-pro无法正确处理的词条
- 能组词就组词，不添加单字词条
- 定期Lint清理冗余词条

**原则2: 固定词组优先**
```json
// ✅ 推荐：固定词组
{"text": "车骑将军", "pinyin": ["chē", "jì", "jiàng", "jūn"]}

// ❌ 避免：单字词条（除非特殊情况）
{"text": "骑", "pinyin": ["jì"]}
```

**原则3: 查证权威来源**
- 优先查Wiktionary: https://en.wiktionary.org/wiki/
- 参考《史记正义》音注
- 结合原文语境判断

### 允许的单字词条例外

**情况1: 修正默认库错误**
```json
// pinyin-pro错误标注"於"为wū，实际应为yú
{"text": "於", "pinyin": ["yú"], "context": "介词"}
```

**情况2: 低风险姓氏**
```json
// "缪"姓读miào，但pinyin-pro默认móu
{"text": "缪", "pinyin": ["miào"], "context": "姓氏"}
```

**详细规则与案例**：参见 [SKILL_01d1_词表设计原则详解](./references/SKILL_01d1_词表设计原则详解.md)

---

## 完整检查清单（v4.1）

### 执行前检查

- [ ] 已安装依赖：`npm install pinyin-pro`，`pip install pypinyin`
- [ ] 特殊读音词表存在：`docs/data/special-pronunciation.json`
- [ ] 原文文件存在：`chapter_md/*.tagged.md`

### 上下文分析阶段

- [ ] **步骤1**: 提取上下文完整（2字窗口，遇标点停止）
- [ ] **步骤2**: 生成标注模板（包含高频词组）
- [ ] **步骤3**: 人工标注完成
  - [ ] 查证Wiktionary权威读音
  - [ ] 结合原文语境验证
  - [ ] 不添加单字词条（除非符合例外）

### 词表更新阶段

- [ ] **步骤4**: 测试pinyin-pro输出
  - [ ] 每个词条都经过测试
  - [ ] 只保留pinyin-pro错误的词条
  - [ ] 原文验证（避免"欲王"事件）
- [ ] **步骤5**: 更新special-pronunciation.json
  - [ ] 版本号递增
  - [ ] description说明本次变更
  - [ ] note字段清晰（含读音、词性、含义）
- [ ] **步骤6**: Lint验证通过
- [ ] **步骤7**: 文本完整性检查通过

### 执行后验证

- [ ] HTML拼音显示正确
- [ ] 无嵌套标注（如 `〖#〖#text〗〗`）
- [ ] 无半角引号（必须全角 `""`）
- [ ] Git提交包含：词表、标注文件、contexts数据

### 常见错误检查

❌ **错误1**: 主观判断读音，未查Wiktionary
- **教训**: "称王"案例（2026-04-04），错误标注wàng，实际为wáng

❌ **错误2**: 只测试孤立词条，未验证原文
- **教训**: "欲王"险些删除，孤立测试显示正确，但原文中是动词wàng

❌ **错误3**: 使用Edit工具时引入半角引号
- **预防**: 修改后立即运行 `grep -n '["'"'"'`]' file.md`

---

## 维护建议

### 月度检查

- [ ] 运行 `node scripts/lint_pronunciation_dict.js`
- [ ] 检查词表规模（推荐<150词条）
- [ ] 清理pinyin-pro已修复的词条

### 季度审查

- [ ] 更新pinyin-pro到最新版
- [ ] 重新测试所有词条必要性
- [ ] 更新SKILL文档统计数据

---

## FAQ

### Q1: 什么时候需要添加词条？

**A**: 满足以下所有条件：
1. pinyin-pro输出错误（用scripts/test_pinyin_pro.js测试）
2. 能组成固定词组（2-4字）
3. 在《史记》中出现≥3次

### Q2: 如何判断多音字的读音？

**A**: 按以下优先级：
1. 查Wiktionary权威标注
2. 参考《史记正义》音注
3. 结合原文语境（动词/名词/官职/地名）

### Q3: 为什么不能添加单字词条？

**A**: 单字词条容易误伤：
- "行"单字标注会导致"银行"、"行为"等常用词错误
- 改用"五行"、"大行"等固定词组，精准控制范围

### Q4: Lint检查失败怎么办？

**A**:
```bash
# 1. 查看哪些词条pinyin-pro已正确处理
node scripts/lint_pronunciation_dict.js

# 2. 手动测试确认
node scripts/test_pinyin_pro.js

# 3. 删除冗余词条，更新版本号
```

---

## 相关文档

### References（详细资料）

- [SKILL_01d1_词表设计原则详解](./references/SKILL_01d1_词表设计原则详解.md) - 特殊读音词表v3.0设计原则、版本演化、案例详解
- [SKILL_01d2_史记正义提取方法](./references/SKILL_01d2_史记正义提取方法.md) - 从《史记正义》提取特殊读音的方法论、工具、质量检查
- [SKILL_01d3_技术实现细节](./references/SKILL_01d3_技术实现细节.md) - 前端Ruby标注、性能优化、故障排除
- [SKILL_01d4_拼音标注质量规范v3.0](./references/SKILL_01d4_拼音标注质量规范v3.0.md) - 质量评估体系、设计哲学、优化路线图、数据统计（v3.0完整规范）
- [SKILL_01d5_多音字处理分析](./references/SKILL_01d5_多音字处理分析.md) - 63个多音字系统性调查、处理策略、版本演进（v2.7状态与路线图）
- [SKILL_01d6_拼音注释功能规范](./references/SKILL_01d6_拼音注释功能规范.md) - 拼音注释功能的前端实现规范、交互设计、技术细节

### 数据与索引

- [`doc/pronunciation/多音字完整索引.md`](../doc/pronunciation/多音字完整索引.md) - 156个多音字的统计分析
- [`doc/pronunciation/上下文分析工作流程说明.md`](../doc/pronunciation/上下文分析工作流程说明.md) - v4.0工作流程完整说明

### 相关Skill

- [SKILL_01a_文本标注与语义结构](./SKILL_01a_文本标注与语义结构.md)
- [SKILL_10f_Skill的提炼与转化](./SKILL_10f_Skill的提炼与转化.md)

---

## 更新日志

### v4.1 (2026-04-04)
- **完善**: 基于"王"字案例反思，完善7步检查清单
- **新增**: "称王"读音辨析（chēng wáng，非chēng wàng）
- **教训**: 必须查Wiktionary，不能主观判断

### v4.0 (2026-03-XX)
- **重构**: 建立基于上下文分析的工作流程
- **新增**: 提取上下文、生成模板、标注、测试的完整工具链
- **完成**: 6个高频多音字（燕、夫、和、且、遗、中、王、占、为、与、将）

### v3.12 (2026-04-04)
- **修正**: 删除"称王"词条（pinyin-pro正确）
- **保留**: 王天下、欲王（动词wàng）
- **词条数**: 120 → 119

### v3.10 (2026-04-04)
- **新增**: Lint机制，自动检查词条必要性
- **清理**: 删除129个冗余词条（pinyin-pro已正确处理）
- **优化**: 词表从231缩减至120词条

详细历史：参见 [SKILL_01d1_词表设计原则详解](./references/SKILL_01d1_词表设计原则详解.md) §版本演化
