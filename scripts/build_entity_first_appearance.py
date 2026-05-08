#!/usr/bin/env python3
"""
build_entity_first_appearance.py

扫描所有 chapter_md/NNN_*.tagged.md 标注文件，提取每个实体在全书中
第一次出现的位置，生成按出现次序排列的列表，保存为 JSON 文件。

输出：docs/wiki/data/entity_first_appearance.json
"""

import json
import re
import os
import sys
import glob
from datetime import datetime, timezone

# ── 常量 ────────────────────────────────────────────────────────────────────

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTER_DIR = os.path.join(REPO_ROOT, 'chapter_md')
PAGES_JSON = os.path.join(REPO_ROOT, 'docs', 'wiki', 'pages.json')
OUTPUT_JSON = os.path.join(REPO_ROOT, 'docs', 'wiki', 'data', 'entity_first_appearance.json')

PREFIX_LABELS = {
    '@': '人物',
    '=': '地名',
    '~': '部族',
    '^': '制度',
    '•': '器物',
    '+': '动植物',
    '$': '数量',
    '!': '天文',
    '#': '身份',
    '&': '族群',
    ';': '官职',
    '◆': '邦国',
}

SKIP_PREFIXES = {'%', '_'}

# 标注正则：匹配 〖前缀显示名〗 或 〖前缀显示名|规范名〗
ENTITY_RE = re.compile(
    r'〖'
    r'([^〗\s|])'    # group 1: 类型前缀（单字符）
    r'([^〗|]*?)'    # group 2: 显示名（可为空）
    r'(?:\|([^〗]*))?' # group 3: 规范名（可选）
    r'〗'
)

# 段落ID：行首的 [数字] 或 [数字.数字] 形式
PARA_RE = re.compile(r'^\[(\d+(?:\.\d+)*)\]')

# ── 工具函数 ─────────────────────────────────────────────────────────────────

def load_pages_json():
    with open(PAGES_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    alias_index = data.get('alias_index', {})
    pages = set(data.get('pages', {}).keys())
    return alias_index, pages


def extract_chapter_info(filename):
    """从文件名 NNN_章节名.tagged.md 提取章节号和章节名"""
    basename = os.path.basename(filename)
    m = re.match(r'^(\d+)_(.+?)\.tagged\.md$', basename)
    if m:
        return m.group(1), m.group(2)
    return None, None


def is_valid_name(name):
    """检查名称是否有效（非空、非纯标点）"""
    if not name or not name.strip():
        return False
    # 去除各种标点后是否还有实质内容
    stripped = re.sub(r'[\s　，。？！、：；""''「」『』【】《》〈〉·…—～()（）-]', '', name)
    return len(stripped) > 0


def build_first_appearances(alias_index, pages_set):
    """主逻辑：扫描所有标注文件，提取首次出现"""
    # 获取所有文件，按文件名排序
    pattern = os.path.join(CHAPTER_DIR, '*.tagged.md')
    files = sorted(glob.glob(pattern))

    seen = {}        # canonical_name -> True（用于去重）
    entries = []

    for filepath in files:
        chapter_num, chapter_name = extract_chapter_info(filepath)
        if chapter_num is None:
            print(f'[警告] 无法解析文件名：{filepath}', file=sys.stderr)
            continue

        current_para = '0'  # 默认段落ID

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')

                # 更新当前段落ID
                m_para = PARA_RE.match(line)
                if m_para:
                    current_para = m_para.group(1)

                # 提取所有实体标注
                for m in ENTITY_RE.finditer(line):
                    prefix = m.group(1)
                    display_name = m.group(2).strip()
                    raw_canonical = m.group(3)

                    # 跳过不需要的前缀
                    if prefix in SKIP_PREFIXES:
                        continue

                    # 跳过未知前缀
                    if prefix not in PREFIX_LABELS:
                        continue

                    # 名称有效性检查
                    if not is_valid_name(display_name):
                        continue

                    # 规范名解析
                    if raw_canonical and raw_canonical.strip():
                        canonical_name = raw_canonical.strip()
                    else:
                        canonical_name = alias_index.get(display_name, display_name)

                    canonical_name = canonical_name.strip()
                    if not is_valid_name(canonical_name):
                        continue

                    # 首次出现检查
                    if canonical_name in seen:
                        continue

                    seen[canonical_name] = True

                    entries.append({
                        'rank': len(entries) + 1,
                        'canonical_name': canonical_name,
                        'display_name': display_name,
                        'prefix': prefix,
                        'type_label': PREFIX_LABELS[prefix],
                        'chapter_num': chapter_num,
                        'chapter_name': chapter_name,
                        'paragraph_id': current_para,
                        'has_page': canonical_name in pages_set,
                    })

    return entries


# ── 主程序 ───────────────────────────────────────────────────────────────────

def main():
    print('加载 pages.json ...')
    alias_index, pages_set = load_pages_json()
    print(f'  alias_index: {len(alias_index)} 条')
    print(f'  pages: {len(pages_set)} 个')

    print('\n扫描标注文件 ...')
    entries = build_first_appearances(alias_index, pages_set)

    # 统计
    total = len(entries)
    has_page_count = sum(1 for e in entries if e['has_page'])

    # 输出 JSON
    output = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'total': total,
        'entries': entries,
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 摘要
    print(f'\n=== 统计摘要 ===')
    print(f'  总实体数：{total}')
    print(f'  有 Wiki 页面：{has_page_count} ({has_page_count/total*100:.1f}%)')
    print(f'  无 Wiki 页面：{total - has_page_count}')

    print(f'\n=== 前 20 个首次出现的实体 ===')
    for e in entries[:20]:
        page_mark = '✓' if e['has_page'] else ' '
        print(f"  {e['rank']:3d}. [{page_mark}] {e['type_label']:3s} {e['canonical_name']}"
              f"  <- 第{e['chapter_num']}篇《{e['chapter_name']}》[{e['paragraph_id']}]"
              f"  (显示名: {e['display_name']})")

    print(f'\nJSON 文件已生成：{OUTPUT_JSON}')


if __name__ == '__main__':
    main()
