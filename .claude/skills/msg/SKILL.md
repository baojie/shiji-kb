---
name: msg
description: 根据 git 缓存区（staged）内容生成中文提交消息草稿。无参数时只看缓存区、不执行 git add；带参数 `/msg X` 时先把与 X 相关的改动 `git add` 到缓存区，再生成消息草稿。始终不执行 git commit。
---

# /msg — 生成 Git 提交消息草稿

## 铁律

1. **不执行 git commit**：只输出消息草稿，等待用户决定是否提交
2. **中文**：提交消息全程使用中文
3. **禁止 `git add -A` / `git add .` / `git add --all`**：只按明确的路径列表添加
4. **分支模式**：
   - **无参数 `/msg`**：只分析 `git diff --cached`，完全忽略未缓存的修改，**不执行 git add**
   - **带参数 `/msg X`**：先把与 X 相关的改动加入缓存区，再按无参数流程生成消息

## 带参数模式 `/msg X` 的执行步骤

1. 运行 `git status --short` 查看当前所有未缓存/已缓存的改动
2. 解析参数 X，确定要加入缓存区的文件列表：
   - **X 是存在的文件或目录路径**（`ls`/`test -e` 能命中）→ 直接 `git add <X>`
   - **X 是主题关键词**（如 `标注修复`、`日志`、`skill`）→ 从 `git status` 的未缓存列表中挑出与主题相关的文件，**显式列出每一个路径**，再执行 `git add <path1> <path2> ...`
3. 向用户展示："本次将加入缓存的文件：" + 路径清单
4. 执行 `git add <明确路径列表>`（**禁止** `-A`/`.`/`--all`）
5. 运行 `git diff --cached --stat` 确认缓存区内容
6. 转入"生成消息"步骤（与无参数模式相同）

## 生成消息步骤（两种模式共用）

1. 运行 `git diff --cached --stat` 查看缓存文件列表
2. 运行 `git diff --cached` 查看具体改动内容
3. 运行 `git log --oneline -5` 了解本项目的 commit message 风格
4. 撰写中文提交消息草稿，以代码块形式展示
5. 生成唯一临时文件名：`/tmp/gitmsg_<YYYYmmdd_HHMMSS>_<sha6>.txt`，其中 sha6 取 `git diff --cached` 内容的 sha256 前 6 位
6. 将消息写入该临时文件
7. 输出可直接执行的 git commit 命令

## 消息格式

```
首行：一句话总结（≤50字，说明做了什么）

模块A:
- 新增/更新/修复/删除 具体内容

模块B:
- ...
```

- 首行说"做了什么"，不写版本号
- 按目录/模块分组
- 区分"新增"、"更新"、"修复"、"删除"

## 输出后

1. 展示消息草稿（代码块）
2. 用 Bash 生成唯一文件名并写入（示例）：
   ```bash
   MSGFILE=$(python3 -c "
   import hashlib, subprocess, datetime
   diff = subprocess.check_output(['git','diff','--cached'])
   h = hashlib.sha256(diff).hexdigest()[:6]
   ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
   print(f'/tmp/gitmsg_{ts}_{h}.txt')
   ")
   ```
   然后用 Write 工具把消息写入 `$MSGFILE` 的值（实际路径）
3. 输出提交命令供用户一键复制执行：

```
git commit -F /tmp/gitmsg_<YYYYmmdd_HHMMSS>_<sha6>.txt
```
（用实际生成的文件名替换占位符）

不主动执行 commit，不主动询问。
