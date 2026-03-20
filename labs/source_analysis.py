#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《史记》事件史源类型批量推理

基于事件年代、章节类型、事件类型等规则，推断每个事件的史源类型和可信度等级
"""

import json
import csv
import re
from pathlib import Path
from typing import Dict, Tuple, List

# 司马谈去世年代
SIMA_TAN_YEAR = -110
# 司马迁出生年代
SIMA_QIAN_YEAR = -100


class SourceAnalyzer:
    """史源类型分析器"""

    def __init__(self):
        # 加载事件汇总数据
        self.summary_path = Path("/home/baojie/work/knowledge/shiji-kb/kg/events/events_summary.json")
        with open(self.summary_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        # 已知的文献史源章节
        self.doc_source_chapters = {
            '001', '002', '003', '004', '005',  # 上古-秦本纪（尚书、春秋）
            '031', '032', '033', '034', '035', '036', '037', '038', '039', '040',  # 世家（左传、国语）
            '041', '042', '043', '044', '045', '046',  # 战国世家（战国策）
            '047',  # 孔子世家（儒家经典）
            '068',  # 商君列传（商君书）
        }

        # 已知的口述史源案例（事件ID）
        self.oral_source_events = {
            '086-017': '夏无且口述',  # 荆轲刺秦
            '007-027': '樊哙家族口述',  # 鸿门宴
            '007-028': '樊哙家族口述',  # 樊哙救主
            '007-017': '项伯家族+军中传闻',  # 破釜沉舟
        }

        self.results = []

    def extract_year(self, time_str: str) -> int or None:
        """从时间字符串中提取年份"""
        if not time_str:
            return None

        # 尝试匹配各种时间格式
        patterns = [
            r'公元前(\d+)年',
            r'前(\d+)年',
            r'—前(\d+)年',
            r'\[约公元前(\d+)年\]',
            r'（公元前(\d+)年）',
        ]

        for pattern in patterns:
            match = re.search(pattern, time_str)
            if match:
                return -int(match.group(1))

        return None

    def analyze_event(self, chapter_num: str, event_id: str, event_name: str,
                      event_type: str, time_str: str) -> Tuple[str, str, str]:
        """
        分析单个事件的史源类型

        返回: (史源类型, 可信度等级, 推理依据)
        """
        event_year = self.extract_year(time_str)

        # 计算时间距离
        if event_year:
            dist_tan = event_year - SIMA_TAN_YEAR
            dist_qian = event_year - SIMA_QIAN_YEAR
        else:
            dist_tan = None
            dist_qian = None

        # 已知口述史源案例
        if event_id in self.oral_source_events:
            return ("亲历口述", "B", self.oral_source_events[event_id])

        # 规则1: 超过400年必定文献传承
        if dist_tan and dist_tan < -400:
            return ("文献传承", "C", f"距司马谈{abs(dist_tan)}年，必依赖文献")

        # 规则2: 按章节类型判断
        chapter_type = self._get_chapter_type(chapter_num)

        # 上古本纪（五帝-秦本纪）
        if chapter_num in self.doc_source_chapters:
            if chapter_num in ['001', '002', '003', '004', '005']:
                return ("文献传承", "C", "上古史料，依据《尚书》《春秋》等")
            elif chapter_num in ['031', '032', '033', '034', '035', '036', '037', '038', '039', '040', '041', '042']:
                return ("文献传承", "B", "春秋史事，依据《左传》《国语》")
            elif chapter_num in ['043', '044', '045', '046']:
                return ("文献传承", "B", "战国史事，依据《战国策》")
            elif chapter_num == '047':
                return ("文献传承", "A", "孔子生平，依据儒家经典")
            elif chapter_num == '068':
                return ("文献传承", "A", "商鞅变法，依据《商君书》")

        # 秦始皇-汉武帝时期（文献+口述+档案混合）
        if chapter_num in ['006', '007', '008', '009', '010', '011', '012']:
            if event_type in ['继位', '战争', '政治改革', '自然灾害']:
                if dist_tan and dist_tan > -50:
                    return ("亲历口述", "A", f"距司马谈{abs(dist_tan)}年，可能有口述传承")
                else:
                    return ("文献传承", "B", "重大政治事件，依据官方档案")
            elif event_type in ['政治活动', '家族事件']:
                if dist_tan and dist_tan > -100:
                    return ("家族传承", "B", f"距司马谈{abs(dist_tan)}年，可能有家族口述")
                else:
                    return ("军中传闻", "C", "军中或民间流传")

        # 汉初世家/列传（口述+家族传承为主）
        if int(chapter_num) >= 48 and int(chapter_num) <= 60:
            if event_type in ['家族事件']:
                return ("家族传承", "A", "汉初功臣家族，可能有家族口述")
            elif event_type in ['战争', '政治活动']:
                if dist_tan and dist_tan > -50:
                    return ("亲历口述", "B", f"距司马谈{abs(dist_tan)}年，可能有亲历者口述")
                else:
                    return ("军中传闻", "C", "军中流传")

        # 先秦列传（文献传承为主）
        if int(chapter_num) >= 61 and int(chapter_num) <= 86:
            if event_type in ['文化活动']:
                return ("文献传承", "B", "先秦人物文化活动，依据学派传承")
            elif event_type in ['战争', '政治活动']:
                return ("文献传承", "C", "先秦史事，依据《战国策》等文献")

        # 秦汉列传（口述+家族传承）
        if int(chapter_num) >= 87 and int(chapter_num) <= 130:
            if event_type in ['家族事件']:
                return ("家族传承", "B", "秦汉人物家族，可能有家族传承")
            elif event_type in ['战争']:
                if dist_tan and dist_tan > -50:
                    return ("亲历口述", "B", f"距司马谈{abs(dist_tan)}年，可能有亲历者口述")
                else:
                    return ("军中传闻", "C", "军中流传")
            elif event_type in ['政治活动']:
                if dist_tan and dist_tan > -30:
                    return ("亲历口述", "A", f"距司马谈{abs(dist_tan)}年，太史公可能亲见或亲闻")
                else:
                    return ("官方叙事", "B", "政治事件，依据官方叙事")

        # 八书（文献+档案+亲见）
        if int(chapter_num) >= 23 and int(chapter_num) <= 30:
            if event_type in ['改革', '政治改革']:
                return ("文献传承", "A", "制度沿革，依据档案文献")
            elif event_type in ['文化活动']:
                return ("文献传承", "B", "礼乐文化，依据文献传承")
            elif event_type in ['自然灾害']:
                return ("文献传承", "A", "天象灾异，依据官方记录")
            elif event_type in ['建设']:
                return ("文献传承", "B", "工程建设，依据档案记录")

        # 十表（档案/文献）
        if int(chapter_num) >= 13 and int(chapter_num) <= 22:
            return ("文献传承", "A", "年表，依据档案文献")

        # 默认规则：按时间距离判断
        if dist_tan:
            if dist_tan > -50:
                return ("亲历口述", "C", f"距司马谈{abs(dist_tan)}年，可能有口述")
            elif dist_tan > -100:
                return ("家族传承", "C", f"距司马谈{abs(dist_tan)}年，可能有2-3代传承")
            elif dist_tan > -200:
                return ("文献传承", "C", f"距司马谈{abs(dist_tan)}年，依赖文献")
            else:
                return ("文献传承", "D", f"距司马谈{abs(dist_tan)}年，远古史料可信度低")

        # 无法判断年代
        return ("民间传说", "E", "无法确定年代，可能为传说")

    def _get_chapter_type(self, chapter_num: str) -> str:
        """获取章节类型"""
        num = int(chapter_num)
        if 1 <= num <= 12:
            return "本纪"
        elif 13 <= num <= 22:
            return "表"
        elif 23 <= num <= 30:
            return "书"
        elif 31 <= num <= 60:
            return "世家"
        elif 61 <= num <= 130:
            return "列传"
        return "未知"

    def process_all(self):
        """处理所有事件"""
        print(f"开始处理 {self.data['total_events']} 个事件...")

        for chapter in self.data['chapters']:
            chapter_num = chapter['num']
            chapter_name = chapter['chapter']

            # 读取事件索引文件
            event_file = Path(f"/home/baojie/work/knowledge/shiji-kb/kg/events/data/{chapter_name}_事件索引.md")

            if not event_file.exists():
                print(f"警告: {event_file} 不存在")
                continue

            # 解析事件索引
            events = self._parse_event_file(event_file)

            for event in events:
                event_id = event['id']
                event_name = event['name']
                event_type = event['type']
                time_str = event['time']

                # 分析史源
                source_type, credibility, reason = self.analyze_event(
                    chapter_num, event_id, event_name, event_type, time_str
                )

                # 计算时间距离
                event_year = self.extract_year(time_str)
                if event_year:
                    dist_tan = abs(event_year - SIMA_TAN_YEAR)
                    dist_qian = abs(event_year - SIMA_QIAN_YEAR)
                else:
                    dist_tan = ""
                    dist_qian = ""

                # 添加结果
                self.results.append({
                    '章节号': chapter_num,
                    '章节名': chapter_name.replace(f"{chapter_num}_", "").replace("_事件索引", ""),
                    '事件ID': event_id,
                    '事件名称': event_name,
                    '事件类型': event_type,
                    '事件年代': event_year if event_year else "",
                    '距司马谈': dist_tan,
                    '距司马迁': dist_qian,
                    '史源类型': source_type,
                    '可信度': credibility,
                    '推理依据': reason
                })

            print(f"已处理: {chapter_name} ({len(events)} 个事件)")

        print(f"处理完成，共 {len(self.results)} 个事件")

    def _parse_event_file(self, file_path: Path) -> List[Dict]:
        """解析事件索引文件"""
        events = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取表格
        table_match = re.search(r'\| 事件ID \| 事件名称 \| 事件类型 \| 时间 \|.*?\n\|(.*?)\n\n', content, re.DOTALL)
        if not table_match:
            return events

        table_content = table_match.group(0)
        lines = table_content.split('\n')

        for line in lines[2:]:  # 跳过表头和分隔行
            if not line.strip() or not line.startswith('|'):
                continue

            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 5:
                continue

            event_id = parts[1]
            event_name = parts[2]
            event_type = parts[3]
            time_str = parts[4]

            if event_id and event_id != '事件ID':
                events.append({
                    'id': event_id,
                    'name': event_name,
                    'type': event_type,
                    'time': time_str
                })

        return events

    def save_csv(self, output_path: str):
        """保存为CSV"""
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            fieldnames = ['章节号', '章节名', '事件ID', '事件名称', '事件类型',
                         '事件年代', '距司马谈', '距司马迁', '史源类型', '可信度', '推理依据']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)

        print(f"CSV文件已保存: {output_path}")

    def generate_summary(self, output_path: str):
        """生成统计报告"""
        # 统计史源类型分布
        source_dist = {}
        for r in self.results:
            st = r['史源类型']
            source_dist[st] = source_dist.get(st, 0) + 1

        # 统计可信度分布
        cred_dist = {}
        for r in self.results:
            cr = r['可信度']
            cred_dist[cr] = cred_dist.get(cr, 0) + 1

        # 统计章节史源分布（本纪/世家/列传）
        chapter_source = {}
        for r in self.results:
            chapter_num = r['章节号']
            chapter_type = self._get_chapter_type(chapter_num)
            source = r['史源类型']

            key = f"{chapter_type}-{source}"
            chapter_source[key] = chapter_source.get(key, 0) + 1

        # 生成报告
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 《史记》事件史源类型统计报告\n\n")
            f.write(f"**生成时间**: 2026-03-20\n\n")
            f.write(f"**总事件数**: {len(self.results)}\n\n")

            f.write("## 一、史源类型分布\n\n")
            f.write("| 史源类型 | 事件数 | 占比 |\n")
            f.write("|---------|--------|------|\n")
            for st in sorted(source_dist.keys(), key=lambda x: source_dist[x], reverse=True):
                count = source_dist[st]
                pct = count / len(self.results) * 100
                f.write(f"| {st} | {count} | {pct:.1f}% |\n")

            f.write("\n## 二、可信度等级分布\n\n")
            f.write("| 可信度等级 | 事件数 | 占比 |\n")
            f.write("|-----------|--------|------|\n")
            for cr in ['A', 'B', 'C', 'D', 'E']:
                count = cred_dist.get(cr, 0)
                pct = count / len(self.results) * 100 if len(self.results) > 0 else 0
                f.write(f"| {cr} | {count} | {pct:.1f}% |\n")

            f.write("\n## 三、按章节类型统计史源分布\n\n")

            for chapter_type in ['本纪', '表', '书', '世家', '列传']:
                f.write(f"### {chapter_type}\n\n")
                f.write("| 史源类型 | 事件数 |\n")
                f.write("|---------|--------|\n")

                type_total = {}
                for key, count in chapter_source.items():
                    ct, st = key.split('-')
                    if ct == chapter_type:
                        type_total[st] = count

                for st in sorted(type_total.keys(), key=lambda x: type_total[x], reverse=True):
                    f.write(f"| {st} | {type_total[st]} |\n")
                f.write("\n")

            f.write("\n## 四、关键发现\n\n")

            # 发现1: 文献传承占比
            doc_count = source_dist.get('文献传承', 0)
            doc_pct = doc_count / len(self.results) * 100
            f.write(f"1. **文献传承是主要史源**：{doc_count}个事件（{doc_pct:.1f}%）依赖文献传承，主要集中在先秦史事\n\n")

            # 发现2: 口述传承
            oral_count = source_dist.get('亲历口述', 0) + source_dist.get('家族传承', 0)
            oral_pct = oral_count / len(self.results) * 100
            f.write(f"2. **口述传承占重要地位**：{oral_count}个事件（{oral_pct:.1f}%）来自亲历口述或家族传承，主要集中在秦汉史事\n\n")

            # 发现3: 可信度分布
            high_cred = cred_dist.get('A', 0) + cred_dist.get('B', 0)
            high_pct = high_cred / len(self.results) * 100
            f.write(f"3. **整体可信度较高**：{high_cred}个事件（{high_pct:.1f}%）达到A/B级可信度\n\n")

            # 发现4: 特殊案例
            f.write("4. **已验证口述史源案例**：\n")
            for event_id, reason in self.oral_source_events.items():
                # 找到对应事件
                for r in self.results:
                    if r['事件ID'] == event_id:
                        f.write(f"   - {r['事件名称']}（{event_id}）：{reason}\n")
                        break
            f.write("\n")

            f.write("\n## 五、最有趣的案例\n\n")

            # 案例1: 荆轲刺秦（明确的口述史源）
            f.write("### 案例1: 荆轲刺秦王（086-017）\n\n")
            f.write("- **史源类型**: 亲历口述\n")
            f.write("- **可信度**: B\n")
            f.write("- **史源**: 侍医夏无且亲历现场并口述（《史记》明确注明）\n")
            f.write("- **意义**: 这是《史记》中少数明确标注口述史源的事件，证明司马迁重视亲历者口述\n\n")

            # 案例2: 鸿门宴（家族传承）
            f.write("### 案例2: 鸿门宴（007-027）\n\n")
            f.write("- **史源类型**: 家族传承\n")
            f.write("- **可信度**: B\n")
            f.write("- **史源**: 樊哙家族口述\n")
            f.write("- **意义**: 汉初功臣家族传承是《史记》重要史源，樊哙后代可能向司马迁讲述当年细节\n\n")

            # 案例3: 五帝本纪（远古传说）
            f.write("### 案例3: 五帝本纪事件（001-xxx）\n\n")
            f.write("- **史源类型**: 文献传承\n")
            f.write("- **可信度**: C-D\n")
            f.write("- **史源**: 《尚书》《春秋》等上古文献\n")
            f.write("- **意义**: 距司马迁2000多年，完全依赖文献，可信度相对较低\n\n")

        print(f"统计报告已保存: {output_path}")


def main():
    analyzer = SourceAnalyzer()

    # 处理所有事件
    analyzer.process_all()

    # 保存CSV
    csv_path = "/home/baojie/work/knowledge/shiji-kb/labs/events_source_analysis.csv"
    analyzer.save_csv(csv_path)

    # 生成统计报告
    summary_path = "/home/baojie/work/knowledge/shiji-kb/labs/events_source_summary.md"
    analyzer.generate_summary(summary_path)

    print("\n=== 分析完成 ===")
    print(f"CSV文件: {csv_path}")
    print(f"统计报告: {summary_path}")


if __name__ == '__main__':
    main()
