#!/usr/bin/env python3
"""释放轮次锁：删除 round_<N>.lock，表示本轮已完成。

无论本轮 accept/fail/skip，每轮末尾必须调用此脚本。
不调用会留下孤儿锁，阻塞其他实例的页面检测。

用法：
    python3 wiki/scripts/butler/release_round.py <round_number>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lock_manager import LockManager


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: release_round.py <round_number>", file=sys.stderr)
        return 1
    try:
        round_num = int(sys.argv[1])
    except ValueError:
        print(f"Error: round_number must be integer, got {sys.argv[1]!r}", file=sys.stderr)
        return 1

    LockManager().release(round_num)
    print(f"[released] round_{round_num}.lock")
    return 0


if __name__ == "__main__":
    sys.exit(main())
