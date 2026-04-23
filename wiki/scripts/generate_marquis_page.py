#!/usr/bin/env python3
"""
生成汉代侯国 wiki 页面 (v2).

数据源:
  - data/tables/data/018|019|020_*.json  年表
  - chapter_md/*.tagged.md              史记正文（含段落号 PN）
  - docs/notes_cache/NNN-notes.json     三家注（简体）
  - wiki/data/semantic.json             人物信息

用法:
    python3 wiki/scripts/generate_marquis_page.py 平阳
    python3 wiki/scripts/generate_marquis_page.py --all [--table 018]
    python3 wiki/scripts/generate_marquis_page.py --list
    python3 wiki/scripts/generate_marquis_page.py --dry-run 平阳
    python3 wiki/scripts/generate_marquis_page.py --all --force
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR   = ROOT / 'data/tables/data'
CHAPTER_DIR  = ROOT / 'chapter_md'
NOTES_DIR    = ROOT / 'docs/notes_cache'
PAGES_DIR    = ROOT / 'wiki/public/pages'
SEMANTIC_DB  = ROOT / 'wiki/data/semantic.json'
ADD_PAGE     = ROOT / 'wiki/scripts/butler/add_page.py'
EDIT_PAGE    = ROOT / 'wiki/scripts/butler/edit_page.py'

TABLE_FILES = {
    '018': TABLES_DIR / '018_高祖功臣侯者年表.json',
    '019': TABLES_DIR / '019_惠景间侯者年表.json',
    '020': TABLES_DIR / '020_建元以来侯者年表.json',
}
TABLE_TAGS = {'018': '高祖功臣', '019': '惠景间受封', '020': '武帝受封'}

# 年号对应元年的公元前值（负数 = BCE）
# 计算: 元年的 BCE = |value|, 第 N 年的 BCE = |value| - N + 1
ERA_BCE: dict[str, int] = {
    '高祖': -206, '孝惠': -194, '高后': -187,
    '孝文': -179, '后元文': -163,          # 孝文后元
    '孝景': -156, '中元': -149, '后元景': -143,
    '建元': -140,
    '元光': -134, '元朔': -128, '元狩': -122,
    '元鼎': -116, '元封': -110, '太初': -104,
    '天汉': -100, '太始': -96, '征和': -92, '后元武': -88,
}
# 用于从列名或日期字符串中识别年号
ERA_KEYS_SORTED = sorted(ERA_BCE.keys(), key=len, reverse=True)

# 军事动词标注（用于识别军功行文）
MILITARY_VERBS = re.compile(r'[攻击破斩拔定降取围虏平灭率将]')
# 封侯相关动词标注
ENFEOFF_RE = re.compile(r'⟦○封⟧|⟦○食邑⟧|封为.*侯|侯.*元年|以.*侯')

# 表章节（010-022）
TABLE_CHAPTER_PREFIXES = tuple(f'{i:03d}_' for i in range(10, 23))

# ─── 中文数字转整数 ──────────────────────────────────────────────────────────

_CN_DIGIT = {'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
_CN_UNIT  = {'十':10,'百':100,'千':1000}

def cn_to_int(s: str) -> int:
    """将简单中文数字（元/一至三十六）转为整数"""
    if not s or s == '元':
        return 1
    # 常规处理: 二十三 → 23
    result = 0
    unit = 1
    s = s.strip()
    # 先处理 "后N年" 中的 N
    s = re.sub(r'^后', '', s)
    if not s:
        return 1

    # 倒序累加
    digits = []
    for ch in reversed(s):
        if ch in _CN_UNIT:
            unit = _CN_UNIT[ch]
            if not digits or digits[-1][1] < unit:
                digits.append((0, unit))
        elif ch in _CN_DIGIT:
            if digits and digits[-1][0] == 0:
                digits[-1] = (_CN_DIGIT[ch], digits[-1][1])
            else:
                digits.append((_CN_DIGIT[ch], unit))
                unit = 1
    for d, u in digits:
        result += d * u
    # 处理 "十N" (十 alone = 10)
    if not result and '十' in s:
        result = 10
    return result or 1


def year_to_bce(year_num: int, era: str) -> int | None:
    """年号第 year_num 年对应的 BCE 年份"""
    if era not in ERA_BCE:
        return None
    return abs(ERA_BCE[era]) - year_num + 1


def detect_era(text: str) -> str | None:
    """从文本片段中识别年号（返回 ERA_BCE 中的 key）"""
    for k in ERA_KEYS_SORTED:
        if k in text:
            return k
    return None


_ANNO_RE = re.compile(
    r'(高祖|孝惠|高后|孝文|孝景|建元|元光|元朔|元狩|元鼎|元封|太初|天汉|太始|征和)'
    r'(后元)?'
    r'([元一二三四五六七八九十百]+)年'
)

def annotate_bce(text: str) -> str:
    """给 '年号N年' 加上公元前注释"""
    def repl(m):
        era_base = m.group(1)
        hou_yuan  = m.group(2)  # '后元' or None
        year_cn   = m.group(3)
        era_key   = era_base + ('后元' if hou_yuan else '')
        # 处理后元
        if hou_yuan:
            if era_base == '孝文':
                era_key = '后元文'
            elif era_base == '孝景':
                era_key = '后元景'
            else:
                era_key = '后元武'
        yn = cn_to_int(year_cn)
        bce = year_to_bce(yn, era_key)
        if bce is None:
            return m.group(0)
        return f'{m.group(0)}（前{bce}）'
    return _ANNO_RE.sub(repl, text)


def era_base_name(col: str) -> str:
    """从列名提取年号: '高祖十二' → '高祖', '元光' → '元光'"""
    col = re.sub(r'[，。至].*$', '', col)      # 去掉复合列的第二段
    col = re.sub(r'[一二三四五六七八九十百]+$', '', col).strip()
    return col or col


def extract_founding_date(row: dict) -> str:
    """从年表第一个有效列提取分封时间，并加公元前注释"""
    skip = {'国名', '侯功', '侯第', '_table_id', '_table_title'}
    for col, text in row.items():
        if col in skip or not text:
            continue
        era = era_base_name(col)
        m = re.search(
            r'([元一二三四五六七八九十]+年(?:[一二三四五六七八九十]+月)?'
            r'(?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])?)',
            text
        )
        if m:
            raw_date = f'{era}{m.group(1)}'
            return annotate_bce(raw_date)
        break
    return ''


def extract_household(侯功: str) -> str:
    m = re.search(r'([一二三四五六七八九十百千万\d]+(?:万)?[零\d百千]*户)', 侯功)
    return m.group(1) if m else ''

# ─── 标注去除（保留显示文本，保留 PN） ───────────────────────────────────────

_TAG_PREFIX = re.compile('[^一-鿿㐀-䶿（）！？，。、：；""a-zA-Z0-9 \t-]+')

def _inner(tag_content: str) -> str:
    if '|' in tag_content:
        display = tag_content.split('|')[0]
    else:
        display = tag_content
    return _TAG_PREFIX.sub('', display)

def strip_tags(text: str) -> str:
    t = re.sub(r'〖([^〗]*)〗', lambda m: _inner(m.group(1)), text)
    t = re.sub(r'⟦([^⟧]*)⟧',  lambda m: _inner(m.group(1)), t)
    t = re.sub(r'〘([^〙]*)〙',  lambda m: _inner(m.group(1)), t)
    t = re.sub(r'^\s*#+\s+', '', t, flags=re.MULTILINE)
    return re.sub(r'\s+', ' ', t).strip()

_PN_LINE = re.compile(r'^\[(\d+(?:\.\d+)*)\]\s*(.*)')

def parse_chapter_lines(path: Path) -> list[tuple[str, str]]:
    """解析章节文件，返回 [(pn, clean_text), ...] 只含有实质文本的行"""
    results = []
    for raw in path.read_text(encoding='utf-8').splitlines():
        m = _PN_LINE.match(raw.strip())
        if m:
            pn   = m.group(1)
            text = strip_tags(m.group(2)).strip()
            if len(text) > 5:
                results.append((pn, text))
    return results

# ─── 数据加载 ────────────────────────────────────────────────────────────────

def load_tables() -> list[dict]:
    rows = []
    for tid, path in TABLE_FILES.items():
        if not path.exists():
            continue
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        for row in data['rows']:
            row = dict(row)
            row['_table_id']    = tid
            row['_table_title'] = data['table_info']['title']
            rows.append(row)
    return rows

def load_semantic() -> dict:
    if not SEMANTIC_DB.exists():
        return {}
    with open(SEMANTIC_DB, encoding='utf-8') as f:
        d = json.load(f)
    return d.get('entities', {})

@lru_cache(maxsize=None)
def load_notes_for_chapter(chapter_num: str) -> list[dict]:
    """加载三家注 JSON（notes_cache 中的简体版）"""
    path = NOTES_DIR / f'{chapter_num}-notes.json'
    if not path.exists():
        return []
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    return d.get('notes', [])

@lru_cache(maxsize=None)
def load_chapter_file(chapter_id: str) -> list[tuple[str, str]]:
    """加载章节文件并解析为 [(pn, text), ...]"""
    path = CHAPTER_DIR / f'{chapter_id}.tagged.md'
    if not path.exists():
        return []
    return parse_chapter_lines(path)

def find_row(guo_name: str, rows: list[dict]) -> dict | None:
    clean = guo_name.replace('侯国', '').replace('侯', '').strip('。 ')
    for row in rows:
        n = row.get('国名', '').strip('。 ')
        if n == clean or n == guo_name:
            return row
    return None

# ─── 年表解析 ────────────────────────────────────────────────────────────────

# 匹配文中出现的完整年号+年份，如 "元鼎三年" "元光五年" 等
_EXPLICIT_DATE_RE = re.compile(
    r'(高祖|孝惠|高后|孝文|孝景|建元|元光|元朔|元狩|元鼎|元封|太初|天汉|太始|征和)'
    r'(后元)?'
    r'(后?[元一二三四五六七八九十]+)年'
    r'(?:([一二三四五六七八九十]+)月)?'
    r'(?:([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]))?'
)


def parse_era_col(col_name: str, text: str) -> list[dict]:
    if not text or not text.strip():
        return []
    era = era_base_name(col_name)
    title_re = re.compile(
        r'(后?[元一二三四五六七八九十]+年(?:[一二三四五六七八九十]+月)?'
        r'(?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])?)?'
        r'[，。]?'
        r'((?:[^\s，。]{1,3}侯|今侯))([一-鿿]{1,5})[。]?元年'
    )
    items = []
    for m in title_re.finditer(text):
        date_raw = (m.group(1) or '').strip('，。 ')
        raw_title = m.group(2)
        name      = m.group(3)
        # 若 date_raw 是纯数字年（如"三年"），扩展搜索窗口找完整年号（如"元光三年"）
        if date_raw and not detect_era(date_raw):
            # m.start() 指向正则匹配起始位置，往前多取15字符覆盖年号前缀
            window = text[max(0, m.start() - 15): m.start() + len(date_raw) + 2]
            em_list = list(_EXPLICIT_DATE_RE.finditer(window))
            if em_list:
                date_raw = em_list[-1].group(0)  # 取最近的年号
        # 计算 BCE 年份
        # 优先检测 date_raw 中是否已经含有明确的年号（如"元鼎三年"）
        date_anno = ''
        if date_raw:
            detected_era = detect_era(date_raw)
            if detected_era:
                # date_raw 本身含年号，直接 annotate
                date_anno = annotate_bce(date_raw)
            else:
                # 用列名年号前缀；若 date_raw 以"后"开头，映射到该帝后元
                use_era = era
                if date_raw.startswith('后'):
                    # 孝文后元 / 孝景后元 / 武帝后元
                    era_map = {'孝文': '后元文', '孝景': '后元景', '建元': '后元武'}
                    use_era = era_map.get(era, era)
                yn_m = re.search(r'[元一二三四五六七八九十]+', date_raw)
                yn   = cn_to_int(yn_m.group()) if yn_m else 1
                bce  = year_to_bce(yn, use_era)
                if bce:
                    date_anno = f'{era}{date_raw}（前{bce}）'
                else:
                    date_anno = f'{era}{date_raw}'
        items.append({
            'marquis':   name,
            'title':     raw_title,
            'date_str':  date_anno or era,
            'col':       col_name,
            'events':    [],
        })
    if items:
        m2 = re.search(r'(坐[^。]+国除|薨，无後，国除|[^\s，。]+国除)', text)
        if m2:
            items[-1]['events'].append(m2.group(0))
    return items

def parse_row_succession(row: dict) -> list[dict]:
    skip = {'国名', '侯功', '侯第', '_table_id', '_table_title'}
    all_items = []
    for col, text in row.items():
        if col in skip:
            continue
        all_items.extend(parse_era_col(col, text or ''))
    return all_items

def extract_extinction(row: dict) -> str | None:
    skip = {'国名', '侯功', '侯第', '_table_id', '_table_title'}
    for col, text in row.items():
        if col in skip or not text:
            continue
        for sent in re.split(r'[。；]', text):
            if '国除' in sent:
                return annotate_bce(sent.strip())
    return None

# ─── 三家注检索 ──────────────────────────────────────────────────────────────

def search_notes(chapter_num: str, keywords: list[str]) -> list[dict]:
    """在某章的三家注中搜索关键词，返回命中的 note 列表"""
    notes = load_notes_for_chapter(chapter_num)
    results = []
    kw_re = re.compile('|'.join(re.escape(k) for k in keywords if k))
    for n in notes:
        anchor  = n.get('anchor_text', '')
        ctx_all = anchor + n.get('before_context', '') + n.get('after_context', '')
        note_texts = ' '.join(i['text'] for i in n.get('items', []))
        if kw_re.search(ctx_all) or kw_re.search(note_texts):
            results.append(n)
    return results

def format_note(n: dict) -> str:
    lines = [f'**锚文**：{n["anchor_text"]}']
    for item in n.get('items', []):
        lines.append(f'- **{item["label"]}**：{item["text"]}')
    return '\n'.join(lines)

# ─── 搜索关键词构建 ─────────────────────────────────────────────────────────

def build_keywords(guo_name: str, founder_name: str,
                   founder_aliases: list[str]) -> tuple[list[str], list[str]]:
    """
    返回 (strong_kws, weak_kws).
    strong: 2+ 字精确词，可靠。
    weak: 需要上下文辅助确认的词（目前仅内部使用，不传入 search）。
    单字国名改为 "X侯"/"XX侯" 复合形式，避免泛化匹配。
    """
    strong: list[str] = []

    # 国名
    if len(guo_name) >= 2:
        strong.append(guo_name)
    else:
        # 单字国名加"侯"后缀，如 "壮侯"
        strong.append(guo_name + '侯')

    # 创始人名（≥2 字）
    if founder_name and len(founder_name) >= 2:
        strong.append(founder_name)

    # 别名（≥2 字）
    for a in founder_aliases:
        if len(a) >= 2 and a not in strong:
            strong.append(a)

    weak = [guo_name] if len(guo_name) == 1 else []
    return strong, weak


def excerpt_hit(text: str, keywords: list[str], radius: int = 50) -> str:
    """
    按句子边界截取含关键词的片段。
    策略：先按句号切句，找含关键词的句子；若该句仍超长再按逗号切分句，
    只保留含关键词的分句（+前一分句作上下文）。
    """
    # 按句号（。！？）切成句子
    sentences = re.split(r'(?<=[。！？])', text)
    matching = [s for s in sentences if any(kw in s for kw in keywords)]
    if not matching:
        # 无句号段落，退回字符窗口
        pos = next((text.find(kw) for kw in keywords if kw in text), -1)
        if pos == -1:
            return text[:radius * 2]
        start, end = max(0, pos - radius), min(len(text), pos + radius)
        return ('……' if start > 0 else '') + text[start:end] + ('……' if end < len(text) else '')

    result_parts: list[str] = []
    for sent in matching:
        # 按逗号切分句，只取含关键词的分句；若以逗号结尾则追加下一分句补完句意
        clauses = re.split(r'(?<=[，；])', sent)
        if len(clauses) > 1:
            kept: list[str] = []
            for i, cl in enumerate(clauses):
                if any(kw in cl for kw in keywords):
                    kept.append(cl)
                    # 若关键词分句以逗号/分号结尾，补入下一分句
                    if cl.endswith(('，', '；')) and i + 1 < len(clauses):
                        kept.append(clauses[i + 1])
            trimmed = ''.join(kept)
            prefix = '……' if sent.find(kept[0]) > 0 else ''
            result_parts.append(prefix + trimmed)
        else:
            result_parts.append(sent)

    snippet = '……'.join(result_parts)
    # 若截取位置不在段首，加省略号提示
    first_sent_start = text.find(matching[0])
    if first_sent_start > 0:
        snippet = '……' + snippet
    return snippet


def is_relevant(text: str, guo_name: str, founder_name: str) -> bool:
    """
    二次相关性过滤：排除国名出现在无关语境（人名、天文、地理）中的误报。

    相关条件（满足任一）:
    1. 创始人名（≥2字）出现在行中
    2. 国名 + 侯 紧邻（即侯国称号形式：南宫侯、平阳侯）
    3. 封 + 国名 在 10 字范围内（分封记载）
    4. 国名 + 县/郡/城（地望引用）
    """
    # 创始人名命中最可靠
    if founder_name and len(founder_name) >= 2 and founder_name in text:
        return True

    if guo_name not in text:
        return False

    # 国名紧跟 侯（标准侯号形式）
    if re.search(re.escape(guo_name) + r'侯', text):
        return True

    # 封...国名 / 国名...封 近距离（分封语境）
    if re.search(r'封.{0,12}' + re.escape(guo_name), text):
        return True
    if re.search(re.escape(guo_name) + r'.{0,6}封', text):
        return True

    # 国名 + 地名后缀（地望引用）
    if re.search(re.escape(guo_name) + r'(?:县|郡|城|地|亭)', text):
        return True

    # 明确的侯国语境词（要求与国名在 20 字窗口内相邻，避免长段落误报）
    for clue in ['食邑', '受封', '列侯', '功臣', '剖符']:
        for m in re.finditer(re.escape(clue), text):
            window = text[max(0, m.start() - 20): m.end() + 20]
            if guo_name in window:
                return True

    return False


# ─── 全文检索（史记正文） ────────────────────────────────────────────────────

def search_chapters_lines(
    keywords: list[str],
    include_tables: bool = False,
    max_per_chapter: int = 6,
) -> dict[str, list[tuple[str, str]]]:
    """
    返回 {chapter_id: [(pn, clean_line), ...]}
    只匹配 keywords 中的词（调用前已由 build_keywords 过滤为 strong 词）
    """
    if not keywords:
        return {}
    kw_re = re.compile('|'.join(re.escape(k) for k in keywords if k))
    results: dict[str, list[tuple[str, str]]] = {}

    for cf in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        is_table = any(cf.name.startswith(p) for p in TABLE_CHAPTER_PREFIXES)
        if is_table and not include_tables:
            continue
        cid = cf.name.replace('.tagged.md', '')
        lines = load_chapter_file(cid)
        hits: list[tuple[str, str]] = []
        seen = set()
        for pn, text in lines:
            if kw_re.search(text) and text not in seen:
                hits.append((pn, text))
                seen.add(text)
        if hits:
            results[cid] = hits[:max_per_chapter]
    return results

def filter_military(hits: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """过滤出含军事动词的行"""
    return [(pn, t) for pn, t in hits if MILITARY_VERBS.search(t)]

def filter_enfeoffment(hits: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """过滤出含封赐信息的行"""
    return [(pn, t) for pn, t in hits if
            any(kw in t for kw in ['封', '侯', '食邑', '剖符', '赐爵'])]

# ─── 人物信息 ────────────────────────────────────────────────────────────────

def lookup_person(name: str, semantic: dict) -> dict | None:
    if name in semantic:
        return semantic[name]
    for eid, ent in semantic.items():
        if name in ent.get('aliases', []):
            return ent
    return None

def fmt_year(ce: int | None) -> str:
    if ce is None:
        return '?'
    return f'前 {-ce}' if ce < 0 else str(ce)

def format_person_brief(ent: dict, name: str) -> str:
    parts = []
    life = ent.get('lifespan')
    if life:
        b, d = life.get('birth'), life.get('death')
        note = life.get('note', '')
        s = f'{fmt_year(b)} — {fmt_year(d)}'
        if note:
            s += f'（{note}）'
        parts.append(f'生卒：{s}')
    aliases = [a for a in ent.get('aliases', []) if a != name]
    if aliases:
        parts.append(f'别名：{"、".join(aliases[:5])}')
    return '；'.join(parts)

def get_main_chapter(ent: dict) -> str | None:
    """返回人物传记主章节（排除年表，偏好世家/列传）"""
    chaps = [c for c in ent.get('chapters', [])
             if not any(c['chapter'].startswith(p) for p in TABLE_CHAPTER_PREFIXES)]
    if not chaps:
        return None
    def sort_key(c):
        num = int(c['chapter'][:3])
        # 世家(031-060)和列传(061-130)加权，本纪(001-012)不加权
        boost = 15 if num >= 31 else 0
        return c['count'] + boost
    return max(chaps, key=sort_key)['chapter']

# ─── 创始人传略提取 ──────────────────────────────────────────────────────────

def extract_biography(founder_name: str, main_chapter: str) -> dict:
    """
    从主传章节提取:
      - opening: 开篇介绍（前 3 段）
      - military: 军功记录（含军事动词的段落）
      - enfeoffment: 封侯相关段落
      - summary: 功绩统计段（"功：" 开头）
    """
    lines = load_chapter_file(main_chapter)
    if not lines:
        return {}

    opening, military, enfeoffment, summary = [], [], [], []
    kw_re = re.compile(re.escape(founder_name))

    for pn, text in lines:
        # 前几段 (pn 是 "1", "2", "3" 等)
        try:
            pn_int = int(pn.split('.')[0])
        except ValueError:
            pn_int = 99
        if pn_int <= 3 and kw_re.search(text):
            opening.append((pn, text))
        if kw_re.search(text) or pn_int <= 4:
            if MILITARY_VERBS.search(text) and len(text) > 20:
                military.append((pn, text))
            if any(kw in text for kw in ['封', '侯', '食邑', '剖符', '赐爵']):
                enfeoffment.append((pn, text))
            if re.search(r'^参功|^功：|凡下|所将卒|斩首', text):
                summary.append((pn, text))

    return {
        'opening':     opening[:3],
        'military':    military[:8],
        'enfeoffment': enfeoffment[:4],
        'summary':     summary[:2],
    }

# ─── 封侯旁证检索 ────────────────────────────────────────────────────────────

def find_secondary_enfeoffment(guo_name: str, founder_name: str) -> dict[str, list[tuple[str, str]]]:
    """
    在非年表章节中找分封旁证:
    包含 "封XXX" / "侯XXX元年" / "XX侯" + 人名 的行
    """
    keywords = [guo_name, founder_name]
    all_hits = search_chapters_lines(keywords, include_tables=False, max_per_chapter=10)
    result = {}
    for cid, hits in all_hits.items():
        enc = filter_enfeoffment(hits)
        if enc:
            result[cid] = enc[:4]
    return result

# ─── 史记十表检索 ────────────────────────────────────────────────────────────

def search_in_tables(strong_kws: list[str]) -> dict[str, list[tuple[str, str]]]:
    """在史记十表（010-022）中检索，只用 strong 关键词"""
    if not strong_kws:
        return {}
    kw_re = re.compile('|'.join(re.escape(k) for k in strong_kws if k))
    results = {}
    for cf in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        if not any(cf.name.startswith(p) for p in TABLE_CHAPTER_PREFIXES):
            continue
        cid = cf.name.replace('.tagged.md', '')
        # 跳过主要年表（018-020），那些是来源
        if any(cid.startswith(p) for p in ['018_', '019_', '020_']):
            continue
        lines = load_chapter_file(cid)
        hits = [(pn, t) for pn, t in lines if kw_re.search(t)]
        if hits:
            results[cid] = hits[:4]
    return results

# ─── 三家注汇集 ──────────────────────────────────────────────────────────────

def collect_sanjia(founder_name: str, guo_name: str, main_chapter: str,
                   other_chapters: list[str]) -> list[tuple[str, dict]]:
    """
    收集相关三家注，返回 [(chapter_id, note_dict), ...]
    只用 2+ 字关键词，避免单字泛化
    """
    keywords = [k for k in [founder_name, guo_name] if k and len(k) >= 2]
    if not keywords and founder_name:
        keywords = [founder_name]  # 只有单字名时才退而求其次
    results = []
    seen_anchors: set[str] = set()

    for chap in ([main_chapter] + other_chapters)[:6]:
        if not chap:
            continue
        num = chap[:3]
        for n in search_notes(num, keywords):
            anchor = n.get('anchor_text', '')
            if anchor in seen_anchors:
                continue
            seen_anchors.add(anchor)
            # 只保留有实质内容的注
            if any(len(i.get('text', '')) > 5 for i in n.get('items', [])):
                results.append((chap, n))

    return results[:12]

# ─── 生成页面 ────────────────────────────────────────────────────────────────

def build_page(row: dict, semantic: dict) -> str:
    guo_name     = row['国名'].strip('。 ')
    hou_gong     = row.get('侯功', '').strip()
    table_id     = row.get('_table_id', '018')
    table_title  = row.get('_table_title', '')
    table_tag    = TABLE_TAGS.get(table_id, '')
    page_id      = f'{guo_name}侯国'
    households   = extract_household(hou_gong)
    founding_date = extract_founding_date(row)
    succession   = parse_row_succession(row)
    extinction   = extract_extinction(row)

    founder_entry  = succession[0] if succession else {}
    founder_name   = founder_entry.get('marquis', '')
    founder_title  = founder_entry.get('title', '').replace('今侯', '').strip()
    founder_date   = founder_entry.get('date_str', '')

    # ── 人物信息 ──────────────────────────────────────────────────────────────
    founder_ent      = lookup_person(founder_name, semantic) if founder_name else None
    founder_brief    = format_person_brief(founder_ent, founder_name) if founder_ent else ''
    main_chapter_id  = get_main_chapter(founder_ent) if founder_ent else None

    # 其他出现章节
    other_chaps = []
    if founder_ent:
        other_chaps = [c['chapter'] for c in
                       sorted(founder_ent.get('chapters', []), key=lambda x: -x['count'])
                       if c['chapter'] != main_chapter_id][:4]

    # ── 传略 ────────────────────────────────────────────────────────────────
    bio = extract_biography(founder_name, main_chapter_id) if main_chapter_id else {}

    # ── 全文检索关键词（smart: 单字国名→复合形式）──────────────────────────
    founder_aliases = [a for a in (founder_ent.get('aliases', []) if founder_ent else [])]
    search_kws, _ = build_keywords(guo_name, founder_name, founder_aliases)

    all_hits   = search_chapters_lines(search_kws, include_tables=False, max_per_chapter=5)
    # 过滤误报：要求命中段落与侯国真正相关
    all_hits = {
        cid: [(pn, t) for pn, t in hits if is_relevant(t, guo_name, founder_name)]
        for cid, hits in all_hits.items()
    }
    all_hits = {cid: hits for cid, hits in all_hits.items() if hits}

    table_hits = search_in_tables(search_kws)

    # ── 封侯旁证 ─────────────────────────────────────────────────────────────
    secondary = {}
    for cid, hits in all_hits.items():
        enc = filter_enfeoffment(hits)
        if enc:
            secondary[cid] = enc[:3]

    # ── 三家注 ───────────────────────────────────────────────────────────────
    sanjia = collect_sanjia(
        founder_name, guo_name, main_chapter_id,
        list(all_hits.keys())[:5]
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 开始生成 Markdown
    # ─────────────────────────────────────────────────────────────────────────
    today = date.today().isoformat()
    L: list[str] = []

    # ── frontmatter ──────────────────────────────────────────────────────────
    L += [
        '---',
        f'id: "{page_id}"',
        f'type: 侯国',
        f'label: {page_id}',
        f'tags: [汉代, 侯国, {table_tag}]',
        f'source_table: "{table_id}_{table_title}"',
        f'auto_generated: true',
        f'generated_date: "{today}"',
        '---',
        '',
    ]

    # ── 标题 + 导言 ──────────────────────────────────────────────────────────
    L.append(f'# {page_id}')
    L.append('')
    founder_link = f'[[{founder_name}]]' if founder_name else '（待考）'
    if founding_date:
        L.append(
            f'{page_id}，汉代列侯封国。'
            f'{founding_date}，{founder_link}以功受封，食邑{households or "户数不详"}。'
        )
    else:
        L.append(
            f'{page_id}，汉代列侯封国。'
            f'初封侯{founder_link}，食邑{households or "户数不详"}。'
        )
    L.append('')

    # ══ 一、始封 ════════════════════════════════════════════════════════════

    L.append('## 始封')
    L.append('')
    if founder_name:
        L.append(f'**初封侯**：{founder_link}（{founder_title}）')
    if founding_date:
        L.append(f'**分封时间**：{founding_date}')
    if households:
        L.append(f'**初封食邑**：{households}')
    L.append('')
    L.append('**封侯原因**（年表原文）：')
    L.append('')
    L.append(f'> {hou_gong}')
    L.append('')

    # ══ 二、始封者传略 ══════════════════════════════════════════════════════

    if founder_ent or bio:
        L.append(f'## 始封者：{founder_name}')
        L.append('')
        if founder_brief:
            L.append(f'{founder_link}：{founder_brief}')
            L.append('')

        # 开篇介绍（来自主传）
        if bio.get('opening'):
            L.append(f'**人物简介**（来自 [[{main_chapter_id}]]）：')
            L.append('')
            for pn, text in bio['opening']:
                L.append(f'> `[{main_chapter_id[:3]}:{pn}]` {text}')
                L.append('')

        # 军功记录
        if bio.get('military') or bio.get('summary'):
            L.append('**军功记录**：')
            L.append('')
            for pn, text in (bio.get('summary', []) + bio.get('military', []))[:6]:
                L.append(f'> `[{main_chapter_id[:3]}:{pn}]` {text}')
                L.append('')

        # 封侯记载（主传中）
        if bio.get('enfeoffment'):
            L.append('**主传中的封侯记载**：')
            L.append('')
            for pn, text in bio['enfeoffment'][:3]:
                anno = annotate_bce(text)
                L.append(f'> `[{main_chapter_id[:3]}:{pn}]` {anno}')
                L.append('')

        # 出现章节
        if founder_ent:
            chaps = founder_ent.get('chapters', [])
            top = sorted(chaps, key=lambda x: -x['count'])[:8]
            L.append('**在史记各章的记载次数**：')
            L.append('')
            for c in top:
                cid2 = c['chapter']
                L.append(f'- [[{cid2}]]（{c["count"]} 处）')
            L.append('')

    # ══ 三、历代侯主 ════════════════════════════════════════════════════════

    if succession:
        L.append('## 历代侯主')
        L.append('')
        L.append('| 侯主 | 谥号 / 称号 | 就封时间 | 备注 |')
        L.append('|------|------------|---------|------|')
        for item in succession:
            nm  = item['marquis']
            ttl = item.get('title', '')
            ds  = item.get('date_str', '')
            evt = item.get('events', [])
            evt_str = '；'.join(evt[:2])
            nm_col  = f'[[{nm}]]' if lookup_person(nm, semantic) else nm
            L.append(f'| {nm_col} | {ttl} | {ds} | {evt_str} |')
        L.append('')

    if extinction:
        L.append(f'**国除**：{extinction}')
        L.append('')

    # ══ 四、封地地望 ════════════════════════════════════════════════════════

    L.append('## 封地地望')
    L.append('')
    L.append(f'封国名**{guo_name}**，其地望待考。')
    L.append('')
    # 从三家注正义中找地理注释
    geo_notes = [
        (chap, n) for chap, n in sanjia
        if any(
            i.get('source') in ('zhengyi', 'jijie') and
            any(gkw in i.get('text', '') for gkw in [guo_name, '县', '郡', '故城', '在今'])
            for i in n.get('items', [])
        )
    ]
    if geo_notes:
        L.append('**三家注地望说明**：')
        L.append('')
        for chap, n in geo_notes[:3]:
            L.append(f'**锚文**（{chap}）：{n["anchor_text"]}')
            for item in n.get('items', []):
                if any(gkw in item.get('text', '') for gkw in [guo_name, '县', '郡', '故城', '在今', '地']):
                    L.append(f'- **{item["label"]}**：{item["text"]}')
            L.append('')
    # 从普通章节检索找地名引用
    geo_lines = []
    for cid, hits in all_hits.items():
        for pn, text in hits:
            if guo_name in text and any(kw in text for kw in ['地', '郡', '县', '城', '在', '属']):
                geo_lines.append((cid, pn, text))
    if geo_lines:
        L.append('**史记正文中的地名引用**：')
        L.append('')
        for cid, pn, text in geo_lines[:4]:
            L.append(f'> `[{cid[:3]}:{pn}]`（[[{cid}]]）{text[:150]}')
            L.append('')

    # ══ 五、他章分封旁证 ═════════════════════════════════════════════════════

    if secondary:
        L.append('## 分封旁证')
        L.append('')
        L.append('以下引文来自年表以外的史记正文，提供分封的第二证据。')
        L.append('')
        for cid, hits in sorted(secondary.items()):
            L.append(f'### [[{cid}]]')
            L.append('')
            for pn, text in hits:
                anno = annotate_bce(text)
                L.append(f'> `[{cid[:3]}:{pn}]` {anno}')
                L.append('')

    # ══ 六、三家注 ══════════════════════════════════════════════════════════

    if sanjia:
        L.append('## 三家注')
        L.append('')
        # 地望注已在上面，这里放其他类型
        non_geo = [
            (ch, n) for ch, n in sanjia
            if (ch, n) not in geo_notes
        ]
        if non_geo:
            L.append('以下为裴骃《集解》、司马贞《索隐》、张守节《正义》的相关注释。')
            L.append('')
            prev_chap = None
            for chap, n in non_geo[:8]:
                if chap != prev_chap:
                    L.append(f'### [[{chap}]]')
                    L.append('')
                    prev_chap = chap
                anchor = n.get('anchor_text', '')
                L.append(f'**锚文**：「{anchor}」')
                for item in n.get('items', []):
                    if len(item.get('text', '')) > 3:
                        L.append(f'- **{item["label"]}**：{item["text"]}')
                L.append('')

    # ══ 七、史记十表相关内容 ═════════════════════════════════════════════════

    if table_hits:
        L.append('## 史记十表中的记载')
        L.append('')
        for cid, hits in sorted(table_hits.items()):
            L.append(f'### [[{cid}]]')
            L.append('')
            for pn, text in hits:
                anno = annotate_bce(text)
                L.append(f'> `[{cid[:3]}:{pn}]` {anno}')
                L.append('')

    # ══ 八、年表原文 ════════════════════════════════════════════════════════

    L.append('## 年表原文')
    L.append('')
    L.append(f'来源：[[{table_id}_{table_title}]]，侯第 {row.get("侯第", "").strip()}')
    L.append('')
    L.append('| 年号 | 记事 |')
    L.append('|------|------|')
    skip = {'国名', '侯功', '侯第', '_table_id', '_table_title'}
    for col, text in row.items():
        if col in skip or not text:
            continue
        L.append(f'| {col} | {annotate_bce(text.strip())} |')
    L.append('')

    # ══ 九、史记其他章节记载 ════════════════════════════════════════════════

    if all_hits:
        L.append('## 在史记其他章节的记载')
        L.append('')
        for cid, hits in sorted(all_hits.items()):
            L.append(f'### [[{cid}]]')
            L.append('')
            for pn, text in hits:
                snippet = excerpt_hit(text, search_kws)
                L.append(f'> `[{cid[:3]}:{pn}]` {snippet}')
                L.append('')

    L.append('')
    return '\n'.join(L)

# ─── 主程序 ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='生成汉代侯国 wiki 页面 v2')
    parser.add_argument('name',    nargs='?', help='侯国名（如 平阳）')
    parser.add_argument('--list',  action='store_true')
    parser.add_argument('--all',   action='store_true', help='批量生成全部')
    parser.add_argument('--table', choices=['018', '019', '020'])
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--force',   action='store_true')
    args = parser.parse_args()

    rows     = load_tables()
    semantic = load_semantic()

    if args.table:
        rows = [r for r in rows if r['_table_id'] == args.table]

    if args.list:
        for r in rows:
            print(f"[{r['_table_id']}] {r['国名'].strip('。 ')}")
        return

    if args.all:
        created, skipped = 0, 0
        for row in rows:
            guo = row['国名'].strip('。 ')
            if not guo:
                continue
            out_path = PAGES_DIR / f'{guo}侯国.md'
            if out_path.exists() and not args.force:
                skipped += 1
                continue
            try:
                content = build_page(row, semantic)
                slug = f'{guo}侯国'
                script = EDIT_PAGE if out_path.exists() else ADD_PAGE
                summary = f'butler/create-stub: {slug} 汉代侯国条目'
                tmp = out_path.with_suffix('.tmp.md')
                tmp.write_text(content, encoding='utf-8')
                r = subprocess.run(
                    [sys.executable, str(script), slug, str(tmp),
                     '--summary', summary, '--author', 'butler'],
                    capture_output=True, text=True
                )
                tmp.unlink(missing_ok=True)
                if r.returncode != 0:
                    raise RuntimeError(r.stderr.strip())
                created += 1
                print(f'✓ {guo}侯国.md', flush=True)
            except Exception as e:
                print(f'✗ {guo}侯国.md: {e}', file=sys.stderr)
        print(f'\n生成 {created} 页，跳过 {skipped} 页')
        return

    if not args.name:
        parser.print_help(); sys.exit(1)

    row = find_row(args.name, rows)
    if not row:
        print(f'未找到「{args.name}」', file=sys.stderr); sys.exit(1)

    content = build_page(row, semantic)
    if args.dry_run:
        print(content); return

    guo      = row['国名'].strip('。 ')
    out_path = PAGES_DIR / f'{guo}侯国.md'
    if out_path.exists() and not args.force:
        print(f'已存在：{out_path}（加 --force 覆盖）', file=sys.stderr); sys.exit(1)
    slug   = f'{guo}侯国'
    script = EDIT_PAGE if out_path.exists() else ADD_PAGE
    summary = f'butler/create-stub: {slug} 汉代侯国条目'
    tmp = out_path.with_suffix('.tmp.md')
    tmp.write_text(content, encoding='utf-8')
    r = subprocess.run(
        [sys.executable, str(script), slug, str(tmp),
         '--summary', summary, '--author', 'butler'],
        capture_output=True, text=True
    )
    tmp.unlink(missing_ok=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr); sys.exit(r.returncode)
    print(r.stdout, end='')


if __name__ == '__main__':
    main()
