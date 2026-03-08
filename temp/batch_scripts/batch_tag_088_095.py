#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量标注史记088-095章节的实体标注脚本
"""

import re
import os

# 实体标注规则
def tag_entities(text):
    """对文本进行实体标注"""

    # 人名列表 (常见人名)
    person_names = [
        '蒙恬', '蒙毅', '扶苏', '始皇', '张耳', '陈馀', '魏豹', '彭越', '黥布',
        '韩信', '淮阴侯', '卢绾', '田儋', '田荣', '田横', '樊哙', '郦商', '滕公',
        '灌婴', '高祖', '项羽', '项梁', '刘邦', '吕后', '沛公', '汉王', '章邯',
        '王离', '李由', '司马欣', '董翳', '赵高', '子婴', '陈胜', '吴广', '
武臣',
        '李良', '田安', '田假', '周市', '周文', '召平', '周苛', '雍齿', '申阳',
        '张同', '贲赫', '栾布', '钟离眛', '蒯通', '郦食其', '陆贾', '随何',
        '武王', '成王', '周公', '太公', '孔子', '荀子', '墨子', '管仲', '晏婴'
    ]

    # 地名列表
    place_names = [
        '咸阳', '上郡', '九原', '云阳', '阳周', '绛', '邯郸', '巨鹿', '陈', '砀',
        '彭城', '荥阳', '成皋', '广武', '鸿门', '霸上', '武关', '函谷关', '关中',
        '巴蜀', '汉中', '南阳', '颍川', '三川', '东郡', '砀郡', '薛', '栎阳',
        '废丘', '临晋', '高奴', '翟', '代', '赵', '燕', '齐', '楚', '魏', '韩',
        '秦', '汉', '陇西', '北地', '辽东', '河东', '河内', '河南', '关东',
        '山东', '江南', '淮南', '淮阴', '下邳', '沛', '丰', '曲逆', '历下',
        '即墨', '临淄', '胶东', '济北', '博阳', '昌邑', '舞阳', '汝阴', '颍阳'
    ]

    # 官职列表
    official_titles = [
        '丞相', '太尉', '御史大夫', '将军', '上将军', '大将军', '列侯', '诸侯王',
        '太子', '皇帝', '天子', '王', '侯', '公', '卿', '大夫', '郎中', '中尉',
        '廷尉', '典客', '宗正', '太仆', '郡守', '县令', '县尉', '亭长', '里正',
        '御史', '博士', '郎', '舍人', '中大夫', '太中大夫', '谒者', '郎中令',
        '卫尉', '少府', '执戟', '郎中骑', '中涓', '骑将', '车骑将军', '骠骑将军',
        '都尉', '校尉', '司马', '候', '长史', '司空', '丞', '令', '尹'
    ]

    # 朝代列表
    dynasties = ['夏', '商', '周', '秦', '汉', '楚', '齐', '燕', '赵', '魏', '韩', '宋', '卫', '郑', '陈', '蔡', '吴', '越', '晋', '鲁']

    # 时间表达
    time_patterns = [
        r'(\d+年)', r'(元年)', r'(\d+月)', r'(春|夏|秋|冬)', r'(正月|二月|三月|四月|五月|六月|七月|八月|九月|十月|十一月|十二月)',
        r'(\d+日)', r'(甲子|乙丑|丙寅|丁卯|戊辰|己巳|庚午|辛未|壬申|癸酉|甲戌|乙亥)',
        r'(朔|望|晦)', r'(\d+岁)', r'(\d+世)'
    ]

    # 制度词汇
    institutions = [
        '封建', '郡县', '分封', '井田', '礼乐', '刑法', '律令', '法令', '诏令',
        '科举', '察举', '征辟', '宗法', '嫡长子', '宗庙', '社稷', '朝贡', '封禅',
        '巡狩', '田猎', '阡陌', '度量衡', '什伍', '连坐', '军功', '爵位', '俸禄',
        '赋税', '徭役', '戍边', '屯田', '盟约', '和亲'
    ]

    # 标注人名
    for name in person_names:
        if len(name) >= 2:
            text = re.sub(f'({name})', r'@\1@', text)

    # 标注地名
    for place in place_names:
        if len(place) >= 2:
            # 避免重复标注
            text = re.sub(f'(?<![=@$%&^~*!?🌿])({place})(?![=@$%&^~*!?🌿])', r'=\1=', text)

    # 标注朝代
    for dynasty in dynasties:
        text = re.sub(f'(?<![=@$%&^~*!?🌿])({dynasty})(?![=@$%&^~*!?🌿国])', r'&\1&', text)

    # 标注官职
    for title in official_titles:
        if len(title) >= 2:
            text = re.sub(f'(?<![=@$%&^~*!?🌿])({title})(?![=@$%&^~*!?🌿])', r'$\1$', text)

    # 标注制度
    for inst in institutions:
        if len(inst) >= 2:
            text = re.sub(f'(?<![=@$%&^~*!?🌿])({inst})(?![=@$%&^~*!?🌿])', r'^\1^', text)

    # 标注时间
    for pattern in time_patterns:
        text = re.sub(pattern, r'%\1%', text)

    # 标注器物
    artifacts = ['剑', '戟', '矛', '弓', '弩', '箭', '车', '马', '船', '舟', '鼎', '钟', '璧', '玉', '金', '银', '铜', '铁', '丝', '帛', '锦', '绣', '冠', '衣', '印', '玺', '符', '节', '旗', '鼓']
    for artifact in artifacts:
        text = re.sub(f'(?<![=@$%&^~*!?🌿🐎🐕🐑🐄🐴🐅🐰🦌🐭])({artifact})(?![=@$%&^~*!?🌿🐎🐕🐑🐄🐴🐅🐰🦌🐭])', r'*\1*', text)

    # 标注动物
    animals = ['马', '牛', '羊', '犬', '鸡', '豕', '龙', '虎', '鹿', '狼', '狐', '兔', '鼠', '象', '犀', '熊', '罴', '鸟', '鹰', '隼', '雁', '鸦', '鸦']
    for animal in animals:
        emoji_map = {'马': '🐎', '牛': '🐄', '羊': '🐑', '犬': '🐕', '虎': '🐅', '鹿': '🦌', '兔': '🐰', '鼠': '🐭', '驴': '🐴'}
        emoji = emoji_map.get(animal, '🌿')
        text = re.sub(f'(?<![=@$%&^~*!?🌿🐎🐕🐑🐄🐴🐅🐰🦌🐭])({animal})(?![=@$%&^~*!?🌿🐎🐕🐑🐄🐴🐅🐰🦌🐭])', f'{emoji}\\1{emoji}', text)

    return text

def process_chapter(input_file, output_file):
    """处理单个章节"""
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 获取标题
    title = lines[0].strip() if lines else ""
    chapter_num = re.search(r'(\d+)', title).group(1) if re.search(r'\d+', title) else "000"

    output_lines = []
    output_lines.append(f"# {chapter_num} {title}\n\n")
    output_lines.append(f"## 标题\n")
    output_lines.append(f"{tag_entities(title)}\n\n")

    # 处理正文
    section_num = 1
    for i, line in enumerate(lines[1:], 1):
        line = line.strip()
        if not line:
            continue

        # 添加段落编号
        output_lines.append(f"## [{section_num}] 第{section_num}段\n\n")
        output_lines.append(f"[{section_num}.1] {tag_entities(line)}\n\n")
        section_num += 1

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    print(f"已完成: {output_file}")

if __name__ == "__main__":
    base_dir = "docs/original_text"
    output_dir = "chapter_md"

    chapters = [
        "088_蒙恬列传",
        "089_张耳陈馀列传",
        "090_魏豹彭越列传",
        "091_黥布列传",
        "092_淮阴侯列传",
        "093_韩信卢绾列传",
        "094_田儋列传",
        "095_樊郦滕灌列传"
    ]

    for chapter in chapters:
        input_file = os.path.join(base_dir, f"{chapter}.txt")
        output_file = os.path.join(output_dir, f"{chapter}.tagged.md")

        if os.path.exists(input_file):
            process_chapter(input_file, output_file)
        else:
            print(f"文件不存在: {input_file}")

    print("\n所有章节处理完成!")
