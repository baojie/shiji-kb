#!/usr/bin/env python3
"""
Token 使用量统计装饰器

用法：
    from scripts.token_tracker import track_tokens

    @track_tokens()
    def my_function():
        # 你的代码
        pass

    @track_tokens(log_to_file=True, log_dir="logs/cost_reports")
    def another_function():
        # 会自动记录到日志文件
        pass
"""

import json
import functools
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Any


class TokenTracker:
    """Token 使用量追踪器"""

    def __init__(self):
        self.config = self._load_config()
        self.claude_dirs = self._get_claude_dirs()
        self.pricing = self.config.get('pricing', {})
        self.default_pricing = self.pricing.get('claude-sonnet-4-5-20250929', {
            'input': 3.0,
            'output': 15.0,
            'cache_creation': 3.75,
            'cache_read': 0.30,
        })

    def _load_config(self) -> dict:
        """加载配置文件"""
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        config_path = project_root / ".claude_cost_config.json"

        if not config_path.exists():
            # 如果配置文件不存在，返回默认配置
            return {
                'claude_project_paths': [],
                'pricing': {
                    'claude-sonnet-4-5-20250929': {
                        'input': 3.0,
                        'output': 15.0,
                        'cache_creation': 3.75,
                        'cache_read': 0.30,
                    }
                }
            }

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {'claude_project_paths': [], 'pricing': {}}

    def _get_claude_dirs(self) -> list:
        """获取 Claude 对话目录"""
        return [
            Path.home() / ".claude" / "projects" / path
            for path in self.config.get('claude_project_paths', [])
        ]

    def get_all_jsonl_files(self) -> list:
        """获取所有对话文件"""
        jsonl_files = []
        for claude_dir in self.claude_dirs:
            if claude_dir.exists():
                files = list(claude_dir.glob("*.jsonl"))
                jsonl_files.extend(files)
        return jsonl_files

    def get_latest_file_mtime(self, files: list) -> Optional[float]:
        """获取最新文件的修改时间"""
        if not files:
            return None
        return max(f.stat().st_mtime for f in files)

    def analyze_new_messages(self, start_time: Optional[float], end_time: Optional[float]) -> dict:
        """分析指定时间范围内的消息"""
        stats = {
            'messages': 0,
            'tokens': {
                'input': 0,
                'output': 0,
                'cache_creation': 0,
                'cache_read': 0,
                'total': 0,
            },
            'cost': {
                'input': 0.0,
                'output': 0.0,
                'cache_creation': 0.0,
                'cache_read': 0.0,
                'total': 0.0,
            },
            'by_model': {},
        }

        jsonl_files = self.get_all_jsonl_files()

        for jsonl_file in jsonl_files:
            # 如果文件修改时间早于起始时间，跳过
            if start_time and jsonl_file.stat().st_mtime < start_time:
                continue

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
                                msg_time = dt.timestamp()
                            else:
                                msg_time = jsonl_file.stat().st_mtime

                            # 检查时间范围
                            if start_time and msg_time < start_time:
                                continue
                            if end_time and msg_time > end_time:
                                continue

                            # 提取 token 信息
                            message_data = data.get('message', {})
                            usage = message_data.get('usage', {})
                            model = message_data.get('model', 'unknown')

                            input_tokens = usage.get('input_tokens', 0)
                            output_tokens = usage.get('output_tokens', 0)
                            cache_creation_tokens = usage.get('cache_creation_input_tokens', 0)
                            cache_read_tokens = usage.get('cache_read_input_tokens', 0)

                            if input_tokens == 0 and output_tokens == 0:
                                continue

                            stats['messages'] += 1

                            # 更新 token 统计
                            stats['tokens']['input'] += input_tokens
                            stats['tokens']['output'] += output_tokens
                            stats['tokens']['cache_creation'] += cache_creation_tokens
                            stats['tokens']['cache_read'] += cache_read_tokens
                            stats['tokens']['total'] += (input_tokens + output_tokens +
                                                        cache_creation_tokens)

                            # 计算成本
                            pricing = self.pricing.get(model, self.default_pricing)
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
                            if model not in stats['by_model']:
                                stats['by_model'][model] = {
                                    'messages': 0,
                                    'tokens': 0,
                                    'cost': 0.0,
                                }
                            stats['by_model'][model]['messages'] += 1
                            stats['by_model'][model]['tokens'] += (input_tokens + output_tokens +
                                                                  cache_creation_tokens)
                            stats['by_model'][model]['cost'] += msg_cost

                        except json.JSONDecodeError:
                            continue

            except Exception:
                continue

        return stats

    def format_stats(self, stats: dict, elapsed_time: float) -> str:
        """格式化统计信息为字符串"""
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("📊 Token 使用统计")
        lines.append("=" * 60)

        if stats['messages'] == 0:
            lines.append("⚠️  此次会话没有检测到新的 Token 使用")
            lines.append("=" * 60)
            return "\n".join(lines)

        lines.append(f"⏱️  执行时间: {elapsed_time:.2f} 秒")
        lines.append(f"💬 消息数: {stats['messages']:,}")
        lines.append("")

        # Token 统计
        lines.append("📦 Token 使用量:")
        lines.append(f"   输入:       {stats['tokens']['input']:>12,}")
        lines.append(f"   输出:       {stats['tokens']['output']:>12,}")
        lines.append(f"   缓存创建:   {stats['tokens']['cache_creation']:>12,}")
        lines.append(f"   缓存读取:   {stats['tokens']['cache_read']:>12,}")
        lines.append(f"   {'─' * 30}")
        lines.append(f"   总计:       {stats['tokens']['total']:>12,}")
        lines.append("")

        # 成本统计
        lines.append("💰 成本分析:")
        lines.append(f"   输入成本:       ${stats['cost']['input']:>10.4f}")
        lines.append(f"   输出成本:       ${stats['cost']['output']:>10.4f}")
        lines.append(f"   缓存创建成本:   ${stats['cost']['cache_creation']:>10.4f}")
        lines.append(f"   缓存读取成本:   ${stats['cost']['cache_read']:>10.4f}")
        lines.append(f"   {'─' * 35}")
        lines.append(f"   总成本:         ${stats['cost']['total']:>10.4f}")
        lines.append("")

        # 按模型统计
        if stats['by_model']:
            lines.append("🤖 模型使用:")
            for model, model_stats in sorted(stats['by_model'].items(),
                                            key=lambda x: x[1]['cost'], reverse=True):
                model_name = model.replace('claude-', '').replace('-20250929', '')
                lines.append(f"   {model_name}:")
                lines.append(f"      消息: {model_stats['messages']:,} | "
                           f"Token: {model_stats['tokens']:,} | "
                           f"成本: ${model_stats['cost']:.4f}")

        lines.append("=" * 60)
        return "\n".join(lines)

    def save_to_log(self, stats: dict, function_name: str, log_dir: str):
        """保存统计信息到日志文件"""
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_path / f"token_usage_{timestamp}.json"

        log_data = {
            'timestamp': datetime.now().isoformat(),
            'function': function_name,
            'stats': stats,
        }

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        return log_file


def track_tokens(
    print_stats: bool = True,
    log_to_file: bool = False,
    log_dir: str = "logs/cost_reports/session_logs"
) -> Callable:
    """
    装饰器：统计函数执行期间的 Token 使用量

    参数：
        print_stats: 是否打印统计信息到控制台（默认 True）
        log_to_file: 是否保存统计信息到日志文件（默认 False）
        log_dir: 日志文件保存目录（默认 "logs/cost_reports/session_logs"）

    用法：
        @track_tokens()
        def my_function():
            pass

        @track_tokens(log_to_file=True)
        def my_function():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            tracker = TokenTracker()

            # 记录开始时间和文件状态
            start_time = datetime.now().timestamp()
            import time
            func_start_time = time.time()

            # 执行函数
            result = func(*args, **kwargs)

            # 计算执行时间
            elapsed_time = time.time() - func_start_time

            # 记录结束时间
            end_time = datetime.now().timestamp()

            # 分析这段时间内的 token 使用
            stats = tracker.analyze_new_messages(start_time, end_time)

            # 打印统计信息
            if print_stats:
                stats_text = tracker.format_stats(stats, elapsed_time)
                print(stats_text)

            # 保存到日志文件
            if log_to_file:
                log_file = tracker.save_to_log(stats, func.__name__, log_dir)
                if print_stats:
                    print(f"\n📝 统计日志已保存: {log_file}")

            return result

        return wrapper

    return decorator


# 示例用法（可以删除或保留作为参考）
if __name__ == "__main__":
    # 示例1：基本用法
    @track_tokens()
    def example_function():
        """示例函数"""
        import time
        print("执行示例函数...")
        time.sleep(1)  # 模拟耗时操作
        print("函数执行完毕")

    # 示例2：带日志记录
    @track_tokens(log_to_file=True)
    def example_with_logging():
        """带日志记录的示例函数"""
        import time
        print("执行带日志记录的函数...")
        time.sleep(1)
        print("函数执行完毕")

    # 运行示例
    print("=" * 60)
    print("示例 1: 基本用法（仅打印统计）")
    print("=" * 60)
    example_function()

    print("\n\n")
    print("=" * 60)
    print("示例 2: 带日志记录")
    print("=" * 60)
    example_with_logging()
