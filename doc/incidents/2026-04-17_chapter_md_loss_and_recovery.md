# 2026-04-17 事故复盘：`chapter_md/` 081-130 章丢失与恢复

> **事故类型**：工作区数据丢失（50 章 tagged.md 被误操作清掉或退化至旧版本）
> **影响范围**：`chapter_md/081_廉颇蔺相如列传.tagged.md` ~ `chapter_md/130_太史公自序.tagged.md`，共 **50 章**
> **修复结果**：全部恢复到事故前最新版本（最终 commit `8cba0f78`、`d4b50045`）
> **决定性工具**：[`scripts/git_restore_latest_blob.py`](../../scripts/git_restore_latest_blob.py)（按 blob 创建时间取最新者自动回写）
> **可复用脚本**：3 个（改名归入 `scripts/git_*.py`），其余 8 个一次性脚本已删除

---

## 一、事故描述

### 1.1 影响范围

- 50 章 `chapter_md/NNN_*.tagged.md`（NNN ∈ [081, 130]）被退化到过旧状态或完全丢失
- 这 50 章都有当轮（第四轮）的标注修正成果，退化后这些修正丢失
- 081-130 是列传末段与太史公自序，信息密度高（每章约 3k-15k 字，含大量人名/时间/动词标注）

### 1.2 事故根因（精确还原，据 `git reflog` 复核）

**触发路径：amend 已推送的 commit，后续 `git pull` 在 checkout 阶段覆盖了未提交的工作区。**

具体事件序列（SHA 与时间均由 reflog 获取）：

| # | 时间 | commit / 动作 | 工作区状态 |
|---|------|--------------|-----------|
| 1 | 05:47:11 | `4d8af2fd` commit "新增君号索引专项" | 081-130 反思改动**未 staged** |
| 2 | 05:55:38 | `f957237b` commit（同 message，重复提交） | 同上，且**推送到 GitHub** |
| 3 | **07:37:04** | **`0d03260d`** — `git commit --amend` 改 message 为"第四轮实体反思HTML重建 + 新增君号索引专项" | 未提交的 081-130 反思仍在工作区 |
| 4 | **07:37:48** | **`git pull --tags origin main`** — reflog 记 `checkout f957237ba45e269c3934df34f88a6b35bb10e437` | **工作区被覆盖回 `f957237b` 的 tree**，081-130 反思丢失 |
| 5 | 07:39:41 | `git reset 0d03260d` | HEAD 回到 amend commit，工作区已是覆盖后的状态 |

**两个验证要点**：

```bash
# amend 只改 message，不改 tree（f957237b 与 0d03260d 树完全一致）
$ git diff --stat f957237b 0d03260d
（空输出）

# 两个 commit 都没有 081-130 的 chapter_md 改动
$ git show --name-only 0d03260d | grep chapter_md/
（空输出——反思工作全在未提交的 working tree 里）
```

**致命点解读**：

- **amend（`0d03260d`）本身无害**：它与 `f957237b` 内容完全相同，只是 SHA + message 不同。
- **pull 是凶手**：local HEAD (`0d03260d`) 与 remote (`f957237b`) SHA 不一致，`git pull --tags` 启动了 checkout/merge 流程。在 checkout 阶段，**git 为了对齐远程 tree，把工作区文件按 `f957237b` 的 tree 写回**——而 `f957237b` 的 tree 不包含未提交的 081-130 反思，于是这些改动被 working-tree-level 覆盖。
- **reset 救不了**：07:39:41 的 `git reset 0d03260d` 只移动 HEAD 指针，对工作区不作处理，丢失的内容无法通过 reset 找回。

**为什么 blob 还在**：AI 反思流程中，每章 `.tagged.md` 在过去几小时被反复读写；每次文件系统写入时，git 的内部机制（包括 `git add` 的预操作、或被 hook/工具触发的 `git hash-object`）曾在 `.git/objects/` 里留下对应的 loose/pack blob。即便工作区被覆盖、blob 从未进入 tree，blob 对象本身仍保留，直到 `git gc --prune` 回收。恢复即用 `git cat-file --batch-all-objects` 把这些"孤儿 blob"捞出来按 btime 取最新者。

**核心教训**：

- **已推送的 commit，`--amend` 是陷阱**：amend 会让 local/remote 分叉，下一次 `git pull` 就会触发 checkout/merge 路径。
- 如真要改已推送 commit 的 message，只有两条安全路线：
  1. `git push --force-with-lease`（单向覆盖远程，完全跳过 pull）
  2. 加新 commit 补说明（完全不 amend）
- **禁止路线**：amend 后再 `git pull`——checkout 会覆盖未提交的工作区，不给任何 warning。
- 任何 `--amend` / `rebase` / `pull` 前，`git stash --include-untracked -m safety` 是唯一兜底。

与 CLAUDE.md 中记载的两次 `git checkout` 事故相比，本次事故**更隐蔽**——不是显式运行破坏性命令，而是 **`git pull` 隐式触发的 working-tree 重置**：

> 2026-04-01：擅自使用 `git checkout` 恢复 69 个文件，险些丢失所有正在进行的修改
> 2026-04-02：再次擅自使用 `git checkout` 恢复 053-080 章节，覆盖了数小时的工作成果
> **2026-04-17：amend 已推送 commit（`f957237b`→`0d03260d`）+ `git pull --tags` → 工作区被 checkout 覆盖，50 章未提交反思丢失**

### 1.3 为什么仍可恢复

**关键条件**：tagged.md 文件在此前的工作流里被频繁读写，每次写入都会在 git object database 中留下一份 blob（即便从未 `git add` 或 `git commit`）。

这些"散落"的 blob 存在于两处：
- **pack 内**：`git gc` / `git push` 等操作打包进 `.git/objects/pack/*.pack`
- **loose**：`.git/objects/xx/yyyy...`（未打包的松散对象）

只要 **blob 的 SHA 还在**，就能找回历史内容。`git fsck --lost-found` 可以把"无引用"的 loose blob 复制到 `.git/lost-found/other/`，但覆盖范围有限，仅发现约 30+ 候选；真正完整的候选来自 `git cat-file --batch-all-objects`（枚举全部 pack+loose 对象）。

---

## 二、恢复过程（7 个阶段）

### 阶段 A：扫描候选（成功）

**工具**：
- `scripts/rescue_dump.py`（后改名 `git_lost_found_extract.py`）— 从 `.git/lost-found/other/` 按章节首行标题匹配提取，按章归类到 `backups/rescue_20260417/NNN_*/`，并生成 `_SUMMARY.md` 列候选特征（大小/标注数/引号类型/与 HEAD 差异行数）
- `scripts/rescue_scan_all_blobs.py`（后改名 `git_scan_all_blobs.py`）— 用 `git cat-file --batch-all-objects` 枚举全库 blob，扩展候选池至 pack 对象
- `scripts/rescue_scan_all_objects.py`（已删）— 仅扫 loose 的变体，与上者重叠，删除

**结果**：44 章各获 3-5 个候选 blob，写入 `backups/rescue_20260417/NNN_*/cand_0N_*.md`。

### 阶段 B：按"最大 blob"选取（失败）

**假设**：最大的 blob 内容最丰富，最可能是最终版。
**工具**：`scripts/rescue_apply.py`（已删）
**问题**：对 082_田单列传等章失效——最大 blob 恰是某次中间状态（标注了一半的试验版），而非真正的最终版。
**教训**：文件大小 ≠ 完整性。AI 标注工作流中，中间态可能字数更多（因冗余标注、未消歧），反而是"最胖的垃圾"。

### 阶段 C：按"接近 anchor 时间"选取（失败）

**假设**：082_田单列传 `cand_02` 有明确时间戳 Apr 17 03:21:20，且该版本人工确认正确。其他章节选 birth time 最接近此 anchor 的 blob。
**工具**：`scripts/rescue_by_btime.py`（已删）
**问题**：不同章节的修正时间分布不均匀，"最接近"并不等于"最新"。有章节的最终版在 anchor 之后 1 小时才产生，被误过滤掉。
**教训**：时间 anchor 需要 **向未来取 max**，不是取 nearest。

### 阶段 D：按"最新 btime"选取（✓ 成功）

**假设**：每章最后一次写入工作区时，git 产生的 blob 有最晚的 birth time；即便后来被覆盖，blob 本身仍在 git objects 里。
**工具**：[`scripts/git_restore_latest_blob.py`](../../scripts/git_restore_latest_blob.py)（原名 `rescue_latest_blob.py`）

核心逻辑（约 40 行关键代码）：

```python
# 1. 枚举所有 blob
git cat-file --batch-check --batch-all-objects --unordered

# 2. 按 size 过滤（tagged.md 合理区间 1KB-200KB）
if 1000 < size < 200000: candidates.append(hash)

# 3. 读首行，匹配章节号
m = re.match(r"^#\s+(?:\[\d+\]\s+)?(.+?)\s*$", first_line)

# 4. 按章汇集候选，取 birth time 最新者
blob_btime = stat("-c", "%W", ".git/objects/xx/yyyy...")
candidates.sort(key=lambda x: -x.btime)
winner = candidates[0]

# 5. 写回前备份 HEAD 到 backups/pre_latest_restore/
shutil.copy(current_chapter_file, backup_dir)

# 6. 写回，附带 3 种 PUA 字符迁移
content = git_cat_file(winner.hash)
content = content.replace('〖\u2018', '〖◆')    # 旧邦国标记
content = re.sub(r'〖：', '〖:', content)        # 全角冒号 OCR 残留
content = re.sub(r'^：：：', ':::', content, flags=re.M)
write(target, content)
```

**结果**：44/50 章一次恢复成功。

### 阶段 E：处理 6 章无 `[0]` 前缀（辅助）

**问题**：121_儒林列传、122_酷吏列传、123_大宛列传、124_游侠列传、125_佞幸列传、129_货殖列传 6 章首行是 `# 儒林列传` 而非 `# [0] 儒林列传`，正则 `^#\s+\[\d+\]\s+(.+)` 匹配失败。

**工具**：
- `scripts/rescue_scan_missing_6.py`（已删）— 专为 6 章放宽首行正则
- `scripts/rescue_6_chapters.py`（已删）— 6 章 apply

**教训**：匹配正则要能兼容 `# [N] 标题` 与 `# 标题` 两种格式。现行 `git_restore_latest_blob.py` 的正则 `^#\s+(?:\[\d+\]\s+)?(.+?)\s*$` 已涵盖（`\[\d+\]` 部分变为可选）。

### 阶段 F：格式迁移（一次性）

恢复的旧 blob 里混有 PUA 字符（早期标注用过的非标准符号）：

| 旧格式 | 新格式 | 来源 |
|--------|--------|------|
| `〖'X〗`（U+2018） | `〖◆X〗`（U+25C6） | 早期邦国标记 |
| `〖：X〗`（全角冒号） | `〖:X〗`（半角冒号） | OCR 残留 |
| 行首 `：：：` | `:::` | 围栏块标记 OCR 残留 |

**工具**：
- `scripts/rescue_fix_fullwidth.py`（已删）
- `scripts/rescue_fix_old_state_marker.py`（已删）

这两个修复已**内联**进 `git_restore_latest_blob.py` 的写回阶段（line 100-102），无需单独脚本。

### 阶段 G：验证 + 提交

- `python scripts/lint_text_integrity.py` 确认 50 章 0 实质差异
- 提交：
  - `8cba0f78` — 恢复第四轮反思 081-090 章标注及反思报告
  - `d4b50045` — 恢复第四轮反思 091-130 章 + 政治动词体系批量补标

---

## 三、失败策略与成功策略对比

| 策略 | 脚本 | 假设 | 结果 |
|------|------|------|------|
| 最大 blob | rescue_apply.py | 最大=最完整 | ✗ 中间态可能最胖 |
| 最近 anchor | rescue_by_btime.py | anchor 时间附近=目标版 | ✗ 漏掉 anchor 之后的版本 |
| **最新 btime** | **git_restore_latest_blob.py** | **最后写入的 blob 就是目标版** | **✓ 一次性 44/50 章成功** |
| 按首行模糊匹配 | rescue_scan_missing_6.py | `[0]` 前缀可选 | ✓（已并入主工具） |

**核心洞察**：`git` 会为每次工作区写入生成 blob 并保留（直到 `git gc --prune`）。**最晚的 blob 就是最后一次合法状态**。无需猜 anchor、无需按大小判断、无需人工审 candidate——直接取 max(btime)。

---

## 四、可复用的恢复 Playbook

下次再遇类似事故，按以下顺序操作。**所有工具都不使用 `git checkout` / `git restore`**（见 CLAUDE.md 血泪条目）。

### Step 1：确认有 blob 可恢复

```bash
git fsck --lost-found 2>&1 | tail        # 看有多少 dangling blob
ls .git/objects/pack/ | wc -l            # pack 文件数
```

如果 `git fsck` 报告大量 dangling blob，且 pack 里也有对应对象——基本可恢复。

### Step 2：扫全库候选

```bash
# 先用 lost-found（快）
python scripts/git_lost_found_extract.py

# 若候选不足，加全库扫描（慢但全）
python scripts/git_scan_all_blobs.py
```

输出：`backups/rescue_<date>/NNN_*/cand_*.md`。

### Step 3：按最新 btime 自动回写（主力工具）

```bash
python scripts/git_restore_latest_blob.py
```

- 默认处理 081-130；改范围编辑 `target_nums = {f"{n:03d}" for n in range(81, 131)}`
- 自动备份 HEAD 到 `backups/pre_latest_restore/NNN_*.tagged.md`
- 自动迁移 3 类 PUA 字符

### Step 4：验证

```bash
python scripts/lint_text_integrity.py    # 全书完整性（目标：0 实质差异）
python scripts/lint_markdown.py          # 格式
```

如有新增差异，回查 `backups/rescue_<date>/NNN_*/_SUMMARY.md` 的 top-3 候选手动复核。

### Step 5：提交

```bash
git add chapter_md/0{81..130}*.tagged.md
git commit -m "恢复 NNN-NNN 章：按最新 blob btime"
```

---

## 五、历史教训与制度改进

### 5.1 CLAUDE.md 已有的约束（事故前）

- ⛔ 绝对禁止 `git checkout <file>` / `git restore <file>` / `git reset --hard`
- ⛔ 绝对禁止 `git add -A` / `git add .`
- 写入前必须验证 `lint_text_integrity.py`

### 5.2 事故暴露的新约束

**A. `git fsck --lost-found` 的覆盖不全**
- 仅扫 loose，不扫 pack
- 依赖 `git gc --prune` 的时间窗口（默认 2 周，过期后 blob 真正消失）
- 教训：重要标注工作后尽早 `commit`，别只存工作区
- 工具：`git_scan_all_blobs.py` 作为补充（用 `--batch-all-objects` 扫全）

**B. 最大 blob 不等于目标版**
- AI 生成的中间态可能比最终版更长
- 策略：**永远按 btime 取最新**，不按 size

**C. 时间 anchor 不能用"最接近"**
- 不同章节的修正时间分布不同
- 策略：**向未来取 max**（`sort(key=-btime)[0]`）

**D. 恢复前必须备份当前 HEAD**
- 即使 HEAD 是"坏状态"，里面也可能有未及记录的修改
- `git_restore_latest_blob.py` 已内建 `backups/pre_latest_restore/` 备份

### 5.3 建议的长期防御

| 措施 | 针对 | 状态 |
|------|------|------|
| **已推送 commit 不改 message**（要改就加新 commit 补说明） | 本次事故直接原因 | ⚠ **最优先**，写入 CLAUDE.md |
| 若必须改已推送 commit，用 `git push --force-with-lease` 覆盖远程，**绝不 merge/pull 自己 amend 过的祖先** | 本次事故直接原因 | ⚠ 建议 |
| 任何 `commit --amend` / `rebase` / `merge` 前先 `git stash --include-untracked -m "safety"` | 通用防御 | ⚠ 建议养成习惯 |
| 定期 commit（≤ 1 天 1 次）关键 tagged.md 改动 | 减小 blob 丢失风险 | ⚠ 建议执行 |
| `git config gc.pruneExpire 30.days`（延长 blob 保留期） | 兜底 | ⚠ 建议配置 |
| 禁用所有 `git checkout`/`git restore` 的脚本直接调用 | 04-01/04-02 事故 | ✓ 已写入 CLAUDE.md |

---

## 六、保留的工具清单

2026-04-18 事后清理，删除 8 个一次性脚本（共 ~720 行），保留 3 个通用工具：

| 脚本 | 作用 | 适用场景 |
|------|------|---------|
| [`scripts/git_lost_found_extract.py`](../../scripts/git_lost_found_extract.py) | 从 `.git/lost-found/` 按章提取候选 blob | 事故首选（快） |
| [`scripts/git_scan_all_blobs.py`](../../scripts/git_scan_all_blobs.py) | `cat-file --batch-all-objects` 扫全库（pack+loose） | lost-found 不够时 |
| [`scripts/git_restore_latest_blob.py`](../../scripts/git_restore_latest_blob.py) | 按 btime 最新自动回写 + 备份 HEAD + PUA 迁移 | **主力恢复工具** |

---

## 七、附录：事故时间线

| 时间 | commit | 事件 |
|------|--------|------|
| 04-17 05:07-05:47 | d74faa11 / 4d8af2fd / f54d09e9 | 第四轮反思 071-080 + 散文集扩容 + 君号索引 commits（081-130 反思**未 commit**，在 working tree） |
| 04-17 05:55 | **f957237b** | commit "新增君号索引专项"（**推送到 GitHub**） |
| 04-17 07:37:04 | **0d03260d** | `git commit --amend` 改 message（tree 不变） |
| 04-17 07:37:48 | — | `git pull --tags origin main` → checkout f957237b → **working tree 被覆盖，081-130 反思丢失** |
| 04-17 07:39:41 | 0d03260d | `git reset 0d03260d` 移动 HEAD，但 working tree 已无法挽回 |
| 04-17 13:31:58 | **8cba0f78** | "恢复第四轮反思 081-090 章标注及反思报告" — 第一批恢复 commit |
| 04-18 02:50:47 | **d4b50045** | "恢复第四轮反思 091-130 章 + 政治动词体系批量补标" — 第二批恢复 commit |
| 04-18 05:13 | — | 清理 rescue 脚本，保留 3 个 `git_*` 通用工具 |
| 04-18 05:14 | — | 写本复盘文档 |
| 2026-04-17 下午 | 尝试 lost-found 提取 → 44 章候选 |
| 2026-04-17 下午 | 尝试最大 blob 策略 → 部分章失败（082 等） |
| 2026-04-17 下午 | 尝试 btime anchor 策略 → 失败 |
| 2026-04-17 晚 | 改用 btime 最新策略 → 44 章一次成功 |
| 2026-04-17 晚 | 处理 6 章无 `[0]` 前缀（121-125, 129） |
| 2026-04-17 晚 | lint_text_integrity 0 差异；提交 `8cba0f78`、`d4b50045` |
| 2026-04-18 凌晨 | 清理 rescue 脚本，保留 3 个通用工具改名入 `git_*` |
| 2026-04-18 凌晨 | 写本复盘文档 |

---

**文档版本**：v1.0
**创建日期**：2026-04-18
**作者**：Claude Agent（追溯记录）
**相关**：
- `scripts/git_restore_latest_blob.py`（主工具）
- CLAUDE.md §禁止破坏性 Git 操作
- `skills/SKILL_10c_Git代码版本管理规范.md`（若存在）
