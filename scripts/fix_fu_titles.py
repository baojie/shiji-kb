#!/usr/bin/env python3
"""
修复赋的标题：将通用标题"章节名+赋"改为具体的赋名
"""

import json
from pathlib import Path

# 赋的正确标题映射（按章节和内容特征）
FU_TITLES = {
    '084': {
        # 屈原贾生列传的3篇赋
        '怀沙': '怀沙赋',
        '吊屈原': '吊屈原赋',
        '鵩鸟': '鵩鸟赋',
    },
    '117': {
        # 司马相如列传的2篇赋
        '子虚': '上林赋',  # 实际包含子虚赋和上林赋，以上林赋为主标题
        '大人': '大人赋',
    }
}

def identify_fu_title(chapter_num, content):
    """根据章节号和内容特征识别赋的标题"""
    if chapter_num not in FU_TITLES:
        return None

    # 根据内容关键词匹配
    if chapter_num == '084':
        if '怀沙' in content or '陶陶' in content and '孟夏' in content:
            return '怀沙赋'
        elif '吊屈原' in content or '共承嘉惠' in content or '侧闻屈' in content:
            return '吊屈原赋'
        elif '鸮' in content or '庚子' in content or '楚人命鸮' in content:
            return '鵩鸟赋'

    elif chapter_num == '117':
        # 优先检查大人赋（因为上林赋内容中也可能出现"大人"一词）
        if '大人赋' in content or '尝为大人赋' in content or '世有大人兮' in content:
            return '大人赋'
        elif '子虚' in content or '楚使子虚' in content:
            return '上林赋'

    return None

def main():
    project_root = Path(__file__).parent.parent
    json_file = project_root / "data/yunwen.json"

    # 读取JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 更新赋的标题
    updated_count = 0
    for item in data:
        if item['type'] == '赋':
            chapter_num = item['chapter_num']
            old_title = item['title']
            content = item['content']

            # 尝试识别正确标题
            new_title = identify_fu_title(chapter_num, content)
            if new_title and new_title != old_title:
                print(f"章节 {chapter_num}: {old_title} → {new_title}")
                item['title'] = new_title
                updated_count += 1

    # 保存更新后的JSON
    if updated_count > 0:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 已更新 {updated_count} 篇赋的标题")
    else:
        print("未发现需要更新的赋标题")

if __name__ == "__main__":
    main()
