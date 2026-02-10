#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从标注的史记章节中构建命名实体索引

功能：
1. 扫描 chapter_md/*.tagged.md，提取所有实体及其段落引用
2. 读取 entity_aliases.json 进行别名合并
3. 生成 entity_index.json（中间数据）
4. 生成 docs/entities/*.html（可浏览的索引页面）

用法：
    python build_entity_index.py
"""

import re
import json
import html
from pathlib import Path
from collections import defaultdict
from urllib.parse import quote
from pypinyin import pinyin, Style

# --- 配置 ---
CHAPTER_DIR = Path('chapter_md')
OUTPUT_DIR = Path('docs/entities')
ALIAS_FILE = Path('entity_aliases.json')
INDEX_JSON = Path('entity_index.json')

# 实体类型定义: (type_key, regex_pattern, css_class, chinese_label, html_filename)
ENTITY_TYPES = [
    ('person',      r'@([^@\n]+)@',           'person',      '人名',     'person.html'),
    ('place',       r'=([^=\n]+)=',            'place',       '地名',     'place.html'),
    ('official',    r'\$([^$\n]+)\$',          'official',    '官职',     'official.html'),
    ('time',        r'%([^%\n]+)%',            'time',        '时间',     'time.html'),
    ('dynasty',     r'&([^&\n]+)&',            'dynasty',     '朝代',     'dynasty.html'),
    ('institution', r'\^([^\^\n]+)\^',         'institution', '制度',     'institution.html'),
    ('tribe',       r'~([^~\n]+)~',            'tribe',       '族群',     'tribe.html'),
    ('artifact',    r'\*\*[^*]+\*\*|(?<!\*)\*([^*\n]+)\*(?!\*)', 'artifact', '器物', 'artifact.html'),
    ('astronomy',   r'!([^!\n]+)!',            'astronomy',   '天文',     'astronomy.html'),
    ('mythical',    r'\?([^?\n]+)\?',          'mythical',    '神话',     'mythical.html'),
    ('flora-fauna', r'🌿([^🌿\n]+)🌿',       'flora-fauna', '动植物',   'flora-fauna.html'),
]

# 段落编号模式
PARA_NUM_PATTERN = r'\[(\d+(?:\.\d+)*)\]'

def is_valid_entity(surface):
    """检查提取的实体名是否合法（白名单：只允许汉字和阿拉伯数字）"""
    if not surface:
        return False
    for ch in surface:
        if '\u4e00' <= ch <= '\u9fff':  # CJK 基本汉字
            continue
        if '\u3400' <= ch <= '\u4dbf':  # CJK 扩展A
            continue
        if ch.isdigit():  # 阿拉伯数字（时间条目可能用到）
            continue
        return False
    return True


# 章节标题提取（用于显示友好名称）
def extract_chapter_title(chapter_id):
    """从章节ID提取显示标题，如 '007_项羽本纪' → '项羽本纪'"""
    parts = chapter_id.split('_', 1)
    return parts[1] if len(parts) > 1 else chapter_id


def extract_entities_from_file(file_path):
    """从单个 .tagged.md 文件提取所有实体及其段落引用

    Returns:
        list of (type_key, surface_form, chapter_id, para_num)
    """
    chapter_id = file_path.stem.replace('.tagged', '')
    results = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    current_para = '0'

    for line in lines:
        # 更新当前段落号（取行中第一个段落编号）
        pn_matches = list(re.finditer(PARA_NUM_PATTERN, line))
        if pn_matches:
            current_para = pn_matches[0].group(1)

        # 提取各类实体
        for type_key, pattern, css_class, label, _ in ENTITY_TYPES:
            # 器物类型需要特殊处理：跳过 **粗体**
            if type_key == 'artifact':
                for m in re.finditer(pattern, line):
                    surface = m.group(1)
                    if surface is None:
                        continue  # **粗体** 匹配，跳过
                    surface = surface.strip()
                    if surface and is_valid_entity(surface):
                        results.append((type_key, surface, chapter_id, current_para))
            else:
                for m in re.finditer(pattern, line):
                    surface = m.group(1).strip()
                    if surface and is_valid_entity(surface):
                        results.append((type_key, surface, chapter_id, current_para))

    return results


def load_alias_map(alias_file):
    """加载别名映射，返回 {type_key: {surface_form: canonical_name}}"""
    if not alias_file.exists():
        return {}

    with open(alias_file, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    reverse_map = {}
    for entity_type, mappings in raw.items():
        reverse_map[entity_type] = {}
        for canonical, aliases in mappings.items():
            reverse_map[entity_type][canonical] = canonical
            for alias in aliases:
                if alias:  # 跳过空别名
                    reverse_map[entity_type][alias] = canonical

    return reverse_map


def build_index(chapter_dir, alias_map):
    """构建完整的实体索引

    Returns:
        {type_key: {canonical_name: {
            'aliases': set of surface forms,
            'refs': [(chapter_id, para_num), ...],
            'count': int
        }}}
    """
    index = {t[0]: {} for t in ENTITY_TYPES}

    # 扫描所有文件
    tagged_files = sorted(chapter_dir.glob('*.tagged.md'))
    print(f"扫描 {len(tagged_files)} 个标注文件...")

    for fpath in tagged_files:
        entities = extract_entities_from_file(fpath)
        for type_key, surface, chapter_id, para_num in entities:
            # 别名解析
            type_aliases = alias_map.get(type_key, {})
            canonical = type_aliases.get(surface, surface)

            # 初始化条目
            if canonical not in index[type_key]:
                index[type_key][canonical] = {
                    'aliases': set(),
                    'refs': [],
                    'count': 0,
                }

            entry = index[type_key][canonical]
            entry['aliases'].add(surface)
            entry['refs'].append((chapter_id, para_num))
            entry['count'] += 1

    # 去重引用并排序
    for type_key in index:
        for canonical, entry in index[type_key].items():
            # 去重：同一章同一段落只记录一次
            unique_refs = sorted(set(entry['refs']),
                                 key=lambda r: (r[0], [int(x) for x in r[1].split('.')]))
            entry['refs'] = unique_refs
            # aliases 转为排序列表
            entry['aliases'] = sorted(entry['aliases'])

    return index


def save_index_json(index, output_file):
    """保存索引为 JSON 文件"""
    # 转换为可序列化格式
    serializable = {}
    for type_key, entries in index.items():
        serializable[type_key] = {}
        for canonical, entry in entries.items():
            serializable[type_key][canonical] = {
                'aliases': entry['aliases'],
                'refs': entry['refs'],
                'count': entry['count'],
            }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)

    print(f"索引数据已保存: {output_file}")


def _get_pinyin_key(name):
    """获取实体名的拼音排序键"""
    py = pinyin(name, style=Style.TONE3)
    return ''.join(p[0] for p in py).lower()


def _get_pinyin_initial(name):
    """获取实体名的拼音首字母（大写）"""
    py = pinyin(name[0], style=Style.NORMAL)
    initial = py[0][0][0].upper() if py and py[0] and py[0][0] else '#'
    if initial.isalpha():
        return initial
    return '#'


def generate_type_page(type_key, css_class, label, filename, entries):
    """生成单个类型的索引 HTML 页面"""
    # 按拼音排序
    sorted_entries = sorted(entries.items(), key=lambda x: _get_pinyin_key(x[0]))

    # 按拼音首字母分组
    grouped_by_letter = defaultdict(list)
    for canonical, entry in sorted_entries:
        letter = _get_pinyin_initial(canonical)
        grouped_by_letter[letter].append((canonical, entry))

    # 收集所有出现的字母，排序
    letters = sorted(grouped_by_letter.keys(), key=lambda x: (x == '#', x))

    total_entities = len(sorted_entries)
    total_refs = sum(e['count'] for _, e in sorted_entries)

    lines = []
    lines.append('<!DOCTYPE html>')
    lines.append('<html lang="zh-CN">')
    lines.append('<head>')
    lines.append('    <meta charset="UTF-8">')
    lines.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    lines.append(f'    <title>{label}索引 - 史记知识库</title>')
    lines.append('    <link rel="stylesheet" href="../css/shiji-styles.css">')
    lines.append('    <link rel="stylesheet" href="../css/entity-index.css">')
    lines.append('</head>')
    lines.append('<body>')

    # 导航
    lines.append('<nav class="chapter-nav">')
    lines.append('    <a href="../index.html" class="nav-home">回到主页</a>')
    lines.append('    <a href="index.html" class="nav-next">实体索引</a>')
    lines.append('</nav>')

    lines.append(f'<h1>{label}索引</h1>')
    lines.append(f'<p class="index-stats">共 <strong>{total_entities}</strong> 个条目，'
                 f'<strong>{total_refs}</strong> 次出现</p>')

    # 搜索框
    lines.append('<div class="entity-filter">')
    lines.append(f'    <input type="text" id="filter-input" placeholder="搜索{label}...">')
    lines.append('</div>')

    # 拼音字母导航栏
    lines.append('<div class="pinyin-nav">')
    for letter in letters:
        count = len(grouped_by_letter[letter])
        lines.append(f'  <a href="#letter-{letter}" class="pinyin-letter">{letter}<span class="letter-count">{count}</span></a>')
    lines.append('</div>')

    # 实体列表（按字母分节）
    lines.append('<div class="entity-index">')

    for letter in letters:
        group = grouped_by_letter[letter]
        lines.append(f'<div class="letter-section" id="letter-{letter}">')
        lines.append(f'  <h2 class="letter-heading">{letter}</h2>')

        for canonical, entry in group:
            aliases = [a for a in entry['aliases'] if a != canonical]
            esc_canonical = html.escape(canonical)

            # 主锚点
            lines.append(f'  <div class="entity-entry" id="entity-{esc_canonical}">')

            # 左侧：名称 + 别名（别名锚点放在 entry-left 内部）
            lines.append('    <div class="entry-left">')
            for alias in aliases:
                esc_alias = html.escape(alias)
                lines.append(f'      <a id="entity-{esc_alias}"></a>')
            lines.append(f'      <span class="canonical-name {css_class}">{esc_canonical}</span>')
            if aliases:
                alias_str = '、'.join(html.escape(a) for a in aliases)
                lines.append(f'      <span class="alias-list">{alias_str}</span>')
            lines.append(f'      <span class="entry-count">({entry["count"]})</span>')
            lines.append('    </div>')

            # 右侧：章节引用
            lines.append('    <div class="entry-right">')
            refs_html = _format_refs(entry['refs'])
            lines.append(f'      {refs_html}')
            lines.append('    </div>')

            lines.append('  </div>')

        lines.append('</div>')

    lines.append('</div>')

    # 过滤脚本
    lines.append('<script src="../js/entity-filter.js"></script>')

    # 底部导航
    lines.append('<nav class="chapter-nav">')
    lines.append('    <a href="../index.html" class="nav-home">回到主页</a>')
    lines.append('    <a href="index.html" class="nav-next">实体索引</a>')
    lines.append('</nav>')

    lines.append('</body>')
    lines.append('</html>')

    return '\n'.join(lines)


def _format_refs(refs):
    """将引用列表格式化为按章节分组的 HTML 链接

    输入: [(chapter_id, para_num), ...]
    输出: "项羽本纪 <a>1.1</a>, <a>1.2</a> | 高祖本纪 <a>3.2</a>"
    """
    # 按章节分组
    grouped = defaultdict(list)
    for chapter_id, para_num in refs:
        grouped[chapter_id].append(para_num)

    parts = []
    for chapter_id in sorted(grouped.keys()):
        paras = grouped[chapter_id]
        title = extract_chapter_title(chapter_id)
        esc_title = html.escape(title)

        # 章节名链接到章节首页
        chapter_link = f'<a href="../chapters/{chapter_id}.html" class="chapter-ref-name">{esc_title}</a>'

        # 段落链接
        para_links = []
        for pn in paras:
            para_links.append(
                f'<a href="../chapters/{chapter_id}.html#pn-{pn}" class="para-ref">{pn}</a>'
            )

        parts.append(f'{chapter_link} {", ".join(para_links)}')

    return ' <span class="ref-sep">|</span> '.join(parts)


def generate_landing_page(index):
    """生成实体索引总览页面"""
    lines = []
    lines.append('<!DOCTYPE html>')
    lines.append('<html lang="zh-CN">')
    lines.append('<head>')
    lines.append('    <meta charset="UTF-8">')
    lines.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    lines.append('    <title>实体索引 - 史记知识库</title>')
    lines.append('    <link rel="stylesheet" href="../css/shiji-styles.css">')
    lines.append('    <link rel="stylesheet" href="../css/entity-index.css">')
    lines.append('</head>')
    lines.append('<body>')

    lines.append('<nav class="chapter-nav">')
    lines.append('    <a href="../index.html" class="nav-home">回到主页</a>')
    lines.append('</nav>')

    lines.append('<h1>命名实体索引</h1>')
    lines.append('<p>史记全文命名实体索引，按实体类型分类。点击类型名称进入详细索引页面。</p>')

    lines.append('<div class="entity-type-grid">')

    # 预加载编年索引统计（用于在时间卡片后插入）
    timeline_card = None
    year_map_file = Path(__file__).parent / 'year_ce_map.json'
    if year_map_file.exists():
        try:
            with open(year_map_file, 'r', encoding='utf-8') as f:
                year_map = json.load(f)
            year_set = set()
            total_refs = 0
            ruler_keys = set()
            for ch_data in year_map.values():
                for para_data in ch_data.values():
                    for surface, info in para_data.items():
                        if 'ce_year' in info:
                            year_set.add(info['ce_year'])
                        elif 'ruler_key' in info:
                            ruler_keys.add(info['ruler_key'])
                        total_refs += 1
            total_entries = len(year_set) + len(ruler_keys)
            timeline_card = [
                f'  <a href="timeline.html" class="entity-type-card">',
                f'    <span class="type-label time">编年</span>',
                f'    <span class="type-count">{total_entries} 个条目</span>',
                f'    <span class="type-total">{total_refs} 次引用（公元纪年索引）</span>',
                f'  </a>',
            ]
        except Exception:
            pass

    for type_key, _, css_class, label, filename in ENTITY_TYPES:
        entries = index.get(type_key, {})
        count = len(entries)
        total = sum(e['count'] for e in entries.values())

        if count == 0:
            continue

        lines.append(f'  <a href="{filename}" class="entity-type-card">')
        lines.append(f'    <span class="type-label {css_class}">{label}</span>')
        lines.append(f'    <span class="type-count">{count} 个条目</span>')
        lines.append(f'    <span class="type-total">{total} 次出现</span>')
        lines.append(f'  </a>')

        # 在时间卡片后紧跟编年卡片
        if type_key == 'time' and timeline_card:
            lines.extend(timeline_card)

    lines.append('</div>')

    lines.append('<nav class="chapter-nav">')
    lines.append('    <a href="../index.html" class="nav-home">回到主页</a>')
    lines.append('</nav>')

    lines.append('</body>')
    lines.append('</html>')

    return '\n'.join(lines)


def main():
    print("=" * 60)
    print("构建命名实体索引")
    print("=" * 60)

    # 加载别名映射
    alias_map = load_alias_map(ALIAS_FILE)
    alias_count = sum(len(v) for m in alias_map.values() for v in m.values())
    print(f"别名映射: {alias_count} 条")

    # 构建索引
    index = build_index(CHAPTER_DIR, alias_map)

    # 统计
    for type_key, _, _, label, _ in ENTITY_TYPES:
        entries = index[type_key]
        count = len(entries)
        total = sum(e['count'] for e in entries.values())
        if count > 0:
            print(f"  {label}: {count} 个条目, {total} 次出现")

    # 保存 JSON
    save_index_json(index, INDEX_JSON)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 生成各类型页面
    for type_key, _, css_class, label, filename in ENTITY_TYPES:
        entries = index[type_key]
        if not entries:
            continue

        page_html = generate_type_page(type_key, css_class, label, filename, entries)
        output_path = OUTPUT_DIR / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(page_html)
        print(f"  生成: {output_path} ({len(entries)} 条)")

    # 生成总览页
    landing_html = generate_landing_page(index)
    landing_path = OUTPUT_DIR / 'index.html'
    with open(landing_path, 'w', encoding='utf-8') as f:
        f.write(landing_html)
    print(f"  生成: {landing_path}")

    print("\n实体索引构建完成！")


if __name__ == '__main__':
    main()
