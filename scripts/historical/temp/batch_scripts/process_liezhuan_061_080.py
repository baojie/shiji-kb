#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理《史记》列传 061-080章节
生成带实体标注的markdown文件
"""

import re
import os
from pathlib import Path

# 配置路径
ORIGINAL_TEXT_DIR = "docs/original_text"
OUTPUT_DIR = "chapter_md"

# 需要处理的章节列表
CHAPTERS = [
    "061_伯夷列传",
    "062_管晏列传",
    "063_老子韩非列传",
    "064_司马穰苴列传",
    "065_孙子吴起列传",
    "066_伍子胥列传",
    "067_仲尼弟子列传",
    "068_商君列传",
    "069_苏秦列传",
    "070_张仪列传",
    "071_樗里子甘茂列传",
    "072_穰侯列传",
    "073_白起王翦列传",
    "074_孟子荀卿列传",
    "075_孟尝君列传",
    "076_平原君虞卿列传",
    "077_魏公子列传",
    "078_春申君列传",
    "079_范睢蔡泽列传",
    "080_乐毅列传"
]

class LiezhuanProcessor:
    """列传处理器"""

    def __init__(self):
        # 实体词典
        self.persons = self._load_persons()
        self.places = self._load_places()
        self.positions = self._load_positions()
        self.dynasties = self._load_dynasties()
        self.tribes = self._load_tribes()
        self.institutions = self._load_institutions()
        self.artifacts = self._load_artifacts()

        # 段落计数器
        self.para_num = 1
        self.sub_para_num = 0

    def _load_persons(self):
        """加载人名词典"""
        return {
            # 列传主角
            '伯夷', '叔齐', '管仲', '晏婴', '晏子', '鲍叔牙', '鲍叔',
            '老子', '韩非', '李耳', '庄子', '申不害', '公孙龙',
            '司马穰苴', '穰苴', '孙武', '孙子', '吴起', '孙膑',
            '伍子胥', '伍员', '申包胥',
            '孔子', '颜回', '颜渊', '子贡', '子路', '曾子', '子夏', '子张',
            '商鞅', '卫鞅', '公孙鞅',
            '苏秦', '张仪',
            '樗里子', '甘茂', '甘罗',
            '穰侯', '魏冉',
            '白起', '王翦', '王贲',
            '孟子', '孟轲', '荀子', '荀卿',
            '孟尝君', '田文',
            '平原君', '赵胜', '虞卿',
            '魏公子', '信陵君', '无忌',
            '春申君', '黄歇',
            '范睢', '蔡泽',
            '乐毅', '乐间',

            # 君主
            '齐桓公', '桓公', '齐灵公', '齐庄公', '齐景公',
            '秦孝公', '孝公', '秦惠王', '惠王', '秦武王', '武王',
            '秦昭王', '昭王', '秦始皇',
            '楚怀王', '怀王', '楚顷襄王', '顷襄王',
            '赵武灵王', '武灵王', '赵惠文王', '惠文王',
            '魏安釐王', '安釐王',
            '燕昭王', '昭王', '燕惠王',
            '齐威王', '威王', '齐宣王', '宣王', '齐湣王', '湣王',
            '周武王', '武王', '周文王', '文王',

            # 其他重要人物
            '公子纠', '公子小白',
            '召忽', '隰朋',
            '越石父',
            '关龙逢', '比干', '箕子',
            '许由', '卞随', '务光',
            '惠施', '邹衍', '淳于髡',
            '鲁仲连', '邹忌',
            '毛遂', '李同',
            '侯嬴', '朱亥',
            '李园',
            '须贾', '郑安平', '王稽',
            '田单', '剧辛',

            # 太史公
            '太史公',
        }

    def _load_places(self):
        """加载地名词典"""
        return {
            # 国名作为地名
            '齐', '鲁', '晋', '秦', '楚', '燕', '赵', '魏', '韩', '宋', '卫', '郑', '陈', '蔡', '曹', '吴', '越',
            '齐国', '鲁国', '晋国', '秦国', '楚国', '燕国', '赵国', '魏国', '韩国',

            # 具体地名
            '颍上', '莱', '夷维', '陈', '苦县', '楚国', '韩国',
            '阿', '即墨', '临淄', '稷下',
            '咸阳', '商', '商於', '函谷关', '武关',
            '郢', '鄢', '邯郸', '大梁', '洛阳', '周',
            '首阳山', '箕山',
            '渑池', '长平', '番吾',
            '中山', '代', '上党',
            '河西', '河东', '河内',
            '雒阳', '新郑',
            '穰', '陶',
            '薛', '孟尝',
            '信陵',
            '淮北', '淮南',
            '济西',

            # 山川
            '黄河', '长江', '淮水', '济水', '渭水',
        }

    def _load_positions(self):
        """加载官职词典"""
        return {
            # 不包含单字的'相'，避免误标注
            '丞相', '相国', '宰相', '左相', '右相',
            '太傅', '太师', '太保',
            '将军', '大将军', '上将军',
            '大夫', '上大夫', '中大夫', '下大夫',
            '令尹', '司马', '司徒', '司空',
            '太尉', '御史大夫',
            '郡守', '县令', '县丞',
            '左庶长', '大良造',
            '客卿',
            '门客', '食客',
            '舍人', '中庶子',
        }

    def _load_dynasties(self):
        """加载朝代/氏族/国号"""
        return {
            '周', '周朝', '周室', '周王室',
            '商', '殷', '商朝',
            '夏', '夏朝',
            '春秋', '战国',
            '神农', '伏羲',
        }

    def _load_tribes(self):
        """加载族群/部落"""
        return {
            '戎', '狄', '胡', '匈奴',
            '山戎', '北狄',
            '蛮夷', '四夷',
        }

    def _load_institutions(self):
        """加载制度/典章"""
        return {
            '井田', '分封', '宗法',
            '礼', '刑', '政',  # 移除单字"乐"避免误标注人名
            '礼乐', '刑政',  # 使用组合词
            '仁义', '道德',
            '法家', '儒家', '道家', '墨家', '名家', '阴阳家', '纵横家',
            '连横', '合纵',
            '变法', '商鞅变法',
            '世袭', '禅让',
        }

    def _load_artifacts(self):
        """加载器物/礼器"""
        return {
            '鼎', '钟', '剑', '璧',
            '玉', '印', '符',
            '车', '马', '舟',
        }

    def tag_entity(self, text):
        """对文本进行实体标注"""
        if not text or text.isspace():
            return text

        result = text

        # 标注顺序：从长到短，避免覆盖
        # 1. 人名（最优先）
        persons_sorted = sorted(self.persons, key=len, reverse=True)
        for person in persons_sorted:
            if person in result:
                # 使用正则避免重复标注和标注已标注内容
                pattern = f'(?<![@ =~$^*!&?🌿])({re.escape(person)})(?![@ =~$^*!&?🌿])'
                result = re.sub(pattern, r'@\1@', result)

        # 2. 地名
        places_sorted = sorted(self.places, key=len, reverse=True)
        for place in places_sorted:
            if place in result:
                pattern = f'(?<![@ =~$^*!&?🌿])({re.escape(place)})(?![@ =~$^*!&?🌿])'
                result = re.sub(pattern, r'=\1=', result)

        # 3. 官职
        positions_sorted = sorted(self.positions, key=len, reverse=True)
        for pos in positions_sorted:
            if pos in result:
                pattern = f'(?<![@ =~$^*!&?🌿])({re.escape(pos)})(?![@ =~$^*!&?🌿])'
                result = re.sub(pattern, r'$\1$', result)

        # 4. 朝代/氏族
        dynasties_sorted = sorted(self.dynasties, key=len, reverse=True)
        for dynasty in dynasties_sorted:
            if dynasty in result:
                pattern = f'(?<![@ =~$^*!&?🌿])({re.escape(dynasty)})(?![@ =~$^*!&?🌿])'
                result = re.sub(pattern, r'&\1&', result)

        # 5. 族群
        for tribe in self.tribes:
            if tribe in result:
                pattern = f'(?<![@ =~$^*!&?🌿])({re.escape(tribe)})(?![@ =~$^*!&?🌿])'
                result = re.sub(pattern, r'~\1~', result)

        # 6. 制度
        for inst in self.institutions:
            if inst in result:
                pattern = f'(?<![@ =~$^*!&?🌿])({re.escape(inst)})(?![@ =~$^*!&?🌿])'
                result = re.sub(pattern, r'^\1^', result)

        # 7. 器物
        for art in self.artifacts:
            if art in result:
                pattern = f'(?<![@ =~$^*!&?🌿])({re.escape(art)})(?![@ =~$^*!&?🌿])'
                result = re.sub(pattern, r'*\1*', result)

        return result

    def process_chapter(self, chapter_name):
        """处理单个章节"""
        print(f"\n{'='*60}")
        print(f"开始处理: {chapter_name}")
        print(f"{'='*60}")

        # 读取原始文本
        input_file = Path(ORIGINAL_TEXT_DIR) / f"{chapter_name}.txt"
        if not input_file.exists():
            print(f"错误: 文件不存在 {input_file}")
            return False

        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 提取列传名称
        title = lines[0].strip() if lines else chapter_name.split('_')[1]

        # 初始化输出
        output_lines = []
        output_lines.append(f"# [0] {title}\n")
        output_lines.append("\n")

        # 重置段落计数
        self.para_num = 1
        self.sub_para_num = 0

        # 分析文本结构
        content_lines = [line.strip() for line in lines[1:] if line.strip()]

        # 处理内容
        current_section = None

        for i, line in enumerate(content_lines):
            if not line:
                continue

            # 检查是否是太史公曰
            if line.startswith('太史公曰') or '太史公曰' in line:
                output_lines.append("\n## 太史公曰\n\n")
                # 将太史公曰的内容作为NOTE块
                remaining_text = line.replace('太史公曰：', '').replace('太史公曰', '').strip()
                if remaining_text:
                    tagged_text = self.tag_entity(remaining_text)
                    output_lines.append(f"> [NOTE] {tagged_text}\n\n")
                continue

            # 检查是否包含对话引号
            if '曰："' in line or '曰:"' in line or '"' in line:
                # 对话内容保持原样，但进行实体标注
                tagged_line = self.tag_entity(line)
                output_lines.append(f"[{self.para_num}] {tagged_line}\n\n")
                self.para_num += 1
            else:
                # 普通段落
                tagged_line = self.tag_entity(line)
                output_lines.append(f"[{self.para_num}] {tagged_line}\n\n")
                self.para_num += 1

        # 写入输出文件
        output_file = Path(OUTPUT_DIR) / f"{chapter_name}.tagged.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(output_lines)

        print(f"✓ 处理完成: {output_file}")
        print(f"  共 {self.para_num - 1} 个段落")
        return True

def main():
    """主函数"""
    print("\n" + "="*60)
    print("《史记》列传 061-080 批量处理工具")
    print("="*60)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    processor = LiezhuanProcessor()

    success_count = 0
    fail_count = 0

    for chapter in CHAPTERS:
        try:
            if processor.process_chapter(chapter):
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"✗ 处理失败: {chapter}")
            print(f"  错误: {e}")
            fail_count += 1

    print("\n" + "="*60)
    print(f"处理完成统计:")
    print(f"  成功: {success_count} 个章节")
    print(f"  失败: {fail_count} 个章节")
    print("="*60)

if __name__ == "__main__":
    main()
