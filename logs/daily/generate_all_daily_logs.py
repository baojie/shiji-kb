#!/usr/bin/env python3
"""
批量生成所有历史日期的工作日志
为所有有git提交的日期生成工作日志和微信群通知
"""

import subprocess
from datetime import datetime
from pathlib import Path
import sys

# 添加当前目录到path，以便导入generate_daily_log
sys.path.insert(0, str(Path(__file__).parent))

from generate_daily_log import get_git_commits, generate_log_content


def get_all_commit_dates():
    """获取所有有提交记录的日期"""
    cmd = ["git", "log", "--all", "--date=short", "--pretty=format:%ad"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    dates = set()
    for line in result.stdout.strip().split('\n'):
        if line:
            dates.add(line)

    return sorted(dates)


def generate_wechat_summary(date_str, commits):
    """为日志生成微信群通知摘要（列表格式）"""
    from collections import defaultdict
    from generate_daily_log import categorize_changes, get_changed_files

    categories = categorize_changes(commits)
    stats_total = len(commits)

    # 提取关键数字
    import re
    key_numbers = []
    for commit in commits:
        numbers = re.findall(r'(\d+[,\d]*)\s*处', commit['subject'] + commit['body'])
        numbers += re.findall(r'(\d+[,\d]*)\s*章', commit['subject'] + commit['body'])
        numbers += re.findall(r'(\d+[,\d]*)\s*个', commit['subject'] + commit['body'])
        key_numbers.extend(numbers)

    # 收集核心工作项
    highlights = []

    # 按优先级提取
    priority_cats = ['新功能', '实体反思', '反思规则更新', 'Bug修复', '可视化', '工具脚本', '文档', '其他']

    for cat in priority_cats:
        if cat in categories and categories[cat]:
            for commit in categories[cat][:3]:  # 每个类别最多3条
                subject = commit['subject']

                # 简化技术术语
                subject = subject.replace('v2.8格式统一：', '').replace('v2.7', '').replace('v2.6', '')
                subject = subject.replace('v2.5', '').replace('v2.4', '').replace('v2.3', '')
                subject = subject.replace('v2.2', '').replace('v2.1', '').replace('v2.0', '')
                subject = subject.replace('v3.0', '').replace('v3.1', '')
                subject = subject.replace('README/', '').replace('SKILL/', '')
                subject = subject.replace('fix:', '修复').replace('add:', '新增')
                subject = subject.replace('update:', '更新').replace('doc:', '')

                # 去掉首尾空白
                subject = subject.strip()

                if subject and len(highlights) < 8:  # 最多8条工作内容
                    highlights.append(subject)

    # 生成微信通知内容
    msg_lines = [f"【史记知识库 {date_str}】", ""]

    for item in highlights[:7]:  # 最多7条工作 + 1条提交次数
        msg_lines.append(f"· {item}")

    msg_lines.append(f"· 提交{stats_total}次代码")

    return "\n".join(msg_lines)


def update_log_with_wechat(log_file, date_str, commits):
    """在日志文件最前面插入微信群通知"""
    content = log_file.read_text(encoding='utf-8')

    # 检查是否已有微信通知
    if '## 微信群通知' in content:
        print(f"  ⏭️  {date_str} 已有微信通知，跳过")
        return False

    # 生成微信通知
    wechat_msg = generate_wechat_summary(date_str, commits)

    # 在标题后插入
    lines = content.split('\n')
    title_line = lines[0]
    rest_content = '\n'.join(lines[1:])

    new_content = f"""{title_line}

## 微信群通知

```
{wechat_msg}
```

---
{rest_content}"""

    log_file.write_text(new_content, encoding='utf-8')
    print(f"  ✅ {date_str} 微信通知已添加")
    return True


def main():
    print("正在扫描所有有提交记录的日期...\n")

    dates = get_all_commit_dates()
    print(f"找到 {len(dates)} 个有提交的日期\n")

    log_dir = Path(__file__).parent.parent / "logs" / "daily"
    log_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        'total': 0,
        'generated': 0,
        'updated': 0,
        'skipped': 0
    }

    for date_str in dates:
        stats['total'] += 1
        print(f"[{stats['total']}/{len(dates)}] 处理 {date_str}...")

        # 获取提交记录
        commits = get_git_commits(date_str)

        if not commits:
            print(f"  ⚠️  没有提交记录，跳过")
            stats['skipped'] += 1
            continue

        log_file = log_dir / f"{date_str}.md"

        # 如果日志文件不存在，生成它
        if not log_file.exists():
            content = generate_log_content(date_str, commits)
            log_file.write_text(content, encoding='utf-8')
            print(f"  ✅ 日志已生成")
            stats['generated'] += 1

        # 添加或更新微信通知
        if update_log_with_wechat(log_file, date_str, commits):
            stats['updated'] += 1

    print("\n" + "="*60)
    print("批量生成完成！")
    print("="*60)
    print(f"总计处理: {stats['total']} 个日期")
    print(f"新生成日志: {stats['generated']} 个")
    print(f"添加微信通知: {stats['updated']} 个")
    print(f"跳过: {stats['skipped']} 个")
    print("="*60)


if __name__ == "__main__":
    main()
