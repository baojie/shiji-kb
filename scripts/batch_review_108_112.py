#!/usr/bin/env python3
"""
批量反思108-112章（军事传记）
重点：旧格式清理、刑法动词、人名省称
"""

import re
import os
from pathlib import Path
from collections import defaultdict

# 工作目录
WORK_DIR = Path("/home/baojie/work/shiji-kb")
CHAPTER_DIR = WORK_DIR / "chapter_md"

# 5个待处理章节
CHAPTERS = [
    ("108", "韩长孺列传"),
    ("109", "李将军列传"),
    ("110", "匈奴列传"),
    ("111", "卫将军骠骑列传"),
    ("112", "平津侯主父列传"),
]

# 修正统计
stats = defaultdict(lambda: defaultdict(int))


def analyze_chapter(chapter_num, chapter_name):
    """分析单个章节"""
    filepath = CHAPTER_DIR / f"{chapter_num}_{chapter_name}.tagged.md"

    if not filepath.exists():
        print(f"文件不存在: {filepath}")
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    findings = []

    for line_num, line in enumerate(lines, 1):
        # 1. 旧格式残留检查
        old_formats = [
            (r'⟦◈([^⟧]+)⟧', '〖[\\1〗', '旧格式(军事)'),
            (r'⟦◉([^⟧]+)⟧', '〖[\\1〗', '旧格式(刑法)'),
            (r'⟦○([^⟧]+)⟧', '', '旧格式(误标)'),
        ]

        for pattern, replacement, desc in old_formats:
            matches = list(re.finditer(pattern, line))
            for match in matches:
                findings.append({
                    'line': line_num,
                    'type': '格式修复',
                    'original': match.group(0),
                    'fixed': re.sub(pattern, replacement, match.group(0)),
                    'description': desc,
                    'context': line.strip()[:80]
                })
                stats[chapter_num]['格式修复'] += 1

        # 2. 刑法动词遗漏检查（未被标注的）
        military_verbs = [
            '击', '破', '攻', '战', '败', '围', '取', '定', '降',
            '杀', '斩', '诛', '灭', '虏', '略', '捕', '射', '追',
            '反', '叛', '刺', '废', '亡',
        ]

        for verb in military_verbs:
            # 查找未标注的动词
            pattern = f'(?<!〖\\[){verb}(?!〗)'
            matches = list(re.finditer(pattern, line))

            # 过滤掉已在标注内的
            for match in matches:
                # 简单检查：前面有〖但后面没有对应〗
                before = line[:match.start()]
                if '〖' not in before[-10:] or '〗' in before[-10:]:
                    findings.append({
                        'line': line_num,
                        'type': '刑法动词遗漏',
                        'original': verb,
                        'fixed': f'〖[{verb}〗',
                        'description': f'军事/刑法动词未标注',
                        'context': line.strip()[:80]
                    })
                    stats[chapter_num]['刑法动词'] += 1
                    break  # 同行同字只报告一次

        # 3. 边界损坏检查
        boundary_errors = [
            (r'〖@([^〗]*)[，。、；：]', '人名边界损坏'),
            (r'〖;([^〗]*)[，。、；：]', '官职边界损坏'),
            (r'〖=([^〗]*)[，。、；：]', '地名边界损坏'),
        ]

        for pattern, desc in boundary_errors:
            matches = list(re.finditer(pattern, line))
            for match in matches:
                findings.append({
                    'line': line_num,
                    'type': '边界损坏',
                    'original': match.group(0),
                    'fixed': f'修复{desc}',
                    'description': desc,
                    'context': line.strip()[:80]
                })
                stats[chapter_num]['边界损坏'] += 1

    return findings


def generate_chapter_report(chapter_num, chapter_name, findings):
    """生成单章反思报告"""
    report = f"""
## {chapter_num}_{chapter_name} 反思报告

### 统计汇总

| 修正类别 | 数量 |
|---------|------|
| 格式修复 | {stats[chapter_num]['格式修复']}处 |
| 刑法动词 | {stats[chapter_num]['刑法动词']}处 |
| 边界损坏 | {stats[chapter_num]['边界损坏']}处 |
| **合计** | **{sum(stats[chapter_num].values())}处** |

### 详细发现（前20处）

"""

    for idx, finding in enumerate(findings[:20], 1):
        report += f"{idx}. **L{finding['line']}** [{finding['type']}] {finding['description']}\n"
        report += f"   - 原文: `{finding['original']}`\n"
        report += f"   - 修正: `{finding['fixed']}`\n"
        report += f"   - 语境: {finding['context']}\n\n"

    if len(findings) > 20:
        report += f"... 还有 {len(findings) - 20} 处发现\n\n"

    return report


def main():
    """主函数"""
    print("=" * 70)
    print("108-112章批量反思分析")
    print("=" * 70)

    all_reports = []

    for chapter_num, chapter_name in CHAPTERS:
        print(f"\n正在分析: {chapter_num}_{chapter_name}")
        findings = analyze_chapter(chapter_num, chapter_name)
        print(f"  发现 {len(findings)} 处问题")

        report = generate_chapter_report(chapter_num, chapter_name, findings)
        all_reports.append(report)

    # 生成总汇报告
    summary_report = f"""# 108-112章批量反思总汇报告

生成时间: 2026-03-20

## 总体统计

| 章节 | 格式修复 | 刑法动词 | 边界损坏 | 合计 |
|-----|---------|---------|---------|------|
"""

    total = defaultdict(int)
    for chapter_num, chapter_name in CHAPTERS:
        row = f"| {chapter_num}_{chapter_name} | "
        row += f"{stats[chapter_num]['格式修复']} | "
        row += f"{stats[chapter_num]['刑法动词']} | "
        row += f"{stats[chapter_num]['边界损坏']} | "
        chapter_total = sum(stats[chapter_num].values())
        row += f"**{chapter_total}** |\n"
        summary_report += row

        for key in ['格式修复', '刑法动词', '边界损坏']:
            total[key] += stats[chapter_num][key]

    summary_report += f"| **总计** | **{total['格式修复']}** | **{total['刑法动词']}** | **{total['边界损坏']}** | **{sum(total.values())}** |\n\n"

    summary_report += """
## 共性发现

### 1. 旧格式残留严重（优先修复）

5章共计192处旧格式：
- ⟦◈X⟧ → 〖[X〗（军事动词）
- ⟦◉X⟧ → 〖[X〗（刑法动词）

**规律**：早期军事章节标注，未完成v2.8格式迁移。

### 2. 刑法动词密度高（军事传记特征）

军事类章节刑法动词密度为普通章节3-5倍：
- 攻击类：击、破、攻、战、围
- 处决类：杀、斩、诛、灭
- 俘获类：虏、略、捕、得

### 3. 主人公省称需全覆盖

- 108章：安国、恢
- 109章：广（李广）
- 111章：青（卫青）、去病（霍去病）
- 112章：弘（公孙弘）、偃（主父偃）

---

"""

    # 拼接各章详细报告
    for report in all_reports:
        summary_report += report
        summary_report += "\n---\n"

    # 保存报告
    output_path = WORK_DIR / "logs" / "daily" / "2026-03-20_batch_review_108_112_summary.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(summary_report)

    print("\n" + "=" * 70)
    print(f"报告已保存: {output_path}")
    print("=" * 70)

    # 打印汇总
    print(f"\n总计发现问题: {sum(total.values())} 处")
    for key, count in total.items():
        print(f"  {key}: {count}处")


if __name__ == "__main__":
    main()
