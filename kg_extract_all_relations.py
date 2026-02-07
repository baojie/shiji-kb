#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从标注的史记章节中提取所有社会关系
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import json

class AllRelationExtractor:
    def __init__(self, chapter_dir):
        self.chapter_dir = Path(chapter_dir)
        # 存储关系
        self.relations = defaultdict(list)

        # 定义所有关系模式
        self.relation_patterns = {
            # 家庭关系
            '父子': [
                (r'@([^@]+)@[^\n]{0,20}父[^\n]{0,5}@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,5}子[^\n]{0,20}@([^@]+)@', 2, 1, '→'),
                (r'@([^@]+)@[^\n]{0,20}生@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,20}之子@([^@]+)@', 1, 2, '→'),
            ],
            '母子': [
                (r'@([^@]+)@[^\n]{0,20}母[^\n]{0,5}@([^@]+)@', 1, 2, '→'),
                (r'母@([^@]+)@[^\n]{0,20}生@([^@]+)@', 1, 2, '→'),
            ],
            '兄弟': [
                (r'@([^@]+)@[^\n]{0,5}兄[^\n]{0,20}@([^@]+)@', 1, 2, '↔'),
                (r'@([^@]+)@[^\n]{0,5}弟[^\n]{0,20}@([^@]+)@', 2, 1, '↔'),
                (r'@([^@]+)@[^\n]{0,5}与@([^@]+)@[^\n]{0,10}兄弟', 0, 0, '↔'),
            ],
            '夫妻': [
                (r'@([^@]+)@[^\n]{0,20}妻[^\n]{0,5}@([^@]+)@', 1, 2, '↔'),
                (r'@([^@]+)@[^\n]{0,20}娶@([^@]+)@', 1, 2, '↔'),
                (r'@([^@]+)@[^\n]{0,5}妃@([^@]+)@', 1, 2, '↔'),
            ],
            '祖孙': [
                (r'@([^@]+)@[^\n]{0,20}祖[^\n]{0,5}@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,20}孙[^\n]{0,5}@([^@]+)@', 2, 1, '→'),
            ],
            '叔侄': [
                (r'@([^@]+)@[^\n]{0,20}叔[^\n]{0,5}@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,20}侄[^\n]{0,5}@([^@]+)@', 2, 1, '→'),
            ],

            # 君臣关系
            '君臣': [
                (r'@([^@]+)@[^\n]{0,20}臣@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,20}事@([^@]+)@', 2, 1, '→'),
                (r'@([^@]+)@[^\n]{0,20}仕@([^@]+)@', 2, 1, '→'),
                (r'@([^@]+)@[^\n]{0,20}相@([^@]+)@', 2, 1, '→'),
                (r'@([^@]+)@[^\n]{0,10}为&([^&]+)&\$([^\$]+)\$', 1, 1, '任'),
            ],

            # 师徒关系
            '师徒': [
                (r'@([^@]+)@[^\n]{0,20}师[^\n]{0,5}@([^@]+)@', 2, 1, '→'),
                (r'@([^@]+)@[^\n]{0,20}弟子@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,5}学[於于][^\n]{0,5}@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,20}授@([^@]+)@', 1, 2, '→'),
            ],

            # 朋友关系
            '朋友': [
                (r'@([^@]+)@[^\n]{0,5}与@([^@]+)@[^\n]{0,10}友', 0, 0, '↔'),
                (r'@([^@]+)@[^\n]{0,5}与@([^@]+)@[^\n]{0,10}善', 0, 0, '↔'),
                (r'@([^@]+)@[^\n]{0,5}与@([^@]+)@[^\n]{0,10}交', 0, 0, '↔'),
                (r'@([^@]+)@[^\n]{0,20}友@([^@]+)@', 0, 0, '↔'),
            ],

            # 敌对关系
            '敌对': [
                (r'@([^@]+)@[^\n]{0,10}攻@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,10}伐@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,10}杀@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,10}灭@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,10}破@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,5}与@([^@]+)@[^\n]{0,10}战', 0, 0, '↔'),
            ],

            # 联盟关系
            '联盟': [
                (r'@([^@]+)@[^\n]{0,5}与@([^@]+)@[^\n]{0,10}盟', 0, 0, '↔'),
                (r'@([^@]+)@[^\n]{0,5}与@([^@]+)@[^\n]{0,10}约', 0, 0, '↔'),
                (r'@([^@]+)@[^\n]{0,5}与@([^@]+)@[^\n]{0,10}合', 0, 0, '↔'),
            ],

            # 推荐/举荐关系
            '推荐': [
                (r'@([^@]+)@[^\n]{0,10}荐@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,10}举@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,10}进@([^@]+)@', 1, 2, '→'),
            ],

            # 封赏关系
            '封赏': [
                (r'@([^@]+)@[^\n]{0,10}封@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,10}赐@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,10}拜@([^@]+)@', 1, 2, '→'),
            ],

            # 辅佐关系
            '辅佐': [
                (r'@([^@]+)@[^\n]{0,10}辅@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,10}佐@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,10}助@([^@]+)@', 1, 2, '→'),
            ],

            # 谋士关系
            '献策': [
                (r'@([^@]+)@[^\n]{0,10}说@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,10}谏@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,10}谋@([^@]+)@', 1, 2, '→'),
            ],

            # 背叛关系
            '背叛': [
                (r'@([^@]+)@[^\n]{0,10}叛@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,10}反@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,10}弑@([^@]+)@', 1, 2, '→'),
            ],

            # 使者关系
            '出使': [
                (r'@([^@]+)@[^\n]{0,10}使[於于]@([^@]+)@', 1, 2, '→'),
                (r'@([^@]+)@[^\n]{0,5}遣@([^@]+)@', 1, 2, '→'),
            ],
        }

    def extract_from_file(self, file_path):
        """从单个文件中提取关系"""
        chapter_name = file_path.stem.replace('.tagged', '')

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 对每种关系类型应用模式
        for rel_type, patterns in self.relation_patterns.items():
            for pattern_data in patterns:
                if len(pattern_data) == 4:
                    pattern, idx1, idx2, direction = pattern_data
                else:
                    pattern, idx1, idx2 = pattern_data
                    direction = '→'

                matches = re.finditer(pattern, content)

                for match in matches:
                    if idx1 == 0 and idx2 == 0:  # 对称关系
                        person1 = match.group(1).strip()
                        person2 = match.group(2).strip()
                    else:
                        try:
                            person1 = match.group(idx1).strip()
                            person2 = match.group(idx2).strip()
                        except:
                            continue

                    # 过滤无效人名
                    if not person1 or not person2:
                        continue
                    if len(person1) > 20 or len(person2) > 20:
                        continue
                    if any(c in person1 for c in ['[', ']', '。', '，', '\n']):
                        continue
                    if any(c in person2 for c in ['[', ']', '。', '，', '\n']):
                        continue

                    # 获取上下文
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    context = content[start:end].replace('\n', ' ')

                    # 添加关系
                    self.relations[rel_type].append({
                        'person1': person1,
                        'person2': person2,
                        'chapter': chapter_name,
                        'context': context,
                        'relation': rel_type,
                        'direction': direction
                    })

    def process_all_files(self):
        """处理所有标注文件"""
        tagged_files = list(self.chapter_dir.glob('*.tagged.md'))
        print(f"发现 {len(tagged_files)} 个标注文件\n")

        for i, file_path in enumerate(tagged_files, 1):
            print(f"[{i}/{len(tagged_files)}] 处理: {file_path.name}")
            self.extract_from_file(file_path)

        print(f"\n提取完成！")

    def deduplicate(self):
        """去重"""
        for rel_type in self.relations:
            seen = set()
            unique_relations = []

            for rel in self.relations[rel_type]:
                # 创建唯一键
                key = (rel['person1'], rel['person2'], rel['relation'])
                if key not in seen:
                    seen.add(key)
                    unique_relations.append(rel)

            self.relations[rel_type] = unique_relations

    def generate_report(self, output_dir):
        """生成关系报告"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 去重
        self.deduplicate()

        # 生成每种关系类型的报告
        filename_map = {
            # 家庭关系
            '父子': '01_家庭关系_父子.md',
            '母子': '02_家庭关系_母子.md',
            '兄弟': '03_家庭关系_兄弟.md',
            '夫妻': '04_家庭关系_夫妻.md',
            '祖孙': '05_家庭关系_祖孙.md',
            '叔侄': '06_家庭关系_叔侄.md',
            # 政治关系
            '君臣': '11_政治关系_君臣.md',
            '推荐': '12_政治关系_推荐.md',
            '封赏': '13_政治关系_封赏.md',
            '辅佐': '14_政治关系_辅佐.md',
            '献策': '15_政治关系_献策.md',
            '背叛': '16_政治关系_背叛.md',
            '出使': '17_政治关系_出使.md',
            # 社会关系
            '师徒': '21_社会关系_师徒.md',
            '朋友': '22_社会关系_朋友.md',
            # 对立关系
            '敌对': '31_对立关系_敌对.md',
            '联盟': '32_对立关系_联盟.md',
        }

        for rel_type, relations in sorted(self.relations.items()):
            if not relations:
                continue

            output_file = output_dir / filename_map.get(rel_type, f'{rel_type}关系.md')

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# 史记{rel_type}关系表\n\n")
                f.write(f"> 关系数量：**{len(relations)}** 对\n")
                f.write(f"> 数据来源：52个已标注章节\n\n")
                f.write("---\n\n")

                # 统计信息
                chapters = set(r['chapter'] for r in relations)
                persons = set()
                for r in relations:
                    persons.add(r['person1'])
                    persons.add(r['person2'])

                f.write("## 统计信息\n\n")
                f.write(f"- 涉及人物：{len(persons)} 人\n")
                f.write(f"- 涉及章节：{len(chapters)} 篇\n")
                f.write(f"- 关系对数：{len(relations)} 对\n\n")

                # 关系表
                f.write("## 关系列表\n\n")
                f.write("| 序号 | 人物1 | 关系 | 人物2 | 出现章节 |\n")
                f.write("|------|-------|------|-------|----------|\n")

                for i, rel in enumerate(sorted(relations, key=lambda x: x['chapter']), 1):
                    direction = rel.get('direction', '→')
                    symbol = f"{direction} ({rel_type})"
                    f.write(f"| {i} | {rel['person1']} | {symbol} | {rel['person2']} | {rel['chapter']} |\n")

                # 详细信息（只显示前50个）
                f.write("\n---\n\n")
                f.write("## 详细信息（前50条）\n\n")

                for i, rel in enumerate(sorted(relations, key=lambda x: x['chapter'])[:50], 1):
                    f.write(f"### {i}. {rel['person1']} → {rel['person2']}\n\n")
                    f.write(f"- **关系类型**：{rel_type}\n")
                    f.write(f"- **出处**：{rel['chapter']}\n")
                    f.write(f"- **上下文**：{rel['context']}\n\n")

            print(f"  生成: {output_file.name} ({len(relations)} 对关系)")

        # 生成汇总报告
        self.generate_summary(output_dir)

        # 生成JSON格式
        self.export_json(output_dir)

        # 生成CSV格式（便于导入数据库）
        self.export_csv(output_dir)

    def generate_summary(self, output_dir):
        """生成汇总报告"""
        summary_file = output_dir / 'README.md'

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# 史记社会关系索引\n\n")
            f.write("> 从52个已标注章节中提取的全部社会关系数据\n\n")
            f.write("---\n\n")

            # 统计总览
            total_relations = sum(len(rels) for rels in self.relations.values())
            all_persons = set()
            for rels in self.relations.values():
                for rel in rels:
                    all_persons.add(rel['person1'])
                    all_persons.add(rel['person2'])

            f.write("## 统计总览\n\n")
            f.write(f"- **关系类型数**：{len(self.relations)} 种\n")
            f.write(f"- **关系总数**：{total_relations} 对\n")
            f.write(f"- **涉及人物**：{len(all_persons)} 人\n\n")

            # 按类别分组统计
            family_rels = ['父子', '母子', '兄弟', '夫妻', '祖孙', '叔侄']
            political_rels = ['君臣', '推荐', '封赏', '辅佐', '献策', '背叛', '出使']
            social_rels = ['师徒', '朋友']
            conflict_rels = ['敌对', '联盟']

            categories = {
                '家庭关系': family_rels,
                '政治关系': political_rels,
                '社会关系': social_rels,
                '对立关系': conflict_rels,
            }

            f.write("## 关系分类统计\n\n")

            for category, rel_types in categories.items():
                count = sum(len(self.relations[rt]) for rt in rel_types if rt in self.relations)
                percentage = count / total_relations * 100 if total_relations > 0 else 0
                f.write(f"### {category}\n\n")
                f.write(f"- 总计：{count} 对（{percentage:.1f}%）\n")
                f.write(f"- 类型数：{len([rt for rt in rel_types if rt in self.relations])} 种\n\n")

                f.write("| 关系类型 | 数量 | 占该类比例 |\n")
                f.write("|----------|------|------------|\n")

                for rt in rel_types:
                    if rt in self.relations:
                        rt_count = len(self.relations[rt])
                        rt_percentage = rt_count / count * 100 if count > 0 else 0
                        f.write(f"| {rt} | {rt_count} | {rt_percentage:.1f}% |\n")
                f.write("\n")

            # 完整关系列表
            f.write("## 完整关系列表\n\n")
            f.write("| 序号 | 类别 | 关系类型 | 数量 | 文件 |\n")
            f.write("|------|------|----------|------|------|\n")

            filename_map = {
                '父子': '01_家庭关系_父子.md',
                '母子': '02_家庭关系_母子.md',
                '兄弟': '03_家庭关系_兄弟.md',
                '夫妻': '04_家庭关系_夫妻.md',
                '祖孙': '05_家庭关系_祖孙.md',
                '叔侄': '06_家庭关系_叔侄.md',
                '君臣': '11_政治关系_君臣.md',
                '推荐': '12_政治关系_推荐.md',
                '封赏': '13_政治关系_封赏.md',
                '辅佐': '14_政治关系_辅佐.md',
                '献策': '15_政治关系_献策.md',
                '背叛': '16_政治关系_背叛.md',
                '出使': '17_政治关系_出使.md',
                '师徒': '21_社会关系_师徒.md',
                '朋友': '22_社会关系_朋友.md',
                '敌对': '31_对立关系_敌对.md',
                '联盟': '32_对立关系_联盟.md',
            }

            i = 1
            for category, rel_types in categories.items():
                for rt in rel_types:
                    if rt in self.relations:
                        count = len(self.relations[rt])
                        filename = filename_map.get(rt, f'{rt}关系.md')
                        f.write(f"| {i} | {category} | {rt} | {count} | [{filename}](./{filename}) |\n")
                        i += 1

            f.write("\n## 使用说明\n\n")
            f.write("### 数据格式\n\n")
            f.write("每个关系记录包含：\n")
            f.write("- 人物1（起点）\n")
            f.write("- 关系类型\n")
            f.write("- 人物2（终点）\n")
            f.write("- 关系方向（→单向 / ↔双向）\n")
            f.write("- 出处章节\n")
            f.write("- 原文上下文\n\n")

            f.write("### 应用场景\n\n")
            f.write("1. **社会网络分析**：构建完整的人物关系网络\n")
            f.write("2. **知识图谱**：导入Neo4j等图数据库\n")
            f.write("3. **势力分析**：分析政治派系、联盟与对立\n")
            f.write("4. **历史研究**：辅助历史事件与人物研究\n")
            f.write("5. **数据挖掘**：发现隐藏的社会关系模式\n\n")

            f.write("---\n\n")
            f.write("**生成时间**：自动提取\n")
            f.write("**数据来源**：52个已标注《史记》章节\n")
            f.write("**提取方法**：基于正则表达式的模式匹配\n")

        print(f"\n  生成汇总: README.md")

    def export_json(self, output_dir):
        """导出JSON格式"""
        json_file = output_dir / 'all_relations.json'

        json_data = {
            'metadata': {
                'total_relations': sum(len(rels) for rels in self.relations.values()),
                'relation_types': list(self.relations.keys()),
                'source': '52个已标注史记章节',
            },
            'relations': {}
        }

        for rel_type, rels in self.relations.items():
            json_data['relations'][rel_type] = rels

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"  生成JSON: all_relations.json")

    def export_csv(self, output_dir):
        """导出CSV格式"""
        import csv

        csv_file = output_dir / 'all_relations.csv'

        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['关系类型', '人物1', '人物2', '方向', '章节', '上下文'])

            for rel_type, rels in sorted(self.relations.items()):
                for rel in rels:
                    writer.writerow([
                        rel_type,
                        rel['person1'],
                        rel['person2'],
                        rel.get('direction', '→'),
                        rel['chapter'],
                        rel['context'][:100]  # 限制长度
                    ])

        print(f"  生成CSV: all_relations.csv")

def main():
    print("\n" + "="*60)
    print("史记全部社会关系提取工具")
    print("="*60 + "\n")

    chapter_dir = "/home/baojie/work/shiji-kb/chapter_md"
    output_dir = Path("/home/baojie/work/shiji-kb/relations")

    extractor = AllRelationExtractor(chapter_dir)

    print("第一步：从标注文件中提取关系\n")
    extractor.process_all_files()

    print("\n第二步：生成关系报告\n")
    extractor.generate_report(output_dir)

    print("\n" + "="*60)
    print("关系提取完成！")
    print(f"输出目录：{output_dir}")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
