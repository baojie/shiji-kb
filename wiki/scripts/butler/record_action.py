#!/usr/bin/env python3
"""
追加一条 action 记录到 wiki/logs/butler/actions.jsonl。

用法:
    python3 wiki/scripts/butler/record_action.py \
        --round 10813 \
        --action enrich-biography \
        --page 韩信 \
        --status accept \
        --instance 注疏者 \
        --note "补全战役年表与陈仓/垓下引文，散文2节" \
        --reflect "淮阴侯列传篇幅长，引文命中率极高"

--instance  命名实例（太史令/列传家/注疏者/索隐者/刊行者），可选
--reflect   每轮一句话观察，可选；W5 反思时扫此字段找规律
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lock_manager import LockManager, LockError

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOG = _REPO_ROOT / "wiki/logs/butler/actions.jsonl"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--action", required=True, dest="action_type",
                    choices=[
                        "create-page", "enrich-biography", "enrich-quality",
                        "premium-upgrade", "add-quote", "add-pn-citations",
                        "fix-links", "fix-alias", "delete-page",
                        "discover", "publish", "housekeeping", "reflect-w5",
                    ])
    ap.add_argument("--page", default="")
    ap.add_argument("--status", required=True, choices=["accept", "fail", "skip"])
    ap.add_argument("--instance", default="", help="命名实例（太史令/列传家/注疏者等）")
    ap.add_argument("--note", default="", help="动作描述")
    ap.add_argument("--reflect", default="", help="一句话观察（可选），供 W5 扫描找规律")
    ap.add_argument("--log", default=str(DEFAULT_LOG))
    ap.add_argument("--skip-lock-check", action="store_true",
                    help="跳过锁检查（仅限 W5/publish 等使用 increment_round 的轮次）")
    args = ap.parse_args()

    # ── 锁检查：确认本轮持有有效轮次锁 ──────────────────────────────────────
    if not args.skip_lock_check:
        try:
            LockManager().assert_owner(args.round)
        except LockError as e:
            print(f"[record_action] 锁检查失败，拒绝写入 actions.jsonl：{e}", file=sys.stderr)
            sys.exit(1)

    record: dict = {
        "round":  args.round,
        "ts":     datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "action": args.action_type,
        "page":   args.page,
        "status": args.status,
        "note":   args.note,
    }
    if args.instance:
        record["instance"] = args.instance
    if args.reflect:
        record["reflect"] = args.reflect

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    inst_tag = f" [{args.instance}]" if args.instance else ""
    print(f"[logged] R{args.round}{inst_tag} {args.action_type} | {args.page} | {args.status}")


if __name__ == "__main__":
    main()
