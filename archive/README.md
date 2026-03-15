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

---

## 维基文库参考版本

从维基文库 epub 提取的繁体 HTML 版本，可作为校勘参考和标注学习素材。

| 目录 | 内容 | 文件数 | 来源 |
|------|------|--------|------|
| `wikisource_shiji/` | 史记130卷（繁体） | 130 + index.html | [維基文庫·史記](https://zh.wikisource.org/wiki/史記) |
| `wikisource_sanjia/` | 史记三家注130卷（繁体） | 130 + index.html | [維基文庫·史記三家註](https://zh.wikisource.org/wiki/史記三家註) |
| `史記.epub` | 维基文库 epub 原始文件 | 1 | 维基文库 |
| `史記三家註.epub` | 维基文库 epub 原始文件 | 1 | 维基文库 |

### 标注特点

**wikisource_shiji/**：
- 维基百科超链接标注实体（人名、地名等链接到对应维基百科条目）
- 维基文库编者添加的小节标题（非原文）
- 含校勘记

**wikisource_sanjia/**：

4种实体标注样式（全书统计）：

| 样式 | 数量 | 实体类型 | 说明 |
|------|------|---------|------|
| 实线下划线 | 11,730 | 人名 + 地名（混合） | 人名为主（注释者徐广2,251/韦昭618/郑玄614等），地名约1,390处（含州/縣/山/河等特征字） |
| 波浪下划线 | 1,198 | 典籍/书名 | 地理志(464)、系本(177)、百官表(78)、大戴禮(38)等 |
| 删除线 | 512 | 校勘异文 | 标示被校改的原文字（异体字/误字） |
| 点线红底 | 513 | 校勘注记 | 与删除线配合，标示校勘替换文字 |

三家注结构标注：
- 集解（绿色标签）、索隐（粉色标签）、正义（褐色标签）
- 注释正文与原文交织排列

**可利用价值**：
- 实线下划线实体 → 按地名特征字分离人名/地名 → 与 `entity_index.json` 比对发现遗漏
- 波浪下划线书名 → 扩充典籍《》词表
- 删除线+点线红底校勘对 → 辅助校勘（SKILL_01）

### 提取脚本

```bash
python scripts/extract_epub_to_html.py
```

每个目录含 `index.html`（按本纪/表/书/世家/列传分类的目录页）和 `styles.css`，各章间有上下卷导航，可直接在浏览器打开。

---

## 注意

- 本目录所有文件均为**只读归档**，不应修改
- 当前生产流程的起点是 `chapter_md/*.tagged.md`
- `chapter_numbered/` 仍被以下脚本用于文本比对：
  - `kg/entities/scripts/validate_tagging.py`
  - `kg/entities/scripts/validate_all_chapters.py`
  - `kg/entities/scripts/find_differences.py`
  - `kg/entities/scripts/report_differences.py`
