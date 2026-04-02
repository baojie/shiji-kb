#!/usr/bin/env python3
"""
分析 Claude Code 对话记录中的 token 使用情况

详细文档：skills/SKILL_10g_项目成本与时间统计.md
快速入门：scripts/TOKEN_TRACKER_QUICKSTART.md
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def load_config():
    """加载配置文件"""
    # 尝试从项目根目录加载配置
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / ".claude_cost_config.json"

    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        print(f"   请复制 .claude_cost_config.example.json 为 .claude_cost_config.json")
        print(f"   并根据你的实际路径修改 claude_project_paths")
        sys.exit(1)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        sys.exit(1)


# 加载配置
CONFIG = load_config()

# Claude 对话记录目录（从配置文件读取）
CLAUDE_DIRS = [
    Path.home() / ".claude" / "projects" / path
    for path in CONFIG.get('claude_project_paths', [])
]

def analyze_token_usage():
    """分析所有对话文件的 token 使用情况"""

    total_input_tokens = 0
    total_output_tokens = 0
    total_cache_creation_tokens = 0
    total_cache_read_tokens = 0
    conversation_count = 0
    message_count = 0

    # 按日期统计
    daily_stats = defaultdict(lambda: {
        'input': 0,
        'output': 0,
        'cache_creation': 0,
        'cache_read': 0,
        'conversations': 0,
        'messages': 0
    })

    # 按模型统计
    model_stats = defaultdict(lambda: {
        'input': 0,
        'output': 0,
        'cache_creation': 0,
        'cache_read': 0,
        'count': 0
    })

    # 收集所有目录的 jsonl 文件
    jsonl_files = []
    for claude_dir in CLAUDE_DIRS:
        if claude_dir.exists():
            files = list(claude_dir.glob("*.jsonl"))
            jsonl_files.extend(files)
            print(f"📁 {claude_dir.name}: {len(files)} 个对话文件")

    if not jsonl_files:
        print("❌ 没有找到任何对话文件")
        return

    print(f"\n📊 总计找到 {len(jsonl_files)} 个对话文件\n")

    for jsonl_file in jsonl_files:
        conversation_count += 1
        conversation_messages = 0

        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        message_count += 1
                        conversation_messages += 1

                        # 获取时间戳
                        timestamp = data.get('timestamp')
                        if timestamp:
                            # 转换为日期
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            date_str = dt.strftime('%Y-%m-%d')
                        else:
                            # 使用文件修改时间
                            mtime = jsonl_file.stat().st_mtime
                            date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

                        # 统计 token - 处理嵌套的 message 结构
                        message_data = data.get('message', {})
                        usage = message_data.get('usage', {})

                        input_tokens = usage.get('input_tokens', 0)
                        output_tokens = usage.get('output_tokens', 0)
                        cache_creation_tokens = usage.get('cache_creation_input_tokens', 0)
                        cache_read_tokens = usage.get('cache_read_input_tokens', 0)

                        total_input_tokens += input_tokens
                        total_output_tokens += output_tokens
                        total_cache_creation_tokens += cache_creation_tokens
                        total_cache_read_tokens += cache_read_tokens

                        # 按日期统计
                        daily_stats[date_str]['input'] += input_tokens
                        daily_stats[date_str]['output'] += output_tokens
                        daily_stats[date_str]['cache_creation'] += cache_creation_tokens
                        daily_stats[date_str]['cache_read'] += cache_read_tokens
                        if input_tokens > 0 or output_tokens > 0:
                            daily_stats[date_str]['messages'] += 1

                        # 按模型统计
                        model = message_data.get('model', 'unknown')
                        if input_tokens > 0 or output_tokens > 0:
                            model_stats[model]['input'] += input_tokens
                            model_stats[model]['output'] += output_tokens
                            model_stats[model]['cache_creation'] += cache_creation_tokens
                            model_stats[model]['cache_read'] += cache_read_tokens
                            model_stats[model]['count'] += 1

                    except json.JSONDecodeError as e:
                        pass  # 跳过无法解析的行

        except Exception as e:
            print(f"⚠️  读取文件出错 {jsonl_file.name}: {e}")
            continue

        # 记录每个对话的对话数
        if conversation_messages > 0:
            # 使用文件修改时间作为日期
            mtime = jsonl_file.stat().st_mtime
            date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
            daily_stats[date_str]['conversations'] += 1

    # 打印总体统计
    print("=" * 80)
    print("📊 总体统计")
    print("=" * 80)
    print(f"对话数量: {conversation_count:,}")
    print(f"消息数量: {message_count:,}")
    print(f"\n💰 Token 使用情况:")
    print(f"  输入 tokens:           {total_input_tokens:>15,}")
    print(f"  输出 tokens:           {total_output_tokens:>15,}")
    print(f"  缓存创建 tokens:       {total_cache_creation_tokens:>15,}")
    print(f"  缓存读取 tokens:       {total_cache_read_tokens:>15,}")
    print(f"  " + "-" * 40)
    print(f"  总计 (不含缓存读取):   {total_input_tokens + total_output_tokens + total_cache_creation_tokens:>15,}")
    print(f"  总计 (含缓存读取):     {total_input_tokens + total_output_tokens + total_cache_creation_tokens + total_cache_read_tokens:>15,}")

    print(f"\n⚠️  统计范围说明:")
    print(f"  本统计仅包含当前机器上的对话记录 (~/.claude/projects/)")
    print(f"  如果在其他机器上也工作过，需要在每台机器上分别统计")
    print(f"  实际项目总成本 = 所有机器的成本之和")

    # 估算成本（Claude Sonnet 价格）
    # Sonnet 4.5: Input: $3/MTok, Output: $15/MTok, Cache Write: $3.75/MTok, Cache Read: $0.3/MTok
    input_cost = total_input_tokens * 3 / 1_000_000
    output_cost = total_output_tokens * 15 / 1_000_000
    cache_write_cost = total_cache_creation_tokens * 3.75 / 1_000_000
    cache_read_cost = total_cache_read_tokens * 0.3 / 1_000_000
    total_cost = input_cost + output_cost + cache_write_cost + cache_read_cost

    print(f"\n💵 估算成本 (Claude Sonnet 4.5 价格):")
    print(f"  输入成本:              ${input_cost:>14.2f}  (@ $3/MTok)")
    print(f"  输出成本:              ${output_cost:>14.2f}  (@ $15/MTok)")
    print(f"  缓存写入成本:          ${cache_write_cost:>14.2f}  (@ $3.75/MTok)")
    print(f"  缓存读取成本:          ${cache_read_cost:>14.2f}  (@ $0.30/MTok)")
    print(f"  " + "-" * 50)
    print(f"  总成本:                ${total_cost:>14.2f}")

    # 计算缓存节省
    without_cache_cost = (total_input_tokens + total_cache_creation_tokens) * 3 / 1_000_000 + output_cost
    cache_savings = without_cache_cost - total_cost
    cache_savings_percent = (cache_savings / without_cache_cost * 100) if without_cache_cost > 0 else 0

    print(f"\n💡 缓存效益:")
    print(f"  无缓存成本:            ${without_cache_cost:>14.2f}")
    print(f"  节省成本:              ${cache_savings:>14.2f}  ({cache_savings_percent:.1f}%)")

    # 打印按模型统计
    print("\n" + "=" * 80)
    print("🤖 按模型统计")
    print("=" * 80)
    for model, stats in sorted(model_stats.items(), key=lambda x: x[1]['input'] + x[1]['output'], reverse=True):
        model_total = stats['input'] + stats['output'] + stats['cache_creation']
        print(f"\n模型: {model}")
        print(f"  消息数:     {stats['count']:>10,}")
        print(f"  输入:       {stats['input']:>10,} tokens")
        print(f"  输出:       {stats['output']:>10,} tokens")
        print(f"  缓存创建:   {stats['cache_creation']:>10,} tokens")
        print(f"  缓存读取:   {stats['cache_read']:>10,} tokens")
        print(f"  总计:       {model_total:>10,} tokens")

    # 打印按日期统计（最近30天）
    print("\n" + "=" * 80)
    print("📅 按日期统计（最近记录）")
    print("=" * 80)
    print(f"{'日期':<12} {'对话数':>6} {'消息数':>6} {'输入':>12} {'输出':>12} {'缓存创建':>12} {'缓存读取':>12} {'总计':>12}")
    print("-" * 100)

    for date_str in sorted(daily_stats.keys(), reverse=True)[:30]:
        stats = daily_stats[date_str]
        daily_total = stats['input'] + stats['output'] + stats['cache_creation']
        print(f"{date_str:<12} {stats['conversations']:>6} {stats['messages']:>6} "
              f"{stats['input']:>12,} {stats['output']:>12,} "
              f"{stats['cache_creation']:>12,} {stats['cache_read']:>12,} "
              f"{daily_total:>12,}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_token_usage()
