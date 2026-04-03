#!/usr/bin/env python3
"""
将 Markdown 表格格式的事实数据转换为 JSON 格式

Usage:
    python markdown_to_json.py <markdown_file> <output_json>

Example:
    python markdown_to_json.py ../markdown/001_五帝本纪_事实表格.md ../data/001_五帝本纪_事实索引.json
"""

import re
import json
import sys
from pathlib import Path


def parse_markdown_table(md_file):
    """解析 Markdown 表格，提取事实数据"""
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 查找表格起始行（以 | ID | 开头）
    table_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('| ID |'):
            table_start = i
            break

    if table_start is None:
        raise ValueError("未找到表格起始行（| ID | ...）")

    # 跳过表头和分隔线
    data_start = table_start + 2

    # 解析数据行
    facts = []
    for line in lines[data_start:]:
        line = line.strip()

        # 空行或非表格行，结束解析
        if not line or not line.startswith('|'):
            break

        # 如果是统计行（如 "**合计事实数**"），跳过
        if '**' in line:
            break

        # 拆分列
        cols = [c.strip() for c in line.split('|')]
        # 去掉首尾空元素（| 之前和之后）
        cols = cols[1:-1]  # 去掉第一个和最后一个空字符串

        if len(cols) != 11:
            print(f"警告：行列数={len(cols)}，期望11列，跳过：{line[:80]}...", file=sys.stderr)
            continue

        fact_id = cols[0]
        pn = cols[1] if cols[1] else None
        s = cols[2]
        p = cols[3]
        o = cols[4] if cols[4] else None
        time_str = cols[5] if cols[5] else None
        place = cols[6] if cols[6] else None
        other_ctx = cols[7] if cols[7] else None
        text = cols[8]
        conf = cols[9] if cols[9] else 'medium'
        event = cols[10] if cols[10] else None

        # 解析时间（如果是数字或"前XXX年"）
        time_val = None
        if time_str:
            # 匹配纯数字（负数或正数）
            m = re.match(r'^(-?\d+)$', time_str)
            if m:
                time_val = int(m.group(1))
            # 匹配"前XXX年"或"公元前XXX年"
            m = re.match(r'^(?:公元)?前(\d+)年$', time_str)
            if m:
                time_val = -int(m.group(1))

        # 构建 ctx
        ctx = {
            'time': time_val,
            'place': place
        }

        # 如果有其他背景，尝试解析为键值对，或作为 occasion
        if other_ctx:
            # 简单处理：直接作为 occasion
            ctx['occasion'] = other_ctx

        # 构建事实对象
        fact = {
            'id': fact_id,
            'pn': pn,
            's': s,
            'p': p,
            'o': o,
            'ctx': ctx,
            'src': extract_chapter_name(md_file),
            'text': text,
            'conf': conf,
            'event': event
        }

        facts.append(fact)

    return facts


def extract_chapter_name(md_file):
    """从文件名提取章节名（如 001_五帝本纪）"""
    stem = Path(md_file).stem
    # 去掉 "_事实表格" 后缀
    if stem.endswith('_事实表格'):
        stem = stem[:-5]
    return stem


def main():
    if len(sys.argv) != 3:
        print("Usage: python markdown_to_json.py <markdown_file> <output_json>")
        sys.exit(1)

    md_file = sys.argv[1]
    output_json = sys.argv[2]

    # 解析 Markdown 表格
    facts = parse_markdown_table(md_file)

    # 输出 JSON
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(facts, f, ensure_ascii=False, indent=2)

    print(f"✅ 成功转换 {len(facts)} 条事实")
    print(f"   输入：{md_file}")
    print(f"   输出：{output_json}")

    # 统计信息
    print(f"\n📊 统计信息：")
    print(f"   事实总数：{len(facts)}")
    print(f"   段落数量：{len(set(f['pn'] for f in facts if f['pn']))}")
    print(f"   主语数量：{len(set(f['s'] for f in facts))}")
    print(f"   谓语数量：{len(set(f['p'] for f in facts))}")
    print(f"   有宾语：{sum(1 for f in facts if f['o'])}")
    print(f"   无宾语：{sum(1 for f in facts if not f['o'])}")
    print(f"   有时间：{sum(1 for f in facts if f['ctx']['time'])}")
    print(f"   有地点：{sum(1 for f in facts if f['ctx']['place'])}")
    print(f"   有事件：{sum(1 for f in facts if f['event'])}")

    # 置信度分布
    conf_dist = {}
    for f in facts:
        conf_dist[f['conf']] = conf_dist.get(f['conf'], 0) + 1
    print(f"\n   置信度分布：")
    for conf in ['exact', 'high', 'medium', 'low']:
        count = conf_dist.get(conf, 0)
        if count > 0:
            print(f"     {conf}: {count}")


if __name__ == '__main__':
    main()
