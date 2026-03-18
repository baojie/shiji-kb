# 文本结构数据 (Text Structure)

《史记》130篇的文本结构元数据，包括章节划分、小节标题、段落编号等。

## 目录结构

```
structure/
├── data/
│   └── sections_data.json    # 130篇章节小节数据
└── README.md
```

## 数据文件

### sections_data.json

**用途**: 每章的小节（section）结构数据，用于生成章节导航和目录。

**格式**:
```json
{
  "001_五帝本纪": [
    {
      "anchor": "1",
      "title": "黄帝"
    },
    {
      "anchor": "5",
      "title": "帝颛顼"
    }
  ],
  "002_夏本纪": [
    ...
  ]
}
```

**字段说明**:
- `anchor`: 小节起始的Purple Number（段落编号），用于生成锚点链接 `#pn-{anchor}`
- `title`: 小节标题

**数据来源**:
- 从 `chapter_md/*.tagged.md` 文件中提取 `## 标题` 和 `### 标题` 生成
- 由 `scripts/section_extract_all.py` 自动提取

**使用场景**:
1. 生成docs/index.html中的章节小节链接（`scripts/section_update_index.py`）
2. 为HTML章节页面生成侧边栏导航
3. 支持章节内快速跳转

## 相关脚本

| 脚本 | 功能 |
|------|------|
| `scripts/section_extract_all.py` | 从所有tagged.md提取小节数据，生成sections_data.json |
| `scripts/section_extract.py` | 从单个章节提取小节 |
| `scripts/section_auto_generate.py` | 自动为无小节的章节生成小节标题 |
| `scripts/section_update_index.py` | 将小节链接更新到docs/index.html |
| `temp/tools/fix_sections.py` | 修复小节数量异常的章节 |
| `temp/tools/fix_sections2.py` | 第二批小节修复 |

## 数据规模

- 章节数: 130篇
- 有小节的章节: 约110篇
- 总小节数: 约1500个
- 平均每章小节数: 约12个

## 设计原则

1. **锚点复用Purple Numbers** — 小节锚点使用已有的段落编号系统，无需额外ID
2. **层级简化** — 最多支持两级小节（## 和 ###），避免过度复杂
3. **自动提取优先** — 从Markdown标题自动提取，减少手工维护
4. **渐进增强** — 无小节的章节仍可正常阅读，小节仅作为导航增强

## 未来扩展

- [ ] 支持小节摘要（summary字段）
- [ ] 支持小节类型标注（type: 人物/事件/制度等）
- [ ] 生成章节大纲可视化（树状图/思维导图）
- [ ] 跨章节小节关联（如"项羽本纪"的垓下之战 → "高祖本纪"对应段落）
