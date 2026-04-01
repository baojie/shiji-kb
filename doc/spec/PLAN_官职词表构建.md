# 史记官职词表(Official Titles Glossary)构建计划

## 一、项目概述

### 1.1 背景与需求

**来源**：Issue #89 - 官制词典：辅助理解复杂官制体系（北京大学考古学生反馈）

**核心问题**：
> 官制是历史学研究一个非常重要的内容。对于学者个人来说，记忆纷繁复杂、变幻莫测的官制是一件非常困难的事情。但AI在读取关于官制的成熟的、可验证的研究之后，能够「记忆」这一体系，并且在读者需要的时候给出提示与参照。

### 1.2 目标

构建一个专业的史记官职词表，包含：
1. **官职名称**：收录先秦至汉代的官职名称（预估500-1000条）
2. **职责说明**：每个官职的具体职责
3. **品级体系**：官职的品级、隶属关系、俸禄
4. **历史演变**：同一官职在不同时期的变化
5. **人物关联**：史记中担任过此官职的人物
6. **官制体系图**：可视化展示官职层级关系

### 1.3 学术价值

1. **降低认知负担**：帮助读者快速理解复杂官制体系
2. **辅助历史研究**：为官制史研究提供结构化数据
3. **支撑阅读功能**：
   - 悬浮查看官职释义
   - 官职之间的对比
   - 同一时期的官制体系图
4. **可扩展性**：为后续制度词典、地理词典等专项词表提供模式

## 二、数据来源

### 2.1 已标注官职实体（优先级最高）

从标注文件中提取 `〖;官职〗` 实体：

```bash
# 统计官职实体
grep -oP '〖;[^〗]+〗' chapter_md/*.tagged.md \
  | sed 's/〖;//' | sed 's/〗//' \
  | sort | uniq -c | sort -rn > data/glossary/officials_raw.txt
```

**预估规模**：500-1000条官职名称

**示例**：
- 丞相、太尉、御史大夫（三公）
- 郡守、县令、县丞（地方官）
- 将军、都尉、校尉（军职）
- 郎中、侍中、宦者（宫廷官）
- 博士、太史、太卜（特殊官职）

### 2.2 权威文献资料

**核心文献**：
1. 《史记》本身
   - 卷019《惠景间侯者年表》
   - 卷022《汉兴以来将相名臣年表》
   - 相关列传中的官职描述

2. 《汉书·百官公卿表》
   - 汉代官制的权威记载
   - 官职职责、品级、演变

3. 专业工具书
   - 《中国古代官职词典》
   - 《秦汉官制史稿》（安作璋、熊铁基）
   - 《中国历代职官词典》

### 2.3 学术研究成果

- 严耕望《中国地方行政制度史·秦汉地方行政制度》
- 杨鸿年《汉代职官表》
- 学术论文中的官制研究

## 三、官职分类体系

### 3.1 中央官职

#### 3.1.1 三公九卿

**三公**：
- 丞相（相国）：最高行政长官
- 太尉：最高军事长官
- 御史大夫：监察长官

**九卿**：
- 奉常（太常）：掌宗庙礼仪
- 郎中令（光禄勋）：掌宫殿门户
- 卫尉：掌宫门卫兵
- 太仆：掌车马
- 廷尉：掌刑法
- 典客（大鸿胪）：掌民族事务
- 宗正：掌皇族事务
- 治粟内史（大司农）：掌财政
- 少府：掌山海池泽收入

#### 3.1.2 其他中央官职

- 中尉（执金吾）：掌京师治安
- 将作少府：掌土木工程
- 詹事：掌太子事务

### 3.2 地方官职

#### 3.2.1 郡县官职

**郡级**：
- 郡守：郡的最高行政长官
- 郡尉：郡的军事长官
- 监御史：郡的监察官

**县级**：
- 县令（万户以上）、县长（万户以下）：县的最高长官
- 县丞：辅佐县令/县长
- 县尉：县的军事长官

#### 3.2.2 基层官职

- 乡啬夫：乡级行政长官
- 亭长：亭级行政长官
- 里正：里级长官

### 3.3 军职

#### 3.3.1 将军系列

- 大将军、骠骑将军、车骑将军（高级将领）
- 前后左右将军（四方将军）
- 材官将军、楼船将军（特种部队）

#### 3.3.2 中下级军职

- 都尉：统领一郡兵力
- 校尉：统领一部兵力
- 司马：军中中级军官

### 3.4 宫廷官职

- 郎中、侍中、中常侍：宫廷侍从官
- 宦者：宫中内侍
- 给事中：宫中顾问官

### 3.5 特殊官职

- 博士：掌经学教育
- 太史：掌天文历法、记录史事
- 太卜：掌占卜
- 太医：掌医药

## 四、数据结构

### 4.1 JSON格式

```json
{
  "official_title": "丞相",
  "variants": ["相国", "相邦"],  // 异称
  "period": {
    "start": "秦",
    "end": "西汉末",
    "changes": [
      {
        "period": "秦",
        "name": "丞相"
      },
      {
        "period": "楚汉",
        "name": "相国",
        "note": "刘邦称相国"
      },
      {
        "period": "汉初",
        "name": "丞相"
      }
    ]
  },
  "category": {
    "major": "中央官职",
    "minor": "三公"
  },
  "rank": {
    "level": "一品",
    "salary": "万石",
    "position": "三公之首"
  },
  "responsibility": {
    "brief": "秦汉最高行政长官，辅佐皇帝处理政务",
    "detailed": "丞相为秦汉时期最高行政长官，位列三公之首。职掌国家政务，辅佐皇帝决策，统领百官。秦始皇设左右丞相，汉初沿用。汉武帝时设大司马，与丞相分掌政事。"
  },
  "hierarchy": {
    "superior": null,  // 无上级
    "subordinates": ["御史大夫", "九卿", "郡守"],
    "peers": ["太尉", "御史大夫"]
  },
  "holders": [  // 史记中担任此职的人物
    {
      "name": "萧何",
      "entity_id": "person_xiahe",
      "chapter": "053",
      "period": "高祖时"
    },
    {
      "name": "曹参",
      "entity_id": "person_caocan",
      "chapter": "054",
      "period": "惠帝时"
    }
    // ... 更多
  ],
  "occurrences": [  // 史记中所有出现位置
    {
      "chapter_num": "008",
      "chapter_title": "高祖本纪",
      "paragraph": "45.2",
      "context": "高祖乃立丞相萧何为相国"
    }
    // ... 更多
  ],
  "sources": [
    {
      "title": "《汉书·百官公卿表》",
      "quote": "相国、丞相，皆秦官..."
    },
    {
      "title": "《史记·萧相国世家》",
      "quote": "何为丞相，功第一"
    }
  ],
  "related_institutions": ["三公", "朝廷", "中央政府"],
  "notes": "秦称'丞相'，楚汉时期刘邦称'相国'，汉初复称'丞相'。汉武帝元狩五年废丞相，设大司马。"
}
```

### 4.2 官制体系图数据

```json
{
  "system_name": "西汉中央官制",
  "period": "汉武帝时期",
  "hierarchy": {
    "皇帝": {
      "level": 0,
      "children": {
        "三公": {
          "level": 1,
          "members": ["丞相", "太尉", "御史大夫"]
        },
        "九卿": {
          "level": 2,
          "members": ["奉常", "郎中令", "卫尉", "太仆", "廷尉", "典客", "宗正", "治粟内史", "少府"]
        }
      }
    }
  }
}
```

### 4.3 输出文件

```
data/glossary/
├── officials/
│   ├── officials_glossary.json       # 完整官职词表
│   ├── officials_by_category.json    # 按类别分类
│   ├── officials_by_period.json      # 按时期分类
│   ├── officials_hierarchy.json      # 官制体系图数据
│   └── officials_stats.json          # 统计数据

docs/special/
├── officials.html                    # Web版官职词典
└── officials_chart.html              # 官制体系图可视化
```

## 五、构建流程

### 5.1 Phase 1: 官职实体提取（第1周）

**任务**：
1. 提取所有 `〖;官职〗` 标注
2. 去重并统计频次
3. 记录每次出现的位置

**脚本**：
```bash
python scripts/extract_official_entities.py \
  --input "chapter_md/*.tagged.md" \
  --output data/glossary/officials/officials_raw.json
```

**输出**：
- `officials_raw.json`：官职原始数据（500-1000条）

### 5.2 Phase 2: 官职分类（第2周）

**任务**：
1. 根据官职性质分类（中央/地方/军职/宫廷/特殊）
2. 标注官职等级（三公/九卿/郡县/基层）
3. 识别官职异称（丞相/相国）

**方法**：
- AI Agent批量分类
- 参考《汉书·百官公卿表》
- 人工审核关键官职

**Agent提示词**：
```
请将以下官职分类到正确的类别：

官职：郡守
候选类别：
1. 中央官职 - 三公
2. 中央官职 - 九卿
3. 中央官职 - 其他
4. 地方官职 - 郡级
5. 地方官职 - 县级
6. 军职
7. 宫廷官职
8. 特殊官职

分析：郡守为郡的最高行政长官，属地方官职郡级
输出：地方官职 - 郡级
```

### 5.3 Phase 3: 职责与品级标注（第3周）

**任务**：
1. 为每个官职添加职责说明
2. 标注官职品级、俸禄
3. 梳理隶属关系

**数据来源**：
- 《汉书·百官公卿表》
- 专业工具书
- AI辅助生成初稿

**脚本**：
```bash
python scripts/annotate_officials.py \
  --input data/glossary/officials/officials_raw.json \
  --reference data/references/baiguan_gongqing.json \
  --output data/glossary/officials/officials_annotated.json
```

### 5.4 Phase 4: 人物关联（第4周）

**任务**：
1. 提取史记中担任过每个官职的人物
2. 标注任职时期
3. 关联到人物实体库

**脚本**：
```bash
python scripts/link_officials_to_persons.py \
  --officials data/glossary/officials/officials_annotated.json \
  --persons data/entities/persons.json \
  --output data/glossary/officials/officials_glossary.json
```

### 5.5 Phase 5: 官制体系图构建（第5周）

**任务**：
1. 构建不同时期的官制体系图数据
   - 秦代官制
   - 汉初官制
   - 汉武帝时期官制
2. 可视化层级关系
3. 标注官职演变

**可视化方案**：
- 树状图（Tree Diagram）
- 组织架构图（Org Chart）
- 时间轴演变图（Timeline）

### 5.6 Phase 6: Web界面与集成（第6周）

**任务**：
1. 开发Web版官职词典页面
2. 实现搜索、筛选、排序功能
3. 集成官制体系图可视化
4. 集成到专项索引总页

**功能设计**：
```html
<!-- 官职词典主界面 -->
<div class="officials-glossary">
  <!-- 搜索栏 -->
  <input type="text" placeholder="搜索官职..." />

  <!-- 筛选器 -->
  <div class="filters">
    <select name="category">按类别筛选</select>
    <select name="period">按时期筛选</select>
    <select name="rank">按品级筛选</select>
  </div>

  <!-- 官职列表 -->
  <div class="officials-list">
    <div class="official-item">
      <h3>丞相</h3>
      <span class="category">中央官职 - 三公</span>
      <p class="brief">秦汉最高行政长官</p>
      <a href="#detail">详情</a>
    </div>
    <!-- 更多官职... -->
  </div>

  <!-- 官制体系图 -->
  <div class="hierarchy-chart">
    <!-- 可视化图表 -->
  </div>
</div>
```

## 六、智能提示功能（Phase 7，第7-8周）

### 6.1 悬浮释义

**需求**（来自Issue #89）：
> 文本中出现官职时，可悬浮查看释义

**实现方案**：

#### 6.1.1 前端实现

```javascript
// 为所有官职标注添加悬浮事件
document.querySelectorAll('.entity-official').forEach(el => {
  el.addEventListener('mouseenter', async (e) => {
    const official = e.target.dataset.official;
    const popup = await fetchOfficialInfo(official);
    showPopup(e.target, popup);
  });
});

// 获取官职信息
async function fetchOfficialInfo(official) {
  const response = await fetch(`/api/officials/${official}`);
  const data = await response.json();
  return {
    title: data.official_title,
    brief: data.responsibility.brief,
    rank: data.rank.level,
    holders: data.holders.slice(0, 5)  // 前5位担任者
  };
}

// 显示弹出框
function showPopup(target, info) {
  const popup = document.createElement('div');
  popup.className = 'official-popup';
  popup.innerHTML = `
    <h4>${info.title}</h4>
    <p>${info.brief}</p>
    <div class="rank">品级：${info.rank}</div>
    <div class="holders">
      担任者：${info.holders.map(h => h.name).join('、')}
    </div>
  `;
  // 定位并显示弹出框
  positionPopup(target, popup);
  document.body.appendChild(popup);
}
```

#### 6.1.2 CSS样式

```css
.official-popup {
  position: absolute;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  max-width: 300px;
  z-index: 1000;
}

.official-popup h4 {
  margin: 0 0 8px 0;
  color: #8b4513;
}

.official-popup .rank {
  color: #666;
  font-size: 0.9em;
  margin: 4px 0;
}

.official-popup .holders {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #eee;
  font-size: 0.9em;
}
```

### 6.2 官职对比

**需求**（来自Issue #89）：
> 提供官职之间的对比

**功能设计**：

```html
<!-- 官职对比界面 -->
<div class="officials-comparison">
  <div class="select-officials">
    <select id="official1">
      <option>丞相</option>
      <option>太尉</option>
      <!-- ... -->
    </select>
    <span>vs</span>
    <select id="official2">
      <option>御史大夫</option>
      <!-- ... -->
    </select>
    <button>对比</button>
  </div>

  <div class="comparison-result">
    <table>
      <tr>
        <th>项目</th>
        <th>丞相</th>
        <th>御史大夫</th>
      </tr>
      <tr>
        <td>类别</td>
        <td>中央官职 - 三公</td>
        <td>中央官职 - 三公</td>
      </tr>
      <tr>
        <td>品级</td>
        <td>一品</td>
        <td>二品</td>
      </tr>
      <tr>
        <td>职责</td>
        <td>掌政务</td>
        <td>掌监察</td>
      </tr>
      <!-- 更多对比项... -->
    </table>
  </div>
</div>
```

### 6.3 官制体系图展示

**需求**（来自Issue #89）：
> 显示同一时期的官制体系图

**实现方案**：

使用D3.js或ECharts绘制树状图：

```javascript
// 使用ECharts绘制官制体系图
const option = {
  title: { text: '西汉中央官制体系图（汉武帝时期）' },
  series: [{
    type: 'tree',
    data: [{
      name: '皇帝',
      children: [
        {
          name: '三公',
          children: [
            { name: '丞相' },
            { name: '太尉' },
            { name: '御史大夫' }
          ]
        },
        {
          name: '九卿',
          children: [
            { name: '奉常' },
            { name: '郎中令' },
            // ...
          ]
        }
      ]
    }],
    layout: 'orthogonal',
    orient: 'TB',  // 从上到下
    label: { position: 'top' }
  }]
};

chart.setOption(option);
```

## 七、质量控制

### 7.1 数据完整性

- **覆盖率**：≥95% 已标注官职纳入词表
- **职责说明**：100% 官职有简明释义
- **品级标注**：≥90% 官职有品级信息
- **人物关联**：≥80% 官职有担任者信息

### 7.2 准确性验证

**分层验证**：
1. **AI生成**：所有官职（500-1000条）
2. **工具书校对**：核心官职（三公九卿、郡县官）
3. **专家审核**：争议官职（约50条）

**验证标准**：
- 职责说明与《汉书·百官公卿表》一致
- 品级信息有明确文献依据
- 官职演变符合历史事实

### 7.3 引用规范

- 所有释义必须注明来源
- 引用原文需标注出处
- 存在争议的观点需列出不同说法

## 八、里程碑与时间表

| 周次 | 任务 | 输出 | 责任人 |
|------|------|------|--------|
| W1 | 官职实体提取 | `officials_raw.json` | TBD |
| W2 | 官职分类 | `officials_classified.json` | TBD |
| W3 | 职责与品级标注 | `officials_annotated.json` | TBD |
| W4 | 人物关联 | `officials_glossary.json` | TBD |
| W5 | 官制体系图构建 | `officials_hierarchy.json` | TBD |
| W6 | Web界面与集成 | `docs/special/officials.html` | TBD |
| W7-W8 | 智能提示功能 | 悬浮释义、对比、体系图 | TBD |

**总计**：8周（约2个月）

## 九、后续扩展

### 9.1 时间维度

- 按朝代展示官制演变
- 官职改革关键事件时间轴
- 官职名称变迁动画

### 9.2 空间维度

- 地方官制地图（郡县分布）
- 边疆官制特点
- 地域差异分析

### 9.3 关系维度

- 官职-人物关系网络
- 官职-事件关联
- 官职-制度关联

### 9.4 跨文献对比

- 《史记》vs《汉书》官制对比
- 与出土简牍印证
- 与传世文献交叉验证

## 十、相关资源

### 10.1 相关Issue

- #89 官制词典：辅助理解复杂官制体系（本计划）
- #3 字典
- #44 辞典释义
- #36 实体悬浮预览

### 10.2 参考SKILL

- [SKILL_02h_词表构建](../../skills/SKILL_02h_词表构建.md)
- [SKILL_03a_实体标注](../../skills/SKILL_03a_实体标注.md)

### 10.3 权威文献

**核心文献**：
1. 《汉书·百官公卿表》（班固）
2. 《史记》卷019、022（司马迁）
3. 《续汉书·百官志》（司马彪）

**工具书**：
1. 《中国古代官职词典》（刘幼民）
2. 《中国历代职官词典》（龚书铎）
3. 《秦汉官制史稿》（安作璋、熊铁基）

**学术研究**：
1. 严耕望《中国地方行政制度史·秦汉地方行政制度》
2. 杨鸿年《汉代职官表》
3. 王子今《秦汉时期的政治与政治文化》

### 10.4 数字资源

- 中国历代人物传记资料库 (CBDB)
- 中央研究院汉籍电子文献
- 国学大师（官职查询）

---

**计划编写时间**：2026-03-31
**对应Issue**：#89
**预计启动时间**：待定
**负责人**：待定
**审核人**：待定
