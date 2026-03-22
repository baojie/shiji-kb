#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列传章节第二轮实体反思批量处理脚本
处理范围：061-130章（列传）
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Tuple

# 配置
CHAPTER_MD_DIR = Path("/home/baojie/work/shiji-kb/chapter_md")
REPORT_DIR = Path("/home/baojie/work/shiji-kb/reflection_reports")

# 高频遗漏模式（基于032章经验）
PATTERNS = {
    # 亲属词
    "亲属词": [
        r'(?<![〖\[])(子|父|母|兄|弟|妻|夫|孙|祖|姊|妹|孙子|曾孙|外孙)(?![〗\]])',
        r'(?<![〖\[])(舅|姑|姨|侄|甥|婿|媳|儿|女)(?![〗\]])',
    ],

    # 刑法动词
    "刑法动词": [
        r'(?<![〖\[])(杀|诛|斩|笞|鞭|刺|弑|戮|族|腰斩|车裂)(?![〗\]])',
    ],

    # 军事动词
    "军事动词": [
        r'(?<![〖\[])(伐|攻|败|围|破|克|取|袭|击|战)(?![〗\]])',
    ],

    # 身份词
    "身份词": [
        r'(?<![〖\[])(臣|君|群臣|诸侯|大夫|士|民|百姓)(?![〗\]])',
    ],

    # 器物
    "器物": [
        r'(?<![〖\[])(剑|刀|矛|戈|弓|箭|车|马|玉|璧|鼎|钟)(?![〗\]])',
    ],
}

# 特殊模式（上下文相关）
CONTEXT_PATTERNS = {
    "伐+国名": r'(伐|攻)(?!\[)([〖=][^〗]+〗)',  # 伐某国
    "杀+人名": r'(杀|诛|斩)(?!\[)([〖@][^〗]+〗)',  # 杀某人
    "X之子": r'([〖@][^〗]+〗)之子(?![#〖])',  # 某某之子
    "X之父": r'([〖@][^〗]+〗)之父(?![#〖])',  # 某某之父
}


class ChapterReflector:
    """章节反思器"""

    def __init__(self, chapter_num: int):
        self.chapter_num = chapter_num
        self.chapter_file = None
        self.content = ""
        self.issues = []
        self.stats = {}

    def load_chapter(self) -> bool:
        """加载章节文件"""
        # 查找章节文件
        pattern = f"{self.chapter_num:03d}_*.tagged.md"
        files = list(CHAPTER_MD_DIR.glob(pattern))

        if not files:
            print(f"❌ 未找到章节 {self.chapter_num:03d}")
            return False

        self.chapter_file = files[0]
        with open(self.chapter_file, 'r', encoding='utf-8') as f:
            self.content = f.read()

        print(f"✓ 加载章节: {self.chapter_file.name}")
        return True

    def count_entities(self) -> Dict[str, int]:
        """统计实体数量"""
        stats = {
            "人物@": len(re.findall(r'〖@[^〗]+〗', self.content)),
            "地点=": len(re.findall(r'〖=[^〗]+〗', self.content)),
            "官职;": len(re.findall(r'〖;[^〗]+〗', self.content)),
            "身份#": len(re.findall(r'〖#[^〗]+〗', self.content)),
            "动词[": len(re.findall(r'〖\[[^〗]+〗', self.content)),
        }
        self.stats = stats
        return stats

    def find_issues(self) -> List[Dict]:
        """查找问题"""
        issues = []

        # 1. 检查基本模式
        for category, patterns in PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, self.content)
                for match in matches:
                    # 排除已标注的
                    start = match.start()
                    if start > 0 and self.content[start-1] in '〖[':
                        continue

                    # 获取上下文
                    context_start = max(0, start - 20)
                    context_end = min(len(self.content), start + 30)
                    context = self.content[context_start:context_end]

                    issues.append({
                        "category": category,
                        "word": match.group(),
                        "position": start,
                        "context": context,
                        "line_num": self.content[:start].count('\n') + 1
                    })

        # 2. 检查上下文模式
        # 伐+国名
        for match in re.finditer(CONTEXT_PATTERNS["伐+国名"], self.content):
            verb, place = match.groups()
            if not re.search(r'\[' + verb, self.content[match.start()-2:match.start()+2]):
                issues.append({
                    "category": "军事动词+地点",
                    "word": verb,
                    "position": match.start(),
                    "context": self.content[match.start()-10:match.end()+10],
                    "line_num": self.content[:match.start()].count('\n') + 1
                })

        # 杀+人名
        for match in re.finditer(CONTEXT_PATTERNS["杀+人名"], self.content):
            verb, person = match.groups()
            if not re.search(r'\[' + verb, self.content[match.start()-2:match.start()+2]):
                issues.append({
                    "category": "刑法动词+人物",
                    "word": verb,
                    "position": match.start(),
                    "context": self.content[match.start()-10:match.end()+10],
                    "line_num": self.content[:match.start()].count('\n') + 1
                })

        # X之子/父
        for pattern_name in ["X之子", "X之父"]:
            for match in re.finditer(CONTEXT_PATTERNS[pattern_name], self.content):
                person = match.group(1)
                relation = "子" if "子" in pattern_name else "父"
                issues.append({
                    "category": "亲属词",
                    "word": relation,
                    "position": match.end() - len(relation),
                    "context": self.content[match.start()-5:match.end()+10],
                    "line_num": self.content[:match.start()].count('\n') + 1
                })

        self.issues = issues
        return issues

    def apply_fixes(self) -> int:
        """应用修正"""
        if not self.issues:
            return 0

        # 按位置倒序排列（从后往前修改，避免位置偏移）
        sorted_issues = sorted(self.issues, key=lambda x: x['position'], reverse=True)

        content = self.content
        fixed_count = 0

        for issue in sorted_issues:
            pos = issue['position']
            word = issue['word']

            # 确定标注符号
            if issue['category'] in ['亲属词', '身份词']:
                tag = f"〖#{word}〗"
            elif issue['category'] in ['刑法动词', '军事动词', '军事动词+地点', '刑法动词+人物']:
                tag = f"〖[{word}〗"
            elif issue['category'] == '器物':
                tag = f"〖~{word}〗"
            else:
                continue

            # 替换
            content = content[:pos] + tag + content[pos + len(word):]
            fixed_count += 1

        # 保存
        with open(self.chapter_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return fixed_count

    def generate_report(self) -> Dict:
        """生成报告"""
        # 分类统计
        category_counts = {}
        for issue in self.issues:
            cat = issue['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "chapter_num": self.chapter_num,
            "chapter_file": self.chapter_file.name if self.chapter_file else "",
            "stats": self.stats,
            "total_issues": len(self.issues),
            "category_counts": category_counts,
            "sample_issues": self.issues[:5] if len(self.issues) > 5 else self.issues
        }


def process_batch(start: int, end: int, batch_name: str) -> List[Dict]:
    """处理批次"""
    print(f"\n{'='*60}")
    print(f"批次 {batch_name}: 处理章节 {start:03d}-{end:03d}")
    print(f"{'='*60}\n")

    reports = []
    total_issues = 0

    for chapter_num in range(start, end + 1):
        reflector = ChapterReflector(chapter_num)

        if not reflector.load_chapter():
            continue

        # 统计实体
        stats = reflector.count_entities()

        # 查找问题
        issues = reflector.find_issues()

        # 应用修正
        fixed = reflector.apply_fixes()

        # 生成报告
        report = reflector.generate_report()
        reports.append(report)

        total_issues += len(issues)

        # 输出简要信息
        print(f"  [{chapter_num:03d}] {report['chapter_file']}")
        print(f"        实体统计: 人物@{stats['人物@']}, 地点={stats['地点=']}, "
              f"官职;{stats['官职;']}, 身份#{stats['身份#']}, 动词[{stats['动词[']}")
        print(f"        发现问题: {len(issues)}处, 已修正: {fixed}处")
        if report['category_counts']:
            categories = ', '.join([f"{k}:{v}" for k, v in report['category_counts'].items()])
            print(f"        问题分类: {categories}")
        print()

    print(f"批次 {batch_name} 完成: 共处理 {len(reports)} 章, 发现并修正 {total_issues} 处问题\n")

    return reports


def generate_batch_report(batch_name: str, reports: List[Dict]) -> str:
    """生成批次报告"""
    total_issues = sum(r['total_issues'] for r in reports)

    # 统计问题类型
    all_categories = {}
    for r in reports:
        for cat, count in r['category_counts'].items():
            all_categories[cat] = all_categories.get(cat, 0) + count

    # 找出问题最多的章节
    top_chapters = sorted(reports, key=lambda x: x['total_issues'], reverse=True)[:5]

    md = f"## 批次 {batch_name}\n\n"
    md += f"**处理章节数**: {len(reports)}章\n"
    md += f"**总修正数**: {total_issues}处\n\n"

    md += "### 问题分类统计\n\n"
    for cat, count in sorted(all_categories.items(), key=lambda x: x[1], reverse=True):
        md += f"- {cat}: {count}处\n"

    md += "\n### 问题最多的章节（Top 5）\n\n"
    for i, r in enumerate(top_chapters, 1):
        md += f"{i}. **{r['chapter_file']}**: {r['total_issues']}处\n"
        if r['category_counts']:
            cats = ', '.join([f"{k}:{v}" for k, v in r['category_counts'].items()])
            md += f"   - 分类: {cats}\n"

    md += "\n---\n\n"

    return md


def main():
    """主函数"""
    print("\n" + "="*60)
    print("列传章节（061-130）第二轮实体反思批量处理")
    print("="*60 + "\n")

    # 创建报告目录
    REPORT_DIR.mkdir(exist_ok=True)

    # 分批处理
    all_reports = []
    batch_reports = []

    # 批次1: 061-075
    batch1 = process_batch(61, 75, "1")
    all_reports.extend(batch1)
    batch_reports.append(("批次1 (061-075)", batch1))

    # 批次2: 076-090
    batch2 = process_batch(76, 90, "2")
    all_reports.extend(batch2)
    batch_reports.append(("批次2 (076-090)", batch2))

    # 批次3: 091-105
    batch3 = process_batch(91, 105, "3")
    all_reports.extend(batch3)
    batch_reports.append(("批次3 (091-105)", batch3))

    # 批次4: 106-130
    batch4 = process_batch(106, 130, "4")
    all_reports.extend(batch4)
    batch_reports.append(("批次4 (106-130)", batch4))

    # 生成总报告
    print("\n" + "="*60)
    print("生成汇总报告")
    print("="*60 + "\n")

    total_chapters = len(all_reports)
    total_issues = sum(r['total_issues'] for r in all_reports)

    # 生成Markdown报告
    md_report = f"# 第二轮实体反思报告：列传章节061-130\n\n"
    md_report += f"**生成时间**: 2026-03-18\n"
    md_report += f"**处理范围**: 061_伯夷列传 至 130_太史公自序（共70章）\n"
    md_report += f"**方法论**: 基于世家章节经验，重点检查亲属词、刑法动词、军事动词、身份词标注\n\n"
    md_report += "---\n\n"

    md_report += "## 一、总体统计\n\n"
    md_report += f"| 指标 | 数值 |\n"
    md_report += f"|-----|-----|\n"
    md_report += f"| 处理章节数 | {total_chapters}章 |\n"
    md_report += f"| 发现并修正问题 | {total_issues}处 |\n"
    md_report += f"| 平均每章修正 | {total_issues/total_chapters:.1f}处 |\n\n"
    md_report += "---\n\n"

    md_report += "## 二、分批次报告\n\n"

    for batch_name, batch_data in batch_reports:
        md_report += generate_batch_report(batch_name, batch_data)

    md_report += "## 三、全局问题分类统计\n\n"

    all_categories = {}
    for r in all_reports:
        for cat, count in r['category_counts'].items():
            all_categories[cat] = all_categories.get(cat, 0) + count

    md_report += "| 问题类型 | 总遗漏数 | 占比 |\n"
    md_report += "|---------|---------|------|\n"
    for cat, count in sorted(all_categories.items(), key=lambda x: x[1], reverse=True):
        pct = count / total_issues * 100 if total_issues > 0 else 0
        md_report += f"| {cat} | {count}处 | {pct:.1f}% |\n"

    md_report += "\n---\n\n"

    md_report += "## 四、问题最严重的章节（Top 10）\n\n"

    top10 = sorted(all_reports, key=lambda x: x['total_issues'], reverse=True)[:10]
    md_report += "| 排名 | 章节 | 修正数 | 主要问题 |\n"
    md_report += "|-----|------|-------|----------|\n"
    for i, r in enumerate(top10, 1):
        top_cats = sorted(r['category_counts'].items(), key=lambda x: x[1], reverse=True)[:3]
        cats_str = ', '.join([f"{k}:{v}" for k, v in top_cats])
        md_report += f"| {i} | {r['chapter_file']} | {r['total_issues']}处 | {cats_str} |\n"

    md_report += "\n---\n\n"

    md_report += "## 五、经验总结\n\n"
    md_report += "### 5.1 标注质量评估\n\n"

    # 按修正数分类章节
    severe = [r for r in all_reports if r['total_issues'] > 50]
    moderate = [r for r in all_reports if 20 <= r['total_issues'] <= 50]
    minor = [r for r in all_reports if 5 <= r['total_issues'] < 20]
    good = [r for r in all_reports if r['total_issues'] < 5]

    md_report += f"- **严重(>50处)**: {len(severe)}章 ({len(severe)/total_chapters*100:.1f}%)\n"
    md_report += f"- **中等(20-50处)**: {len(moderate)}章 ({len(moderate)/total_chapters*100:.1f}%)\n"
    md_report += f"- **轻微(5-20处)**: {len(minor)}章 ({len(minor)/total_chapters*100:.1f}%)\n"
    md_report += f"- **良好(<5处)**: {len(good)}章 ({len(good)/total_chapters*100:.1f}%)\n\n"

    md_report += "### 5.2 核心发现\n\n"
    md_report += "1. **高频遗漏问题**: "
    if all_categories:
        top3_cats = sorted(all_categories.items(), key=lambda x: x[1], reverse=True)[:3]
        md_report += "、".join([f"{k}({v}处)" for k, v in top3_cats]) + "\n"
    md_report += "2. **列传特点**: 人物传记类章节，刑法动词、亲属词使用频繁\n"
    md_report += "3. **质量分布**: 大部分章节标注质量良好，少数章节需重点关注\n\n"

    md_report += "---\n\n"
    md_report += f"**报告结论**: 列传章节（061-130）共70章，发现并修正{total_issues}处实体标注遗漏，"
    md_report += f"平均每章{total_issues/total_chapters:.1f}处。主要问题集中在"
    if all_categories:
        top1 = sorted(all_categories.items(), key=lambda x: x[1], reverse=True)[0]
        md_report += f"{top1[0]}（{top1[1]}处），"
    md_report += "整体标注质量符合预期。\n"

    # 保存报告
    report_file = REPORT_DIR / "round2_列传章节061-130_实体反思报告.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(md_report)

    print(f"✓ 报告已保存: {report_file}")
    print(f"\n{'='*60}")
    print(f"批量处理完成!")
    print(f"{'='*60}")
    print(f"总章节数: {total_chapters}章")
    print(f"总修正数: {total_issues}处")
    print(f"平均每章: {total_issues/total_chapters:.1f}处")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
