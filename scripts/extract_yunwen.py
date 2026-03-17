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

def extract_title_from_context(content, match_start, yunwen_type):
    """从韵文前的上下文中提取标题"""
    # 获取区块前的100个字符
    start_pos = max(0, match_start - 200)
    context = content[start_pos:match_start]

    # 尝试从前文提取标题线索
    title_patterns = [
        r'刻(?:所立)?石[，。](?:其)?(?:辞|文)曰',  # 刻石文字
        r'立石刻[，。](?:颂|铭|曰)',  # 立石刻
        r'(?:作|为)([^。，]+)[，。](?:其)?(?:辞|文)曰',  # 作XX，其辞曰
        r'(?:登|至|过)([^。，]+)[，。]刻石',  # 登XX，刻石
    ]

    for pattern in title_patterns:
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
        pattern = rf'^::: {re.escape(yunwen_type)}$(.*?)^:::$'
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)

        for match in matches:
            block_content = match.group(1).strip()
            if block_content:
                # 尝试从上下文提取标题
                title = extract_title_from_context(content, match.start(), yunwen_type)
                blocks.append((yunwen_type, block_content, title))

    return blocks

def main():
    project_root = Path(__file__).parent.parent
    chapter_dir = project_root / "chapter_md"
    output_dir = project_root / "docs/special"
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

        for yunwen_type, content, title in blocks:
            # 如果没有提取到标题，使用默认标题
            if not title:
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
