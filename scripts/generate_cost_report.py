#!/usr/bin/env python3
"""
生成 Claude Code Token 使用周报/月报

Usage:
    python scripts/generate_cost_report.py --period weekly
    python scripts/generate_cost_report.py --period monthly
    python scripts/generate_cost_report.py --start 2026-03-01 --end 2026-03-31

详细文档：skills/SKILL_10g_项目成本与时间统计.md
快速入门：scripts/TOKEN_TRACKER_QUICKSTART.md
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


def load_config():
    """加载配置文件"""
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

# 价格配置（从配置文件读取）
PRICING = CONFIG.get('pricing', {})

# 默认价格（如果模型未在配置中）
DEFAULT_PRICING = PRICING.get('claude-sonnet-4-5-20250929', {
    'input': 3.0,
    'output': 15.0,
    'cache_creation': 3.75,
    'cache_read': 0.30,
})


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='生成 Claude Code 成本报告')
    parser.add_argument('--period', choices=['weekly', 'monthly'], help='报告周期')
    parser.add_argument('--start', help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--output', default='logs/cost_reports', help='输出目录')
    parser.add_argument('--format', choices=['markdown', 'text'], default='markdown', help='输出格式')
    return parser.parse_args()


def get_date_range(period=None, start=None, end=None):
    """获取统计日期范围"""
    today = datetime.now()

    if start and end:
        start_date = datetime.strptime(start, '%Y-%m-%d')
        end_date = datetime.strptime(end, '%Y-%m-%d')
    elif period == 'weekly':
        # 上周一到上周日
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday + 7)
        start_date = last_monday
        end_date = last_monday + timedelta(days=6)
    elif period == 'monthly':
        # 上个月
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        start_date = last_day_last_month.replace(day=1)
        end_date = last_day_last_month
    else:
        # 默认最近7天
        end_date = today
        start_date = today - timedelta(days=7)

    return start_date, end_date


def analyze_conversations(start_date, end_date):
    """分析指定时间段的对话数据"""

    # 统计数据
    stats = {
        'total_conversations': 0,
        'total_messages': 0,
        'tokens': {
            'input': 0,
            'output': 0,
            'cache_creation': 0,
            'cache_read': 0,
        },
        'cost': {
            'input': 0.0,
            'output': 0.0,
            'cache_creation': 0.0,
            'cache_read': 0.0,
            'total': 0.0,
        },
        'by_model': defaultdict(lambda: {
            'messages': 0,
            'tokens': {'input': 0, 'output': 0, 'cache_creation': 0, 'cache_read': 0},
            'cost': 0.0,
        }),
        'by_date': defaultdict(lambda: {
            'conversations': 0,
            'messages': 0,
            'tokens': {'input': 0, 'output': 0, 'cache_creation': 0, 'cache_read': 0},
            'cost': 0.0,
        }),
    }

    # 收集所有目录的 jsonl 文件
    jsonl_files = []
    for claude_dir in CLAUDE_DIRS:
        if claude_dir.exists():
            files = list(claude_dir.glob("*.jsonl"))
            jsonl_files.extend(files)

    if not jsonl_files:
        print("❌ 没有找到任何对话文件")
        return stats

    for jsonl_file in jsonl_files:
        conversation_in_range = False
        conversation_messages = 0

        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # 获取时间戳
                        timestamp = data.get('timestamp')
                        if timestamp:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        else:
                            # 使用文件修改时间
                            mtime = jsonl_file.stat().st_mtime
                            dt = datetime.fromtimestamp(mtime)

                        # 检查是否在统计范围内（去除时区信息进行比较）
                        dt_date = dt.replace(tzinfo=None) if dt.tzinfo else dt
                        start_date_naive = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
                        end_date_naive = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date

                        if not (start_date_naive <= dt_date <= end_date_naive + timedelta(days=1)):
                            continue

                        conversation_in_range = True
                        date_str = dt.strftime('%Y-%m-%d')

                        # 处理 token 统计
                        message_data = data.get('message', {})
                        usage = message_data.get('usage', {})
                        model = message_data.get('model', 'unknown')

                        input_tokens = usage.get('input_tokens', 0)
                        output_tokens = usage.get('output_tokens', 0)
                        cache_creation_tokens = usage.get('cache_creation_input_tokens', 0)
                        cache_read_tokens = usage.get('cache_read_input_tokens', 0)

                        if input_tokens == 0 and output_tokens == 0:
                            continue

                        conversation_messages += 1
                        stats['total_messages'] += 1

                        # 更新 token 统计
                        stats['tokens']['input'] += input_tokens
                        stats['tokens']['output'] += output_tokens
                        stats['tokens']['cache_creation'] += cache_creation_tokens
                        stats['tokens']['cache_read'] += cache_read_tokens

                        # 计算成本
                        pricing = PRICING.get(model, DEFAULT_PRICING)
                        msg_cost = (
                            input_tokens * pricing['input'] / 1_000_000 +
                            output_tokens * pricing['output'] / 1_000_000 +
                            cache_creation_tokens * pricing['cache_creation'] / 1_000_000 +
                            cache_read_tokens * pricing['cache_read'] / 1_000_000
                        )

                        stats['cost']['input'] += input_tokens * pricing['input'] / 1_000_000
                        stats['cost']['output'] += output_tokens * pricing['output'] / 1_000_000
                        stats['cost']['cache_creation'] += cache_creation_tokens * pricing['cache_creation'] / 1_000_000
                        stats['cost']['cache_read'] += cache_read_tokens * pricing['cache_read'] / 1_000_000
                        stats['cost']['total'] += msg_cost

                        # 按模型统计
                        stats['by_model'][model]['messages'] += 1
                        stats['by_model'][model]['tokens']['input'] += input_tokens
                        stats['by_model'][model]['tokens']['output'] += output_tokens
                        stats['by_model'][model]['tokens']['cache_creation'] += cache_creation_tokens
                        stats['by_model'][model]['tokens']['cache_read'] += cache_read_tokens
                        stats['by_model'][model]['cost'] += msg_cost

                        # 按日期统计
                        stats['by_date'][date_str]['messages'] += 1
                        stats['by_date'][date_str]['tokens']['input'] += input_tokens
                        stats['by_date'][date_str]['tokens']['output'] += output_tokens
                        stats['by_date'][date_str]['tokens']['cache_creation'] += cache_creation_tokens
                        stats['by_date'][date_str]['tokens']['cache_read'] += cache_read_tokens
                        stats['by_date'][date_str]['cost'] += msg_cost

                    except json.JSONDecodeError:
                        continue

            if conversation_in_range and conversation_messages > 0:
                stats['total_conversations'] += 1
                # 获取对话日期
                mtime = jsonl_file.stat().st_mtime
                date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
                if start_date <= datetime.fromtimestamp(mtime) <= end_date + timedelta(days=1):
                    stats['by_date'][date_str]['conversations'] += 1

        except Exception as e:
            continue

    return stats


def format_number(num):
    """格式化数字显示"""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.2f}K"
    else:
        return f"{num:,}"


def generate_markdown_report(stats, start_date, end_date, period):
    """生成 Markdown 格式报告"""

    report = []

    # 标题
    if period == 'weekly':
        report.append(f"# Claude Code Token 使用周报")
        report.append(f"\n**统计周期**：{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    elif period == 'monthly':
        report.append(f"# Claude Code Token 使用月报")
        report.append(f"\n**统计月份**：{start_date.strftime('%Y 年 %m 月')}")
    else:
        report.append(f"# Claude Code Token 使用报告")
        report.append(f"\n**统计周期**：{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

    # 概览
    report.append("\n## 📊 概览\n")
    report.append(f"- **对话数**：{stats['total_conversations']:,} 个")
    report.append(f"- **消息数**：{stats['total_messages']:,} 条")

    total_tokens = (stats['tokens']['input'] + stats['tokens']['output'] +
                   stats['tokens']['cache_creation'])
    report.append(f"- **Token 总计**：{format_number(total_tokens)}")
    report.append(f"- **总成本**：${stats['cost']['total']:.2f}")

    # 计算日均
    days = (end_date - start_date).days + 1
    report.append(f"\n### 日均统计\n")
    report.append(f"- **日均对话数**：{stats['total_conversations'] / days:.1f}")
    report.append(f"- **日均消息数**：{stats['total_messages'] / days:.1f}")
    report.append(f"- **日均成本**：${stats['cost']['total'] / days:.2f}")

    # 成本明细
    report.append("\n## 💰 成本明细\n")
    report.append("| 项目 | Token 数 | 单价 | 成本 |")
    report.append("|------|----------|------|------|")
    report.append(f"| 输入 | {format_number(stats['tokens']['input'])} | $3/MTok | ${stats['cost']['input']:.2f} |")
    report.append(f"| 输出 | {format_number(stats['tokens']['output'])} | $15/MTok | ${stats['cost']['output']:.2f} |")
    report.append(f"| 缓存创建 | {format_number(stats['tokens']['cache_creation'])} | $3.75/MTok | ${stats['cost']['cache_creation']:.2f} |")
    report.append(f"| 缓存读取 | {format_number(stats['tokens']['cache_read'])} | $0.30/MTok | ${stats['cost']['cache_read']:.2f} |")
    report.append(f"| **总计** | - | - | **${stats['cost']['total']:.2f}** |")

    # 按模型统计
    report.append("\n## 🤖 模型使用分布\n")
    report.append("| 模型 | 消息数 | Token 总计 | 成本 | 占比 |")
    report.append("|------|--------|------------|------|------|")

    for model, model_stats in sorted(stats['by_model'].items(),
                                     key=lambda x: x[1]['cost'], reverse=True):
        model_total = (model_stats['tokens']['input'] +
                      model_stats['tokens']['output'] +
                      model_stats['tokens']['cache_creation'])
        cost_percent = (model_stats['cost'] / stats['cost']['total'] * 100) if stats['cost']['total'] > 0 else 0

        # 简化模型名称显示
        model_display = model.replace('claude-', '').replace('-20250929', '').replace('-20251001', '').replace('-4-6', '')

        report.append(f"| {model_display} | {model_stats['messages']:,} | "
                     f"{format_number(model_total)} | "
                     f"${model_stats['cost']:.2f} | {cost_percent:.1f}% |")

    # 按日期统计
    report.append("\n## 📅 每日统计\n")
    report.append("| 日期 | 对话数 | 消息数 | Token 总计 | 成本 |")
    report.append("|------|--------|--------|------------|------|")

    for date_str in sorted(stats['by_date'].keys()):
        day_stats = stats['by_date'][date_str]
        day_total = (day_stats['tokens']['input'] +
                    day_stats['tokens']['output'] +
                    day_stats['tokens']['cache_creation'])

        report.append(f"| {date_str} | {day_stats['conversations']:,} | "
                     f"{day_stats['messages']:,} | "
                     f"{format_number(day_total)} | "
                     f"${day_stats['cost']:.2f} |")

    # 分析与建议
    report.append("\n## 💡 分析与建议\n")

    # 缓存效益分析
    cache_creation_cost = stats['cost']['cache_creation']
    cache_read_cost = stats['cost']['cache_read']
    input_cost = stats['cost']['input']

    if cache_creation_cost + cache_read_cost > input_cost:
        report.append("### 缓存策略\n")
        report.append(f"- 当前缓存总成本（${cache_creation_cost + cache_read_cost:.2f}）高于直接输入成本（${input_cost:.2f}）")
        report.append("- 建议评估缓存策略，考虑：")
        report.append("  - 减少频繁变化的提示词缓存")
        report.append("  - 增加单次对话工作量以提高缓存利用率")

    # 成本优化建议
    if stats['cost']['output'] > stats['cost']['input'] * 3:
        report.append("\n### 输出优化\n")
        report.append(f"- 输出成本（${stats['cost']['output']:.2f}）显著高于输入成本")
        report.append("- 建议：")
        report.append("  - 使用更精确的指令，减少冗长输出")
        report.append("  - 考虑使用 Haiku 模型处理简单任务")

    report.append("\n---")
    report.append(f"\n**⚠️ 统计范围说明**：本报告仅包含当前机器上的对话记录。如果在其他机器上也工作过，实际成本会更高。")
    report.append(f"\n*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return "\n".join(report)


def main():
    args = parse_args()

    # 获取日期范围
    start_date, end_date = get_date_range(args.period, args.start, args.end)

    print(f"📊 正在分析 {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} 的数据...\n")

    # 分析数据
    stats = analyze_conversations(start_date, end_date)

    if stats['total_conversations'] == 0:
        print("⚠️  该时间段内没有对话记录")
        return

    # 生成报告
    if args.format == 'markdown':
        report = generate_markdown_report(stats, start_date, end_date, args.period)
    else:
        report = generate_markdown_report(stats, start_date, end_date, args.period)  # 暂时都用 markdown

    # 输出报告
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.period == 'weekly':
        filename = f"weekly_report_{start_date.strftime('%Y%W')}.md"
    elif args.period == 'monthly':
        filename = f"monthly_report_{start_date.strftime('%Y%m')}.md"
    else:
        filename = f"report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.md"

    output_path = output_dir / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ 报告已生成: {output_path}")
    print(f"\n📊 快速预览:")
    print(f"   对话数: {stats['total_conversations']:,}")
    print(f"   消息数: {stats['total_messages']:,}")
    print(f"   总成本: ${stats['cost']['total']:.2f}")


if __name__ == "__main__":
    main()
