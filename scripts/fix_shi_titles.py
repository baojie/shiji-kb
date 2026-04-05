#!/usr/bin/env python3
"""
修复秦始皇本纪的7篇刻石诗标题
"""

import json
from pathlib import Path

# 秦始皇本纪刻石诗的正确标题（按在文件中的出现顺序）
SHIKE_TITLES = [
    '泰山刻石',      # 第1篇: 刻所立石，其辞曰
    '琅邪刻石',      # 第2篇: 作琅邪台，立石刻
    '之罘刻石',      # 第3篇: 登之罘，刻石
    '之罘东观刻石',  # 第4篇: 其东观曰
    '碣石刻石',      # 第5篇: 之碣石，使燕人卢生求羡门、高誓
    '会稽刻石',      # 第6篇: 遂登会稽，宣省习俗
    '琅邪台刻石',    # 第7篇: 还，过吴，从江乘渡。并海上，北至琅邪
]

def main():
    project_root = Path(__file__).parent.parent
    json_file = project_root / "data/yunwen.json"

    # 读取JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 找到006章的诗歌并按顺序更新标题
    shi_index = 0
    updated_count = 0

    for item in data:
        if item['chapter_num'] == '006' and item['type'] == '诗歌':
            if shi_index < len(SHIKE_TITLES):
                old_title = item['title']
                new_title = SHIKE_TITLES[shi_index]
                print(f"诗歌 {shi_index + 1}: {old_title} → {new_title}")
                item['title'] = new_title
                shi_index += 1
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
