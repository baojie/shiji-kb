# logs/ 目录说明

本目录**仅**存放机器自动生成的 IT 性日志（脚本输出、运行记录、队列状态）。

**铁律**：人类可读的工作文档（反思记录、分析报告、文本整理记录）一律放 `doc/`，不得放在此目录。

## 目录结构

```
logs/
├── daily/           # 每日工作日志（特例保留）
├── lint/            # 脚本运行日志与校验结果（IT）
├── runs/            # 自动化运行完成记录（IT）
└── event_import/    # 队列状态文件（仅 JSON，IT）
```

---

## 各子目录说明

### `daily/` - 每日工作日志

**用途**：记录每日工作进展、commit统计、任务完成情况

**文件命名**：`YYYY-MM-DD.md`

**生成方式**：
```bash
python logs/daily/generate_log.py YYYY-MM-DD
```

**参考规范**：[`SKILL_10b_每日工作日志维护.md`](../skills/SKILL_10b_每日工作日志维护.md)

---

### `lint/` - 脚本运行日志与校验结果（IT）

**用途**：存放自动化校验脚本的运行日志（机器生成，非人类工作文档）

**典型文件**：
- `lint_text_integrity_*.txt` - 文本完整性校验日志（按章节编号命名）
- `lint_text_integrity_chapter_md/` - 按章节组织的校验结果
- `pn_lint_*.txt` - PN 标注校验输出
- `symbol_conflicts_*.txt` - 符号冲突检测输出

**生成方式**：
```bash
python scripts/lint_text_integrity.py
```

---

### `runs/` - 自动化运行完成记录（IT）

**用途**：存放自动化流程的完成状态记录

---

### `event_import/` - 队列状态文件（IT）

**用途**：存放事件导入流程的队列状态 JSON 文件

**⚠️ 注意**：此目录只保留 JSON 队列文件，可执行脚本已迁移至 `scripts/import/`。

**保留文件**：
- `queue.json` - 当前队列状态
- `queue.md` - 队列摘要
- `pn_verify_queue.json` - PN 验证队列
- `event_groups.json`, `events_parsed.json` - 事件数据

---

## ❌ 不应放在 logs/ 的内容及去向

| 内容类型 | 正确位置 |
|---------|---------|
| Agent 反思记录 | `doc/reflection/` 或 `doc/entities/` |
| 文本整理记录（curation）| `doc/curation/` |
| 数据分析报告（Markdown）| `doc/analysis/` |
| 成本报告（Markdown）| `doc/reports/` |
| 导入脚本（.py）| `scripts/import/` |

---

## 相关规范

- [SKILL_10b_每日工作日志维护](../skills/SKILL_10b_每日工作日志维护.md)
- [SKILL_10e_文件组织与目录结构](../skills/SKILL_10e_文件组织与目录结构.md)

---

最后更新：2026-05-14
