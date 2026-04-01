# GitHub Discussions 内容模板

本目录包含准备发布到 GitHub Discussions 的读音考证内容。

## 使用方法

### 1. 创建 GitHub Discussion

在您的仓库中：
1. 进入 **Discussions** 标签页
2. 点击 **New discussion**
3. 选择分类：**Q&A** 或 **General**
4. 将下面对应文件的内容复制粘贴

### 2. 已准备的内容

| 文件 | 标题 | 建议分类 |
|------|------|---------|
| `01_身毒读音考证.md` | 身毒的读音：shēn dú 还是 yuán dú？ | Q&A |
| `02_月氏读音考证.md` | 月氏的读音：yuè zhī 还是 ròu zhī？ | Q&A |

### 3. 创建后更新链接

创建 Discussion 后，您会得到一个 URL，格式类似：
```
https://github.com/yourusername/shiji-kb/discussions/1
https://github.com/yourusername/shiji-kb/discussions/2
```

然后更新 `docs/pronunciation-debates.html` 中的链接：

**第225行**（身毒）：
```html
<a href="https://github.com/yourusername/shiji-kb/discussions/1" class="discussion-link" target="_blank">
```
改为实际的 Discussion URL

**第251行**（月氏）：
```html
<a href="https://github.com/yourusername/shiji-kb/discussions/2" class="discussion-link" target="_blank">
```
改为实际的 Discussion URL

### 4. 仓库设置

如果您的仓库尚未启用 Discussions：

1. 进入仓库的 **Settings**
2. 找到 **Features** 部分
3. 勾选 **Discussions**

## 内容特点

两篇考证文章都包含：

✅ **史记原文出处** - 完整引用相关段落
✅ **古注考证** - 《索隐》《正义》《集解》三家注
✅ **其他文献佐证** - 《汉书》《后汉书》《新唐书》等
✅ **语言学分析** - 上古音、中古音、梵文/吐火罗语词源
✅ **读音争议分析** - 详细解释每种读音的来源和依据
✅ **本知识库的选择** - 说明采用的读音及理由
✅ **参考文献** - 完整的古籍和现代学术文献引用

## 维护说明

当需要添加新的读音争议词汇时：

1. 在本目录创建新的 `.md` 文件（如 `03_某词读音考证.md`）
2. 参考现有文件的结构编写内容
3. 在 `docs/pronunciation-debates.html` 中添加新条目
4. 创建 GitHub Discussion 后更新链接
5. 更新本 README 文件

## 模板结构

每篇考证文章的标准结构：

```markdown
# [词汇]的读音：[读音A] 还是 [读音B]？

## 一、史记原文出处
## 二、古注考证
## 三、其他文献佐证
## 四、语言学分析
## 五、读音争议分析
## 六、本知识库的选择
## 七、参考文献
## 八、欢迎讨论
```

---

**最后更新**：2026-04-01
