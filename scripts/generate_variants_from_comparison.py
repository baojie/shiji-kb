#!/usr/bin/env python3
"""
通过逐字比较简体底本和维基文库繁体版本，生成 custom-variants.json

工作流程：
1. 加载简体底本（corpus/archive/chapter/*.txt）
2. 加载维基文库繁体HTML，提取纯文本
3. 使用OpenCC标准转换简体→繁体
4. 逐字比较OpenCC结果和维基文库文本
5. 提取差异字符和周边上下文
6. 生成特殊词汇对照表

输出：docs/data/custom-variants.json
"""

import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from difflib import SequenceMatcher

try:
    import opencc
    OPENCC_AVAILABLE = True
except ImportError:
    OPENCC_AVAILABLE = False
    print("警告: opencc-python 未安装")
    print("运行: pip install opencc-python-reimplemented")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("警告: beautifulsoup4 未安装，将使用正则表达式解析HTML")
    print("建议运行: pip install beautifulsoup4")


def load_simplified_text(chapter_num):
    """加载简体底本"""
    files = list(Path("corpus/archive/chapter").glob(f"{chapter_num:03d}_*.txt"))
    if not files:
        return None

    with open(files[0], 'r', encoding='utf-8') as f:
        return f.read()


def extract_text_from_html(html_content):
    """从HTML中提取纯文本"""
    if BS4_AVAILABLE:
        # 使用BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # 移除script和style标签
        for script in soup(["script", "style"]):
            script.decompose()

        # 获取文本
        text = soup.get_text()
    else:
        # 使用正则表达式（粗糙但可用）
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', html_content)

    # 清理空白
    text = re.sub(r'\s+', '', text)
    return text


def load_wikisource_text(chapter_num):
    """加载维基文库繁体HTML，提取纯文本"""
    files = list(Path("corpus/shiji/wikisource_shiji").glob(f"{chapter_num:03d}_*.html"))
    if not files:
        return None

    with open(files[0], 'r', encoding='utf-8') as f:
        html_content = f.read()

    return extract_text_from_html(html_content)


def convert_with_opencc(text):
    """使用OpenCC进行简体→繁体转换"""
    if not OPENCC_AVAILABLE:
        return None

    converter = opencc.OpenCC('s2t.json')
    return converter.convert(text)


def find_char_differences(simp_text, opencc_text, wiki_text):
    """
    逐字比较，找出OpenCC转换与维基文库不同的字符

    返回：{简体字: {繁体字: [(上下文, 位置), ...]}}
    """
    if not opencc_text or not wiki_text:
        return {}

    # 清理空白
    simp_clean = re.sub(r'\s+', '', simp_text)
    opencc_clean = re.sub(r'\s+', '', opencc_text)
    wiki_clean = re.sub(r'\s+', '', wiki_text)

    # 使用SequenceMatcher对齐文本
    matcher = SequenceMatcher(None, opencc_clean, wiki_clean)

    differences = defaultdict(lambda: defaultdict(list))

    # 遍历所有差异块
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            # 字符替换
            opencc_chunk = opencc_clean[i1:i2]
            wiki_chunk = wiki_clean[j1:j2]

            # 只处理单字符差异（忽略插入/删除）
            if len(opencc_chunk) == len(wiki_chunk) == 1:
                # 找到对应的简体字
                if i1 < len(simp_clean):
                    simp_char = simp_clean[i1]
                    opencc_char = opencc_chunk
                    wiki_char = wiki_chunk

                    # 获取上下文（前后各3个字符）
                    context_start = max(0, i1 - 3)
                    context_end = min(len(simp_clean), i1 + 4)
                    context = simp_clean[context_start:context_end]

                    # 记录差异
                    if opencc_char != wiki_char:
                        differences[simp_char][wiki_char].append((context, i1))

    return differences


def extract_variant_words(differences, min_occurrences=2):
    """
    从字符差异中提取词汇级别的变体

    策略：
    1. 对于同一个简体字，如果有多个繁体对应，选择出现次数最多的
    2. 只保留出现次数 >= min_occurrences 的映射
    3. 扩展为词汇（查找包含该字符的常见词）
    """
    variants = {}

    for simp_char, trad_variants in differences.items():
        # 统计每个繁体字的出现次数
        total_count = sum(len(contexts) for contexts in trad_variants.values())

        if total_count >= min_occurrences:
            # 选择出现最多的繁体字
            best_trad = max(trad_variants.items(), key=lambda x: len(x[1]))[0]

            # 单字映射
            if simp_char != best_trad:
                variants[simp_char] = best_trad

                # 尝试扩展为常见词汇
                for contexts, _ in trad_variants[best_trad]:
                    # 提取包含该字符的2-4字词
                    for length in [4, 3, 2]:
                        for i in range(len(contexts) - length + 1):
                            if simp_char in contexts[i:i+length]:
                                word = contexts[i:i+length]
                                # 转换整个词
                                # （这里简化处理，实际应该检查整个词的转换）
                                if simp_char in word and len(word) > 1:
                                    # 只记录高频词
                                    pass  # TODO: 词频统计

    return variants


def analyze_all_chapters(chapter_range=range(1, 131), sample_size=None):
    """
    分析所有章节（或样本）

    Args:
        chapter_range: 要分析的章节范围
        sample_size: 如果指定，只分析前N章作为样本
    """
    if sample_size:
        chapter_range = range(1, sample_size + 1)

    print(f"准备分析章节：{list(chapter_range)[:5]}{'...' if len(chapter_range) > 5 else ''}")
    print(f"总计 {len(chapter_range)} 章\n")

    all_differences = defaultdict(lambda: defaultdict(list))

    for chapter_num in chapter_range:
        print(f"分析章节 {chapter_num:03d}...")

        # 加载文本
        simp_text = load_simplified_text(chapter_num)
        if not simp_text:
            print(f"  ⚠ 跳过：未找到简体文本")
            continue

        wiki_text = load_wikisource_text(chapter_num)
        if not wiki_text:
            print(f"  ⚠ 跳过：未找到维基文库文本")
            continue

        # OpenCC转换
        opencc_text = convert_with_opencc(simp_text)
        if not opencc_text:
            print(f"  ⚠ 跳过：OpenCC转换失败")
            continue

        # 比较差异
        differences = find_char_differences(simp_text, opencc_text, wiki_text)

        if differences:
            print(f"  ✓ 发现 {len(differences)} 个差异字符")

            # 合并到总差异
            for simp_char, trad_variants in differences.items():
                for trad_char, contexts in trad_variants.items():
                    all_differences[simp_char][trad_char].extend(contexts)
        else:
            print(f"  - 无差异")

    return all_differences


def generate_variants_json(all_differences, output_file, min_occurrences=3):
    """
    生成 custom-variants.json

    Args:
        all_differences: 所有章节的差异汇总
        output_file: 输出文件路径
        min_occurrences: 最小出现次数阈值
    """
    print(f"\n生成变体对照表...")
    print(f"最小出现次数阈值: {min_occurrences}")

    variants = {}

    # 统计和筛选
    for simp_char, trad_variants in all_differences.items():
        total_count = sum(len(contexts) for contexts in trad_variants.values())

        if total_count >= min_occurrences:
            # 选择出现最多的繁体字
            best_trad, best_contexts = max(trad_variants.items(), key=lambda x: len(x[1]))

            if simp_char != best_trad:
                count = len(best_contexts)
                variants[simp_char] = best_trad
                print(f"  {simp_char} → {best_trad} ({count}次)")

                # 显示一些上下文示例
                if count <= 3:
                    for ctx, _ in best_contexts[:3]:
                        print(f"    示例: {ctx}")

    # 添加已知的高频词汇变体
    known_variants = get_known_variants()
    print(f"\n添加已知高频词汇变体: {len(known_variants)} 条")

    # 合并（已知变体优先）
    final_variants = {**variants, **known_variants}

    # 排序
    sorted_variants = dict(sorted(final_variants.items()))

    # 保存
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_variants, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 变体对照表已保存: {output_path}")
    print(f"  总计: {len(sorted_variants)} 条映射")
    print(f"  自动提取: {len(variants)} 条")
    print(f"  已知变体: {len(known_variants)} 条")


def get_known_variants():
    """
    已知的高频词汇变体（人工维护）

    这些是史记中确认的特殊转换规则
    """
    return {
        # 时间词
        "后": "後",      # 后世、后代、其后、然后等（时间义）
        "历": "歷",      # 历史、历代、历年、游历等

        # 常用词
        "复": "復",      # 恢复、答复、反复、往复
        "于": "於",      # 于是、生于、在于等

        # 人名相关
        "后稷": "後稷",
        "太后": "太後",
        "皇后": "皇後",
        "王后": "王後",
        "后土": "後土",
        "后羿": "後羿",

        # 时间词组
        "后代": "後代",
        "后世": "後世",
        "后人": "後人",
        "后嗣": "後嗣",
        "其后": "其後",
        "之后": "之後",
        "然后": "然後",
        "此后": "此後",
        "前后": "前後",
        "先后": "先後",

        # 历相关
        "历史": "歷史",
        "历代": "歷代",
        "历年": "歷年",
        "游历": "遊歷",

        # 复相关
        "恢复": "恢復",
        "答复": "答復",
        "反复": "反復",
        "重复": "重複",
        "复辟": "復辟",
        "往复": "往復",
    }


def main():
    """主函数"""
    if not OPENCC_AVAILABLE:
        print("\n错误: 需要安装 opencc-python-reimplemented")
        print("运行: pip install opencc-python-reimplemented")
        return

    print("=" * 60)
    print("史记知识库 - 特殊词汇繁简对照表生成器 v2.0")
    print("通过逐字比较简体底本与维基文库繁体版本")
    print("=" * 60)
    print()

    # 分析策略：先分析前20章，确认效果
    print("阶段1：样本分析（前20章）")
    print("-" * 60)

    all_differences = analyze_all_chapters(sample_size=20)

    if not all_differences:
        print("\n未发现任何差异")
        return

    # 生成对照表
    output_file = "docs/data/custom-variants.json"
    generate_variants_json(all_differences, output_file, min_occurrences=2)

    print("\n" + "=" * 60)
    print("提示：")
    print("1. 如需分析全部130章，修改 sample_size=None")
    print("2. 可通过调整 min_occurrences 参数控制阈值")
    print("3. 查看生成的 JSON 文件，检查转换是否准确")
    print("=" * 60)


if __name__ == '__main__':
    main()
