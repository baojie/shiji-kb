#!/usr/bin/env python3
"""
从分类数据生成人物本体的分类树(taxonomy.md)和RDF(person.ttl)

输入：/tmp/person_classified_final10.pkl（pickle格式的分类数据）
输出：
  - kg/rdf/person_taxonomy.md — 可读的层级分类树
  - kg/rdf/person.ttl — OWL/RDF本体

用法：
  python kg/rdf/scripts/build_person_taxonomy.py

注意：分类数据由多轮反思迭代产生（见SKILL_实体到本体管线.md），
本脚本只负责从分类结果生成输出文件。
"""

import pickle
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT_TAXONOMY = PROJECT_ROOT / 'kg' / 'rdf' / 'person_taxonomy.md'
OUTPUT_TTL = PROJECT_ROOT / 'kg' / 'rdf' / 'person.ttl'
INPUT_PKL = Path('/tmp/person_classified_final10.pkl')

# ── Sub-class label mapping ──

SUB_ZH = {
    # 帝王
    'Zhou':'周','Han':'汉','Ancient':'上古','Xia':'夏','Shang':'商','QinDynasty':'秦朝','LateQin':'秦末',
    # 诸侯
    'Qin':'秦国','Chu':'楚国','Qi':'齐国','Jin':'晋国','Zhao':'赵国','Wei':'魏国',
    'Yan':'燕国','Wu':'吴国','Yue':'越国','Song':'宋国','Wey':'卫国',
    'Zheng':'郑国','Lu':'鲁国','Chen':'陈国','Cai':'蔡国','Cao':'曹国',
    # 疑似误标
    'SingleChar':'单字名','AmbiguousTitle':'无国名谥号',
    # 外邦
    'Xiongnu':'匈奴','Nanyue':'南越','Dongyue':'东越','Chaoxian':'朝鲜','Southwest':'西南夷','XiYu':'大宛西域',
    # 儒生
    'Kongmen':'孔门弟子','HanRu':'汉儒',
    # 方术
    'Yizhe':'医者','Fangshi':'方士','Rizhe':'日者龟策',
    # 汉宗室
    'WuChu':'吴楚七国','HuainanHengshan':'淮南衡山',
    # 后妃
    'PreQinConsort':'先秦后妃','HanConsort':'汉后妃',
    # 臣 level-1
    'EarlyPreQin':'先秦早期','SpringAutumn':'春秋','WarringStates':'战国',
    'QinAll':'秦臣子','ChuHan':'楚汉','EarlyHan':'汉初','LateHan':'汉中后',
    # 臣 level-2 (时代×国)
    'EarlyPreQin_WuDi':'五帝时代','EarlyPreQin_Xia':'夏代','EarlyPreQin_Shang':'商代',
    'EarlyPreQin_WestZhou':'西周','EarlyPreQin_SanDai':'三代',
    'SpringAutumn_Qi':'齐国臣子','SpringAutumn_Lu':'鲁国臣子','SpringAutumn_Zheng':'郑国臣子',
    'SpringAutumn_Wu':'吴国臣子','SpringAutumn_Cai':'管蔡臣子','SpringAutumn_Wey':'卫国臣子',
    'SpringAutumn_Song':'宋国臣子','SpringAutumn_Chen':'陈国臣子','SpringAutumn_Yan':'燕国臣子',
    'SpringAutumn_WuChu':'吴楚臣子','SpringAutumn_Qin':'秦国臣子','SpringAutumn_Kongmen':'孔门弟子',
    'WarringStates_Jin':'晋国臣子','WarringStates_Chu':'楚国臣子','WarringStates_Zhao':'赵国臣子',
    'WarringStates_Wei':'魏国臣子','WarringStates_QiTian':'齐国田氏臣子','WarringStates_Han_s':'韩国臣子',
    'WarringStates_Qin':'秦国臣子','WarringStates_Qi':'齐国臣子','WarringStates_Yan':'燕国臣子',
    'EarlyHan_LiuBang':'刘邦阵营','EarlyHan_Generals':'汉初诸将','EarlyHan_LvShi':'吕氏集团',
    'ChuHan_Xiang':'项羽阵营','ChuHan_Liu':'刘邦阵营',
    'LateHan_WenJing':'文景朝臣','LateHan_WenJingWu':'文景武朝臣',
    'LateHan_Wu':'武帝朝臣','LateHan_Various':'汉其他','LateHan_Wen':'文帝朝臣','LateHan_Jing':'景帝朝臣',
    # 臣 level-3 (性质)
    'EarlyPreQin_WestZhou_周族先祖':'周族先祖','EarlyPreQin_WestZhou_西周朝臣':'西周朝臣',
    'EarlyPreQin_Shang_商代名臣':'商代名臣',
    'SpringAutumn_Qi_齐国贤臣':'齐国贤臣','SpringAutumn_Qi_齐国权臣':'齐国权臣',
    'WarringStates_Jin_SixFamilies':'晋国六卿','WarringStates_Jin_晋国世族':'晋国世族','WarringStates_Jin_宗室':'晋国宗室','WarringStates_Jin_将领':'晋国将领','WarringStates_Jin_卿大夫':'晋国卿大夫','WarringStates_Jin_谋臣':'晋国谋臣',
    'WarringStates_Zhao_赵国将领':'赵国将领','WarringStates_Zhao_赵国政治':'赵国政治',
    'WarringStates_Chu_楚国权贵':'楚国权贵','WarringStates_Chu_楚国臣子':'楚国臣子',
    'Qin_Ancestor':'秦国先祖','Qin_General':'秦国将领','Qin_Minister':'秦国相臣',
    'WarringStates_Qin_General':'秦国将领','WarringStates_Qin_Minister':'秦国相臣','WarringStates_Qin_Ancestor':'秦国先祖',
    'QinAll_秦朝权臣':'秦朝权臣','QinAll_秦朝将领':'秦朝将领','QinAll_秦朝重臣':'秦朝重臣','QinAll_秦末起义':'秦末起义','QinAll_End':'秦末起义',
    'EarlyHan_LiuBang_General':'刘邦武将','EarlyHan_LiuBang_Minister':'刘邦文臣',
    'LateHan_Wu_武帝将领':'武帝将领','LateHan_Wu_武帝文臣':'武帝文臣',
}

# Class grouping
WANGSHI = {'帝王','诸侯','后妃','汉宗室'}
ZHUZI = {'儒生','法家','兵家','思想家','文学家','隐士','史家'}
SHEHUI = {'刺客','游侠','佞幸','滑稽','商贾'}

TREE_ORDER = ['帝王','诸侯','后妃','汉宗室','臣','策士',
              '儒生','法家','兵家','思想家','文学家','隐士','史家',
              '刺客','游侠','佞幸','滑稽','商贾',
              '方术','外邦','虚构人物','疑似误标']

CLS_SUFFIX = {'帝王':'帝王','诸侯':'诸侯','臣':'臣','外邦':'外邦',
              '儒生':'儒生','方术':'方术','汉宗室':'汉宗室','后妃':''}

MAX_SHOW = 20


def get_label(sub):
    if sub == 'Han': return '韩国'  # avoid Han/汉 ambiguity under 诸侯
    return SUB_ZH.get(sub, sub)


def get_sub_uri(cls, sub):
    zh = get_label(sub)
    suffix = CLS_SUFFIX.get(cls, '')
    if cls == '疑似误标': return f'per:{zh}'
    return f'per:{zh}{suffix}'


def build_sub_tree(flat_items):
    """Build hierarchical tree from flat sub-class codes."""
    all_subs = sorted(flat_items.keys())
    parent_of = {}
    for sub in all_subs:
        parts = sub.split('_')
        for i in range(len(parts)-1, 0, -1):
            candidate = '_'.join(parts[:i])
            if candidate in all_subs:
                parent_of[sub] = candidate
                break

    children_of = defaultdict(list)
    roots = []
    for sub in all_subs:
        if sub in parent_of:
            children_of[parent_of[sub]].append(sub)
        else:
            roots.append(sub)

    return roots, children_of


def gen_tree_lines(node, flat_items, children_of, prefix, is_last, lines):
    """Recursively generate tree lines."""
    items = flat_items.get(node, [])
    kids = children_of.get(node, [])

    # Collect all descendant names
    child_names = set()
    def collect(n):
        for k in children_of.get(n, []):
            for nm, _ in flat_items.get(k, []): child_names.add(nm)
            collect(k)
    collect(node)

    direct = [(n, c) for n, c in items if n not in child_names]
    total = len(items)

    conn = '└── ' if is_last else '├── '
    lines.append(f'{prefix}{conn}{get_label(node)}  [{total}人]')
    cp = prefix + ('    ' if is_last else '│   ')

    sorted_kids = sorted(kids, key=lambda k: -len(flat_items.get(k, [])))
    for ki, kid in enumerate(sorted_kids):
        kl = (ki == len(sorted_kids) - 1) and not direct
        gen_tree_lines(kid, flat_items, children_of, cp, kl, lines)

    if direct:
        show = min(len(direct), MAX_SHOW)
        if kids:
            lines.append(f'{cp}└── (本级)  [{len(direct)}人]')
            ip = cp + '    '
        else:
            ip = cp
        for i, (name, count) in enumerate(direct[:show]):
            il = (i == show - 1) and len(direct) <= show
            lines.append(f'{ip}{"└── " if il else "├── "}{name} ({count})')
        if len(direct) > show:
            lines.append(f'{ip}└── ……其余{len(direct)-show}人')


def main():
    with open(INPUT_PKL, 'rb') as f:
        classified = pickle.load(f)

    # Build class items and sub-class structure
    class_items = defaultdict(list)
    chen_flat = defaultdict(list)
    other_subs = defaultdict(lambda: defaultdict(list))

    for name, (classes, count, sub) in classified.items():
        for c in classes:
            class_items[c].append((name, count))
            if c == '臣' and sub:
                chen_flat[sub].append((name, count))
            elif sub:
                other_subs[c][sub].append((name, count))

    for c in class_items: class_items[c].sort(key=lambda x: -x[1])
    for sub in chen_flat: chen_flat[sub].sort(key=lambda x: -x[1])
    for c in other_subs:
        for s in other_subs[c]: other_subs[c][s].sort(key=lambda x: -x[1])

    roots, children_of = build_sub_tree(chen_flat)

    # ── Generate taxonomy.md ──
    lines = ['# 史记人物分类树', '', f'> {len(classified)} 位人物，全部归类', '',
             '## 类层次结构', '', '```', '人物',
             '├── 王室（帝王/诸侯/后妃/汉宗室）',
             '├── 臣（时代×国×性质 三级嵌套）',
             '├── 策士',
             '├── 诸子百家（儒生/法家/兵家/思想家/文学家/隐士/史家）',
             '├── 社会人物（刺客/游侠/佞幸/滑稽/商贾）',
             '├── 方术 / 外邦 / 虚构人物',
             '└── 疑似误标', '```', '', '## 详细分类树', '', '```',
             f'人物  [{len(classified)}人]']

    active = [c for c in TREE_ORDER if class_items.get(c)]
    for idx, cn in enumerate(active):
        items = class_items[cn]
        is_last = (idx == len(active) - 1)

        # Insert group headers
        if cn == '帝王': lines.append('├── 王室')
        if cn == '儒生':
            t = sum(len(class_items[c]) for c in ZHUZI if class_items.get(c))
            lines.append(f'├── 诸子百家  [{t}人]')
        if cn == '刺客':
            t = sum(len(class_items[c]) for c in SHEHUI if class_items.get(c))
            lines.append(f'├── 社会人物  [{t}人]')

        # Determine prefix
        if cn in WANGSHI:
            p = '│   '; co = '│   └── ' if cn == '汉宗室' else '│   ├── '
        elif cn in ZHUZI:
            p = '│   '; co = '│   └── ' if cn == '史家' else '│   ├── '
        elif cn in SHEHUI:
            p = '│   '; co = '│   └── ' if cn == '商贾' else '│   ├── '
        else:
            p = ''; co = '└── ' if is_last else '├── '

        lines.append(f'{p}{co}{cn}  [{len(items)}人]')
        pf = p + ('    ' if '└' in co else '│   ')

        if cn == '臣':
            # Hierarchical tree for 臣
            sorted_roots = sorted(roots, key=lambda r: -len(chen_flat.get(r, [])))
            for ri, root in enumerate(sorted_roots):
                rl = (ri == len(sorted_roots) - 1)
                gen_tree_lines(root, chen_flat, children_of, pf, rl, lines)
        else:
            # Flat sub-classes for other types
            subs = other_subs.get(cn, {})
            bs = {s: it for s, it in subs.items() if len(it) >= 3}
            if bs and len(items) > 15:
                ss = sorted(bs.items(), key=lambda x: -len(x[1]))
                sn = set()
                for _, it in ss:
                    for n, _ in it: sn.add(n)
                us = [(n, c) for n, c in items if n not in sn]
                for si, (sid, si_items) in enumerate(ss):
                    sl = (si == len(ss)-1) and not us
                    lines.append(f'{pf}{"└── " if sl else "├── "}{get_label(sid)}  [{len(si_items)}人]')
                    sp = pf + ('    ' if sl else '│   ')
                    sh = min(len(si_items), MAX_SHOW)
                    for i, (n, c) in enumerate(si_items[:sh]):
                        lines.append(f'{sp}{"└── " if (i==sh-1 and len(si_items)<=sh) else "├── "}{n} ({c})')
                    if len(si_items) > sh:
                        lines.append(f'{sp}└── ……其余{len(si_items)-sh}人')
                if us:
                    lines.append(f'{pf}└── (未细分)  [{len(us)}人]')
                    up = pf + '    '
                    sh = min(len(us), MAX_SHOW)
                    for i, (n, c) in enumerate(us[:sh]):
                        lines.append(f'{up}{"└── " if (i==sh-1 and len(us)<=sh) else "├── "}{n} ({c})')
                    if len(us) > sh:
                        lines.append(f'{up}└── ……其余{len(us)-sh}人')
            else:
                ip = pf + '│   ' if len(items) > 1 else pf
                sh = min(len(items), 20)
                for i, (n, c) in enumerate(items[:sh]):
                    il = (i == sh - 1) and len(items) <= sh
                    lines.append(f'{ip}{"└── " if il else "├── "}{n} ({c})')
                if len(items) > sh:
                    lines.append(f'{ip}└── ……其余{len(items)-sh}人')

    lines.append('```')
    OUTPUT_TAXONOMY.write_text('\n'.join(lines), encoding='utf-8')
    print(f'taxonomy.md: {len(lines)} lines')

    # ── Generate person.ttl ──
    ttl = [
        '@prefix : <http://memect.cn/baojie/ontologies/2025/1/shiji/> .',
        '@prefix per: <http://memect.cn/baojie/ontologies/2025/1/shiji/person/> .',
        '@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .',
        '@prefix owl: <http://www.w3.org/2002/07/owl#> .',
        '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .',
        '', f'# 史记人物本体 — {len(classified)}人', '',
        'per:人物 a owl:Class ; rdfs:label "人物"@zh .', '',
        'per:王室 a owl:Class ; rdfs:subClassOf per:人物 ; rdfs:label "王室"@zh .', '',
        'per:诸子百家 a owl:Class ; rdfs:subClassOf per:人物 ; rdfs:label "诸子百家"@zh .', '',
        'per:社会人物 a owl:Class ; rdfs:subClassOf per:人物 ; rdfs:label "社会人物"@zh .', '',
    ]

    for cn in TREE_ORDER:
        if not class_items.get(cn): continue
        par = '王室' if cn in WANGSHI else ('诸子百家' if cn in ZHUZI else ('社会人物' if cn in SHEHUI else '人物'))
        ttl.append(f'per:{cn} a owl:Class ; rdfs:subClassOf per:{par} ; rdfs:label "{cn}"@zh .')
        ttl.append('')

    # Sub-classes with hierarchy
    ttl.append('# -- 子类 --\n')

    # 臣 sub-classes (hierarchical)
    parent_of_map = {}
    for sub in sorted(chen_flat.keys()):
        parts = sub.split('_')
        for i in range(len(parts)-1, 0, -1):
            candidate = '_'.join(parts[:i])
            if candidate in chen_flat:
                parent_of_map[sub] = candidate
                break

    sw = set()
    for sub in sorted(chen_flat.keys()):
        uri = get_sub_uri('臣', sub)
        if uri in sw: continue
        sw.add(uri)
        parent_sub = parent_of_map.get(sub)
        if parent_sub:
            parent_uri = get_sub_uri('臣', parent_sub)
        else:
            parent_uri = 'per:臣'
        zh = get_label(sub)
        sf = CLS_SUFFIX.get('臣', '')
        ttl.append(f'{uri} a owl:Class ; rdfs:subClassOf {parent_uri} ; rdfs:label "{zh}{sf}"@zh .')
    ttl.append('')

    # Other sub-classes (flat)
    for cn in TREE_ORDER:
        if cn == '臣': continue
        for sub in sorted(other_subs.get(cn, {})):
            uri = get_sub_uri(cn, sub)
            if uri in sw: continue
            sw.add(uri)
            zh = get_label(sub)
            sf = CLS_SUFFIX.get(cn, '')
            ttl.append(f'{uri} a owl:Class ; rdfs:subClassOf per:{cn} ; rdfs:label "{zh}{sf}"@zh .')
    ttl.append('')

    # Instances
    ibc = defaultdict(list)
    for name, (classes, count, sub) in sorted(classified.items(), key=lambda x: -x[1][1]):
        ibc[classes[0]].append((name, classes, count, sub))

    used = set()
    for cn in TREE_ORDER:
        insts = ibc.get(cn, [])
        if not insts: continue
        ttl.append(f'\n# {cn} ({len(insts)})')
        for name, classes, count, sub in insts:
            safe = name
            if safe in used: safe += '_2'
            used.add(safe)
            tp = [get_sub_uri(c, sub) if sub else f'per:{c}' for c in classes]
            ttl.append(f'per:{safe} a {" , ".join(tp)} ; rdfs:label "{name}"@zh ; :count {count} .')

    ttl.append('\n:count a owl:DatatypeProperty ; rdfs:label "出现次数"@zh ; rdfs:range xsd:integer .')

    OUTPUT_TTL.write_text('\n'.join(ttl), encoding='utf-8')

    # Validate
    from rdflib import Graph, URIRef
    from rdflib.namespace import RDF, OWL
    g = Graph()
    g.parse(str(OUTPUT_TTL), format='turtle')
    COUNT = URIRef('http://memect.cn/baojie/ontologies/2025/1/shiji/count')
    unique = len(set(g.subjects(COUNT, None)))
    nc = len(list(g.subjects(RDF.type, OWL.Class)))
    print(f'person.ttl: {len(g)} triples, {nc} classes, {unique} instances — VALID')


if __name__ == '__main__':
    main()
