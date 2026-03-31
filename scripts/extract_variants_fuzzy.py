#!/usr/bin/env python3
"""
使用模糊匹配从维基文库提取繁简转换差异
忽略文本版本和校勘差异，只关注OpenCC未覆盖的繁简转换

策略：
1. 用OpenCC转换简体文本
2. 与维基文库繁体文本进行模糊对齐
3. 只提取单字或短词（2-4字）的转换差异
4. 过滤明显的校勘差异（如数字、人名等）
"""

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from opencc import OpenCC
from difflib import SequenceMatcher
from collections import Counter

# 初始化OpenCC转换器
cc = OpenCC('s2t')

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

def is_likely_variant_not_version(simp_frag, wiki_frag):
    """
    判断是繁简差异还是版本差异

    返回True表示可能是繁简差异，False表示可能是版本/校勘差异
    """
    # 规则1: 长度差异太大，可能是版本差异
    if abs(len(simp_frag) - len(wiki_frag)) > 2:
        return False

    # 规则2: 只包含数字，可能是年份差异
    if simp_frag.isdigit() or wiki_frag.isdigit():
        return False

    # 规则3: 完全不同的字（无共同部首），可能是人名/地名差异
    # 简化版：检查是否有任何相同的字
    simp_chars = set(simp_frag)
    wiki_chars = set(wiki_frag)

    # 如果是单字且完全不同，需要检查是否为已知异体字
    if len(simp_frag) == 1 and len(wiki_frag) == 1:
        # 已知异体字对照表（常见的）
        known_variants = {
            '于': '於', '后': '後', '台': '臺', '历': '歷', '里': '裏',
            '干': '幹', '范': '範', '丑': '醜', '余': '餘', '复': '復',
            '钟': '鐘', '征': '徵', '只': '隻', '发': '發', '游': '遊',
            '云': '雲', '舍': '捨', '采': '採', '制': '製', '表': '錶',
            '准': '準', '困': '睏', '卷': '捲', '克': '剋', '坏': '壞',
            '朴': '樸', '松': '鬆', '板': '闆', '柜': '櫃', '极': '極',
            '欲': '慾', '沈': '瀋', '注': '註', '汇': '匯', '沾': '霑',
            '泄': '洩', '涂': '塗', '准': '準', '凶': '兇', '向': '嚮',
            '叶': '葉', '吁': '籲', '听': '聽', '启': '啟', '咸': '鹹',
            '回': '迴', '团': '糰', '困': '睏', '御': '禦', '志': '誌',
            '恶': '噁', '才': '纔', '扎': '紮', '折': '摺', '系': '繫',
            '咨': '諮', '弦': '絃', '胡': '鬍', '致': '緻', '苏': '囌',
            '蒙': '矇', '药': '藥', '获': '穫', '虫': '蟲', '蜡': '蠟',
            '街': '衘', '冲': '衝', '表': '錶', '象': '像', '谷': '穀',
            '赞': '讚', '适': '適', '郁': '鬱', '采': '採', '钟': '鍾',
            '面': '麵', '丰': '豐', '党': '黨', '即': '卽', '原': '願',
            '厂': '廠', '历': '曆', '琅': '瑯', '锺': '鍾', '措': '錯'
        }

        # 检查是否在已知异体字表中
        if simp_frag in known_variants and wiki_frag == known_variants[simp_frag]:
            return True

        # 如果OpenCC已经正确转换了，说明不需要custom variant
        if cc.convert(simp_frag) == wiki_frag:
            return False

    # 规则4: 2-4字的词，检查相似度
    if 2 <= len(simp_frag) <= 4 and len(wiki_frag) == len(simp_frag):
        # 计算OpenCC转换后与维基版本的相似度
        opencc_result = cc.convert(simp_frag)

        # 如果OpenCC转换结果与维基文库完全一致，说明不需要custom variant
        if opencc_result == wiki_frag:
            return False

        # 如果只有1-2个字不同，可能是繁简差异
        diff_count = sum(1 for a, b in zip(opencc_result, wiki_frag) if a != b)
        if diff_count <= 2:
            return True

    return False

def extract_variants_from_alignment(simp_text, wiki_text, max_word_len=4):
    """
    使用序列对齐提取繁简差异
    """
    # 清理空白
    simp_clean = re.sub(r'\s+', '', simp_text)
    wiki_clean = re.sub(r'\s+', '', wiki_text)

    # OpenCC转换
    opencc_clean = re.sub(r'\s+', '', cc.convert(simp_text))

    variants = {}

    # 使用SequenceMatcher进行模糊对齐
    matcher = SequenceMatcher(None, opencc_clean, wiki_clean)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            # 找到不匹配的片段
            opencc_frag = opencc_clean[i1:i2]
            wiki_frag = wiki_clean[j1:j2]

            # 限制长度
            if len(opencc_frag) > max_word_len or len(wiki_frag) > max_word_len:
                continue

            # 从原始简体文本找对应片段
            # 在原始简体中查找
            simp_frag_candidates = []

            # 尝试在简体文本中定位
            # 策略：在opencc转换前后找对应位置
            context_before = opencc_clean[max(0, i1-10):i1]
            context_after = opencc_clean[i2:min(len(opencc_clean), i2+10)]

            # 在原简体文本中搜索上下文
            simp_context_before = cc.convert(context_before)
            simp_context_after = cc.convert(context_after)

            # 简化策略：直接用当前片段在简体中反查
            # 因为OpenCC是确定性转换，我们可以反推
            for k in range(len(simp_clean)):
                if cc.convert(simp_clean[k:k+len(opencc_frag)]) == opencc_frag:
                    simp_frag = simp_clean[k:k+len(opencc_frag)]

                    # 判断是否为繁简差异
                    if is_likely_variant_not_version(simp_frag, wiki_frag):
                        if simp_frag and wiki_frag:
                            variants[simp_frag] = wiki_frag
                    break

    return variants

def compare_chapter(simp_path, wiki_path):
    """比较单个章节"""
    simp_text = extract_text_from_txt(simp_path)
    wiki_text = extract_text_from_html(wiki_path)

    return extract_variants_from_alignment(simp_text, wiki_text)

def main():
    """主函数"""
    base_dir = Path(__file__).parent.parent
    simp_dir = base_dir / 'archive' / 'chapter'
    wiki_dir = base_dir / 'archive' / 'wikisource_shiji'

    # 统计所有变体的出现频率
    variant_counts = Counter()
    all_variants = {}

    chapter_count = 0

    print("开始提取繁简转换差异...")
    print("=" * 60)

    # 遍历所有章节
    for simp_file in sorted(simp_dir.glob('*.txt')):
        chapter_num = simp_file.stem.split('_')[0]

        # 查找对应的维基文库文件
        wiki_candidates = list(wiki_dir.glob(f'{chapter_num}_*.html'))

        if not wiki_candidates:
            continue

        wiki_file = wiki_candidates[0]

        print(f"\n比较 {simp_file.name} <-> {wiki_file.name}")

        try:
            variants = compare_chapter(simp_file, wiki_file)

            # 统计频率
            for simp, trad in variants.items():
                key = f"{simp}→{trad}"
                variant_counts[key] += 1

                if simp not in all_variants:
                    all_variants[simp] = trad
                elif all_variants[simp] != trad:
                    print(f"  ⚠ 冲突: {simp} -> {all_variants[simp]} vs {trad}")

            chapter_count += 1
            if variants:
                print(f"  ✓ 发现 {len(variants)} 处差异")
                for simp, trad in list(variants.items())[:5]:
                    print(f"    - {simp} -> {trad}")

        except Exception as e:
            print(f"  ✗ 错误: {e}")

    print("\n" + "=" * 60)
    print(f"总计比较 {chapter_count} 章")
    print(f"提取 {len(all_variants)} 条独特转换规则")

    # 按频率排序
    sorted_by_freq = sorted(variant_counts.items(), key=lambda x: x[1], reverse=True)

    print("\n" + "=" * 60)
    print("高频转换差异（出现3次以上）:")
    print("=" * 60)

    high_freq_variants = {}
    for variant_str, count in sorted_by_freq:
        if count >= 3:
            simp, trad = variant_str.split('→')
            high_freq_variants[simp] = trad
            print(f"{simp:8s} -> {trad:8s}  (出现{count}次)")

    # 按长度分类显示
    print("\n" + "=" * 60)
    print("按长度分类:")
    print("=" * 60)

    for length in [4, 3, 2, 1]:
        items = {k: v for k, v in high_freq_variants.items() if len(k) == length}
        if items:
            print(f"\n{length}字词/字 ({len(items)}条):")
            for simp, trad in sorted(items.items()):
                count = variant_counts[f"{simp}→{trad}"]
                print(f"  {simp:6s} -> {trad:6s}  ({count}次)")

    # 保存高频词库
    output_file = base_dir / 'docs' / 'data' / 'custom-variants-extracted.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        # 按长度排序（长的优先）
        sorted_variants = dict(sorted(high_freq_variants.items(),
                                     key=lambda x: (-len(x[0]), x[0])))
        json.dump(sorted_variants, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 高频词库已保存到: {output_file}")
    print(f"  包含 {len(high_freq_variants)} 条规则（出现≥3次）")

    # 同时保存完整词库（包含低频项）
    output_file_full = base_dir / 'docs' / 'data' / 'custom-variants-extracted-full.json'
    with open(output_file_full, 'w', encoding='utf-8') as f:
        sorted_all = dict(sorted(all_variants.items(),
                                key=lambda x: (-len(x[0]), x[0])))
        json.dump(sorted_all, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 完整词库已保存到: {output_file_full}")
    print(f"  包含 {len(all_variants)} 条规则（所有出现）")

if __name__ == '__main__':
    main()
