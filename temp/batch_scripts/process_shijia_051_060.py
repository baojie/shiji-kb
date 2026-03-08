#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理《史记》世家 051-060章节
生成带实体标注的markdown文件
"""

import re
import os
from pathlib import Path

# 配置路径
ORIGINAL_TEXT_DIR = "/home/baojie/work/shiji-kb/docs/original_text"
OUTPUT_DIR = "/home/baojie/work/shiji-kb/chapter_md"

# 需要处理的章节列表
CHAPTERS = [
    "051_荆燕世家",
    "052_齐悼惠王世家",
    "053_萧相国世家",
    "054_曹相国世家",
    "055_留侯世家",
    "056_陈丞相世家",
    "057_绛侯周勃世家",
    "058_梁孝王世家",
    "059_五宗世家",
    "060_三王世家"
]

class ShijiaProcessor:
    """世家处理器"""

    def __init__(self):
        # 实体词典
        self.persons = self._load_persons()
        self.places = self._load_places()
        self.positions = self._load_positions()
        self.dynasties = self._load_dynasties()
        self.tribes = self._load_tribes()
        self.institutions = self._load_institutions()
        self.artifacts = self._load_artifacts()
        self.time_expressions = self._load_time_expressions()
        self.flora_fauna = self._load_flora_fauna()

        # 段落计数器
        self.para_num = 1
        self.sub_para_num = 0

    def _load_persons(self):
        """加载人名词典"""
        return {
            # 汉初诸王
            '刘贾', '刘泽', '刘濞', '刘肥', '刘交', '刘长', '刘安', '刘建', '刘勃', '刘辟光',
            '刘胜', '刘越', '刘寄', '刘舜', '刘乘', '刘彭祖', '刘端', '刘发',
            '刘闳', '刘旦', '刘胥', '刘弘',

            # 功臣
            '萧何', '曹参', '张良', '陈平', '周勃', '周亚夫', '灌婴', '樊哙',
            '周昌', '周苛', '王陵', '审食其',

            # 汉帝
            '刘邦', '高祖', '高帝', '刘盈', '惠帝', '孝惠', '刘恒', '文帝', '孝文',
            '刘启', '景帝', '孝景', '刘彻', '武帝', '孝武', '刘弗陵', '昭帝', '孝昭',
            '刘询', '宣帝', '孝宣',

            # 后妃
            '吕后', '吕雉', '窦太后', '薄太后', '王夫人', '李夫人', '卫夫人', '卫子夫',
            '戚夫人', '薄姬',

            # 外戚
            '吕产', '吕禄', '吕台', '吕嘉', '吕通', '窦婴', '田蚡', '霍光', '霍去病',
            '卫青', '上官桀',

            # 谋臣
            '陆贾', '叔孙通', '郦食其', '随何', '蒯通', '田生', '韩信', '彭越', '黥布',
            '英布', '卢绾', '臧荼',

            # 楚汉人物
            '项羽', '项伯', '项庄', '范增', '虞子期', '龙且', '钟离昧', '季布',
            '周殷', '共尉', '武王', '楚王信', '楚元王', '楚王戊',

            # 齐鲁人物
            '田横', '田荣', '田都', '田齐', '召平',

            # 燕赵人物
            '张耳', '陈余', '张敖', '贯高',

            # 其他
            '司马迁', '太史公', '褚先生',
            '郢人', '田叔', '任敖', '王稽', '张子卿',
            '丞相青翟', '御史大夫汤', '太常充', '大行令息', '太子少傅安',
        }

    def _load_places(self):
        """加载地名词典"""
        return {
            # 郡国
            '荆', '楚', '齐', '燕', '赵', '魏', '韩', '吴', '越', '梁', '代',
            '淮南', '淮东', '淮西', '江淮', '关中', '关东', '山东', '河东', '河西', '河内', '河南',
            '巴', '蜀', '南越', '东越', '闽越', '西域',

            # 都城
            '长安', '洛阳', '雒阳', '咸阳', '邯郸', '大梁', '临淄', '彭城', '薛', '寿春',
            '番禺', '广陵', '江都', '睢阳', '定陶',

            # 具体地名
            '沛', '丰', '砀', '泗水', '薛郡', '琅邪', '东海', '临江',
            '荥阳', '成皋', '白马津', '固陵', '垓下', '富陵',
            '梁', '梁国', '睢阳', '砀山',
            '营陵', '平原', '济南', '济北', '菑川', '胶东', '胶西', '城阳',
            '中山', '常山', '真定', '涿郡',
            '雁门', '云中', '九原', '上谷', '渔阳',
            '南郡', '江陵', '九江', '庐江', '衡山',
            '武库', '敖仓', '未央宫', '长乐宫',

            # 山川
            '太行山', '首阳山', '泰山', '华山', '恒山', '衡山', '嵩山',
            '黄河', '长江', '淮河', '济水', '泗水', '汉水', '渭水',
            '五湖', '三江', '江湖', '东海', '北海',

            # 关隘
            '函谷关', '武关', '萧关', '居庸关',
        }

    def _load_positions(self):
        """加载官职词典"""
        return {
            # 三公九卿
            '丞相', '相国', '太尉', '御史大夫', '太常', '郎中令', '卫尉',
            '太仆', '廷尉', '典客', '宗正', '治粟内史', '少府', '大行令',

            # 列侯爵位
            '侯', '列侯', '关内侯', '彻侯', '通侯',

            # 王公
            '王', '诸侯王', '亲王', '公', '公子',

            # 将军
            '将军', '大将军', '骠骑将军', '车骑将军', '卫将军', '前将军', '后将军',
            '左将军', '右将军', '上将军',

            # 大夫
            '大夫', '中大夫', '太中大夫', '谏大夫', '博士', '议郎', '郎中',

            # 地方官
            '郡守', '太守', '都尉', '县令', '县丞', '县尉', '乡长', '亭长',
            '诸侯相', '国相', '中尉',

            # 侍从
            '舍人', '中庶子', '郎', '侍郎', '侍中', '常侍', '黄门侍郎',

            # 师傅
            '太傅', '太师', '太保', '少傅', '少师', '少保',
            '太子太傅', '太子少傅', '师傅',

            # 特殊
            '尚书令', '御史', '谒者', '使者', '万夫长', '千夫长',
        }

    def _load_dynasties(self):
        """加载朝代/氏族/国号"""
        return {
            '汉', '汉朝', '汉室', '汉国', '大汉', '汉家',
            '秦', '秦朝', '秦国',
            '周', '周朝', '周室', '周王室',
            '商', '殷', '夏',
            '刘氏', '吕氏', '赵氏', '窦氏', '田氏', '姬氏',
        }

    def _load_tribes(self):
        """加载族群/部落"""
        return {
            '匈奴', '胡', '荤粥', '荤粥氏', '戎', '狄', '蛮夷', '四夷',
            '羌', '氐', '越', '百越', '南蛮', '东夷', '西戎', '北狄',
        }

    def _load_institutions(self):
        """加载制度/典章"""
        return {
            '封建', '郡县', '分封', '世袭', '禅让',
            '礼', '乐', '刑', '法', '律', '令',
            '礼义', '礼乐', '仁义', '忠孝', '孝道',
            '社稷', '宗庙', '太社', '国社',
            '儒家', '法家', '道家', '阴阳家',
            '制度', '典章', '诏书', '策书', '奏疏',
        }

    def _load_artifacts(self):
        """加载器物/礼器"""
        return {
            '鼎', '钟', '鼓', '磬', '剑', '戈', '矛', '戟', '弓', '弩',
            '玉', '璧', '圭', '璋', '印', '绶', '符', '节',
            '车', '马', '辇', '舟', '船',
            '金', '钱', '财币', '黄金', '白金',
            '粟', '米', '麦', '布', '帛', '丝',
        }

    def _load_time_expressions(self):
        """加载时间表达"""
        # 年号、纪年会通过正则匹配，这里只放一些常见的
        return {
            '元年', '二年', '三年', '四年', '五年', '六年', '七年', '八年', '九年', '十年',
            '十一年', '十二年', '十三年', '十四年', '十五年', '十六年', '十七年', '十八年',
            '正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月',
            '春', '夏', '秋', '冬',
            '本始元年', '元朔元年', '建元', '元鼎', '元封', '太初',
        }

    def _load_flora_fauna(self):
        """加载动植物"""
        return {
            '马', '牛', '羊', '犬', '豕', '鸡', '鸭', '鹅',
            '龙', '凤', '麟', '龟', '鹤', '鹿', '象', '虎', '豹', '熊', '罴',
            '禾', '稻', '粟', '麦', '黍', '稷', '菽', '麻',
            '桑', '松', '柏', '梧桐', '竹', '兰', '芝',
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
                # 使用正则避免重复标注
                pattern = f'(?<![@ =~$^*!&?%🌿])({re.escape(person)})(?![@ =~$^*!&?%🌿])'
                result = re.sub(pattern, r'@\1@', result)

        # 2. 地名
        places_sorted = sorted(self.places, key=len, reverse=True)
        for place in places_sorted:
            if place in result:
                pattern = f'(?<![@ =~$^*!&?%🌿])({re.escape(place)})(?![@ =~$^*!&?%🌿])'
                result = re.sub(pattern, r'=\1=', result)

        # 3. 时间表达（使用正则匹配）
        # 匹配"X年"、"X月"、"春夏秋冬"等
        result = re.sub(r'(?<![@ =~$^*!&?%🌿])([元本]始元年|元[朔鼎封](?:元年)?|太初(?:元年)?|建元(?:元年)?|[元二三四五六七八九十]+年|十[一二三四五六七八九]年|[正二三四五六七八九十冬腊]+月|十[一二]月|春|夏|秋|冬)(?![@ =~$^*!&?%🌿])', r'%\1%', result)
        # 匹配干支日期
        result = re.sub(r'(?<![@ =~$^*!&?%🌿])([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])(?![@ =~$^*!&?%🌿])', r'%\1%', result)

        # 4. 官职
        positions_sorted = sorted(self.positions, key=len, reverse=True)
        for pos in positions_sorted:
            if pos in result:
                pattern = f'(?<![@ =~$^*!&?%🌿])({re.escape(pos)})(?![@ =~$^*!&?%🌿])'
                result = re.sub(pattern, r'$\1$', result)

        # 5. 朝代/氏族
        dynasties_sorted = sorted(self.dynasties, key=len, reverse=True)
        for dynasty in dynasties_sorted:
            if dynasty in result:
                pattern = f'(?<![@ =~$^*!&?%🌿])({re.escape(dynasty)})(?![@ =~$^*!&?%🌿])'
                result = re.sub(pattern, r'&\1&', result)

        # 6. 族群
        tribes_sorted = sorted(self.tribes, key=len, reverse=True)
        for tribe in tribes_sorted:
            if tribe in result:
                pattern = f'(?<![@ =~$^*!&?%🌿])({re.escape(tribe)})(?![@ =~$^*!&?%🌿])'
                result = re.sub(pattern, r'~\1~', result)

        # 7. 制度
        institutions_sorted = sorted(self.institutions, key=len, reverse=True)
        for inst in institutions_sorted:
            if inst in result:
                pattern = f'(?<![@ =~$^*!&?%🌿])({re.escape(inst)})(?![@ =~$^*!&?%🌿])'
                result = re.sub(pattern, r'^\1^', result)

        # 8. 器物
        artifacts_sorted = sorted(self.artifacts, key=len, reverse=True)
        for art in artifacts_sorted:
            if art in result:
                pattern = f'(?<![@ =~$^*!&?%🌿])({re.escape(art)})(?![@ =~$^*!&?%🌿])'
                result = re.sub(pattern, r'*\1*', result)

        # 9. 动植物
        flora_fauna_sorted = sorted(self.flora_fauna, key=len, reverse=True)
        for ff in flora_fauna_sorted:
            if ff in result:
                pattern = f'(?<![@ =~$^*!&?%🌿])({re.escape(ff)})(?![@ =~$^*!&?%🌿])'
                result = re.sub(pattern, r'🌿\1🌿', result)

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

        # 提取世家名称
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
        in_taishigong = False

        for i, line in enumerate(content_lines):
            if not line:
                continue

            # 检查是否是太史公曰或褚先生曰
            if line.startswith('太史公曰') or '太史公曰' in line:
                output_lines.append("\n## 太史公曰\n\n")
                in_taishigong = True
                # 将太史公曰的内容作为NOTE块
                remaining_text = line.replace('太史公曰：', '').replace('太史公曰', '').strip()
                if remaining_text:
                    tagged_text = self.tag_entity(remaining_text)
                    output_lines.append(f"> [NOTE] {tagged_text}\n\n")
                continue
            elif line.startswith('褚先生曰') or '褚先生曰' in line:
                output_lines.append("\n## 褚先生曰\n\n")
                in_taishigong = True
                remaining_text = line.replace('褚先生曰：', '').replace('褚先生曰', '').strip()
                if remaining_text:
                    tagged_text = self.tag_entity(remaining_text)
                    output_lines.append(f"> [NOTE] {tagged_text}\n\n")
                continue

            # 如果在太史公曰或褚先生曰部分，使用NOTE格式
            if in_taishigong:
                # 检查是否是诗赋类内容（短句，可能有韵律）
                if len(line) < 30 and '，' in line:
                    tagged_line = self.tag_entity(line)
                    output_lines.append(f"> {tagged_line}\n>\n")
                else:
                    tagged_line = self.tag_entity(line)
                    output_lines.append(f"> [NOTE] {tagged_line}\n\n")
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
    print("《史记》世家 051-060 批量处理工具")
    print("="*60)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    processor = ShijiaProcessor()

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
            import traceback
            traceback.print_exc()
            fail_count += 1

    print("\n" + "="*60)
    print(f"处理完成统计:")
    print(f"  成功: {success_count} 个章节")
    print(f"  失败: {fail_count} 个章节")
    print("="*60)

if __name__ == "__main__":
    main()
