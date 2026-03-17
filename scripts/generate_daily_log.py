#!/usr/bin/env python3
"""
每日工作日志生成器
根据git提交记录自动生成每日工作摘要

重要说明：
---------
工作日的划分以早上7:00为界，而非传统的午夜0:00。
这样设计是因为：
1. 凌晨0-7点的工作通常属于前一天的延续
2. 更符合实际工作习惯和作息规律
3. 方便次日早上7点后统计前一天的完整工作

时间范围：
- YYYY-MM-DD.md 对应的时间范围是：
  (YYYY-MM-DD-1) 07:00:00 至 (YYYY-MM-DD) 07:00:00

示例：
- 2026-03-17.md 包含：2026-03-16 07:00 ~ 2026-03-17 07:00 的提交
- 如果你在 2026-03-17 凌晨2点提交，会计入 2026-03-17.md
- 如果你在 2026-03-17 早上8点提交，会计入 2026-03-18.md
"""

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


def get_git_commits(date_str):
    """获取指定日期的git提交记录

    注意：工作日的划分以早上7:00为界
    - 某日的工作日志包含：前一天 07:00 到 当天 07:00 的提交
    - 例如：2026-03-17.md 包含 2026-03-16 07:00 ~ 2026-03-17 07:00 的提交
    """
    # 获取当天的开始和结束时间（以早上7点为界）
    date = datetime.strptime(date_str, "%Y-%m-%d")
    start = (date - timedelta(days=1)).strftime("%Y-%m-%d 07:00:00")
    end = date.strftime("%Y-%m-%d 07:00:00")

    cmd = [
        "git", "log",
        f"--since={start}",
        f"--until={end}",
        "--pretty=format:%H|||%ai|||%s|||%b",
        "--no-merges"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    commits = []

    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('|||')
        if len(parts) >= 3:
            commits.append({
                'hash': parts[0],
                'time': parts[1],
                'subject': parts[2],
                'body': parts[3] if len(parts) > 3 else ''
            })

    return commits


def get_changed_files(commit_hash):
    """获取某次提交改动的文件"""
    cmd = ["git", "show", "--name-only", "--pretty=format:", commit_hash]
    result = subprocess.run(cmd, capture_output=True, text=True)
    files = [f for f in result.stdout.strip().split('\n') if f]
    return files


def categorize_changes(commits):
    """将提交按类型分类"""
    categories = defaultdict(list)

    for commit in commits:
        subject = commit['subject']
        files = get_changed_files(commit['hash'])

        # 根据提交信息和文件路径分类
        if 'skill' in subject.lower() or any('skills/' in f for f in files):
            categories['反思规则更新'].append(commit)
        elif '反思' in subject or 'reflection' in subject.lower():
            categories['实体反思'].append(commit)
        elif 'html' in subject.lower() or any('.html' in f for f in files):
            categories['可视化'].append(commit)
        elif '文档' in subject or any('doc/' in f for f in files):
            categories['文档'].append(commit)
        elif '修复' in subject or 'fix' in subject.lower() or 'bug' in subject.lower():
            categories['Bug修复'].append(commit)
        elif '新增' in subject or 'add' in subject.lower() or 'new' in subject.lower():
            categories['新功能'].append(commit)
        elif 'script' in subject.lower() or any('scripts/' in f for f in files):
            categories['工具脚本'].append(commit)
        else:
            categories['其他'].append(commit)

    return categories


def extract_stats(commits):
    """提取统计数据"""
    stats = {
        'total_commits': len(commits),
        'files_changed': set(),
        'key_numbers': []
    }

    for commit in commits:
        files = get_changed_files(commit['hash'])
        stats['files_changed'].update(files)

        # 提取数字统计
        import re
        numbers = re.findall(r'(\d+)处', commit['subject'] + commit['body'])
        numbers.extend(re.findall(r'(\d+)章', commit['subject'] + commit['body']))
        numbers.extend(re.findall(r'(\d+)个', commit['subject'] + commit['body']))
        stats['key_numbers'].extend(numbers)

    return stats


def generate_log_content(date_str, commits):
    """生成日志内容"""
    categories = categorize_changes(commits)
    stats = extract_stats(commits)

    content = f"# 工作日志 {date_str}\n\n"

    # 核心功能变化
    content += "## 核心功能变化\n\n"

    priority_categories = ['新功能', '实体反思', '反思规则更新', 'Bug修复']
    for cat in priority_categories:
        if cat in categories and categories[cat]:
            content += f"### {cat}\n\n"
            for commit in categories[cat]:
                content += f"- {commit['subject']}\n"
                if commit['body'].strip():
                    for line in commit['body'].strip().split('\n'):
                        if line.strip():
                            content += f"  - {line.strip()}\n"
            content += "\n"

    # 技术细节
    content += "## 技术细节\n\n"
    content += f"- 提交次数: {stats['total_commits']}\n"
    content += f"- 涉及文件: {len(stats['files_changed'])}个\n"

    other_categories = [cat for cat in categories if cat not in priority_categories]
    for cat in other_categories:
        if categories[cat]:
            content += f"\n### {cat}\n\n"
            for commit in categories[cat]:
                content += f"- {commit['subject']}\n"

    content += "\n## 下一步计划\n\n"
    content += "（待填写）\n"

    return content


def generate_wechat_message(date_str, commits):
    """生成微信群通知格式（平实语言，适合微信群）"""
    categories = categorize_changes(commits)

    # 提取核心工作内容（用平实语言）
    highlights = []

    # 优先显示重要工作
    priority_cats = ['新功能', '实体反思', '反思规则更新', 'Bug修复']
    for cat in priority_cats:
        if cat in categories and categories[cat]:
            for commit in categories[cat]:
                # 去掉技术细节，保留核心信息
                subject = commit['subject']
                # 简化一些常见的技术术语
                subject = subject.replace('v2.8格式统一：', '')
                subject = subject.replace('v2.7', '')
                subject = subject.replace('v2.4', '')
                subject = subject.replace('README/', '')
                highlights.append(subject)

    # 生成平实的文本消息（无编号，无层级）
    msg = f"【史记知识库 {date_str}】\n\n"

    if highlights:
        # 只取前3条最重要的，用平实语言连接
        msg += "、".join(highlights[:3])
        msg += f"。提交{len(commits)}次。"
    else:
        msg += f"代码维护和优化。提交{len(commits)}次。"

    return msg


def main():
    if len(sys.argv) < 2:
        # 默认使用昨天的日期
        date = datetime.now() - timedelta(days=1)
        date_str = date.strftime("%Y-%m-%d")
    else:
        date_str = sys.argv[1]

    print(f"生成 {date_str} 的工作日志...")

    commits = get_git_commits(date_str)

    if not commits:
        print(f"⚠️  {date_str} 没有git提交记录")
        return

    # 生成日志文件
    log_dir = Path(__file__).parent.parent / "logs" / "daily"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{date_str}.md"
    content = generate_log_content(date_str, commits)

    log_file.write_text(content, encoding='utf-8')
    print(f"✅ 日志已生成: {log_file}")

    # 生成微信消息
    wechat_msg = generate_wechat_message(date_str, commits)
    print("\n" + "="*50)
    print("微信群通知格式：")
    print("="*50)
    print(wechat_msg)
    print("="*50)


if __name__ == "__main__":
    main()
