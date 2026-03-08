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
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CHAPTER_DIR = _PROJECT_ROOT / 'chapter_md'
OUTPUT_DIR = _PROJECT_ROOT / 'docs' / 'entities'
ALIAS_FILE = _PROJECT_ROOT / 'kg' / 'entities' / 'data' / 'entity_aliases.json'
INDEX_JSON = _PROJECT_ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
EVENT_DIR = _PROJECT_ROOT / 'kg' / 'events' / 'data'

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


def extract_events_from_index_files(event_dir):
    """从事件索引文件中提取事件条目

    解析每个 *_事件索引.md 的概览表，提取事件名称、类型、章节引用。

    Returns:
        list of (event_name, event_type, chapter_id, event_id, time_str, people, locations)
    """
    results = []
    if not event_dir.exists():
        return results

    for fpath in sorted(event_dir.glob('*_事件索引.md')):
        chapter_id = fpath.stem.replace('_事件索引', '')
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines_list = content.split('\n')

        # 第一遍：从详情段落提取 event_id → 段落位置 映射
        para_map = {}  # event_id → paragraph_number
        current_event_id = None
        for line in lines_list:
            stripped = line.strip()
            # 匹配 "### 001-001 黄帝诞生显灵"
            m = re.match(r'^###\s+(\S+)\s+', stripped)
            if m:
                current_event_id = m.group(1)
            # 匹配 "- **段落位置**: [1.2]"
            if current_event_id and stripped.startswith('- **段落位置**'):
                m2 = re.search(r'\[([^\]]+)\]', stripped)
                if m2:
                    para_map[current_event_id] = m2.group(1)

        # 第二遍：解析概览表格
        in_table = False
        for line in lines_list:
            line = line.strip()
            if line.startswith('| 事件ID'):
                in_table = True
                continue
            if in_table and line.startswith('|---'):
                continue
            if in_table and not line.startswith('|'):
                in_table = False
                continue
            if not in_table:
                continue

            cols = [c.strip() for c in line.split('|')]
            if len(cols) < 7:
                continue

            event_id = cols[1].strip()
            event_name = cols[2].strip()
            event_type = cols[3].strip()
            time_str = cols[4].strip()
            locations = cols[5].strip()
            people = cols[6].strip()

            if not event_name or not event_id:
                continue

            clean_name = re.sub(r'[@=$%&^~*!?🌿]', '', event_name).strip()
            para_num = para_map.get(event_id, '')
            if clean_name:
                results.append((clean_name, event_type, chapter_id,
                                event_id, time_str, people, locations,
                                para_num))

    return results


def _parse_ce_year(time_str):
    """从时间字符串中提取公元年。返回 int 或 None。

    示例: '%二世元年七月% （公元前209年）' → -209
          '%汉元年四月% （公元前206年）' → -206
          '-' → None
    """
    m = re.search(r'公元前(\d+)年', time_str)
    if m:
        return -int(m.group(1))
    m = re.search(r'公元(\d+)年', time_str)
    if m:
        return int(m.group(1))
    return None


def _strip_entity_tags(text):
    """去除实体标记符号，保留纯文本"""
    return re.sub(r'[@=$%&^~*!?🌿]', '', text).strip()


def _extract_people_list(people_str):
    """从人物字段提取人名列表。'@项羽@、@刘邦@' → ['项羽', '刘邦']"""
    names = re.findall(r'@([^@]+)@', people_str)
    return names if names else [_strip_entity_tags(people_str)] if people_str.strip() not in ('', '-') else []


def _extract_location_list(loc_str):
    """从地点字段提取地名列表。'=长安=、=洛阳=' → ['长安', '洛阳']"""
    places = re.findall(r'=([^=]+)=', loc_str)
    return places if places else [_strip_entity_tags(loc_str)] if loc_str.strip() not in ('', '-') else []


def build_event_index(event_dir):
    """构建事件索引，保留完整元数据（时间、人物、地点）

    Returns:
        {event_name: {'aliases': [...], 'refs': [...], 'count': int,
                      'event_type': str, 'event_id': str,
                      'ce_year': int|None, 'time_str': str,
                      'people': [str], 'locations': [str]}}
    """
    events = extract_events_from_index_files(event_dir)
    index = {}

    for name, etype, chapter_id, event_id, time_str, people, locations, para_num in events:
        # 同名事件用 event_id 区分（避免覆盖）
        key = f"{name}|{event_id}" if name in index else name
        if key in index:
            key = f"{name}|{event_id}"

        index[key] = {
            'aliases': [name],
            'refs': [(chapter_id, event_id)],
            'count': 1,
            'event_type': etype,
            'event_id': event_id,
            'ce_year': _parse_ce_year(time_str),
            'time_str': _strip_entity_tags(time_str) if time_str.strip() != '-' else '',
            'people': _extract_people_list(people),
            'locations': _extract_location_list(locations),
            'para_num': para_num,
        }

    return index


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


def _format_ce_year_label(ce_year, approximate=False):
    """格式化公元年显示"""
    if ce_year is None:
        return '时间不详'
    prefix = '约' if approximate else ''
    if ce_year < 0:
        return f'{prefix}前{-ce_year}年'
    return f'{prefix}{ce_year}年'


def _ce_year_to_period(ce_year):
    """将公元年映射到历史分期（按君主/皇帝），用于时间轴分组"""
    if ce_year is None:
        return ('未知时期', 99999)
    y = ce_year
    # ── 上古 ──
    if y <= -2100: return ('五帝时代（约前2700-前2100年）', -2700)
    if y <= -1600: return ('夏朝（约前2100-前1600年）', -2100)
    if y <= -1046: return ('商朝（约前1600-前1046年）', -1600)
    # ── 西周 ──
    if y <= -771:  return ('西周（前1046-前771年）', -1046)
    # ── 春秋 ──
    if y <= -476:  return ('春秋（前770-前476年）', -770)
    # ── 战国 ──
    if y <= -221:  return ('战国（前475-前221年）', -475)
    # ── 秦朝（按皇帝）──
    if y <= -210:  return ('秦始皇（前221-前210年）', -221)
    if y <= -206:  return ('秦二世/子婴（前209-前207年）', -209)
    # ── 楚汉之争 ──
    if y <= -202:  return ('楚汉之争（前206-前202年）', -206)
    # ── 西汉（按皇帝）──
    if y <= -195:  return ('汉高祖（前202-前195年）', -202)
    if y <= -188:  return ('汉惠帝（前194-前188年）', -194)
    if y <= -180:  return ('吕后称制（前187-前180年）', -187)
    if y <= -157:  return ('汉文帝（前179-前157年）', -179)
    if y <= -141:  return ('汉景帝（前156-前141年）', -156)
    if y <= -87:   return ('汉武帝（前140-前87年）', -140)
    return ('其他', y)


# ─── 章节时代范围（用于完全无纪年事件的兜底推断）───
CHAPTER_ERA = {
    # 本纪
    "001": -2500,  # 五帝
    "002": -1900,  # 夏
    "003": -1300,  # 殷
    "004": -900,   # 周
    "005": -900,   # 秦本纪（秦非子约前900年~秦王政）
    "006": -230,   # 秦始皇
    "007": -207,   # 项羽
    "008": -205,   # 高祖
    "009": -190,   # 吕太后
    "010": -175,   # 孝文
    "011": -155,   # 孝景
    "012": -135,   # 孝武
    # 表
    "013": -1500, "014": -800, "015": -450, "016": -250,
    "017": -200, "018": -200, "019": -200, "020": -200,
    "021": -200, "022": -200,
    # 书
    "023": -300, "024": -300, "025": -300, "026": -300,
    "027": -300, "028": -300, "029": -300, "030": -150,
    # 世家
    "031": -800, "032": -800, "033": -800, "034": -800,
    "035": -1000, "036": -700, "037": -700, "038": -700,
    "039": -650, "040": -700, "041": -500, "042": -700,
    "043": -450, "044": -400, "045": -400, "046": -350,
    "047": -520, "048": -209, "049": -200, "050": -200,
    "051": -200, "052": -200, "053": -200, "054": -200,
    "055": -210, "056": -210, "057": -200, "058": -170,
    "059": -150, "060": -120,
    # 列传
    "061": -1050, "062": -200, "063": -200, "064": -200,
    "065": -500, "066": -300, "067": -200, "068": -200,
    "069": -334, "070": -330, "071": -350, "072": -300,
    "073": -280, "074": -400, "075": -300, "076": -300,
    "077": -300, "078": -300, "079": -270, "080": -284,
    "081": -300, "082": -300, "083": -300, "084": -350,
    "085": -250, "086": -250, "087": -250, "088": -250,
    "089": -210, "090": -200, "091": -200, "092": -210,
    "093": -210, "094": -200, "095": -200, "096": -200,
    "097": -200, "098": -200, "099": -200, "100": -200,
    "101": -200, "102": -180, "103": -170, "104": -170,
    "105": -160, "106": -160, "107": -160, "108": -150,
    "109": -150, "110": -200, "111": -130, "112": -130,
    "113": -130, "114": -130, "115": -130, "116": -130,
    "117": -140, "118": -140, "119": -130, "120": -130,
    "121": -150, "122": -200, "123": -150, "124": -130,
    "125": -130, "126": -130, "127": -130, "128": -130,
    "129": -500, "130": -100,
}


def _load_person_lifespans():
    """加载人物生卒年数据库"""
    lifespan_file = Path(__file__).resolve().parent.parent / "data" / "person_lifespans.json"
    if not lifespan_file.exists():
        return {}
    with open(lifespan_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('persons', {})


def _person_active_range(people_list, lifespans):
    """根据事件人物列表，计算人物生存期的交集区间

    Returns: (latest_birth, earliest_death) 或 (None, None)
    """
    ranges = []
    for person in people_list:
        if person in lifespans:
            info = lifespans[person]
            ranges.append((info['birth'], info['death']))
    if not ranges:
        return None, None
    latest_birth = max(b for b, d in ranges)
    earliest_death = min(d for b, d in ranges)
    if latest_birth <= earliest_death:
        return latest_birth, earliest_death
    return None, None


def infer_undated_events(event_entries):
    """为没有 CE 年的事件推断近似日期

    策略（优先级从高到低）：
    1. 人物生卒年交集中点（最可靠）
    2. 同章节相邻事件插值（用最近的已知日期）
    3. 章节时代兜底（最粗略）

    对已推断的日期，用人物生卒年做合理性检查和修正。
    """
    lifespans = _load_person_lifespans()

    # 按章节分组
    by_chapter = defaultdict(list)
    for key, entry in event_entries.items():
        ch_full = entry['refs'][0][0] if entry['refs'] else ''
        ch_num = ch_full[:3] if ch_full else ''
        event_id = entry.get('event_id', '')
        by_chapter[ch_num].append((key, entry, event_id))

    inferred_count = 0
    person_refined = 0

    for ch_id, events in by_chapter.items():
        events.sort(key=lambda x: x[2])

        # 收集已知 CE 年的位置
        dated_positions = []
        for i, (key, entry, eid) in enumerate(events):
            if entry.get('ce_year') is not None:
                dated_positions.append((i, entry['ce_year']))

        for i, (key, entry, eid) in enumerate(events):
            if entry.get('ce_year') is not None:
                continue

            inferred = None

            # 策略1: 人物生卒年交集
            people = entry.get('people', [])
            if people and lifespans:
                lb, ed = _person_active_range(people, lifespans)
                if lb is not None and ed is not None:
                    inferred = (lb + ed) // 2  # 取活跃期中点
                    person_refined += 1

            # 策略2: 章节内插值
            if inferred is None and dated_positions:
                prev_year = None
                next_year = None
                for pos, year in dated_positions:
                    if pos <= i:
                        prev_year = year
                    if pos >= i and next_year is None:
                        next_year = year

                if prev_year is not None and next_year is not None:
                    inferred = prev_year
                elif prev_year is not None:
                    inferred = prev_year
                elif next_year is not None:
                    inferred = next_year

            # 策略3: 章节时代兜底
            if inferred is None:
                inferred = CHAPTER_ERA.get(ch_id)

            if inferred is not None:
                # 合理性检查：用人物生卒年约束
                if people and lifespans:
                    lb, ed = _person_active_range(people, lifespans)
                    if lb is not None and ed is not None:
                        if inferred < lb - 20:
                            inferred = (lb + ed) // 2
                            person_refined += 1
                        elif inferred > ed + 20:
                            inferred = (lb + ed) // 2
                            person_refined += 1

                entry['ce_year_inferred'] = inferred
                entry['ce_year_approximate'] = True
                inferred_count += 1

    print(f"    其中 {person_refined} 个由人物生卒年约束/修正")
    return inferred_count


def generate_event_page(event_entries):
    """生成事件索引 HTML 页面，以时间为主索引"""
    total_events = len(event_entries)
    dated_count = sum(1 for e in event_entries.values() if e.get('ce_year') is not None)
    inferred_count = sum(1 for e in event_entries.values()
                         if e.get('ce_year') is None and e.get('ce_year_inferred') is not None)

    # 按时期分组（优先用精确年，否则用推断年）
    grouped_by_period = defaultdict(list)
    for name, entry in event_entries.items():
        effective_year = entry.get('ce_year') or entry.get('ce_year_inferred')
        period_name, period_sort = _ce_year_to_period(effective_year)
        display_name = name.split('|')[0]
        grouped_by_period[period_name].append((display_name, entry, period_sort))

    # 每组内按有效年+事件ID排序
    for period in grouped_by_period:
        grouped_by_period[period].sort(
            key=lambda x: (x[1].get('ce_year') or x[1].get('ce_year_inferred') or 99999,
                           x[1].get('event_id', '')))

    # 时期按时间排序
    period_order = sorted(grouped_by_period.keys(),
                          key=lambda p: grouped_by_period[p][0][2])

    # 收集所有事件类型用于筛选
    all_types = sorted(set(e.get('event_type', '') for e in event_entries.values()))

    lines = []
    lines.append('<!DOCTYPE html>')
    lines.append('<html lang="zh-CN">')
    lines.append('<head>')
    lines.append('    <meta charset="UTF-8">')
    lines.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    lines.append('    <title>事件索引 - 史记知识库</title>')
    lines.append('    <link rel="stylesheet" href="../css/shiji-styles.css">')
    lines.append('    <link rel="stylesheet" href="../css/entity-index.css">')
    lines.append('    <style>')
    lines.append('      .event-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 3px; }')
    lines.append('      .event-tag { font-size: 0.75em; padding: 1px 6px; border-radius: 3px;')
    lines.append('                   display: inline-block; line-height: 1.5; }')
    lines.append('      .tag-type { background: #f0e6d3; color: #8B4513; }')
    lines.append('      .tag-person { background: #fdf2e9; color: #a0522d; }')
    lines.append('      .tag-place { background: #fef9e7; color: #b8860b; }')
    lines.append('      .tag-time { background: #e8f8f5; color: #008b8b; font-weight: bold; }')
    lines.append('      .tag-time-approx { background: #f0f0e8; color: #6b8e6b;')
    lines.append('                         font-weight: normal; font-style: italic; }')
    lines.append('      .event-entry { display: flex; justify-content: space-between;')
    lines.append('                     align-items: flex-start; padding: 6px 8px;')
    lines.append('                     border-bottom: 1px solid #f0ebe3; }')
    lines.append('      .event-entry:hover { background: #faf8f5; }')
    lines.append('      .event-id { font-size: 0.75em; color: #999; font-family: monospace; }')
    lines.append('      .event-name { font-weight: 500; }')
    lines.append('      .event-name a { color: #3c2415; text-decoration: none; }')
    lines.append('      .event-name a:hover { text-decoration: underline; }')
    lines.append('      .event-chapter { font-size: 0.8em; color: #888; white-space: nowrap; }')
    lines.append('      .filter-bar { display: flex; gap: 8px; flex-wrap: wrap;')
    lines.append('                    margin: 12px 0; align-items: center; }')
    lines.append('      .filter-bar select { padding: 4px 8px; border: 1px solid #d4c5a9;')
    lines.append('                           border-radius: 4px; background: #faf8f5; }')
    lines.append('      details.letter-section { margin-bottom: 4px; }')
    lines.append('      details.letter-section > summary { cursor: pointer; user-select: none;')
    lines.append('                                         list-style: none; }')
    lines.append('      details.letter-section > summary::-webkit-details-marker { display: none; }')
    lines.append('      details.letter-section > summary::before { content: "▶ "; font-size: 0.8em;')
    lines.append('                                                  color: #999; }')
    lines.append('      details.letter-section[open] > summary::before { content: "▼ "; }')
    lines.append('    </style>')
    lines.append('</head>')
    lines.append('<body>')

    lines.append('<nav class="chapter-nav">')
    lines.append('    <a href="../index.html" class="nav-home">回到主页</a>')
    lines.append('    <a href="index.html" class="nav-next">实体索引</a>')
    lines.append('</nav>')

    lines.append('<h1>事件时间索引</h1>')
    lines.append(f'<p class="index-stats">共 <strong>{total_events}</strong> 个事件，'
                 f'<strong>{dated_count}</strong> 个有精确纪年，'
                 f'<strong>{inferred_count}</strong> 个推断纪年，'
                 f'跨越 <strong>{len(period_order) - (1 if "未知时期" in grouped_by_period else 0)}</strong> 个历史分期</p>')
    lines.append('<p class="index-stats" style="font-size:0.85em; color:#666;">'
                 '时间标签：'
                 '<span class="event-tag tag-time" style="font-size:1em;">前260年</span> 精确纪年　'
                 '<span class="event-tag tag-time tag-time-approx" style="font-size:1em;">约前260年</span> 推断纪年'
                 '（据人物生卒年、相邻事件、章节时代推断）</p>')

    # 搜索 + 类型筛选
    lines.append('<div class="filter-bar">')
    lines.append('    <input type="text" id="filter-input" placeholder="搜索事件、人物、地点..."'
                 ' style="flex:1; min-width:200px; padding:4px 8px; border:1px solid #d4c5a9;'
                 ' border-radius:4px;">')
    lines.append('    <select id="type-filter" onchange="filterEvents()">')
    lines.append('      <option value="">全部类型</option>')
    for t in all_types:
        if t:
            lines.append(f'      <option value="{html.escape(t)}">{html.escape(t)}</option>')
    lines.append('    </select>')
    lines.append('</div>')

    # 时期导航栏
    lines.append('<div class="pinyin-nav">')
    for period in period_order:
        count = len(grouped_by_period[period])
        short = period.split('（')[0]  # 取括号前的简称
        lines.append(f'  <a href="#period-{html.escape(short)}" class="pinyin-letter">'
                     f'{html.escape(short)}<span class="letter-count">{count}</span></a>')
    lines.append('</div>')

    # 事件列表（按时期分节）
    lines.append('<div class="entity-index">')

    for pi, period in enumerate(period_order):
        group = grouped_by_period[period]
        short = period.split('（')[0]
        # 默认展开前3个分期（上古），其余折叠
        open_attr = ' open' if pi < 3 else ''
        lines.append(f'<details class="letter-section" id="period-{html.escape(short)}"{open_attr}>')
        lines.append(f'  <summary class="letter-heading">{html.escape(period)}（{len(group)}）</summary>')

        for display_name, entry, _ in group:
            event_id = entry.get('event_id', '')
            etype = entry.get('event_type', '')
            ce_year = entry.get('ce_year')
            people = entry.get('people', [])
            locations = entry.get('locations', [])
            ch_id = entry['refs'][0][0] if entry['refs'] else ''
            ch_title = extract_chapter_title(ch_id) if ch_id else ''
            para_num = entry.get('para_num', '')

            esc_name = html.escape(display_name)
            esc_id = html.escape(event_id)

            lines.append(f'  <div class="event-entry" data-type="{html.escape(etype)}"'
                         f' id="event-{esc_id}">')

            # 左侧：事件名 + 标签
            lines.append('    <div style="flex:1">')
            # 事件名链接到章节段落（含事件编号）
            id_label = f'<span class="event-id">{esc_id}</span> ' if event_id else ''
            if ch_id:
                anchor = f'#pn-{para_num}' if para_num else ''
                lines.append(f'      <div class="event-name">{id_label}'
                             f'<a href="../chapters/{ch_id}.html{anchor}">{esc_name}</a></div>')
            else:
                lines.append(f'      <div class="event-name">{id_label}{esc_name}</div>')

            is_approximate = entry.get('ce_year_approximate', False)
            effective_year = ce_year or entry.get('ce_year_inferred')

            # 标签行
            lines.append('      <div class="event-tags">')
            # 时间标签
            if effective_year is not None:
                approx_class = ' tag-time-approx' if is_approximate else ''
                lines.append(f'        <span class="event-tag tag-time{approx_class}">'
                             f'{_format_ce_year_label(effective_year, is_approximate)}</span>')
            # 类型标签
            if etype:
                lines.append(f'        <span class="event-tag tag-type">'
                             f'{html.escape(etype)}</span>')
            # 人物标签（最多显示4个）
            for p in people[:4]:
                lines.append(f'        <span class="event-tag tag-person">'
                             f'{html.escape(p)}</span>')
            if len(people) > 4:
                lines.append(f'        <span class="event-tag tag-person">+{len(people)-4}</span>')
            # 地点标签（最多显示2个）
            for loc in locations[:2]:
                lines.append(f'        <span class="event-tag tag-place">'
                             f'{html.escape(loc)}</span>')
            if len(locations) > 2:
                lines.append(f'        <span class="event-tag tag-place">'
                             f'+{len(locations)-2}</span>')
            lines.append('      </div>')

            lines.append('    </div>')

            # 右侧：章节名 + 段落号
            if ch_title:
                anchor = f'#pn-{para_num}' if para_num else ''
                para_label = f' [{para_num}]' if para_num else ''
                lines.append(f'    <div class="event-chapter">'
                             f'<a href="../chapters/{ch_id}.html{anchor}" '
                             f'class="chapter-ref-name">{html.escape(ch_title)}{para_label}</a></div>')

            lines.append('  </div>')

        lines.append('</details>')

    lines.append('</div>')

    # 筛选脚本
    lines.append('''<script>
function filterEvents() {
  const q = document.getElementById('filter-input').value.toLowerCase();
  const typeFilter = document.getElementById('type-filter').value;
  document.querySelectorAll('.event-entry').forEach(el => {
    const text = el.textContent.toLowerCase();
    const type = el.getAttribute('data-type') || '';
    const matchText = !q || text.includes(q);
    const matchType = !typeFilter || type === typeFilter;
    el.style.display = (matchText && matchType) ? '' : 'none';
  });
  // 隐藏空的时期段，搜索时自动展开匹配的
  document.querySelectorAll('details.letter-section').forEach(sec => {
    const visible = sec.querySelectorAll('.event-entry:not([style*="display: none"])');
    if (visible.length === 0) {
      sec.style.display = 'none';
    } else {
      sec.style.display = '';
      if (q || typeFilter) sec.open = true;
    }
  });
}
document.getElementById('filter-input').addEventListener('input', filterEvents);
</script>''')

    lines.append('<nav class="chapter-nav">')
    lines.append('    <a href="../index.html" class="nav-home">回到主页</a>')
    lines.append('    <a href="index.html" class="nav-next">实体索引</a>')
    lines.append('</nav>')

    lines.append('</body>')
    lines.append('</html>')

    return '\n'.join(lines)


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
    year_map_file = _PROJECT_ROOT / 'kg' / 'year_ce_map.json'
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

    # 事件索引卡片
    event_entries = index.get('event', {})
    if event_entries:
        event_count = len(event_entries)
        # 统计事件类型数
        event_types = set(e.get('event_type', '') for e in event_entries.values())
        lines.append(f'  <a href="event.html" class="entity-type-card">')
        lines.append(f'    <span class="type-label event">事件</span>')
        lines.append(f'    <span class="type-count">{event_count} 个条目</span>')
        lines.append(f'    <span class="type-total">{len(event_types)} 种类型</span>')
        lines.append(f'  </a>')

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

    # 构建事件索引
    event_index = build_event_index(EVENT_DIR)
    # 为无纪年事件推断近似日期
    inferred = infer_undated_events(event_index)
    print(f"  事件日期推断: {inferred} 个事件获得近似纪年")
    index['event'] = event_index

    # 统计
    for type_key, _, _, label, _ in ENTITY_TYPES:
        entries = index[type_key]
        count = len(entries)
        total = sum(e['count'] for e in entries.values())
        if count > 0:
            print(f"  {label}: {count} 个条目, {total} 次出现")

    # 事件统计
    event_count = len(event_index)
    event_total = sum(e['count'] for e in event_index.values())
    print(f"  事件: {event_count} 个条目, {event_total} 次出现")

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

    # 生成事件索引页
    if event_index:
        page_html = generate_event_page(event_index)
        output_path = OUTPUT_DIR / 'event.html'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(page_html)
        print(f"  生成: {output_path} ({len(event_index)} 条)")

    # 生成总览页
    landing_html = generate_landing_page(index)
    landing_path = OUTPUT_DIR / 'index.html'
    with open(landing_path, 'w', encoding='utf-8') as f:
        f.write(landing_html)
    print(f"  生成: {landing_path}")

    print("\n实体索引构建完成！")


if __name__ == '__main__':
    main()
