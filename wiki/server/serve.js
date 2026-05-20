#!/usr/bin/env node
/* 史记 Wiki 本地静态服务器 (无外部依赖, 仅用 Node 内置 http/fs)。
 *
 * 用法:
 *   node wiki/server/serve.js [root] [port]
 *   node wiki/server/serve.js wiki/public         # 默认端口 8000
 *   node wiki/server/serve.js wiki/public 9001    # 指定端口
 *
 * 常规启动走 wiki/wiki.sh, 无需直接调用本脚本。
 * 
 */

import http from 'node:http';
import fs   from 'node:fs';
import path from 'node:path';
import os   from 'node:os';

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
};

function resolveArgs() {
  const args = process.argv.slice(2);
  let root = process.cwd();
  let port = 8000;
  let fallback = null;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--fallback' && args[i + 1]) {
      fallback = path.resolve(args[++i]);
    } else if (/^\d+$/.test(args[i])) {
      port = parseInt(args[i], 10);
    } else {
      root = path.resolve(args[i]);
    }
  }
  return { root, port, fallback };
}

// 对"可选资源"路径返回空内容，避免浏览器控制台产生红色 404
const OPTIONAL_CONFIG_RE = /^\/local\/config\/[^/]+\.config\.js$/;
const OPTIONAL_DATA_RE   = /^(\/data\/[^/]+\.json|\/kb\.json)$/;
const EMPTY_MODULE = 'export default {};\n';
const EMPTY_JSON   = '{}\n';

function serveOptional(urlPath, res) {
  if (OPTIONAL_CONFIG_RE.test(urlPath)) {
    res.writeHead(200, { 'Content-Type': 'application/javascript; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(EMPTY_MODULE);
    return true;
  }
  if (OPTIONAL_DATA_RE.test(urlPath)) {
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(EMPTY_JSON);
    return true;
  }
  return false;
}

function serveFile(filePath, urlPath, res) {
  let final = filePath;
  const ext  = path.extname(final).toLowerCase();
  const type = MIME[ext] || 'application/octet-stream';
  res.writeHead(200, {
    'Content-Type': type,
    'Cache-Control': 'no-store',
    'Access-Control-Allow-Origin': '*',
  });
  fs.createReadStream(final).on('error', () => res.end()).pipe(res);
  console.log(`  GET ${urlPath} → 200`);
}

function makeHandler(root, fallback) {
  return (req, res) => {
    let urlPath;
    try {
      urlPath = decodeURIComponent(req.url.split('?')[0]);
    } catch {
      res.writeHead(400); res.end('Bad URL'); return;
    }
    if (urlPath === '/') urlPath = '/index.html';

    const filePath = path.normalize(path.join(root, urlPath));
    if (!filePath.startsWith(root)) {
      res.writeHead(403); res.end('Forbidden'); return;
    }

    fs.stat(filePath, (err, stat) => {
      if (!err) {
        const final = stat.isDirectory() ? path.join(filePath, 'index.html') : filePath;
        return serveFile(final, urlPath, res);
      }
      // 主目录未找到 → 尝试 fallback 目录
      if (fallback) {
        const fbPath = path.normalize(path.join(fallback, urlPath));
        if (!fbPath.startsWith(fallback)) { res.writeHead(403); res.end('Forbidden'); return; }
        fs.stat(fbPath, (err2, stat2) => {
          if (!err2) {
            const final = stat2.isDirectory() ? path.join(fbPath, 'index.html') : fbPath;
            console.log(`  GET ${urlPath} → fallback`);
            return serveFile(final, urlPath, res);
          }
          if (serveOptional(urlPath, res)) return;
          res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
          res.end(`404 Not Found: ${urlPath}`);
        });
      } else {
        if (serveOptional(urlPath, res)) return;
        res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end(`404 Not Found: ${urlPath}`);
      }
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
  server.listen(port, '0.0.0.0', () => {
    const { address, port: p } = server.address();
    const hostname = os.hostname();
    console.log(`史记 Wiki · http://${address}:${p}/  (本机)`);
    console.log(`史记 Wiki · http://${hostname}:${p}/  (局域网)`);
    console.log('  Ctrl+C 停止\n');
  });
}

function main() {
  const { root, port, fallback } = resolveArgs();
  if (!fs.existsSync(root)) {
    console.error(`根目录不存在: ${root}`); process.exit(1);
  }
  console.log(`根目录: ${root}`);
  if (fallback) console.log(`引擎回退: ${fallback}`);
  tryListen(makeHandler(root, fallback), port);
}

main();
