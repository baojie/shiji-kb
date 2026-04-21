# 史记 · 点校本二十四史

本目录存放《史记》正文，**底本为"点校本二十四史"**（中华书局 1959 年起出版的整理本）——现代学术界最通行的《史记》校勘本。

> **"点校本"**（點校本）指中华书局组织顾颉刚、聂崇岐等学者整理校勘的《二十四史》整理本。采用现代标点、分段，是研究《史记》的标准底本。文本保持**繁体原貌**，不做简化处理。

## 来源

- **项目**：Yann-Chen/Twenty-Four-Histories
- **仓库**：<https://github.com/Yann-Chen/Twenty-Four-Histories>
- **源路径**：`Twenty-Four-Histories/史記/*.tex`
- **导入脚本**：[`scripts/import_traditional_shiji.py`](../../../scripts/import_traditional_shiji.py)

## 文件范围

共 **120 章**：
- 本纪 001-012（12 章）
- 书 023-030（8 章）
- 世家 031-060（30 章）
- 列传 061-130（70 章）

**缺**：十表（013-022，10 章）——源仓库未收录表格类内容。

## 文件格式

- 文件名：`NNN_章节名_点校本.txt`
  - `NNN` 编号与 [`chapter_md/NNN_*.tagged.md`](../../../chapter_md/) 对齐
  - 章节名使用**简体**（便于文件索引统一），**正文保留繁体原貌**
- 头部注明来源与原繁体章名
- 按自然段分段（空行分隔）

## 繁简名差异（命名对齐）

opencc `t2s` 对以下章节转换后与本库命名不同，脚本 `NAME_ALIASES` 做人工兜底：

| 繁体（源） | opencc 转换 | 本库命名 |
|----|----|----|
| 張耳陳餘列傳 | 张耳陈余列传 | 张耳陈馀列传 |
| 袁盎鼂錯列傳 | 袁盎鼌错列传 | 袁盎晁错列传 |

## 更新机制

当源仓库更新时重新运行：

```bash
python scripts/import_traditional_shiji.py
```

依赖 `opencc-python-reimplemented`（已安装）。脚本会覆盖重新生成所有文件。
