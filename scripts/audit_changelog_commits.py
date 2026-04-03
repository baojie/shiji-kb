#!/usr/bin/env python3
"""
CHANGELOG commit ID 完整性审查工具

功能：检查CHANGELOG.md中每个日期是否包含了所有对应的git commits
用法：python scripts/audit_changelog_commits.py
"""

import subprocess
import re
from datetime import datetime, timedelta

def get_changelog_commits(changelog_path):
    """从CHANGELOG中提取所有commit ID"""
    changelog_commits = set()
    with open(changelog_path, 'r') as f:
        content = f.read()
        # 匹配[XXXXXXX]格式的commit ID (7-8位短hash)
        matches = re.findall(r'\[([0-9a-f]{7,8})\]', content)
        changelog_commits = set(m[:7] for m in matches)
    return changelog_commits

def get_commits_for_date(date):
    """获取指定日期（07:00-次日07:00）的所有commits"""
    start_time = f"{date} 07:00"
    next_date = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    end_time = f"{next_date} 07:00"
    
    result = subprocess.run(
        ['git', 'log', '--oneline', f'--since={start_time}', f'--until={end_time}', '--format=%h'],
        capture_output=True, text=True
    )
    
    actual_commits = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
    # 过滤空字符串
    return {c for c in actual_commits if c}

def audit_changelog(changelog_path='CHANGELOG.md'):
    """审查CHANGELOG，返回缺失的commit ID"""
    # 检查的日期列表（按CHANGELOG中出现的日期）
    dates = [
        "2026-04-03", "2026-04-02", "2026-03-31", "2026-03-30", "2026-03-29",
        "2026-03-28", "2026-03-26", "2026-03-24", "2026-03-23", "2026-03-22",
        "2026-03-21", "2026-03-20", "2026-03-19", "2026-03-18", "2026-03-17",
        "2026-03-16", "2026-03-15", "2026-03-14", "2026-03-13", "2026-03-12",
        "2026-03-11", "2026-03-10", "2026-03-09", "2026-03-08", "2026-03-05",
        "2026-02-10", "2026-02-09", "2026-02-08", "2026-02-07", "2026-02-06"
    ]
    
    changelog_commits = get_changelog_commits(changelog_path)
    print(f"CHANGELOG中已包含的commit ID总数: {len(changelog_commits)}\n")
    
    missing_by_date = {}
    
    for date in dates:
        actual_commits = get_commits_for_date(date)
        missing = actual_commits - changelog_commits
        
        if missing:
            missing_by_date[date] = sorted(missing)
    
    # 输出结果
    if missing_by_date:
        print(f"⚠️  需要补充commit ID的日期数: {len(missing_by_date)}")
        print(f"⚠️  总计缺失commits数: {sum(len(v) for v in missing_by_date.values())}\n")
        
        for date, commits in sorted(missing_by_date.items(), reverse=True):
            print(f"## {date}: 缺少 {len(commits)} 个commits")
            print(f"   {', '.join(commits)}")
            print()
    else:
        print("✅ CHANGELOG完整，所有commits都已记录！")

if __name__ == '__main__':
    audit_changelog()
