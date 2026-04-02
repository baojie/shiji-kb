#!/usr/bin/env python3
"""
验证10组问题集的互斥性（无交集）

Usage:
    python validate_uniqueness.py --all
    python validate_uniqueness.py --sets set01 set02
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class UniquenessValidator:
    """互斥性验证器"""

    def __init__(self, questions_dir: Path):
        """初始化验证器

        Args:
            questions_dir: 问题集目录路径
        """
        self.questions_dir = questions_dir
        self.all_sets = self._load_all_sets()

    def _load_all_sets(self) -> Dict[str, List[Dict]]:
        """加载所有问题集

        Returns:
            {set_name: [questions]}
        """
        all_sets = {}
        question_files = sorted(self.questions_dir.glob("set*.json"))

        for qf in question_files:
            with open(qf, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_sets[qf.stem] = data.get('questions', [])

        return all_sets

    def check_question_text_duplicates(self) -> Tuple[bool, List[Dict]]:
        """检查问题文本是否有重复

        Returns:
            (是否通过, 重复详情列表)
        """
        question_to_sets = defaultdict(list)

        # 收集所有问题及其所属集合
        for set_name, questions in self.all_sets.items():
            for q in questions:
                question_text = q.get('question', '').strip()
                if question_text:
                    question_to_sets[question_text].append({
                        'set': set_name,
                        'id': q.get('id', 'N/A')
                    })

        # 找出重复的问题
        duplicates = []
        for question_text, locations in question_to_sets.items():
            if len(locations) > 1:
                duplicates.append({
                    'question': question_text,
                    'appears_in': locations
                })

        passed = len(duplicates) == 0
        return passed, duplicates

    def check_question_id_duplicates(self) -> Tuple[bool, List[Dict]]:
        """检查问题ID是否有重复

        Returns:
            (是否通过, 重复详情列表)
        """
        id_to_sets = defaultdict(list)

        for set_name, questions in self.all_sets.items():
            for q in questions:
                qid = q.get('id', '')
                if qid:
                    id_to_sets[qid].append(set_name)

        duplicates = []
        for qid, sets in id_to_sets.items():
            if len(sets) > 1:
                duplicates.append({
                    'id': qid,
                    'appears_in': sets
                })

        passed = len(duplicates) == 0
        return passed, duplicates

    def extract_core_entities(self, question: Dict) -> Set[str]:
        """提取问题的核心实体

        Args:
            question: 问题字典

        Returns:
            核心实体集合
        """
        entities = set()

        # 从keywords字段提取
        keywords = question.get('keywords', [])
        if keywords:
            entities.update(keywords)

        # 从问题文本中提取（简单规则）
        # TODO: 可以使用更复杂的NER方法
        question_text = question.get('question', '')

        # 匹配人名标记 〖@人名〗
        import re
        person_pattern = r'〖@([^〗]+)〗'
        persons = re.findall(person_pattern, question_text)
        entities.update(persons)

        return entities

    def check_core_entity_overlap(self) -> Tuple[bool, List[Dict]]:
        """检查核心实体是否在多个问题集中重复出现

        Returns:
            (是否通过, 重叠详情列表)
        """
        entity_to_sets = defaultdict(set)

        for set_name, questions in self.all_sets.items():
            for q in questions:
                entities = self.extract_core_entities(q)
                for entity in entities:
                    entity_to_sets[entity].add(set_name)

        # 找出出现在多个集合中的实体
        overlaps = []
        for entity, sets in entity_to_sets.items():
            if len(sets) > 1:
                overlaps.append({
                    'entity': entity,
                    'appears_in': sorted(sets)
                })

        # 允许一定程度的实体重叠（如"孔子"可能在多个维度被提问）
        # 但不应过度重叠
        excessive_overlaps = [o for o in overlaps if len(o['appears_in']) >= 3]

        passed = len(excessive_overlaps) == 0
        return passed, overlaps

    def check_answer_similarity(self) -> Tuple[bool, List[Dict]]:
        """检查答案是否有高度相似（简单版本）

        Returns:
            (是否通过, 相似详情列表)
        """
        # TODO: 实现更复杂的答案相似度检测
        # 目前简化为检查答案文本完全相同的情况

        # 需要答案文件，暂时跳过
        return True, []

    def calculate_uniqueness_score(self) -> float:
        """计算整体互斥性得分（0-1）

        Returns:
            互斥性得分，1.0表示完全互斥
        """
        text_passed, text_dups = self.check_question_text_duplicates()
        id_passed, id_dups = self.check_question_id_duplicates()
        entity_passed, entity_overlaps = self.check_core_entity_overlap()

        # 计算得分
        score = 1.0

        if not text_passed:
            # 问题文本重复是严重问题
            score -= 0.5

        if not id_passed:
            # ID重复是中等问题
            score -= 0.2

        if not entity_passed:
            # 实体重叠是轻微问题
            score -= 0.3

        return max(0.0, score)

    def generate_report(self) -> str:
        """生成互斥性验证报告

        Returns:
            报告文本
        """
        report = []
        report.append("# 问题集互斥性验证报告")
        report.append(f"\n## 概览")
        report.append(f"- 问题集数量：{len(self.all_sets)}")

        total_questions = sum(len(questions) for questions in self.all_sets.values())
        report.append(f"- 总问题数：{total_questions}")

        # 1. 问题文本重复检查
        text_passed, text_dups = self.check_question_text_duplicates()
        report.append(f"\n## 1. 问题文本重复检查")
        if text_passed:
            report.append("✓ 通过：所有问题文本唯一，无重复")
        else:
            report.append(f"✗ 失败：发现 {len(text_dups)} 个重复问题")
            report.append("\n### 重复问题详情")
            for dup in text_dups[:10]:  # 只显示前10个
                report.append(f"\n**问题**：{dup['question']}")
                report.append(f"**出现位置**：")
                for loc in dup['appears_in']:
                    report.append(f"  - {loc['set']} ({loc['id']})")
            if len(text_dups) > 10:
                report.append(f"\n... 还有 {len(text_dups) - 10} 个重复问题")

        # 2. 问题ID重复检查
        id_passed, id_dups = self.check_question_id_duplicates()
        report.append(f"\n## 2. 问题ID重复检查")
        if id_passed:
            report.append("✓ 通过：所有问题ID唯一，无重复")
        else:
            report.append(f"✗ 失败：发现 {len(id_dups)} 个重复ID")
            report.append("\n### 重复ID详情")
            for dup in id_dups[:10]:
                report.append(f"- ID {dup['id']} 出现在：{', '.join(dup['appears_in'])}")

        # 3. 核心实体重叠检查
        entity_passed, entity_overlaps = self.check_core_entity_overlap()
        report.append(f"\n## 3. 核心实体重叠检查")
        report.append(f"- 总实体数：{len(entity_overlaps)}")

        # 统计重叠程度
        overlap_2 = [o for o in entity_overlaps if len(o['appears_in']) == 2]
        overlap_3_plus = [o for o in entity_overlaps if len(o['appears_in']) >= 3]

        report.append(f"- 出现在2个集合：{len(overlap_2)}个实体")
        report.append(f"- 出现在3+个集合：{len(overlap_3_plus)}个实体")

        if entity_passed:
            report.append("\n✓ 通过：核心实体重叠在合理范围内")
        else:
            report.append(f"\n△ 警告：{len(overlap_3_plus)}个实体出现在3个以上集合，建议检查")
            report.append("\n### 高频重叠实体（Top 10）")
            top_overlaps = sorted(entity_overlaps, key=lambda x: len(x['appears_in']), reverse=True)[:10]
            for overlap in top_overlaps:
                report.append(f"- {overlap['entity']}：{len(overlap['appears_in'])}个集合 ({', '.join(overlap['appears_in'])})")

        # 4. 整体评估
        score = self.calculate_uniqueness_score()
        report.append(f"\n## 整体评估")
        report.append(f"- 互斥性得分：{score*100:.1f}/100")

        if score >= 0.95:
            report.append("- 评级：优秀 ✓")
            report.append("- 结论：10组问题集互斥性极好，符合设计要求")
        elif score >= 0.85:
            report.append("- 评级：良好 ✓")
            report.append("- 结论：问题集互斥性良好，有少量重叠但可接受")
        elif score >= 0.70:
            report.append("- 评级：及格 △")
            report.append("- 结论：问题集存在一定重叠，建议优化")
        else:
            report.append("- 评级：不及格 ✗")
            report.append("- 结论：问题集重叠严重，需要重新设计")

        return '\n'.join(report)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='验证史记知识库测试问题集的互斥性')
    parser.add_argument('--all', action='store_true', help='验证所有问题集')
    parser.add_argument('--sets', nargs='+', help='指定要验证的问题集（如 set01 set02）')
    parser.add_argument('--questions-dir', type=str,
                       default='../questions',
                       help='问题集目录路径')

    args = parser.parse_args()

    # 确定问题集目录
    script_dir = Path(__file__).parent
    questions_dir = (script_dir / args.questions_dir).resolve()

    if not questions_dir.exists():
        print(f"错误：问题集目录不存在：{questions_dir}")
        sys.exit(1)

    validator = UniquenessValidator(questions_dir)

    if not validator.all_sets:
        print(f"错误：在 {questions_dir} 中没有找到问题集文件")
        sys.exit(1)

    # 生成报告
    report = validator.generate_report()
    print(report)

    # 保存报告
    reports_dir = questions_dir.parent / 'reports'
    reports_dir.mkdir(exist_ok=True)

    report_file = reports_dir / 'uniqueness_report.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n报告已保存至：{report_file}")

    # 返回退出码
    score = validator.calculate_uniqueness_score()
    if score >= 0.85:
        sys.exit(0)  # 成功
    else:
        sys.exit(1)  # 失败


if __name__ == '__main__':
    main()
