#!/usr/bin/env python3
"""
史记 Wiki Python 服务器 — 静态文件 + /api/want 接口

用法：
    python3 wiki/server/serve.py [root] [port]
    python3 wiki/server/serve.py wiki/public 8000   # 默认
    python3 wiki/server/serve.py . 8000             # 从仓库根服务

/api/want?page=<page_id>  把页面加入 wiki/logs/butler/queue.md 首位 (P0)
"""

import http.server
import json
import os
import sys
import urllib.parse
from datetime import date
from pathlib import Path

# ── 路径解析 ──────────────────────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent          # wiki/server/
REPO = HERE.parent.parent                       # 仓库根
QUEUE_PATH = REPO / 'wiki' / 'logs' / 'butler' / 'queue.md'
SECTION_HEADER = '## ⭐ 用户想要 (P0)'


# ── 队列操作 ──────────────────────────────────────────────────────────────────

def build_entry(page: str) -> str:
    return f"- [ ] **[想要]** {page}: `create-stub` [P0] [{date.today()}] [用户请求]\n"


def insert_into_queue(page: str) -> dict:
    if not QUEUE_PATH.exists():
        return {'ok': False, 'error': f'queue.md 不存在: {QUEUE_PATH}'}

    raw = QUEUE_PATH.read_text(encoding='utf-8')

    if f'**[想要]** {page}:' in raw:
        return {'ok': True, 'page': page, 'added': False, 'message': f'"{page}" 已在队列中'}

    entry = build_entry(page)
    idx = raw.find(SECTION_HEADER)
    if idx != -1:
        after_header = raw.index('\n', idx) + 1
        updated = raw[:after_header] + entry + raw[after_header:]
    else:
        first_section = raw.find('\n## ')
        insert_at = len(raw) if first_section == -1 else first_section + 1
        block = SECTION_HEADER + '\n' + entry + '\n'
        updated = raw[:insert_at] + block + raw[insert_at:]

    QUEUE_PATH.write_text(updated, encoding='utf-8')
    return {'ok': True, 'page': page, 'added': True, 'message': f'"{page}" 已加入队列首位'}


# ── HTTP 处理器 ───────────────────────────────────────────────────────────────

class WikiHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/want':
            params = dict(urllib.parse.parse_qsl(parsed.query))
            self._handle_want(params)
        else:
            super().do_GET()

    def _handle_want(self, params: dict):
        page = params.get('page', '').strip()
        if not page:
            self._send_json(400, {'ok': False, 'error': 'missing page'})
            return
        result = insert_into_queue(page)
        self._send_json(200, result)

    def _send_json(self, code: int, body: dict):
        data = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        # 过滤 /api/want 以外的高频静态请求，保持日志整洁
        if '/api/want' in (args[0] if args else ''):
            super().log_message(fmt, *args)
        elif not any(ext in str(args) for ext in ('.json', '.md', '.js', '.css')):
            super().log_message(fmt, *args)


# ── 入口 ──────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    root = None
    port = 8000

    for a in args:
        if a.isdigit():
            port = int(a)
        else:
            root = Path(a).resolve()

    if root is None:
        # 默认：serve.py 在 wiki/server/，上两级是仓库根，再进 wiki/public
        default = HERE.parent / 'public'
        root = default if default.is_dir() else Path.cwd()

    if not root.is_dir():
        print(f'✗ 目录不存在: {root}', file=sys.stderr)
        sys.exit(1)

    os.chdir(root)
    print(f'[wiki-py] 服务根目录 : {root}')
    print(f'[wiki-py] 队列文件   : {QUEUE_PATH}')
    print(f'[wiki-py] 监听地址   : http://localhost:{port}')
    print(f'[wiki-py] 按 Ctrl+C 停止')

    handler = WikiHandler
    with http.server.HTTPServer(('', port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n[wiki-py] 已停止')


if __name__ == '__main__':
    main()
