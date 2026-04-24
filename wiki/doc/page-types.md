# 页面类型（type 字段）定义

Wiki 每个页面的 frontmatter 必须包含 `type` 字段。

## 类型一览

| type | 中文名 | 说明 |
|------|--------|------|
| `person` | 人名 | 史记中出现的人物 |
| `place` | 地名 | 地理位置、地点 |
| `state` | 邦国 | 诸侯国、王国、政权 |
| `official` | 官职 | 官职名称 |
| `identity` | 身份 | 社会身份、称谓 |
| `dynasty` | 朝代 | 朝代、历史时期 |
| `event` | 事件 | 史记中的具体事件 |
| `concept` | 概念 | 抽象概念、思想 |
| `chapter` | 章节 | 史记130篇章节页 |
| `topic` | 主题 | 主题汇总页（已废弃，迁移至 overview/concept）|
| `overview` | 综述 | 综合性主题页 |
| `list` | 列表 | 通过 ::: query 生成的动态列表页 |
| `meta` | 元页 | 系统元数据页 |
| `sanwen` | 散文 | 史记散文文本页 |
| `story` | 故事 | 故事/叙事页 |
| `redirect` | 重定向 | 指向规范页的重定向（含 `redirect_to` 字段）|

## redirect 页格式

```markdown
---
id: 冗余页名
type: redirect
label: 冗余页名
redirect_to: 规范页名
---

> **重定向**：本页重定向至 [[规范页名]]。
```

## list 页格式

见 [query-syntax.md](query-syntax.md)。
