#!/usr/bin/env python3
"""
提取史记中的韵文内容（赞、诗歌、赋）
这些是史记中以诗歌形式呈现的文学作品
"""

import re
import json
from pathlib import Path

# 韵文类型定义
YUNWEN_TYPES = {
    '赞': '司马迁以诗歌形式对历史人物和事件的歌颂与评价',
    '诗歌': '史记中收录的诗歌作品',
    '赋': '史记中收录的赋体文学作品'
}

# 加载手工标题映射
def load_manual_titles():
    """加载手工确定的诗歌和赋标题"""
    titles_file = Path(__file__).parent.parent / 'data' / 'yunwen_titles.json'
    if titles_file.exists():
        with open(titles_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 过滤掉注释字段
            return {k: v for k, v in data.items() if not k.startswith('_')}
    return {}

MANUAL_TITLES = load_manual_titles()

def extract_title_from_context(content, match_start, yunwen_type):
    """从韵文前的上下文中提取标题"""
    # 获取区块前的200个字符
    start_pos = max(0, match_start - 200)
    context = content[start_pos:match_start]

    # 🔥 优先提取 Markdown 标题（## 标题）
    md_title_match = re.search(r'##\s+(.+?)$', context, re.MULTILINE)
    if md_title_match:
        title = md_title_match.group(1).strip()
        # 清理可能的标点符号
        title = title.rstrip('，。、；：')
        return title

    # 尝试从前文提取标题线索
    if yunwen_type == '诗歌':
        # 刻石诗歌：提取地名
        title_patterns = [
            r'刻(?:所立)?石於?〖[=]+([^〗]+)〗',  # 刻石于泰山
            r'登(?:于)?〖[=]+([^〗]+)〗[^。，]*刻石',  # 登泰山，刻石
            r'至〖[=]+([^〗]+)〗[^。，]*刻石',  # 至之罘，刻石
            r'刻〖[=]+([^〗]+)〗石',  # 刻泰山石
        ]
        for pattern in title_patterns:
            m = re.search(pattern, context)
            if m:
                place = m.group(1).strip()
                return place + '刻石'

    elif yunwen_type == '赋':
        # 赋的标题模式
        title_patterns = [
            r'作〖[^〗]*〗?([^〖〗]+赋)〗?[，。]',  # 作《离骚赋》
            r'([^〖〗]+赋)[，。]',  # 《上林赋》，
            r'〖[•~]([^〗]+)〗',  # 〖~离骚〗
        ]
        for pattern in title_patterns:
            m = re.search(pattern, context)
            if m:
                title = m.group(1).strip()
                # 清理标点
                title = title.rstrip('，。、；：')
                if '赋' in title or '骚' in title:
                    return title

    # 通用模式（适用所有类型）
    generic_patterns = [
        r'刻(?:所立)?石[，。](?:其)?(?:辞|文)曰',  # 刻石文字
        r'立石刻[，。](?:颂|铭|曰)',  # 立石刻
        r'(?:作|为)([^。，]+)[，。](?:其)?(?:辞|文)曰',  # 作XX，其辞曰
        r'(?:登|至|过)([^。，]+)[，。]刻石',  # 登XX，刻石
    ]

    for pattern in generic_patterns:
        m = re.search(pattern, context)
        if m:
            # 提取地名或事件
            if m.groups():
                place = m.group(1).strip()
                # 清理实体标注
                place = re.sub(r'〖[^〗]+〗', '', place)
                if place:
                    return place + yunwen_type

    return None

def extract_yunwen_blocks(chapter_file):
    """
    从章节文件中提取所有韵文区块

    Returns:
        list: [(type, content, title), ...]
    """
    content = chapter_file.read_text(encoding='utf-8')
    blocks = []

    # 匹配 ::: 韵文类型 ... ::: 格式
    for yunwen_type in YUNWEN_TYPES.keys():
        # 精确匹配（如 ::: 赞）
        pattern = rf'^::: {re.escape(yunwen_type)}$(.*?)^:::$'
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)

        for match in matches:
            block_content = match.group(1).strip()
            if block_content:
                # 尝试从上下文提取标题
                title = extract_title_from_context(content, match.start(), yunwen_type)
                blocks.append((yunwen_type, block_content, title))

        # 对于"赞"类型，额外支持变体标记（如 ::: 太史公赞）
        if yunwen_type == '赞':
            variant_pattern = r'^::: (?:太史公赞|褚先生赞|后人赞辞|.*赞语)$(.*?)^:::$'
            variant_matches = re.finditer(variant_pattern, content, re.MULTILINE | re.DOTALL)

            for match in variant_matches:
                block_content = match.group(1).strip()
                if block_content:
                    # 尝试从上下文提取标题
                    title = extract_title_from_context(content, match.start(), yunwen_type)
                    blocks.append((yunwen_type, block_content, title))

    return blocks

def main():
    project_root = Path(__file__).parent.parent
    chapter_dir = project_root / "chapter_md"
    # 中间文件保存在根目录的data/下
    output_dir = project_root / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 提取所有韵文
    all_yunwen = []
    chapter_files = sorted(chapter_dir.glob("*.tagged.md"))

    print(f"扫描 {len(chapter_files)} 个章节文件...")

    for chapter_file in chapter_files:
        # 提取章节编号和标题
        filename = chapter_file.stem.replace('.tagged', '')
        match = re.match(r'(\d+)_(.*)', filename)
        if not match:
            continue

        chapter_num = match.group(1)
        chapter_title = match.group(2)

        # 提取韵文区块
        blocks = extract_yunwen_blocks(chapter_file)

        # 用于统计每种类型的韵文序号
        type_counter = {}

        for yunwen_type, content, title in blocks:
            # 统计该类型韵文在本章的序号
            type_counter[yunwen_type] = type_counter.get(yunwen_type, 0) + 1
            seq_num = type_counter[yunwen_type]

            # 🔥 优先使用手工映射的标题
            manual_key = f"{chapter_num}_{yunwen_type}_{seq_num}"
            if manual_key in MANUAL_TITLES:
                title = MANUAL_TITLES[manual_key]
            # 如果没有手工映射，且自动提取也没有标题，使用默认标题
            elif not title:
                if yunwen_type == '赞':
                    title = f"{chapter_title}之赞"
                elif yunwen_type == '诗歌':
                    title = f"{chapter_title}诗"
                elif yunwen_type == '赋':
                    title = f"{chapter_title}赋"
                else:
                    title = chapter_title

            all_yunwen.append({
                'chapter_num': chapter_num,
                'chapter_title': chapter_title,
                'type': yunwen_type,
                'type_desc': YUNWEN_TYPES[yunwen_type],
                'title': title,
                'content': content
            })

    print(f"\n提取结果：")
    print(f"  总计: {len(all_yunwen)} 篇韵文")

    # 按类型统计
    type_counts = {}
    for item in all_yunwen:
        yunwen_type = item['type']
        type_counts[yunwen_type] = type_counts.get(yunwen_type, 0) + 1

    for yunwen_type, count in sorted(type_counts.items()):
        print(f"  {yunwen_type}: {count} 篇")

    # 保存JSON
    output_json = output_dir / "yunwen.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(all_yunwen, f, ensure_ascii=False, indent=2)
    print(f"\n✓ JSON 已保存: {output_json}")

    # 生成 Markdown
    output_md = output_dir / "yunwen.md"
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write("# 史记韵文集\n\n")
        f.write(f"史记中共有 {len(all_yunwen)} 篇韵文作品\n\n")

        # 按类型分组
        for yunwen_type, desc in YUNWEN_TYPES.items():
            items = [item for item in all_yunwen if item['type'] == yunwen_type]
            if not items:
                continue

            f.write(f"## {yunwen_type}（{len(items)}篇）\n\n")
            f.write(f"{desc}\n\n")

            for item in items:
                f.write(f"### {item['title']}\n\n")
                f.write(f"*{item['chapter_num']} {item['chapter_title']}*\n\n")
                f.write(f"{item['content']}\n\n")
                f.write("---\n\n")

    print(f"✓ Markdown 已保存: {output_md}")

    # 统计信息
    print(f"\n统计信息：")
    print(f"  覆盖章节: {len(set(item['chapter_num'] for item in all_yunwen))}/130")
    print(f"  平均每章: {len(all_yunwen)/130:.2f} 篇")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
