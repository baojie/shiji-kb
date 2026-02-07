#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从标注的史记章节中提取帝王家谱
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import json

class ImperialGenealogyExtractor:
    def __init__(self, chapter_dir):
        self.chapter_dir = Path(chapter_dir)
        # 存储帝王: {帝王名: {朝代, 称号, 关系列表}}
        self.emperors = {}
        # 存储家族关系
        self.family_relations = defaultdict(list)

        # 定义帝王称号模式（用于识别帝王）
        self.emperor_titles = [
            '帝', '皇帝', '王', '天子', '上', '主', '君', '侯',
            '公', '伯', '子', '男',  # 五等爵位
        ]

        # 朝代映射
        self.dynasty_map = {
            '001_五帝本纪': '五帝',
            '002_夏本纪': '夏',
            '003_殷本纪': '商',
            '004_周本纪': '周',
            '005_秦本纪': '秦',
            '006_秦始皇本纪': '秦',
            '007_项羽本纪': '秦末',
            '008_高祖本纪': '汉',
            '009_吕太后本纪': '汉',
            '010_孝文本纪': '汉',
            '011_孝景本纪': '汉',
            '012_孝武本纪': '汉',
        }

        # 家庭关系模式
        self.relation_patterns = {
            '父子': [
                (r'@([^@]+)@[^\n]{0,20}[为是](.*?)[之]?父', 1, 0, '→', 'parent'),
                (r'@([^@]+)@[^\n]{0,20}父[^\n]{0,5}@([^@]+)@', 1, 2, '→', 'parent'),
                (r'@([^@]+)@[^\n]{0,5}子[^\n]{0,20}@([^@]+)@', 2, 1, '→', 'parent'),
                (r'@([^@]+)@[^\n]{0,20}生@([^@]+)@', 1, 2, '→', 'parent'),
                (r'@([^@]+)@[^\n]{0,20}之子', 1, 0, '→', 'parent_context'),
                (r'子@([^@]+)@', 0, 1, '→', 'child_context'),
            ],
            '母子': [
                (r'@([^@]+)@[^\n]{0,20}母[^\n]{0,5}@([^@]+)@', 1, 2, '→', 'mother'),
                (r'母@([^@]+)@[^\n]{0,20}生@([^@]+)@', 1, 2, '→', 'mother'),
            ],
            '兄弟': [
                (r'@([^@]+)@[^\n]{0,5}[为是][^\n]{0,5}@([^@]+)@[之]?兄', 1, 2, '↔', 'elder_brother'),
                (r'@([^@]+)@[^\n]{0,5}[为是][^\n]{0,5}@([^@]+)@[之]?弟', 2, 1, '↔', 'younger_brother'),
                (r'@([^@]+)@[^\n]{0,5}与@([^@]+)@[^@]{0,10}兄弟', 0, 0, '↔', 'siblings'),
            ],
            '夫妻': [
                (r'@([^@]+)@[^\n]{0,20}[娶迎取立][^\n]{0,10}@([^@]+)@[为]?[妻后妃嫔]', 1, 2, '↔', 'spouse'),
                (r'@([^@]+)@[^\n]{0,5}妻[^\n]{0,5}@([^@]+)@', 1, 2, '↔', 'spouse'),
                (r'@([^@]+)@[^\n]{0,5}配@([^@]+)@', 1, 2, '↔', 'spouse'),
            ],
            '祖孙': [
                (r'@([^@]+)@[^\n]{0,20}祖[^\n]{0,5}@([^@]+)@', 1, 2, '→', 'grandparent'),
                (r'@([^@]+)@[^\n]{0,20}孙[^\n]{0,5}@([^@]+)@', 2, 1, '→', 'grandparent'),
            ],
            '继承': [
                (r'@([^@]+)@[^\n]{0,20}[崩死][^\n]{0,30}[立]@([^@]+)@', 1, 2, '→', 'succession'),
                (r'@([^@]+)@[^\n]{0,20}[立即位][为]?[王帝君]', 1, 0, '→', 'ascension'),
                (r'@([^@]+)@[^\n]{0,5}[崩薨卒][^\n]{0,20}@([^@]+)@[^\n]{0,5}[立即位]', 1, 2, '→', 'succession'),
            ],
        }

    def is_emperor(self, person_name, context):
        """判断是否为帝王"""
        # 如果名字本身包含帝王称号
        for title in ['帝', '王', '公', '侯', '伯']:
            if title in person_name:
                return True

        # 如果上下文中有帝王行为
        emperor_actions = ['立', '即位', '崩', '薨', '践祚', '嗣位', '继位', '在位', '治']
        for action in emperor_actions:
            if action in context:
                return True

        return False

    def extract_from_file(self, file_path):
        """从单个文件中提取帝王家谱"""
        chapter_name = file_path.stem.replace('.tagged', '')
        dynasty = self.dynasty_map.get(chapter_name, '其他')

        print(f"  处理: {chapter_name} ({dynasty})")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取所有@人名@
        all_persons = set(re.findall(r'@([^@]+)@', content))

        # 识别帝王
        for person in all_persons:
            # 获取该人物的上下文
            pattern = re.compile(r'.{0,50}@' + re.escape(person) + r'@.{0,50}')
            contexts = pattern.findall(content)
            context_text = ' '.join(contexts)

            if self.is_emperor(person, context_text):
                if person not in self.emperors:
                    self.emperors[person] = {
                        'name': person,
                        'dynasty': dynasty,
                        'chapters': [],
                        'titles': [],
                        'parents': [],
                        'children': [],
                        'spouses': [],
                        'siblings': [],
                        'succession': [],
                    }

                self.emperors[person]['chapters'].append(chapter_name)

                # 提取称号
                title_pattern = r'@' + re.escape(person) + r'@[^\n]{0,20}[为即立](.*?)[帝王公侯]'
                titles = re.findall(title_pattern, content)
                for title in titles:
                    title = title.strip()
                    if title and len(title) < 10:
                        self.emperors[person]['titles'].append(title)

        # 提取家庭关系
        for rel_type, patterns in self.relation_patterns.items():
            for pattern, idx1, idx2, direction, rel_subtype in patterns:
                matches = re.finditer(pattern, content)

                for match in matches:
                    # 处理不同的索引模式
                    if idx1 == 0 and idx2 == 0:  # 对称关系
                        person1 = match.group(1).strip()
                        person2 = match.group(2).strip()
                    elif idx1 == 0:  # person1来自匹配，person2需要从上下文推断
                        person1 = match.group(1).strip()
                        person2 = None
                    elif idx2 == 0:  # person2来自匹配，person1需要从上下文推断
                        person1 = match.group(1).strip()
                        person2 = None
                    else:
                        person1 = match.group(idx1).strip()
                        person2 = match.group(idx2).strip()

                    # 过滤无效人名
                    if len(person1) > 20 or (person2 and len(person2) > 20):
                        continue
                    if any(c in person1 for c in ['[', ']', '。', '，', '\n', '：']):
                        continue
                    if person2 and any(c in person2 for c in ['[', ']', '。', '，', '\n', '：']):
                        continue

                    # 只保存涉及帝王的关系
                    if person1 in self.emperors or (person2 and person2 in self.emperors):
                        # 获取上下文
                        start = max(0, match.start() - 100)
                        end = min(len(content), match.end() + 100)
                        context = content[start:end].replace('\n', ' ')

                        relation = {
                            'person1': person1,
                            'person2': person2,
                            'type': rel_type,
                            'subtype': rel_subtype,
                            'direction': direction,
                            'chapter': chapter_name,
                            'dynasty': dynasty,
                            'context': context,
                        }

                        self.family_relations[rel_type].append(relation)

                        # 更新帝王记录
                        if person1 in self.emperors and person2:
                            if rel_type == '父子' and rel_subtype in ['parent', 'parent_context']:
                                self.emperors[person1]['children'].append(person2)
                            elif rel_type == '母子':
                                self.emperors[person1]['children'].append(person2)
                            elif rel_type == '夫妻':
                                self.emperors[person1]['spouses'].append(person2)
                            elif rel_type == '兄弟':
                                self.emperors[person1]['siblings'].append(person2)
                            elif rel_type == '继承':
                                self.emperors[person1]['succession'].append(person2)

                        if person2 and person2 in self.emperors:
                            if rel_type == '父子' and rel_subtype in ['parent', 'parent_context']:
                                self.emperors[person2]['parents'].append(person1)
                            elif rel_type == '母子':
                                self.emperors[person2]['parents'].append(person1)
                            elif rel_type == '夫妻':
                                self.emperors[person2]['spouses'].append(person1)
                            elif rel_type == '兄弟':
                                self.emperors[person2]['siblings'].append(person1)

    def process_all_files(self):
        """处理所有本纪文件"""
        benji_files = []
        for i in range(1, 13):
            pattern = f"{i:03d}_*本纪.tagged.md"
            files = list(self.chapter_dir.glob(pattern))
            benji_files.extend(files)

        print(f"\n发现 {len(benji_files)} 个本纪文件\n")

        for file_path in sorted(benji_files):
            self.extract_from_file(file_path)

        print(f"\n提取完成！")
        print(f"  识别帝王: {len(self.emperors)} 位")
        print(f"  提取关系: {sum(len(rels) for rels in self.family_relations.values())} 对")

    def deduplicate(self):
        """去重并整理"""
        for emperor in self.emperors.values():
            emperor['titles'] = list(set(emperor['titles']))
            emperor['parents'] = list(set(emperor['parents']))
            emperor['children'] = list(set(emperor['children']))
            emperor['spouses'] = list(set(emperor['spouses']))
            emperor['siblings'] = list(set(emperor['siblings']))
            emperor['succession'] = list(set(emperor['succession']))

    def generate_reports(self, output_dir):
        """生成家谱报告"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 去重
        self.deduplicate()

        # 按朝代分组
        dynasties = defaultdict(list)
        for emperor in self.emperors.values():
            dynasties[emperor['dynasty']].append(emperor)

        # 生成各朝代家谱
        dynasty_order = ['五帝', '夏', '商', '周', '秦', '秦末', '汉', '其他']

        for dynasty in dynasty_order:
            if dynasty not in dynasties:
                continue

            emperors = sorted(dynasties[dynasty], key=lambda x: x['name'])
            if not emperors:
                continue

            filename = f"{dynasty}朝帝王家谱.md"
            self.generate_dynasty_report(output_dir / filename, dynasty, emperors)

        # 生成总览
        self.generate_summary(output_dir, dynasties, dynasty_order)

        # 生成JSON
        self.export_json(output_dir)

    def generate_dynasty_report(self, output_file, dynasty, emperors):
        """生成单个朝代的家谱报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {dynasty}朝帝王家谱\n\n")
            f.write(f"> 从《史记》本纪中提取的{dynasty}朝帝王世系\n\n")
            f.write("---\n\n")

            f.write("## 统计信息\n\n")
            f.write(f"- **帝王数量**: {len(emperors)} 位\n")

            all_relations = 0
            for emperor in emperors:
                all_relations += len(emperor['parents']) + len(emperor['children'])
                all_relations += len(emperor['spouses']) + len(emperor['siblings'])

            f.write(f"- **家族关系**: {all_relations} 对\n")
            f.write(f"- **数据来源**: 史记本纪章节\n\n")

            f.write("---\n\n")

            # 世系列表
            f.write("## 帝王世系\n\n")
            f.write("| 序号 | 帝王 | 称号 | 父 | 子 | 配偶 | 出处 |\n")
            f.write("|------|------|------|-------|-------|--------|------|\n")

            for i, emperor in enumerate(emperors, 1):
                name = emperor['name']
                titles = '、'.join(emperor['titles'][:3]) if emperor['titles'] else '-'
                parents = '、'.join(emperor['parents']) if emperor['parents'] else '-'
                children = '、'.join(emperor['children'][:5]) if emperor['children'] else '-'
                if len(emperor['children']) > 5:
                    children += '...'
                spouses = '、'.join(emperor['spouses'][:3]) if emperor['spouses'] else '-'
                if len(emperor['spouses']) > 3:
                    spouses += '...'
                chapters = '、'.join(set(emperor['chapters']))

                f.write(f"| {i} | {name} | {titles} | {parents} | {children} | {spouses} | {chapters} |\n")

            # 详细信息
            f.write("\n---\n\n")
            f.write("## 详细世系\n\n")

            for i, emperor in enumerate(emperors, 1):
                f.write(f"### {i}. {emperor['name']}\n\n")

                if emperor['titles']:
                    f.write(f"**称号**: {' / '.join(emperor['titles'])}\n\n")

                f.write(f"**朝代**: {emperor['dynasty']}\n\n")

                if emperor['parents']:
                    f.write(f"**父辈**:\n")
                    for parent in emperor['parents']:
                        f.write(f"- {parent}\n")
                    f.write("\n")

                if emperor['children']:
                    f.write(f"**子嗣** ({len(emperor['children'])}位):\n")
                    for child in emperor['children']:
                        f.write(f"- {child}\n")
                    f.write("\n")

                if emperor['spouses']:
                    f.write(f"**配偶** ({len(emperor['spouses'])}位):\n")
                    for spouse in emperor['spouses']:
                        f.write(f"- {spouse}\n")
                    f.write("\n")

                if emperor['siblings']:
                    f.write(f"**兄弟**: {' / '.join(emperor['siblings'])}\n\n")

                if emperor['succession']:
                    f.write(f"**继承**: {' → '.join(emperor['succession'])}\n\n")

                f.write(f"**出处**: {' / '.join(set(emperor['chapters']))}\n\n")
                f.write("---\n\n")

        print(f"  生成: {output_file.name} ({len(emperors)} 位帝王)")

    def generate_summary(self, output_dir, dynasties, dynasty_order):
        """生成总览报告"""
        summary_file = output_dir / 'README.md'

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# 史记帝王家谱总览\n\n")
            f.write("> 从《史记》十二本纪中提取的历代帝王世系\n\n")
            f.write("---\n\n")

            # 统计总览
            total_emperors = len(self.emperors)
            total_relations = sum(len(rels) for rels in self.family_relations.values())

            f.write("## 统计总览\n\n")
            f.write(f"- **朝代数量**: {len([d for d in dynasty_order if d in dynasties])} 个\n")
            f.write(f"- **帝王总数**: {total_emperors} 位\n")
            f.write(f"- **家族关系**: {total_relations} 对\n")
            f.write(f"- **数据来源**: 史记十二本纪\n\n")

            # 各朝代统计
            f.write("## 各朝代帝王数\n\n")
            f.write("| 朝代 | 帝王数 | 家谱文件 |\n")
            f.write("|------|--------|----------|\n")

            for dynasty in dynasty_order:
                if dynasty not in dynasties:
                    continue
                count = len(dynasties[dynasty])
                filename = f"{dynasty}朝帝王家谱.md"
                f.write(f"| {dynasty} | {count} | [{filename}](./{filename}) |\n")

            f.write("\n## 关系类型分布\n\n")
            f.write("| 关系类型 | 数量 | 占比 |\n")
            f.write("|----------|------|------|\n")

            for rel_type, rels in sorted(self.family_relations.items(),
                                        key=lambda x: len(x[1]),
                                        reverse=True):
                count = len(rels)
                percentage = count / total_relations * 100 if total_relations > 0 else 0
                f.write(f"| {rel_type} | {count} | {percentage:.1f}% |\n")

            # 使用说明
            f.write("\n---\n\n")
            f.write("## 使用说明\n\n")
            f.write("### 数据结构\n\n")
            f.write("每位帝王的记录包含：\n")
            f.write("- **基本信息**: 姓名、称号、朝代\n")
            f.write("- **父辈**: 父亲、母亲\n")
            f.write("- **子嗣**: 所有子女\n")
            f.write("- **配偶**: 皇后、妃嫔\n")
            f.write("- **兄弟**: 同辈关系\n")
            f.write("- **继承**: 继位关系\n")
            f.write("- **出处**: 原文章节\n\n")

            f.write("### 应用场景\n\n")
            f.write("1. **历史研究**: 研究历代帝王世系与继承规律\n")
            f.write("2. **家谱构建**: 自动生成帝王家族树\n")
            f.write("3. **知识图谱**: 作为图数据库的核心节点\n")
            f.write("4. **教育教学**: 辅助历史教学与学习\n")
            f.write("5. **文化传承**: 数字化保存历史文化资料\n\n")

            f.write("### 数据质量说明\n\n")
            f.write("- 数据来源于《史记》原文标注\n")
            f.write("- 使用正则表达式自动提取\n")
            f.write("- 可能存在遗漏或误识别\n")
            f.write("- 建议对照原文进行核对\n\n")

            f.write("---\n\n")
            f.write("**生成时间**: 自动提取\n")
            f.write("**数据来源**: 《史记》十二本纪已标注章节\n")
            f.write("**提取方法**: 基于正则表达式的模式匹配\n")

        print(f"\n  生成汇总: README.md")

    def export_json(self, output_dir):
        """导出JSON格式"""
        json_file = output_dir / 'imperial_genealogy.json'

        # 转换为JSON友好格式
        json_data = {
            'metadata': {
                'total_emperors': len(self.emperors),
                'total_relations': sum(len(rels) for rels in self.family_relations.values()),
                'source': '史记十二本纪',
            },
            'emperors': self.emperors,
            'relations': {}
        }

        for rel_type, rels in self.family_relations.items():
            json_data['relations'][rel_type] = rels

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"  生成JSON: imperial_genealogy.json")

def main():
    print("\n" + "="*60)
    print("史记帝王家谱提取工具")
    print("="*60 + "\n")

    chapter_dir = "/home/baojie/work/shiji-kb/chapter_md"
    output_dir = Path("/home/baojie/work/shiji-kb/genealogy")

    extractor = ImperialGenealogyExtractor(chapter_dir)

    print("第一步：从本纪中提取帝王与关系\n")
    extractor.process_all_files()

    print("\n第二步：生成家谱报告\n")
    extractor.generate_reports(output_dir)

    print("\n" + "="*60)
    print("帝王家谱提取完成！")
    print(f"输出目录：{output_dir}")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
