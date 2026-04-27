# recent.jsonl 修订日志格式与轮转机制

## 文件位置

| 文件 | 说明 |
|------|------|
| `wiki/public/recent.jsonl` | 滚动窗口（最近 1000 条，前端直接读此文件，每行一条 JSON） |
| `wiki/logs/recent/recent.N.jsonl` | 归档批次（每档 500 条，永久保留，仅供历史查询） |

## recent.jsonl 格式

每行一个 JSON 对象，按时间升序（最旧在前）：

```jsonl
{"page":"霸陵","rev_id":"20260423-171912-abc123","timestamp":"2026-04-23T17:19:12Z","author":"butler","summary":"butler/edit: 补充人物信息","parent_rev":"20260423-161234-def456","content_hash":"sha256:abcdef...","size":1234}
{"page":"晏孺子","rev_id":"20260427-055608-bd7b87","timestamp":"2026-04-27T05:56:08Z","author":"butler","summary":"butler/enrich: 补充内容","parent_rev":"...","content_hash":"sha256:...","size":2345}
```

## 滚动窗口机制

- **`recent.jsonl`** = 最新 `WINDOW_SIZE`（1000）条的滚动窗口（JSONL 格式）
- **归档触发**：行数超过 `WINDOW_SIZE` 时，把最旧的 `ARCHIVE_BATCH`（500）条移至 `wiki/logs/recent/recent.{N+1}.jsonl`
- **保留策略**：归档文件永久保留，不删除
- **设计目标**：前端单次 fetch `recent.jsonl` 即可获得足够显示 500 条的数据

## 前端显示逻辑

1. 读取 `recent.jsonl`（单次 fetch，text 格式）
2. 按 `\n` 拆行，过滤空行，每行 `JSON.parse`
3. 取最后 500 条（`allEntries.slice(-500)`），逆序显示（最新在前）
4. 分页，每页 50 条

## 写入方式

由 `wiki/scripts/butler/record_revision.py` 在每次页面编辑后调用。
不含 `content` 字段（完整内容存于 `wiki/public/history/<slug>.json`）。
