---
name: daily
description: 扫描并补齐缺失的每日工作日志。对比 logs/daily/ 已有日志与 git 有提交的日期（按 07:00 边界归属），列出「昨天及之前、有 commit 但无日志」的日期，逐日调用 generate_log.py 生成骨架，再按 SKILL_10b 补写微信通知和改动意义。不执行 git add/commit，不补齐今天。
---

# /daily — 补齐缺失的每日工作日志

## 铁律

1. **不执行 git commit / git add**：只写日志文件
2. **不补齐今天**：今天的日志还在进行中，除非用户显式 `/daily <今天日期>`
3. **07:00 边界归属**：`YYYY-MM-DD.md` 覆盖 `YYYY-MM-DD 07:00` ~ `YYYY-MM-DD+1 07:00` 的 commit（凌晨 0-7 点归前一天）
4. **分支模式**：
   - **无参数 `/daily`**：扫描所有缺口并逐一补齐
   - **带参数 `/daily YYYY-MM-DD`**：只补齐指定日期（允许补今天）

## 无参数 `/daily` 执行步骤

### 1. 扫描已有日志

```bash
ls logs/daily/*.md | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | sort -u
```

### 2. 列出所有有提交的日期（按 07:00 边界归属）

```bash
# 取出每个 commit 的 ISO 时间戳，再用 awk 按 07:00 归属到日期
git log --all --date=iso --pretty=format:"%cd" \
  | awk '{ date=$1; time=$2; if (time < "07:00:00") { cmd="date -d \"" date " -1 day\" +%Y-%m-%d"; cmd | getline date; close(cmd); } print date }' \
  | sort -u
```

### 3. 计算缺口

集合差：`{有提交的日期}` − `{已有日志的日期}` − `{今天}`，得到要补齐的日期列表。

### 4. 展示清单 + 确认

向用户展示：

```
以下日期有 commit 但无日志，将逐一补齐：
- 2026-04-20（N 次提交）
- 2026-04-21（M 次提交）

共 2 天需补齐。是否继续？
```

等待用户确认后再执行第 5 步（除非用户已开启自动确认）。

### 5. 逐日补齐

对每个缺失日期 `D`：

1. **生成骨架**：`python logs/daily/generate_log.py D`
2. **按 SKILL_10b §3 生成微信通知**：
   - 读取 `logs/daily/D.md`
   - 用 `git log --since="D 07:00" --until="D+1 07:00"` 统计章节数、新增文件、新增 SKILL
   - 选 5-9 条核心工作 + 末尾 `· 提交N次代码`
   - 有提交日用 3.2 常规格式；无提交日用 3.3 「太史公曰」+ 32 字赞文
   - **可浏览成果 URL**：对「变化很大」的可浏览成果（新建/重构的 HTML 页面、索引、可视化、搜索界面），在该 bullet 下一行缩进列出 URL，**每条最多 3 个**，基准域名 `https://baojie.github.io/shiji-kb/`；纯脚本/文档/小修不列 URL
3. **按 SKILL_10b §4 撰写改动意义**（三问各 1-3 句，合计 150-200 字）
4. **插入日志开头**：在第一行标题后插入 `## 微信群通知` 代码块
5. **汇报**：`✅ D 已补齐（N 次提交）`

### 6. 汇总输出

```
补齐完成：
- 2026-04-20 ✅
- 2026-04-21 ✅

共 2 天，未执行 git add/commit。
```

## 带参数 `/daily YYYY-MM-DD` 执行步骤

跳过扫描和清单确认，直接对该日期执行「第 5 步：逐日补齐」流程。允许指定今天。

## 数据统计参考命令（SKILL_10b §5 摘要）

```bash
# 章节数
git log --since="D 07:00" --until="D+1 07:00" \
  --name-only --format="" | grep "chapter_md.*tagged.md" | sort -u | wc -l

# 总文件数
git log --since="D 07:00" --until="D+1 07:00" \
  --name-only --format="" | sort -u | wc -l

# 新增 SKILL/README/SPEC
git log --since="D 07:00" --until="D+1 07:00" \
  --diff-filter=A --name-only | grep -E "SKILL|README|SPEC"
```

## 插入格式（参照 SKILL_10b）

在日志第一行标题后追加：

```markdown
# 工作日志 D

## 微信群通知

​```
【史记知识库 D】

· 核心工作1（含数字）
  → https://baojie.github.io/shiji-kb/path/to/page.html  （可选：最多3个）
· 核心工作2
...
· 提交N次代码

为什么做这些事？

（动机和背景，1-3句）

要解决什么问题？

（痛点和目标，1-3句）

会影响什么最终交付物？

（成果和价值，1-3句）
​```

---

（原有自动生成内容）
```

## 输出后

- 只写日志文件，不触碰 git
- 若某日 git 有提交但当日实际是「无提交日」（7:00 边界过滤后为 0），按 SKILL_10b §3.3 太史公曰处理
- 有疑问不确定时询问用户，不要自作主张归并或跳过

## 相关资源

- 骨架生成脚本：`logs/daily/generate_log.py`
- 完整规范：`skills/SKILL_10b_每日工作日志维护.md`
- 太史公文风：`labs/sima-qian-style/SKILL.md`
