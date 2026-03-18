#!/usr/bin/env python3
"""
导出战争专项索引

将wars.json转换为专项索引格式（JSON + Markdown）
"""

import json
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent
WARS_JSON = PROJECT_ROOT / "kg" / "events" / "data" / "wars.json"
OUTPUT_JSON = PROJECT_ROOT / "data" / "wars.json"
OUTPUT_MD = PROJECT_ROOT / "data" / "wars.md"


def load_wars() -> List[Dict[str, Any]]:
    """加载战争数据"""
    with open(WARS_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


def convert_to_special_format(wars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """转换为专项索引格式"""
    special_data = []

    for war in wars:
        # 提取章节号（从第一个来源）
        chapter_num = war['sources'][0].split('-')[0]

        # 获取章节标题（从chapters字段）
        chapter_title = war['chapters'][0].replace('_事件索引', '').replace(f'{chapter_num}_', '')

        # 构建战争描述
        desc_parts = []

        # 基本信息
        time_str = ', '.join(war['time']['original']) if war['time']['original'] else '-'
        location_str = ', '.join(war['location']) if war['location'] else '-'

        desc_parts.append(f"**时间**: {time_str}")
        desc_parts.append(f"**地点**: {location_str}")

        # 交战双方
        if war['belligerents']['attacker']['state'] or war['belligerents']['defender']['state']:
            attacker = ', '.join(war['belligerents']['attacker']['state']) or '未知'
            defender = ', '.join(war['belligerents']['defender']['state']) or '未知'
            desc_parts.append(f"**交战双方**: {attacker} vs {defender}")

        # 将领
        if war['belligerents']['attacker']['commanders']:
            commanders = ', '.join(war['belligerents']['attacker']['commanders'][:5])
            desc_parts.append(f"**将领**: {commanders}")

        # 伤亡
        if war['casualties']:
            casualties_text = '; '.join([f"{c['text']}" for c in war['casualties'][:3]])
            desc_parts.append(f"**伤亡**: {casualties_text}")

        # 战果
        if war['outcome']:
            outcome_text = war['outcome'][0] if war['outcome'] else ''
            if len(outcome_text) > 100:
                outcome_text = outcome_text[:100] + '...'
            desc_parts.append(f"**战果**: {outcome_text}")

        # 来源说明
        if len(war['sources']) > 1:
            source_count = len(war['sources'])
            desc_parts.append(f"**多源战争**: {source_count}个来源")

        # 完整描述（从第一个来源）
        full_desc = war['descriptions'][0]['text'] if war['descriptions'] else ''

        special_data.append({
            "chapter_num": chapter_num,
            "chapter_title": chapter_title,
            "war_id": war['war_id'],
            "war_name": war['war_name'],
            "description": '\n'.join(desc_parts),
            "full_description": full_desc,
            "sources": war['sources'],
            "chapters": [ch.replace('_事件索引', '') for ch in war['chapters']],
            "source_count": len(war['sources'])
        })

    # 按章节号排序
    special_data.sort(key=lambda x: x['chapter_num'])

    return special_data


def export_json(data: List[Dict[str, Any]]):
    """导出JSON"""
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"JSON已导出至: {OUTPUT_JSON}")


def export_markdown(data: List[Dict[str, Any]]):
    """导出Markdown"""
    lines = [
        "# 史记战争事件专项索引",
        "",
        "## 统计概览",
        "",
        f"- **总战争数**: {len(data)}",
        f"- **多源战争**: {sum(1 for d in data if d['source_count'] > 1)}条",
        f"- **单源战争**: {sum(1 for d in data if d['source_count'] == 1)}条",
        f"- **覆盖章节**: {len(set(d['chapter_num'] for d in data))}章",
        "",
        "---",
        "",
        "## 战争列表",
        "",
        "| 战争ID | 战争名称 | 章节 | 时间 | 来源数 |",
        "|--------|---------|------|------|--------|"
    ]

    # 添加表格行
    for d in data:
        time_str = d['description'].split('**时间**: ')[1].split('\n')[0] if '**时间**:' in d['description'] else '-'
        lines.append(
            f"| {d['war_id']} | {d['war_name']} | {d['chapter_num']}_{d['chapter_title']} | {time_str} | {d['source_count']} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 详细记录",
        ""
    ])

    # 按章节分组
    current_chapter = None
    for d in data:
        if d['chapter_num'] != current_chapter:
            current_chapter = d['chapter_num']
            lines.extend([
                f"### {d['chapter_num']}_{d['chapter_title']}",
                ""
            ])

        lines.extend([
            f"#### {d['war_id']} {d['war_name']}",
            "",
            d['description'],
            ""
        ])

        if d['source_count'] > 1:
            lines.append(f"**其他来源**: {', '.join(d['chapters'][1:])}")
            lines.append("")

        lines.extend([
            "**描述**:",
            "",
            f"> {d['full_description'][:500]}{'...' if len(d['full_description']) > 500 else ''}",
            "",
            "---",
            ""
        ])

    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Markdown已导出至: {OUTPUT_MD}")


def main():
    print("=" * 60)
    print("导出战争专项索引")
    print("=" * 60)

    # 加载数据
    wars = load_wars()
    print(f"\n加载了 {len(wars)} 个战争")

    # 转换格式
    special_data = convert_to_special_format(wars)
    print(f"转换完成，共 {len(special_data)} 条记录")

    # 导出
    export_json(special_data)
    export_markdown(special_data)

    print("\n完成！")
    print(f"多源战争: {sum(1 for d in special_data if d['source_count'] > 1)}")
    print(f"覆盖章节: {len(set(d['chapter_num'] for d in special_data))}")


if __name__ == "__main__":
    main()
