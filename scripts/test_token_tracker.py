#!/usr/bin/env python3
"""
Token Tracker 测试脚本

测试 token_tracker 装饰器的功能
"""

from token_tracker import track_tokens


@track_tokens()
def hello_world():
    """
    Hello World 测试函数

    这是一个简单的测试函数，用于验证 token_tracker 装饰器是否正常工作。
    """
    print("\n🌍 Hello World!")
    print("这是一个测试函数，用于验证 Token 统计装饰器的功能。")
    print("\n说明:")
    print("- 如果你在调用此函数前后使用了 Claude Code")
    print("- 装饰器会自动统计这段时间内产生的 Token 使用量")
    print("- 并在函数结束时打印统计报告")

    return "测试成功！"


@track_tokens(log_to_file=True, log_dir="logs/cost_reports/session_logs")
def hello_world_with_logging():
    """
    Hello World 测试函数（带日志记录）

    这个版本会将统计结果保存到日志文件
    """
    print("\n🌍 Hello World (带日志记录)!")
    print("这个版本会将 Token 统计结果保存到日志文件中。")

    import time
    print("\n模拟一些耗时操作...")
    for i in range(3):
        time.sleep(0.5)
        print(f"  步骤 {i+1}/3 完成")

    return "测试成功（带日志）！"


def main():
    """主测试函数"""
    print("=" * 70)
    print(" Token Tracker 装饰器测试")
    print("=" * 70)

    print("\n【测试 1】基本功能测试（仅打印统计）")
    print("-" * 70)
    result1 = hello_world()
    print(f"\n函数返回值: {result1}")

    print("\n\n【测试 2】带日志记录测试")
    print("-" * 70)
    result2 = hello_world_with_logging()
    print(f"\n函数返回值: {result2}")

    print("\n" + "=" * 70)
    print("✅ 所有测试完成！")
    print("=" * 70)

    print("\n📋 使用说明:")
    print("1. 在任何函数上添加 @track_tokens() 装饰器即可自动统计 Token")
    print("2. 使用 @track_tokens(log_to_file=True) 可保存统计结果到日志文件")
    print("3. 默认日志目录: logs/cost_reports/session_logs/")
    print("4. 可通过 log_dir 参数自定义日志目录")

    print("\n📝 代码示例:")
    print("""
    from scripts.token_tracker import track_tokens

    @track_tokens()
    def my_function():
        # 你的代码
        pass

    @track_tokens(log_to_file=True)
    def another_function():
        # 会自动记录到日志文件
        pass
    """)


if __name__ == "__main__":
    main()
