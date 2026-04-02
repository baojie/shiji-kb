---
name: skill-10f4
title: 脚本分解示例
description: 大型脚本拆分为可复用小脚本的方法和实际案例。
---

# SKILL 10f4: 脚本分解示例

> 单一职责原则：一个脚本只做一件事，做好一件事。

---

## 一、何时需要脚本分解

**触发条件**（满足任一即需拆分）：

- [ ] 脚本超过300行
- [ ] 包含3个以上独立功能
- [ ] 有大量复制粘贴的代码
- [ ] 难以测试或调试
- [ ] 其他脚本也需要类似功能

---

## 二、脚本分解原则

### 2.1 单一职责

每个脚本只负责一个明确的功能：

| ✅ 好的脚本 | ❌ 不好的脚本 |
|-----------|------------|
| `pre_annotate_person.py` - 人名预标注 | `annotate_all.py` - 做所有标注 |
| `validate_format.py` - 格式验证 | `process_chapter.py` - 处理章节的所有事情 |
| `generate_report.py` - 生成报告 | `main.py` - 主脚本包含所有逻辑 |

### 2.2 可复用性

拆分后的脚本应该能被多个工作流复用：

```
scripts/annotation/pre_annotate_person.py
  ↑ 被以下工作流使用：
  - workflows/annotate_chapter.sh（完整标注流程）
  - workflows/quick_test.sh（快速测试流程）
  - CI/CD pipeline（自动化测试）
```

### 2.3 标准输入输出

每个脚本应该有清晰的输入输出：

```python
# 输入：命令行参数 + 文件
# 输出：修改后的文件 OR 报告

def main(input_file: str, output_file: str = None) -> int:
    """
    人名预标注

    Args:
        input_file: 原始.txt文件
        output_file: 输出.tagged.md文件（默认: input_file.tagged.md）

    Returns:
        0: 成功
        1: 失败
    """
    # ...
    return 0
```

---

## 三、拆分示例

### 示例1：大型标注脚本拆分

**原始脚本**（`annotate_all.py`, 800行）：

```python
def annotate_all(chapter):
    # 读取文件（100行）
    content = read_file(chapter)

    # 人名标注（200行）
    for line in content:
        if is_person_name(line):
            annotate_person(line)

    # 地名标注（150行）
    for line in content:
        if is_place_name(line):
            annotate_place(line)

    # 时间标注（120行）
    for line in content:
        if is_time_expr(line):
            annotate_time(line)

    # 格式验证（100行）
    errors = validate_format(content)
    if errors:
        print(f"发现 {len(errors)} 处错误")

    # 生成报告（130行）
    report = generate_report(content)
    save_report(report)
```

**问题诊断**：
- ❌ 单文件过长（800行）
- ❌ 职责不单一（5个独立功能）
- ❌ 难以复用（无法单独执行人名标注）
- ❌ 难以测试（必须测试整个流程）

**拆分后**：

```
scripts/annotation/
├── pre_annotate_person.py     # 200行：人名预标注
├── pre_annotate_place.py      # 150行：地名预标注
├── pre_annotate_time.py       # 120行：时间预标注
├── validation/
│   └── validate_format.py     # 100行：格式验证
└── generation/
    └── annotation_report.py   # 130行：报告生成

# 工作流脚本（orchestration）
scripts/workflows/
└── annotate_chapter.sh        # 30行：调用上述脚本
```

**拆分后的工作流脚本**：

```bash
#!/bin/bash
# scripts/workflows/annotate_chapter.sh

set -e  # 遇到错误立即退出

chapter=$1

echo "开始标注 $chapter..."

# 步骤1: 人名预标注
python scripts/annotation/pre_annotate_person.py "$chapter"

# 步骤2: 地名预标注
python scripts/annotation/pre_annotate_place.py "$chapter"

# 步骤3: 时间预标注
python scripts/annotation/pre_annotate_time.py "$chapter"

# 步骤4: 验证格式
python scripts/validation/validate_format.py "$chapter.tagged.md"

# 步骤5: 生成报告
python scripts/generation/annotation_report.py "$chapter.tagged.md"

echo "✅ 标注完成"
```

**优势**：
- ✅ 每个脚本职责单一（<200行）
- ✅ 可单独执行（快速测试人名标注）
- ✅ 可复用（其他工作流也能调用）
- ✅ 易于测试（单元测试每个脚本）
- ✅ 易于维护（修改人名标注逻辑只改一个文件）

---

### 示例2：大型验证脚本拆分

**原始脚本**（`validate_all.py`, 600行）：

```python
def validate_all(file):
    # 文本完整性检查（150行）
    check_text_integrity(file)

    # 标注符号检查（120行）
    check_annotation_syntax(file)

    # 嵌套标注检查（100行）
    check_nested_tags(file)

    # 实体类型检查（130行）
    check_entity_types(file)

    # 生成校验报告（100行）
    generate_validation_report(file)
```

**拆分后**：

```
scripts/validation/
├── lint_text_integrity.py         # 文本完整性
├── lint_annotation_syntax.py      # 标注语法
├── lint_nested_tags.py            # 嵌套标注
├── lint_entity_types.py           # 实体类型
└── generate_validation_report.py  # 校验报告

scripts/workflows/
└── validate_chapter.sh            # 调用所有验证脚本
```

**工作流脚本**：

```bash
#!/bin/bash
# scripts/workflows/validate_chapter.sh

file=$1
errors=0

echo "验证 $file..."

# 并行执行独立的检查
python scripts/validation/lint_text_integrity.py "$file" || errors=$((errors+1))
python scripts/validation/lint_annotation_syntax.py "$file" || errors=$((errors+1))
python scripts/validation/lint_nested_tags.py "$file" || errors=$((errors+1))
python scripts/validation/lint_entity_types.py "$file" || errors=$((errors+1))

if [ $errors -eq 0 ]; then
    echo "✅ 验证通过"
    python scripts/validation/generate_validation_report.py "$file"
else
    echo "❌ 发现 $errors 类错误"
    exit 1
fi
```

---

### 示例3：大型生成脚本拆分

**原始脚本**（`generate_all.py`, 700行）：

```python
def generate_all():
    # 生成实体索引（200行）
    generate_entity_index()

    # 生成关系图谱（180行）
    generate_relation_graph()

    # 生成统计报告（150行）
    generate_statistics()

    # 生成HTML页面（170行）
    generate_html_pages()
```

**拆分后**：

```
scripts/generation/
├── entity_index.py          # 实体索引
├── relation_graph.py        # 关系图谱
├── statistics_report.py     # 统计报告
└── html_renderer.py         # HTML渲染

scripts/workflows/
└── publish_website.sh       # 发布工作流
```

---

## 四、Skill中的引用方式

拆分后，在Skill中应该提供两种使用方式：

### 方式1：完整流程（推荐）

```markdown
## 工具与脚本

### 完整标注流程

```bash
# 一键执行完整标注流程
bash scripts/workflows/annotate_chapter.sh chapter_md/001_五帝本纪.txt
```

**输出**：
- `.tagged.md` - 标注后的文件
- `_report.json` - 标注报告
```

### 方式2：单步执行（调试/定制）

```markdown
### 单步执行

**步骤1：人名预标注**
```bash
python scripts/annotation/pre_annotate_person.py chapter_md/001_五帝本纪.txt
```

**步骤2：地名预标注**
```bash
python scripts/annotation/pre_annotate_place.py chapter_md/001_五帝本纪.txt
```

**步骤3：时间预标注**
```bash
python scripts/annotation/pre_annotate_time.py chapter_md/001_五帝本纪.txt
```

**步骤4：验证格式**
```bash
python scripts/validation/validate_format.py chapter_md/001_五帝本纪.tagged.md
```

**步骤5：生成报告**
```bash
python scripts/generation/annotation_report.py chapter_md/001_五帝本纪.tagged.md
```
```

---

## 五、脚本组织规范

### 目录结构

```
scripts/
├── annotation/          # 标注相关
│   ├── pre_annotate_person.py
│   ├── pre_annotate_place.py
│   └── pre_annotate_time.py
├── validation/          # 验证相关
│   ├── lint_text_integrity.py
│   ├── lint_nested_tags.py
│   └── validate_format.py
├── generation/          # 生成相关
│   ├── entity_index.py
│   ├── statistics_report.py
│   └── html_renderer.py
├── conversion/          # 转换相关
│   ├── txt_to_md.py
│   └── md_to_html.py
└── workflows/           # 工作流编排
    ├── annotate_chapter.sh
    ├── validate_chapter.sh
    └── publish_website.sh
```

### 命名规范

| 类型 | 命名格式 | 示例 |
|-----|---------|------|
| 标注脚本 | `pre_annotate_{type}.py` | `pre_annotate_person.py` |
| 验证脚本 | `lint_{aspect}.py` | `lint_text_integrity.py` |
| 生成脚本 | `generate_{output}.py` | `generate_entity_index.py` |
| 转换脚本 | `{from}_to_{to}.py` | `txt_to_md.py` |
| 工作流 | `{action}_{object}.sh` | `annotate_chapter.sh` |

---

## 六、脚本分解检查清单

### 执行前

- [ ] 原脚本超过300行
- [ ] 包含3个以上独立功能
- [ ] 有明确的拆分边界

### 执行中

- [ ] 每个拆分脚本<200行
- [ ] 每个脚本有清晰的docstring
- [ ] 每个脚本有 `--help` 选项
- [ ] 创建工作流脚本串联所有步骤

### 执行后

- [ ] 工作流脚本可正常运行
- [ ] 单个脚本可独立测试
- [ ] 在Skill中更新脚本引用
- [ ] 删除或归档原始大脚本

---

## 相关文档

- 主文档：[SKILL_10f_Skill的提炼与转化.md](../SKILL_10f_Skill的提炼与转化.md)
- 模板库：[SKILL_10f1_模板库.md](./SKILL_10f1_模板库.md)
- 精简拆分：[SKILL_10f2_精简拆分案例库.md](./SKILL_10f2_精简拆分案例库.md)
- 更新维护：[SKILL_10f3_更新维护指南.md](./SKILL_10f3_更新维护指南.md)
