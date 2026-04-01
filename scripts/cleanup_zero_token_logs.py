#!/usr/bin/env python3
"""
清理 Token 为 0 的日志文件

使用场景：
- 定期清理测试产生的空日志文件
- 保留真实有 Token 消耗的日志

用法：
    python scripts/cleanup_zero_token_logs.py              # 预览要删除的文件
    python scripts/cleanup_zero_token_logs.py --execute    # 实际删除
    python scripts/cleanup_zero_token_logs.py --keep-days 30  # 只清理 30 天前的文件
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta


def parse_args():
    parser = argparse.ArgumentParser(description='清理 Token 为 0 的日志文件')
    parser.add_argument('--execute', action='store_true',
                       help='实际删除文件（默认只预览）')
    parser.add_argument('--keep-days', type=int, default=None,
                       help='保留最近 N 天的文件（即使 Token 为 0）')
    parser.add_argument('--log-dir', default='logs/cost_reports/session_logs',
                       help='日志目录路径')
    return parser.parse_args()


def should_delete(log_file: Path, keep_days: int = None) -> tuple[bool, str]:
    """
    判断是否应该删除文件

    返回：(是否删除, 原因说明)
    """
    try:
        # 读取 JSON 文件
        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查 Token 是否为 0
        messages = data.get('stats', {}).get('messages', 0)
        total_cost = data.get('stats', {}).get('cost', {}).get('total', 0)

        if messages == 0 and total_cost == 0:
            # Token 为 0，检查文件时间
            if keep_days is not None:
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                cutoff_date = datetime.now() - timedelta(days=keep_days)

                if file_mtime > cutoff_date:
                    return False, f"Token=0 但在保留期内（{keep_days}天）"

            return True, "Token=0 且超出保留期"

        return False, f"有 Token 使用（{messages} 消息，${total_cost:.4f}）"

    except Exception as e:
        return False, f"读取失败: {e}"


def main():
    args = parse_args()

    # 查找所有日志文件
    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print(f"❌ 日志目录不存在: {log_dir}")
        return

    log_files = sorted(log_dir.glob("token_usage_*.json"))

    if not log_files:
        print(f"📭 没有找到日志文件: {log_dir}")
        return

    print(f"📂 扫描目录: {log_dir}")
    print(f"📋 找到 {len(log_files)} 个日志文件\n")

    if args.keep_days:
        print(f"⏰ 保留最近 {args.keep_days} 天的文件\n")

    # 分析文件
    to_delete = []
    to_keep = []

    for log_file in log_files:
        should_del, reason = should_delete(log_file, args.keep_days)

        if should_del:
            to_delete.append((log_file, reason))
        else:
            to_keep.append((log_file, reason))

    # 显示结果
    print("=" * 70)
    print(f"📊 分析结果")
    print("=" * 70)
    print(f"保留: {len(to_keep)} 个")
    print(f"删除: {len(to_delete)} 个")
    print()

    if to_delete:
        print("🗑️  将要删除的文件：")
        print("-" * 70)
        for i, (file, reason) in enumerate(to_delete, 1):
            file_time = datetime.fromtimestamp(file.stat().st_mtime)
            print(f"{i:3d}. {file.name}")
            print(f"      时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      原因: {reason}")

        print()
        total_size = sum(f.stat().st_size for f, _ in to_delete)
        print(f"💾 释放空间: {total_size:,} 字节 ({total_size/1024:.2f} KB)")

    if to_keep:
        print()
        print("✅ 将要保留的文件：")
        print("-" * 70)
        for i, (file, reason) in enumerate(to_keep, 1):
            file_time = datetime.fromtimestamp(file.stat().st_mtime)
            print(f"{i:3d}. {file.name}")
            print(f"      时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      原因: {reason}")

    # 执行删除
    if to_delete:
        print()
        print("=" * 70)

        if args.execute:
            print("⚠️  正在删除文件...")
            deleted_count = 0

            for file, _ in to_delete:
                try:
                    file.unlink()
                    deleted_count += 1
                    print(f"✓ 已删除: {file.name}")
                except Exception as e:
                    print(f"✗ 删除失败: {file.name} - {e}")

            print()
            print(f"✅ 成功删除 {deleted_count}/{len(to_delete)} 个文件")

        else:
            print("💡 预览模式（未实际删除）")
            print()
            print("要实际删除这些文件，请运行：")
            cmd = f"python {Path(__file__).name} --execute"
            if args.keep_days:
                cmd += f" --keep-days {args.keep_days}"
            print(f"    {cmd}")

    else:
        print()
        print("✨ 没有需要删除的文件")


if __name__ == "__main__":
    main()
