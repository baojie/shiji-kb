# CSS版本历史与更新说明

## 当前版本：v5.4 (2026-03-19)

### 版本演进路径

```
v5.0 → v5.3.2 → v5.3.3 → v5.4 (当前)
```

---

## v5.4 (2026-03-19 13:45)

**基础**：v5.3.3 + v6.0方案B精选改进
**文件**：
- `docs/css/shiji-styles.css`
- `css/shiji-styles.css`
- `docs/css/shiji-styles-v5.4.css` (备份)

### 核心改进

#### 1. 朝代样式增强
```css
.dynasty {
    color: #9370DB;
    background-color: #F0E6FF;
    text-decoration: underline solid #9370DB80;
    text-decoration-thickness: 2px;  /* ← 新增：加粗 */
    text-underline-offset: 3px;
    padding: 0 3px;
    border-radius: 2px;
}
```
**效果**：秦、汉、周等朝代名称下划线加粗，更突出政治重要性

#### 2. 典籍样式增强
```css
.book {
    color: #4B0082;
    text-decoration: underline wavy #4B008280;  /* ← 新增：波浪线 */
    text-decoration-thickness: 2px;  /* ← 新增：加粗 */
    text-underline-offset: 3px;  /* ← 新增：偏移 */
    font-style: italic;
}
```
**效果**：《诗》《书》《礼》《乐》等典籍使用传统书名波浪线

#### 3. 神话样式增强
```css
.mythical {
    color: #8B008B;
    text-decoration: underline wavy #8B008B80;  /* ← 新增：波浪线 */
    text-decoration-thickness: 2px;  /* ← 新增：加粗 */
    text-underline-offset: 3px;  /* ← 新增：偏移 */
    font-weight: 500;
}
```
**效果**：夸父、共工等神话人物/事件使用波浪线标识

#### 4. 思想样式优化
```css
.concept {
    color: #2F4F4F;
    text-decoration: underline dotted #2F4F4F80;  /* ← 改进：透明度 */
    text-decoration-thickness: 2px;  /* ← 新增：加粗 */
    text-underline-offset: 3px;
}
```
**效果**：仁、义、礼、智等思想概念点线加粗，更清晰

### 设计原则

#### 保持 v5.3.x 风格
- ✅ 使用 `text-decoration` 而非 `border-bottom`
- ✅ 统一 `text-underline-offset: 3px`
- ✅ 朝代保持淡紫背景 `#F0E6FF`
- ✅ 保持v5.3的整体配色方案

#### 应用 v6.0 精选改进
- ✅ 波浪线加粗到2px（典籍、神话）
- ✅ 朝代下划线加粗到2px
- ✅ 思想点线加粗到2px
- ✅ 颜色透明度优化

### 视觉对比

| 元素 | v5.3.3 | v5.4 |
|------|--------|------|
| 朝代 | 紫底+细实线 | 紫底+**粗实线(2px)** |
| 典籍 | 无下划线 | **波浪线(2px)** |
| 神话 | 无下划线 | **波浪线(2px)** |
| 思想 | 细点线 | **粗点线(2px)** |

---

## v5.3.3 (2026-03-19 13:30)

**修复**：dynasty样式添加紫色下划线

```css
.dynasty {
    color: #9370DB;
    background-color: #F0E6FF;
    text-decoration: underline solid #9370DB80;  /* ← 新增 */
    text-underline-offset: 3px;  /* ← 新增 */
    padding: 0 3px;
    border-radius: 2px;
}
```

**问题**：v5.3.2中朝代只有背景色，缺少下划线，与封国不一致
**解决**：添加紫色下划线，保持与.feudal-state一致的设计模式

---

## v5.3.2 (2026-03-19 02:25)

**主要特性**：
- 使用 `text-decoration` 替代 `border-bottom`
- 统一 `text-underline-offset: 3px`
- 封国使用 `text-decoration: underline solid`
- 思想使用 `text-decoration: underline dotted`

---

## v5.0 (2026-03-19)

**初始版本**：基于《实体渲染规划 v5.0》
- 7色语义分组
- 使用 `border-bottom` 实现下划线
- 统一淡黄底色 `rgba(255, 248, 220, 0.6)`
- 动词使用鲜明底色

---

## 已废弃版本

### v6.0 完整方案（未实施）
- **设计亮点**：底色分3层、帝王特殊标识、重大事件渐变线
- **未实施原因**：需要额外标注工作（标识帝王、重大事件等）
- **保留元素**：波浪线加粗、朝代加粗、思想加粗（已合并到v5.4）
- **参考文档**：`doc/spec/实体渲染规划_v6_增强版.md`

### v5.1 (未发布)
- **内容**：基于v5.0应用v6.0方案B改进
- **状态**：被v5.4取代（v5.4基于v5.3.3更佳）

---

## 文件对照表

| 文件路径 | 版本 | 用途 | MD5 |
|---------|------|------|-----|
| `docs/css/shiji-styles.css` | v5.4 | 主CSS（HTML生成使用） | `c6c89752f20b9b63ffe7309005209415` |
| `css/shiji-styles.css` | v5.4 | 源CSS | `c6c89752f20b9b63ffe7309005209415` |
| `docs/css/shiji-styles-v5.4.css` | v5.4 | 备份 | `c6c89752f20b9b63ffe7309005209415` |
| `docs/css/shiji-styles-v5.css` | v5.0 | 旧版备份 | - |
| `docs/css/shiji-styles-v6.css` | v6.0 | 未使用（完整方案） | - |

---

## 更新日志

### 2026-03-19
- ✅ 创建 v5.4 (融合v5.3.3 + v6.0方案B)
- ✅ 修复 v5.3.3 (dynasty添加下划线)
- ✅ 重新生成所有130章HTML
- ✅ 同步 docs/css/ 和 css/ 两个目录

### 未来计划
- [ ] 浏览器兼容性测试（波浪线支持）
- [ ] 用户反馈收集
- [ ] 考虑是否实施v6.0高级功能（帝王标识、重大事件）

---

**维护者**：Claude AI Agent
**最后更新**：2026-03-19 14:00
