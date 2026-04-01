#!/usr/bin/env python3
"""
Token Tracker 真实场景演示

这个脚本展示了如何在实际调用 Claude API 的场景中使用 @track_tokens 装饰器。

注意：这个脚本本身不会调用 API，但演示了典型的使用模式。
要看到实际的 Token 统计，需要在脚本执行期间确实有 Claude Code 的交互。

使用建议：
1. 在 Claude Code 中执行任何操作（比如让 Claude 读取文件、分析代码等）
2. 在执行过程中调用被装饰的函数
3. 函数结束时会看到统计结果
"""

from token_tracker import track_tokens
import subprocess
import time


@track_tokens(log_to_file=True, log_dir="logs/cost_reports/session_logs")
def analyze_codebase_structure():
    """
    分析代码库结构（示例）

    在实际项目中，这个函数可能会：
    1. 读取多个文件
    2. 调用 AI 进行分析
    3. 生成报告

    如果在 Claude Code 会话中调用此函数，装饰器会捕获期间产生的 Token。
    """
    print("\n🔍 开始分析代码库结构...")

    # 示例：列出项目文件
    print("\n📁 扫描项目目录...")
    result = subprocess.run(['find', '.', '-name', '*.py', '-type', 'f'],
                          capture_output=True, text=True, timeout=5)
    py_files = result.stdout.strip().split('\n')
    print(f"   找到 {len(py_files)} 个 Python 文件")

    # 示例：分析脚本
    print("\n📊 分析脚本分布...")
    scripts = [f for f in py_files if f.startswith('./scripts/')]
    print(f"   scripts/ 目录: {len(scripts)} 个脚本")

    # 模拟一些处理时间
    time.sleep(1)

    print("\n✅ 分析完成")
    return {
        'total_files': len(py_files),
        'scripts': len(scripts),
    }


@track_tokens(log_to_file=True)
def process_with_ai_help():
    """
    需要 AI 辅助的处理任务（示例）

    实际场景：
    - 如果你在这个函数执行期间，通过 Claude Code 进行了交互
    - 比如让 Claude 帮你分析某个文件、生成代码等
    - 装饰器就会捕获这些交互产生的 Token
    """
    print("\n🤖 执行需要 AI 辅助的任务...")
    print("\n说明：")
    print("- 如果在此函数执行期间你与 Claude Code 有交互")
    print("- 比如让 Claude 读取文件、生成代码、分析问题等")
    print("- 那么函数结束时会显示这段时间内的 Token 使用统计")
    print("\n⏳ 等待 5 秒（模拟处理时间，期间你可以与 Claude 交互）...")

    for i in range(5, 0, -1):
        print(f"   {i}...", end=' ', flush=True)
        time.sleep(1)

    print("\n\n✅ 任务完成")
    return "processed"


def main():
    """主函数"""
    print("=" * 70)
    print(" Token Tracker 真实场景演示")
    print("=" * 70)

    print("\n📖 说明：")
    print("这个脚本展示了如何在实际工作流中使用 @track_tokens 装饰器。")
    print("\n要看到真实的 Token 统计：")
    print("1. 在 Claude Code 会话中运行这个脚本")
    print("2. 在函数执行期间，与 Claude 进行交互")
    print("3. 函数结束时会显示该时间段的 Token 使用量")

    print("\n" + "─" * 70)
    print("【演示 1】分析代码库结构")
    print("─" * 70)

    result1 = analyze_codebase_structure()
    print(f"\n分析结果: {result1}")

    print("\n" + "─" * 70)
    print("【演示 2】AI 辅助处理任务")
    print("─" * 70)

    result2 = process_with_ai_help()

    print("\n" + "=" * 70)
    print(" 演示完成")
    print("=" * 70)

    print("\n💡 提示：")
    print("- 查看生成的日志文件: logs/cost_reports/session_logs/")
    print("- 如果 Token 为 0，说明执行期间没有 Claude API 调用")
    print("- 这在纯 Python 脚本中是正常的")

    print("\n📚 实际应用场景：")
    print("\n1. **标注工作流**")
    print("   在调用 Claude API 进行文本标注的函数上添加装饰器")
    print("   ```python")
    print("   @track_tokens(log_to_file=True)")
    print("   def annotate_chapter(chapter_file):")
    print("       # 调用 Claude API 进行标注")
    print("       pass")
    print("   ```")

    print("\n2. **批量处理**")
    print("   统计批量处理所有章节的总成本")
    print("   ```python")
    print("   @track_tokens(log_to_file=True)")
    print("   def batch_annotate_all_chapters():")
    print("       for chapter in chapters:")
    print("           annotate_chapter(chapter)")
    print("   ```")

    print("\n3. **质量检查**")
    print("   统计生成质量报告的成本")
    print("   ```python")
    print("   @track_tokens(log_to_file=True)")
    print("   def generate_quality_reports():")
    print("       # 使用 Claude 分析标注质量")
    print("       pass")
    print("   ```")

    print("\n📊 查看统计报告：")
    print("   python scripts/generate_cost_report.py --period weekly")


if __name__ == "__main__":
    main()
