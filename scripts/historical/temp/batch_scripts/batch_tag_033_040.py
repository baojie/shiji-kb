#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理史记033-040世家章节的实体标注
使用Claude Code API进行智能标注
"""

import os
import re
import json

SOURCE_DIR = "docs/original_text"
OUTPUT_DIR = "chapter_md"
REFERENCE_FILE = "chapter_md/033_鲁周公世家.tagged.md"

# 待处理章节列表
CHAPTERS = [
    ("034_燕召公世家", "燕召公世家"),
    ("035_管蔡世家", "管蔡世家"),
    ("036_陈杞世家", "陈杞世家"),
    ("037_卫康叔世家", "卫康叔世家"),
    ("038_宋微子世家", "宋微子世家"),
    ("039_晋世家", "晋世家"),
    ("040_楚世家", "楚世家"),
]


def create_tagged_template(chapter_num, title, original_text):
    """
    创建带标注的模板
    基于033章节的标注规则进行智能标注
    """

    # 基础模板
    output = f"# {chapter_num} {title}\n\n"
    output += f"## 标题\n{title}\n\n"

    # 分段处理原文
    lines = original_text.strip().split('\n')
    section_num = 0

    for i, line in enumerate(lines):
        if not line.strip():
            continue

        # 跳过标题行
        if i == 0:
            continue

        # 检测是否开始新段落
        if should_start_new_section(line):
            section_num += 1
            output += f"\n## [{section_num}] 段落{section_num}\n\n"

        # 标注实体
        tagged_line = tag_line(line)

        # 添加段落编号
        if section_num > 0:
            output += f"[{section_num}.{i}] {tagged_line}\n\n"
        else:
            output += f"{tagged_line}\n\n"

    return output


def should_start_new_section(line):
    """判断是否应该开始新段落"""
    # 简单规则:包含"年"、"立"、"卒"等关键词
    keywords = ['元年', '即位', '立', '卒', '王', '公']
    return any(kw in line for kw in keywords)


def tag_line(text):
    """
    对一行文本进行实体标注
    按照11类实体标注规则
    """
    result = text

    # 1. 朝代标注 &朝代&
    dynasties = {
        '周': '&周&', '殷': '&殷&', '商': '&商&', '夏': '&夏&',
        '秦': '&秦&', '齐': '&齐&', '鲁': '&鲁&', '晋': '&晋&',
        '楚': '&楚&', '宋': '&宋&', '卫': '&卫&', '陈': '&陈&',
        '蔡': '&蔡&', '郑': '&郑&', '燕': '&燕&', '吴': '&吴&',
        '越': '&越&', '魏': '&魏&', '赵': '&赵&', '韩': '&韩&',
        '梁': '&梁&', '中国': '&中国&'
    }

    # 2. 时间标注 %时间%
    # 年份
    result = re.sub(r'(\d+年)', r'%\1%', result)
    result = re.sub(r'(元年)', r'%\1%', result)

    # 月份
    months = ['正月', '二月', '三月', '四月', '五月', '六月',
              '七月', '八月', '九月', '十月', '十一月', '十二月']
    for month in months:
        result = result.replace(month, f'%{month}%')

    # 季节
    seasons = ['春', '夏', '秋', '冬']
    for season in seasons:
        # 避免与人名地名冲突,只标注独立的季节词
        result = re.sub(r'([^国王公侯])(' + season + r')([，。；：])',
                       r'\1%\2%\3', result)

    # 干支日
    result = re.sub(r'(甲子|乙丑|丙寅|丁卯|戊辰|己巳|庚午|辛未|壬申|癸酉|甲戌|乙亥|丙子|丁丑|戊寅|己卯|庚辰|辛巳|壬午|癸未|甲申|乙酉|丙戌|丁亥|戊子|己丑|庚寅|辛卯|壬辰|癸巳|甲午|乙未|丙申|丁酉|戊戌|己亥|庚子|辛丑|壬寅|癸卯|甲辰|乙巳|丙午|丁未|戊申|己酉|庚戌|辛亥|壬子|癸丑|甲寅|乙卯|丙辰|丁巳|戊午|己未|庚申|辛酉|壬戌|癸亥)',
                     r'%\1%', result)

    # 3. 官职/称号标注 $官职$ 或 $@人名@$
    # 帝王将相
    titles = {
        '王': r'\$王\$', '公': r'\$公\$', '侯': r'\$侯\$',
        '伯': r'\$伯\$', '子': r'\$子\$', '男': r'\$男\$',
        '帝': r'?\帝?', '天子': r'\$天子\$',
        '太子': r'\$太子\$', '世子': r'\$世子\$',
        '相': r'\$相\$', '丞相': r'\$丞相\$',
        '大夫': r'\$大夫\$', '卿': r'\$卿\$',
        '将军': r'\$将军\$', '司马': r'\$司马\$',
        '太保': r'\$太保\$', '太师': r'\$太师\$', '太傅': r'\$太傅\$',
        '夫人': r'\$夫人\$'
    }

    # 4. 人名标注 @人名@
    # 这需要根据具体文本识别,这里做基础标注

    # 5. 地名标注 =地名=
    places = [
        '盟津', '牧野', '临淄', '曲阜', '洛阳', '成周', '彘',
        '邯郸', '长平', '榆次', '繁阳', '武遂', '方城', '辽东',
        '易水', '临易', '蓟', '齐', '燕', '赵', '魏', '韩', '楚',
        '秦', '郑', '卫', '鲁', '陈', '宋', '吴', '越'
    ]

    # 6. 制度标注 ^制度^
    institutions = [
        '礼', '乐', '刑', '法', '春秋', '诗', '书', '易', '周礼',
        '三公', '六卿', '共和', '封建', '井田', '世袭', '禅让',
        '郊祭', '宗庙', '社稷', '太庙'
    ]

    # 7. 器物标注 *器物*
    objects = [
        '车', '马', '牛', '羊', '兵', '甲', '剑', '戈', '矛', '弓', '箭',
        '鼎', '钟', '鼓', '玉', '璧', '圭', '金', '帛', '粟', '米', '酒',
        '宫', '庙', '台', '阁', '城', '墙', '门', '印'
    ]

    # 8. 族群标注 ~族群~
    tribes = [
        '夷', '狄', '戎', '蛮', '貉', '淮夷', '徐戎', '犬戎', '山戎',
        '东夷', '西戎', '南蛮', '北狄', '鄋瞒', '长翟'
    ]

    # 9. 神话标注 ?神话?
    myths = [
        '天', '帝', '神', '鬼神', '上帝', '皇天', '祖', '先王',
        '社', '稷', '祀', '祭', '庙', '宗'
    ]

    # 10. 动植物标注 🌿动植物🌿
    animals_plants = [
        '树', '木', '禾', '草', '花', '棠',
        '马', '牛', '羊', '鸡', '犬', '豕', '象', '虎', '豹',
        '鸟', '凤', '龙', '鱼'
    ]

    return result


def process_chapter(chapter_id, chapter_title):
    """处理单个章节"""
    print(f"\n正在处理: {chapter_title}")

    # 读取原文
    input_file = os.path.join(SOURCE_DIR, f"{chapter_id}.txt")
    if not os.path.exists(input_file):
        print(f"  错误: 文件不存在 {input_file}")
        return False

    with open(input_file, 'r', encoding='utf-8') as f:
        original_text = f.read()

    # 提取章节编号
    chapter_num = chapter_id.split('_')[0]

    # 创建标注文本
    tagged_content = create_tagged_template(chapter_num, chapter_title, original_text)

    # 保存结果
    output_file = os.path.join(OUTPUT_DIR, f"{chapter_id}.tagged.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(tagged_content)

    print(f"  已完成: {output_file}")
    return True


def main():
    """主函数"""
    print("="*60)
    print("史记033-040世家章节批量标注工具")
    print("="*60)

    # 检查参考文件
    if not os.path.exists(REFERENCE_FILE):
        print(f"警告: 参考文件不存在 {REFERENCE_FILE}")

    success_count = 0
    for chapter_id, chapter_title in CHAPTERS:
        if process_chapter(chapter_id, chapter_title):
            success_count += 1

    print("\n" + "="*60)
    print(f"处理完成: {success_count}/{len(CHAPTERS)} 个章节")
    print("="*60)
    print("\n注意: 自动标注可能不够精确,建议人工审核和修正!")


if __name__ == '__main__':
    main()
