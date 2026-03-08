#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从标注的史记章节中提取家庭关系
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import json

class FamilyRelationExtractor:
    def __init__(self, chapter_dir):
        self.chapter_dir = Path(chapter_dir)
        # 存储关系: {关系类型: [(人物1, 人物2, 章节, 上下文)]}
        self.relations = defaultdict(list)

        # 定义家庭关系模式
        self.relation_patterns = {
            '父子': [
                (r'@([^@]+)@[^\n]{0,20}父[^\n]{0,5}@([^@]+)@', 1, 2),  # A父B
                (r'@([^@]+)@[^\n]{0,5}子[^\n]{0,20}@([^@]+)@', 2, 1),  # A子B
                (r'@([^@]+)@[^\n]{0,20}生@([^@]+)@', 1, 2),  # A生B
                (r'@([^@]+)@[^\n]{0,20}之子@([^@]+)@', 1, 2),  # A之子B
            ],
            '母子': [
                (r'@([^@]+)@[^\n]{0,20}母[^\n]{0,5}@([^@]+)@', 1, 2),  # A母B
                (r'母@([^@]+)@[^\n]{0,20}生@([^@]+)@', 1, 2),  # 母A生B
            ],
            '兄弟': [
                (r'@([^@]+)@[^\n]{0,5}兄[^\n]{0,20}@([^@]+)@', 1, 2),  # A兄B
                (r'@([^@]+)@[^\n]{0,5}弟[^\n]{0,20}@([^@]+)@', 2, 1),  # A弟B
                (r'@([^@]+)@[^\n]{0,5}与@([^@]+)@[^\n]{0,10}兄弟', 0, 0),  # A与B兄弟
            ],
            '夫妻': [
                (r'@([^@]+)@[^\n]{0,20}妻[^\n]{0,5}@([^@]+)@', 1, 2),  # A妻B
                (r'@([^@]+)@[^\n]{0,20}娶@([^@]+)@', 1, 2),  # A娶B
                (r'@([^@]+)@[^\n]{0,5}妃@([^@]+)@', 1, 2),  # A妃B
            ],
            '祖孙': [
                (r'@([^@]+)@[^\n]{0,20}祖[^\n]{0,5}@([^@]+)@', 1, 2),  # A祖B
                (r'@([^@]+)@[^\n]{0,20}孙[^\n]{0,5}@([^@]+)@', 2, 1),  # A孙B
            ],
            '叔侄': [
                (r'@([^@]+)@[^\n]{0,20}叔[^\n]{0,5}@([^@]+)@', 1, 2),  # A叔B
                (r'@([^@]+)@[^\n]{0,20}侄[^\n]{0,5}@([^@]+)@', 2, 1),  # A侄B
            ],
        }

    def extract_from_file(self, file_path):
        """从单个文件中提取家庭关系"""
        chapter_name = file_path.stem.replace('.tagged', '')

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 对每种关系类型应用模式
        for rel_type, patterns in self.relation_patterns.items():
            for pattern, idx1, idx2 in patterns:
                matches = re.finditer(pattern, content)

                for match in matches:
                    if idx1 == 0 and idx2 == 0:  # 对称关系
                        person1 = match.group(1).strip()
                        person2 = match.group(2).strip()
                    else:
                        person1 = match.group(idx1).strip()
                        person2 = match.group(idx2).strip()

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
                        'relation': rel_type
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
        for rel_type, relations in self.relations.items():
            if not relations:
                continue

            filename_map = {
                '父子': '01_父子关系.md',
                '母子': '02_母子关系.md',
                '兄弟': '03_兄弟关系.md',
                '夫妻': '04_夫妻关系.md',
                '祖孙': '05_祖孙关系.md',
                '叔侄': '06_叔侄关系.md',
            }

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

                # 关系说明
                rel_descriptions = {
                    '父子': '记录父亲→子女的关系（包括"父"、"生"等表述）',
                    '母子': '记录母亲→子女的关系',
                    '兄弟': '记录兄弟关系（包括同父异母、异父同母）',
                    '夫妻': '记录婚姻关系（包括妻、妃、嫔等）',
                    '祖孙': '记录祖辈→孙辈的关系',
                    '叔侄': '记录叔伯→侄子的关系',
                }
                f.write(f"**关系说明**：{rel_descriptions.get(rel_type, '')}\n\n")
                f.write("---\n\n")

                # 关系表
                f.write("## 关系列表\n\n")
                f.write("| 序号 | 人物1 | 关系 | 人物2 | 出现章节 |\n")
                f.write("|------|-------|------|-------|----------|\n")

                for i, rel in enumerate(sorted(relations, key=lambda x: x['chapter']), 1):
                    rel_symbol = {
                        '父子': '→ (父)',
                        '母子': '→ (母)',
                        '兄弟': '↔ (兄弟)',
                        '夫妻': '↔ (夫妻)',
                        '祖孙': '→ (祖)',
                        '叔侄': '→ (叔)',
                    }
                    symbol = rel_symbol.get(rel_type, '→')
                    f.write(f"| {i} | {rel['person1']} | {symbol} | {rel['person2']} | {rel['chapter']} |\n")

                # 详细信息
                f.write("\n---\n\n")
                f.write("## 详细信息\n\n")

                for i, rel in enumerate(sorted(relations, key=lambda x: x['chapter']), 1):
                    f.write(f"### {i}. {rel['person1']} → {rel['person2']}\n\n")
                    f.write(f"- **关系类型**：{rel_type}\n")
                    f.write(f"- **出处**：{rel['chapter']}\n")
                    f.write(f"- **上下文**：{rel['context']}\n\n")

            print(f"  生成: {output_file.name} ({len(relations)} 对关系)")

        # 生成汇总报告
        self.generate_summary(output_dir)

        # 生成JSON格式
        self.export_json(output_dir)

    def generate_summary(self, output_dir):
        """生成汇总报告"""
        summary_file = output_dir / 'README.md'

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# 史记家庭关系索引\n\n")
            f.write("> 从52个已标注章节中提取的家庭关系数据\n\n")
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

            # 各类型统计
            f.write("## 关系类型分布\n\n")
            f.write("| 序号 | 关系类型 | 数量 | 占比 | 文件 |\n")
            f.write("|------|----------|------|------|------|\n")

            filename_map = {
                '父子': '01_父子关系.md',
                '母子': '02_母子关系.md',
                '兄弟': '03_兄弟关系.md',
                '夫妻': '04_夫妻关系.md',
                '祖孙': '05_祖孙关系.md',
                '叔侄': '06_叔侄关系.md',
            }

            sorted_rels = sorted(self.relations.items(),
                               key=lambda x: len(x[1]),
                               reverse=True)

            for i, (rel_type, rels) in enumerate(sorted_rels, 1):
                count = len(rels)
                percentage = count / total_relations * 100 if total_relations > 0 else 0
                filename = filename_map.get(rel_type, f'{rel_type}关系.md')
                f.write(f"| {i} | {rel_type} | {count} | {percentage:.1f}% | [{filename}](./{filename}) |\n")

            f.write("\n## 使用说明\n\n")
            f.write("### 关系类型说明\n\n")
            f.write("- **父子关系**：记录父亲→子女的直系关系\n")
            f.write("- **母子关系**：记录母亲→子女的直系关系\n")
            f.write("- **兄弟关系**：记录兄弟间的平行关系\n")
            f.write("- **夫妻关系**：记录婚姻关系（包括妻、妃等）\n")
            f.write("- **祖孙关系**：记录隔代的直系关系\n")
            f.write("- **叔侄关系**：记录旁系血亲关系\n\n")

            f.write("### 数据格式\n\n")
            f.write("每个关系记录包含：\n")
            f.write("- 人物1（起点）\n")
            f.write("- 关系类型\n")
            f.write("- 人物2（终点）\n")
            f.write("- 出处章节\n")
            f.write("- 原文上下文\n\n")

            f.write("### 应用场景\n\n")
            f.write("1. **家谱构建**：自动生成历史人物家族树\n")
            f.write("2. **知识图谱**：作为图数据库的边数据\n")
            f.write("3. **关系推理**：推导隐含的家族关系\n")
            f.write("4. **社会网络分析**：分析家族势力与联姻\n")
            f.write("5. **数据验证**：对比不同章节的记载一致性\n\n")

            f.write("---\n\n")
            f.write("**生成时间**：自动提取\n")
            f.write("**数据来源**：52个已标注《史记》章节\n")
            f.write("**提取方法**：基于正则表达式的模式匹配\n")

        print(f"\n  生成汇总: README.md")

    def export_json(self, output_dir):
        """导出JSON格式"""
        json_file = output_dir / 'family_relations.json'

        # 转换为JSON友好格式
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

        print(f"  生成JSON: family_relations.json")

def main():
    print("\n" + "="*60)
    print("史记家庭关系提取工具")
    print("="*60 + "\n")

    chapter_dir = "chapter_md"
    output_dir = Path("kg/relations")

    extractor = FamilyRelationExtractor(chapter_dir)

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
