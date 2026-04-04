# SPEC_目录结构与工作流程

**版本**: v1.0
**创建日期**: 2026-03-29
**状态**: 已实施

---

## 一、目录结构规范

### 1.1 总体结构

```
shiji-kb/
├── archive/                              # 所有原始和历史数据
│   ├── sources/                          # 所有底本的不同版本（用于校勘）
│   ├── references/                       # 知识参考资料（不直接用于校勘）
│   └── legacy/                           # 历史版本归档
│
├── curation/                            # 校勘工作区（SKILL_01b 产出）
│   ├── simplified/                       # 校勘本-简体（标准底本）
│   ├── traditional/                      # 校勘本-繁体（平行版本）
│   ├── mapping/                          # 繁简字级映射文件
│   └── reports/                          # 校对报告
│
├── final/                                # 底本终稿（所有改进后的最终版本）
│   ├── simplified/                       # 简体终稿（用于语义分析）
│   ├── traditional/                      # 繁体终稿（用于阅读增强）
│   └── improvements/                     # 改进日志
│
└── chapters/                             # 后续分析（基于 final/）
    ├── *.tagged.md                       # 实体标注
    └── ...
```

### 1.2 详细说明

#### archive/sources/ （底本来源，用于校勘）

```
archive/sources/
├── chapter/                      # 简体分章版（主要底本）
│   ├── 001_五帝本纪.txt
│   └── ...
├── wikisource/                   # 维基文库繁体HTML版
│   ├── 001_五帝本纪.html
│   └── ...
├── siku.txt                      # 四库全书版（整本）
├── traditional.txt               # 繁体纯文本版（整本）
└── sanjia/                       # 维基三家注版
    ├── 001_五帝本纪.html
    └── ...
```

**用途**：SKILL_01b 多版本互校的输入材料

#### archive/references/ （参考资料，不直接用于校勘）

```
archive/references/
├── annotations.txt               # 注释合本
├── maps/                         # 历史地图
├── chronology/                   # 年表
└── research/                     # 考据资料
```

**用途**：知识增强、背景研究，但不参与底本校勘

#### archive/legacy/ （历史版本归档）

```
archive/legacy/
├── chapter_v1/                   # 迁移前的旧底本
├── wikisource_shiji/             # 旧的wikisource目录（改名前）
└── ...
```

**用途**：保留历史版本，便于回溯

#### curation/ （校勘工作区）

```
curation/
├── simplified/                   # 校勘本-简体
│   ├── 001_五帝本纪.txt
│   └── ...
├── traditional/                  # 校勘本-繁体（字级映射）
│   ├── 001_五帝本纪.txt
│   └── ...
├── mapping/                      # 繁简字级映射文件
│   ├── 001.json
│   ├── 001.v1.json               # 历史版本
│   ├── 001.changelog.md          # 映射变更日志
│   └── ...
└── reports/                      # 校对报告
    ├── 001_五帝本纪.md
    └── ...
```

**用途**：SKILL_01b 的输出结果

#### final/ （底本终稿）

```
final/
├── simplified/                   # 简体终稿
│   ├── 001_五帝本纪.txt
│   └── ...
├── traditional/                  # 繁体终稿
│   ├── 001_五帝本纪.txt
│   └── ...
└── improvements/                 # 改进日志
    ├── punctuation.md            # 标点归一化日志
    ├── paragraphs.md             # 段落整合日志
    └── normalization.md          # 其他规范化日志
```

**用途**：后续所有分析的基准文本

#### chapters/ （语义分析）

```
chapters/
├── 001_五帝本纪.tagged.md        # 实体标注
├── 002_夏本纪.tagged.md
└── ...
```

**用途**：基于 `final/simplified/` 进行的语义标注

---

## 二、工作流程

```
【阶段0：准备】
当前目录结构 → 迁移到新结构 → archive/sources/ + archive/legacy/

【阶段1：多版本互校】SKILL_01b
archive/sources/*
  → 对比校勘
  → curation/simplified/ + curation/traditional/
  → 生成 curation/mapping/ + curation/reports/

【阶段2：底本改进】SKILL_01c（新增）
curation/simplified/ + curation/traditional/
  → 标点归一化
  → 段落整合修复
  → 其他文本规范化
  → final/simplified/ + final/traditional/
  → 更新 curation/mapping/ （基于文本变化）

【阶段3：语义分析】SKILL_03a等
final/simplified/
  → 实体标注
  → chapters/*.tagged.md

【阶段4：繁体渲染】（未来）
chapters/*.tagged.md + curation/mapping/
  → 应用繁简映射
  → chapters/*.traditional.tagged.md 或 HTML
```

---

## 三、底本改进规范

### 3.1 标点归一化

**规则**：原文只使用全角标点

| 类型 | 允许 | 禁止 |
|------|------|------|
| 逗号 | ，（U+FF0C） | ,（U+002C） |
| 句号 | 。（U+3002） | .（U+002E） |
| 分号 | ；（U+FF1B） | ;（U+003B） |
| 冒号 | ：（U+FF1A） | :（U+003A） |
| 问号 | ？（U+FF1F） | ?（U+003F） |
| 感叹号 | ！（U+FF01） | !（U+0021） |
| 左双引号 | "（U+201C） | "（U+0022） |
| 右双引号 | "（U+201D） | "（U+0022） |
| 左单引号 | '（U+2018） | '（U+0027） |
| 右单引号 | '（U+2019） | '（U+0027） |

**操作**：
- 扫描 `curation/simplified/` 和 `curation/traditional/`
- 将所有半角标点转换为对应的全角标点
- 记录到 `final/improvements/punctuation.md`

### 3.2 段落整合

**规则**：
1. **修复错误换行**：句子中间不应有换行符
2. **合并断句错误**：错误断开的句子应合并

**示例**：
```
错误：
黄帝者，少典之子，姓公孙
，名曰轩辕。

正确：
黄帝者，少典之子，姓公孙，名曰轩辕。
```

**操作**：
- 人工审核或规则检测
- 记录到 `final/improvements/paragraphs.md`

### 3.3 其他规范化

| 项目 | 规则 | 说明 |
|------|------|------|
| 空格/制表符 | 删除所有空格和制表符 | 古文不使用空格 |
| 换行符 | 统一使用LF（\n） | 禁止CRLF（\r\n） |
| BOM标记 | 删除BOM（U+FEFF） | UTF-8不需要BOM |
| 文件编码 | UTF-8 without BOM | 统一编码 |

**操作**：
- 自动化脚本处理
- 记录到 `final/improvements/normalization.md`

---

## 四、注意事项

### 4.1 兼容性

- **向后兼容**：旧的 `chapter_md/*.tagged.md` 需要基于新的 `final/simplified/` 重新验证
- **工具更新**：所有引用旧路径的脚本需要更新

### 4.2 质量控制

- **人工审核**：底本改进（尤其是段落整合）需要人工抽检
- **映射验证**：每次映射更新后需要运行 `validate_mapping.py`

### 4.3 备份策略

- **迁移前备份**：执行迁移前完整备份当前目录
- **映射版本**：每次映射更新保留历史版本

---

## 五、相关文档

- [SKILL_01_古籍校勘](../../skills/SKILL_01_古籍校勘.md)
- [SKILL_01b_多版本互校底本](../../skills/SKILL_01b_多版本互校底本.md)
- [SKILL_01c_底本改进规范](../../skills/SKILL_01c_底本改进规范.md)（待创建）
- [SPEC_繁简映射方案](./SPEC_繁简映射方案.md)

---

**最后更新**: 2026-04-05
**维护者**: shiji-kb项目组
