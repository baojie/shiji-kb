#!/usr/bin/env python3
"""
质控函数：验证转换后的 md 文件没有改动原始文本内容
"""

import re
import sys
from pathlib import Path


def remove_all_tags(text):
    """去除所有语义标签和编号"""
    # 去除段落编号 [1], [1.1], [1.1.2] 等
    text = re.sub(r'^\[\d+(?:\.\d+)*\]\s*', '', text, flags=re.MULTILINE)

    # 去除 markdown 标题标记
    text = re.sub(r'^##\s+.*$', '', text, flags=re.MULTILINE)

    # 去除引用块标记和前导 >
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\[!NOTE\]\s+', '', text, flags=re.MULTILINE)

    # 去除各种语义标签（按出现频率优化顺序）
    # @person@ - 人物
    text = re.sub(r'@([^@]+)@', r'\1', text)
    # &state& - 国家/组织
    text = re.sub(r'&([^&]+)&', r'\1', text)
    # =place= - 地点
    text = re.sub(r'=([^=]+)=', r'\1', text)
    # $position$ - 职位
    text = re.sub(r'\$([^$]+)\$', r'\1', text)
    # %time% - 时间
    text = re.sub(r'%([^%]+)%', r'\1', text)
    # *object* - 物品
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    # ^concept^ - 概念 (修正：不能用 ^，要用 \^)
    text = re.sub(r'\^([^\^]+)\^', r'\1', text)
    # ~tribe~ - 部落
    text = re.sub(r'~([^~]+)~', r'\1', text)
    # ?deity? - 神灵
    text = re.sub(r'\?([^?]+)\?', r'\1', text)
    # 🌿animal🌿 - 动植物
    text = re.sub(r'🌿([^🌿]+)🌿', r'\1', text)
    # !event! - 天象
    text = re.sub(r'!([^!]+)!', r'\1', text)

    return text.strip()


def get_paragraphs_from_md(md_path):
    """从 md 文件中提取段落"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按空行分割段落
    paragraphs = []
    current_para = []

    for line in content.split('\n'):
        line = line.rstrip()
        if not line:
            if current_para:
                paragraphs.append('\n'.join(current_para))
                current_para = []
        else:
            current_para.append(line)

    if current_para:
        paragraphs.append('\n'.join(current_para))

    return paragraphs


def normalize_text(text):
    """标准化文本，用于比较"""
    # 移除所有空白字符的变化
    text = re.sub(r'\s+', '', text)
    return text


def extract_paragraph_number(para):
    """从段落中提取段落编号，如 [1], [1.1], [1.1.2] 等"""
    match = re.match(r'^\[(\d+(?:\.\d+)*)\]', para)
    if match:
        return match.group(1)
    return None


def get_root_number(para_num):
    """获取段落编号的根编号，如 1.2.3 -> 1"""
    if not para_num:
        return None
    return para_num.split('.')[0]


def validate_chapter(md_path, txt_path):
    """验证章节转换的正确性"""
    # 读取原始文本
    with open(txt_path, 'r', encoding='utf-8') as f:
        original_text = f.read()

    # 清理原始文本（去除段落编号）
    clean_original = remove_all_tags(original_text)

    # 标准化原始文本
    normalized_original = normalize_text(clean_original)

    # 获取 md 中的段落
    paragraphs = get_paragraphs_from_md(md_path)

    # 按段落编号分组
    grouped_paragraphs = {}
    for i, para in enumerate(paragraphs, 1):
        # 跳过标题行（以 # 开头的）
        if para.startswith('#'):
            continue

        # 跳过引用块的标记行
        if para.startswith('> [!NOTE]'):
            continue

        # 提取段落编号
        para_num = extract_paragraph_number(para)
        if para_num:
            root_num = get_root_number(para_num)
            if root_num not in grouped_paragraphs:
                grouped_paragraphs[root_num] = []
            grouped_paragraphs[root_num].append((i, para_num, para))

    errors = []
    checked_count = 0

    # 验证每组段落
    for root_num in sorted(grouped_paragraphs.keys(), key=lambda x: int(x)):
        group = grouped_paragraphs[root_num]

        # 合并同一组的所有段落
        combined_text = ''
        for _, _, para in group:
            clean_para = remove_all_tags(para)
            if clean_para:
                combined_text += clean_para

        if not combined_text:
            continue

        checked_count += 1

        # 标准化合并后的文本
        normalized_combined = normalize_text(combined_text)

        # 检查是否在原始文本中
        if normalized_combined not in normalized_original:
            errors.append({
                'root_num': root_num,
                'para_count': len(group),
                'para_nums': [pn for _, pn, _ in group],
                'combined': combined_text[:300] + '...' if len(combined_text) > 300 else combined_text
            })

    # 报告结果
    print(f"验证文件: {md_path.name}")
    print(f"检查段落组数: {checked_count}")

    if errors:
        print(f"\n❌ 发现 {len(errors)} 个不匹配的段落组:\n")
        for err in errors:
            print(f"段落组 [{err['root_num']}] (包含 {err['para_count']} 个子段落: {', '.join(['[' + pn + ']' for pn in err['para_nums']])})")
            print(f"  合并后文本: {err['combined']}")
            print()
        return False
    else:
        print("✅ 所有段落验证通过！")
        return True


if __name__ == '__main__':
    # 测试 005 章
    base_dir = Path('/home/baojie/work/shiji-kb')
    md_file = base_dir / 'chapter_md' / '005_秦本纪.tagged.md'
    txt_file = base_dir / 'chapter_numbered' / '005_秦本纪.txt'

    if not md_file.exists():
        print(f"错误: MD 文件不存在: {md_file}")
        sys.exit(1)

    if not txt_file.exists():
        print(f"错误: TXT 文件不存在: {txt_file}")
        sys.exit(1)

    success = validate_chapter(md_file, txt_file)

    if not success:
        print("\n验证失败！存在文本改动。")
        sys.exit(1)
    else:
        print("\n验证成功！转换未改动原文。")
        sys.exit(0)
