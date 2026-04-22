"""本地 CLI 编辑 wiki 页面，自动写入 revision.

流程:
  1. 取该页面最新版内容（无则空白模板）
  2. 写入临时文件, 启动 $EDITOR
  3. 用户保存退出后，比较 hash:
       - 若未变 → 提示并退出
       - 若变了 → 提示 summary, append 一条 revision, 触发 build

用法:
  python scripts/wiki_edit.py 刘邦
  python scripts/wiki_edit.py 刘邦 -m "修正生卒年"
  EDITOR=nvim python scripts/wiki_edit.py 新页面
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from wiki_revisions import (
    REPO_ROOT,
    append_revision,
    content_hash,
    latest_revision,
)

NEW_PAGE_TEMPLATE = """---
id: {page}
type: person
label: {page}
aliases: []
tags: []
---

# {page}

(在此撰写正文)
"""


def get_author() -> str:
    """优先 WIKI_AUTHOR 环境变量, 否则 git config user.name (仅作字段, 不依赖 git 历史), 兜底 unknown."""
    if env := os.environ.get("WIKI_AUTHOR"):
        return env
    try:
        r = subprocess.run(
            ["git", "config", "user.name"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except FileNotFoundError:
        pass
    return "unknown"


def open_in_editor(initial_content: str, page: str) -> str:
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "vi"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=f".{page}.md", delete=False, encoding="utf-8"
    ) as tf:
        tf.write(initial_content)
        tf_path = Path(tf.name)
    try:
        # editor 可能含参数 (eg. "code -w"), 用 shell 拆分
        cmd = f'{editor} "{tf_path}"'
        ret = subprocess.call(cmd, shell=True)
        if ret != 0:
            print(f"编辑器返回码 {ret}, 取消提交", file=sys.stderr)
            sys.exit(1)
        return tf_path.read_text(encoding="utf-8")
    finally:
        tf_path.unlink(missing_ok=True)


def prompt_summary(provided: str | None) -> str:
    if provided is not None:
        return provided.strip()
    print("\n请输入修改摘要 (一行, 直接回车放弃):")
    s = input("> ").strip()
    if not s:
        print("摘要为空, 放弃提交", file=sys.stderr)
        sys.exit(1)
    return s


def run_build() -> None:
    script = Path(__file__).parent / "build_wiki_history.py"
    subprocess.check_call([sys.executable, str(script)])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("page", help="页面名 (如 '刘邦')")
    parser.add_argument("-m", "--message", default=None, help="修改摘要")
    parser.add_argument("--author", default=None,
                        help="作者 (覆盖 $WIKI_AUTHOR / git user.name)")
    parser.add_argument("--no-build", action="store_true",
                        help="保存后不触发 build_wiki_history.py")
    args = parser.parse_args()

    page = args.page
    parent = latest_revision(page)
    initial = parent.content if parent else NEW_PAGE_TEMPLATE.format(page=page)

    new_content = open_in_editor(initial, page)

    if content_hash(new_content) == content_hash(initial):
        print("内容未改变, 不写入新修订")
        return 0

    summary = prompt_summary(args.message)
    author = args.author or get_author()

    rev = append_revision(
        page=page, content=new_content, author=author, summary=summary,
    )
    print(f"\n✓ 新修订: {rev.rev_id}  (author={rev.author})")

    if not args.no_build:
        print("\n触发 build_wiki_history.py ...")
        run_build()
    else:
        print("(--no-build 已启用, 跳过派生)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
