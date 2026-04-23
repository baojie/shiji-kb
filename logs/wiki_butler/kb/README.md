# Butler 知识库目录规范

## 目录位置

```
logs/wiki_butler/kb/
```

## 命名规范

```
w<N>_<skill_abbr>.md
```

| 文件 | 对应 Skill | 内容 |
|------|-----------|------|
| `w5_ops.md` | SKILL_W5 反思与自改 | 已验证的操作规则（哪类 action 在哪种条件下失败/成功） |
| `w7_citations.md` | SKILL_W7 引文核验 | 已验证的引文真实性结论、章节可信度 |
| `w9_schemas.md` | SKILL_W9 图式反思 | 已定稿的页面模板规则（schema_patterns/ 的提炼结论） |
| `w11_taxonomy.md` | SKILL_W11 分类元反思 | 已验证的分类判断规则 |

## 写入规范（所有 KB 文件共用）

1. **只写定论**：猜测/待验证的内容留在 reflections/、schema_patterns/，不进 KB
2. **标注来源轮次**：每条规则注明 `[R<N> 确认]`，可追溯
3. **格式**：Markdown 二级标题分组，每条规则一行，用 `-` 列表
4. **追加不替换**：每次写入是追加新规则或更新已有规则，不清空重写
5. **覆盖旧规则时**：用 `[R<N> 更新，原规则见 R<M>]` 标注

## 读取规范

- Butler 每次 invocation 启动时读取所有 KB 文件（与 queue.md 同级必读）
- KB 文件内容直接影响本轮行动决策
