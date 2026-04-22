# Bot Lint Agent 设计文档

创建日期：2026-04-23

---

## 一、问题背景

Wiki 页面中的引文使用 `NNN-MMM` 格式引用《史记》段落（如 `101-023`），
但这些 PN 是手工填写的，容易出错（错写 PN、PN 随标注重排后过时等）。
需要一个后台 agent 自动检查并修复，同时通过 butler revision 留下记录。

---

## 二、边界划分

| 操作对象 | Bot 权限 | 原因 |
|---|---|---|
| `chapter_md/*.tagged.md` | **只读** — 检测报告，不修改 | CLAUDE.md 禁止自动修改标注文件 |
| `wiki/public/pages/*.md` | **可修改** — 通过 butler revision | Wiki 页面由 butler 体系管理 |
| `logs/wiki_butler/actions.jsonl` | 追加审计条目 | 与 butler 共用同一审计日志 |
| `logs/wiki_butler/queue.md` | 追加待审条目 | 低置信度问题送人工 |
| `logs/lint/bot-lint-*.json` | 写入 L1 报告 | 章节问题离线报告 |

---

## 三、两类任务

### L1 — 章节文本完整性（只读）

- 调用现有 `lint_text_integrity.check_chapter()`
- 检测：原文字符丢失/多余、嵌套标注（`〖〖...〗〗`）
- **不自动修复**，只写 `logs/lint/bot-lint-YYYY-MM-DD.json`

```bash
python scripts/bot_lint_agent.py --task l1
python scripts/bot_lint_agent.py --task l1 --chapter 101
```

### L2 — Wiki 引文 PN 核验（可自动修复）

- 扫描 wiki 页面中 blockquote + citation 格式：
  ```
  > 引文文字（[[NNN_章节名|NNN-MMM]]）
  > 引文文字（NNN-MMM意旨）
  ```
- 用 `find_pn_for_quote.find_pn()` 逆向验证引文和 PN 的对应
- 置信度 ≥ 0.95 → 自动修复 + 记录 revision
- 置信度 < 0.95 → 追加到 `queue.md` 待人工审查

```bash
python scripts/bot_lint_agent.py --task l2
python scripts/bot_lint_agent.py --task l2 --page 晁错
python scripts/bot_lint_agent.py --task l2 --dry-run   # 预览
```

---

## 四、数据流

```
bot_lint_agent.py
  │
  ├─ L1: lint_text_integrity.check_chapter()
  │       └─ logs/lint/bot-lint-YYYY-MM-DD.json
  │
  └─ L2: WikiCitationLinter
          ├─ scan_page_citations()    提取 blockquote + PN
          ├─ verify_citations()       find_pn 交叉核验
          │
          ├─ [conf ≥ 0.95]
          │   ├─ apply_fix()          修改 wiki 页面文件
          │   ├─ record_revision.py   写入 revision（author=bot-lint）
          │   └─ actions.jsonl        追加审计条目
          │
          └─ [conf < 0.95]
              └─ queue.md             追加待审条目
```

---

## 五、Butler Revision 集成

Bot 编辑走与 butler 完全相同的 revision 通道：

```bash
# bot_lint_agent.py 内部调用：
python3 wiki/scripts/butler/record_revision.py <slug> \
    --summary "bot-lint/citation-fix: 晁错 （101-023）→157 (conf=1.00)" \
    --author bot-lint
```

产出三个文件（与人工 butler 完全一致）：
1. `wiki/public/history/<slug>/<rev_id>.md` — 内容副本
2. `wiki/public/history/<slug>.json` — per-page 索引
3. `wiki/public/recent.json` — 全局最近

`actions.jsonl` 中的审计条目格式：
```json
{
  "ts": "2026-04-23T...",
  "agent": "bot-lint",
  "task": "l2",
  "action": "citation-quote_mismatch",
  "target": "wiki/public/pages/晁错.md",
  "issue": "（[[101_袁盎晁错列传|101-023]]） (L67)",
  "old_text": "（[[101_袁盎晁错列传|101-023]]）",
  "new_text": "（[[101_袁盎晁错列传|101-157]]）",
  "confidence": 1.0,
  "verdict": "accept",
  "dry_run": false
}
```

---

## 六、依赖关系

| 依赖 | 用途 |
|---|---|
| `scripts/find_pn_for_quote.py` | PN 索引 + 模糊匹配（本次新建） |
| `scripts/lint_text_integrity.py` | L1 章节文本检查 |
| `wiki/scripts/butler/record_revision.py` | 写 wiki revision 记录 |
| `scripts/wiki_revisions.py` | revision 数据模型 |
| `logs/wiki_butler/actions.jsonl` | 共用审计日志 |

---

## 七、调度建议

Bot 本身无状态，可在任何时候安全重跑。推荐两种运行方式：

**方式 A：手动触发**（适合当前阶段）
```bash
python scripts/bot_lint_agent.py --dry-run    # 先预览
python scripts/bot_lint_agent.py              # 执行
```

**方式 B：定时运行**（后续用 Claude Code CronCreate 设置）
```
每天 03:00 运行 L1（章节 lint 报告）
每次 wiki 页面大量更新后运行 L2（引文核验）
```

---

## 八、已知局限

1. **citation 格式覆盖不全**：目前只处理 blockquote（`>`）行末的引用，
   正文中间的 `（NNN-MMM）` 尚未处理（可扩展 `_CITE_RE`）。

2. **PN 格式假设**：wiki 中 `NNN-MMM` 只覆盖整数 PN（如 `101-023`），
   不覆盖层级 PN（如 `101-4.1`）。层级引用通常用 `§4.1` 格式，不在此处理。

3. **L1 不自动修复**：章节文本差异需要人工判断，bot 只报告。

---

## 九、已验证的真实 Bug

首次 dry-run（2026-04-23，晁错页面）：

| 页面 | 原引用 | 正确 PN | 置信度 | 状态 |
|---|---|---|---|---|
| 晁错 | `101-023` | `101-157` | 1.00 | 自动修复 |
| 晁错 | (另一条) | 待查 | < 0.95 | 送 queue |

验证：PN [23] 在章节 101 是"上弗听，遂行之"；PN [157] 是太史公曰
"晁错为家令时，数言事不用…"，与引文完全吻合。
