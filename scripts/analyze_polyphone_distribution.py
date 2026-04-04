#!/usr/bin/env python3
"""
《史记》多音字读音分布详尽统计分析

类似"读"字的分析，对史记中的常见多音字进行：
1. 统计每个读音在史记中的出现次数
2. 分析具体使用场景和上下文
3. 验证pypinyin的标注准确性
4. 生成详细的分布报告
"""

import re
import json
from collections import defaultdict, Counter
from pathlib import Path
from pypinyin import pinyin, Style

# 史记文本路径
SHIJI_TEXT = Path("corpus/shiji/史记.简体.txt")
SPECIAL_PRONUNCIATION = Path("docs/data/special-pronunciation.json")

# 重点分析的多音字列表（基于之前的调查）
POLYPHONE_CHARS = {
    # 高频多音字
    "读": {"readings": ["dú", "dòu"], "contexts": ["阅读", "句读"]},
    "王": {"readings": ["wáng", "wàng"], "contexts": ["君王", "称王"]},
    "相": {"readings": ["xiāng", "xiàng"], "contexts": ["互相", "宰相"]},
    "将": {"readings": ["jiāng", "jiàng", "qiāng"], "contexts": ["将要", "将军", "将领"]},
    "行": {"readings": ["xíng", "háng"], "contexts": ["行走", "行列/官职"]},
    "数": {"readings": ["shù", "shǔ", "shuò"], "contexts": ["数字", "计数", "屡次"]},
    "中": {"readings": ["zhōng", "zhòng"], "contexts": ["中央", "中试/击中"]},
    "乘": {"readings": ["chéng", "shèng"], "contexts": ["乘坐", "千乘/战车量词"]},
    "长": {"readings": ["cháng", "zhǎng"], "contexts": ["长久", "年长"]},
    "少": {"readings": ["shǎo", "shào"], "contexts": ["少许", "少年"]},
    "降": {"readings": ["jiàng", "xiáng"], "contexts": ["下降", "投降"]},
    "乐": {"readings": ["lè", "yuè", "yào"], "contexts": ["快乐", "音乐", "喜好"]},
    "好": {"readings": ["hǎo", "hào"], "contexts": ["好坏", "好学/喜好"]},
    "说": {"readings": ["shuō", "shuì", "yuè"], "contexts": ["说话", "游说", "通悦"]},
    "间": {"readings": ["jiān", "jiàn"], "contexts": ["中间", "离间"]},
    "更": {"readings": ["gēng", "gèng"], "contexts": ["更名/改变", "更加"]},
    "传": {"readings": ["chuán", "zhuàn"], "contexts": ["传递", "列传"]},
    "为": {"readings": ["wéi", "wèi"], "contexts": ["作为", "因为"]},
    "朝": {"readings": ["zhāo", "cháo"], "contexts": ["朝夕/早晨", "朝廷/朝见"]},
    "率": {"readings": ["shuài", "lǜ"], "contexts": ["率领", "效率"]},

    # 地名相关
    "会": {"readings": ["huì", "kuài"], "contexts": ["会合", "会稽"]},
    "华": {"readings": ["huá", "huà"], "contexts": ["繁华", "华山/华姓"]},
    "单": {"readings": ["dān", "shàn", "chán"], "contexts": ["单独", "单父/单姓", "单于"]},
    "殽": {"readings": ["xiáo", "yáo"], "contexts": ["殽函", ""]},
    "句": {"readings": ["jù", "gōu"], "contexts": ["句子", "句践/句注"]},

    # 人名姓氏相关
    "召": {"readings": ["zhào", "shào"], "contexts": ["召唤", "召公/召平"]},
    "共": {"readings": ["gòng", "gōng"], "contexts": ["共同", "共工/共伯"]},
    "解": {"readings": ["jiě", "jiè", "xiè"], "contexts": ["解释", "解县", "解狐/姓"]},
    "盖": {"readings": ["gài", "gě", "hé"], "contexts": ["覆盖", "盖公/姓", "通盍"]},
    "仇": {"readings": ["chóu", "qiú"], "contexts": ["仇恨", "仇液/姓"]},
    "缪": {"readings": ["móu", "miào", "liáo"], "contexts": ["绸缪", "缪姓", ""]},
    "尉": {"readings": ["wèi", "yù"], "contexts": ["都尉", "尉氏县"]},
    "华": {"readings": ["huá", "huà"], "contexts": ["繁华", "华姓/华元"]},

    # 官职相关
    "骑": {"readings": ["qí", "jì"], "contexts": ["骑马", "骑都尉/骑士"]},
    "射": {"readings": ["shè", "yè", "shí"], "contexts": ["射箭", "仆射", "无射"]},
    "大": {"readings": ["dà", "dài", "tài"], "contexts": ["大小", "大夫", ""]},
    "卒": {"readings": ["zú", "cù"], "contexts": ["士卒/死亡", "仓卒"]},

    # 其他常见多音字
    "与": {"readings": ["yǔ", "yù", "yú"], "contexts": ["给与", "参与", "通欤"]},
    "复": {"readings": ["fù", "fù"], "contexts": ["恢复", "重复"]},
    "过": {"readings": ["guò", "guō"], "contexts": ["经过", "过国"]},
    "使": {"readings": ["shǐ", "shì"], "contexts": ["使用", "使者"]},
    "应": {"readings": ["yīng", "yìng"], "contexts": ["应当", "应对"]},
    "当": {"readings": ["dāng", "dàng"], "contexts": ["应当", "适当"]},
}

def load_shiji_text():
    """加载史记文本"""
    with open(SHIJI_TEXT, 'r', encoding='utf-8') as f:
        return f.read()

def load_special_pronunciation():
    """加载特殊读音词表"""
    with open(SPECIAL_PRONUNCIATION, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('entries', [])

def extract_contexts(text, char, window=20):
    """提取多音字的上下文"""
    contexts = []
    for match in re.finditer(re.escape(char), text):
        start = max(0, match.start() - window)
        end = min(len(text), match.end() + window)
        context = text[start:end]
        contexts.append({
            'position': match.start(),
            'context': context,
            'before': text[start:match.start()],
            'after': text[match.end():end]
        })
    return contexts

def classify_usage(char, contexts, special_words):
    """根据上下文对多音字用法进行分类"""
    usage_patterns = defaultdict(list)

    # 从特殊读音词表中提取相关词条
    char_words = [w for w in special_words if char in w['text']]

    for ctx in contexts:
        matched = False
        # 检查是否匹配特殊读音词条
        for word_entry in char_words:
            word = word_entry['text']
            if word in ctx['context']:
                pattern = f"{word}({word_entry['context']})"
                usage_patterns[pattern].append(ctx['context'][:50])
                matched = True
                break

        if not matched:
            # 通用分类
            usage_patterns['其他用法'].append(ctx['context'][:50])

    return usage_patterns

def analyze_polyphone(char, info, text, special_words):
    """分析单个多音字"""
    print(f"\n{'='*80}")
    print(f"分析多音字：【{char}】")
    print(f"{'='*80}")

    # 统计出现次数
    total_count = text.count(char)
    print(f"\n📊 基本统计")
    print(f"  总出现次数：{total_count}")

    # 提取上下文
    contexts = extract_contexts(text, char, window=30)
    print(f"  提取上下文：{len(contexts)} 个")

    # 分类用法
    usage_patterns = classify_usage(char, contexts, special_words)

    print(f"\n📋 用法分类（共 {len(usage_patterns)} 类）")
    for pattern, examples in sorted(usage_patterns.items(),
                                   key=lambda x: len(x[1]),
                                   reverse=True)[:10]:
        print(f"  {pattern}：{len(examples)} 次")
        if len(examples) <= 3:
            for ex in examples:
                print(f"    示例：{ex}")

    # 测试pypinyin标注
    print(f"\n🔍 pypinyin标注测试")
    test_contexts = [ctx['context'] for ctx in contexts[:5]]
    for ctx in test_contexts:
        idx = ctx.find(char)
        if idx != -1:
            py = pinyin(ctx, style=Style.TONE)
            if idx < len(py):
                print(f"  {ctx[:30]}... → [{py[idx][0]}]")

    return {
        'char': char,
        'total_count': total_count,
        'usage_patterns': {k: len(v) for k, v in usage_patterns.items()},
        'top_patterns': list(usage_patterns.keys())[:5]
    }

def generate_summary_report(results):
    """生成汇总报告"""
    print(f"\n\n{'='*80}")
    print("《史记》多音字读音分布汇总报告")
    print(f"{'='*80}")

    print(f"\n📈 多音字出现频率排行（Top 20）")
    sorted_results = sorted(results, key=lambda x: x['total_count'], reverse=True)
    for i, r in enumerate(sorted_results[:20], 1):
        char = r['char']
        count = r['total_count']
        patterns = len(r['usage_patterns'])
        print(f"  {i:2d}. 【{char}】 {count:5d}次，{patterns}种用法")

    print(f"\n📊 用法复杂度分析（用法类别数 >= 5）")
    complex_chars = [r for r in results if len(r['usage_patterns']) >= 5]
    for r in sorted(complex_chars, key=lambda x: len(x['usage_patterns']), reverse=True):
        char = r['char']
        patterns = len(r['usage_patterns'])
        print(f"  【{char}】 {patterns}种用法：{', '.join(r['top_patterns'][:3])}...")

    print(f"\n💡 pypinyin处理建议")
    print("  1. 高频多音字（出现>1000次）需要重点关注上下文标注准确性")
    print("  2. 专有名词（人名、地名、官职）应添加到特殊读音词表")
    print("  3. 通假字需要根据文意判断读音")
    print("  4. 部分多音字在史记中只用一种读音，pypinyin默认处理即可")

def main():
    """主函数"""
    print("《史记》多音字读音分布详尽统计分析")
    print("="*80)

    # 加载数据
    print("\n📖 加载数据...")
    text = load_shiji_text()
    special_words = load_special_pronunciation()
    print(f"  史记文本：{len(text)} 字符")
    print(f"  特殊读音词表：{len(special_words)} 条")

    # 分析每个多音字
    results = []
    for char, info in list(POLYPHONE_CHARS.items())[:10]:  # 先分析前10个
        result = analyze_polyphone(char, info, text, special_words)
        results.append(result)

    # 生成汇总报告
    generate_summary_report(results)

    # 保存结果
    output_file = Path("doc/pronunciation/polyphone_analysis_report.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_chars_analyzed': len(results),
                'shiji_total_chars': len(text),
                'special_words_count': len(special_words),
                'analysis_date': '2026-04-01'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n\n✅ 分析完成！结果已保存到：{output_file}")
    print(f"\n📄 详细分析报告可查看上方输出")

if __name__ == "__main__":
    main()
