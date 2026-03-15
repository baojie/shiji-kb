# 三Agent并行工作规划

> 将当前TODO中的任务分配给三个Agent并行执行，确保任务之间无文件冲突、无数据依赖。

---

## 一、并行化原则

### 1.1 冲突源分析

Agent之间的冲突来自三种情况：

| 冲突类型 | 示例 | 后果 |
|----------|------|------|
| **文件写冲突** | 两个Agent同时修改同一个 `tagged.md` | git merge冲突，人工解决 |
| **数据依赖** | Agent B需要Agent A的输出作为输入 | Agent B阻塞等待 |
| **索引重建冲突** | 两个Agent都触发 `entity_index.json` 重建 | 后者覆盖前者 |

### 1.2 隔离策略

- **按目录隔离**：每个Agent只写入自己的目录，不触碰其他Agent的输出目录
- **只读共享**：`chapter_md/*.tagged.md`、`entity_index.json` 等基础数据所有Agent可读，但同一时间只有一个Agent可写
- **索引重建放在最后**：需要重建全局索引的操作（实体索引、HTML生成）在所有Agent完成后统一执行
- **按体裁/章节分片**：若多个Agent需要处理 `tagged.md`，按章节范围分片（本纪/世家/列传）

---

## 二、三条工作轨道

```
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│  Agent A: 本体构建    │  │  Agent B: 三家注处理  │  │  Agent C: 阅读体验   │
│  (知识图谱层)         │  │  (数据层)             │  │  (应用层)            │
├─────────────────────┤  ├─────────────────────┤  ├─────────────────────┤
│ 写入:                │  │ 写入:                │  │ 写入:                │
│  kg/*/data/*.ttl     │  │  kg/sanjia/          │  │  docs/css/           │
│  kg/*/data/*_tax.md  │  │  archive/wikisource_*│  │  docs/js/            │
│  ontology/           │  │  scripts/parse_*.py  │  │  app/                │
│                      │  │                      │  │  render_shiji_html.py│
│ 只读:                │  │ 只读:                │  │ 只读:                │
│  entity_index.json   │  │  archive/wikisource_*│  │  chapter_md/*.tagged │
│  chapter_md/*.tagged │  │  entity_index.json   │  │  entity_index.json   │
│                      │  │  chapter_md/*.tagged │  │  kg/events/data/     │
│ 不触碰:              │  │ 不触碰:              │  │ 不触碰:              │
│  docs/ app/ css/     │  │  ontology/ docs/     │  │  ontology/ kg/sanjia │
│  kg/sanjia/          │  │  app/ css/           │  │  kg/*/data/*.ttl     │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

---

## 三、Agent A：本体构建（知识图谱层）

### 工作范围

将已有实体词表构建为分类本体（OWL/RDF），扩展人物本体，构建新类型本体。

### 任务清单

| 序号 | 任务 | 输入（只读） | 输出（写入） | 预估工作量 |
|------|------|------------|------------|-----------|
| A1 | 人物本体收尾 | `entity_index.json` | `kg/entities/data/person.ttl` | 2-3h |
| | - 补全低频人物（count=1,2） | `person_taxonomy.md` | `person_taxonomy.md` 更新 | |
| | - 诸侯18人消歧 | | | |
| | - 疑似误标342人清理 | | | |
| | - 类名后缀冗余修复 | | | |
| A2 | 通用分类树生成器 | `build_person_taxonomy.py` | `kg/scripts/build_taxonomy.py` | 1h |
| | - 抽象为通用工具 | | | |
| A3 | 地名本体构建 | `entity_index.json` | `kg/entities/data/place.ttl` | 4-6h |
| | - 1,800+地名分类 | `chapter_md/*.tagged` | `place_taxonomy.md` | |
| A4 | 官职本体构建 | `entity_index.json` | `kg/entities/data/official.ttl` | 4-6h |
| | - 2,100+官职分类 | `chapter_md/*.tagged` | `official_taxonomy.md` | |
| A5 | 词条简介生成 | `chapter_md/*.tagged` | `kg/*/data/*_summaries.json` | 3-4h |
| | - 人物1,825条优先 | `entity_index.json` | | |

### 执行顺序

```
A1 → A2 → A3 ─┐
               ├→ A5（可在A3/A4任一完成后开始）
          A4 ─┘
```

### 无冲突保证

- 只写入 `kg/*/data/` 下的本体文件（`.ttl`、`_taxonomy.md`、`_summaries.json`）
- 不修改 `chapter_md/`、`docs/`、`app/` 中的任何文件
- 不触发全局索引重建

---

## 四、Agent B：三家注处理（数据层）

### 工作范围

从维基文库三家注HTML中提取结构化数据，构建三家注JSON，提取校勘和实体增量。

### 任务清单

| 序号 | 任务 | 输入（只读） | 输出（写入） | 预估工作量 |
|------|------|------------|------------|-----------|
| B1 | 编写 `parse_sanjia_html.py` | `archive/wikisource_sanjia/*.html` | `scripts/parse_sanjia_html.py` | 2-3h |
| | - 按 `<small>` 分离注文 | | | |
| | - 按颜色标签识别集解/索隐/正义 | | | |
| | - 提取下划线标注实体 | | | |
| | - 提取删除线校勘对 | | | |
| B2 | 批量解析130卷 | B1的脚本 | `kg/sanjia/data/NNN_*.sanjia.json` | 1h |
| B3 | 编写 `match_target_pn.py` | `kg/sanjia/data/*.json` | 更新 `target_pn` 字段 | 2h |
| | - 繁简转换匹配 | `chapter_md/*.tagged`（只读） | | |
| | - 顺序对齐 | | | |
| B4 | 提取实体增量候选 | `kg/sanjia/data/*.json` | `kg/sanjia/reports/` | 1-2h |
| | - 实线下划线 vs entity_index | `entity_index.json`（只读） | `entity_candidates.json` | |
| | - 波浪下划线 vs 典籍词表 | | `book_candidates.json` | |
| B5 | 提取校勘异文表 | `kg/sanjia/data/*.json` | `kg/sanjia/reports/collation.md` | 1h |
| B6 | 提取古今地名对照 | `kg/sanjia/data/*.json` | `kg/sanjia/reports/place_mapping.json` | 1-2h |
| | - "在今某州某县"模式 | | | |
| B7 | 提取引书目录 | `kg/sanjia/data/*.json` | `kg/sanjia/reports/bibliography.json` | 0.5h |

### 执行顺序

```
B1 → B2 → B3
        ├→ B4（B2完成即可开始）
        ├→ B5
        ├→ B6
        └→ B7
```

### 无冲突保证

- 写入目录为 `kg/sanjia/`（新目录，不与其他Agent冲突）和 `scripts/` 下的新脚本
- 对 `chapter_md/*.tagged` 和 `entity_index.json` 只读不写
- 不修改 `docs/`、`app/`、`ontology/` 中的任何文件

---

## 五、Agent C：阅读体验（应用层）

### 工作范围

改进前端渲染、交互功能和可视化，提升阅读器体验。

### 任务清单

| 序号 | 任务 | 输入（只读） | 输出（写入） | 预估工作量 |
|------|------|------------|------------|-----------|
| C1 | 实体颜色系统重设计 | `docs/css/shiji-styles.css` | `docs/css/shiji-styles.css` | 2-3h |
| | - 18类→视觉分层方案 | | | |
| | - hover显色/默认灰度等 | | | |
| C2 | 繁体支持 | `chapter_md/*.tagged`（只读） | `docs/js/trad-simp.js` | 2-3h |
| | - 繁简切换按钮 | `archive/wikisource_shiji/` | `render_shiji_html.py` 更新 | |
| | - 繁简字映射表 | | | |
| C3 | 搜索功能 | `entity_index.json`（只读） | `docs/js/search.js` | 3-4h |
| | - 全文搜索 | `chapter_md/*.tagged`（只读） | `docs/search.html` | |
| | - 按实体类型/章节筛选 | | `docs/search_index.json` | |
| C4 | 段落便签系统 | `kg/events/data/*事件索引.md` | `render_shiji_html.py` 更新 | 3-4h |
| | - LLM生成段落摘要 | `chapter_md/*.tagged`（只读） | `docs/css/` 更新 | |
| | - 事件关联 | | `chapter_md/*.sticky.json` | |
| C5 | 地铁图换乘优化 | `app/metro/data/` | `app/metro/metro.js` 更新 | 2h |
| | - 换乘节点视觉重设计 | | `app/metro/metro.css` 更新 | |
| C6 | 响应式移动端优化 | `docs/css/` | `docs/css/` 更新 | 2h |

### 执行顺序

```
C1 → C6（颜色定了再做响应式）
C2（独立）
C3（独立）
C4（独立）
C5（独立）
```

### 无冲突保证

- 写入 `docs/css/`、`docs/js/`、`app/metro/` — 均为前端展示文件
- `render_shiji_html.py` 是唯一与其他Agent可能共享的文件，但Agent A/B不修改它
- 不修改 `kg/`、`ontology/`、`archive/` 中的数据文件

---

## 六、共享资源与合并点

### 6.1 只读共享文件（所有Agent可读）

| 文件 | 说明 |
|------|------|
| `chapter_md/*.tagged.md` | 标注主文本（130篇） |
| `kg/entities/data/entity_index.json` | 实体索引（11,875条） |
| `kg/entities/data/entity_aliases.json` | 别名映射 |
| `kg/entities/data/disambiguation_map.json` | 消歧映射 |
| `kg/events/data/*事件索引.md` | 事件索引（3,185条） |
| `sections_data.json` | 章节小节数据 |

### 6.2 合并点（所有Agent完成后）

三个Agent各自完成后，需要一次**统一合并**操作：

```
Agent A 完成 → 本体数据就绪
Agent B 完成 → 三家注JSON + 实体候选就绪
Agent C 完成 → 前端改进就绪
                    │
                    ▼
              统一合并阶段
    ├── 1. Agent B的实体候选 → 审核后更新 tagged.md → 重建 entity_index.json
    ├── 2. Agent A的本体 → 链接到实体索引页
    ├── 3. Agent C的渲染器更新 → 重新生成130章HTML
    ├── 4. Agent B的三家注JSON → 注入渲染器（Agent C的展示代码）
    └── 5. 发布 → bash publish_to_docs.sh
```

### 6.3 禁止操作

- **任何Agent不得在工作过程中运行 `generate_all_chapters.py` 或 `publish_to_docs.sh`**
  （全局HTML重建放在合并阶段统一执行）
- **任何Agent不得修改 `entity_index.json`**
  （索引重建放在合并阶段，避免中间状态不一致）
- **不得同时修改同一个 `.py` 脚本文件**
  （每个Agent的新脚本放在各自目录下）

---

## 七、优先级排序

若资源有限（不能同时启动三个Agent），推荐顺序：

| 优先级 | Agent | 理由 |
|--------|-------|------|
| 1 | **Agent B（三家注）** | 产出的实体候选和校勘数据对Agent A（本体）和Agent C（渲染）都有价值 |
| 2 | **Agent A（本体）** | 地名/官职本体是知识图谱的核心骨架 |
| 3 | **Agent C（阅读体验）** | 前端改进可随时插入，不阻塞数据工作 |

若只能启动两个Agent，推荐 **A + B**（数据优先），C的任务可在A/B完成后单独执行。

---

## 八、风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| Agent B的繁简匹配准确率低 | target_pn关联失败 | 先跑自动匹配，人工审核失败case |
| Agent A的本体反思轮次超预期 | 阻塞后续任务 | 设置反思上限（每类型最多5轮），收敛后停止 |
| Agent C修改 render_shiji_html.py 与合并阶段冲突 | 合并时需要人工resolve | Agent C的渲染器改动用独立函数/模块，减少diff范围 |
| 三家注HTML解析遇到异常格式 | 部分章节解析失败 | 先跑全量，记录失败章节，后续单独处理 |

---

## 九、检查清单

### 启动前

- [ ] 确认 `entity_index.json` 是最新状态（最近一次全量重建）
- [ ] 确认所有 `tagged.md` 已commit（无未保存改动）
- [ ] 为每个Agent创建独立git分支：`agent-a/ontology`、`agent-b/sanjia`、`agent-c/frontend`

### 完成后

- [ ] Agent A：所有 `.ttl` 文件通过 RDF 语法检查
- [ ] Agent B：所有 `.sanjia.json` 文件通过 JSON schema 验证
- [ ] Agent C：所有 CSS/JS 改动在浏览器中验证
- [ ] 三个分支合并到main（解决冲突）
- [ ] 运行 `python generate_all_chapters.py` 重建HTML
- [ ] 运行 `bash publish_to_docs.sh` 发布
