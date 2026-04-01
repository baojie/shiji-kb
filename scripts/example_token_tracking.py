#!/usr/bin/env python3
"""
Token Tracker 实际应用示例

展示如何在实际项目中使用 @track_tokens 装饰器来统计成本
"""

from token_tracker import track_tokens
import time


@track_tokens()
def process_single_chapter(chapter_name: str):
    """
    处理单个章节（示例）

    在实际项目中，这可能是：
    - 调用 Claude API 进行文本标注
    - 使用 AI 生成校对报告
    - 进行知识抽取
    """
    print(f"\n正在处理章节: {chapter_name}")
    print("- 读取原始文本")
    time.sleep(0.5)
    print("- 调用 AI 进行标注（这里会产生 Token 使用）")
    time.sleep(0.5)
    print("- 保存标注结果")
    print(f"✅ {chapter_name} 处理完成")
    return f"{chapter_name}_tagged.md"


@track_tokens(log_to_file=True, log_dir="logs/cost_reports/session_logs")
def batch_process_chapters(chapter_list: list):
    """
    批量处理章节（带日志记录）

    这个版本会：
    1. 统计整个批处理过程的 Token 使用
    2. 将统计结果保存到日志文件
    3. 方便后续成本分析
    """
    print(f"\n📦 开始批量处理 {len(chapter_list)} 个章节")
    results = []

    for i, chapter in enumerate(chapter_list, 1):
        print(f"\n[{i}/{len(chapter_list)}] 处理: {chapter}")
        time.sleep(0.3)
        # 实际项目中这里会调用 AI API
        results.append(f"{chapter}_processed")

    print(f"\n✅ 批量处理完成，共处理 {len(results)} 个章节")
    return results


@track_tokens(log_to_file=True)
def generate_quality_report(chapter_name: str):
    """
    生成质量报告（示例）

    实际应用：
    - 使用 AI 分析标注质量
    - 生成校对报告
    - 提取关键信息
    """
    print(f"\n📊 正在为 {chapter_name} 生成质量报告")

    steps = [
        "分析标注完整性",
        "检查格式规范性",
        "提取统计数据",
        "生成可视化报告",
        "保存报告文件"
    ]

    for step in steps:
        print(f"  ⏳ {step}...")
        time.sleep(0.2)

    print(f"✅ 质量报告已生成")
    return f"quality_report_{chapter_name}.md"


def main():
    """主函数：演示各种使用场景"""

    print("=" * 70)
    print(" Token Tracker 实际应用示例")
    print("=" * 70)

    # 场景 1: 处理单个章节
    print("\n【场景 1】处理单个章节")
    print("-" * 70)
    result1 = process_single_chapter("001_五帝本纪")

    # 场景 2: 批量处理（带日志）
    print("\n\n【场景 2】批量处理章节（带成本日志）")
    print("-" * 70)
    chapters = [
        "002_夏本纪",
        "003_殷本纪",
        "004_周本纪",
    ]
    results = batch_process_chapters(chapters)

    # 场景 3: 生成报告
    print("\n\n【场景 3】生成质量报告")
    print("-" * 70)
    report = generate_quality_report("001_五帝本纪")

    # 总结
    print("\n" + "=" * 70)
    print(" 演示完成")
    print("=" * 70)

    print("\n📋 实际应用建议:")
    print("\n1. **开发阶段**")
    print("   - 使用 @track_tokens() 快速查看成本")
    print("   - 对比不同实现方案的 Token 消耗")
    print("   - 优化提示词以降低成本")

    print("\n2. **生产运行**")
    print("   - 使用 @track_tokens(log_to_file=True) 记录详细日志")
    print("   - 定期分析日志，识别成本热点")
    print("   - 监控成本趋势，及时调整策略")

    print("\n3. **批量处理**")
    print("   - 在批处理函数上添加装饰器")
    print("   - 统计整个批次的总成本")
    print("   - 计算单项平均成本，优化处理流程")

    print("\n4. **成本预估**")
    print("   - 先用小样本测试，获取单位成本")
    print("   - 根据日志数据预估大规模处理成本")
    print("   - 制定成本预算和优化目标")

    print("\n📂 日志文件位置:")
    print("   logs/cost_reports/session_logs/token_usage_*.json")

    print("\n💡 查看完整文档:")
    print("   skills/SKILL_10g_项目成本统计.md")


if __name__ == "__main__":
    main()
