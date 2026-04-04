# Index.html 设计说明与保护机制

## 概述

`docs/index.html` 是《史记知识库》的首页，包含精心设计的章节索引、项目介绍、实体标注说明等内容。本文档说明 index.html 的设计特性、保护机制和更新方法。

---

## 当前设计特性（2026-04-02版本）

### 页面标题
**史记知识库 - AI驱动的历史知识图谱**

### 视觉设计

#### 布局系统
- ✨ **卡片式布局**：使用 `chapter-card` 和 `chapter-grid` 类实现现代化卡片布局
- 📱 **响应式设计**：自适应不同屏幕尺寸（最大宽度1200px）
- 🎨 **古典配色**：褐色主题（#8B4513）+ 金色点缀（#d4af37）+ 米黄背景（#faf8f0）

#### 交互效果
- 🔽 **可折叠简介**：项目简介部分可点击折叠/展开，带平滑过渡动画
  - 使用 `.intro.collapsed` 状态控制
  - 带旋转箭头指示器（`.toggle-arrow`）
- 🔄 **悬停效果**：卡片悬停时有阴影加深效果（无位移动画）
- 🎯 **章节展开/折叠**：每个章节可独立展开小节列表
  - 使用 `.section-toggle` 控制
  - 带展开/收起指示符

#### 样式组件
- **section-header**：渐变色标题栏（135度渐变，#8B4513 → #A0522D）
- **chapter-card**：章节卡片（白色背景，左侧金色边框，圆角8px）
- **entity-tags**：18类实体标签（彩色编码，横向排列）
- **chapter-num**：章节编号（金色圆形徽章）

### 内容组织

#### 章节分组
- 📖 **五大分类**：本纪、表、书、世家、列传
- 📊 **每组说明**：包含 `.section-desc` 说明该类别特点
- 🔢 **章节总数**：130篇完整章节

#### 章节信息
- **章节编号**：001-130，三位数编号
- **章节标题**：中文标题 + 链接到章节HTML
- **小节链接**：部分章节包含小节快速跳转（Purple Numbers集成）
- **链接格式**：`chapters/NNN_章节名.html`（无 `.tagged` 后缀）

#### 实体标注说明
包含18类实体标签：
1. 人名（.person）- 橙色
2. 地名（.place）- 蓝色
3. 官职（.official）- 紫色
4. 身份（.identity）- 青色
5. 时间（.time）- 绿色
6. 氏族（.dynasty）- 深红
7. 邦国（.feudal-state）- 靛蓝
8. 制度（.institution）- 棕色
9. 族群（.tribe）- 橄榄色
10. 器物（.artifact）- 灰色
11. 天文（.astronomy）- 深蓝
12. 神话（.mythical）- 品红
13. 生物（.biology）- 青绿
14. 典籍（.book）- 深紫
15. 礼仪（.ritual）- 粉色
16. 刑法（.legal）- 暗红
17. 思想（.concept）- 深青
18. 数量（.quantity）- 褐色

### 技术特性

#### CSS类识别标志
脚本通过检测以下CSS类来识别详细设计版本：
- `chapter-card` - 章节卡片
- `chapter-grid` - 章节网格布局
- `section-header` - 分类标题
- `intro-content` - 简介内容区
- `section-toggle` - 展开/折叠控制

#### JavaScript功能
- 简介折叠/展开逻辑
- 章节小节列表展开/折叠
- 本地存储保存折叠状态

---

## 保护机制

### 1. 自动检测保护

`generate_all_chapters.py` 脚本已添加智能检测：
- ✅ 运行时自动检查 `index.html` 是否包含详细设计标志（`chapter-card` 或 `chapter-grid` 类）
- ✅ 如检测到详细设计版本，**自动跳过生成**，避免覆盖
- ⚠️ 只有当文件不存在或为简单版本时，才会生成新的 index.html

### 2. 模板备份

- **模板文件**：`docs/index.html.template`
- **用途**：当前详细设计的完整备份副本
- **更新时机**：每次对 index.html 进行重大更新后
- **恢复方法**：如果 index.html 被意外覆盖，可从模板恢复：
  ```bash
  cp docs/index.html.template docs/index.html
  ```

---

## 如何更新 index.html

### 安全更新方法

#### 1. 手动修改内容（推荐）
直接编辑 `docs/index.html`，Git会追踪所有变更

**常见修改场景**：
- 添加新章节：在对应分类的 `.chapter-grid` 中添加 `.chapter-card` 块
- 更新章节描述：修改 `.chapter-desc` 内容
- 调整样式：修改 `<style>` 标签内的CSS规则
- 添加小节链接：在 `.section-links` 中添加链接

#### 2. 添加新章节小节链接
如果有专用脚本（待开发）：
```bash
# 1. 提取新章节的小节信息
python scripts/extract_sections.py

# 2. 更新 index.html（脚本会保留现有设计）
python scripts/update_index_with_sections.py
```

#### 3. 样式调整
- **内联修改**：直接修改文件内的 `<style>` 标签
- **外部CSS**：提取到 `docs/css/` 目录（需要同步更新链接）

#### 4. 重大更新后同步模板
```bash
cp docs/index.html docs/index.html.template
git add docs/index.html.template
git commit -m "更新index模板到最新版本"
```

### ⚠️ 危险操作（避免）

❌ **不要运行** `generate_all_chapters.py` 并期望它更新 index.html
   - 该脚本只会生成简单版本的索引
   - 已添加保护，会自动跳过详细设计版本

❌ **不要删除** `index.html.template` 备份文件
   - 这是恢复详细设计的唯一途径（除了Git历史）

❌ **不要直接覆盖** `docs/index.html`
   - 除非有完整备份或确定需要重置

---

## 恢复详细设计

如果 `index.html` 被意外覆盖，按以下步骤恢复：

### 方法1：从模板恢复（最快）
```bash
cp docs/index.html.template docs/index.html
git diff docs/index.html  # 检查差异
git add docs/index.html
git commit -m "从模板恢复详细设计的index.html"
```

### 方法2：从Git历史恢复（最可靠）
```bash
# 查找最近的良好版本
git log --oneline --follow docs/index.html

# 查看某个版本的内容
git show <commit-hash>:docs/index.html | head -50

# 恢复到指定版本
git checkout <commit-hash> -- docs/index.html
```

### 方法3：从GitHub Pages查看
如果已经发布到GitHub Pages，可以：
1. 访问线上版本
2. 查看源代码（右键 → 查看页面源代码）
3. 复制完整HTML保存到本地

---

## 发布流程保护

### publish_to_docs.sh 脚本
该脚本**不会覆盖** index.html，仅执行以下安全操作：
- ✅ 更新章节HTML文件
- ✅ 修复CSS/JS路径引用
- ✅ 移除文件名中的 `.tagged` 后缀
- ✅ 更新 index.html 中的链接后缀（仅替换 `.tagged.html` → `.html`）

**不会**：
- ❌ 重新生成 index.html
- ❌ 覆盖现有设计
- ❌ 删除自定义内容

---

## 版本历史追踪

### Git 保护
所有对 `index.html` 的修改都会被 Git 追踪，可随时回退：

```bash
# 查看修改历史
git log --follow docs/index.html

# 查看最近5次提交
git log --oneline --follow docs/index.html -5

# 查看某次提交的详细内容
git show <commit-hash>:docs/index.html

# 查看两个版本之间的差异
git diff <commit1> <commit2> -- docs/index.html

# 恢复到之前的版本
git checkout <commit-hash> -- docs/index.html
```

### 重要版本记录
- **2026-04-02**：当前版本（AI驱动的历史知识图谱，章节展开/折叠功能）
- **2026-02-08**：首次创建详细设计版本（卡片布局、可折叠简介）
- **d4bfcb4**：恢复详细设计的 index.html（包含卡片布局、章节描述）

---

## 最佳实践

### ✅ 推荐做法
1. **修改前备份**：重大修改前先 `git commit` 或复制一份
2. **测试后提交**：在浏览器中测试无误后再 `git commit`
3. **同步模板**：重大更新后执行 `cp docs/index.html docs/index.html.template`
4. **保留注释**：在HTML中添加注释说明自定义部分
5. **小步提交**：每次修改一个功能，及时提交，便于回退

### ❌ 避免做法
1. 盲目运行批量生成脚本
2. 未备份直接大规模修改
3. 删除模板文件
4. 忽略Git追踪信息
5. 一次性修改多个功能导致难以定位问题

---

## 相关文件

| 文件 | 用途 | 是否可修改 |
|------|------|------------|
| `docs/index.html` | 线上展示的首页 | ✅ 手动修改，但需谨慎 |
| `docs/index.html.template` | 详细设计备份模板 | ✅ 作为 index.html 的完整备份 |
| `docs/index.html.bak` | 临时备份（如存在） | ⚠️ 可选，手动备份时创建 |
| `generate_all_chapters.py` | 批量生成章节HTML | ⚠️ 已添加保护，自动跳过详细版 |
| `scripts/update_index_with_sections.py` | 更新小节链接（如存在） | ✅ 安全使用，保留设计 |
| `scripts/publish_to_docs.sh` | 发布脚本（如存在） | ✅ 不会覆盖设计 |

---

## 技术细节

### HTML结构层次
```
index.html
├── head
│   ├── title: 史记知识库 - AI驱动的历史知识图谱
│   ├── link: css/shiji-styles.css
│   └── style: 内联样式（主要设计）
├── body
│   ├── h1: 史记知识库
│   ├── .intro（可折叠项目简介）
│   │   ├── h2（带toggle-arrow）
│   │   └── .intro-content
│   │       ├── 项目说明段落
│   │       └── .entity-tags（18类实体标签）
│   ├── .section（本纪）
│   │   ├── .section-header
│   │   │   ├── h2: 本纪
│   │   │   └── .section-desc
│   │   └── .chapter-grid
│   │       └── .chapter-card × N
│   │           ├── .chapter-title
│   │           │   ├── .chapter-num
│   │           │   └── a（章节链接）
│   │           ├── .chapter-desc（章节说明）
│   │           └── .section-links（小节链接，可选）
│   ├── .section（表）
│   ├── .section（书）
│   ├── .section（世家）
│   └── .section（列传）
└── script: JavaScript交互逻辑
```

### CSS变量（可提取为外部样式）
```css
/* 主要颜色 */
--primary-brown: #8B4513;
--secondary-brown: #A0522D;
--gold: #d4af37;
--background: #faf8f0;
--card-bg: #ffffff;
--intro-bg: #fff9e6;

/* 尺寸 */
--max-width: 1200px;
--border-radius: 8px;
--card-shadow: 0 2px 4px rgba(0,0,0,0.05);
```

---

## 维护计划

### 定期检查（每月）
- [ ] 验证所有章节链接有效
- [ ] 检查模板是否与 index.html 同步
- [ ] 测试可折叠功能正常工作
- [ ] 验证响应式布局在不同设备上的表现

### 功能增强（待开发）
- [ ] 添加搜索功能（章节标题搜索）
- [ ] 添加筛选功能（按分类、标签筛选）
- [ ] 提取CSS到外部文件（便于维护）
- [ ] 开发自动更新小节链接的脚本
- [ ] 添加阅读进度追踪（localStorage）

---

**创建时间**：2026-02-08
**重大更新**：2026-04-02（添加章节展开/折叠功能）
**本文档更新**：2026-04-05
**维护者**：[@baojie](https://github.com/baojie)
