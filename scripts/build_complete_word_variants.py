#!/usr/bin/env python3
"""
构建完整的繁简词表
对全部130章做分词统计,对照维基文库提取繁体版本,生成完整的繁简对照词表

步骤:
1. 对全部130章做全文分词
2. 统计词频
3. 对照维基文库提取繁体版本
4. 筛选出繁简不同的词,生成词表
"""

import re
import json
from pathlib import Path
from collections import Counter
import jieba
import subprocess

# 配置路径
PROJECT_ROOT = Path("/home/baojie/work/knowledge/shiji-kb")
ORIGINAL_TEXT_DIR = PROJECT_ROOT / "docs" / "original_text"
WIKISOURCE_DIR = PROJECT_ROOT / "archive" / "wikisource_sanjia"
TRADITIONAL_TEXT_FILE = PROJECT_ROOT / "archive" / "史記正文.繁体.txt"
OUTPUT_DIR = PROJECT_ROOT / "doc" / "analysis" / "word"

def load_chapter_text(chapter_id: str) -> str:
    """加载某章的简体原文"""
    files = list(ORIGINAL_TEXT_DIR.glob(f"{chapter_id}_*.txt"))
    if not files:
        return ""
    return files[0].read_text(encoding='utf-8')

def load_wikisource_text(chapter_id: str) -> str:
    """加载某章的维基文库繁体HTML"""
    files = list(WIKISOURCE_DIR.glob(f"{chapter_id}_*.html"))
    if not files:
        return ""
    html = files[0].read_text(encoding='utf-8')

    # 简单提取文本内容(去除HTML标签)
    # 更精确的提取可以使用BeautifulSoup
    text = re.sub(r'<[^>]+>', '', html)
    # 去除HTML实体
    text = re.sub(r'&[a-z]+;', '', text)
    return text

def segment_text(text: str) -> list:
    """对文本进行分词"""
    # 使用jieba分词
    words = jieba.lcut(text)
    # 过滤:只保留长度>=2的词(排除单字和标点)
    words = [w for w in words if len(w) >= 2 and not re.match(r'^[，。；：！？""''（）《》、\s]+$', w)]
    return words

def build_s2t_char_map() -> dict:
    """构建简繁单字映射表"""
    # 常用简繁字对照(可以从OpenCC的字典文件中提取)
    # 这里先用一个基础版本
    s2t_map = {
        '为': '為', '国': '國', '发': '發', '单': '單', '项': '項',
        '汉': '漢', '赵': '趙', '齐': '齊', '来': '來', '杀': '殺',
        '书': '書', '长': '長', '韩': '韓', '孙': '孫', '军': '軍',
        '见': '見', '宾': '賓', '马': '馬', '过': '過', '苏': '蘇',
        '与': '與', '战': '戰', '说': '說', '东': '東', '义': '義',
        '应': '應', '时': '時', '乐': '樂', '务': '務', '当': '當',
        '听': '聽', '实': '實', '宝': '寶', '后': '後', '历': '歷',
        '宁': '寧', '岁': '歲', '礼': '禮', '从': '從', '亲': '親',
        '邓': '鄧', '张': '張', '杨': '楊', '陈': '陳', '周': '週',
        '吴': '吳', '黄': '黃', '卫': '衛', '郑': '鄭', '刘': '劉',
        '关': '關', '庙': '廟', '灵': '靈', '临': '臨', '阳': '陽',
        '廉': '廉', '颇': '頗', '圣': '聖', '万': '萬', '观': '觀',
        '须': '須', '虑': '慮', '边': '邊', '台': '臺', '叶': '葉',
        '刘': '劉', '郑': '鄭', '冯': '馮', '韦': '韋', '袁': '袁',
        '尧': '堯', '舜': '舜', '萧': '蕭', '曹': '曹', '陆': '陸',
        '济': '濟', '渐': '漸', '减': '減', '师': '師', '帅': '帥',
        '归': '歸', '蓝': '藍', '鱼': '魚', '鲁': '魯', '叶': '葉',
        '号': '號', '寻': '尋', '显': '顯', '签': '簽', '县': '縣',
        '贾': '賈', '贺': '賀', '钟': '鍾', '锺': '鍾', '钱': '錢',
        '铁': '鐵', '镇': '鎮', '续': '續', '罗': '羅', '谢': '謝',
        '简': '簡', '编': '編', '纪': '紀', '运': '運', '远': '遠',
        '达': '達', '选': '選', '还': '還', '进': '進', '连': '連',
        '迁': '遷', '宣': '宣', '纷': '紛', '绝': '絕', '续': '續',
        '丝': '絲', '纲': '綱', '网': '網', '罗': '羅', '绕': '繞',
        '练': '練', '经': '經', '织': '織', '维': '維', '纳': '納',
        '纪': '紀', '级': '級', '纷': '紛', '纸': '紙', '绍': '紹',
        '统': '統', '绪': '緒', '综': '綜', '线': '線', '组': '組',
        '细': '細', '织': '織', '终': '終', '绊': '絆', '绍': '紹',
        '经': '經', '结': '結', '绕': '繞', '给': '給', '络': '絡',
        '绝': '絕', '绞': '絞', '统': '統', '继': '繼', '绩': '績',
    }
    return s2t_map

def convert_word_s2t(simplified_word: str, s2t_map: dict) -> str:
    """使用字符映射表转换单词"""
    trad_chars = []
    for char in simplified_word:
        if char in s2t_map:
            trad_chars.append(s2t_map[char])
        else:
            trad_chars.append(char)
    return ''.join(trad_chars)

def build_word_mapping(simplified_words: set, traditional_text: str) -> dict:
    """通过对照繁体文本,为简体词建立繁体映射

    新策略:
    1. 对每个简体词,用简繁字符映射转换为繁体
    2. 在繁体文本中查找转换后的词
    3. 如果找到,确认映射;如果找不到,检查是否繁简相同
    """
    print("  构建简繁字符映射表...")
    s2t_map = build_s2t_char_map()
    print(f"  映射字符数: {len(s2t_map)}")

    # 建立映射
    mapping = {}
    direct_match = 0  # 繁简相同
    converted_match = 0  # 转换后匹配
    not_found = 0  # 未找到

    print(f"\n  处理 {len(simplified_words):,} 个词...")

    for idx, word in enumerate(simplified_words, 1):
        # 先检查是否繁简相同(直接在文本中出现)
        if word in traditional_text:
            mapping[word] = word
            direct_match += 1
        else:
            # 用字符映射转换
            trad_word = convert_word_s2t(word, s2t_map)

            # 检查转换后的词是否在繁体文本中
            if trad_word in traditional_text:
                mapping[word] = trad_word
                converted_match += 1
            else:
                # 找不到,保持原样或标记
                not_found += 1

        if idx % 5000 == 0:
            print(f"    已处理 {idx}/{len(simplified_words)}")

    print(f"\n  映射统计:")
    print(f"    - 繁简相同(直接匹配): {direct_match:,}")
    print(f"    - 转换后匹配: {converted_match:,}")
    print(f"    - 未找到: {not_found:,}")
    print(f"    - 总映射数: {len(mapping):,}")

    return mapping

def step1_segment_all_chapters():
    """步骤1: 对全部130章做分词"""
    print("=" * 60)
    print("步骤1: 对全部130章做全文分词")
    print("=" * 60)

    all_words = []
    chapter_count = 0

    for chapter_id in range(1, 131):
        cid = f"{chapter_id:03d}"
        text = load_chapter_text(cid)
        if not text:
            print(f"⚠️  {cid} 未找到文本文件")
            continue

        words = segment_text(text)
        all_words.extend(words)
        chapter_count += 1

        if chapter_id % 10 == 0:
            print(f"✓ 已处理 {chapter_id}/130 章")

    print(f"\n完成分词:")
    print(f"  - 处理章节: {chapter_count}/130")
    print(f"  - 总词数: {len(all_words):,}")

    # 保存分词结果
    output_file = OUTPUT_DIR / "01_all_words.txt"
    output_file.write_text('\n'.join(all_words), encoding='utf-8')
    print(f"  - 已保存: {output_file}")

    return all_words

def step2_count_word_frequency(all_words: list):
    """步骤2: 统计词频"""
    print("\n" + "=" * 60)
    print("步骤2: 统计词频")
    print("=" * 60)

    word_freq = Counter(all_words)
    total_unique = len(word_freq)

    print(f"\n词频统计:")
    print(f"  - 总词数(含重复): {len(all_words):,}")
    print(f"  - 去重后词数: {total_unique:,}")

    # 按频率分组统计
    freq_1 = sum(1 for w, c in word_freq.items() if c == 1)
    freq_2_5 = sum(1 for w, c in word_freq.items() if 2 <= c <= 5)
    freq_6_10 = sum(1 for w, c in word_freq.items() if 6 <= c <= 10)
    freq_11_plus = sum(1 for w, c in word_freq.items() if c > 10)

    print(f"  - 出现1次: {freq_1:,} 词")
    print(f"  - 出现2-5次: {freq_2_5:,} 词")
    print(f"  - 出现6-10次: {freq_6_10:,} 词")
    print(f"  - 出现11次以上: {freq_11_plus:,} 词")

    # 保存完整词频表
    output_file = OUTPUT_DIR / "02_word_frequency.json"
    freq_dict = {word: count for word, count in word_freq.most_common()}
    output_file.write_text(json.dumps(freq_dict, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"  - 已保存: {output_file}")

    # 保存可读版本(按频率排序)
    output_file_md = OUTPUT_DIR / "02_word_frequency.md"
    lines = ["# 《史记》词频统计表\n"]
    lines.append(f"**统计日期**: 2026-04-01\n")
    lines.append(f"**总词数(含重复)**: {len(all_words):,}\n")
    lines.append(f"**去重后词数**: {total_unique:,}\n")
    lines.append("\n| 排名 | 词 | 频率 |\n")
    lines.append("|-----|---|------|\n")

    for rank, (word, count) in enumerate(word_freq.most_common(100), 1):
        lines.append(f"| {rank} | {word} | {count} |\n")

    lines.append("\n...(仅显示前100个高频词)\n")
    output_file_md.write_text(''.join(lines), encoding='utf-8')
    print(f"  - 已保存(可读版): {output_file_md}")

    return word_freq

def step3_extract_traditional_variants(word_freq: Counter, min_frequency: int = 2):
    """步骤3: 对照已有繁体文件提取繁体版本"""
    print("\n" + "=" * 60)
    print(f"步骤3: 提取繁体版本(频率 >= {min_frequency})")
    print("=" * 60)

    # 筛选符合频率要求的词
    target_words = {word: count for word, count in word_freq.items() if count >= min_frequency}
    print(f"\n符合频率要求的词: {len(target_words):,}")

    # 加载繁体文本文件
    print(f"\n加载繁体文本: {TRADITIONAL_TEXT_FILE.name}")
    if not TRADITIONAL_TEXT_FILE.exists():
        print(f"❌ 文件不存在: {TRADITIONAL_TEXT_FILE}")
        return {}

    traditional_text = TRADITIONAL_TEXT_FILE.read_text(encoding='utf-8')
    print(f"✓ 已加载 (文件大小: {len(traditional_text):,} 字符)")

    # 建立简繁词映射
    print("\n建立简繁词映射...")
    mapping = build_word_mapping(set(target_words.keys()), traditional_text)

    # 构建variants结构
    variants = {}
    mapped_count = 0
    unmapped_count = 0

    for word, count in target_words.items():
        if word in mapping:
            trad_word = mapping[word]
            status = "mapped"
            mapped_count += 1
        else:
            trad_word = word  # 未找到映射,保持原样
            status = "unmapped"
            unmapped_count += 1

        variants[word] = {
            "traditional": trad_word,
            "frequency": count,
            "status": status
        }

    print(f"\n提取结果:")
    print(f"  - 成功映射: {mapped_count:,} 词")
    print(f"  - 未找到映射: {unmapped_count:,} 词")
    print(f"  - 总计: {len(variants):,} 词")

    # 保存结果
    output_file = OUTPUT_DIR / "03_word_variants_raw.json"
    output_file.write_text(json.dumps(variants, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"  - 已保存: {output_file}")

    return variants

def step4_filter_different_variants(variants: dict):
    """步骤4: 筛选出繁简不同的词"""
    print("\n" + "=" * 60)
    print("步骤4: 筛选繁简不同的词")
    print("=" * 60)

    # 筛选繁体和简体不同的词
    different_variants = {}
    same_count = 0

    for simp, info in variants.items():
        trad = info.get("traditional")

        if simp != trad:
            different_variants[simp] = trad
        else:
            same_count += 1

    print(f"\n筛选结果:")
    print(f"  - 繁简相同: {same_count:,} 词(已排除)")
    print(f"  - 繁简不同: {len(different_variants):,} 词 ⭐")

    # 按频率分组统计
    high_freq = sum(1 for s in different_variants if variants[s]['frequency'] >= 10)
    mid_freq = sum(1 for s in different_variants if 3 <= variants[s]['frequency'] < 10)
    low_freq = sum(1 for s in different_variants if variants[s]['frequency'] < 3)

    print(f"\n按频率分组:")
    print(f"  - 高频(≥10次): {high_freq:,} 词")
    print(f"  - 中频(3-9次): {mid_freq:,} 词")
    print(f"  - 低频(2次): {low_freq:,} 词")

    # 保存最终词表
    output_file = OUTPUT_DIR / "04_s2t_variants_final.json"
    output_file.write_text(json.dumps(different_variants, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n  - 已保存: {output_file}")

    # 保存可读版本
    output_file_md = OUTPUT_DIR / "04_s2t_variants_final.md"
    lines = ["# 《史记》繁简对照词表(完整版)\n\n"]
    lines.append(f"**生成日期**: 2026-04-01\n")
    lines.append(f"**词条数量**: {len(different_variants):,}\n\n")
    lines.append("| 简体 | 繁体 | 频率 |\n")
    lines.append("|-----|------|------|\n")

    # 按频率排序
    for simp in sorted(different_variants.keys(), key=lambda s: -variants[s]['frequency']):
        trad = different_variants[simp]
        freq = variants[simp]['frequency']
        lines.append(f"| {simp} | {trad} | {freq} |\n")

    output_file_md.write_text(''.join(lines), encoding='utf-8')
    print(f"  - 已保存(可读版): {output_file_md}")

    return different_variants

def main():
    """主流程"""
    print("\n" + "=" * 60)
    print("《史记》完整繁简词表构建")
    print("=" * 60)

    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 步骤1: 分词
    all_words = step1_segment_all_chapters()

    # 步骤2: 统计词频
    word_freq = step2_count_word_frequency(all_words)

    # 步骤3: 提取繁体(频率>=1,即所有词)
    variants = step3_extract_traditional_variants(word_freq, min_frequency=1)

    # 步骤4: 筛选繁简不同的词
    final_variants = step4_filter_different_variants(variants)

    print("\n" + "=" * 60)
    print("✅ 完成!")
    print("=" * 60)
    print(f"\n输出目录: {OUTPUT_DIR}")
    print("\n生成的文件:")
    print("  1. 01_all_words.txt - 所有分词结果")
    print("  2. 02_word_frequency.json - 完整词频表(JSON)")
    print("  3. 02_word_frequency.md - 词频表(可读版,前100)")
    print("  4. 03_word_variants_raw.json - 原始繁简对照(含未找到)")
    print("  5. 04_s2t_variants_final.json - 最终繁简词表(JSON)")
    print("  6. 04_s2t_variants_final.md - 最终繁简词表(可读版)")

if __name__ == "__main__":
    main()
