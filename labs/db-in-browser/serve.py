#!/usr/bin/env python3
"""
本地预览服务器，正确处理 HTTP Range 请求。

Python 标准库的 http.server 不支持 Range，直接用它会让 sql.js-httpvfs
退化成一次性下载整个数据库。这个脚本补齐 Range 支持。

生产部署不需要这个脚本 —— GitHub Pages / S3 / Cloudflare Pages / Nginx
等静态托管默认都支持 Range。
"""
import http.server
import os
import re
import socketserver
import sys

PORT = int(os.environ.get("PORT", "5247"))
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")


class RangeHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().do_GET()

        rng = self.headers.get("Range")
        size = os.path.getsize(path)
        ctype = self.guess_type(path)

        if not rng:
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(size))
            self.send_header("Accept-Ranges", "bytes")
            # 关闭缓存，避免开发时数据库更新后浏览器拿旧的
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            with open(path, "rb") as f:
                self.copyfile(f, self.wfile)
            return

        m = re.match(r"bytes=(\d+)-(\d*)", rng)
        if not m:
            self.send_error(416, "Invalid Range")
            return
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else size - 1
        if start >= size or end >= size or start > end:
            self.send_error(416, "Range Not Satisfiable")
            return

        length = end - start + 1
        self.send_response(206)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def guess_type(self, path):
        # SimpleHTTPRequestHandler 不认识 .wasm 和 .sqlite3
        if path.endswith(".wasm"):
            return "application/wasm"
        if path.endswith((".sqlite3", ".sqlite", ".db")):
            return "application/vnd.sqlite3"
        return super().guess_type(path)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    os.chdir(ROOT)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", PORT), RangeHandler) as httpd:
        print(f"Serving {ROOT} at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
