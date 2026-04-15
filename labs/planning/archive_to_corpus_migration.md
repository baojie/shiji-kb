# archive/ → corpus/archive/ 迁移规划

## 一、迁移概述

### 1.1 目标

将 `archive/` 目录整体迁移到 `corpus/archive/`，使其成为corpus语料库的一个子目录，与`corpus/shiji/`和`corpus/other/`并列。

### 1.2 目录结构变化

**迁移前**：
```
项目根目录/
├── archive/                    # 文本处理历史阶段
│   ├── chapter/               # 130章纯文本底本（★核心基准）
│   ├── chapter_improved/      # 改进版（保留空行）
│   ├── chapter_numbered/      # 编号版（带段落号）
│   └── README.md
├── corpus/                     # 语料库
│   ├── shiji/                 # 史记各版本
│   └── other/                 # 其他古籍
└── chapter_md/                 # 当前工作目录（130个标注文件）
```

**迁移后**：
```
项目根目录/
├── corpus/                     # 语料库（统一管理所有语料）
│   ├── archive/               # 文本处理历史阶段（迁移后）
│   │   ├── chapter/          # 130章纯文本底本（★核心基准）
│   │   ├── chapter_improved/ # 改进版（保留空行）
│   │   ├── chapter_numbered/ # 编号版（带段落号）
│   │   └── README.md
│   ├── shiji/                 # 史记各版本
│   └── other/                 # 其他古籍
└── chapter_md/                 # 当前工作目录（130个标注文件）
```

### 1.3 迁移原因

- **统一语料管理**：所有语料资源集中在corpus/目录下
- **清晰的层级关系**：corpus/作为顶层语料目录，archive/、shiji/、other/作为子分类
- **符合目录规范**：遵循项目的corpus/语料库体系设计

---

## 二、影响范围调研

### 2.1 目录统计

| 目录 | 文件数 | 总大小 | 内容 |
|------|--------|--------|------|
| `archive/chapter/` | 130 | ~2MB | 纯文本底本（无格式） |
| `archive/chapter_improved/` | 130 | ~2MB | 改进版（保留空行） |
| `archive/chapter_numbered/` | 130 | ~2MB | 编号版（带[N]段落号） |

**总计**: 390个文件，约6MB

### 2.2 路径引用统计

通过grep全局搜索，发现以下路径引用分布：

| 路径模式 | 引用次数 | 主要文件类型 | 是否更新 |
|---------|---------|-------------|---------|
| `archive/chapter/` | 110 | skills/*.md | ✅ 需要更新 |
| `archive/chapter/` | 13 | scripts/*.py | ✅ 需要更新 |
| `archive/chapter/` | 4 | kg/entities/scripts/*.py | ✅ 需要更新 |
| `archive/chapter/` | ~50 | doc/reports/, doc/entities/, logs/ | ❌ 不更新（历史文档） |
| `archive/chapter/` | ~5 | CLAUDE.md, README.md, doc/workflow/, doc/spec/ | ✅ 需要更新 |
| `chapter_md/` | 1030 | 全项目各类文件 | ❌ 不迁移 |

**⚠️ 关键发现**：
- `archive/chapter/` 作为**标准底本基准**，被大量文档和脚本引用
- `chapter_md/` (当前工作目录) 在项目中被1030次引用，**不应迁移**
- 迁移archive/到corpus/后，**实际需要更新约130+个文件**（排除历史文档和日志）

### 2.3 核心依赖关系

#### 2.3.1 校勘工作流依赖

```
corpus/archive/chapter/NNN_篇名.txt  (标准底本)
    ↓ 校对修改
    ↓ 同步更新
    ├─→ corpus/archive/chapter_improved/NNN_篇名.txt
    ├─→ corpus/archive/chapter_numbered/NNN_篇名.txt
    ├─→ docs/original_text/NNN_篇名.txt (独立工作定本)
    └─→ chapter_md/NNN_篇名.tagged.md (标注文件)
```

#### 2.3.2 文本完整性检查依赖

```python
# scripts/lint_text_integrity.py
# 去除标注符号后与 archive/chapter/ 中的原文底本逐字比对
标注文件(chapter_md/*.tagged.md) → 去标注 → 纯文本
    ↓ 逐字比对
corpus/archive/chapter/*.txt (基准底本)
```

#### 2.3.3 实体验证依赖

```python
# kg/entities/scripts/validate_all_chapters.py
# 验证标注文件与底本一致性
for chapter in 001-130:
    txt_file = 'corpus/archive/chapter_numbered/{NNN}_*.txt'
    tagged_file = 'chapter_md/{NNN}_*.tagged.md'
    validate(txt_file, tagged_file)
```

---

## 三、需要更新的文件清单

### 3.1 SKILL文档（110+处引用）

#### 核心SKILL文件

1. **SKILL_01b_多版本互校底本.md** (41处) - 最多引用
   - 版本路径表格
   - 校对流程说明
   - 派生文件同步规范
   - 示例命令

2. **SKILL_01_古籍校勘.md** (若干处)
   - 版本资源路径
   - 文件结构图

3. **SKILL_01a_标注完整性维护.md** (若干处)
   - 底本路径引用
   - lint脚本说明

4. **SKILL_01g_标注符号集合原则.md** (8处)
   - 示例路径

5. **其他SKILL文档**：
   - SKILL_00_管线总览.md
   - SKILL_02b_区块与韵文处理.md
   - SKILL_02c_三家注标注.md
   - SKILL_03a_实体标注.md
   - SKILL_03c_按章反思.md
   - SKILL_03d_渲染与发布.md
   - SKILL_03e_按类型反思.md
   - SKILL_03f_实体边界错误综合反思.md
   - SKILL_05d_事实发现.md
   - SKILL_09m_排版和电子书构造.md
   - SKILL_10b_每日工作日志维护.md
   - SKILL_10c_Git代码版本管理规范.md
   - ... (更多)

#### 参考文档

- skills/references/SKILL_01a1_标注格式规范.md
- skills/references/SKILL_01f_background.md
- skills/references/SKILL-03c1-rules.md
- skills/references/SKILL_10c1_禁止命令清单.md
- skills/references/SKILL_10f4_脚本分解示例.md

### 3.2 Python脚本（17处引用）

#### scripts/ 目录（13处）

1. **generate_custom_variants.py** (2处)
   ```python
   chapter_file = Path(f"archive/chapter/{chapter_num:03d}_*.txt")
   files = list(Path("archive/chapter").glob(f"{chapter_num:03d}_*.txt"))
   ```

2. **generate_variants_from_comparison.py** (2处)
   ```python
   # 加载简体底本（archive/chapter/*.txt）
   files = list(Path("archive/chapter").glob(f"{chapter_num:03d}_*.txt"))
   ```

3. **lint_text_integrity.py** (1处)
   ```python
   # 去除全部语义标注符号后，与 archive/chapter/ 中的原文底本逐字比对
   ```

4. **fix_missing_parent_pn.py** (2处)
   ```python
   help='选择处理的目录：chapter_md（默认）或 archive/chapter_numbered'
   target_dir = Path('archive/chapter_numbered')
   ```

5. **fix_fudao_typo.py** (6处)
   ```python
   # archive/chapter_numbered/ (4个文件)
   "archive/chapter_numbered/006_秦始皇本纪.txt",
   "archive/chapter_numbered/012_孝武本纪.txt",
   "archive/chapter_numbered/028_封禅书.txt",
   "archive/chapter_numbered/099_刘敬叔孙通列传.txt",
   print("\n📁 修改 archive/chapter_numbered/")
   ```

#### kg/entities/scripts/ 目录（4处）

1. **find_differences.py** (1处)
   ```python
   txt_file = base_dir / 'archive/chapter_numbered' / '005_秦本纪.txt'
   ```

2. **report_differences.py** (1处)
   ```python
   txt_file = base_dir / 'archive/chapter_numbered' / '005_秦本纪.txt'
   ```

3. **validate_all_chapters.py** (2处)
   ```python
   txt_file = base_dir / 'archive/chapter_numbered' / f'{num:03d}_*.txt'
   txt_files = list(base_dir.glob(f'archive/chapter_numbered/{num:03d}_*.txt'))
   ```

### 3.3 根目录文档和配置文件（~5处）

**需要更新的文件**：

- CLAUDE.md (2处)
- README.md (1处)
- corpus/archive/README.md (自身文档，迁移后需更新内部路径引用)

**⚠️ 不需要更新的文件/目录**：

- ❌ `CHANGELOG.md` - 不更新（历史记录）
- ❌ `TODO.md` - 不更新
- ❌ `doc/reports/` - 不更新（历史报告）
- ❌ `doc/entities/` - 不更新（历史反思报告）
- ❌ `logs/` - 不更新（所有日志文件）

**仅需更新的doc/子目录**：

- ✅ doc/workflow/开发工作流程.md (若有引用)
- ✅ doc/methodology/研究方法总则.md (若有引用)
- ✅ doc/spec/*.md (规范文档，若有引用)

### 3.4 特殊引用：chapter_md/

⚠️ **重要决策**：`chapter_md/` 目录**不迁移**

**理由**：
- `chapter_md/` 是**当前工作目录**，不是历史归档
- 有1030+处引用，迁移成本极高
- 逻辑上，它是基于archive/chapter的**工作副本**，不属于corpus语料库
- 符合项目约定："当前生产流程的起点是 `chapter_md/*.tagged.md`"

---

## 四、迁移路径映射表

| 原路径 | 新路径 | 说明 |
|--------|--------|------|
| `archive/` | `corpus/archive/` | 整个目录迁移 |
| `archive/chapter/` | `corpus/archive/chapter/` | 标准底本 |
| `archive/chapter_improved/` | `corpus/archive/chapter_improved/` | 改进版 |
| `archive/chapter_numbered/` | `corpus/archive/chapter_numbered/` | 编号版 |
| `archive/README.md` | `corpus/archive/README.md` | 说明文档 |
| `chapter_md/` | `chapter_md/` | **不迁移**（保持不变） |
| `docs/original_text/` | `docs/original_text/` | **不迁移**（独立工作定本） |

---

## 五、迁移实施步骤（不执行，仅规划）

### 5.1 准备阶段

1. **创建corpus/archive/目录**
   ```bash
   mkdir -p corpus/archive
   ```

2. **Git移动archive/内容**
   ```bash
   git mv archive/chapter corpus/archive/
   git mv archive/chapter_improved corpus/archive/
   git mv archive/chapter_numbered corpus/archive/
   git mv archive/README.md corpus/archive/
   ```

### 5.2 路径更新阶段

#### 阶段1：更新SKILL文档（110+处）

```bash
# 批量替换 archive/chapter → corpus/archive/chapter
find skills/ -name "*.md" -type f -exec sed -i \
  's|archive/chapter|corpus/archive/chapter|g' {} \;

# 验证
grep -rn "archive/chapter" skills/ --include="*.md" | wc -l
# 应返回 0
```

#### 阶段2：更新Python脚本（17处）

**方案A：批量sed替换**（不推荐，可能破坏字符串）
```bash
find scripts/ kg/ -name "*.py" -type f -exec sed -i \
  's|archive/chapter|corpus/archive/chapter|g' {} \;
```

**方案B：逐个文件手动更新**（推荐）
- 使用Edit工具逐个更新Python文件中的路径字符串
- 每个文件更新后运行语法检查

#### 阶段3：更新根目录文档和doc/部分子目录（~5处）

```bash
# 根目录文档（仅更新CLAUDE.md和README.md）
sed -i 's|archive/chapter|corpus/archive/chapter|g' CLAUDE.md
sed -i 's|archive/chapter|corpus/archive/chapter|g' README.md

# doc/子目录（仅更新workflow和spec，排除reports和entities）
find doc/workflow/ doc/spec/ doc/methodology/ -name "*.md" -type f 2>/dev/null -exec sed -i \
  's|archive/chapter|corpus/archive/chapter|g' {} \;

# ⚠️ 以下目录不更新（历史文档）：
# - doc/reports/
# - doc/entities/
# - logs/
# - CHANGELOG.md
# - TODO.md
```

#### 阶段4：更新corpus/archive/README.md

更新自身路径引用：
```bash
sed -i 's|archive/chapter|corpus/archive/chapter|g' corpus/archive/README.md
```

### 5.3 验证阶段

#### 验证1：路径引用完整性

```bash
# 检查需要更新的目录中是否还有旧路径引用
grep -rn "archive/chapter" \
  skills/ scripts/ kg/ CLAUDE.md README.md \
  doc/workflow/ doc/spec/ doc/methodology/ \
  --include="*.md" --include="*.py" 2>/dev/null | \
  wc -l
# 应返回 0

# ⚠️ 以下目录中的旧路径引用是正常的（历史文档，不需要更新）：
# - doc/reports/
# - doc/entities/
# - logs/
# - CHANGELOG.md
# - TODO.md
```

#### 验证2：脚本功能验证

```bash
# 测试lint_text_integrity.py
python scripts/lint_text_integrity.py chapter_md/001_五帝本纪.tagged.md

# 测试validate_all_chapters.py
python kg/entities/scripts/validate_all_chapters.py

# 测试generate_custom_variants.py
python scripts/generate_custom_variants.py --chapter 1
```

#### 验证3：Git状态检查

```bash
git status
# 应显示：
# - renamed: archive/chapter → corpus/archive/chapter
# - renamed: archive/chapter_improved → corpus/archive/chapter_improved
# - renamed: archive/chapter_numbered → corpus/archive/chapter_numbered
# - renamed: archive/README.md → corpus/archive/README.md
# - modified: skills/*.md (大量文件)
# - modified: scripts/*.py (17个文件)
# - modified: doc/*.md, logs/*.md, CLAUDE.md, README.md等
```

### 5.4 更新corpus/README.md

添加archive/子目录说明：

```markdown
## archive/ - 文本处理历史阶段

存放《史记》从原始文本到标注就绪的各处理阶段中间产物，供溯源参考。

| 子目录 | 内容 | 文件数 | 说明 |
|--------|------|--------|------|
| `chapter/` | 按章分割的纯文本（无格式） | 130 | 项目标准底本，lint基准 |
| `chapter_improved/` | 改进版（保留段落空行） | 130 | 基于chapter/，格式优化 |
| `chapter_numbered/` | 编号版（带[N]段落号） | 130 | 基于chapter/，添加编号 |

详见 [archive/README.md](archive/README.md)
```

---

## 六、风险评估与应对

### 6.1 高风险点

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| **脚本路径硬编码** | Python脚本功能失效 | 逐个测试所有脚本，手动修复 |
| **批量替换误伤** | 文档/代码损坏 | 分阶段commit，每阶段验证后再继续 |
| **Git历史混乱** | 文件溯源困难 | 使用 `git mv` 而非 `mv`，保留Git历史 |
| **lint检查失效** | 标注完整性无法验证 | 优先测试lint_text_integrity.py |

### 6.2 回退方案

如果迁移后发现严重问题：

```bash
# 方案1：Git回退（未push时）
git reset --hard HEAD~1

# 方案2：Git revert（已push时）
git revert <commit-hash>

# 方案3：手动恢复（最后手段）
git mv corpus/archive/chapter archive/
git mv corpus/archive/chapter_improved archive/
git mv corpus/archive/chapter_numbered archive/
git mv corpus/archive/README.md archive/
# 然后恢复所有文档中的路径引用
```

---

## 七、迁移后的目录结构

### 7.1 corpus/目录完整结构

```
corpus/
├── README.md                      # corpus总览文档
├── archive/                       # 文本处理历史阶段（迁移后）
│   ├── chapter/                  # 130章纯文本底本
│   │   ├── 001_五帝本纪.txt
│   │   ├── ...
│   │   └── 130_太史公自序.txt
│   ├── chapter_improved/         # 改进版（保留空行）
│   │   ├── 001_五帝本纪.txt
│   │   └── ...
│   ├── chapter_numbered/         # 编号版（带段落号）
│   │   ├── 001_五帝本纪.txt
│   │   └── ...
│   └── README.md                 # archive说明文档
├── shiji/                         # 史记各版本语料
│   ├── 史记.简体.txt
│   ├── 史記正文.繁体.txt
│   ├── 史記三家注.繁体.txt
│   ├── wikisource_shiji/
│   ├── wikisource_sanjia/
│   └── ... (其他史记版本)
└── other/                         # 其他古籍语料
    ├── 春秋左传.txt
    ├── 汉书.txt
    └── ... (其他古籍)
```

### 7.2 项目根目录结构（迁移后）

```
项目根目录/
├── corpus/                        # 语料库（统一管理）
│   ├── archive/                  # 文本处理历史（迁移后）
│   ├── shiji/                    # 史记各版本
│   └── other/                    # 其他古籍
├── chapter_md/                    # 当前工作目录（不迁移）
│   ├── 001_五帝本纪.tagged.md
│   └── ...
├── docs/                          # 文档（路径已更新）
├── scripts/                       # 脚本（路径已更新）
├── skills/                        # 技能文档（路径已更新）
├── logs/                          # 日志（路径已更新）
├── kg/                           # 知识图谱（路径已更新）
├── CLAUDE.md                     # 项目指南（路径已更新）
├── README.md                     # 项目README（路径已更新）
└── ...
```

---

## 八、验证检查清单

### 8.1 迁移前检查

- [ ] 备份当前working tree（如有未提交变更）
- [ ] 确认git status干净
- [ ] 统计archive/目录大小和文件数
- [ ] 列出所有引用archive/chapter的文件清单

### 8.2 迁移中检查

- [ ] Git移动操作完成（4个mv命令）
- [ ] SKILL文档路径更新完成（110+处）
- [ ] Python脚本路径更新完成（17处）
- [ ] 根目录文档路径更新完成（CLAUDE.md, README.md）
- [ ] doc/部分子目录路径更新完成（workflow/, spec/, methodology/）
- [ ] corpus/README.md已更新
- [ ] corpus/archive/README.md自身路径已更新

### 8.3 迁移后验证

- [ ] grep验证需更新目录无残留旧路径（skills/, scripts/, kg/, CLAUDE.md, README.md, doc/workflow/, doc/spec/）
- [ ] 确认历史文档保持原样（doc/reports/, doc/entities/, logs/, CHANGELOG.md, TODO.md）
- [ ] lint_text_integrity.py测试通过
- [ ] validate_all_chapters.py测试通过
- [ ] generate_custom_variants.py测试通过
- [ ] Git status显示正确（renamed + modified）
- [ ] 所有变更已commit

---

## 九、未来优化建议

### 9.1 路径常量化

建议创建 `scripts/config.py`：

```python
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 语料库路径
CORPUS_ROOT = PROJECT_ROOT / 'corpus'
ARCHIVE_ROOT = CORPUS_ROOT / 'archive'
SHIJI_ROOT = CORPUS_ROOT / 'shiji'

# 底本路径
CHAPTER_DIR = ARCHIVE_ROOT / 'chapter'
CHAPTER_IMPROVED_DIR = ARCHIVE_ROOT / 'chapter_improved'
CHAPTER_NUMBERED_DIR = ARCHIVE_ROOT / 'chapter_numbered'

# 工作目录
BASE_COPY = PROJECT_ROOT / 'chapter_md'
```

然后所有脚本import使用：
```python
from scripts.config import CHAPTER_DIR, BASE_COPY
```

### 9.2 SKILL文档路径变量

在SKILL文档中使用变量引用：

```markdown
**底本路径**: `{{ARCHIVE_CHAPTER}}`
**标注目录**: `{{CHAPTER_MD}}`
```

使用预处理脚本统一替换，便于未来路径调整。

---

## 十、总结

### 10.1 迁移规模

- **目录移动**: 4个子目录（chapter/, chapter_improved/, chapter_numbered/, README.md）
- **文件迁移**: 390个文本文件（约6MB）
- **路径更新**: 约130+个文件需要更新
  - SKILL文档: 110+处
  - Python脚本: 17处
  - 根目录文档: 2处（CLAUDE.md, README.md）
  - doc/子目录: 若干处（workflow/, spec/, methodology/）

**不更新的文件**（保留历史路径引用）:
- ❌ doc/reports/ - 历史报告
- ❌ doc/entities/ - 历史反思报告
- ❌ logs/ - 所有日志文件
- ❌ CHANGELOG.md - 历史变更记录
- ❌ TODO.md - 任务清单

### 10.2 关键注意事项

1. **使用 `git mv` 而非 `mv`**：保留Git历史追踪
2. **分阶段commit**：每完成一个类别的更新就commit，便于回退
3. **优先测试核心脚本**：lint_text_integrity.py、validate_all_chapters.py
4. **chapter_md/不迁移**：它是当前工作目录，不属于corpus归档
5. **docs/original_text/不迁移**：它是独立工作定本，不强制同步
6. **历史文档不更新**：doc/reports/, doc/entities/, logs/, CHANGELOG.md, TODO.md保持原样

### 10.3 预期收益

- ✅ 语料库结构更清晰（corpus/统一管理）
- ✅ 符合项目规范（corpus/shiji/, corpus/other/, corpus/archive/）
- ✅ 便于未来扩展（可添加corpus/other_editions/等）
- ✅ 目录层级更合理（archive作为corpus的子目录）

---

**规划完成日期**: 2026-04-05
**规划人**: Claude (AI Agent)
**状态**: 待用户审核

---

## 附录：快速执行脚本（待用户确认后使用）

```bash
#!/bin/bash
# 文件名: migrate_archive_to_corpus.sh
# 用途: 将archive/迁移到corpus/archive/并更新所有路径引用

set -e  # 遇到错误立即退出

echo "=== archive/ → corpus/archive/ 迁移脚本 ==="
echo ""

# 1. 检查前置条件
echo "[1/6] 检查前置条件..."
if [ -d "corpus/archive" ]; then
    echo "❌ corpus/archive/已存在，请先删除或重命名"
    exit 1
fi
if [ ! -d "archive" ]; then
    echo "❌ archive/目录不存在"
    exit 1
fi
echo "✓ 前置条件检查通过"

# 2. Git移动目录
echo "[2/6] Git移动archive/到corpus/..."
git mv archive/chapter corpus/archive/chapter
git mv archive/chapter_improved corpus/archive/chapter_improved
git mv archive/chapter_numbered corpus/archive/chapter_numbered
git mv archive/README.md corpus/archive/README.md
echo "✓ Git移动完成"

# 3. 更新SKILL文档
echo "[3/6] 更新SKILL文档路径引用..."
find skills/ -name "*.md" -type f -exec sed -i \
  's|archive/chapter|corpus/archive/chapter|g' {} \;
echo "✓ SKILL文档更新完成"

# 4. 更新Python脚本
echo "[4/6] 更新Python脚本路径引用..."
find scripts/ kg/ -name "*.py" -type f -exec sed -i \
  's|archive/chapter|corpus/archive/chapter|g' {} \;
echo "✓ Python脚本更新完成"

# 5. 更新根目录文档和doc/部分子目录
echo "[5/6] 更新根目录文档和doc/部分子目录路径引用..."
# 仅更新CLAUDE.md和README.md
sed -i 's|archive/chapter|corpus/archive/chapter|g' CLAUDE.md
sed -i 's|archive/chapter|corpus/archive/chapter|g' README.md
# 仅更新doc/workflow, doc/spec, doc/methodology
find doc/workflow/ doc/spec/ doc/methodology/ -name "*.md" -type f 2>/dev/null -exec sed -i \
  's|archive/chapter|corpus/archive/chapter|g' {} \;
# 更新corpus/archive/README.md自身路径
sed -i 's|archive/chapter|corpus/archive/chapter|g' corpus/archive/README.md
echo "✓ 文档更新完成"
echo "⚠️  以下文件保持原样（不更新）："
echo "   - doc/reports/"
echo "   - doc/entities/"
echo "   - logs/"
echo "   - CHANGELOG.md"
echo "   - TODO.md"

# 6. 验证
echo "[6/6] 验证需更新目录中的旧路径引用..."
old_refs=$(grep -rn "archive/chapter" \
  skills/ scripts/ kg/ CLAUDE.md README.md \
  doc/workflow/ doc/spec/ doc/methodology/ \
  --include="*.md" --include="*.py" 2>/dev/null | \
  wc -l)

if [ "$old_refs" -eq 0 ]; then
    echo "✓ 验证通过：需更新目录中无残留旧路径引用"
else
    echo "⚠️ 警告：需更新目录中仍有 $old_refs 处旧路径引用"
    echo "请手动检查："
    grep -rn "archive/chapter" \
      skills/ scripts/ kg/ CLAUDE.md README.md \
      doc/workflow/ doc/spec/ doc/methodology/ \
      --include="*.md" --include="*.py" 2>/dev/null
fi

echo ""
echo "📌 历史文档中的旧路径引用是正常的（不需要更新）："
echo "   - doc/reports/, doc/entities/, logs/, CHANGELOG.md, TODO.md"

echo ""
echo "=== 迁移完成 ==="
echo "请运行以下命令验证："
echo "  python scripts/lint_text_integrity.py chapter_md/001_五帝本纪.tagged.md"
echo "  python kg/entities/scripts/validate_all_chapters.py"
echo ""
echo "如无问题，请commit变更："
echo "  git status"
echo "  git commit -m '重组目录结构：迁移archive/到corpus/archive/'"
```

**使用方法**：
1. 保存为 `scripts/migrate_archive_to_corpus.sh`
2. 添加执行权限：`chmod +x scripts/migrate_archive_to_corpus.sh`
3. 执行：`./scripts/migrate_archive_to_corpus.sh`

⚠️ **执行前务必**：
- 备份当前工作目录
- 确认git status干净
- 仔细阅读本规划文档
