# archive/ — 文本处理历史阶段

本目录保存《史记》原始文本从获取到标注就绪的各处理阶段中间产物，供溯源参考，不参与当前生产流程。

---

## 管线阶段

```
史记.txt
  │  单文件原始文本（来源：ctext.org）
  │
  ▼
chapter/
  │  按130章分割的纯文本（无段落编号）
  │  脚本：temp/tools/split_chapters.py（历史脚本）
  │
  ▼
chapter_improved/
  │  改善版分章文本（修正断章错误、统一标题格式）
  │
  ▼
chapter_numbered/
  │  130个 .txt 文件，加入段落编号 [1] [2] [1.1] ...
  │  脚本：temp/tools/add_numbering.py（历史脚本）
  │
  ▼
chapter_md/  （项目根目录，当前工作目录）
     130个 *.tagged.md：11类实体标注 + 小节划分
```

## 各目录说明

| 目录 | 内容 | 文件数 | 格式 |
|------|------|--------|------|
| `史记.txt` | 全书单文件原始文本 | 1 | 纯文本 |
| `chapter/` | 按章分割，无任何格式处理 | 130 | `.txt` |
| `chapter_improved/` | 断章修正 + 标题规范化 | 130 | `.txt` |
| `chapter_numbered/` | 加入圣经式段落编号 | 130 | `.txt` |
| `chapter_md_legacy/` | 早期HTML span格式标注（已废弃） | 3 | `.md` |

## 注意

- 本目录所有文件均为**只读归档**，不应修改
- 当前生产流程的起点是 `chapter_md/*.tagged.md`
- `chapter_numbered/` 仍被以下脚本用于文本比对：
  - `kg/entities/scripts/validate_tagging.py`
  - `kg/entities/scripts/validate_all_chapters.py`
  - `kg/entities/scripts/find_differences.py`
  - `kg/entities/scripts/report_differences.py`
