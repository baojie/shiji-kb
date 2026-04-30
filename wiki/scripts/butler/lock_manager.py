#!/usr/bin/env python3
"""Butler 统一锁 API。

所有 Butler 脚本通过此模块操作锁，不直接读写 .lock 文件。

设计原则
--------
多实例（太史令/列传家/注疏者/索隐者/刊行者/…）可以**并发运行**，
只要它们操作不同的页面。冲突保护分两层：

  1. 任务层：round-level 锁确保每个轮号全局唯一分配。
  2. 页面层：assert_page_free() 确保同一页面不被两个轮次同时写入。

轮次锁生命周期
--------------
  acquire()          递增计数器，创建 round_<N>.lock（此时 pages=[]）
  set_page()         任务选定后，把 page 写入 round_<N>.lock 的 pages 列表
  assert_page_free() 写页面前调用，扫描其他活跃锁，发现同页冲突则报错
  assert_owner()     记账前调用，确认本轮锁仍有效（未超时）
  release()          记账完成，删除 round_<N>.lock

计数器互斥锁（round_counter.lock）
-----------------------------------
仅在 acquire() 内部递增计数器的极短时间内持有，外部不可见。

Python API
----------
    from lock_manager import LockManager, LockError
    lm = LockManager()

    round_num = lm.acquire(instance="注疏者")          # 并发安全
    lm.set_page(round_num, "韩信")                     # 任务选定后记录目标页
    lm.assert_page_free("韩信", my_round=round_num)    # 写前检查
    lm.assert_owner(round_num)                          # 记账前检查
    lm.release(round_num)

    lm.check_duplicate(instance="注疏者")              # 启动时：检测同名实例
    lm.list_active()                                    # 所有活跃锁
    lm.cleanup_stale()                                  # 清理超时锁

CLI
---
    python3 lock_manager.py acquire --instance 注疏者 [--page 韩信]
    python3 lock_manager.py set-page --round N --page 韩信
    python3 lock_manager.py release  --round N
    python3 lock_manager.py check    --round N          exit 0=有效
    python3 lock_manager.py check-page --page 韩信 --round N   exit 0=无冲突
    python3 lock_manager.py check-dup  --instance 注疏者       exit 0=无重复
    python3 lock_manager.py status                      JSON 列表
    python3 lock_manager.py cleanup                     清理超时锁
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import time
from pathlib import Path

# ── 路径常量 ────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[3]
LOGS_DIR   = _REPO_ROOT / "wiki/logs/butler"
STALE_SECONDS = 600   # 超过 10 分钟的轮次锁视为超时


class LockError(RuntimeError):
    """锁检查失败时抛出。"""


# ── LockManager ─────────────────────────────────────────────────────────────
class LockManager:
    """Butler 统一锁管理器。多实例并发安全。"""

    def __init__(self, logs_dir: Path = LOGS_DIR) -> None:
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    # ── 内部：计数器锁（极短暂，仅递增期间）────────────────────────────────
    def _acquire_counter_lock(self, max_wait: float = 10.0, retry_ms: float = 0.05) -> None:
        lock = self.logs_dir / "round_counter.lock"
        deadline = time.monotonic() + max_wait
        while True:
            try:
                fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return
            except FileExistsError:
                if time.monotonic() > deadline:
                    lock.unlink(missing_ok=True)
                time.sleep(retry_ms)

    def _release_counter_lock(self) -> None:
        (self.logs_dir / "round_counter.lock").unlink(missing_ok=True)

    def _lock_path(self, round_num: int) -> Path:
        return self.logs_dir / f"round_{round_num}.lock"

    def _read_lock(self, p: Path) -> dict | None:
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    # ── 公开 API ─────────────────────────────────────────────────────────────

    def acquire(self, instance: str = "", page: str | None = None) -> int:
        """递增计数器，创建轮次锁，返回轮号。

        多实例可并发调用，不互相阻塞。
        可选 page 参数：若任务在 acquire 前已知，可直接记录；否则用 set_page() 补填。
        """
        self.cleanup_stale()

        self._acquire_counter_lock()
        try:
            counter = self.logs_dir / "round_counter.txt"
            raw  = counter.read_text(encoding="utf-8").strip() if counter.exists() else ""
            last = raw.splitlines()[-1] if raw else ""
            val  = int(last) + 1 if last.isdigit() else 1

            lock_data: dict = {
                "round":    val,
                "instance": instance or f"inst{os.getpid()}",
                "pid":      os.getpid(),
                "ts":       datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "pages":    [page] if page else [],
            }
            self._lock_path(val).write_text(
                json.dumps(lock_data, ensure_ascii=False), encoding="utf-8"
            )

            tmp = counter.with_suffix(".tmp")
            tmp.write_text(str(val) + "\n", encoding="utf-8")
            os.replace(tmp, counter)
        finally:
            self._release_counter_lock()

        return val

    def set_page(self, round_num: int, page: str) -> None:
        """声明本轮要写的页面（追加到 pages 列表，可多次调用）。

        必须在 assert_page_free() 和 Write/Edit 之前调用。
        """
        p = self._lock_path(round_num)
        if not p.exists():
            raise LockError(f"round_{round_num}.lock 不存在，无法 set_page")
        data = self._read_lock(p) or {}
        pages: list = data.get("pages") or []
        if page not in pages:
            pages.append(page)
        data["pages"] = pages
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def assert_page_free(self, page: str, my_round: int) -> None:
        """断言目标页面未被其他活跃轮次占用。

        在写页面（add_page/edit_page）之前调用。
        若发现另一轮次已声明同一页面，抛出 LockError。
        """
        for info in self.list_active():
            if info.get("round") == my_round:
                continue
            other_pages: list = info.get("pages") or (
                [info["page"]] if info.get("page") else []
            )
            if page in other_pages:
                raise LockError(
                    f"页面冲突：'{page}' 已被 R{info['round']}（实例 "
                    f"{info.get('instance','?')}）占用，当前轮次 R{my_round} 不可写入。"
                )

    def assert_owner(self, round_num: int) -> None:
        """断言本轮锁存在且未超时。

        在 record_action 等写操作前调用。
        """
        p = self._lock_path(round_num)
        if not p.exists():
            raise LockError(
                f"round_{round_num}.lock 不存在——未通过 claim_round.py 领取锁，禁止写入。"
            )
        try:
            age = time.time() - p.stat().st_mtime
        except FileNotFoundError:
            raise LockError(f"round_{round_num}.lock 在检查中消失（并发问题？）")
        if age > STALE_SECONDS:
            p.unlink(missing_ok=True)
            raise LockError(
                f"round_{round_num}.lock 已超时（{age:.0f}s），锁已清理，拒绝写入。"
            )

    def check_duplicate(self, instance: str) -> list[dict]:
        """返回与 instance 同名的其他活跃锁列表。

        空列表 = 无重复，可以启动。
        非空  = 已有同名实例在运行，应停止。
        """
        return [
            info for info in self.list_active()
            if info.get("instance") == instance
        ]

    def release(self, round_num: int) -> None:
        """释放轮次锁（幂等）。"""
        p = self._lock_path(round_num)
        if p.exists():
            p.unlink()
        else:
            print(
                f"[lock_manager] warn: round_{round_num}.lock 不存在（已释放？）",
                file=sys.stderr,
            )

    def list_active(self) -> list[dict]:
        """返回所有未超时的轮次锁信息列表。"""
        active = []
        now = time.time()
        for p in sorted(self.logs_dir.glob("round_*.lock")):
            try:
                if now - p.stat().st_mtime < STALE_SECONDS:
                    info = self._read_lock(p) or {"file": p.name}
                    active.append(info)
            except FileNotFoundError:
                pass
        return active

    def cleanup_stale(self) -> list[int]:
        """删除超时锁，返回已清理的轮号。"""
        cleaned, now = [], time.time()
        for p in sorted(self.logs_dir.glob("round_*.lock")):
            try:
                if now - p.stat().st_mtime >= STALE_SECONDS:
                    p.unlink(missing_ok=True)
                    try:
                        cleaned.append(int(p.stem.split("_")[1]))
                    except (IndexError, ValueError):
                        pass
            except FileNotFoundError:
                pass
        return cleaned


# ── CLI ─────────────────────────────────────────────────────────────────────
def _cli() -> int:
    ap = argparse.ArgumentParser(description="Butler 统一锁管理 CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("acquire", help="领取轮次锁（允许并发）")
    p.add_argument("--instance", default="")
    p.add_argument("--page", default=None, help="目标页面（可选，稍后用 set-page 补填）")

    p = sub.add_parser("set-page", help="把目标页面写入已有轮次锁")
    p.add_argument("--round", type=int, required=True, dest="round_num")
    p.add_argument("--page", required=True)

    p = sub.add_parser("release", help="释放轮次锁")
    p.add_argument("--round", type=int, required=True, dest="round_num")

    p = sub.add_parser("check", help="验证轮次锁有效性（exit 0=有效）")
    p.add_argument("--round", type=int, required=True, dest="round_num")

    p = sub.add_parser("check-page", help="检查页面是否被其他轮次占用（exit 0=空闲）")
    p.add_argument("--page", required=True)
    p.add_argument("--round", type=int, required=True, dest="round_num")

    p = sub.add_parser("check-dup", help="检查同名实例是否已在运行（exit 0=无重复）")
    p.add_argument("--instance", required=True)

    sub.add_parser("status", help="列出所有活跃轮次锁（JSON）")
    sub.add_parser("cleanup", help="清理超时锁")

    args = ap.parse_args()
    lm   = LockManager()

    if args.cmd == "acquire":
        val = lm.acquire(instance=args.instance, page=args.page)
        print(val)
        return 0

    elif args.cmd == "set-page":
        try:
            lm.set_page(args.round_num, args.page)
            print(f"[set-page] round_{args.round_num} → page={args.page!r}")
            return 0
        except LockError as e:
            print(f"[error] {e}", file=sys.stderr)
            return 1

    elif args.cmd == "release":
        lm.release(args.round_num)
        print(f"[released] round_{args.round_num}.lock")
        return 0

    elif args.cmd == "check":
        try:
            lm.assert_owner(args.round_num)
            print(f"[valid] round_{args.round_num}.lock")
            return 0
        except LockError as e:
            print(f"[invalid] {e}", file=sys.stderr)
            return 1

    elif args.cmd == "check-page":
        try:
            lm.assert_page_free(args.page, my_round=args.round_num)
            print(f"[free] '{args.page}' 无冲突")
            return 0
        except LockError as e:
            print(f"[conflict] {e}", file=sys.stderr)
            return 1

    elif args.cmd == "check-dup":
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

    elif args.cmd == "status":
        print(json.dumps(lm.list_active(), ensure_ascii=False, indent=2))
        return 0

    elif args.cmd == "cleanup":
        cleaned = lm.cleanup_stale()
        print(f"[cleanup] 已清理: {cleaned}" if cleaned else "[cleanup] 无超时锁")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(_cli())
