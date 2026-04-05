# 标注符号系统级迁移 (Reference for SKILL_03a)

> 本文档记录标注符号迁移的实战方法论，参考自邦国符号迁移案例（2026-04）

---

## 迁移场景

**何时需要符号迁移**：
1. **符号冲突**：旧符号与Markdown/标点符号冲突（如`*`与斜体语法）
2. **Disjoint原则违反**：旧符号使用了标点符号（如`〖'`使用U+0027半角单引号）
3. **系统重构**：标注体系升级（如5类→18类实体扩展）
4. **可读性提升**：使用更直观的符号（如`〖◆`比`〖'`语义更明确）

---

## 通用迁移流程

### 阶段1：规划与准备
1. **明确迁移动机**（记录为什么要迁移，便于后续审查）
2. **选择新符号**（符合Disjoint原则，参考SKILL_01g）
3. **估算影响范围**：
   ```bash
   grep -r "旧符号" --include="*.md" --include="*.json" --include="*.py" | wc -l
   ```
4. **编写迁移脚本**（使用下方的标准模板）

### 阶段2：分批执行（4批次）
1. **核心标注文件** (`chapter_md/*.tagged.md`) - 最重要，优先处理
2. **文档和规范** (`README.md`, `SKILL_*.md`) - 用户文档同步
3. **派生数据文件** (JSON, logs/) - 容易遗漏
4. **渲染脚本和代码** (`.py`, `.js`) - 最后更新

**每批次必做**：
- 运行验证脚本（lint_text_integrity.py）
- 提交Git（独立commit，便于回滚）
- 记录统计数据（文件数、替换次数）

### 阶段3：验证与收尾
1. **全局残留检查**（确保无遗漏）
2. **渲染功能测试**（至少3个章节）
3. **更新项目文档**（SKILL、CHANGELOG等）

---

## 迁移案例：邦国符号 `〖'` → `〖◆`

**迁移动机**：旧符号 `〖'` 使用半角单引号(U+0027)，违反"标点/标注/Markdown三大符号集合完全分离"原则（SKILL_01g § Disjoint原则）。

**迁移规模**：
- 174个活跃文件，21,462+处符号替换
- 4次Git提交完成（核心标注 → 文档规范 → 派生数据 → 渲染脚本）

---

## 迁移步骤（4批次）

### 1. 核心标注文件 (commit 70cc1ee4)

**命令**：
```bash
python scripts/migrate_country_symbol.py chapter_md/*.tagged.md
```

**结果**：128 files, 12,505 replacements

**验证**：
```bash
find chapter_md -name "*.tagged.md" -exec grep -l "〖'" {} \; | wc -l  # 应为0
```

### 2. 文档和规范 (commit 3ee3e6e9)

**更新文件**：
- `skills/SKILL_03a_实体标注.md` - 所有示例
- `README.md` - 标注语法表
- 脚本注释和正则表达式

**结果**：31 files

### 3. 派生数据JSON (commit 88c082b3)

**方法**：
```python
from pathlib import Path
import json

old_marker = '〖' + chr(0x0027)  # 〖'
new_marker = '〖' + chr(0x25C6)  # 〖◆

for file_path in json_files:
    content = Path(file_path).read_text(encoding='utf-8')
    new_content = content.replace(old_marker, new_marker)
    json.loads(new_content)  # 验证JSON格式
    Path(file_path).write_text(new_content, encoding='utf-8')
```

**结果**：11 files (chengyu.json, reflection reports等), 8,059 replacements

### 4. 渲染脚本和实验文档 (commit a8f11702)

**更新内容**：
- `render_shiji_html.py` - 正则表达式（第64-65行）
- 文件头部注释 - 标注语法表
- 删除过时的兼容代码

**结果**：6 files

---

## 验证方法

### 1. 文本完整性检查
```bash
python scripts/lint_text_integrity.py
```
确保标注符号替换不改变原文字符。

### 2. 渲染功能测试
```bash
python render_shiji_html.py chapter_md/004_周本纪.tagged.md /tmp/test.html
grep -c '〖◆' /tmp/test.html  # 应为0（全部转换为HTML）
grep 'feudal-state' /tmp/test.html  # 检查HTML输出正确
```

### 3. 全局残留检查
```bash
find . -type f ! -path "*/backups/*" ! -path "*/.git/*" -exec grep -l "〖'" {} \;
```

---

## 关键经验

### 成功要素
1. ✅ **分批提交**：每批独立验证，问题隔离，易于回滚
2. ✅ **完整性验证**：lint检查确保标注符号替换不改变原文字符
3. ✅ **文档同步**：技术文档、用户文档、代码注释同步更新
4. ✅ **Git提交顺序**：核心数据 → 文档 → 派生数据 → 代码（依赖关系从强到弱）

### 风险点与应对
1. ⚠️  **工具陷阱**：Edit工具可能自动转换全角/半角符号
   - **应对**：优先使用Python脚本批量替换，避免Edit工具处理包含引号的内容

2. ⚠️  **派生数据遗漏**：JSON、日志、HTML等派生文件容易被忽略
   - **应对**：使用 `grep -r "旧符号"` 全局扫描，分类处理

3. ⚠️  **文本完整性破坏**：符号替换可能误改原文
   - **应对**：每次批量替换后运行 `lint_text_integrity.py`

4. ⚠️  **渲染功能回归**：符号更新可能导致HTML渲染失败
   - **应对**：迁移后必须测试至少3个章节的HTML生成

5. ⚠️  **实体索引构建脚本遗漏**：`kg/entities/scripts/build_entity_index.py` 中的正则模式容易被忽略
   - **现象**：迁移后邦国实体从索引页面中消失（2026-04-05发现）
   - **检查点**：
     - `ENTITY_TYPES` 列表中的正则表达式（第49行）
     - `ENTITY_DESCRIPTIONS` 字典中的标记符号说明（第424行）
   - **应对**：迁移后必须运行 `python kg/entities/scripts/build_entity_index.py` 并检查索引页面

6. ⚠️  **词表文件遗漏**：`kg/vocabularies/*.md` 中嵌入了大量实体标注示例
   - **现象**：词表中包含27,972处旧符号（2026-04-05发现）
   - **影响范围**：18个词表文件 + README.md
   - **应对**：编写专门脚本批量处理词表文件（参考 `scripts/fix_vocabularies_feudal_symbol.py`）

---

## 迁移脚本标准模板

```python
#!/usr/bin/env python3
"""标注符号迁移脚本模板"""
import sys
from pathlib import Path

def migrate_symbol(file_path: Path, old_marker: str, new_marker: str) -> int:
    """替换单个文件中的标注符号

    Args:
        file_path: 文件路径
        old_marker: 旧符号（如 '〖' + chr(0x0027)）
        new_marker: 新符号（如 '〖' + chr(0x25C6)）

    Returns:
        替换次数
    """
    content = file_path.read_text(encoding='utf-8')

    # 统计替换次数
    count = content.count(old_marker)
    if count == 0:
        return 0

    # 执行替换
    new_content = content.replace(old_marker, new_marker)

    # 写回文件
    file_path.write_text(new_content, encoding='utf-8')

    return count

if __name__ == '__main__':
    # 定义符号（使用Unicode码点避免编辑器自动转换）
    old_marker = '〖' + chr(0x0027)  # 旧符号
    new_marker = '〖' + chr(0x25C6)  # 新符号

    # 处理所有输入文件
    total_count = 0
    for file_path in sys.argv[1:]:
        path = Path(file_path)
        count = migrate_symbol(path, old_marker, new_marker)
        if count > 0:
            print(f"✓ {path.name}: {count}处替换")
            total_count += count

    print(f"\n总计: {total_count}处替换")
```

**使用示例**：
```bash
python scripts/migrate_symbol.py chapter_md/*.tagged.md
```

---

## 检查清单模板

### 文件修改清单
- [ ] 核心标注文件 (`chapter_md/*.tagged.md`)
- [ ] 文档和规范 (`SKILL_03a`, `README`等)
- [ ] 派生数据文件 (JSON, `logs/`)
- [ ] 渲染脚本 (`render_shiji_html.py`等)
- [ ] 实体索引构建脚本 (`kg/entities/scripts/build_entity_index.py`)
- [ ] 词表文件 (`kg/vocabularies/*.md`)

### 验证清单
- [ ] 文本完整性验证 (`lint_text_integrity.py`)
- [ ] 重新构建实体索引 (`python kg/entities/scripts/build_entity_index.py`)
- [ ] 检查实体索引页面 (`docs/entities/index.html` 和各类型索引页)
- [ ] 渲染功能测试 (生成HTML验证，至少3个章节)
- [ ] 全局残留检查 (`find + grep`)

---

## 更新历史

- **2026-04-05**：初版，基于邦国符号迁移实战（4个commit，174 files，21,462+ replacements）
- **2026-04-05**：补充风险点5和6（实体索引构建脚本和词表文件遗漏），新增验证清单
