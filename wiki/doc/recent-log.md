# recent.json 修订日志格式与轮转机制

## 文件位置

| 文件 | 说明 |
|------|------|
| `wiki/public/recent.json` | 滚动窗口（最近 500-600 条，前端直接读此文件） |
| `wiki/public/log/recent.N.json` | 归档批次（每档 100 条，永久保留，仅供历史查询） |

## recent.json 格式

```json
{
  "entries": [
    {
      "page": "霸陵",
      "rev_id": "20260423-171912-abc123",
      "timestamp": "2026-04-23T17:19:12Z",
      "author": "butler",
      "summary": "butler/edit: 补充人物信息",
      "parent_rev": "20260423-161234-def456",
      "content_hash": "sha256:abcdef...",
      "size": 1234
    }
  ],
  "rotations": 11
}
```

- `entries`：按时间升序（最旧在前），始终保留最近 500-600 条
- `rotations`：已归档批次数，等于 `log/` 目录中最大编号

## 滚动窗口机制

- **`recent.json`** = 最新 `WINDOW_SIZE`（600）条的滚动窗口
- **归档触发**：`entries` 超过 `WINDOW_SIZE`（600）时，把最旧的 `ARCHIVE_BATCH`（100）条移至 `log/recent.{N+1}.json`
- **保留策略**：归档文件永久保留，不删除
- **设计目标**：前端单次 fetch `recent.json` 即可获得足够显示 500 条的数据，无需循环补档

## 前端显示逻辑

1. 读取 `recent.json`（单次 fetch）
2. 取最后 500 条（`entries.slice(-500)`），逆序显示（最新在前）
3. 分页，每页 50 条

## 写入方式

由 `wiki/scripts/butler/record_revision.py` 在每次页面编辑后调用。
不含 `content` 字段（完整内容存于 `wiki/public/history/<slug>.json`）。
