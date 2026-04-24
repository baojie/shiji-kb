# shiji-kb-browser

在浏览器端直接查询 SQLite 数据库的骨架。**服务器只托管静态文件，不运行任何代码，也不依赖任何第三方服务。**

基于 [`sql.js-httpvfs`](https://github.com/phiresky/sql.js-httpvfs):
浏览器通过 HTTP Range 请求按需读取 SQLite 文件的 4KB 页，不用下载整个数据库。一个带合适索引的查询通常只需要几 KB 传输。

## 运行

```bash
python3 serve.py
# -> http://localhost:5247
```

就这一个命令，零依赖。`serve.py` 是本仓库里的一个脚本，正确处理 Range 请求（Python 自带的 `http.server` 不支持）。

## 目录结构

```
shiji-kb-browser/
├── db/
│   ├── build.py              构建 SQLite 的脚本（改这个来塞入真实数据）
│   └── shiji.sqlite3         生成的数据库
├── public/                   ← 只部署这个目录
│   ├── index.html            前端页面（纯原生 JS，无构建）
│   ├── db-config.json        sql.js-httpvfs 指向数据库的配置
│   ├── shiji.sqlite3         数据库副本
│   └── vendor/
│       ├── index.js          sql.js-httpvfs 主库（UMD，~8KB）
│       ├── sqlite.worker.js  Web Worker（~84KB）
│       └── sql-wasm.wasm     SQLite WASM（~1.2MB，只下载一次，浏览器会缓存）
└── serve.py                  本地预览（支持 Range）
```

## 工作原理

1. 浏览器加载 `index.html` + `vendor/index.js`。
2. `createDbWorker` 启动一个 Web Worker。
3. Worker 加载 `sql-wasm.wasm`（SQLite 编译成 WASM），并注册一个 HTTP Range 虚拟文件系统。
4. SQLite 需要读 `shiji.sqlite3` 的哪几页，就用 `Range: bytes=N-M` 请求去拿那几 4KB。
5. 因为数据库有索引，B-tree 查找只会碰到少量页。典型查询只读 2-10 页（8-40KB）。
6. 所有 SQL 在浏览器里跑。服务器什么都不知道。

## 部署到真实服务器

### 首选：静态文件托管

`public/` 整个目录扔到任何静态托管都行。以下都**默认支持 Range 请求**，开箱即用：

- GitHub Pages
- Cloudflare Pages
- Netlify
- AWS S3 + CloudFront
- Nginx（默认就支持）
- 你的 VPS 上随便一个 `nginx` 或 `caddy`

### 注意事项

- **CORS**：如果数据库和前端在不同源，服务器需要返回：
  ```
  Access-Control-Allow-Origin: *
  Access-Control-Expose-Headers: Content-Length, Content-Range, Accept-Ranges
  ```
  同源部署则无需任何 CORS 配置。

- **压缩**：**不要**对 `.sqlite3` 文件启用 gzip/brotli。压缩后 Range 请求的字节偏移会对不上，直接坏掉。如果用 nginx，给 sqlite 的 location 加 `gzip off;`。WASM 可以压缩。

- **缓存**：生产环境建议让 sqlite 文件带 hash（如 `shiji-v1a2b3c.sqlite3`），然后 `Cache-Control: public, max-age=31536000, immutable`。每次数据更新就改文件名，避免 Range 响应被旧缓存污染。

## 改成你自己的数据

编辑 `db/build.py`：把 `SAMPLE_ENTITIES` 替换成你真实数据的导入逻辑，调整表 schema 和索引。关键：

```python
c.execute("PRAGMA page_size = 4096")  # 必须在建表之前
```

并且**为所有 WHERE 子句中的列建索引**，否则浏览器会被迫下载整张表。用 covering index（把 SELECT 出来的列也放进索引）让查询只读索引页，不读数据页：

```sql
CREATE INDEX idx ON entity (type, name, id, dynasty, birth_year);
--                ^^^^^^^^^^  过滤列    ^^^^^^^^^^^^^^^^^^^^^^^^^^  返回列
```

然后：

```bash
python3 db/build.py
cp db/shiji.sqlite3 public/shiji.sqlite3
```

## 性能调优

用 Chrome DevTools 的 Network 面板看 Range 请求数量。一个好的查询：

- 少量 Range 请求（< 20 次）
- 每次小（通常 4KB）
- 主要命中的是索引页

如果看到几百次请求，说明缺索引——浏览器在做全表扫描。

浏览器控制台可以跑：

```js
await _dbWorker.db.query("EXPLAIN QUERY PLAN SELECT ... FROM entity WHERE ...")
```

看到 `SCAN TABLE` 就是全表扫。`SEARCH TABLE x USING INDEX y` 或 `USING COVERING INDEX` 才是好的。

## 能不能支持全文检索？

能。SQLite 原生支持 FTS5 全文索引。中文需要分词：

- **按字切分**（最简单）：把所有内容当作独立字序列存，召回率高但精度一般。适合短文本。
- **预分词**：用 jieba/pkuseg 离线分词后存入 FTS5 的 `external content` 表。精度最好。
- **三字 trigram**（折中）：`CREATE VIRTUAL TABLE ... USING fts5(content, tokenize='trigram')`，SQLite 3.34+ 原生支持。

下一步如果要加进来可以告诉我，需要改 `build.py`，前端不需要大改。

## 规模建议

- **< 10 MB**：可以不开索引也能跑，但索引总归让查询更快。
- **10 MB – 1 GB**：本方案的甜蜜区。GitHub Pages 单文件上限 100 MB，超过就用 Git LFS 或者 S3/Cloudflare R2。
- **> 1 GB**：考虑 `serverMode: "chunked"` 把数据库切成多个小文件，减轻 CDN 缓存单文件的压力。参见 sql.js-httpvfs 的 `chunked` 模式文档。

## 限制

- **只读**。浏览器不能写回服务器的 sqlite 文件（那就不是静态托管了）。如果需要写，考虑 `wa-sqlite` + OPFS，数据存在用户本地。
- **WebAssembly + Web Worker**：IE、旧 Safari 不行，2020 年后的主流浏览器都 OK。
- **SharedArrayBuffer**：不是必需的，但如果启用会更快。需要 `Cross-Origin-Opener-Policy: same-origin` + `Cross-Origin-Embedder-Policy: require-corp` 两个头。GitHub Pages 目前不发这俩头，影响不大，XHR 同步版本一样能用。

## 参考

- sql.js-httpvfs 原作博客：<https://phiresky.github.io/blog/2021/hosting-sqlite-databases-on-github-pages/>
- 仓库：<https://github.com/phiresky/sql.js-httpvfs>
