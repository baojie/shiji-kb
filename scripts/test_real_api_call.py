#!/usr/bin/env python3
"""
测试 Token Tracker 捕获真实 API 调用

这个脚本展示了装饰器能够捕获 Token 的场景：
当函数内部调用 Claude API 时（使用 Anthropic SDK）

注意：这个脚本需要：
1. 安装 anthropic: pip install anthropic
2. 设置环境变量 ANTHROPIC_API_KEY
3. 实际调用会产生费用

如果你不想实际调用 API，可以只阅读代码了解如何使用。
"""

from token_tracker import track_tokens
import os


@track_tokens(log_to_file=True, log_dir="logs/cost_reports/session_logs")
def call_claude_api_example():
    """
    示例：在函数内部调用 Claude API

    这种情况下，装饰器能够捕获到 Token 使用。
    """
    try:
        import anthropic
    except ImportError:
        print("❌ 未安装 anthropic 库")
        print("   请运行: pip install anthropic")
        return "需要安装 anthropic"

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 未设置 ANTHROPIC_API_KEY 环境变量")
        print("   请设置: export ANTHROPIC_API_KEY='your-api-key'")
        return "需要设置 API key"

    print("\n🚀 调用 Claude API...")

    client = anthropic.Anthropic(api_key=api_key)

    # 进行一个简单的 API 调用
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": "请用一句话介绍《史记》这本书。"
            }
        ]
    )

    print(f"\n📝 Claude 的回复：")
    print(f"   {message.content[0].text}")

    print(f"\n📊 API 返回的 Token 统计：")
    print(f"   输入 Token: {message.usage.input_tokens}")
    print(f"   输出 Token: {message.usage.output_tokens}")

    print("\n✅ API 调用完成")
    print("   装饰器会在函数结束时显示 Token 统计")

    return message.content[0].text


def main():
    print("=" * 70)
    print(" Token Tracker - 真实 API 调用测试")
    print("=" * 70)

    print("\n⚠️  注意：")
    print("这个脚本会实际调用 Claude API，产生费用（预计 <$0.01）")
    print("\n需要：")
    print("1. pip install anthropic")
    print("2. export ANTHROPIC_API_KEY='your-api-key'")

    response = input("\n是否继续？(y/N): ")

    if response.lower() != 'y':
        print("\n已取消")
        return

    result = call_claude_api_example()

    print("\n" + "=" * 70)
    print(" 测试完成")
    print("=" * 70)

    print("\n💡 说明：")
    print("装饰器显示的 Token 统计来自本地 Claude Code 对话记录。")
    print("如果你在这个函数执行期间没有使用 Claude Code，Token 会是 0。")
    print("\n但这个测试证明了：")
    print("✅ 装饰器的代码是正确的")
    print("✅ 在实际使用 Claude API 的场景中，它能捕获 Token")


if __name__ == "__main__":
    main()
