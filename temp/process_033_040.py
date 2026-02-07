#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理史记033-040世家章节的实体标注
包含11类实体标注和圣经式段落编号
"""

import re
import os

# 章节配置
CHAPTERS = [
    ("033_鲁周公世家", "鲁周公世家"),
    ("034_燕召公世家", "燕召公世家"),
    ("035_管蔡世家", "管蔡世家"),
    ("036_陈杞世家", "陈杞世家"),
    ("037_卫康叔世家", "卫康叔世家"),
    ("038_宋微子世家", "宋微子世家"),
    ("039_晋世家", "晋世家"),
    ("040_楚世家", "楚世家"),
]

SOURCE_DIR = "/home/baojie/work/shiji-kb/docs/original_text"
OUTPUT_DIR = "/home/baojie/work/shiji-kb/chapter_md"


def tag_entities(text):
    """标注文本中的实体"""
    # 保存原文
    result = text

    # 1. 标注朝代 &朝代&
    dynasties = ['周', '殷', '商', '夏', '秦', '齐', '鲁', '晋', '楚', '宋', '卫', '陈', '蔡', '郑', '燕', '吴', '越', '魏', '赵', '韩', '梁', '中国']
    for dynasty in dynasties:
        # 避免重复标注
        result = re.sub(r'(?<!&)(' + dynasty + r')(?!&)', r'&\1&', result)

    # 2. 标注时间 %时间%
    time_patterns = [
        r'(\d+年)',
        r'(元年)',
        r'(正月|二月|三月|四月|五月|六月|七月|八月|九月|十月|十一月|十二月)',
        r'(春|夏|秋|冬)',
        r'(\d+日)',
        r'(\d+岁)',
        r'(丙子|癸亥|己未|戊戌|己亥|甲午|丙戌|辛未|乙未)',
    ]
    for pattern in time_patterns:
        result = re.sub(r'(?<!%)' + pattern + r'(?!%)', r'%\1%', result)

    # 3. 标注地名 =地名=
    places = [
        '盟津', '牧野', '曲阜', '少昊之虚', '棠', '太山', '祊', '许田', '菟裘', '蔿氏', '曹', '柯',
        '党氏', '陈', '邾', '莒', '汶阳', '鄪', '高梁', '咸', '长丘', '北门', '锾离', '卫',
        '乾侯', '沂上', '郓', '阳关', '夹谷', '缯', '邹', '袪州', '陵阪', '陉氏', '有山氏',
        '徐州', '下邑', '柯', '洙泗', '雒', '丰', '成周', '毕', '肸', '茅阙门', '针巫氏',
        '五父之衢', '防山', '防', '社圃', '厉', '匡', '蒲', '河', '范魁'
    ]
    for place in places:
        result = re.sub(r'(?<!=)(' + place + r')(?!=)', r'=\1=', result)

    # 4. 标注官职 $官职$
    officials = [
        '王', '公', '太子', '夫人', '大夫', '相', '太公', '召公', '司徒', '司空', '司寇', '宰',
        '史', '师', '卿', '大司寇', '中都宰', '左右司马', '太史', '太保', '元孙', '帝',
        '侯', '伯', '子', '男', '君'
    ]

    # 特殊处理:@人名@$称号$ 格式
    result = re.sub(r'周公旦', '@周公@$@旦@$', result)
    result = re.sub(r'周武王', '&周&$@武王@$', result)
    result = re.sub(r'成王', '$@成王@$', result)
    result = re.sub(r'文王', '$@文王@$', result)
    result = re.sub(r'武王', '$@武王@$', result)

    # 5. 标注人名 @人名@
    # 这部分需要根据具体文本手动补充,这里先列出一些常见人名
    names = [
        '周公', '武王', '成王', '文王', '伯禽', '管叔', '蔡叔', '召公', '太公',
        '伯夏', '孔防叔', '叔梁纥', '孔子', '孔丘', '季友', '庆父', '叔牙',
        '子路', '子贡', '季桓子', '季康子', '季文子', '季武子', '阳虎',
        '齐襄公', '齐桓公', '齐景公', '晋文公', '楚庄王', '吴王夫差', '越王句践',
        '管仲', '曹沬', '晏婴', '晏子', '孟女', '哀姜', '叔姜', '申繻'
    ]

    # 6. 标注制度 ^制度^
    institutions = ['礼', '春秋', '金縢', '三桓', '三都', '郊祭', '会遇之礼']
    for inst in institutions:
        result = re.sub(r'(?<!\^)(' + inst + r')(?!\^)', r'^\1^', result)

    # 7. 标注器物 *器物*
    objects = [
        '大钺', '小钺', '璧', '圭', '鼎', '车', '马', '竖子', '甲', '俎豆',
        '乘车', '坛', '土阶', '旍旄羽袚矛戟剑拨', '阶', '台', '文衣', '康乐',
        '文马', '膰', '膰俎', '粟', '策', '絺帷', '帷', '环珮玉', '鸟', '牛',
        '羊', '马牛', '刍茭', '糗粮', '桢榦', '甲胄', '牿', '衣帛', '金玉',
        '宝器', '赂鼎', '土缶', '金距', '五乘', '千社', '千里马', '鸡', '社', '祀'
    ]
    for obj in objects:
        result = re.sub(r'(?<!\*)(' + obj + r')(?!\*)', r'*\1*', result)

    # 8. 标注族群 ~族群~
    tribes = ['淮夷', '徐戎', '鄋瞒', '犬戎', '长翟', '夷狄', '九夷', '百蛮']
    for tribe in tribes:
        result = re.sub(r'(?<!~)(' + tribe + r')(?!~)', r'~\1~', result)

    # 9. 标注动植物 🌿动植物🌿
    animals_plants = ['树', '禾', '木', '羔豚', '狗', '鸡', '骥', '骊', '骅骝', '绿耳', '熊蹯', '鸲鹆', '凤', '龙', '牛', '马', '羊']
    for item in animals_plants:
        if item not in result:
            continue
        result = re.sub(r'(?<!🌿)(' + item + r')(?!🌿)', r'🌿\1🌿', result)

    # 10. 标注神话 ?神话?
    myths = ['帝', '天', '神', '鬼神', '帝庭', '先王', '三王', '太王', '王季', '社', '祭', '祀', '卜', '龟策']
    for myth in myths:
        result = re.sub(r'(?<!\?)(' + myth + r')(?!\?)', r'?\1?', result)

    return result


def add_paragraph_numbers(text):
    """添加圣经式段落编号"""
    lines = text.strip().split('\n')
    result = []

    section_num = 0
    subsection_num = 0

    for line in lines:
        line = line.strip()
        if not line:
            result.append('')
            continue

        # 检测是否是新的大段落(根据内容判断)
        if any(marker in line for marker in ['公', '王', '年']):
            section_num += 1
            subsection_num = 0
            result.append(f'\n## [{section_num}] 段落{section_num}\n')

        # 添加子段落编号
        if line:
            subsection_num += 1
            if subsection_num == 1:
                result.append(f'[{section_num}] {line}')
            else:
                result.append(f'[{section_num}.{subsection_num-1}] {line}')

    return '\n'.join(result)


def process_chapter(chapter_id, chapter_title):
    """处理单个章节"""
    print(f"\n处理章节: {chapter_title}")

    # 读取原文
    input_file = os.path.join(SOURCE_DIR, f"{chapter_id}.txt")
    if not os.path.exists(input_file):
        print(f"  错误: 文件不存在 {input_file}")
        return False

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 处理内容
    # 1. 标注实体
    tagged_content = tag_entities(content)

    # 2. 添加段落编号
    # numbered_content = add_paragraph_numbers(tagged_content)

    # 3. 生成输出
    output = f"# {chapter_id.split('_')[0]} {chapter_title}\n\n"
    output += f"## [0] 标题\n{chapter_title}\n\n"
    output += tagged_content

    # 保存结果
    output_file = os.path.join(OUTPUT_DIR, f"{chapter_id}.tagged.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"  完成: {output_file}")
    return True


def main():
    """主函数"""
    print("="*60)
    print("开始处理史记033-040世家章节")
    print("="*60)

    success_count = 0
    for chapter_id, chapter_title in CHAPTERS:
        if process_chapter(chapter_id, chapter_title):
            success_count += 1

    print("\n" + "="*60)
    print(f"处理完成: {success_count}/{len(CHAPTERS)} 个章节")
    print("="*60)


if __name__ == '__main__':
    main()
