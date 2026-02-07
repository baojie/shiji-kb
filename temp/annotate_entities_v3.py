#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
史记命名实体标注脚本 v3
改进版：修正岳的标注，避免嵌套标签
"""

import re

# 定义实体列表和对应的标注样式
ENTITIES = {
    # 人名 - 棕色+下划线
    'person': {
        'style': 'color: #8B4513; text-decoration: underline;',
        'names': [
            '黄帝', '少典', '轩辕', '蚩尤', '炎帝', '嫘祖', '玄嚣', '青阳', '昌意', '昌仆',
            '帝颛顼高阳', '帝颛顼', '颛顼', '穷蝉', '帝喾高辛', '帝喾', '高辛', '蟜极',
            '放勋', '帝挚', '帝尧', '羲仲', '羲叔', '和仲', '和叔', '放齐', '丹硃', '讙兜',
            '虞舜', '重华', '瞽叟', '桥牛', '句望', '敬康', '帝舜', '虞帝',
            '风后', '力牧', '常先', '大鸿', '八恺', '八元', '浑沌', '穷奇', '檮杌', '饕餮',
            '伯禹', '皋陶', '后稷', '伯夷', '硃虎', '熊罴', '三凶', '四凶族', '商均',
            '孔子', '宰予', '帝禹', '彭祖',
            # 单字人名
            '尧', '舜', '禹', '契', '弃', '垂', '益', '夔', '龙', '倕', '鲧', '挚', '羲', '和', '象', '高阳'
        ]
    },
    # 地名 - 深黄色+下划线
    'place': {
        'style': 'color: #B8860B; text-decoration: underline;',
        'names': [
            '阪泉之野', '涿鹿之野', '轩辕之丘', '涿鹿之阿', '南河之南', '苍梧之野', '江南九疑',
            '丸山', '岱宗', '空桐', '鸡头', '釜山', '桥山', '幽陵', '交阯', '流沙', '蟠木',
            '郁夷', '旸谷', '南交', '西土', '昧谷', '北方', '幽都', '妫汭', '文祖', '江淮',
            '荆州', '崇山', '三危', '羽山', '冀州', '历山', '雷泽', '河滨', '寿丘', '负夏',
            '大麓', '零陵', '涿鹿', '轩丘', '西陵', '江水', '若水',
            # 单字地名
            '海', '江', '熊', '湘'
        ]
    },
    # 官职 - 深红色
    'official': {
        'style': 'color: #8B0000;',
        'names': [
            '天子', '云师', '左右大监', '工师', '司空', '司徒', '朕虞', '秩宗', '典乐',
            '纳言', '大理', '十二牧', '四岳',
            # 单字官职
            '士', '虞', '稷', '岳'  # 添加"岳"作为官职
        ]
    },
    # 时间 - 青色
    'time': {
        'style': 'color: #008B8B;',
        'names': [
            '年二十', '年三十', '年五十', '年五十八', '年六十一', '正月上日', '岁二月',
            '五月', '八月', '十一月', '七十年', '二十八年', '三十九年', '二十年', '十七年',
            '九岁', '八年', '五岁', '三岁', '三年', '一年', '二年'
        ]
    },
    # 朝代/国号/氏族 - 紫色+高亮
    'dynasty': {
        'style': 'color: #9370DB; background-color: #F0E6FF;',
        'names': [
            '神农氏', '高阳氏', '高辛氏', '帝鸿氏', '少暤氏', '颛顼氏', '缙云氏', '蜀山氏',
            '陈锋氏', '娵訾氏', '有熊', '陶唐', '有虞', '夏后',
            # 单字国号
            '商', '周'
        ]
    },
    # 族群/部落 - 深灰绿色
    'tribe': {
        'style': 'color: #2F4F4F;',
        'names': [
            '荤粥', '北狄', '南蛮', '西戎', '东夷', '三苗', '析枝', '渠廋', '山戎', '息慎',
            '鸟夷', '北发',
            # 单字族群
            '戎', '氐', '羌', '发'
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

# 需要上下文匹配的单字实体
CONTEXT_SENSITIVE = {
    '尧': r'(?:帝|曰|於|而|以|之|与|自|为|让|知|使|乃|问|举|时|崩|老)',
    '舜': r'(?:帝|曰|於|而|以|之|与|自|为|让|虞|使|乃|入|居|耕|父|子|年|得|归|摄|践)',
    '禹': r'(?:帝|曰|於|而|以|之|与|自|为|伯|乃|荐|让)',
    '和': r'(?:羲|命|申命|律|神人以|慎)',
    '象': r'(?:载时以|弟|生|与|父母分|傲|曰|鄂|封)',
    '岳': r'(?:四|曰|应|彊)',  # 岳的上下文
    '发': r'(?:北|其|山戎)',
    '士': r'(?:作|其服也)',
    '商': r'(?:为|契为)',
    '周': r'(?:为|弃为)',
}

def annotate_text(text):
    """对文本进行实体标注"""
    # 收集所有实体
    all_entities = []
    for entity_type, entity_data in ENTITIES.items():
        style = entity_data['style']
        for name in entity_data['names']:
            all_entities.append((name, style, entity_type))

    # 按长度降序排序
    all_entities.sort(key=lambda x: len(x[0]), reverse=True)

    # 替换实体
    for name, style, entity_type in all_entities:
        # 检查是否需要上下文匹配
        if len(name) == 1 and name in CONTEXT_SENSITIVE:
            # 单字实体需要上下文
            context_pattern = CONTEXT_SENSITIVE[name]
            # 前后文匹配
            pattern = f'({context_pattern}){re.escape(name)}|{re.escape(name)}({context_pattern})'

            def replace_with_context(match):
                full_match = match.group(0)
                if match.group(1):  # 前文匹配
                    return f'{match.group(1)}<span style="{style}">{name}</span>'
                else:  # 后文匹配
                    return f'<span style="{style}">{name}</span>{match.group(2)}'

            text = re.sub(pattern, replace_with_context, text)
        else:
            # 多字实体或不需要上下文的单字实体
            pattern = re.escape(name)
            replacement = f'<span style="{style}">{name}</span>'
            # 避免重复标注
            text = re.sub(
                f'(?<!<span style=")(?<!">){pattern}(?!</span>)(?!">)',
                replacement,
                text
            )

    return text

def clean_nested_spans(text):
    """清理嵌套的span标签"""
    # 移除嵌套的span标签，保留外层
    while True:
        # 查找嵌套的span
        nested_pattern = r'(<span style="[^"]*">)([^<]*)<span style="[^"]*">([^<]*)</span>([^<]*)(</span>)'
        match = re.search(nested_pattern, text)
        if not match:
            break
        # 合并内容，保留外层span
        text = re.sub(nested_pattern, r'\1\2\3\4\5', text)

    return text

def process_file(input_file, output_file):
    """处理文件"""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 先移除旧的标注
    content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
    content = re.sub(r'<u>([^<]+)</u>', r'\1', content)
    content = re.sub(r'<mark>([^<]+)</mark>', r'\1', content)
    content = re.sub(r'<span style="[^"]*">([^<]+)</span>', r'\1', content)

    # 应用新的标注
    content = annotate_text(content)

    # 清理嵌套的span标签
    content = clean_nested_spans(content)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"标注完成！输出文件：{output_file}")

if __name__ == '__main__':
    input_file = '/home/baojie/work/shiji-kb/chapter_md/001_五帝本纪.md'
    output_file = '/home/baojie/work/shiji-kb/chapter_md/001_五帝本纪.md'
    process_file(input_file, output_file)
