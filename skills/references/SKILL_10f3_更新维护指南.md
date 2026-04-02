---
name: skill-10f3
title: Skill更新维护指南
description: Skill文档的更新触发条件、标准流程、验证方法和实际案例。
---

# SKILL 10f3: Skill更新维护指南

> 系统化的Skill维护流程，确保文档始终与实际状态同步。

---

## 一、何时需要更新Skill

**触发条件**（满足任一即需更新）：

- [ ] **数据规模变化**：实体数量、章节覆盖率等统计数据有显著变化（>10%）
- [ ] **文件路径变更**：引用的文件/目录被重命名或移动
- [ ] **脚本逻辑更新**：关联脚本的输入输出格式发生变化
- [ ] **工具链升级**：新增或替换了关键工具
- [ ] **过时内容**：文档中提到的版本号、日期、状态描述不符合当前实际
- [ ] **用户反馈**：有明确的错误报告或改进建议

---

## 二、更新流程（标准化）

### 步骤1：触发更新

```bash
# 场景：文件重命名触发更新需求
git mv skills/SKILL_03b_实体消歧.md skills/SKILL_03b_人名消歧.md
# → 需要更新所有引用此文件的地方
```

### 步骤2：全面检查需要更新的内容

使用系统化的检查清单：

**2.1 统计数据检查**
```bash
# 检查Skill中的数字是否过时
grep -n "条\|个\|章\|组" skills/SKILL_XX.md | head -20

# 验证实际数据
python3 << 'EOF'
import json
# 读取实际数据文件，统计当前数字
with open('kg/entities/data/entity_index.json') as f:
    data = json.load(f)
    person_count = len(data.get('person', {}))
    total_count = sum(len(v) for v in data.values() if isinstance(v, dict))
    print(f"人名实体数: {person_count}")
    print(f"全部实体数: {total_count}")
EOF
```

**2.2 文件路径检查**
```bash
# 检查Skill中引用的所有文件路径
grep -n "\.md\|\.json\|\.py\|\.csv" skills/SKILL_XX.md

# 验证路径是否存在
for path in $(grep -o "[a-z/]*/[a-zA-Z_]*.md" skills/SKILL_XX.md); do
    [ -f "$path" ] || echo "Missing: $path"
done
```

**2.3 脚本逻辑检查**
```bash
# 检查Skill中提到的脚本
grep -n "scripts/" skills/SKILL_XX.md

# 验证脚本的docstring与Skill描述一致
head -20 scripts/xxx/yyy.py
```

**2.4 索引文件检查**
```bash
# 检查是否需要更新索引文件
grep "SKILL_XX" skills/INDEX.md
grep "SKILL_XX" skills/SKILL_00_管线总览.md
grep "SKILL_XX" skills/SKILL_YY_相关技能.md
```

**2.5 引用脚本检查**
```bash
# 检查哪些脚本引用了这个Skill
grep -r "SKILL_XX" scripts/
```

### 步骤3：批量更新

**3.1 更新统计数据**

示例（基于SKILL_03b的实际更新）：

```markdown
<!-- 更新前 -->
人名实体数 | 3,797条
全部实体数 | （未记录）
别名组 | 586组
君主数据 | 651条

<!-- 更新后 -->
人名实体数 | 4,418条 (+621, +16.4%)
全部实体数 | 17,483条（19类）
别名关系数 | 591条（11个分类）
君主数据 | 656条 (+5)
```

**关键点**：
- ✅ 使用实际脚本统计，不手动猜测
- ✅ 更新所有相关数字（摘要、章节、表格）
- ✅ 保持数字格式一致（千位分隔符、单位）

**3.2 更新文件路径**

```bash
# 批量替换文件名引用
sed -i 's/SKILL_03b_实体消歧.md/SKILL_03b_人名消歧.md/g' \
    skills/INDEX.md \
    skills/SKILL_00_管线总览.md \
    skills/SKILL_03_实体构建.md

# 更新子目录引用
# 错误: doc/entities/史记君主列表整理过程.md
# 正确: doc/entities/特殊任务/史记君主列表整理过程.md
```

**3.3 更新脚本引用**

检查脚本中硬编码的Skill名称：

```python
# scripts/update_skill_frontmatter.py
DESCRIPTIONS = {
    "SKILL_03b_实体消歧.md": "...",  # ← 需要更新为 SKILL_03b_人名消歧.md
}
```

**3.4 更新版本说明**

在Skill末尾更新变更日志：

```markdown
*最后更新：2026-04-02*
*v1.3 更新内容：*
- 统计数据：人名实体 3,797 → 4,418条，全部实体新增统计（17,483条）
- 君主数据：651 → 656条
- 文件路径：修正 doc/entities/ 子目录结构
- 文件重命名：实体消歧 → 人名消歧
```

### 步骤4：验证完整性

**4.1 链接验证**
```bash
# 检查所有Markdown链接是否有效
for link in $(grep -o "\[.*\](.*\.md)" skills/SKILL_XX.md | sed 's/.*(\(.*\))/\1/'); do
    [ -f "skills/$link" ] || [ -f "$link" ] || echo "Broken: $link"
done
```

**4.2 数字一致性验证**
```bash
# 检查同一数字在不同位置是否一致
# 例如："4418" 应该在摘要、表格、描述中出现多次
grep -n "4418\|4,418" skills/SKILL_XX.md
# 确保所有出现都已更新
```

**4.3 格式一致性**
```bash
# 检查格式规范
# - 千位分隔符：4,418 vs 4418
# - 单位统一：条/个/章
# - 日期格式：YYYY-MM-DD
```

---

## 三、更新检查清单

### 执行前

- [ ] 确认更新触发条件（数据变化/路径变更/脚本升级）
- [ ] 备份原文件（`cp SKILL_XX.md SKILL_XX.md.backup`）
- [ ] 读取实际数据文件，获取准确统计

### 执行中

- [ ] 更新所有统计数字（摘要、章节、表格）
- [ ] 更新所有文件路径（绝对路径、相对路径、子目录）
- [ ] 更新所有索引文件引用（INDEX.md、管线总览、相关Skill）
- [ ] 更新脚本中的硬编码引用
- [ ] 更新版本说明和日期

### 执行后

- [ ] 验证所有Markdown链接有效
- [ ] 验证数字在多处出现的一致性
- [ ] 验证格式统一（千位分隔符、单位、日期）
- [ ] 运行 `git diff` 检查改动范围
- [ ] 暂存所有相关文件

---

## 四、实际案例：SKILL_03b人名消歧

**背景**：文件重命名 + 数据规模增长

**触发条件**：
1. 文件重命名：`SKILL_03b_实体消歧.md` → `SKILL_03b_人名消歧.md`
2. 统计数据过时：人名实体数从3,797增长到4,418

**执行过程**：

```bash
# 1. 重命名文件
git mv skills/SKILL_03b_实体消歧.md skills/SKILL_03b_人名消歧.md

# 2. 获取实际统计数据
python3 << 'EOF'
import json
with open('kg/entities/data/entity_index.json') as f:
    index = json.load(f)
    person = len(index.get('person', {}))
    total = sum(len(v) for v in index.values() if isinstance(v, dict))
    print(f"人名: {person}, 总计: {total}")
# 输出: 人名: 4418, 总计: 17483
EOF

# 3. 批量更新Skill内容
# - 第9行：摘要中的人名数（3,797 → 4,418）
# - 第26行：数据规模描述（新增全部实体统计）
# - 第447行：别名组数（586 → 591）
# - 第449-450行：实体统计表格
# - 第524行：entity_index.json说明
# - 第536行：君主数据规模（651 → 656）

# 4. 更新索引文件
vim skills/INDEX.md             # 第100行
vim skills/SKILL_03_实体构建.md  # 第16行
vim skills/SKILL_00_管线总览.md  # 第164行

# 5. 更新脚本引用
vim scripts/update_skill_frontmatter.py  # 第65行

# 6. 验证
git diff --cached
```

**更新内容总结**：
- 文件重命名：1个
- 统计数据更新：7处（3,797→4,418、586→591、651→656、新增17,483等）
- 索引文件更新：3个（INDEX.md、SKILL_03、SKILL_00）
- 脚本更新：1个（update_skill_frontmatter.py）

**经验教训**：

✅ **做得好的**：
- 使用脚本统计实际数据，而非估算
- 系统化检查所有需要更新的位置
- 同步更新所有索引文件和引用脚本

⚠️ **可改进的**：
- 应该有自动化脚本检测Skill中的过时数据
- 应该有Skill版本管理机制（记录每次更新的具体改动）
- 应该定期（如每月）扫描所有Skill的统计数据新鲜度

---

## 五、自动化工具（建议开发）

### 工具1：Skill统计数据新鲜度检查

```python
# scripts/check_skill_freshness.py
"""检查Skill中的统计数据是否过时"""

import re
import json

def check_skill_stats(skill_file):
    """
    提取Skill中的所有数字，与实际数据对比

    输出：
    - ✅ PASS: 数字一致
    - ⚠️  WARN: 数字偏差<20%
    - ❌ FAIL: 数字偏差>20%
    """
    # 读取Skill中的统计数字
    with open(skill_file) as f:
        content = f.read()

    numbers = re.findall(r'(\d{1,3}(?:,\d{3})*|\d+)(?:条|个|章|组)', content)

    # 读取实际数据
    actual_stats = get_actual_stats()

    # 对比差异
    for num_str, unit in numbers:
        num = int(num_str.replace(',', ''))
        # 根据unit判断对应的实际数据
        # ...
```

**使用示例**：

```bash
# 检查单个Skill
python scripts/check_skill_freshness.py skills/SKILL_03b_人名消歧.md

# 检查所有Skill
python scripts/check_skill_freshness.py --all

# 输出示例：
# ✅ SKILL_01_古籍校勘.md - 统计数据最新
# ⚠️  SKILL_03b_人名消歧.md - 人名实体数过时（3797 vs 4418, +16%)
# ❌ SKILL_05_关系构建.md - 关系数严重过时（200 vs 1500, +650%)
```

### 工具2：Skill链接有效性检查

```bash
# scripts/check_skill_links.sh
#!/bin/bash

skill_file=$1

echo "检查 $skill_file 的所有链接..."

# 提取所有Markdown链接
grep -o "\[.*\](.*\.md)" "$skill_file" | sed 's/.*(\(.*\))/\1/' | while read link; do
    # 尝试绝对路径和相对路径
    if [ -f "$link" ] || [ -f "skills/$link" ] || [ -f "$(dirname $skill_file)/$link" ]; then
        echo "✅ $link"
    else
        echo "❌ Broken link: $link"
    fi
done
```

---

## 六、定期维护

### 月度检查（每月1号）

```bash
# 1. 运行Skill新鲜度检查
python scripts/check_skill_freshness.py --all

# 2. 检查失效链接
for skill in skills/SKILL_*.md; do
    bash scripts/check_skill_links.sh "$skill"
done

# 3. 检查关联脚本可用性
for skill in skills/SKILL_*.md; do
    # 提取脚本路径
    scripts=$(grep -o "scripts/[a-zA-Z_/]*\.py" "$skill")
    for script in $scripts; do
        if [ -f "$script" ]; then
            python "$script" --help &>/dev/null || echo "⚠️  $script 无法运行"
        else
            echo "❌ $script 不存在（引用于 $skill）"
        fi
    done
done
```

### 季度审查（每季度末）

- [ ] 识别过时Skill（最近90天引用<3次）
- [ ] 更新所有统计数据
- [ ] 重构超过800行的Skill
- [ ] 归档废弃的Skill

---

## 相关文档

- 主文档：[SKILL_10f_Skill的提炼与转化.md](../SKILL_10f_Skill的提炼与转化.md)
- 模板库：[SKILL_10f1_模板库.md](./SKILL_10f1_模板库.md)
- 精简拆分：[SKILL_10f2_精简拆分案例库.md](./SKILL_10f2_精简拆分案例库.md)
- 脚本分解：[SKILL_10f4_脚本分解示例.md](./SKILL_10f4_脚本分解示例.md)
