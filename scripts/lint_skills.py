#!/usr/bin/env python3
"""
Skill质量检查工具

检查Skill文件是否符合SKILL_10f规范。

用法:
    python scripts/lint_skills.py skills/SKILL_03a_实体标注.md
    python scripts/lint_skills.py --all
    python scripts/lint_skills.py --report monthly
"""

import os
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class SkillLinter:
    """Skill质量检查器"""

    def __init__(self, skill_path: str):
        self.skill_path = Path(skill_path)
        self.content = self.skill_path.read_text(encoding='utf-8')
        self.lines = self.content.split('\n')
        self.checks = []
        self.warnings = []
        self.errors = []

    def lint(self) -> Dict:
        """执行所有检查"""
        results = {
            'file': str(self.skill_path),
            'total_lines': len(self.lines),
            'checks': {},
            'warnings': [],
            'errors': [],
            'score': 0
        }

        # 结构检查
        results['checks']['has_frontmatter'] = self.check_frontmatter()
        results['checks']['has_quick_start'] = self.check_quick_start()
        results['checks']['has_tools_section'] = self.check_tools_section()
        results['checks']['has_checklist'] = self.check_checklist()
        results['checks']['has_success_criteria'] = self.check_success_criteria()

        # 长度检查
        results['checks']['length_ok'] = self.check_length()
        results['checks']['quick_start_length_ok'] = self.check_quick_start_length()

        # 链接检查
        results['checks']['script_links_valid'] = self.check_script_links()
        results['checks']['skill_refs_valid'] = self.check_skill_refs()

        # 内容检查
        results['checks']['has_examples'] = self.check_has_examples()

        # 汇总
        results['warnings'] = self.warnings
        results['errors'] = self.errors
        results['score'] = self.calculate_score(results['checks'])

        return results

    def check_frontmatter(self) -> bool:
        """检查是否有YAML frontmatter"""
        if not self.content.startswith('---\n'):
            self.errors.append("缺少YAML frontmatter")
            return False

        # 提取frontmatter
        parts = self.content.split('---\n', 2)
        if len(parts) < 3:
            self.errors.append("YAML frontmatter格式错误")
            return False

        frontmatter = parts[1]
        required_fields = ['name', 'title', 'description']
        for field in required_fields:
            if not re.search(rf'^{field}:', frontmatter, re.MULTILINE):
                self.errors.append(f"frontmatter缺少必需字段: {field}")
                return False

        return True

    def check_quick_start(self) -> bool:
        """检查是否有快速开始章节"""
        pattern = r'^##\s+.*快速开始'
        if not re.search(pattern, self.content, re.MULTILINE):
            self.errors.append('缺少"快速开始"章节')
            return False
        return True

    def check_tools_section(self) -> bool:
        """检查是否有工具与脚本章节"""
        pattern = r'^##\s+.*工具.*脚本'
        if not re.search(pattern, self.content, re.MULTILINE):
            self.warnings.append('建议添加"工具与脚本"章节')
            return False
        return True

    def check_checklist(self) -> bool:
        """检查是否有检查清单"""
        pattern = r'^##\s+.*检查清单'
        if not re.search(pattern, self.content, re.MULTILINE):
            self.warnings.append('建议添加"检查清单"章节')
            return False
        return True

    def check_success_criteria(self) -> bool:
        """检查是否有成功标准"""
        pattern = r'成功标准|Success Criteria'
        if not re.search(pattern, self.content, re.IGNORECASE):
            self.warnings.append("建议明确成功标准")
            return False
        return True

    def check_length(self) -> bool:
        """检查总长度"""
        total_lines = len(self.lines)
        if total_lines > 600:
            self.warnings.append(f"总长度超标: {total_lines}行 (建议<600行)")
            return False
        return True

    def check_quick_start_length(self) -> bool:
        """检查快速开始章节长度"""
        # 找到快速开始章节
        start_idx = None
        end_idx = None
        for i, line in enumerate(self.lines):
            if re.match(r'^##\s+.*快速开始', line):
                start_idx = i
            elif start_idx is not None and re.match(r'^##\s+', line):
                end_idx = i
                break

        if start_idx is None:
            return True  # 已在check_quick_start中报错

        if end_idx is None:
            end_idx = len(self.lines)

        quick_start_lines = end_idx - start_idx
        if quick_start_lines > 150:
            self.warnings.append(f"快速开始章节过长: {quick_start_lines}行 (建议<150行)")
            return False

        return True

    def check_script_links(self) -> bool:
        """检查脚本路径是否存在"""
        # 查找所有脚本引用（如 scripts/xxx.py）
        script_pattern = r'`(scripts/[^`]+\.py)`'
        scripts = re.findall(script_pattern, self.content)

        all_valid = True
        for script in scripts:
            script_path = Path(script)
            if not script_path.exists():
                self.warnings.append(f"脚本不存在: {script}")
                all_valid = False

        return all_valid

    def check_skill_refs(self) -> bool:
        """检查Skill引用是否有效"""
        # 查找所有Skill引用（如 SKILL_10a.md）
        skill_pattern = r'`(SKILL_\w+\.md)`'
        skills = re.findall(skill_pattern, self.content)

        all_valid = True
        for skill in skills:
            skill_path = Path('skills') / skill
            if not skill_path.exists():
                self.warnings.append(f"Skill文件不存在: {skill}")
                all_valid = False

        return all_valid

    def check_has_examples(self) -> bool:
        """检查是否有使用示例"""
        # 查找代码块
        code_blocks = re.findall(r'```[\s\S]+?```', self.content)
        if len(code_blocks) < 1:
            self.warnings.append("建议添加使用示例")
            return False
        return True

    def calculate_score(self, checks: Dict) -> int:
        """计算总分"""
        # 权重配置
        weights = {
            'has_frontmatter': 10,
            'has_quick_start': 15,
            'has_tools_section': 10,
            'has_checklist': 10,
            'has_success_criteria': 10,
            'length_ok': 10,
            'quick_start_length_ok': 5,
            'script_links_valid': 10,
            'skill_refs_valid': 10,
            'has_examples': 10,
        }

        score = 0
        max_score = sum(weights.values())

        for check, passed in checks.items():
            if passed:
                score += weights.get(check, 0)

        return int((score / max_score) * 100)


def lint_skill(skill_path: str) -> Dict:
    """对单个Skill执行lint检查"""
    linter = SkillLinter(skill_path)
    return linter.lint()


def lint_all_skills() -> List[Dict]:
    """对所有Skill执行lint检查"""
    skills_dir = Path('skills')
    skill_files = list(skills_dir.glob('SKILL_*.md'))

    results = []
    for skill_file in skill_files:
        result = lint_skill(str(skill_file))
        results.append(result)

    return results


def print_result(result: Dict):
    """打印单个检查结果"""
    file_name = Path(result['file']).name
    score = result['score']
    total_lines = result['total_lines']

    # 状态符号
    if score >= 90:
        status = "✅ PASS"
        color = "\033[92m"  # 绿色
    elif score >= 70:
        status = "⚠️  WARN"
        color = "\033[93m"  # 黄色
    else:
        status = "❌ FAIL"
        color = "\033[91m"  # 红色

    reset = "\033[0m"

    print(f"{color}{file_name} - {status} (score: {score}/100, {total_lines}行){reset}")

    # 打印错误
    for error in result['errors']:
        print(f"  ❌ 错误: {error}")

    # 打印警告
    for warning in result['warnings']:
        print(f"  ⚠️  警告: {warning}")

    print()


def generate_monthly_report(results: List[Dict]):
    """生成月度报告"""
    print("=" * 60)
    print("Skill质量月度报告")
    print("=" * 60)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"检查文件数: {len(results)}")
    print()

    # 统计
    total_score = sum(r['score'] for r in results)
    avg_score = total_score / len(results) if results else 0

    pass_count = sum(1 for r in results if r['score'] >= 90)
    warn_count = sum(1 for r in results if 70 <= r['score'] < 90)
    fail_count = sum(1 for r in results if r['score'] < 70)

    print(f"平均分数: {avg_score:.1f}/100")
    print(f"通过: {pass_count}, 警告: {warn_count}, 失败: {fail_count}")
    print()

    # 按分数排序
    sorted_results = sorted(results, key=lambda r: r['score'], reverse=True)

    print("-" * 60)
    print("详细结果:")
    print("-" * 60)

    for result in sorted_results:
        print_result(result)

    # 需要关注的Skill
    print("-" * 60)
    print("需要关注的Skill:")
    print("-" * 60)

    for result in sorted_results:
        if result['score'] < 70:
            print(f"- {Path(result['file']).name} (分数: {result['score']})")

    print()


def main():
    parser = argparse.ArgumentParser(description='Skill质量检查工具')
    parser.add_argument('files', nargs='*', help='要检查的Skill文件')
    parser.add_argument('--all', action='store_true', help='检查所有Skill')
    parser.add_argument('--report', choices=['monthly'], help='生成报告')

    args = parser.parse_args()

    if args.all or args.report:
        results = lint_all_skills()
        if args.report == 'monthly':
            generate_monthly_report(results)
        else:
            for result in results:
                print_result(result)
    elif args.files:
        for file_path in args.files:
            result = lint_skill(file_path)
            print_result(result)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
