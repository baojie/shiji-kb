#!/usr/bin/env python3
"""
修复所有诗歌的标题
"""

import json
from pathlib import Path

# 诗歌标题映射
SHI_TITLES = {
    '007': ['垓下歌'],  # 项羽的诗
    '008': ['大风歌'],  # 刘邦的诗
    '009': ['赵王歌'],  # 赵王刘友的诗
    '024': ['天马歌（其一）', '天马歌（其二）'],  # 乐书的两首天马歌
}

def identify_shi_title(chapter_num, content, poem_index):
    """根据章节号、内容和诗歌索引识别标题"""
    if chapter_num not in SHI_TITLES:
        return None

    titles = SHI_TITLES[chapter_num]
    if poem_index < len(titles):
        return titles[poem_index]

    return None

def main():
    project_root = Path(__file__).parent.parent
    json_file = project_root / "data/yunwen.json"

    # 读取JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 按章节统计诗歌索引
    poem_counters = {}
    updated_count = 0

    for item in data:
        if item['type'] == '诗歌':
            chapter_num = item['chapter_num']
            old_title = item['title']

            # 获取当前章节的诗歌索引
            if chapter_num not in poem_counters:
                poem_counters[chapter_num] = 0

            poem_index = poem_counters[chapter_num]
            poem_counters[chapter_num] += 1

            # 尝试识别正确标题
            new_title = identify_shi_title(chapter_num, item['content'], poem_index)
            if new_title and new_title != old_title:
                print(f"章节 {chapter_num} 诗歌 {poem_index + 1}: {old_title} → {new_title}")
                item['title'] = new_title
                updated_count += 1

    # 保存更新后的JSON
    if updated_count > 0:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 已更新 {updated_count} 篇诗歌的标题")
    else:
        print("未发现需要更新的诗歌标题")

if __name__ == "__main__":
    main()
