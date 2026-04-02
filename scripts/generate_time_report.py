#!/usr/bin/env python3
"""
生成项目时间投入报告

Usage:
    python scripts/generate_time_report.py --period weekly
    python scripts/generate_time_report.py --period monthly
    python scripts/generate_time_report.py --start 2026-03-01 --end 2026-03-31
    python scripts/generate_time_report.py --period monthly --output logs/time_reports/

详细文档：skills/SKILL_10g_项目成本与时间统计.md
快速入门：scripts/TIME_TRACKING_QUICKSTART.md
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict


def load_config():
    """加载配置文件"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / ".claude_cost_config.json"

    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        print(f"   请复制 .claude_cost_config.example.json 为 .claude_cost_config.json")
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

# Claude 对话记录目录
CLAUDE_DIRS = [
    Path.home() / ".claude" / "projects" / path
    for path in CONFIG.get('claude_project_paths', [])
]

# 时间参数配置（分钟）
SESSION_TIMEOUT = 30  # 会话超时
MAX_INTERVAL_COUNT = 10  # 最大间隔计时
MESSAGE_BUFFER = 5  # 消息缓冲时间


class Session:
    """会话对象"""
    def __init__(self, start_time: datetime):
        self.start_time = start_time
        self.end_time = start_time
        self.user_messages: List[datetime] = []
        self.total_messages = 0
        self.user_message_count = 0
        self.assistant_message_count = 0

    def add_message(self, timestamp: datetime, msg_type: str):
        """添加消息"""
        self.end_time = max(self.end_time, timestamp)
        self.total_messages += 1

        if msg_type == 'user':
            self.user_messages.append(timestamp)
            self.user_message_count += 1
        elif msg_type == 'assistant':
            self.assistant_message_count += 1

    def calculate_duration(self) -> timedelta:
        """计算会话总时长"""
        return self.end_time - self.start_time

    def calculate_active_time(self) -> timedelta:
        """计算用户主动参与时间"""
        if not self.user_messages:
            return timedelta(0)

        if len(self.user_messages) == 1:
            return timedelta(minutes=MESSAGE_BUFFER * 2)

        sorted_msgs = sorted(self.user_messages)
        total_active = timedelta(minutes=MESSAGE_BUFFER)

        for i in range(len(sorted_msgs) - 1):
            interval = sorted_msgs[i + 1] - sorted_msgs[i]
            interval_minutes = interval.total_seconds() / 60
            counted_minutes = min(interval_minutes, MAX_INTERVAL_COUNT)
            total_active += timedelta(minutes=counted_minutes)

        total_active += timedelta(minutes=MESSAGE_BUFFER)

        # 有效时间不能超过会话总时长
        duration = self.calculate_duration()
        return min(total_active, duration)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='生成项目时间投入报告')
    parser.add_argument('--period', choices=['weekly', 'monthly'], help='报告周期')
    parser.add_argument('--start', help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--output', default='logs/time_reports', help='输出目录')
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


def parse_conversations_in_range(start_date: datetime, end_date: datetime) -> List[Session]:
    """解析指定时间范围内的对话"""

    sessions: List[Session] = []

    # 收集所有 jsonl 文件
    jsonl_files = []
    for claude_dir in CLAUDE_DIRS:
        if claude_dir.exists():
            files = list(claude_dir.glob("*.jsonl"))
            jsonl_files.extend(files)

    if not jsonl_files:
        return sessions

    # 解析每个对话文件
    for jsonl_file in jsonl_files:
        try:
            current_session = None
            last_user_time = None

            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # 获取时间戳
                        timestamp = data.get('timestamp')
                        if not timestamp:
                            continue

                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        dt_naive = dt.replace(tzinfo=None)

                        # 检查是否在统计范围内
                        if not (start_date <= dt_naive <= end_date + timedelta(days=1)):
                            continue

                        # 获取消息类型
                        msg_type = data.get('type', '')

                        # 用户消息：判断是否开始新会话
                        if msg_type == 'user':
                            if (current_session is None or
                                last_user_time is None or
                                (dt_naive - last_user_time).total_seconds() > SESSION_TIMEOUT * 60):

                                # 保存旧会话
                                if current_session and current_session.total_messages > 0:
                                    sessions.append(current_session)

                                # 开始新会话
                                current_session = Session(dt_naive)

                            last_user_time = dt_naive

                        # 添加消息到当前会话
                        if current_session:
                            current_session.add_message(dt_naive, msg_type)

                    except json.JSONDecodeError:
                        continue

            # 保存最后一个会话
            if current_session and current_session.total_messages > 0:
                # 确保会话在时间范围内
                if start_date <= current_session.start_time <= end_date + timedelta(days=1):
                    sessions.append(current_session)

        except Exception as e:
            continue

    return sessions


def analyze_sessions(sessions: List[Session], start_date: datetime, end_date: datetime) -> Dict:
    """分析会话统计"""

    if not sessions:
        return {
            'total_sessions': 0,
            'total_duration_hours': 0,
            'total_active_hours': 0,
            'total_messages': 0,
            'avg_session_minutes': 0,
            'by_date': {},
        }

    # 总体统计
    total_duration = sum(s.calculate_duration().total_seconds() for s in sessions) / 3600
    total_active = sum(s.calculate_active_time().total_seconds() for s in sessions) / 3600
    total_messages = sum(s.total_messages for s in sessions)
    avg_duration = (sum(s.calculate_duration().total_seconds() for s in sessions) / len(sessions)) / 60

    # 按日期统计
    by_date = defaultdict(lambda: {
        'sessions': 0,
        'duration_hours': 0,
        'active_hours': 0,
        'messages': 0,
    })

    for session in sessions:
        date_str = session.start_time.strftime('%Y-%m-%d')
        duration_hours = session.calculate_duration().total_seconds() / 3600
        active_hours = session.calculate_active_time().total_seconds() / 3600

        by_date[date_str]['sessions'] += 1
        by_date[date_str]['duration_hours'] += duration_hours
        by_date[date_str]['active_hours'] += active_hours
        by_date[date_str]['messages'] += session.total_messages

    return {
        'total_sessions': len(sessions),
        'total_duration_hours': total_duration,
        'total_active_hours': total_active,
        'total_messages': total_messages,
        'avg_session_minutes': avg_duration,
        'by_date': dict(by_date),
    }


def format_hours(hours: float) -> str:
    """格式化小时数显示"""
    if hours < 1:
        return f"{hours * 60:.0f}分钟"
    elif hours < 10:
        return f"{hours:.1f}小时"
    else:
        return f"{hours:.0f}小时"


def generate_markdown_report(stats: Dict, start_date: datetime, end_date: datetime, period: str) -> str:
    """生成 Markdown 格式报告"""

    report = []

    # 标题
    if period == 'weekly':
        report.append(f"# 项目时间投入周报")
        report.append(f"\n**统计周期**：{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    elif period == 'monthly':
        report.append(f"# 项目时间投入月报")
        report.append(f"\n**统计月份**：{start_date.strftime('%Y 年 %m 月')}")
    else:
        report.append(f"# 项目时间投入报告")
        report.append(f"\n**统计周期**：{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

    # 概览
    report.append("\n## ⏱️ 概览\n")
    report.append(f"- **会话数量**：{stats['total_sessions']:,} 次")
    report.append(f"- **总时长**：{format_hours(stats['total_duration_hours'])}")
    report.append(f"- **有效工作时间**：{format_hours(stats['total_active_hours'])}")
    report.append(f"- **消息总数**：{stats['total_messages']:,} 条")

    # 计算效率比
    if stats['total_duration_hours'] > 0:
        efficiency = stats['total_active_hours'] / stats['total_duration_hours'] * 100
        report.append(f"- **主动参与率**：{efficiency:.1f}%")

    # 日均统计
    days = (end_date - start_date).days + 1
    report.append(f"\n### 日均统计\n")
    report.append(f"- **日均会话数**：{stats['total_sessions'] / days:.1f}")
    report.append(f"- **日均工作时间**：{format_hours(stats['total_active_hours'] / days)}")
    report.append(f"- **日均消息数**：{stats['total_messages'] / days:.0f}")

    # 时间明细
    report.append("\n## 📊 时间明细\n")
    report.append("| 项目 | 时长 | 占比 |")
    report.append("|------|------|------|")

    total_duration = stats['total_duration_hours']
    total_active = stats['total_active_hours']

    if total_duration > 0:
        active_percent = (total_active / total_duration * 100)
        idle_hours = total_duration - total_active
        idle_percent = 100 - active_percent

        report.append(f"| 有效工作时间 | {format_hours(total_active)} | {active_percent:.1f}% |")
        report.append(f"| Claude自动执行 | {format_hours(idle_hours)} | {idle_percent:.1f}% |")
        report.append(f"| **总计** | **{format_hours(total_duration)}** | 100% |")

    # 每日统计
    report.append("\n## 📅 每日统计\n")
    report.append("| 日期 | 会话数 | 总时长 | 有效时间 | 参与率 | 消息数 |")
    report.append("|------|--------|--------|----------|--------|--------|")

    for date_str in sorted(stats['by_date'].keys()):
        day_stats = stats['by_date'][date_str]
        participation = (day_stats['active_hours'] / day_stats['duration_hours'] * 100) \
            if day_stats['duration_hours'] > 0 else 0

        report.append(f"| {date_str} | {day_stats['sessions']:,} | "
                     f"{format_hours(day_stats['duration_hours'])} | "
                     f"{format_hours(day_stats['active_hours'])} | "
                     f"{participation:.0f}% | "
                     f"{day_stats['messages']:,} |")

    # 分析与建议
    report.append("\n## 💡 分析与建议\n")

    # 参与率分析
    if total_duration > 0:
        efficiency = total_active / total_duration * 100

        if efficiency < 30:
            report.append("### 工作模式\n")
            report.append(f"- 当前主动参与率较低（{efficiency:.1f}%），说明大部分时间Claude在自动执行任务")
            report.append("- 建议：")
            report.append("  - 这是正常的自动化工作模式，无需优化")
            report.append("  - 如需提高参与率，可以将长任务拆分为多个交互式步骤")
        elif efficiency > 70:
            report.append("### 工作模式\n")
            report.append(f"- 当前主动参与率较高（{efficiency:.1f}%），说明大部分时间在主动指导")
            report.append("- 建议：")
            report.append("  - 考虑将重复性任务自动化，减少手动干预")
            report.append("  - 使用批量处理脚本提高效率")

    # 工作时间分布
    if stats['by_date']:
        dates_with_work = [d for d, s in stats['by_date'].items() if s['active_hours'] > 0]
        work_days = len(dates_with_work)

        if work_days > 0:
            report.append("\n### 工作节奏\n")
            report.append(f"- 工作天数：{work_days} 天（共 {days} 天）")
            avg_daily_active = total_active / work_days
            report.append(f"- 工作日平均投入：{format_hours(avg_daily_active)}")

            if avg_daily_active > 4:
                report.append("- 工作日投入较高，注意适当休息")
            elif avg_daily_active < 1:
                report.append("- 工作日投入较少，可能适合目前的项目阶段")

    report.append("\n---")
    report.append(f"\n**⚠️ 统计范围说明**：本报告仅包含当前机器上的对话记录。如果在其他机器上也工作过，实际时间会更多。")

    report.append(f"\n**📝 统计方法**：")
    report.append(f"- 会话识别：相邻用户消息间隔 > {SESSION_TIMEOUT}分钟视为新会话")
    report.append(f"- 有效时间：用户消息周围的活跃时段（每条消息±{MESSAGE_BUFFER}分钟）")
    report.append(f"- 长间隔过滤：两条用户消息间隔 > {MAX_INTERVAL_COUNT}分钟，只计{MAX_INTERVAL_COUNT}分钟（Claude自动执行）")

    report.append(f"\n*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return "\n".join(report)


def main():
    args = parse_args()

    # 获取日期范围
    start_date, end_date = get_date_range(args.period, args.start, args.end)

    print(f"⏱️  正在分析 {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} 的数据...\n")

    # 解析对话
    sessions = parse_conversations_in_range(start_date, end_date)

    if not sessions:
        print("⚠️  该时间段内没有会话记录")
        return

    print(f"✅ 识别到 {len(sessions)} 个会话\n")

    # 分析统计
    stats = analyze_sessions(sessions, start_date, end_date)

    # 生成报告
    report = generate_markdown_report(stats, start_date, end_date, args.period)

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
    print(f"   会话数: {stats['total_sessions']:,}")
    print(f"   总时长: {format_hours(stats['total_duration_hours'])}")
    print(f"   有效工作时间: {format_hours(stats['total_active_hours'])}")


if __name__ == "__main__":
    main()
