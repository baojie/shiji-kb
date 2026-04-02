#!/usr/bin/env python3
"""
分析项目时间投入

基于 Claude Code 对话记录，推断用户在项目上的实际时间投入。

核心逻辑：
1. 会话识别：相邻用户消息间隔 > 30分钟视为新会话
2. 有效时间：用户消息周围的活跃时段（每条消息前后±5分钟）
3. 过滤长间隔：两条用户消息间隔 > 10分钟，只计10分钟（Claude自动执行时间）

详细文档：skills/SKILL_10g_项目成本与时间统计.md
快速入门：scripts/TIME_TRACKING_QUICKSTART.md
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Tuple


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
SESSION_TIMEOUT = 30  # 会话超时：相邻用户消息间隔超过此值视为新会话
MAX_INTERVAL_COUNT = 10  # 最大间隔计时：超过此值的间隔只计这么多分钟（Claude自动执行）
MESSAGE_BUFFER = 5  # 消息缓冲时间：每条用户消息前后的缓冲时间


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
        """
        计算用户主动参与时间

        规则：
        1. 基于用户消息时间戳
        2. 每条用户消息周围有±MESSAGE_BUFFER分钟的缓冲时间
        3. 两条用户消息间隔超过MAX_INTERVAL_COUNT分钟，只计MAX_INTERVAL_COUNT分钟
        4. 有效时间不能超过会话总时长
        """
        if not self.user_messages:
            return timedelta(0)

        if len(self.user_messages) == 1:
            # 单条消息：只计前后缓冲时间
            return timedelta(minutes=MESSAGE_BUFFER * 2)

        # 排序用户消息
        sorted_msgs = sorted(self.user_messages)

        # 计算间隔时间
        total_active = timedelta(0)

        # 首条消息的前缓冲
        total_active += timedelta(minutes=MESSAGE_BUFFER)

        # 计算消息间的时间
        for i in range(len(sorted_msgs) - 1):
            interval = sorted_msgs[i + 1] - sorted_msgs[i]
            interval_minutes = interval.total_seconds() / 60

            # 超过MAX_INTERVAL_COUNT分钟的间隔，只计MAX_INTERVAL_COUNT分钟
            counted_minutes = min(interval_minutes, MAX_INTERVAL_COUNT)
            total_active += timedelta(minutes=counted_minutes)

        # 最后一条消息的后缓冲
        total_active += timedelta(minutes=MESSAGE_BUFFER)

        # 有效时间不能超过会话总时长
        duration = self.calculate_duration()
        return min(total_active, duration)

    def to_dict(self) -> Dict:
        """转换为字典"""
        duration = self.calculate_duration()
        active_time = self.calculate_active_time()

        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_minutes': duration.total_seconds() / 60,
            'active_minutes': active_time.total_seconds() / 60,
            'user_messages': self.user_message_count,
            'assistant_messages': self.assistant_message_count,
            'total_messages': self.total_messages,
        }


def parse_conversations() -> List[Session]:
    """解析所有对话，识别会话"""

    sessions: List[Session] = []

    # 收集所有 jsonl 文件
    jsonl_files = []
    for claude_dir in CLAUDE_DIRS:
        if claude_dir.exists():
            files = list(claude_dir.glob("*.jsonl"))
            jsonl_files.extend(files)

    if not jsonl_files:
        print("❌ 没有找到任何对话文件")
        return sessions

    print(f"📁 找到 {len(jsonl_files)} 个对话文件")

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

                        # 获取消息类型
                        msg_type = data.get('type', '')

                        # 用户消息：判断是否开始新会话
                        if msg_type == 'user':
                            # 检查是否需要开始新会话
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
                sessions.append(current_session)

        except Exception as e:
            print(f"⚠️  读取文件出错 {jsonl_file.name}: {e}")
            continue

    return sessions


def analyze_time_investment(sessions: List[Session]) -> Dict:
    """分析时间投入统计"""

    if not sessions:
        return {
            'total_sessions': 0,
            'total_duration_hours': 0,
            'total_active_hours': 0,
            'avg_session_minutes': 0,
            'by_date': {},
            'by_week': {},
            'by_month': {},
        }

    # 总体统计
    total_duration = sum(s.calculate_duration().total_seconds() for s in sessions) / 3600
    total_active = sum(s.calculate_active_time().total_seconds() for s in sessions) / 3600
    avg_duration = (sum(s.calculate_duration().total_seconds() for s in sessions) / len(sessions)) / 60

    # 按日期统计
    by_date = defaultdict(lambda: {
        'sessions': 0,
        'duration_hours': 0,
        'active_hours': 0,
        'messages': 0,
    })

    by_week = defaultdict(lambda: {
        'sessions': 0,
        'duration_hours': 0,
        'active_hours': 0,
        'messages': 0,
    })

    by_month = defaultdict(lambda: {
        'sessions': 0,
        'duration_hours': 0,
        'active_hours': 0,
        'messages': 0,
    })

    for session in sessions:
        date_str = session.start_time.strftime('%Y-%m-%d')
        week_str = session.start_time.strftime('%Y-W%W')
        month_str = session.start_time.strftime('%Y-%m')

        duration_hours = session.calculate_duration().total_seconds() / 3600
        active_hours = session.calculate_active_time().total_seconds() / 3600

        # 按日期
        by_date[date_str]['sessions'] += 1
        by_date[date_str]['duration_hours'] += duration_hours
        by_date[date_str]['active_hours'] += active_hours
        by_date[date_str]['messages'] += session.total_messages

        # 按周
        by_week[week_str]['sessions'] += 1
        by_week[week_str]['duration_hours'] += duration_hours
        by_week[week_str]['active_hours'] += active_hours
        by_week[week_str]['messages'] += session.total_messages

        # 按月
        by_month[month_str]['sessions'] += 1
        by_month[month_str]['duration_hours'] += duration_hours
        by_month[month_str]['active_hours'] += active_hours
        by_month[month_str]['messages'] += session.total_messages

    return {
        'total_sessions': len(sessions),
        'total_duration_hours': total_duration,
        'total_active_hours': total_active,
        'avg_session_minutes': avg_duration,
        'by_date': dict(by_date),
        'by_week': dict(by_week),
        'by_month': dict(by_month),
    }


def format_hours(hours: float) -> str:
    """格式化小时数显示"""
    if hours < 1:
        return f"{hours * 60:.0f}分钟"
    elif hours < 10:
        return f"{hours:.1f}小时"
    else:
        return f"{hours:.0f}小时"


def print_report(stats: Dict):
    """打印统计报告"""

    print("\n" + "=" * 80)
    print("⏱️  项目时间投入分析")
    print("=" * 80)

    print(f"\n📊 总体统计")
    print(f"  会话数量:           {stats['total_sessions']:>10,} 次")
    print(f"  总时长:             {format_hours(stats['total_duration_hours']):>15}")
    print(f"  有效工作时间:       {format_hours(stats['total_active_hours']):>15}")
    print(f"  平均会话时长:       {stats['avg_session_minutes']:>12.0f} 分钟")

    # 计算效率比
    if stats['total_duration_hours'] > 0:
        efficiency = stats['total_active_hours'] / stats['total_duration_hours'] * 100
        print(f"  主动参与率:         {efficiency:>14.1f}%")

    # 按月统计
    if stats['by_month']:
        print(f"\n📅 按月统计")
        print(f"  {'月份':<10} {'会话数':>6} {'总时长':>12} {'有效时间':>12} {'参与率':>8}")
        print("  " + "-" * 60)

        for month in sorted(stats['by_month'].keys(), reverse=True):
            month_stats = stats['by_month'][month]
            participation = (month_stats['active_hours'] / month_stats['duration_hours'] * 100) \
                if month_stats['duration_hours'] > 0 else 0

            print(f"  {month:<10} {month_stats['sessions']:>6} "
                  f"{format_hours(month_stats['duration_hours']):>12} "
                  f"{format_hours(month_stats['active_hours']):>12} "
                  f"{participation:>7.1f}%")

    # 按日期统计（最近30天）
    if stats['by_date']:
        print(f"\n📅 每日统计（最近30天）")
        print(f"  {'日期':<12} {'会话':>4} {'总时长':>10} {'有效时间':>10} {'消息数':>6}")
        print("  " + "-" * 50)

        sorted_dates = sorted(stats['by_date'].keys(), reverse=True)[:30]
        for date in sorted_dates:
            day_stats = stats['by_date'][date]
            print(f"  {date:<12} {day_stats['sessions']:>4} "
                  f"{format_hours(day_stats['duration_hours']):>10} "
                  f"{format_hours(day_stats['active_hours']):>10} "
                  f"{day_stats['messages']:>6}")

    print("\n" + "=" * 80)
    print("\n💡 说明:")
    print("  - 会话识别：相邻用户消息间隔 > 30分钟视为新会话")
    print("  - 有效时间：用户消息周围的活跃时段（每条消息±5分钟）")
    print("  - 长间隔过滤：两条用户消息间隔 > 10分钟，只计10分钟（Claude自动执行）")
    print("  - 主动参与率 = 有效工作时间 / 总时长")

    print("\n⚠️  统计范围说明:")
    print("  本统计仅包含当前机器上的对话记录 (~/.claude/projects/)")
    print("  如果在其他机器上也工作过，需要在每台机器上分别统计")
    print("  实际项目总时间 = 所有机器的时间之和")
    print("=" * 80)


def main():
    """主函数"""
    print("⏱️  正在分析项目时间投入...\n")

    # 解析对话
    sessions = parse_conversations()

    if not sessions:
        print("⚠️  没有找到任何会话记录")
        return

    print(f"✅ 识别到 {len(sessions)} 个会话\n")

    # 分析统计
    stats = analyze_time_investment(sessions)

    # 打印报告
    print_report(stats)


if __name__ == "__main__":
    main()
