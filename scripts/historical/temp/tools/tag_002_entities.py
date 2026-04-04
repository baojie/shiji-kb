#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tag remaining entities in 002_夏本纪.tagged.md"""

import re
from pathlib import Path

# Define entity lists based on the document
PLACES = [
    '徐州', '扬州', '豫州', '梁州', '雍州',
    '海岱', '淮', '沂', '蒙', '羽', '大野', '东原', '峄', '泗',
    '淮海', '彭蠡', '三江', '震泽', '江海',
    '荆河', '伊', '雒', '瀍', '涧', '荥', '荷泽', '明都',
    '华阳', '黑水', '汶', '嶓', '蔡', '潜', '沔', '渭',
    '西河', '弱水', '泾', '漆', '沮', '沣', '荆', '岐', '终南', '敦物', '鸟鼠',
    '都野', '三危', '三苗', '积石', '龙门', '渭汭', '昆仑', '析支', '渠搜',
    '汧', '荆山', '雷首', '太岳', '砥柱', '析城', '王屋', '太行', '常山',
    '西倾', '硃圉', '太华', '熊耳', '外方', '桐柏', '负尾', '嶓冢',
    '内方', '大别', '汶山', '衡山', '九江', '敷浅原',
    '合黎', '流沙', '南海', '华阴', '盟津', '雒汭', '大邳', '降水', '逆河',
    '苍浪', '三澨', '北江', '醴', '东陵', '汇', '中江', '梅',
    '沇水', '陶丘', '荷', '鸟鼠同穴', '涂山', '阳城', '箕山', '甘',
    '洛汭', '夏台', '鸣条', '会稽', '江南', '杞'
]

TRIBES = [
    '淮夷', '岛夷', '西戎', '和夷', '夷', '蛮', '蔡'
]

PERSONS = [
    '商均', '启', '太康', '中康', '相', '少康', '予', '槐', '芒', '泄',
    '不降', '扃', '廑', '孔甲', '刘累', '皋', '发', '履癸', '桀', '汤',
    '丹硃', '夔', '羲', '羿', '浞'
    # 注意：'和' 字太常见（如"律和声"、"神人以和"），不应自动标注
    # 需要手动标注 "羲、和" 这样的特定上下文
]

DYNASTIES = [
    '涂山氏', '有扈氏', '陶唐', '豢龙氏', '御龙氏', '豕韦',
    '夏后氏', '有男氏', '斟寻氏', '彤城氏', '襃氏', '费氏', '杞氏',
    '缯氏', '辛氏', '冥氏', '斟戈氏', '姒氏', '商', '周'
]

INSTITUTIONS = [
    '五服', '甸服', '侯服', '绥服', '要服', '荒服',
    '五刑', '六府', '三壤', '五行', '三正', '九德', '六律', '五声', '八音'
]

OFFICIALS = [
    '士', '六卿', '六事', '四辅臣'
]

TIME = [
    '元年', '十七年', '十年', '三年'
]

ARTIFACTS = [
    '玄圭', '甘誓', '五子之歌', '胤征', '夏小正'
]

def tag_entities(content):
    """Apply semantic tags to entities"""

    # Sort by length (longest first) to avoid partial matches
    all_entities = [
        (PLACES, '=', '='),
        (TRIBES, '~', '~'),
        (PERSONS, '@', '@'),
        (DYNASTIES, '&', '&'),
        (INSTITUTIONS, '^', '^'),
        (OFFICIALS, '$', '$'),
        (TIME, '%', '%'),
        (ARTIFACTS, '*', '*'),
    ]

    for entities, start_token, end_token in all_entities:
        # Sort by length descending
        sorted_entities = sorted(entities, key=len, reverse=True)

        for entity in sorted_entities:
            # Skip if already tagged
            if f'{start_token}{entity}{end_token}' in content:
                continue

            # Create pattern that matches entity not already surrounded by tag tokens
            # and not in the middle of other Chinese characters
            pattern = rf'(?<![{re.escape("@=$%&^~*!?")}])(?<![\u4e00-\u9fff])({re.escape(entity)})(?![\u4e00-\u9fff])(?![{re.escape("@=$%&^~*!?")}])'

            replacement = f'{start_token}\\1{end_token}'
            content = re.sub(pattern, replacement, content)

    return content

def main():
    file_path = Path('chapter_md/002_夏本纪.tagged.md')

    if not file_path.exists():
        print(f'File not found: {file_path}')
        return

    content = file_path.read_text(encoding='utf-8')

    # Apply tags
    tagged_content = tag_entities(content)

    # Write back
    file_path.write_text(tagged_content, encoding='utf-8')

    print(f'Successfully tagged entities in {file_path}')

if __name__ == '__main__':
    main()
