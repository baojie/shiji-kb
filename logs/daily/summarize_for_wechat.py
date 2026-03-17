#!/usr/bin/env python3
"""
AI总结微信群通知
读取详细的日志markdown文件，用AI生成适合微信群发送的平实文本
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta


def read_daily_log(date_str):
    """读取指定日期的日志文件"""
    log_file = Path(__file__).parent / f"{date_str}.md"

    if not log_file.exists():
        print(f"❌ 日志文件不存在: {log_file}")
        print(f"请先运行: python generate_log.py {date_str}")
        return None

    return log_file.read_text(encoding='utf-8')


def create_prompt(date_str, log_content):
    """创建AI总结的prompt"""

    prompt = f"""你是一个技术工作总结助手。请根据下面的详细工作日志，生成一段适合微信群发送的简短总结。

要求：
1. 纯文本格式，无markdown语法，无列表编号
2. 用平实的中文，避免技术术语
3. 提取3-4条最核心的工作成果
4. 用顿号（、）连接多项内容
5. 总长度控制在150字以内
6. 格式：【史记知识库 日期】 + 核心内容 + 提交次数

示例输出：
【史记知识库 2026-03-15】

纪年系统重建，完善时间轴、实体反思方法论重构拆分为按章和按类型两个流程、完成001-002章标注修正。提交23次。

---

日期：{date_str}

工作日志内容：
{log_content}

---

请生成微信群通知："""

    return prompt


def generate_summary_with_claude(prompt):
    """调用Claude API生成总结

    注意：这个函数需要在支持Claude Code的环境中运行
    在这里我们只是打印prompt，让用户手动或通过其他方式调用AI
    """

    print("="*60)
    print("AI总结Prompt（请使用Claude Code或其他AI工具处理）")
    print("="*60)
    print(prompt)
    print("="*60)
    print()
    print("💡 提示：")
    print("1. 复制上面的prompt")
    print("2. 发送给Claude Code或其他AI助手")
    print("3. AI会生成适合微信群的总结")
    print()


def main():
    if len(sys.argv) < 2:
        # 默认使用昨天的日期
        date = datetime.now() - timedelta(days=1)
        date_str = date.strftime("%Y-%m-%d")
    else:
        date_str = sys.argv[1]

    print(f"为 {date_str} 生成微信群通知...\n")

    # 读取日志内容
    log_content = read_daily_log(date_str)
    if not log_content:
        return

    # 创建prompt
    prompt = create_prompt(date_str, log_content)

    # 显示prompt供AI处理
    generate_summary_with_claude(prompt)


if __name__ == "__main__":
    main()
