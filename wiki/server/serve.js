#!/usr/bin/env node
/* 史记 Wiki 本地静态服务器 (无外部依赖, 仅用 Node 内置 http/fs)。
 *
 * 用法:
 *   node wiki/server/serve.js [root] [port]
 *   node wiki/server/serve.js wiki/public         # 默认端口 8000
 *   node wiki/server/serve.js wiki/public 9000    # 指定端口
 *
 * 常规启动走 wiki/wiki.sh, 无需直接调用本脚本。
 *
 * 特性:
 *   - 自动处理 /  → index.html
 *   - 合理 MIME (含 .md, .ttl, .svg)
 *   - 防止路径穿越
 *   - dev 禁缓存 (Cache-Control: no-store)
 *   - 端口被占用时自动往后加 1, 最多试 10 次
 */

'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const apiRouter = require('./api/index.js');

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.js':   'application/javascript; charset=utf-8',
  '.mjs':  'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.md':   'text/markdown; charset=utf-8',
  '.txt':  'text/plain; charset=utf-8',
  '.svg':  'image/svg+xml',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif':  'image/gif',
  '.ico':  'image/x-icon',
  '.woff': 'font/woff',
  '.woff2':'font/woff2',
  '.ttl':  'text/turtle; charset=utf-8',
  '.yaml': 'application/yaml; charset=utf-8',
  '.yml':  'application/yaml; charset=utf-8',
};

function resolveArgs() {
  const args = process.argv.slice(2);
  let root = process.cwd();
  let port = 8000;
  for (const a of args) {
    if (/^\d+$/.test(a)) {
      port = parseInt(a, 10);
    } else {
      root = path.resolve(a);
    }
  }
  return { root, port };
}

function makeHandler(root) {
  return (req, res) => {
    // /api/* 前置分派: 走 API 路由, 不落静态文件系统
    if (req.url.startsWith('/api/') || req.url === '/api') {
      console.log(`  ${req.method} ${req.url} → api`);
      return apiRouter.dispatch(req, res);
    }

    let urlPath;
    try {
      urlPath = decodeURIComponent(req.url.split('?')[0]);
    } catch {
      res.writeHead(400); res.end('Bad URL'); return;
    }
    if (urlPath === '/') urlPath = '/index.html';

    // 正规化 + 防穿越
    const filePath = path.normalize(path.join(root, urlPath));
    if (!filePath.startsWith(root)) {
      res.writeHead(403); res.end('Forbidden'); return;
    }

    fs.stat(filePath, (err, stat) => {
      if (err) {
        res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end(`404 Not Found: ${urlPath}`);
        console.log(`  ${req.method} ${urlPath} → 404`);
        return;
      }
      let final = filePath;
      if (stat.isDirectory()) {
        final = path.join(filePath, 'index.html');
      }
      const ext = path.extname(final).toLowerCase();
      const type = MIME[ext] || 'application/octet-stream';
      res.writeHead(200, {
        'Content-Type': type,
        'Cache-Control': 'no-store',
        'Access-Control-Allow-Origin': '*',
      });
      fs.createReadStream(final)
        .on('error', () => { res.end(); })
        .pipe(res);
      console.log(`  ${req.method} ${urlPath} → 200 ${type.split(';')[0]}`);
    });
  };
}

function tryListen(handler, port, attempt = 0) {
  if (attempt >= 10) {
    console.error('无可用端口 (尝试了 10 个)。');
    process.exit(1);
  }
  const server = http.createServer(handler);
  server.once('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      console.log(`端口 ${port} 占用, 试 ${port + 1}`);
      tryListen(handler, port + 1, attempt + 1);
    } else {
      console.error('监听失败:', err.message);
      process.exit(1);
    }
  });
  server.listen(port, '127.0.0.1', () => {
    const { address, port: actualPort } = server.address();
    console.log(`史记 Wiki · http://${address}:${actualPort}/`);
    console.log('  Ctrl+C 停止\n');
  });
}

function main() {
  const { root, port } = resolveArgs();
  if (!fs.existsSync(root)) {
    console.error(`根目录不存在: ${root}`); process.exit(1);
  }
  if (!fs.statSync(root).isDirectory()) {
    console.error(`不是目录: ${root}`); process.exit(1);
  }
  console.log(`根目录: ${root}`);
  tryListen(makeHandler(root), port);
}

main();
