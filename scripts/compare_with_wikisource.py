#!/usr/bin/env python3
"""
逐字比较当前简体章节文本与维基文库繁体版本，提取OpenCC转换差异
生成custom-variants.json
"""

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict
from opencc import OpenCC

# 初始化OpenCC转换器
cc = OpenCC('s2t')  # 简体到繁体

def extract_text_from_html(html_path):
    """从维基文库HTML提取纯文本"""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # 移除导航、脚本、样式等
    for tag in soup(['nav', 'script', 'style', 'table', 'dl', 'dd', 'img', 'a']):
        tag.decompose()

    # 提取段落文本
    paragraphs = soup.find_all('p')
    text = '\n'.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())

    return text

def extract_text_from_txt(txt_path):
    """从简体txt提取纯文本"""
    with open(txt_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def find_word_level_differences(simp_text, wiki_text, max_word_len=6):
    """
    找出OpenCC转换结果与维基文库的词级差异

    策略：
    1. 用OpenCC转换简体文本
    2. 逐字符比对，找出差异位置
    3. 在差异位置向前向后扩展，尝试找到有意义的词
    """
    opencc_result = cc.convert(simp_text)

    # 清理空白字符以便对齐
    simp_clean = re.sub(r'\s+', '', simp_text)
    opencc_clean = re.sub(r'\s+', '', opencc_result)
    wiki_clean = re.sub(r'\s+', '', wiki_text)

    variants = {}

    # 找出OpenCC转换与维基文库的差异
    min_len = min(len(opencc_clean), len(wiki_clean))

    i = 0
    while i < min_len:
        if opencc_clean[i] != wiki_clean[i]:
            # 发现差异，向后查找连续差异的结尾
            j = i + 1
            while j < min_len and opencc_clean[j] != wiki_clean[j]:
                j += 1

            # 限制差异片段长度，避免大段文本
            if j - i <= max_word_len:
                # 从原始简体文本找对应位置
                # 简单策略：在差异前后各取5个字符作为上下文匹配
                context_len = 5
                start_ctx = max(0, i - context_len)
                end_ctx = min(min_len, j + context_len)

                # 在简体文本中找对应片段
                search_pattern = opencc_clean[start_ctx:end_ctx]
                simp_pos = simp_clean.find(re.sub(r'\s+', '', cc.convert(search_pattern)))

                if simp_pos != -1:
                    # 调整位置
                    simp_start = simp_pos + (i - start_ctx)
                    simp_end = simp_pos + (j - start_ctx)

                    if 0 <= simp_start < len(simp_clean) and simp_end <= len(simp_clean):
                        simp_fragment = simp_clean[simp_start:simp_end]
                        wiki_fragment = wiki_clean[i:j]

                        if simp_fragment and wiki_fragment and simp_fragment != wiki_fragment:
                            variants[simp_fragment] = wiki_fragment

            i = j
        else:
            i += 1

    return variants

def compare_chapter(simp_path, wiki_path):
    """比较单个章节"""
    simp_text = extract_text_from_txt(simp_path)
    wiki_text = extract_text_from_html(wiki_path)

    return find_word_level_differences(simp_text, wiki_text)

def main():
    """主函数：比较所有130章"""
    base_dir = Path(__file__).parent.parent
    simp_dir = base_dir / 'archive' / 'chapter'
    wiki_dir = base_dir / 'archive' / 'wikisource_shiji'
    output_file = base_dir / 'docs' / 'data' / 'custom-variants.json'

    all_variants = {}
    chapter_count = 0
    total_variants = 0

    # 遍历所有章节
    for simp_file in sorted(simp_dir.glob('*.txt')):
        chapter_num = simp_file.stem.split('_')[0]

        # 查找对应的维基文库文件
        wiki_candidates = list(wiki_dir.glob(f'{chapter_num}_*.html'))

        if not wiki_candidates:
            print(f"⚠ 未找到维基文库文件: {chapter_num}")
            continue

        wiki_file = wiki_candidates[0]

        print(f"比较 {simp_file.name} <-> {wiki_file.name}")

        try:
            variants = compare_chapter(simp_file, wiki_file)

            # 合并到总variants，处理冲突
            for simp, trad in variants.items():
                if simp in all_variants:
                    if all_variants[simp] != trad:
                        # 冲突：同一简体对应不同繁体，记录更常见的
                        print(f"  ⚠ 冲突: {simp} -> {all_variants[simp]} vs {trad}")
                        # 简单策略：保留第一个遇到的
                else:
                    all_variants[simp] = trad
                    total_variants += 1

            chapter_count += 1
            print(f"  ✓ 发现 {len(variants)} 处差异")

        except Exception as e:
            print(f"  ✗ 错误: {e}")

    print(f"\n总计比较 {chapter_count} 章")
    print(f"提取 {total_variants} 条独特转换规则")

    # 按字符串长度排序（长的优先，确保词级优先于字级）
    sorted_variants = dict(sorted(all_variants.items(), key=lambda x: (-len(x[0]), x[0])))

    # 保存到JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_variants, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 已保存到: {output_file}")

    # 显示一些示例（按长度分组）
    print("\n示例差异:")

    # 长词（4-6字）
    long_words = {k: v for k, v in sorted_variants.items() if len(k) >= 4}
    if long_words:
        print(f"\n长词（{len(long_words)}条，显示前10条）:")
        for i, (simp, trad) in enumerate(list(long_words.items())[:10], 1):
            print(f"  {i}. {simp} -> {trad}")

    # 双字词
    two_chars = {k: v for k, v in sorted_variants.items() if len(k) == 2}
    if two_chars:
        print(f"\n双字词（{len(two_chars)}条，显示前10条）:")
        for i, (simp, trad) in enumerate(list(two_chars.items())[:10], 1):
            print(f"  {i}. {simp} -> {trad}")

    # 单字
    single_chars = {k: v for k, v in sorted_variants.items() if len(k) == 1}
    if single_chars:
        print(f"\n单字（{len(single_chars)}条，显示前20条）:")
        for i, (simp, trad) in enumerate(list(single_chars.items())[:20], 1):
            print(f"  {i}. {simp} -> {trad}")

if __name__ == '__main__':
    main()
