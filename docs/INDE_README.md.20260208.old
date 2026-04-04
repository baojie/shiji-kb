# Index.html 设计保护说明

## 概述

`docs/index.html` 是项目的首页，包含精心设计的章节索引、项目介绍、实体标注说明等内容。为防止被自动脚本覆盖，已实施以下保护措施。

---

## 保护机制

### 1. 自动检测保护

`generate_all_chapters.py` 脚本已添加智能检测：
- ✅ 运行时自动检查 `index.html` 是否包含详细设计标志（`chapter-card` 或 `chapter-grid` 类）
- ✅ 如检测到详细设计版本，**自动跳过生成**，避免覆盖
- ⚠️ 只有当文件不存在或为简单版本时，才会生成新的 index.html

### 2. 模板备份

- **模板文件**：`docs/index.html.template`
- **用途**：当前详细设计的备份副本
- **恢复方法**：如果 index.html 被意外覆盖，可从模板恢复：
  ```bash
  cp docs/index.html.template docs/index.html
  ```

---

## 当前设计特性

当前 `index.html` 包含以下精心设计的元素，**请勿随意覆盖**：

### 视觉设计
- ✨ **卡片式布局**：使用 `chapter-card` 和 `chapter-grid` 类实现现代化卡片布局
- 🎨 **渐变色标题**：section-header 使用渐变背景色
- 🔄 **悬停效果**：卡片悬停时有平滑的动画效果
- 📱 **响应式设计**：自适应不同屏幕尺寸

### 内容组织
- 📖 **分组展示**：按本纪、表、书、世家、列传分类
- 📝 **章节描述**：每章配有详细说明文字
- 🔗 **小节链接**：部分章节包含小节快速跳转链接
- 📊 **统计信息**：显示实体标注类型和Purple Numbers说明

### 交互功能
- 🔽 **可折叠简介**：项目简介部分可点击折叠/展开
- 🔗 **精确链接**：所有链接已更新为正确的相对路径（无 `.tagged` 后缀）
- 🎯 **Purple Numbers集成**：小节链接直接跳转到特定段落

---

## 如何更新 index.html

### 安全更新方法

#### 1. 添加新章节小节链接
使用专用脚本（推荐）：
```bash
# 1. 提取新章节的小节信息
python extract_sections.py

# 2. 更新 index.html（脚本会保留现有设计）
python update_index_with_sections.py
```

#### 2. 手动修改内容
直接编辑 `docs/index.html`，Git会追踪所有变更

#### 3. 样式调整
修改文件内的 `<style>` 标签，或提取到外部CSS文件

### ⚠️ 危险操作（避免）

❌ **不要运行** `generate_all_chapters.py` 并期望它更新 index.html
   - 该脚本只会生成简单版本的索引
   - 已添加保护，会自动跳过详细设计版本

❌ **不要删除** `index.html.template` 备份文件
   - 这是恢复详细设计的唯一途径

❌ **不要直接覆盖** `docs/index.html`
   - 除非有完整备份或确定需要重置

---

## 版本历史追踪

### Git 保护
所有对 `index.html` 的修改都会被 Git 追踪，可随时回退：

```bash
# 查看修改历史
git log --follow docs/index.html

# 查看某次提交的内容
git show <commit-hash>:docs/index.html

# 恢复到之前的版本
git checkout <commit-hash> -- docs/index.html
```

### 重要提交记录
- **d4bfcb4**：恢复详细设计的 index.html（包含卡片布局、章节描述）
- **当前版本**：添加可折叠项目简介功能

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

## 恢复详细设计

如果 `index.html` 被意外覆盖，按以下步骤恢复：

### 方法1：从模板恢复
```bash
cp docs/index.html.template docs/index.html
git diff docs/index.html  # 检查差异
git add docs/index.html
git commit -m "恢复详细设计的index.html"
```

### 方法2：从Git历史恢复
```bash
# 查找最近的良好版本
git log --oneline --follow docs/index.html

# 恢复到指定版本
git checkout <commit-hash> -- docs/index.html
```

### 方法3：从GitHub Pages查看
如果已经发布到GitHub Pages，可以：
1. 访问线上版本
2. 查看源代码（右键 → 查看页面源代码）
3. 复制完整HTML保存到本地

---

## 最佳实践

### ✅ 推荐做法
1. **修改前备份**：重大修改前先 `git commit` 或复制一份
2. **使用专用脚本**：用 `update_index_with_sections.py` 更新小节链接
3. **测试后提交**：在浏览器中测试无误后再 `git commit`
4. **保留注释**：在HTML中添加注释说明自定义部分

### ❌ 避免做法
1. 盲目运行批量生成脚本
2. 未备份直接大规模修改
3. 删除模板文件
4. 忽略Git追踪信息

---

## 相关文件

| 文件 | 用途 | 是否可修改 |
|------|------|------------|
| `docs/index.html` | 线上展示的首页 | ✅ 手动修改，但需谨慎 |
| `docs/index.html.template` | 详细设计备份模板 | ❌ 仅用于恢复，不要修改 |
| `generate_all_chapters.py` | 批量生成章节HTML | ⚠️ 已添加保护，自动跳过详细版 |
| `update_index_with_sections.py` | 更新小节链接 | ✅ 安全使用，保留设计 |
| `publish_to_docs.sh` | 发布脚本 | ✅ 不会覆盖设计 |

---

## 技术细节

### 设计标志检测
脚本通过检测以下CSS类来识别详细设计版本：
- `chapter-card`
- `chapter-grid`
- `section-header`
- `intro-content`

### 模板同步
每次对 `index.html` 进行重大更新后，建议同步更新模板：
```bash
cp docs/index.html docs/index.html.template
git add docs/index.html.template
git commit -m "更新index模板"
```

---

**创建时间**：2026-02-08
**最后更新**：2026-02-08
**维护者**：[@baojie](https://github.com/baojie)
