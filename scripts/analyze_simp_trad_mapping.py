#!/usr/bin/env python3
"""
分析《史记》简体文本中的繁简映射关系

统计：
1. 总字符数、独特字符数
2. 一对一映射的字符（简→繁唯一）
3. 一对多映射的字符（简→繁多个，取决于上下文）
4. 详细列举不能一一映射的字及其所有可能的繁体形式
"""

import sys
import os
import json
from collections import defaultdict, Counter
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from opencc import OpenCC
except ImportError:
    print("错误：需要安装 opencc-python-reimplemented")
    print("运行：.venv/bin/pip install opencc-python-reimplemented")
    sys.exit(1)


def load_shiji_text():
    """加载所有《史记》章节文本"""
    text_dir = project_root / "archive" / "chapter"
    all_text = ""

    for txt_file in sorted(text_dir.glob("*.txt")):
        with open(txt_file, 'r', encoding='utf-8') as f:
            all_text += f.read()

    return all_text


def analyze_char_mapping(text):
    """分析字符的繁简映射关系"""
    cc = OpenCC('s2t')

    # 统计每个简体字符出现的频率
    char_freq = Counter(text)

    # 只保留汉字（Unicode CJK范围）
    def is_cjk(char):
        code = ord(char)
        return (0x4E00 <= code <= 0x9FFF or  # CJK Unified Ideographs
                0x3400 <= code <= 0x4DBF or  # CJK Extension A
                0x20000 <= code <= 0x2A6DF)  # CJK Extension B

    chinese_chars = {char: freq for char, freq in char_freq.items() if is_cjk(char)}

    # 分析每个字符的转换结果
    # 简体字 → [所有可能的繁体字]
    simp_to_trad_all = defaultdict(set)

    for char in chinese_chars.keys():
        # 单字转换
        trad_single = cc.convert(char)
        simp_to_trad_all[char].add(trad_single)

        # 在不同上下文中的转换（采样前后各2个字）
        # 在实际文本中查找该字的所有出现位置
        for i, c in enumerate(text):
            if c == char:
                # 提取上下文（前后各2个字）
                start = max(0, i - 2)
                end = min(len(text), i + 3)
                context = text[start:end]

                # 转换上下文
                trad_context = cc.convert(context)

                # 提取转换后该字符的位置
                char_pos = i - start
                if char_pos < len(trad_context):
                    trad_char = trad_context[char_pos]
                    simp_to_trad_all[char].add(trad_char)

    return chinese_chars, simp_to_trad_all


def classify_mappings(simp_to_trad_all):
    """分类映射关系"""
    one_to_one = {}      # 一对一映射
    one_to_many = {}     # 一对多映射
    unchanged = {}       # 繁简相同

    for simp, trad_set in simp_to_trad_all.items():
        trad_list = sorted(trad_set)

        if len(trad_list) == 1:
            trad = trad_list[0]
            if simp == trad:
                unchanged[simp] = trad
            else:
                one_to_one[simp] = trad
        else:
            one_to_many[simp] = trad_list

    return one_to_one, one_to_many, unchanged


def generate_report(chinese_chars, one_to_one, one_to_many, unchanged):
    """生成统计报告"""
    report = []

    report.append("=" * 80)
    report.append("《史记》繁简映射关系统计报告")
    report.append("=" * 80)
    report.append("")

    # 一、总体统计
    report.append("## 一、总体统计")
    report.append("")
    total_chars = sum(chinese_chars.values())
    unique_chars = len(chinese_chars)
    report.append(f"- 总字符数（汉字）: {total_chars:,} 字")
    report.append(f"- 独特字符数: {unique_chars:,} 个")
    report.append("")

    # 二、映射关系分类
    report.append("## 二、映射关系分类")
    report.append("")

    unchanged_count = len(unchanged)
    one_to_one_count = len(one_to_one)
    one_to_many_count = len(one_to_many)

    report.append(f"1. **繁简相同**（无需转换）: {unchanged_count} 个 ({unchanged_count/unique_chars*100:.1f}%)")
    report.append(f"2. **一对一映射**（简→繁唯一）: {one_to_one_count} 个 ({one_to_one_count/unique_chars*100:.1f}%)")
    report.append(f"3. **一对多映射**（简→繁多个，上下文相关）: {one_to_many_count} 个 ({one_to_many_count/unique_chars*100:.1f}%)")
    report.append("")

    # 三、一对多映射详细列表
    report.append("## 三、一对多映射详细列表（不能一一映射的字）")
    report.append("")
    report.append("这些字符在不同上下文中会转换为不同的繁体字：")
    report.append("")

    # 按出现频率排序
    one_to_many_sorted = sorted(
        one_to_many.items(),
        key=lambda x: chinese_chars[x[0]],
        reverse=True
    )

    report.append("| 序号 | 简体 | 所有繁体形式 | 出现次数 | 说明 |")
    report.append("|-----|------|------------|---------|------|")

    for idx, (simp, trad_list) in enumerate(one_to_many_sorted, 1):
        trad_str = "、".join(trad_list)
        freq = chinese_chars[simp]

        # 添加说明（常见的上下文相关字）
        explanation = get_explanation(simp, trad_list)

        report.append(f"| {idx} | {simp} | {trad_str} | {freq} | {explanation} |")

    report.append("")

    # 四、典型案例分析
    report.append("## 四、典型案例分析")
    report.append("")

    # 选择几个典型的一对多映射进行详细分析
    typical_cases = get_typical_cases(one_to_many, chinese_chars)

    for case in typical_cases:
        report.append(f"### {case['simp']} → {'/'.join(case['trad_list'])}")
        report.append("")
        report.append(f"**出现频率**: {case['freq']} 次")
        report.append("")
        report.append("**上下文规则**:")
        for rule in case['rules']:
            report.append(f"- {rule}")
        report.append("")

    # 五、统计图表
    report.append("## 五、分布统计")
    report.append("")
    report.append("```")
    report.append("映射关系分布:")
    report.append("")
    report.append(f"  繁简相同    {unchanged_count:>5} 个  {'█' * int(unchanged_count/unique_chars*50)}")
    report.append(f"  一对一映射  {one_to_one_count:>5} 个  {'█' * int(one_to_one_count/unique_chars*50)}")
    report.append(f"  一对多映射  {one_to_many_count:>5} 个  {'█' * int(one_to_many_count/unique_chars*50)}")
    report.append("```")
    report.append("")

    return "\n".join(report)


def get_explanation(simp, trad_list):
    """获取字符的说明"""
    explanations = {
        '后': '皇后/太后用"后"，时间用"後"',
        '历': '经历用"歷"，历法用"曆"',
        '干': '干戈用"干"，相干用"干"',
        '里': '里程用"里"，里面用"裏"',
        '台': '台阁用"臺"，天台用"台"',
        '于': '介词用"於"，姓氏用"于"',
        '复': '恢复用"復"，重复用"複"',
        '发': '发射用"發"，头发用"髮"',
        '系': '关系用"係"，系绳用"繫"',
        '征': '出征用"征"，徵兆用"徵"',
        '斗': '斗争用"鬥"，斗量用"斗"',
        '谷': '山谷用"谷"，谷物用"穀"',
        '丰': '丰收用"豐"，丰采用"丰"',
        '姜': '姓氏用"姜"，生姜用"薑"',
        '余': '余下用"餘"，人称用"余"',
        '钟': '时钟用"鐘"，钟情用"鍾"',
        '苏': '苏醒用"蘇"，姓氏用"蘇"',
        '范': '范围用"範"，姓氏用"范"',
        '叶': '叶子用"葉"，姓氏用"葉"',
        '蒙': '蒙蔽用"矇"，蒙古用"蒙"',
    }
    return explanations.get(simp, '上下文相关')


def get_typical_cases(one_to_many, chinese_chars):
    """获取典型案例进行详细分析"""
    cases = []

    # 案例1: 后
    if '后' in one_to_many:
        cases.append({
            'simp': '后',
            'trad_list': one_to_many['后'],
            'freq': chinese_chars['后'],
            'rules': [
                '爵位（皇后、太后、王后）→ 保持"后"',
                '时间/方位（后世、其后、然后）→ 转为"後"',
                '人名（后稷、后羿）→ 转为"後"'
            ]
        })

    # 案例2: 于
    if '于' in one_to_many:
        cases.append({
            'simp': '于',
            'trad_list': one_to_many['于'],
            'freq': chinese_chars['于'],
            'rules': [
                '介词（生于、死于）→ 转为"於"',
                '姓氏（于姓）→ 保持"于"（较少见）'
            ]
        })

    # 案例3: 历
    if '历' in one_to_many:
        cases.append({
            'simp': '历',
            'trad_list': one_to_many['历'],
            'freq': chinese_chars['历'],
            'rules': [
                '经历、历史 → 转为"歷"',
                '历法、历书 → 转为"曆"'
            ]
        })

    # 案例4: 发
    if '发' in one_to_many:
        cases.append({
            'simp': '发',
            'trad_list': one_to_many['发'],
            'freq': chinese_chars['发'],
            'rules': [
                '发射、发展、发现 → 转为"發"',
                '头发、须发 → 转为"髮"'
            ]
        })

    # 案例5: 复
    if '复' in one_to_many:
        cases.append({
            'simp': '复',
            'trad_list': one_to_many['复'],
            'freq': chinese_chars['复'],
            'rules': [
                '恢复、复兴 → 转为"復"',
                '重复、复制 → 转为"複"'
            ]
        })

    return cases


def main():
    print("正在加载《史记》文本...")
    text = load_shiji_text()
    print(f"已加载 {len(text):,} 字符")
    print()

    print("正在分析繁简映射关系...")
    chinese_chars, simp_to_trad_all = analyze_char_mapping(text)
    print(f"发现 {len(chinese_chars):,} 个独特汉字")
    print()

    print("正在分类映射关系...")
    one_to_one, one_to_many, unchanged = classify_mappings(simp_to_trad_all)
    print(f"- 繁简相同: {len(unchanged)} 个")
    print(f"- 一对一映射: {len(one_to_one)} 个")
    print(f"- 一对多映射: {len(one_to_many)} 个")
    print()

    print("正在生成报告...")
    report = generate_report(chinese_chars, one_to_one, one_to_many, unchanged)

    # 保存报告
    output_file = project_root / "doc" / "analysis" / "繁简映射统计报告.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ 报告已保存到: {output_file}")
    print()

    # 保存JSON数据供进一步分析
    json_data = {
        'one_to_one': one_to_one,
        'one_to_many': {k: list(v) for k, v in one_to_many.items()},
        'unchanged': unchanged,
        'frequency': {k: v for k, v in chinese_chars.items() if k in one_to_many}
    }

    json_file = project_root / "doc" / "analysis" / "繁简映射数据.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON数据已保存到: {json_file}")


if __name__ == '__main__':
    main()
