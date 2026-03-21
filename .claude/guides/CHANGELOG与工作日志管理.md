# SKILL: CHANGELOG与工作日志管理

**版本**: v1.0
**最后更新**: 2026-03-21
**适用场景**: 项目文档维护、变更记录管理、工作日志归档

---

## 一、核心原则

### 1. 三层文档体系

```
CHANGELOG.md（概要层）
    ↓ 链接到
logs/daily/YYYY-MM-DD.md（详细层）
    ↓ 引用
git commits（代码层）
```

**分层职责**：
- **CHANGELOG**: 高层总结，核心功能，按日期/月度组织
- **daily logs**: 详细工作记录，完整功能说明，技术细节
- **git commits**: 完整代码变更历史

### 2. 信息完整性原则

✅ **零遗失**: 所有重要信息都要有归档位置
✅ **可追溯**: 从概要到细节都能找到
✅ **不重复**: 详细信息只在一处记录，其他处链接引用

### 3. 详略得当原则

- **CHANGELOG要简**: 一句话总结功能，关键数据
- **daily logs要详**: 完整的功能说明，子功能列表，技术细节
- **重构时归档**: 删除的详细信息必须转移到工作日志

---

## 二、CHANGELOG编写规范

### 1. 基本结构

```markdown
# 更新日志 (Changelog)

本文档记录《项目名》的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

**每日详细工作日志**: [`logs/daily/`](logs/daily/) 目录

---

## YYYY-MM-DD

### 新增 (Added)

- **功能名称** ([commit_hash](github_url))：简短描述

### 修复 (Fixed)

- **问题名称** ([commit_hash](github_url))：修复内容+关键数字

### 更改 (Changed)

- **模块名称** ([commit_hash](github_url))：变更概括

**详细工作日志**: [`logs/daily/YYYY-MM-DD.md`](logs/daily/YYYY-MM-DD.md)

---

## YYYY-MM（月度汇总，用于早期/commit少的月份）

### 新增 (Added)
...

---

**最后更新**: YYYY-MM-DD
```

### 2. Commit链接格式

**标准格式**（必须使用）：
```markdown
([commit_hash](https://github.com/user/repo/commit/commit_hash))
```

**多commit**：
```markdown
([hash1](url1) / [hash2](url2) / [hash3](url3))
```

**说明**：
- 必须使用8位短hash
- 必须包含完整GitHub URL
- 不要使用 `[hash]` 这种不完整格式

### 3. 条目编写要点

**标题要清晰**：
```markdown
✅ - **司马迁文风提炼实验** ([hash](url))：三层SKILL架构
❌ - **新实验** ([hash](url))：做了些东西
```

**数据要具体**：
```markdown
✅ - **实体边界修复** ([hash](url))：75处切分错误
❌ - **实体修复** ([hash](url))：修了一些错误
```

**链接要完整**：
```markdown
✅ - **溯源推理** ([`skills/SKILL_07d_溯源推理.md`](skills/SKILL_07d_溯源推理.md))
✅ - **详细工作日志**: [`logs/daily/2026-03-20.md`](logs/daily/2026-03-20.md)
```

### 4. 按日期 vs 按月度

**按日期条目**（推荐用于活跃开发期）：
- 适用：commit数量多的月份（如每月>20个commit）
- 优点：时间线清晰，便于查找
- 示例：2026年2-3月

**按月度汇总**（适用于早期/不活跃期）：
- 适用：commit数量少的月份（如每月<20个commit）
- 优点：避免过于分散
- 示例：2026年1月、2025年

### 5. 不要包含的内容

❌ **技术栈变更** - 属于README或架构文档
❌ **贡献者列表** - 属于README
❌ **许可证变更** - 属于LICENSE文件
❌ **版本号标记** - 用git tag管理
❌ **未来计划** - 属于TODO或项目规划文档

---

## 三、工作日志编写规范

### 1. 文件命名

```
logs/daily/YYYY-MM-DD.md
```

### 2. 基本结构

```markdown
# YYYY-MM-DD 工作日志

## 核心功能变化

### 新功能

- **功能名称**（文件路径或模块名）：
  - 子功能1
  - 子功能2
  - 详细说明

### 实体反思/Bug修复

- **问题名称**：
  - 问题描述
  - 修复方案
  - 涉及文件数量
  - 详细报告链接

### 文档更新

- 文档路径：具体变更

## 技术细节

- 提交次数: X
- 涉及文件: X个
- Issue关闭: #X

## 相关Commit

- [hash](url) - 简短描述

---

**工作时长**: 约X小时
**参与者**: 人名/AI名称
```

### 3. 归档旧版详细信息

当CHANGELOG重构精简后，将删除的详细信息归档到对应日期的工作日志：

```markdown
## 旧版CHANGELOG详细信息（归档）

以下内容来自重构前的CHANGELOG (commit_hash版本)，
记录了更详细的功能说明。

---

[完整的旧版条目内容，保持原格式]

---
```

**归档要点**：
- 标注来源版本（commit hash）
- 保持原有格式和链接
- 放在工作日志末尾
- 用明确的分隔符（`---`）

---

## 四、重构工作流程

### 场景：CHANGELOG过于冗长需要精简

#### 步骤1：备份与分析

```bash
# 1. 确定重构前的commit版本
git log --oneline | head -1  # 记录当前commit hash

# 2. 导出旧版CHANGELOG
git show <commit_hash>:CHANGELOG.md > /tmp/changelog_old.md

# 3. 分析规模
wc -l CHANGELOG.md
wc -l /tmp/changelog_old.md
```

#### 步骤2：重构CHANGELOG

**原则**：
- 保持核心信息（commit链接、关键数字）
- 删除过度详细的子功能列表
- 按日期/月度重新组织

**检查清单**：
- [ ] 所有commit链接格式正确
- [ ] 每个日期都有"详细工作日志"链接
- [ ] 删除了技术栈、贡献者等冗余章节
- [ ] 保留了关键统计数字

#### 步骤3：归档详细信息

```python
# 使用Python脚本提取旧版详细信息
import re

with open('/tmp/changelog_old.md', 'r') as f:
    old_content = f.read()

# 按日期分组提取详细条目
sections = re.split(r'^## ', old_content, flags=re.MULTILINE)[1:]

# 为每个日期生成归档内容
# （见完整脚本示例）
```

**归档方法**：
1. 读取旧版CHANGELOG
2. 提取每个日期的所有详细条目
3. 附加到对应日期的工作日志末尾
4. 标注来源版本

#### 步骤4：验证完整性

```bash
# 检查commit覆盖率
python3 << 'EOF'
import re
import subprocess

# 读取CHANGELOG中所有commit
with open('CHANGELOG.md', 'r') as f:
    changelog = f.read()

commits_in_changelog = set(re.findall(
    r'([0-9a-f]{8})\]\(https://github\.com/.*?/commit/\1\)',
    changelog
))

# 获取git历史所有commit
result = subprocess.run(['git', 'log', '--all', '--format=%h'],
                       capture_output=True, text=True)
all_commits = set(result.stdout.strip().split('\n'))

# 统计
print(f"Git历史总commit数: {len(all_commits)}")
print(f"CHANGELOG已归档: {len(commits_in_changelog)}")
print(f"覆盖率: {len(commits_in_changelog)/len(all_commits)*100:.1f}%")
EOF
```

**目标覆盖率**：
- 活跃开发月份：≥ 60%
- 完整发布月份：≥ 80%
- 月度汇总：≥ 30%

#### 步骤5：更新今日工作日志

在 `logs/daily/YYYY-MM-DD.md` 中记录：
- 重构前后行数对比
- 归档的工作日志数量
- 覆盖率变化
- 删除的章节（技术栈等）

---

## 五、常见场景与方法

### 场景1：新增一天的工作

**CHANGELOG添加**：
```markdown
## 2026-03-XX

### 新增 (Added)
- **功能名** ([hash](url))：简述

**详细工作日志**: [`logs/daily/2026-03-XX.md`](logs/daily/2026-03-XX.md)
```

**创建工作日志**：
```bash
cat > logs/daily/2026-03-XX.md << 'EOF'
# 2026-03-XX 工作日志

## 核心功能变化
...
EOF
```

### 场景2：月度汇总改为按日条目

**适用条件**：某月commit数从<20增长到>30

**操作**：
1. 提取该月所有commit和日期
2. 为每个有commit的日期创建条目
3. 将月度汇总的详细信息分配到各日期
4. 更新或创建对应的daily logs

### 场景3：Commit链接格式修复

**常见问题**：
```markdown
❌ ([hash])           # 没有URL
❌ [hash]             # 没有括号和URL
❌ ([hash] / [hash2]) # 第一个hash没有URL
```

**批量修复脚本**：
```python
import re

with open('CHANGELOG.md', 'r') as f:
    content = f.read()

# 修复格式1: [hash] → [hash](url)
pattern = r'\[([0-9a-f]{8})\](?!\()'
replacement = r'[\1](https://github.com/user/repo/commit/\1)'
content = re.sub(pattern, replacement, content)

with open('CHANGELOG.md', 'w') as f:
    f.write(content)
```

### 场景4：删除冗余章节并归档

**要删除的章节**：
- 技术栈变更
- 贡献者
- 许可证变更

**操作**：
1. 从CHANGELOG中删除这些章节
2. 将内容完整复制到今日工作日志的归档章节
3. 在今日工作日志中说明删除原因

---

## 六、质量检查清单

### CHANGELOG质量检查

- [ ] **结构清晰**：按日期倒序排列
- [ ] **链接完整**：所有commit都有完整的GitHub URL
- [ ] **日志链接**：每个日期都链接到对应的daily log
- [ ] **分类准确**：Added/Fixed/Changed分类正确
- [ ] **描述简洁**：每条1-2行，包含关键数字
- [ ] **无冗余章节**：没有技术栈、贡献者等
- [ ] **覆盖率合理**：活跃月份≥60%

### 工作日志质量检查

- [ ] **命名规范**：`logs/daily/YYYY-MM-DD.md`
- [ ] **内容完整**：包含核心功能、技术细节、commit列表
- [ ] **详略得当**：详细但不冗长，有重点
- [ ] **链接有效**：文件路径、commit链接都正确
- [ ] **归档完整**：如有旧版信息，都已归档

### 重构后验证

- [ ] **信息零遗失**：所有删除的详细信息都已归档
- [ ] **覆盖率达标**：按场景要求的覆盖率
- [ ] **文件完整**：所有提到的daily logs都存在
- [ ] **格式统一**：commit链接格式一致
- [ ] **可追溯性**：从CHANGELOG能找到详细信息

---

## 七、工具脚本模板

### 脚本1：统计commit覆盖率

```python
#!/usr/bin/env python3
import re
import subprocess

def check_commit_coverage():
    """检查CHANGELOG中的commit覆盖率"""

    # 读取CHANGELOG
    with open('CHANGELOG.md', 'r') as f:
        changelog = f.read()

    # 提取所有已归档的commit
    pattern = r'([0-9a-f]{8})\]\(https://github\.com/.*?/commit/\1\)'
    commits_in_changelog = set(re.findall(pattern, changelog))

    # 获取git历史
    result = subprocess.run(
        ['git', 'log', '--all', '--format=%h'],
        capture_output=True, text=True
    )
    all_commits = set(result.stdout.strip().split('\n'))

    # 统计
    total = len(all_commits)
    covered = len(commits_in_changelog)
    rate = covered / total * 100 if total > 0 else 0

    print(f"📊 Commit覆盖率统计")
    print(f"  总commit数: {total}")
    print(f"  已归档: {covered}")
    print(f"  覆盖率: {rate:.1f}%")
    print(f"  缺失: {total - covered}")

    return rate >= 60  # 返回是否达标

if __name__ == '__main__':
    check_commit_coverage()
```

### 脚本2：修复commit链接格式

```python
#!/usr/bin/env python3
import re

def fix_commit_links(repo_url):
    """修复CHANGELOG中不完整的commit链接"""

    with open('CHANGELOG.md', 'r') as f:
        content = f.read()

    # 修复 [hash] → [hash](url)
    pattern = r'\[([0-9a-f]{8})\](?!\()'
    replacement = f'[\\1]({repo_url}/commit/\\1)'
    new_content = re.sub(pattern, replacement, content)

    # 统计修复数量
    count = len(re.findall(pattern, content))

    # 写回文件
    with open('CHANGELOG.md', 'w') as f:
        f.write(new_content)

    print(f"✅ 修复了 {count} 个不完整的commit链接")

if __name__ == '__main__':
    REPO_URL = 'https://github.com/user/repo'
    fix_commit_links(REPO_URL)
```

### 脚本3：归档旧版CHANGELOG详细信息

```python
#!/usr/bin/env python3
import re
import os
from collections import defaultdict

def archive_old_changelog_details(old_changelog_path):
    """将旧版CHANGELOG的详细信息归档到工作日志"""

    # 读取旧版CHANGELOG
    with open(old_changelog_path, 'r') as f:
        old_content = f.read()

    # 提取所有模块条目
    sections = re.split(r'^## ', old_content, flags=re.MULTILINE)[1:]

    # 按日期组织
    details_by_date = defaultdict(list)
    for section in sections:
        title = section.split('\n')[0]

        # 提取日期
        dates = re.findall(r'(\d{4}-\d{2}-\d{2})', title)
        if dates:
            date = dates[-1]  # 使用最后一个日期
            details_by_date[date].append('## ' + section)

    # 为每个日期附加到工作日志
    updated = 0
    for date in sorted(details_by_date.keys(), reverse=True):
        log_file = f'logs/daily/{date}.md'

        if not os.path.exists(log_file):
            continue

        # 读取现有日志
        with open(log_file, 'r') as f:
            existing = f.read()

        # 检查是否已归档
        if '旧版CHANGELOG详细信息' in existing:
            continue

        # 生成归档内容
        appendix = '\n\n---\n\n## 旧版CHANGELOG详细信息（归档）\n\n'
        appendix += '以下内容来自重构前的CHANGELOG，记录了更详细的功能说明。\n\n'
        appendix += '---\n\n'

        for section in details_by_date[date]:
            appendix += section + '\n\n---\n\n'

        # 写入
        with open(log_file, 'w') as f:
            f.write(existing.rstrip() + appendix)

        print(f"✅ {date}: 已归档 {len(details_by_date[date])} 个详细条目")
        updated += 1

    print(f"\n完成！共更新 {updated} 个工作日志")

if __name__ == '__main__':
    archive_old_changelog_details('/tmp/changelog_old.md')
```

---

## 八、最佳实践

### 1. 每日工作结束时

- [ ] 更新或创建今日工作日志
- [ ] 添加今日的CHANGELOG条目
- [ ] 确保commit链接格式正确

### 2. 每周回顾时

- [ ] 检查本周工作日志的完整性
- [ ] 补充遗漏的技术细节
- [ ] 检查CHANGELOG条目的准确性

### 3. 月度整理时

- [ ] 决定是否需要月度汇总
- [ ] 检查commit覆盖率
- [ ] 统一commit链接格式

### 4. 大版本发布前

- [ ] 全面检查CHANGELOG完整性
- [ ] 确保覆盖率≥80%
- [ ] 补充所有缺失的工作日志

### 5. 重构CHANGELOG时

- [ ] 先备份旧版（git show导出）
- [ ] 重构时保持核心信息
- [ ] 将删除的详细信息归档到工作日志
- [ ] 验证信息零遗失

---

## 九、参考资源

### 标准和规范

- [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

### 本项目实例

- `/CHANGELOG.md` - 当前CHANGELOG
- `/logs/daily/2026-03-21.md` - CHANGELOG重构工作日志示例
- `/logs/daily/2026-03-20.md` - 旧版详细信息归档示例

### 相关SKILL

- `00-META-01_反思.md` - 反思方法论
- `00-META-02_迭代工作流.md` - 迭代开发流程
- `00-META-00_好东西都是总结出来的.md` - 总结方法论

---

## 十、版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0 | 2026-03-21 | 初版：基于CHANGELOG重构实践总结 |

---

**作者**: 史记知识库项目组
**最后审阅**: 2026-03-21
**适用于**: 所有需要维护CHANGELOG和工作日志的项目
