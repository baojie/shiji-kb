# SPEC_繁简映射方案

> **⚠️ 本方案未实施 - 已废弃**
>
> **废弃原因**: 采用了更简单的 OpenCC + 词表方案替代
>
> **废弃日期**: 2026-04-05
>
> **保留目的**: 记录技术方案设计过程，供未来参考

---

**版本**: v1.0
**创建日期**: 2026-03-29
**原状态**: 待实施 → 已废弃

---

## 一、核心原则

1. **映射对象**：只映射繁简不同的字符
2. **映射基准**：以去除标注符号后的纯文本为基准
3. **定位策略**：基于上下文的相对定位（容错性强）
4. **版本控制**：映射文件支持版本历史和变更日志

---

## 二、映射文件格式

### 2.1 文件路径

`curation/mapping/NNN.json`

### 2.2 数据结构

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

### 2.3 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 映射条目唯一标识（格式：`章节号-序号`） |
| `context_before` | string | 目标字符前的上下文（1-3字） |
| `context_after` | string | 目标字符后的上下文（1-3字） |
| `s` | string | 简体字符 |
| `t` | string | 繁体字符 |
| `backup_pos` | int | 绝对位置（备份，用于快速定位） |
| `note` | string | 人工备注（可选） |

---

## 三、映射查找算法

### 3.1 算法实现

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

---

## 四、映射应用流程

### 4.1 场景A：简体标注 → 繁体渲染

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

---

## 五、映射更新流程

### 5.1 场景B：底本终稿修改后，更新映射

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

### 5.2 变更日志示例

`curation/mapping/001.changelog.md`:

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

---

## 六、映射失效处理

### 6.1 情况1：上下文仍可匹配（90%情况）

```
修改前: "其后裔封于"
修改后: "其后代裔封于"  # 在"后裔"之间插入"代"
```

**处理**：
- 上下文 `"其" + "后" + "裔封"` 仍然存在
- 映射自动更新位置 ✅

### 6.2 情况2：上下文部分匹配

```
修改前: "其后裔封于"
修改后: "其后世子孙封于"  # "裔"被替换为"世子孙"
```

**处理**：
- `context_before="其"` 和 `target_char="后"` 仍存在
- `context_after="裔封"` 变为 `"世子孙封"`
- **策略**：使用模糊匹配（只匹配before），标记为"需要人工确认"

### 6.3 情况3：映射字符被删除

```
修改前: "其后裔封于"
修改后: "封于"  # 删除了"其后裔"
```

**处理**：
- 上下文和目标字符都不存在
- **策略**：映射自动失效，从列表中移除

### 6.4 情况4：无法定位（需要人工介入）

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

## 七、工具脚本清单

### 7.1 繁简映射工具

```bash
scripts/mapping/
├── generate_mapping.py           # 从 simplified + traditional 生成 mapping
├── update_mapping.py             # 文本修改后更新 mapping
├── apply_mapping.py              # 将简体标注转换为繁体
├── validate_mapping.py           # 验证映射完整性
└── merge_mapping.py              # 合并多个版本的映射
```

### 7.2 使用示例

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

---

## 八、实施计划

### 8.1 阶段1：工具开发（3天）

- [ ] 开发 `generate_mapping.py`（繁简映射生成）
- [ ] 开发 `update_mapping.py`（映射更新）
- [ ] 开发 `apply_mapping.py`（映射应用）
- [ ] 开发 `validate_mapping.py`（映射验证）

### 8.2 阶段2：测试验证（2天）

- [ ] 在001-004章上测试完整流程
- [ ] 验证繁简映射准确性
- [ ] 测试映射失效处理机制

### 8.3 阶段3：批量处理（视情况而定）

- [ ] 生成全部130章繁简映射
- [ ] 验证映射完整性
- [ ] 更新相关文档

---

## 九、相关文档

- [SPEC_目录结构与工作流程](./SPEC_目录结构与工作流程.md)
- [SKILL_01_古籍校勘](../../skills/SKILL_01_古籍校勘.md)
- [SKILL_01b_多版本互校底本](../../skills/SKILL_01b_多版本互校底本.md)

---

**最后更新**: 2026-04-05
**维护者**: shiji-kb项目组
