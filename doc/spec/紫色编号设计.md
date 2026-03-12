# 设计说明 - Purple Numbers 致敬

## 段落编号的紫色设计

本项目中的段落编号使用**淡紫色**配色方案，这是对计算机先驱 **Doug Engelbart** 的 **Purple Numbers** 概念的致敬。

## Purple Numbers 的历史

### Doug Engelbart 与超文本

**Douglas Engelbart**（1925-2013）是计算机科学的先驱，他在 1960 年代提出了许多革命性的概念：

- **鼠标**的发明者
- **超文本**（Hypertext）的早期倡导者
- **协同工作**（Collaborative Work）系统的先驱
- **知识增强**（Augmenting Human Intellect）理论的提出者

### Purple Numbers 的诞生

在 1960 年代，Engelbart 在斯坦福研究院（SRI）开发 **NLS**（oN-Line System）时，提出了一个重要概念：

> **为文档中的每个段落分配唯一的、可引用的编号**

这些编号在屏幕上显示为**紫色**，因此被称为 **Purple Numbers**（紫色数字）。

### Purple Numbers 的意义

Purple Numbers 解决了一个关键问题：**如何精确引用文档中的特定段落？**

在 Purple Numbers 之前：
- ❌ "请看第三页第二段" - 不同版本页码可能不同
- ❌ "在讨论协作的那一段" - 描述模糊，难以定位

有了 Purple Numbers：
- ✅ "请看段落 [3.2.5]" - 永久、唯一、精确
- ✅ 可以创建指向特定段落的超链接
- ✅ 支持版本控制和协同编辑

### 对现代互联网的影响

Purple Numbers 的概念深刻影响了：

1. **URL 片段标识符**（Fragment Identifiers）
   - 例如：`https://example.com/page#section-3`
   - 可以链接到页面的特定部分

2. **维基百科的章节链接**
   - 每个章节都有唯一的锚点
   - 可以直接链接到特定章节

3. **学术引用系统**
   - DOI（Digital Object Identifier）
   - 精确到段落的引用

4. **协同编辑工具**
   - Google Docs 的评论和建议功能
   - GitHub 的行号引用

## 本项目的实现

### 设计理念

我们在《史记》知识库中采用段落编号系统，并使用紫色配色，是为了：

1. **致敬先驱**：向 Doug Engelbart 的创新精神致敬
2. **精确引用**：使读者能够精确引用和讨论特定段落
3. **知识链接**：为未来的交叉引用和知识图谱奠定基础
4. **历史传承**：将古代文献与现代知识管理技术结合

### 配色方案

```css
.para-num {
    background-color: #F3E5F5;  /* 淡紫色背景 - 柔和不刺眼 */
    color: #7B1FA2;             /* 紫色文字 - 清晰可读 */
    border: 1px solid #CE93D8;  /* 淡紫色边框 - 优雅边界 */
}
```

这个配色方案：
- 🎨 **视觉和谐**：与古籍风格的米黄色背景协调
- 👁️ **易于识别**：紫色在文本中醒目但不突兀
- 📖 **阅读友好**：淡雅的色调不干扰正文阅读
- 💜 **历史致敬**：紫色直接呼应 Purple Numbers

## 扩展阅读

### Doug Engelbart 的演讲

1968 年 12 月 9 日，Doug Engelbart 在旧金山进行了一场著名的演示，被称为 **"The Mother of All Demos"**（所有演示之母）。在这场演示中，他展示了：

- 鼠标
- 超文本
- 视频会议
- 协同编辑
- 窗口系统

这场演示预见了现代计算机的几乎所有核心功能。

### 相关资源

- [Doug Engelbart Institute](https://www.dougengelbart.org/)
- [Purple Numbers 规范](http://www.burningchrome.com/~cdent/mt/archives/000108.html)
- [The Mother of All Demos - 视频](https://www.youtube.com/watch?v=yJDv-zdhzMY)

## 未来展望

在本项目中，Purple Numbers 不仅是视觉设计，更是功能基础：

- [ ] 实现段落的永久链接（Permalink）
- [ ] 支持精确到段落的引用和分享
- [ ] 构建基于段落的知识图谱
- [ ] 实现段落级别的评论和注释

---

> "The better we get at getting better, the faster we will get better."
> — Doug Engelbart

**致敬 Doug Engelbart，致敬所有为知识增强而努力的先驱们。**

---

**文档创建日期**: 2026-01-23
**作者**: 史记知识库项目组
