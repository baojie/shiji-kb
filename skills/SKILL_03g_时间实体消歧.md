---
skill_id: SKILL_03g
title: 时间实体消歧
category: entity_construction
dependencies: [SKILL_03_实体构建]
tools: [kg/events/scripts/build_year_map.py]
status: active
created: 2026-04-02
---

# SKILL_03g_时间实体消歧

## 概述

将《史记》中的相对年份（如"元年"、"三年"）消歧为绝对公元年，支持时间轴构建和事件定位。

**输入**: 标注了`〖%年份%〗`的markdown文件
**输出**: `year_ce_map.json` - 年份→公元年映射表
**覆盖率**: 76.8% (6648/8657)
**质量**: 98.4%包含公元年

## 快速开始

### 执行完整流程

```bash
# 运行年份消歧脚本（3个阶段）
python kg/events/scripts/build_year_map.py
```

**输出文件**:
- `kg/chronology/data/year_ce_map.json` - 年份映射（6648条）
- `kg/chronology/data/reign_periods.json` - 君主在位时期（390君主）
- `kg/chronology/data/year_state_map.json` - 公元年→诸侯国映射（635年）
- `docs/entities/timeline.html` - 时间轴可视化

### 检查覆盖率

```bash
python -c "
import json
with open('kg/chronology/data/year_ce_map.json', 'r') as f:
    data = json.load(f)
total = sum(sum(len(p) for p in ch.values()) for ch in data.values())
print(f'总映射数: {total}, 覆盖率: {total/8657*100:.1f}%')
"
```

## 核心概念

### 1. 年份类型

| 类型 | 示例 | 标注 | 说明 |
|------|------|------|------|
| **绝对年份** | 元年、三年 | `〖%元年〗` | 需要消歧 |
| **时长** | 立十二年 | `〖%十二年\|时长〗` | 跳过 |
| **年号年份** | 建元元年 | `〖%建元元年〗` | 通过年号映射 |
| **干支年** | 甲子 | `〖%甲子〗` | 通过60甲子推算 |

### 2. 消歧方法

#### 五层策略（优先级递减）

1. **era_name**: 年号映射
   - 示例: `建元元年` → 公元前140年
   - 依赖: `reign_periods.json`中的年号数据

2. **nearby_ruler**: 邻近统治者
   - 示例: `〖@齐桓公〗...〖%三年〗` → 齐桓公3年
   - 范围: 年份前后100字符内的`〖@〗`标注

3. **sequential**: 序列推导
   - 示例: `元年...二年...三年` → 延续前一年份
   - 验证: 检查年份是否在君主在位范围内（±5年容错）

4. **section_ruler**: 章节标题推导
   - 示例: `## 齐桓公` 下的年份推导为齐桓公年份
   - 适用: 世家、本纪类章节

5. **raw_nearby**: 原始邻近法（无验证）
   - 最后手段，用于上古时期无公元年数据的君主
   - 结果: `ruler_key` 而非 `ce_year`

#### 特殊方法

6. **table_row**: 年表章节表格行解析
   - 适用: 014/015章（十二诸侯年表、六国年表）
   - 原理: 每行`[rX]`对应一个公元年，从单元格提取年份文本
   - 贡献: 4654条（70%覆盖率）

### 3. 数据结构

#### year_ce_map.json

```json
{
  "章节ID": {
    "段落ID": {
      "表面文本": {
        "ce_year": -201,
        "ruler": "高皇帝",
        "method": "nearby_ruler"
      }
    }
  }
}
```

**字段说明**:
- `ce_year`: 公元年（负数=公元前）
- `ruler`: 对应君主显示名
- `ruler_key`: 君主规范名（上古时期无ce_year时使用）
- `method`: 消歧方法（见上）

#### reign_periods.json

```json
{
  "rulers": {
    "齐桓公": {
      "state": "齐",
      "登基年": -685,
      "退位年": -643,
      "年数": 43
    }
  }
}
```

从014/015/022年表章节自动提取。

#### year_state_map.json

```json
{
  "-841": {
    "周": ["周共和", 1],
    "鲁": ["鲁真公", 15],
    "齐": ["齐武公", 10]
  }
}
```

**用途**: 年表章节表格行解析（`[r1]`→公元前841年）

## 处理流程

### Phase 1: 提取君主在位时期

**目标**: 从年表章节提取君主在位时期数据

**处理章节**:
- 014_十二诸侯年表（春秋，前841-前476）
- 015_六国年表（战国，前475-前207）
- 022_汉兴以来将相名臣年表（汉朝，前206-前87）

**输出**:
- `reign_periods.json` (390君主)
- `year_state_map.json` (635年)

**关键函数**: `extract_reign_periods()`

### Phase 2: 年份消歧

**目标**: 为所有标注的年份确定公元年

**处理逻辑**:

```
for each chapter:
    if chapter in [014, 015]:
        # 年表章节：表格行解析
        process_table_chapter()
    else:
        # 文本章节：五层消歧策略
        for each 〖%年份〗:
            if is_duration():
                skip
            else:
                disambiguate_year()
```

**输出**: `year_ce_map.json` (6648条)

**关键函数**:
- `disambiguate_years()`
- `process_table_chapter()`

### Phase 3: 生成时间轴

**目标**: 生成HTML可视化时间轴

**输出**: `docs/entities/timeline.html`

**内容**:
- 897个不同公元年
- 6541个文本引用
- 3082个事件（带公元年）

**关键函数**: `generate_timeline_html()`

#### 数据来源

timeline.html **每次完全重新生成**，综合三个数据源：

1. **year_ce_map.json** (Phase 2输出)
   - 6655条年份→公元年映射
   - 来自消歧结果

2. **event_year_map** (从事件索引提取)
   - 3082个事件的公元年
   - 来自 `kg/events/007_事件索引.json`

3. **year_state_map.json** (Phase 1输出)
   - 635年的诸侯国君主信息
   - 用于显示每年各国君主

#### 更新机制

**重要**: timeline.html的更新是**重建式**，不是**追加式**

```python
def generate_timeline(year_map, reign_data, event_year_map, year_state_map):
    """每次运行都完全重新生成timeline.html"""
    # 1. 聚合所有年份引用
    by_year = defaultdict(list)  # 从year_ce_map收集
    by_year_events = defaultdict(list)  # 从event_year_map收集

    # 2. 生成HTML
    with open(TIMELINE_FILE, 'w') as f:  # 'w'模式会覆盖旧文件
        f.write(html_content)
```

**执行流程**:
```
运行 build_year_map.py
  ↓
Phase 1: extract_reign_periods() → year_state_map.json
  ↓
Phase 2: disambiguate_years() → year_ce_map.json (重新生成)
  ↓
Phase 3: load_event_index_years() → event_year_map
  ↓
Phase 4: generate_timeline() → timeline.html (完全覆盖)
```

**数据安全性**:
- ✅ year_ce_map.json 已commit到git（可恢复）
- ✅ timeline.html 从year_ce_map.json重建（可重现）
- ⚠️ 如果year_ce_map.json丢失，timeline.html也会丢失所有数据

**不会丢失数据的条件**:
1. year_ce_map.json已commit
2. 脚本逻辑没有破坏性修改
3. 原始tagged.md文件没有被错误修改

**会丢失数据的情况**:
1. 删除year_ce_map.json后运行脚本
2. 修改脚本导致消歧失败
3. 删除tagged.md中的年份/人物标注

## 年表章节处理

### 适用章节

| 章节 | 类型 | 结构 | 处理方法 |
|------|------|------|----------|
| 014 | 十二诸侯年表 | 行=公元年，列=诸侯国 | ✅ table_row |
| 015 | 六国年表 | 行=公元年，列=诸侯国 | ✅ table_row |
| 022 | 将相名臣年表 | 行=公元年，列=官职 | ⚠️ 汉朝，无数据 |
| 018 | 高祖功臣年表 | 行=侯国，列=皇帝 | ⚠️ 待开发 |
| 019 | 惠景间侯者年表 | 行=侯国，列=皇帝 | ⚠️ 待开发 |
| 020 | 建元已来侯者年表 | 行=侯国，列=皇帝 | ⚠️ 待开发 |
| 021 | 建元以来侯者年表 | 行=侯国，列=皇帝 | ⚠️ 待开发 |

### 表格行解析算法

**前提**: `year_state_map.json` 包含该时期的公元年数据

**步骤**:

1. **加载映射表**
   ```python
   year_state_map = load_year_state_map()  # {公元年: {国家: [君主, 在位年]}}
   row_to_year = build_row_to_year_map(year_state_map)  # {行号: 公元年}
   ```

2. **解析表头**
   ```python
   # 从 | 年 | 〖◆周〗 | 〖◆鲁〗 | ... 提取列顺序
   state_cols = ['周', '鲁', '齐', '晋', ...]
   ```

3. **遍历表格行**
   ```python
   for line in lines:
       if match('[rX]'):
           ce_year = row_to_year[X]
           for cell in row_cells:
               extract_year_numbers(cell)  # 二、十、元年...
               map_to_ce_year(year_num, ce_year, ruler)
   ```

4. **提取年份文本**
   - 模式: `元年|[一二三四五六七八九十百]+`
   - 排除: 在`〖〗`标注内的文本
   - 排除: 包含"月"、"日"的时间

5. **生成映射**
   ```python
   year_map[para_id][year_text] = {
       'ce_year': ce_year,
       'ruler': ruler_key,
       'method': 'table_row'
   }
   ```

**关键点**:
- 使用`[rX]`作为段落ID（避免覆盖）
- 每行约10个单元格，每个单元格可能有多个年份文本
- 014章: 365行 × 平均10列 = 3525条映射

## 质量控制

### 自动验证

1. **年份范围检查**
   - 君主在位年份应在`[登基年, 退位年+5]`范围内
   - 超范围尝试修正：查找同名其他君主

2. **时长识别**
   ```python
   # 排除模式
   NOT_CALENDAR_YEAR_PATS = [
       r'立.*年',    # 立十二年
       r'在位.*年',  # 在位三十年
       r'\d+年',     # 阿拉伯数字（年龄）
   ]
   ```

3. **重复消除**
   - 使用dict自动去重：同一段落的同一文本只保留一个映射

### 人工验证（待实施）

1. **抽样检查**: 随机抽取100条映射人工验证
2. **边界案例**: 检查年份边界（君主即位/退位年）
3. **异常检测**: 标记ce_year为None或ruler_key的条目

### 错误修正

**out_of_range_recovered**: 132条

年份超出君主在位范围时，尝试查找同名其他君主并修正。

**示例**:
```
原: 齐桓公五十年 → 齐桓公(-685~-643) → 超范围！
修正: 查找其他齐桓公 → 齐桓公(-685~-643) 只有一个
→ 保留但标记为recovered
```

## 已知限制

### 1. 汉朝年表未处理

**影响**: 3328条年份（38.4%）

**章节**: 018/019/020/021/017/022

**原因**:
- 表格结构不同（行=侯国 vs 行=公元年）
- year_state_map只覆盖前841-前207年

**解决方案**:
1. 扩展year_state_map到汉朝（前206~）
2. 开发侯国表专用解析器
3. 利用皇帝在位时期+年号映射

### 2. 部分章节消歧率低

| 章节 | 覆盖率 | 原因 | 改进方向 |
|------|--------|------|----------|
| 027_天官书 | 0% | 天文历法，时间表述特殊 | 需要领域知识 |
| 016_秦楚之际月表 | 3.8% | 月份+年份组合 | 月份解析器 |
| 012_孝武本纪 | 1.6% | 汉武帝年号密集 | 年号映射表 |

### 3. 上古时期无公元年

**影响**: 96条（1.5%）

**时期**: 夏商周早期（公元前1000年以前）

**处理**:
- 保留`ruler_key`（如"夏禹元年"）
- 不分配`ce_year`
- 可用于相对时序排列

## 工具与脚本

### 主脚本

**文件**: `kg/events/scripts/build_year_map.py` (1674行)

**用法**:
```bash
python kg/events/scripts/build_year_map.py
```

**参数**: 无（使用内置配置）

**运行时间**: ~30秒

### 辅助函数

| 函数 | 功能 | 输出 |
|------|------|------|
| `extract_reign_periods()` | 提取君主在位时期 | reign_periods.json |
| `build_ruler_lookup()` | 构建君主查找索引 | 4个dict |
| `load_year_state_map()` | 加载公元年映射 | dict |
| `build_row_to_year_map()` | 建立行号映射 | {row: year} |
| `process_table_chapter()` | 解析年表表格 | year_map, stats |
| `disambiguate_years()` | 文本年份消歧 | year_map |
| `generate_timeline_html()` | 生成时间轴 | HTML |

### 配置常量

```python
CHAPTER_DIR = 'chapter_md'
OUTPUT_FILE = 'kg/chronology/data/year_ce_map.json'
TOLERANCE_YEARS = 5  # 年份范围容错

CHAPTER_STATE = {  # 章节→主要诸侯国
    '032': '齐', '033': '齐',
    '034': '燕', '035': '赵',
    # ...
}

STATE_ALIASES = {  # 国家别名
    '田': '齐', '赢': '秦'
}
```

### 数据安全最佳实践

**修改脚本前的保护措施**:

```bash
# 1. 备份关键数据文件
cp kg/chronology/data/year_ce_map.json \
   kg/chronology/data/year_ce_map.json.v1.0.backup

# 2. 记录当前覆盖率（baseline）
python -c "
import json
with open('kg/chronology/data/year_ce_map.json', 'r') as f:
    data = json.load(f)
total = sum(sum(len(p) for p in ch.values()) for ch in data.values())
print(f'Baseline: {total} 条映射')
" > baseline_coverage.txt

# 3. 在git分支上修改（推荐）
git checkout -b optimize-year-disambiguation
```

**运行脚本后的验证**:

```bash
# 1. 检查新覆盖率
python -c "
import json
with open('kg/chronology/data/year_ce_map.json', 'r') as f:
    data = json.load(f)
total = sum(sum(len(p) for p in ch.values()) for ch in data.values())
print(f'当前: {total} 条映射')
"

# 2. 如果覆盖率显著下降，立即恢复
git diff kg/chronology/data/year_ce_map.json  # 检查差异
git checkout kg/chronology/data/year_ce_map.json  # 恢复

# 3. 或从备份恢复
cp kg/chronology/data/year_ce_map.json.v1.0.backup \
   kg/chronology/data/year_ce_map.json
```

**版本管理建议**:

1. **重大版本标记**: 在milestone版本创建带tag的备份
   ```bash
   cp year_ce_map.json year_ce_map.json.v1.0
   git tag -a v1.0-year-disambiguation -m "76.87% coverage milestone"
   ```

2. **定期commit**: 每次显著改进都commit
   ```bash
   git add kg/chronology/data/year_ce_map.json
   git commit -m "优化nearby_ruler: 覆盖率76.8%→76.87%"
   ```

3. **分支开发**: 重大修改在分支上进行
   ```bash
   git checkout -b feature/han-dynasty-tables
   # 修改和测试
   git checkout main && git merge feature/han-dynasty-tables
   ```

## 执行清单

### 执行前

- [ ] 确认`chapter_md/*.tagged.md`存在且包含`〖%〗`标注
- [ ] 确认`kg/relations/rulers.json`存在（656君主）
- [ ] 备份现有`year_ce_map.json`（如有重要版本）
- [ ] 记录当前覆盖率作为baseline

### 执行中

- [ ] 观察Phase 1输出：390君主、635年
- [ ] 观察Phase 2输出：Mapped总数、各方法统计
- [ ] 检查warnings（escape sequence等可忽略）

### 执行后

- [ ] 验证覆盖率: `total/8657 >= 75%`
- [ ] 检查`year_ce_map.json`文件大小：~1.5MB
- [ ] 浏览`timeline.html`确认可视化正常
- [ ] 运行质量检查脚本（待开发）

## 示例

### 消歧示例1: 邻近统治者

**输入文本** (039_晋世家):
```markdown
[3.1] 〖@晋献公〗始即位，〖%元年〗...
[3.2] 〖%二年〗，使太子申生伐〖=东山〗。
```

**处理过程**:
1. 识别`〖%元年〗`，前文100字符内找到`〖@晋献公〗`
2. 查询`reign_periods.json`: 晋献公(-676, -651)
3. 计算: 元年 = -676
4. 识别`〖%二年〗`，无邻近人物，使用sequential
5. 延续: 二年 = 元年+1 = -675
6. 验证: -675 in [-676, -646] ✓

**输出映射**:
```json
{
  "039": {
    "3.1": {
      "元年": {"ce_year": -676, "ruler": "晋献公", "method": "nearby_ruler"}
    },
    "3.2": {
      "二年": {"ce_year": -675, "ruler": "晋献公", "method": "sequential"}
    }
  }
}
```

### 消歧示例2: 表格行解析

**输入表格** (014_十二诸侯年表):
```
|  [r1]  |  庚申  |  共和元年  |  十五  |  十  |  十八  |  四  |  七  |  ...
|  [r2]  |        |  二        |  十六  |  十一|  晋厘侯元年  |  五  |  八  |  ...
```

**处理过程**:
1. `year_state_map['-841']` → 周/鲁/齐/晋...各国君主
2. `row_to_year[1]` = -841, `row_to_year[2]` = -840
3. [r1]行提取: `二`、`十五`、`十`、`十八`、`四`、`七` → 6个年份文本
4. [r2]行提取: `二`、`十六`、`十一`、`元年`、`五`、`八` → 6个年份文本
5. 每个映射到ce_year=-841或-840，ruler从year_state_map获取

**输出映射** (部分):
```json
{
  "014": {
    "r1": {
      "二": {"ce_year": -841, "ruler": "周共和", "method": "table_row"},
      "十五": {"ce_year": -841, "ruler": "鲁真公", "method": "table_row"},
      "十": {"ce_year": -841, "ruler": "齐武公", "method": "table_row"}
    },
    "r2": {
      "二": {"ce_year": -840, "ruler": "周共和", "method": "table_row"},
      "十六": {"ce_year": -840, "ruler": "鲁真公", "method": "table_row"},
      "元年": {"ce_year": -840, "ruler": "晋厘侯", "method": "table_row"}
    }
  }
}
```

## 扩展方向

### 短期（达到85%）

1. **改进世家/列传消歧**
   - 加强章节标题统治者识别
   - 扩展STATE_ALIASES字典
   - 优化sequential验证逻辑

2. **处理月表章节**
   - 016_秦楚之际月表（128条）
   - 解析"某月"+"某年"组合

### 中期（达到90%+）

1. **汉朝年表解析器**
   - 扩展year_state_map到汉朝
   - 处理018/019/020/021侯国表（3328条）
   - 建立皇帝年号→公元年映射表

2. **质量提升**
   - 开发validate_year_disambiguation.py
   - 人工抽检100条样本
   - 修正识别出的错误

### 长期（完整覆盖）

1. **细粒度时间**
   - 支持月份、季节
   - 支持"某事X年后"相对表述
   - 建立完整的年号系统

2. **跨章节关联**
   - 同一事件在多章节的时间一致性验证
   - 人物生卒年与事件时间的逻辑验证

## 相关文档

- [PLAN_时间实体消歧.md](../doc/spec/PLAN_时间实体消歧.md) - 规划文档
- [year_disambiguation_progress_20260402.md](../logs/reports/year_disambiguation_progress_20260402.md) - 进展报告
- [SKILL_03_实体构建.md](SKILL_03_实体构建.md) - 父级SKILL
- [build_year_map.py](../kg/events/scripts/build_year_map.py) - 主脚本

## 版本历史

- **v1.0** (2026-04-02): 初始版本
  - 覆盖率76.8%
  - 支持014/015年表章节表格解析
  - 五层文本消歧策略
  - 6648条映射，98.4%包含公元年
