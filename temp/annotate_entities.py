#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
史记命名实体标注脚本
根据新的标注方案，对文本中的命名实体进行颜色标注
"""

import re

# 定义实体列表和对应的标注样式
ENTITIES = {
    # 人名 - 棕色+下划线
    'person': {
        'style': 'color: #8B4513; text-decoration: underline;',
        'names': [
            '黄帝', '少典', '轩辕', '蚩尤', '炎帝', '嫘祖', '玄嚣', '青阳', '昌意', '昌仆', '高阳',
            '帝颛顼', '颛顼', '穷蝉', '高辛', '蟜极', '帝喾', '放勋', '挚', '帝挚', '帝尧', '尧',
            '羲', '和', '羲仲', '羲叔', '和仲', '和叔', '放齐', '丹硃', '讙兜', '共工', '鲧',
            '虞舜', '舜', '重华', '瞽叟', '桥牛', '句望', '敬康', '象', '帝舜', '虞帝',
            '风后', '力牧', '常先', '大鸿', '八恺', '八元', '浑沌', '穷奇', '檮杌', '饕餮',
            '禹', '皋陶', '契', '后稷', '伯夷', '夔', '龙', '倕', '益', '彭祖', '伯禹', '弃',
            '垂', '硃虎', '熊罴', '三凶', '四凶族', '商均', '孔子', '宰予', '帝禹'
        ]
    },
    # 地名 - 深黄色+下划线
    'place': {
        'style': 'color: #B8860B; text-decoration: underline;',
        'names': [
            '阪泉之野', '涿鹿之野', '海', '丸山', '岱宗', '空桐', '鸡头', '江', '熊', '湘',
            '釜山', '涿鹿之阿', '轩辕之丘', '西陵', '江水', '若水', '桥山', '幽陵', '交阯',
            '流沙', '蟠木', '郁夷', '旸谷', '南交', '西土', '昧谷', '北方', '幽都', '妫汭',
            '文祖', '江淮', '荆州', '崇山', '三危', '羽山', '南河之南', '冀州', '历山',
            '雷泽', '河滨', '寿丘', '负夏', '大麓', '苍梧之野', '江南九疑', '零陵', '涿鹿',
            '轩丘'
        ]
    },
    # 官职 - 深红色
    'official': {
        'style': 'color: #8B0000;',
        'names': [
            '天子', '云师', '左右大监', '工师', '司空', '后稷', '司徒', '士', '共工', '朕虞',
            '秩宗', '典乐', '纳言', '大理', '工师', '虞', '稷', '十二牧'
        ]
    },
    # 时间 - 青色
    'time': {
        'style': 'color: #008B8B;',
        'names': [
            '年二十', '年三十', '年五十', '年五十八', '年六十一', '正月上日', '岁二月',
            '五月', '八月', '十一月', '三年', '二十年', '七十年', '二十八年', '三十九年',
            '十七年', '九岁', '八年', '五岁', '三岁', '一年', '二年'
        ]
    },
    # 朝代/国号/氏族 - 紫色+高亮
    'dynasty': {
        'style': 'color: #9370DB; background-color: #F0E6FF;',
        'names': [
            '神农氏', '高阳氏', '高辛氏', '帝鸿氏', '少暤氏', '颛顼氏', '缙云氏',
            '有熊', '高阳', '高辛', '陶唐', '有虞', '夏后', '商', '周', '蜀山氏',
            '陈锋氏', '娵訾氏'
        ]
    },
    # 族群/部落 - 深灰绿色
    'tribe': {
        'style': 'color: #2F4F4F;',
        'names': [
            '荤粥', '北狄', '南蛮', '西戎', '东夷', '三苗', '戎', '析枝', '渠廋', '氐', '羌',
            '山戎', '发', '息慎', '长', '鸟夷', '北发'
        ]
    },
    # 器物/礼器 - 秘鲁棕色
    'artifact': {
        'style': 'color: #CD853F;',
        'names': [
            '宝鼎', '璿玑玉衡', '五瑞', '五器'
        ]
    },
    # 制度/典章 - 钢青色
    'institution': {
        'style': 'color: #4682B4;',
        'names': [
            '五典', '五刑', '三礼', '五礼', '五教', '典刑', '流宥五刑', '官刑', '教刑', '赎刑'
        ]
    },
    # 天文/历法 - 深蓝紫色
    'astronomy': {
        'style': 'color: #483D8B;',
        'names': [
            '星鸟', '星火', '星虚', '星昴', '七政', '日中', '日永', '夜中', '日短',
            '中春', '中夏', '中秋', '中冬', '闰月'
        ]
    }
}

def annotate_text(text):
    """对文本进行实体标注"""
    # 按照实体长度从长到短排序，避免短实体覆盖长实体
    all_entities = []
    for entity_type, entity_data in ENTITIES.items():
        style = entity_data['style']
        for name in entity_data['names']:
            all_entities.append((name, style))

    # 按长度降序排序
    all_entities.sort(key=lambda x: len(x[0]), reverse=True)

    # 替换实体
    for name, style in all_entities:
        # 避免重复标注（如果已经被标注过就跳过）
        pattern = re.escape(name)
        # 只替换未被标注的实体
        replacement = f'<span style="{style}">{name}</span>'
        # 使用负向前瞻和负向后顾，确保不在已有的span标签内
        text = re.sub(
            f'(?<!<span style=")(?<!">){pattern}(?!</span>)(?!">)',
            replacement,
            text
        )

    return text

def process_file(input_file, output_file):
    """处理文件"""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 先移除旧的标注（**、<u>、<mark>、旧的span标签）
    # 移除加粗
    content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
    # 移除下划线
    content = re.sub(r'<u>([^<]+)</u>', r'\1', content)
    # 移除mark标签
    content = re.sub(r'<mark>([^<]+)</mark>', r'\1', content)
    # 移除旧的span标签（蓝色官职）
    content = re.sub(r'<span style="color: #0066cc;">([^<]+)</span>', r'\1', content)

    # 应用新的标注
    content = annotate_text(content)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"标注完成！输出文件：{output_file}")

if __name__ == '__main__':
    input_file = '/home/baojie/work/shiji-kb/chapter_md/001_五帝本纪.md'
    output_file = '/home/baojie/work/shiji-kb/chapter_md/001_五帝本纪.md'
    process_file(input_file, output_file)
