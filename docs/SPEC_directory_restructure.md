# SPEC: 目录重构和繁简映射方案

**版本**: v1.0
**创建日期**: 2026-03-29
**状态**: 待实施

---

## 一、目录结构规范

### 1.1 总体结构

```
shiji-kb/
├── archive/                              # 所有原始和历史数据
│   ├── sources/                          # 所有底本的不同版本（用于校勘）
│   ├── references/                       # 知识参考资料（不直接用于校勘）
│   └── legacy/                           # 历史版本归档
│
├── curation/                            # 校勘工作区（SKILL_01b 产出）
│   ├── simplified/                       # 校勘本-简体（标准底本）
│   ├── traditional/                      # 校勘本-繁体（平行版本）
│   ├── mapping/                          # 繁简字级映射文件
│   └── reports/                          # 校对报告
│
├── final/                                # 底本终稿（所有改进后的最终版本）
│   ├── simplified/                       # 简体终稿（用于语义分析）
│   ├── traditional/                      # 繁体终稿（用于阅读增强）
│   └── improvements/                     # 改进日志
│
└── chapters/                             # 后续分析（基于 final/）
    ├── *.tagged.md                       # 实体标注
    └── ...
```

### 1.2 详细说明

#### archive/sources/ （底本来源，用于校勘）

```
archive/sources/
├── chapter/                      # 简体分章版（主要底本）
│   ├── 001_五帝本纪.txt
│   └── ...
├── wikisource/                   # 维基文库繁体HTML版
│   ├── 001_五帝本纪.html
│   └── ...
├── siku.txt                      # 四库全书版（整本）
├── traditional.txt               # 繁体纯文本版（整本）
└── sanjia/                       # 维基三家注版
    ├── 001_五帝本纪.html
    └── ...
```

**用途**：SKILL_01b 多版本互校的输入材料

#### archive/references/ （参考资料，不直接用于校勘）

```
archive/references/
├── annotations.txt               # 注释合本
├── maps/                         # 历史地图
├── chronology/                   # 年表
└── research/                     # 考据资料
```

**用途**：知识增强、背景研究，但不参与底本校勘

#### archive/legacy/ （历史版本归档）

```
archive/legacy/
├── chapter_v1/                   # 迁移前的旧底本
├── wikisource_shiji/             # 旧的wikisource目录（改名前）
└── ...
```

**用途**：保留历史版本，便于回溯

#### curation/ （校勘工作区）

```
curation/
├── simplified/                   # 校勘本-简体
│   ├── 001_五帝本纪.txt
│   └── ...
├── traditional/                  # 校勘本-繁体（字级映射）
│   ├── 001_五帝本纪.txt
│   └── ...
├── mapping/                      # 繁简字级映射文件
│   ├── 001.json
│   ├── 001.v1.json               # 历史版本
│   ├── 001.changelog.md          # 映射变更日志
│   └── ...
└── reports/                      # 校对报告
    ├── 001_五帝本纪.md
    └── ...
```

**用途**：SKILL_01b 的输出结果

#### final/ （底本终稿）

```
final/
├── simplified/                   # 简体终稿
│   ├── 001_五帝本纪.txt
│   └── ...
├── traditional/                  # 繁体终稿
│   ├── 001_五帝本纪.txt
│   └── ...
└── improvements/                 # 改进日志
    ├── punctuation.md            # 标点归一化日志
    ├── paragraphs.md             # 段落整合日志
    └── normalization.md          # 其他规范化日志
```

**用途**：后续所有分析的基准文本

#### chapters/ （语义分析）

```
chapters/
├── 001_五帝本纪.tagged.md        # 实体标注
├── 002_夏本纪.tagged.md
└── ...
```

**用途**：基于 `final/simplified/` 进行的语义标注

---

## 二、工作流程

```
【阶段0：准备】
当前目录结构 → 迁移到新结构 → archive/sources/ + archive/legacy/

【阶段1：多版本互校】SKILL_01b
archive/sources/*
  → 对比校勘
  → curation/simplified/ + curation/traditional/
  → 生成 curation/mapping/ + curation/reports/

【阶段2：底本改进】SKILL_01c（新增）
curation/simplified/ + curation/traditional/
  → 标点归一化
  → 段落整合修复
  → 其他文本规范化
  → final/simplified/ + final/traditional/
  → 更新 curation/mapping/ （基于文本变化）

【阶段3：语义分析】SKILL_03a等
final/simplified/
  → 实体标注
  → chapters/*.tagged.md

【阶段4：繁体渲染】（未来）
chapters/*.tagged.md + curation/mapping/
  → 应用繁简映射
  → chapters/*.traditional.tagged.md 或 HTML
```

---

## 三、底本改进规范

### 3.1 标点归一化

**规则**：原文只使用全角标点

| 类型 | 允许 | 禁止 |
|------|------|------|
| 逗号 | ，（U+FF0C） | ,（U+002C） |
| 句号 | 。（U+3002） | .（U+002E） |
| 分号 | ；（U+FF1B） | ;（U+003B） |
| 冒号 | ：（U+FF1A） | :（U+003A） |
| 问号 | ？（U+FF1F） | ?（U+003F） |
| 感叹号 | ！（U+FF01） | !（U+0021） |
| 左双引号 | "（U+201C） | "（U+0022） |
| 右双引号 | "（U+201D） | "（U+0022） |
| 左单引号 | '（U+2018） | '（U+0027） |
| 右单引号 | '（U+2019） | '（U+0027） |

**操作**：
- 扫描 `curation/simplified/` 和 `curation/traditional/`
- 将所有半角标点转换为对应的全角标点
- 记录到 `final/improvements/punctuation.md`

### 3.2 段落整合

**规则**：
1. **修复错误换行**：句子中间不应有换行符
2. **合并断句错误**：错误断开的句子应合并

**示例**：
```
错误：
黄帝者，少典之子，姓公孙
，名曰轩辕。

正确：
黄帝者，少典之子，姓公孙，名曰轩辕。
```

**操作**：
- 人工审核或规则检测
- 记录到 `final/improvements/paragraphs.md`

### 3.3 其他规范化

| 项目 | 规则 | 说明 |
|------|------|------|
| 空格/制表符 | 删除所有空格和制表符 | 古文不使用空格 |
| 换行符 | 统一使用LF（\n） | 禁止CRLF（\r\n） |
| BOM标记 | 删除BOM（U+FEFF） | UTF-8不需要BOM |
| 文件编码 | UTF-8 without BOM | 统一编码 |

**操作**：
- 自动化脚本处理
- 记录到 `final/improvements/normalization.md`

---

## 四、繁简映射方案

### 4.1 核心原则

1. **映射对象**：只映射繁简不同的字符
2. **映射基准**：以去除标注符号后的纯文本为基准
3. **定位策略**：基于上下文的相对定位（容错性强）
4. **版本控制**：映射文件支持版本历史和变更日志

### 4.2 映射文件格式

**文件路径**：`curation/mapping/NNN.json`

```json
{
  "chapter_id": "001",
  "chapter_name": "五帝本纪",
  "version": "2.0",
  "created": "2026-03-29T10:00:00Z",
  "updated": "2026-03-29T14:30:00Z",
  "base_checksum": "sha256_hash_of_simplified",
  "trad_checksum": "sha256_hash_of_traditional",
  "char_diff": [
    {
      "id": "001-001",
      "context_before": "其",
      "context_after": "裔封",
      "s": "后",
      "t": "後",
      "backup_pos": 27,
      "note": "时间义的'後'，非方位义的'后'"
    },
    {
      "id": "001-002",
      "context_before": "季",
      "context_after": "立为",
      "s": "历",
      "t": "歷",
      "backup_pos": 127,
      "note": "人名'季歷'"
    }
  ]
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 映射条目唯一标识（格式：`章节号-序号`） |
| `context_before` | string | 目标字符前的上下文（1-3字） |
| `context_after` | string | 目标字符后的上下文（1-3字） |
| `s` | string | 简体字符 |
| `t` | string | 繁体字符 |
| `backup_pos` | int | 绝对位置（备份，用于快速定位） |
| `note` | string | 人工备注（可选） |

### 4.3 映射查找算法

```python
def find_char_position(text: str, mapping_entry: dict) -> int:
    """
    基于上下文查找字符位置

    返回：字符在text中的绝对位置
    抛出：MappingNotFoundError 如果无法定位
    """
    context_before = mapping_entry['context_before']
    context_after = mapping_entry['context_after']
    target_char = mapping_entry['s']  # 或 't'，取决于方向
    backup_pos = mapping_entry['backup_pos']

    # 构造完整上下文
    full_context = context_before + target_char + context_after

    # 策略1：快速路径 - 检查backup_pos是否仍然有效
    if 0 <= backup_pos < len(text):
        start = max(0, backup_pos - len(context_before))
        end = min(len(text), backup_pos + 1 + len(context_after))
        if text[start:end] == full_context:
            return backup_pos

    # 策略2：精确匹配 - 在全文中查找完整上下文
    pos = text.find(full_context)
    if pos != -1:
        return pos + len(context_before)

    # 策略3：模糊匹配 - 只匹配before或after
    # （用于上下文部分被修改的情况）
    pattern_before = context_before + target_char
    pattern_after = target_char + context_after

    for i in range(len(text) - len(pattern_before) + 1):
        if text[i:i+len(pattern_before)] == pattern_before:
            # 验证after部分（允许部分匹配）
            if i + len(pattern_before) <= len(text):
                return i + len(context_before)

    # 策略4：失败 - 需要人工介入
    raise MappingNotFoundError(
        f"无法定位字符 '{target_char}' "
        f"(context: '{full_context}', backup_pos: {backup_pos})"
    )
```

### 4.4 映射应用流程

#### 场景A：简体标注 → 繁体渲染

```python
# 输入：chapters/001_五帝本纪.tagged.md（简体标注）
# 输出：繁体HTML或繁体标注文件

def apply_simplified_to_traditional(
    tagged_md_path: str,
    mapping_json_path: str
) -> str:
    """
    将简体标注文件转换为繁体
    """
    # 1. 读取标注文件
    tagged_text = read_file(tagged_md_path)

    # 2. 提取标注信息和纯文本
    annotations, plain_text = extract_annotations(tagged_text)
    # plain_text: "黄帝者，少典之子...其后裔..."
    # annotations: [
    #   {"start": 0, "end": 2, "type": "PER", "text": "黄帝"},
    #   ...
    # ]

    # 3. 读取繁简映射
    mapping = read_json(mapping_json_path)

    # 4. 对纯文本应用繁简映射
    trad_text = plain_text
    for entry in reversed(mapping['char_diff']):  # 从后往前，避免位置偏移
        pos = find_char_position(plain_text, entry)
        trad_text = trad_text[:pos] + entry['t'] + trad_text[pos+1:]

    # 5. 重新插入标注标记（位置不变，因为是字符级替换）
    tagged_trad_text = rebuild_annotations(trad_text, annotations)

    return tagged_trad_text
```

### 4.5 映射更新流程

#### 场景B：底本终稿修改后，更新映射

```bash
# 1. 用户修改 final/simplified/001_五帝本纪.txt 和 final/traditional/001_五帝本纪.txt
vim final/simplified/001_五帝本纪.txt

# 2. 运行映射更新工具
python scripts/mapping/update_mapping.py 001

# 输出：
# ✓ 扫描 final/simplified/001_五帝本纪.txt
# ✓ 扫描 final/traditional/001_五帝本纪.txt
# ⚠ 检测到文本变更（checksum不匹配）
# ✓ 尝试匹配旧映射（基于上下文）
#   - 001-001 "其后裔" → 找到，位置从27变为29（前面插入了2字）
#   - 001-002 "季历立" → 找到，位置不变
# ✓ 生成新映射 curation/mapping/001.json
# ✓ 备份旧映射 curation/mapping/001.v1.json
# ✓ 更新变更日志 curation/mapping/001.changelog.md
```

**变更日志示例** (`curation/mapping/001.changelog.md`):

```markdown
# 001_五帝本纪 映射变更日志

## v2 (2026-03-29 14:30)

**变更原因**: 修复底本错误，"黄帝"前插入"轩辕"二字

**影响的映射**:
- `001-001`: backup_pos 27 → 29（位置偏移+2）
- `001-002`: 无变化

**校验和**:
- simplified: `sha256_old` → `sha256_new`
- traditional: `sha256_old` → `sha256_new`

## v1 (2026-03-28 10:00)

**初始版本**: 从 curation/simplified + curation/traditional 生成
```

### 4.6 映射失效处理

#### 情况1：上下文仍可匹配（90%情况）

```
修改前: "其后裔封于"
修改后: "其后代裔封于"  # 在"后裔"之间插入"代"
```

**处理**：
- 上下文 `"其" + "后" + "裔封"` 仍然存在
- 映射自动更新位置 ✅

#### 情况2：上下文部分匹配

```
修改前: "其后裔封于"
修改后: "其后世子孙封于"  # "裔"被替换为"世子孙"
```

**处理**：
- `context_before="其"` 和 `target_char="后"` 仍存在
- `context_after="裔封"` 变为 `"世子孙封"`
- **策略**：使用模糊匹配（只匹配before），标记为"需要人工确认"

#### 情况3：映射字符被删除

```
修改前: "其后裔封于"
修改后: "封于"  # 删除了"其后裔"
```

**处理**：
- 上下文和目标字符都不存在
- **策略**：映射自动失效，从列表中移除

#### 情况4：无法定位（需要人工介入）

```
修改前: "其后裔封于邾"
修改后: "其子孙封于邾"  # "后裔"整体被替换
```

**处理**：
- 抛出 `MappingNotFoundError`
- 工具提示需要人工审核
- 用户选择：
  1. 手动更新映射条目的上下文
  2. 删除该映射（如果繁体也做了相同修改）
  3. 重新生成映射（全自动扫描）

---

## 五、工具脚本清单

### 5.1 目录迁移工具

```bash
scripts/migration/
├── migrate_to_new_structure.py   # 一键迁移到新目录结构
└── validate_migration.py         # 验证迁移完整性
```

**功能**：
- 将当前 `archive/chapter/` 迁移到 `archive/sources/chapter/`
- 将当前 `curation_base/` 迁移到 `curation/simplified/`
- 将当前 `logs/curation/reports/` 迁移到 `curation/reports/`
- 备份旧目录到 `archive/legacy/`

### 5.2 繁简映射工具

```bash
scripts/mapping/
├── generate_mapping.py           # 从 simplified + traditional 生成 mapping
├── update_mapping.py             # 文本修改后更新 mapping
├── apply_mapping.py              # 将简体标注转换为繁体
├── validate_mapping.py           # 验证映射完整性
└── merge_mapping.py              # 合并多个版本的映射
```

**generate_mapping.py**:
```bash
# 为指定章节生成初始映射
python scripts/mapping/generate_mapping.py 001 002 003

# 为所有章节生成映射
python scripts/mapping/generate_mapping.py --all
```

**update_mapping.py**:
```bash
# 检测文本变化并更新映射
python scripts/mapping/update_mapping.py 001

# 强制重新生成（忽略旧映射）
python scripts/mapping/update_mapping.py 001 --force
```

**apply_mapping.py**:
```bash
# 将简体标注文件转换为繁体
python scripts/mapping/apply_mapping.py \
  --input chapters/001_五帝本纪.tagged.md \
  --output chapters/001_五帝本纪.traditional.tagged.md \
  --mapping curation/mapping/001.json
```

### 5.3 底本改进工具

```bash
scripts/improvements/
├── normalize_punctuation.py      # 标点归一化
├── fix_paragraphs.py             # 段落整合
└── normalize_text.py             # 其他规范化（空格、换行符、BOM）
```

**使用流程**：
```bash
# 从 curation/simplified 生成 final/simplified
python scripts/improvements/normalize_punctuation.py --input curation/simplified --output final/simplified
python scripts/improvements/fix_paragraphs.py --input final/simplified --output final/simplified
python scripts/improvements/normalize_text.py --input final/simplified --output final/simplified

# 同步处理繁体版本
python scripts/improvements/normalize_punctuation.py --input curation/traditional --output final/traditional
python scripts/improvements/fix_paragraphs.py --input final/traditional --output final/traditional
python scripts/improvements/normalize_text.py --input final/traditional --output final/traditional

# 更新映射（因为文本已改变）
python scripts/mapping/update_mapping.py --all
```

---

## 六、实施计划

### 阶段1：准备阶段（1天）

- [ ] 创建新目录结构
- [ ] 开发 `migrate_to_new_structure.py`
- [ ] 执行迁移并验证

### 阶段2：工具开发（3天）

- [ ] 开发 `generate_mapping.py`（繁简映射生成）
- [ ] 开发 `update_mapping.py`（映射更新）
- [ ] 开发 `apply_mapping.py`（映射应用）
- [ ] 开发 `normalize_punctuation.py`（标点归一化）
- [ ] 开发 `fix_paragraphs.py`（段落整合）
- [ ] 开发 `normalize_text.py`（文本规范化）

### 阶段3：测试验证（2天）

- [ ] 在001-004章上测试完整流程
- [ ] 验证繁简映射准确性
- [ ] 验证底本改进质量

### 阶段4：批量处理（视情况而定）

- [ ] 对全部130章执行底本改进
- [ ] 生成全部繁简映射
- [ ] 更新所有相关文档

---

## 七、注意事项

### 7.1 兼容性

- **向后兼容**：旧的 `chapter_md/*.tagged.md` 需要基于新的 `final/simplified/` 重新验证
- **工具更新**：所有引用旧路径的脚本需要更新

### 7.2 质量控制

- **人工审核**：底本改进（尤其是段落整合）需要人工抽检
- **映射验证**：每次映射更新后需要运行 `validate_mapping.py`

### 7.3 备份策略

- **迁移前备份**：执行迁移前完整备份当前目录
- **映射版本**：每次映射更新保留历史版本

---

## 八、相关文档

- [SKILL_01_古籍校勘](../skills/SKILL_01_古籍校勘.md)
- [SKILL_01b_多版本互校底本](../skills/SKILL_01b_多版本互校底本.md)
- [SKILL_01c_底本改进规范](../skills/SKILL_01c_底本改进规范.md)（待创建）

---

**最后更新**: 2026-03-29
**维护者**: shiji-kb项目组
