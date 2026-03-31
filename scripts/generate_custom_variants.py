#!/usr/bin/env python3
"""
生成特殊词汇繁简对照表

通过比较以下两个来源来构造特殊词汇对照表：
1. OpenCC 标准转换结果
2. 维基文库繁体版本

识别出 OpenCC 转换不准确的词汇，生成自定义对照表。

输出：docs/data/custom-variants.json
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher

try:
    import opencc
    OPENCC_AVAILABLE = True
except ImportError:
    OPENCC_AVAILABLE = False
    print("警告: opencc-python 未安装，请运行: pip install opencc-python-reimplemented")


def load_simplified_text(chapter_num):
    """加载简体文本"""
    chapter_file = Path(f"archive/chapter/{chapter_num:03d}_*.txt")
    files = list(Path("archive/chapter").glob(f"{chapter_num:03d}_*.txt"))
    if not files:
        return None

    with open(files[0], 'r', encoding='utf-8') as f:
        return f.read()


def load_wikisource_text(chapter_num):
    """加载维基文库繁体HTML，提取纯文本"""
    html_file = Path(f"archive/wikisource_shiji/{chapter_num:03d}_*.html")
    files = list(Path("archive/wikisource_shiji").glob(f"{chapter_num:03d}_*.html"))
    if not files:
        return None

    with open(files[0], 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 简单的 HTML 清理（提取文本）
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', '', html_content)
    # 移除多余空白
    text = re.sub(r'\s+', '', text)

    return text


def convert_with_opencc(text):
    """使用 OpenCC 进行简体→繁体转换"""
    if not OPENCC_AVAILABLE:
        return None

    converter = opencc.OpenCC('s2t.json')  # 简体到繁体
    return converter.convert(text)


def extract_differences(simp_text, opencc_result, wiki_text, min_length=2, max_length=10):
    """
    提取 OpenCC 转换与维基文库不一致的词汇

    返回：{简体词: 繁体词} 字典
    """
    if not opencc_result or not wiki_text:
        return {}

    # 移除所有空白，便于对比
    simp_clean = re.sub(r'\s+', '', simp_text)
    opencc_clean = re.sub(r'\s+', '', opencc_result)
    wiki_clean = re.sub(r'\s+', '', wiki_text)

    variants = {}

    # 使用滑动窗口查找不一致的词汇片段
    for length in range(max_length, min_length - 1, -1):  # 优先匹配长词
        i = 0
        while i < len(simp_clean) - length + 1:
            simp_word = simp_clean[i:i+length]

            # 在 wiki 文本中找到对应位置
            if i < len(wiki_clean) - length + 1:
                wiki_word = wiki_clean[i:i+length]
                opencc_word = opencc_clean[i:i+length] if i < len(opencc_clean) - length + 1 else None

                # 如果 OpenCC 结果与维基文库不同，记录下来
                if opencc_word and wiki_word != opencc_word:
                    # 只记录包含汉字的词汇
                    if re.search(r'[\u4e00-\u9fff]', simp_word):
                        if simp_word not in variants:
                            variants[simp_word] = wiki_word
                            print(f"  发现差异: {simp_word} -> OpenCC:{opencc_word} vs Wiki:{wiki_word}")

            i += 1

    return variants


def analyze_chapter(chapter_num):
    """分析单个章节，提取特殊词汇"""
    print(f"\n=== 分析章节 {chapter_num:03d} ===")

    # 加载文本
    simp_text = load_simplified_text(chapter_num)
    if not simp_text:
        print(f"  简体文本未找到")
        return {}

    wiki_text = load_wikisource_text(chapter_num)
    if not wiki_text:
        print(f"  维基文库文本未找到")
        return {}

    # OpenCC 转换
    opencc_result = convert_with_opencc(simp_text)
    if not opencc_result:
        print(f"  OpenCC 转换失败")
        return {}

    # 提取差异
    variants = extract_differences(simp_text, opencc_result, wiki_text)

    print(f"  共提取 {len(variants)} 个特殊词汇")
    return variants


def merge_variants(all_variants):
    """
    合并所有章节的特殊词汇，处理冲突

    规则：
    1. 如果同一个简体词对应多个繁体词，选择出现次数最多的
    2. 如果出现次数相同，保留第一个
    """
    variant_counts = defaultdict(lambda: defaultdict(int))

    # 统计每个简体词对应的繁体词出现次数
    for chapter_variants in all_variants:
        for simp, trad in chapter_variants.items():
            variant_counts[simp][trad] += 1

    # 选择出现次数最多的繁体词
    merged = {}
    for simp, trad_counts in variant_counts.items():
        # 按出现次数降序排序
        best_trad = max(trad_counts.items(), key=lambda x: x[1])[0]
        merged[simp] = best_trad

    return merged


def add_known_variants(variants):
    """
    添加已知的特殊词汇（人工维护）

    这些是史记专用的繁简对应关系，OpenCC 无法正确转换
    """
    known = {
        # 人名相关
        "后稷": "後稷",  # "后"作为人名时用"後"
        "太后": "太後",

        # 地名相关
        "临淄": "臨淄",

        # 官职相关
        "御史": "御史",

        # 常见误转
        "制": "制",  # 不转为"製"
        "复": "復",  # "恢复"的"复"

        # 可以在这里添加更多已知的特殊词汇
    }

    # 合并，已知词汇优先
    return {**variants, **known}


def save_variants(variants, output_file):
    """保存对照表到 JSON 文件"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 按简体词排序
    sorted_variants = dict(sorted(variants.items()))

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_variants, f, ensure_ascii=False, indent=2)

    print(f"\n特殊词汇对照表已保存到: {output_path}")
    print(f"共 {len(sorted_variants)} 条记录")


def main():
    """主函数"""
    if not OPENCC_AVAILABLE:
        print("\n错误: 需要安装 opencc-python-reimplemented")
        print("运行: pip install opencc-python-reimplemented")
        return

    print("史记知识库 - 特殊词汇繁简对照表生成器")
    print("=" * 60)

    # 可以选择分析部分章节或全部章节
    # 这里先分析前10章作为示例
    chapters_to_analyze = range(1, 11)  # 001-010章

    all_variants = []

    for chapter_num in chapters_to_analyze:
        variants = analyze_chapter(chapter_num)
        if variants:
            all_variants.append(variants)

    if not all_variants:
        print("\n未提取到任何特殊词汇")
        return

    # 合并所有章节的结果
    print("\n=== 合并结果 ===")
    merged_variants = merge_variants(all_variants)
    print(f"合并后共 {len(merged_variants)} 个特殊词汇")

    # 添加已知的特殊词汇
    final_variants = add_known_variants(merged_variants)
    print(f"添加已知词汇后共 {len(final_variants)} 个特殊词汇")

    # 保存结果
    output_file = "docs/data/custom-variants.json"
    save_variants(final_variants, output_file)

    # 显示部分结果
    print("\n=== 部分结果示例 ===")
    for i, (simp, trad) in enumerate(list(final_variants.items())[:20]):
        print(f"{simp:10s} -> {trad}")
        if i >= 19:
            break

    if len(final_variants) > 20:
        print(f"... 还有 {len(final_variants) - 20} 条")


if __name__ == '__main__':
    main()
