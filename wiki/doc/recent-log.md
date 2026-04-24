# recent.json 修订日志格式与轮转机制

## 文件位置

| 文件 | 说明 |
|------|------|
| `wiki/public/recent.json` | 当前活跃日志（append-only） |
| `wiki/public/log/recent.N.json` | 轮转归档（永久保留） |

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

- `entries`：按时间升序（最旧在前），append-only
- `rotations`：已轮转次数，等于 `log/` 目录中最大编号

## 轮转机制

类似 Linux logrotate：

- **触发条件**：`entries` 超过 `ROTATE_LIMIT`（当前 100 条）
- **操作**：`recent.json` → `log/recent.{N+1}.json`，新建空 `recent.json`
- **保留策略**：永久保留所有轮转文件，不删除

## 前端显示逻辑

1. 读取 `recent.json`（当前活跃日志）
2. 若条数不足 500，从 `log/recent.{rotations}.json` 开始往前补充
3. 取最后 500 条，逆序显示（最新在前）
4. 分页，每页 50 条

## 写入方式

由 `wiki/scripts/butler/record_revision.py` 在每次页面编辑后调用。
不含 `content` 字段（完整内容存于 `wiki/public/history/<slug>.json`）。
