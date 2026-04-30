#!/usr/bin/env python3
"""原子递增 round_counter.txt，输出新轮号。

⚠️  仅用于不涉及页面写入的轮次（W5 反思、/wiki 发布等周期任务）。
    常规工作轮次请改用 claim_round.py（创建持久轮次锁）+ release_round.py（释放）。
    此类轮次调用 record_action.py 时须加 --skip-lock-check。

用法：
    ROUND=$(python3 wiki/scripts/butler/increment_round.py)
"""
import os
import sys
import time
from pathlib import Path

COUNTER  = Path(__file__).resolve().parents[3] / "wiki/logs/butler/round_counter.txt"
LOCKFILE = COUNTER.parent / "round_counter.lock"
MAX_WAIT = 10.0
RETRY_MS = 0.05


def _acquire_lock() -> None:
    deadline = time.monotonic() + MAX_WAIT
    while True:
        try:
            fd = os.open(str(LOCKFILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            if time.monotonic() > deadline:
                LOCKFILE.unlink(missing_ok=True)
            time.sleep(RETRY_MS)


def _release_lock() -> None:
    LOCKFILE.unlink(missing_ok=True)


def main() -> int:
    COUNTER.parent.mkdir(parents=True, exist_ok=True)
    _acquire_lock()
    try:
        raw = COUNTER.read_text(encoding="utf-8").strip() if COUNTER.exists() else ""
        last = raw.splitlines()[-1] if raw else ""
        val = int(last) + 1 if last.isdigit() else 1
        tmp = COUNTER.with_suffix(".tmp")
        tmp.write_text(str(val) + "\n", encoding="utf-8")
        os.replace(tmp, COUNTER)
    finally:
        _release_lock()
    print(val)
    return 0


if __name__ == "__main__":
    sys.exit(main())
