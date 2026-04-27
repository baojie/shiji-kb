---
name: commit
description: 把项目当前所有变更按内容分组，一组一组地调用 /msg 生成提交消息并输出 git commit 命令，由用户逐组执行后再继续下一组。
---

# /commit — 分组提交助手

## 工作原理

每次调用 `/commit` 只处理**一组**变更：

1. 用 `git status` 扫描当前所有未提交变更（staged + unstaged + untracked）
2. 若无变更 → 输出"无未提交变更"并退出
3. 将变更按**内容领域**分组（见"分组策略"）
4. 展示完整分组计划（首次）或当前剩余组（后续调用）
5. 取**第一组**，执行 `/msg` 流程（stage → 生成消息 → 写临时文件）
6. 输出 `git commit -F <tmpfile>` 命令
7. 告知用户执行该命令后再次调用 `/commit` 处理下一组

用户工作流：`/commit` → 执行命令 → `/commit` → 执行命令 → … 直到所有组完成。

## 分组策略

按以下顺序判断，一个文件只属于一组：

| 优先级 | 组名 | 匹配规则 |
|--------|------|----------|
| 1 | **scripts** | `wiki/scripts/` 下的 `.py` / `.sh` |
| 2 | **skills** | `.claude/skills/` 或 `skills/` 下的文件 |
| 3 | **frontend-js** | `wiki/public/js/` 下的 `.js` |
| 4 | **frontend-css** | `wiki/public/css/` 下的文件 |
| 5 | **pages** | `wiki/public/pages/` 下的 `.md` |
| 6 | **history** | `wiki/public/history/` 下的文件 |
| 7 | **logs** | `wiki/logs/` 下的文件 |
| 8 | **docs** | `README.md`、`wiki/doc/`、`docs/` 下的文件 |
| 9 | **config** | `wiki/public/pages.json`、`*.json`（非 pages/history）、`.gitignore` |
| 10 | **other** | 其他所有文件 |

分组后若某组只有 1 个文件且与相邻组强相关，可合并（由 Claude 判断）。

## 执行步骤

### Step 1 — 扫描变更

```bash
git status --short
```

收集所有 `M`、`A`、`D`、`??` 状态的文件路径。

### Step 2 — 分组并展示计划

按分组策略归类，输出如下格式：

```
📦 分组计划（共 N 组）：

[1/N] scripts（3 个文件）
  - wiki/scripts/record_revision.py
  - wiki/scripts/publish.sh
  - wiki/scripts/rebuild_recent.py

[2/N] skills（1 个文件）
  - .claude/skills/wiki/SKILL.md

[3/N] docs（2 个文件）
  - README.md
  - wiki/doc/recent-log.md
```

### Step 3 — 处理第一组

**判断"第一组"**：即 `git status` 中仍有变更的最高优先级组（已完成提交的组不再出现在 status 中）。

对该组执行 `/msg` 流程：

1. `git add <该组所有文件路径>`（逐个显式路径，**禁止** `-A`/`.`）
2. `git diff --cached --stat` 确认缓存区
3. `git diff --cached` 查看具体内容
4. `git log --oneline -5` 了解 commit 风格
5. 撰写中文提交消息草稿
6. 生成唯一临时文件名：
   ```bash
   python3 -c "
   import hashlib, subprocess, datetime
   diff = subprocess.check_output(['git','diff','--cached'])
   h = hashlib.sha256(diff).hexdigest()[:6]
   ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
   print(f'/tmp/gitmsg_{ts}_{h}.txt')
   "
   ```
7. 用 Write 工具将消息写入该路径

### Step 4 — 输出并等待

输出格式：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/N] scripts — 提交消息已写入 /tmp/gitmsg_XXXXXXXX_XXXXXX.txt

<消息草稿全文>

执行：
  git commit -F /tmp/gitmsg_20260427_143521_a3f8c1.txt

完成后再次运行 /commit 处理下一组 [2/N] skills
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

若这是最后一组，替换为"完成后所有变更已提交"。

## 禁止事项

- ❌ 禁止 `git add -A` / `git add .` / `git add --all`
- ❌ 禁止自动执行 `git commit`
- ❌ 禁止一次处理多组（每次调用只处理一组）

## 边界情况

- **缓存区已有内容**：先询问用户是否要先清除（`git restore --staged .`）还是将缓存区内容并入当前组
- **文件跨组**：按优先级表取最高优先级组
- **只有一组**：直接执行，不展示分组计划
