#!/usr/bin/env python3
"""
验证问题集的章节覆盖率

Usage:
    python validate_coverage.py --set set01_person_basic
    python validate_coverage.py --all
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import Counter


class CoverageValidator:
    """章节覆盖率验证器"""

    # 史记130章分类
    CHAPTER_RANGES = {
        '本纪': range(1, 13),      # 001-012
        '表': range(13, 23),        # 013-022
        '书': range(23, 31),        # 023-030
        '世家': range(31, 61),      # 031-060
        '列传': range(61, 131),     # 061-130
    }

    TOTAL_CHAPTERS = 130

    def __init__(self, questions_file: Path):
        """初始化验证器

        Args:
            questions_file: 问题集JSON文件路径
        """
        self.questions_file = questions_file
        self.questions = self._load_questions()
        self.covered_chapters = self._extract_covered_chapters()

    def _load_questions(self) -> List[Dict]:
        """加载问题集"""
        with open(self.questions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('questions', [])

    def _extract_covered_chapters(self) -> Set[int]:
        """提取所有被覆盖的章节"""
        chapters = set()
        for q in self.questions:
            target_chapters = q.get('target_chapters', [])
            for ch in target_chapters:
                # 处理 "047" 或 47 格式
                if isinstance(ch, str):
                    ch_num = int(ch.lstrip('0'))
                else:
                    ch_num = int(ch)
                if 1 <= ch_num <= 130:
                    chapters.add(ch_num)
        return chapters

    def calculate_coverage(self) -> Tuple[float, Dict[str, Dict]]:
        """计算覆盖率

        Returns:
            (总覆盖率, 分类覆盖详情)
        """
        total_coverage = len(self.covered_chapters) / self.TOTAL_CHAPTERS

        category_coverage = {}
        for category, chapter_range in self.CHAPTER_RANGES.items():
            covered = self.covered_chapters & set(chapter_range)
            total = len(list(chapter_range))
            rate = len(covered) / total if total > 0 else 0

            category_coverage[category] = {
                'covered': len(covered),
                'total': total,
                'rate': rate,
                'covered_chapters': sorted(covered),
                'uncovered_chapters': sorted(set(chapter_range) - covered)
            }

        return total_coverage, category_coverage

    def count_questions_per_chapter(self) -> Dict[int, int]:
        """统计每个章节的问题数"""
        chapter_counts = Counter()
        for q in self.questions:
            target_chapters = q.get('target_chapters', [])
            for ch in target_chapters:
                if isinstance(ch, str):
                    ch_num = int(ch.lstrip('0'))
                else:
                    ch_num = int(ch)
                if 1 <= ch_num <= 130:
                    chapter_counts[ch_num] += 1
        return dict(chapter_counts)

    def calculate_balance(self) -> Tuple[float, float]:
        """计算分布均衡性

        Returns:
            (平均每章问题数, 标准差)
        """
        counts = self.count_questions_per_chapter()
        all_counts = [counts.get(i, 0) for i in range(1, 131)]

        mean = sum(all_counts) / len(all_counts)

        variance = sum((x - mean) ** 2 for x in all_counts) / len(all_counts)
        std_dev = variance ** 0.5

        return mean, std_dev

    def generate_report(self) -> str:
        """生成覆盖率报告"""
        total_coverage, category_coverage = self.calculate_coverage()
        mean, std_dev = self.calculate_balance()

        report = []
        report.append(f"# 章节覆盖率报告")
        report.append(f"\n## 问题集：{self.questions_file.stem}")
        report.append(f"\n### 总体统计")
        report.append(f"- 总问题数：{len(self.questions)}")
        report.append(f"- 覆盖章节数：{len(self.covered_chapters)}/{self.TOTAL_CHAPTERS} ({total_coverage*100:.1f}%)")
        report.append(f"- 平均每章问题数：{mean:.2f}")
        report.append(f"- 标准差：{std_dev:.2f}")

        # 分类覆盖详情
        for category, stats in category_coverage.items():
            report.append(f"\n### {category}覆盖 ({stats['total']}篇)")
            report.append(f"- 覆盖章节：{stats['covered']}/{stats['total']} ({stats['rate']*100:.1f}%)")

            if stats['uncovered_chapters']:
                uncovered_str = ', '.join([f"{ch:03d}" for ch in stats['uncovered_chapters'][:10]])
                if len(stats['uncovered_chapters']) > 10:
                    uncovered_str += f" ... (共{len(stats['uncovered_chapters'])}个)"
                report.append(f"- 未覆盖：{uncovered_str}")

        # 问题分布热点
        chapter_counts = self.count_questions_per_chapter()
        if chapter_counts:
            top_chapters = sorted(chapter_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            report.append(f"\n### 问题分布热点（Top 10）")
            for ch, count in top_chapters:
                report.append(f"- 第{ch:03d}章：{count}个问题")

        # 覆盖率评估
        report.append(f"\n### 覆盖率评估")
        if total_coverage >= 0.9:
            report.append("✓ 优秀：覆盖率超过90%")
        elif total_coverage >= 0.8:
            report.append("✓ 良好：覆盖率超过80%")
        elif total_coverage >= 0.7:
            report.append("△ 及格：覆盖率超过70%")
        else:
            report.append("✗ 不足：覆盖率低于70%，需要补充")

        # 均衡性评估
        report.append(f"\n### 均衡性评估")
        if std_dev < 1.5:
            report.append("✓ 优秀：问题分布非常均衡")
        elif std_dev < 2.5:
            report.append("✓ 良好：问题分布较均衡")
        elif std_dev < 3.5:
            report.append("△ 一般：问题分布有轻微集中")
        else:
            report.append("✗ 失衡：问题过度集中在少数章节")

        return '\n'.join(report)


def validate_single_set(questions_dir: Path, set_name: str) -> None:
    """验证单个问题集

    Args:
        questions_dir: 问题集目录
        set_name: 问题集名称（如 set01_person_basic）
    """
    questions_file = questions_dir / f"{set_name}.json"

    if not questions_file.exists():
        print(f"错误：问题集文件不存在：{questions_file}")
        return

    validator = CoverageValidator(questions_file)
    report = validator.generate_report()

    # 输出报告
    print(report)

    # 保存报告
    reports_dir = questions_dir.parent / 'reports'
    reports_dir.mkdir(exist_ok=True)

    report_file = reports_dir / f"{set_name}_coverage.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n报告已保存至：{report_file}")


def validate_all_sets(questions_dir: Path) -> None:
    """验证所有问题集"""
    question_files = sorted(questions_dir.glob("set*.json"))

    if not question_files:
        print(f"错误：在 {questions_dir} 中没有找到问题集文件")
        return

    print(f"找到 {len(question_files)} 个问题集，开始验证...\n")

    summary = []
    for qf in question_files:
        set_name = qf.stem
        print(f"{'='*60}")
        print(f"验证：{set_name}")
        print(f"{'='*60}")

        validator = CoverageValidator(qf)
        total_coverage, category_coverage = validator.calculate_coverage()
        mean, std_dev = validator.calculate_balance()

        print(f"覆盖率：{total_coverage*100:.1f}% ({len(validator.covered_chapters)}/130章)")
        print(f"均衡性：均值={mean:.2f}, 标准差={std_dev:.2f}")

        # 保存详细报告
        report = validator.generate_report()
        reports_dir = questions_dir.parent / 'reports'
        reports_dir.mkdir(exist_ok=True)
        report_file = reports_dir / f"{set_name}_coverage.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        summary.append({
            'set_name': set_name,
            'coverage': total_coverage,
            'covered_chapters': len(validator.covered_chapters),
            'mean': mean,
            'std_dev': std_dev
        })

        print(f"详细报告：{report_file}\n")

    # 生成总结报告
    print(f"{'='*60}")
    print("总结报告")
    print(f"{'='*60}")
    print(f"{'问题集':<30} {'覆盖率':<15} {'均衡性(std)':<15}")
    print(f"{'-'*60}")
    for s in summary:
        print(f"{s['set_name']:<30} {s['coverage']*100:>6.1f}% ({s['covered_chapters']:>3}/130)  {s['std_dev']:>6.2f}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='验证史记知识库测试问题集的章节覆盖率')
    parser.add_argument('--set', type=str, help='问题集名称（如 set01_person_basic）')
    parser.add_argument('--all', action='store_true', help='验证所有问题集')
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

    if args.all:
        validate_all_sets(questions_dir)
    elif args.set:
        validate_single_set(questions_dir, args.set)
    else:
        parser.print_help()
        print("\n示例用法：")
        print("  python validate_coverage.py --set set01_person_basic")
        print("  python validate_coverage.py --all")


if __name__ == '__main__':
    main()
