#!/usr/bin/env python3
"""领取轮次：原子递增计数器并创建轮次锁 round_<N>.lock。

多实例（太史令/列传家/注疏者/索隐者/刊行者/…）可并发调用，互不阻塞。
页面级冲突由 lock_manager set-page + check-page 在执行前检测。

用法：
    ROUND=$(python3 wiki/scripts/butler/claim_round.py --instance 注疏者)

启动时检查同名实例是否已在运行：
    python3 wiki/scripts/butler/claim_round.py --check-only --instance 注疏者
    → exit 0 = 无重复实例，可启动
    → exit 1 = 已有同名实例在运行，应停止
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lock_manager import LockManager, LockError


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--instance", default="", help="实例标识符")
    ap.add_argument("--page", default=None, help="目标页面（可选）")
    ap.add_argument("--check-only", action="store_true",
                    help="仅检测是否有同名实例在运行，不领取轮次")
    args = ap.parse_args()

    lm = LockManager()

    if args.check_only:
        if not args.instance:
            print("--check-only 需要 --instance 参数", file=sys.stderr)
            return 1
        dups = lm.check_duplicate(args.instance)
        if dups:
            print(
                json.dumps({"duplicate": True, "conflicts": dups}, ensure_ascii=False),
                file=sys.stderr,
            )
            print("DUPLICATE")
            return 1
        print(json.dumps({"duplicate": False}), file=sys.stderr)
        return 0

    val = lm.acquire(instance=args.instance, page=args.page)
    print(val)
    return 0


if __name__ == "__main__":
    sys.exit(main())
