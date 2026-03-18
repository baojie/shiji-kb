# 实体渲染规划 v6.0 增强版

**设计理念**：在v5.0基础上，通过组合下划线颜色、样式、粗细和底色变化，创造更丰富的视觉层次。

**核心改进**：
1. **底色分层**：不再统一淡黄底，按重要性和语义分3层底色
2. **下划线增强**：组合颜色、样式、粗细创造更多视觉维度
3. **帝王特殊标识**：使用双线下划线突出帝王人物
4. **渐变应用**：重大历史事件使用渐变下划线

---

## 一、设计原则

### 1. 底色分层系统（3层）

```
第1层（核心实体）：淡金底 rgba(255, 250, 205, 0.7) - 帝王、重要人物、重大事件
第2层（常规实体）：淡黄底 rgba(255, 248, 220, 0.6) - 大多数名词实体
第3层（次要实体）：极淡黄底 rgba(255, 252, 240, 0.5) - 低频、抽象实体
```

### 2. 下划线增强系统

| 下划线类型 | CSS样式 | 粗细 | 颜色 | 适用场景 |
|----------|---------|------|------|---------|
| **粗实线** | `solid` | 2-3px | 深色 | 帝王、核心人物 |
| **双线** | `double` | 3px | 中色 | 特殊重要实体 |
| **中实线** | `solid` | 1px | 中色 | 高频核心实体 |
| **粗虚线** | `dashed` | 2px | 中色 | 重要次级实体 |
| **细虚线** | `dashed` | 1px | 淡色 | 一般次级实体 |
| **粗点线** | `dotted` | 2px | 中色 | 重要抽象概念 |
| **细点线** | `dotted` | 1px | 淡色 | 一般抽象概念 |
| **波浪线** | `wavy` | 2px | 彩色 | 书籍、神话 |
| **渐变线** | `background` | 2-3px | 渐变 | 重大历史事件 |

### 3. 颜色语义不变

保持v5.0的7色分组：褐(空间) 青(时间) 紫(政治) 蓝(社会) 墨绿(文化) 橙褐(物质) 海绿(数量)

---

## 二、18类实体增强渲染方案

### 【空间叙事要素】褐色系 `#8B4513`

#### 1.1 人名（帝王）`〖@人名〗`

```css
.person-emperor {
    color: #8B0000;                          /* 深红（区别于普通人） */
    background-color: rgba(255, 250, 205, 0.7);  /* 淡金底（第1层） */
    border-bottom: 3px double rgba(139, 0, 0, 0.6);  /* 粗双线 */
    padding: 0 4px;
    border-radius: 2px;
    font-weight: 600;
    cursor: help;
}
```

**特点**：深红色 + 淡金底 + 粗双线 + 加粗

#### 1.2 人名（重要人物）`〖@人名〗`

```css
.person-major {
    color: #8B4513;                          /* 标准褐色 */
    background-color: rgba(255, 248, 220, 0.6);  /* 淡黄底（第2层） */
    border-bottom: 2px solid rgba(139, 69, 19, 0.5);  /* 中粗实线 */
    padding: 0 3px;
    border-radius: 2px;
    font-weight: 500;
    cursor: help;
}
```

**特点**：标准褐 + 淡黄底 + 中粗实线

#### 1.3 人名（普通人物）`〖@人名〗`

```css
.person {
    color: #8B4513;                          /* 标准褐色 */
    background-color: rgba(255, 248, 220, 0.6);  /* 淡黄底（第2层） */
    border-bottom: 1px solid rgba(139, 69, 19, 0.4);  /* 细实线 */
    padding: 0 2px;
    border-radius: 2px;
    cursor: help;
}
```

**特点**：标准褐 + 淡黄底 + 细实线（v5.0标准）

#### 2. 地名 `〖^地名〗`

```css
.place {
    color: #A0522D;                          /* 赭褐色 */
    background-color: rgba(255, 248, 220, 0.6);  /* 淡黄底 */
    border-bottom: 1px dashed rgba(160, 82, 45, 0.5);  /* 细虚线（彩色） */
    padding: 0 2px;
    border-radius: 2px;
    cursor: help;
}
```

**改进**：下划线颜色与文字颜色一致（更和谐）

#### 3. 官职 `〖;官职〗`

```css
.official {
    color: #8B4513;                          /* 褐色 */
    background-color: rgba(255, 248, 220, 0.6);  /* 淡黄底 */
    border-bottom: 1px dashed rgba(139, 69, 19, 0.4);  /* 细虚线 */
    padding: 0 2px;
    border-radius: 2px;
    font-weight: 500;
    cursor: help;
}
```

---

### 【时间维度】青色系 `#008B8B`

#### 4.1 时间（重大历史节点）`〖#时间〗`

```css
.time-major {
    color: #008B8B;                          /* 深青色 */
    background-color: rgba(255, 250, 205, 0.7);  /* 淡金底（第1层） */
    border-bottom: 2px solid rgba(0, 139, 139, 0.6);  /* 中粗实线 */
    padding: 0 3px;
    border-radius: 2px;
    font-weight: 500;
    cursor: help;
}
```

**特点**：重大时间节点（如"秦统一六国"）突出显示

#### 4.2 时间（普通）`〖#时间〗`

```css
.time {
    color: #008B8B;                          /* 深青色 */
    background-color: rgba(255, 252, 240, 0.5);  /* 极淡黄底（第3层） */
    border-bottom: 1px dotted rgba(0, 139, 139, 0.4);  /* 细点线 */
    padding: 0 2px;
    border-radius: 2px;
    cursor: help;
}
```

---

### 【政治组织】紫色系 `#9370DB`

#### 5. 朝代 `〖$朝代〗`

```css
.dynasty {
    color: #9370DB;                          /* 中紫色 */
    background-color: rgba(255, 248, 220, 0.6);  /* 淡黄底 */
    border-bottom: 2px solid rgba(147, 112, 219, 0.6);  /* 中粗实线（彩色） */
    padding: 0 3px;
    border-radius: 2px;
    font-weight: 500;
    cursor: help;
}
```

**改进**：加粗下划线，突出朝代重要性

#### 6. 封国 `〖&封国〗`

```css
.feudal-state {
    color: #9370DB;                          /* 紫色 */
    background-color: rgba(255, 248, 220, 0.6);  /* 淡黄底 */
    border-bottom: 1px solid rgba(147, 112, 219, 0.5);  /* 细实线（彩色） */
    padding: 0 2px;
    border-radius: 2px;
    cursor: help;
}
```

#### 7. 族群 `〖%族群〗`

```css
.tribe {
    color: #9370DB;                          /* 紫色 */
    background-color: rgba(255, 248, 220, 0.6);  /* 淡黄底 */
    border-bottom: 1px dashed rgba(147, 112, 219, 0.5);  /* 细虚线（彩色） */
    padding: 0 2px;
    border-radius: 2px;
    cursor: help;
}
```

---

### 【社会制度】蓝色系 `#4682B4`

#### 8. 制度 `〖~制度〗`

```css
.institution {
    color: #4682B4;                          /* 钢青色 */
    background-color: rgba(255, 252, 240, 0.5);  /* 极淡黄底（第3层） */
    border-bottom: 1px solid rgba(70, 130, 180, 0.4);  /* 细实线（彩色） */
    padding: 0 2px;
    border-radius: 2px;
    cursor: help;
}
```

**改进**：添加细实线，不再是无下划线

#### 9. 刑法 `〖/刑法〗`

```css
.legal {
    color: #4682B4;                          /* 钢青色 */
    background-color: rgba(255, 248, 220, 0.6);  /* 淡黄底 */
    border-bottom: 1px dashed rgba(70, 130, 180, 0.5);  /* 细虚线（彩色） */
    padding: 0 2px;
    border-radius: 2px;
    cursor: help;
}
```

#### 10. 礼仪 `〖*礼仪〗`

```css
.ritual {
    color: #4682B4;                          /* 钢青色 */
    background-color: rgba(255, 252, 240, 0.5);  /* 极淡黄底（第3层） */
    border-bottom: 1px dotted rgba(70, 130, 180, 0.5);  /* 细点线（彩色） */
    padding: 0 2px;
    border-radius: 2px;
    cursor: help;
}
```

#### 11. 身份 `〖_身份〗`

```css
.identity {
    color: #4682B4;                          /* 钢青色 */
    background-color: rgba(255, 252, 240, 0.5);  /* 极淡黄底（第3层） */
    padding: 0 2px;
    border-radius: 2px;
    cursor: help;
}
```

**保持**：无下划线（背景色已足够）

---

### 【文化思想】墨绿系 `#2F4F4F`

#### 12. 典籍 `〖!典籍〗`

```css
.book {
    color: #2F4F4F;                          /* 深石板灰 */
    background-color: rgba(255, 248, 220, 0.6);  /* 淡黄底 */
    text-decoration: underline wavy rgba(47, 79, 79, 0.6);  /* 波浪线（彩色） */
    text-decoration-thickness: 2px;          /* 加粗波浪线 */
    text-underline-offset: 2px;              /* 下移2px */
    padding: 0 2px;
    border-radius: 2px;
    font-style: italic;
    cursor: help;
}
```

**改进**：加粗波浪线 + 偏移

#### 13. 思想 `〖?思想〗`

```css
.concept {
    color: #2F4F4F;                          /* 深石板灰 */
    background-color: rgba(255, 252, 240, 0.5);  /* 极淡黄底（第3层） */
    border-bottom: 1px dotted rgba(47, 79, 79, 0.5);  /* 细点线（彩色） */
    padding: 0 2px;
    border-radius: 2px;
    cursor: help;
}
```

---

### 【物质世界】橙褐系 `#CD853F`

#### 14. 器物 `〖=器物〗`

```css
.artifact {
    color: #CD853F;                          /* 秘鲁色 */
    background-color: rgba(255, 252, 240, 0.5);  /* 极淡黄底（第3层） */
    border-bottom: 1px dashed rgba(205, 133, 63, 0.5);  /* 细虚线（彩色） */
    padding: 0 2px;
    border-radius: 2px;
    cursor: help;
}
```

**改进**：添加细虚线（不再无下划线）

#### 15. 生物 `〖+生物〗`

```css
.biology {
    color: #CD853F;                          /* 秘鲁色 */
    background-color: rgba(255, 252, 240, 0.5);  /* 极淡黄底（第3层） */
    border-bottom: 1px dotted rgba(205, 133, 63, 0.5);  /* 细点线（彩色） */
    padding: 0 2px;
    border-radius: 2px;
    cursor: help;
}
```

#### 16. 天文 `〖•天文〗`

```css
.astronomy {
    color: #CD853F;                          /* 秘鲁色 */
    background-color: rgba(255, 252, 240, 0.5);  /* 极淡黄底（第3层） */
    border-bottom: 1px dotted rgba(205, 133, 63, 0.4);  /* 细点线 */
    padding: 0 2px;
    border-radius: 2px;
    cursor: help;
}
```

#### 17. 神话 `〖:神话〗`

```css
.mythical {
    color: #CD853F;                          /* 秘鲁色 */
    background-color: rgba(255, 248, 220, 0.6);  /* 淡黄底 */
    text-decoration: underline wavy rgba(205, 133, 63, 0.6);  /* 波浪线（彩色） */
    text-decoration-thickness: 2px;          /* 加粗波浪线 */
    text-underline-offset: 2px;              /* 下移2px */
    padding: 0 2px;
    border-radius: 2px;
    cursor: help;
}
```

**改进**：加粗波浪线 + 偏移

---

### 【数量度量】海绿系 `#2E8B57`

#### 18. 数量 `〖数量〗`

```css
.quantity {
    color: #2E8B57;                          /* 海洋绿 */
    background-color: rgba(255, 248, 220, 0.6);  /* 淡黄底 */
    border-bottom: 1px solid rgba(46, 139, 87, 0.5);  /* 细实线（彩色） */
    padding: 0 2px;
    border-radius: 2px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;  /* 等宽字体 */
    font-weight: 500;
    cursor: help;
}
```

---

## 三、特殊场景：重大历史事件

### 事件标注（新增）

```css
.event-major {
    color: #8B0000;                          /* 深红 */
    background-color: rgba(255, 250, 205, 0.8);  /* 淡金底 */
    background-image: linear-gradient(to right,
        rgba(139, 0, 0, 0.3),
        rgba(255, 193, 7, 0.3));             /* 红→金渐变底纹 */
    background-position: 0 100%;
    background-size: 100% 2px;
    background-repeat: no-repeat;
    padding: 0 4px;
    border-radius: 2px;
    font-weight: 600;
    cursor: help;
}
```

**应用场景**：
- 焚书坑儒
- 鸿门宴
- 楚汉之争
- 垓下之围
- 统一六国

**特点**：深红色 + 淡金底 + 渐变下划线 + 加粗

---

## 四、视觉层次总结

### 底色分层

```
第1层（核心）：rgba(255, 250, 205, 0.7) 淡金底
├─ 帝王人物
├─ 重大历史时间节点
└─ 重大历史事件

第2层（常规）：rgba(255, 248, 220, 0.6) 淡黄底
├─ 大多数人名、地名、官职
├─ 朝代、封国、族群
├─ 典籍、神话
└─ 数量

第3层（次要）：rgba(255, 252, 240, 0.5) 极淡黄底
├─ 时间（普通）
├─ 制度、礼仪、身份
└─ 器物、生物、天文、思想
```

### 下划线层次

```
粗双线（3px double）：帝王人物
粗实线（2px solid）：朝代、重大时间节点
中实线（1px solid）：人名、地名、封国、制度、数量
粗虚线（2px dashed）：（暂无使用）
细虚线（1px dashed）：官职、族群、刑法、器物
粗点线（2px dotted）：（暂无使用）
细点线（1px dotted）：时间、礼仪、思想、生物、天文
粗波浪线（2px wavy）：典籍、神话
渐变线（2px gradient）：重大历史事件
无下划线：身份
```

### 颜色+下划线组合矩阵

| 实体类型 | 文字颜色 | 底色层级 | 下划线 | 粗细 | 颜色匹配 |
|---------|---------|---------|-------|------|---------|
| 帝王 | 深红 #8B0000 | 第1层 | 双线 | 3px | 匹配 |
| 重要人物 | 褐 #8B4513 | 第2层 | 实线 | 2px | 匹配 |
| 普通人名 | 褐 #8B4513 | 第2层 | 实线 | 1px | 匹配 |
| 地名 | 赭褐 #A0522D | 第2层 | 虚线 | 1px | 匹配 |
| 官职 | 褐 #8B4513 | 第2层 | 虚线 | 1px | 匹配 |
| 时间（重大） | 青 #008B8B | 第1层 | 实线 | 2px | 匹配 |
| 时间（普通） | 青 #008B8B | 第3层 | 点线 | 1px | 匹配 |
| 朝代 | 紫 #9370DB | 第2层 | 实线 | 2px | 匹配 |
| 封国 | 紫 #9370DB | 第2层 | 实线 | 1px | 匹配 |
| 族群 | 紫 #9370DB | 第2层 | 虚线 | 1px | 匹配 |
| 制度 | 蓝 #4682B4 | 第3层 | 实线 | 1px | 匹配 |
| 刑法 | 蓝 #4682B4 | 第2层 | 虚线 | 1px | 匹配 |
| 礼仪 | 蓝 #4682B4 | 第3层 | 点线 | 1px | 匹配 |
| 身份 | 蓝 #4682B4 | 第3层 | 无 | - | - |
| 典籍 | 墨绿 #2F4F4F | 第2层 | 波浪 | 2px | 匹配 |
| 思想 | 墨绿 #2F4F4F | 第3层 | 点线 | 1px | 匹配 |
| 器物 | 橙褐 #CD853F | 第3层 | 虚线 | 1px | 匹配 |
| 生物 | 橙褐 #CD853F | 第3层 | 点线 | 1px | 匹配 |
| 天文 | 橙褐 #CD853F | 第3层 | 点线 | 1px | 匹配 |
| 神话 | 橙褐 #CD853F | 第2层 | 波浪 | 2px | 匹配 |
| 数量 | 海绿 #2E8B57 | 第2层 | 实线 | 1px | 匹配 |
| 重大事件 | 深红 #8B0000 | 第1层 | 渐变 | 2px | 渐变 |

**关键设计**：下划线颜色始终与文字颜色匹配，形成统一的视觉组

---

## 五、与v5.0的对比

| 维度 | v5.0 | v6.0 增强版 |
|------|------|-----------|
| **底色** | 统一淡黄 | 3层分级（金/黄/极淡黄） |
| **下划线粗细** | 统一1px | 1-3px分级 |
| **下划线颜色** | 灰色为主 | 与文字颜色匹配 |
| **帝王标识** | 无 | 深红+淡金底+粗双线 |
| **重大事件** | 无 | 渐变下划线 |
| **时间分级** | 无 | 重大/普通两级 |
| **波浪线** | 细 | 加粗+偏移 |
| **无下划线实体** | 2类（身份、器物） | 1类（仅身份） |

---

## 六、实现建议

### 方案A：完全实施v6.0

- **优点**：视觉层次最丰富，区分度最高
- **缺点**：需要额外标注帝王人物、重大事件、时间等级
- **工作量**：中等（需人工标注分级）

### 方案B：部分实施v6.0（推荐）

保留改进：
1. ✅ 下划线颜色与文字颜色匹配（提升视觉和谐度）
2. ✅ 波浪线加粗+偏移（改善典籍、神话显示效果）
3. ✅ 朝代使用2px实线（突出政治重要性）
4. ✅ 器物添加细虚线（不再无下划线）
5. ❌ 暂不实施底色分层（保持统一淡黄底）
6. ❌ 暂不实施帝王特殊样式（需额外标注）
7. ❌ 暂不实施重大事件渐变（需额外标注）

### 方案C：保持v5.0

- **优点**：已经实施，无需修改
- **缺点**：视觉层次相对扁平

---

## 七、下一步行动

### 立即可执行（无需标注变更）

1. 下划线颜色与文字颜色匹配
2. 波浪线加粗+偏移
3. 朝代使用2px实线
4. 器物添加细虚线

### 需要标注支持（未来可选）

1. 帝王人物标识：`〖@帝:秦始皇〗`
2. 重大事件标识：`〖◆事:鸿门宴〗`
3. 时间等级标识：`〖#重:秦统一六国〗`

---

**文档维护**: Claude AI Agent
**创建时间**: 2026-03-19 13:00
**状态**: 📝 **设计方案** - 待评审和实施决策
**基于**: v5.0 实体渲染规划
