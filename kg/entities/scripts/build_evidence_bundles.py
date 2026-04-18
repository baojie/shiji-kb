#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为每个 place 构建"证据包"，包含：
  1. context_windows: chapter_md 中每次出现的前后文段（60 字）
  2. cooccur_tags: 同句共现的其它实体 tag（官职/人名/制度 等）
  3. sanjia_mentions: 三家注中该名字出现的段落
  4. verb_ops: 作用于该地名的动词 tag（攻/封/禅/战/渡 等）

用作第三轮反思的原始证据材料。输出 JSON（方便后续再处理）。

  python3 build_evidence_bundles.py [--names 万里沙,沛谷,...]
                                    [--conf-max 0.9]

默认输出：kg/entities/data/place_evidence_bundles.json
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INDEX_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
CATS_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'place_categories.json'
CHAPTER_DIR = _ROOT / 'chapter_md'
SANJIA_FILE = _ROOT / 'corpus' / 'shiji' / '史记集解三家注索隐正义.txt'
OUT_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'place_evidence_bundles.json'

# Tag 结构正则
PLACE_RE = re.compile(r'〖=([^〖〗\n|]+)(?:\|[^〖〗\n]+)?〗')
ANY_TAG_RE = re.compile(r'[〖⟦]([@=;%&◆\^~#•!\?\+\$\{:\[_◈◉○◇])([^〖〗⟦⟧\n]+)[〗⟧]')

TAG_TYPE_LABELS = {
    '@': '人名', '=': '地名', ';': '官职', '%': '时间',
    '&': '氏族', '◆': '邦国', '^': '制度', '~': '族群',
    '#': '身份', '•': '器物', '!': '天文', '?': '神话',
    '+': '生物', '$': '数量', '{': '典籍', ':': '礼仪',
    '[': '刑法', '_': '思想',
    '◈': '军事动词', '◉': '刑罚动词', '○': '政治动词', '◇': '经济动词',
}

CONTEXT_BEFORE = 30
CONTEXT_AFTER = 30


def strip_tags(text):
    """去所有 〖X内容〗 / ⟦X内容⟧ 外壳 + 剥去 '|消歧' 部分"""
    text = re.sub(r'〖[@=;%&◆\^~#•!\?\+\$\{:\[_]([^〖〗]+)〗', r'\1', text)
    text = re.sub(r'⟦[◈◉○◇]([^⟦⟧]+)⟧', r'\1', text)
    text = re.sub(r'([^|\s]+)\|[^〖〗\n|]+', r'\1', text)
    return text


def iter_chapters():
    for chap in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        yield chap.stem.replace('.tagged', ''), chap.read_text(encoding='utf-8')


def build_bundle(names):
    """为给定 names 集合构建证据包"""
    bundles = {n: {
        'context_windows': [],
        'cooccur_tags': Counter(),
        'verb_ops': Counter(),
        'sanjia_mentions': [],
    } for n in names}
    name_set = set(names)

    for chap_id, content in iter_chapters():
        # 段落分隔：用双换行
        for m in PLACE_RE.finditer(content):
            name = m.group(1)
            if name not in name_set:
                continue
            pos = m.start()
            # 取前后窗口
            start = max(0, pos - CONTEXT_BEFORE * 3)  # 多取，后面 strip_tags 会缩短
            end = min(len(content), m.end() + CONTEXT_AFTER * 3)
            raw = content[start:end]
            stripped = strip_tags(raw)
            # 重新定位 name 在 stripped 中的位置
            idx = stripped.find(name)
            if idx >= 0:
                s = max(0, idx - CONTEXT_BEFORE)
                e = min(len(stripped), idx + len(name) + CONTEXT_AFTER)
                window = stripped[s:idx] + '【' + name + '】' + stripped[idx+len(name):e]
                window = re.sub(r'\s+', ' ', window).strip()
            else:
                window = stripped[:120]
            bundles[name]['context_windows'].append(f'{chap_id}: {window}')

            # 同句共现的其它 tag（先找同句范围：以中文句号/叹号/问号/换行/分号为边界）
            sent_start = start
            sent_end = end
            # 向前找句首
            for bound in ('。', '！', '？', '\n', ';', '，', '：'):
                p = content.rfind(bound, start, pos)
                if p > sent_start:
                    sent_start = p + 1
            # 向后找句尾
            for bound in ('。', '！', '？', '\n', ';', '，', '：'):
                p = content.find(bound, m.end(), end)
                if p != -1 and p < sent_end:
                    sent_end = p
            sentence = content[sent_start:sent_end]
            # 提取所有 tag
            for tm in ANY_TAG_RE.finditer(sentence):
                ttype = tm.group(1)
                tcontent = tm.group(2)
                # 跳过本 place
                if ttype == '=' and tcontent == name:
                    continue
                type_label = TAG_TYPE_LABELS.get(ttype, '?')
                key = f'{type_label}:{tcontent}'
                if ttype in '◈◉○◇':   # 动词
                    bundles[name]['verb_ops'][key] += 1
                else:
                    bundles[name]['cooccur_tags'][key] += 1

    # 三家注
    if SANJIA_FILE.exists():
        sj_text = SANJIA_FILE.read_text(encoding='utf-8')
        # 按段落分（以换行）
        for para in sj_text.split('\n'):
            para = para.strip()
            if not para:
                continue
            for name in name_set:
                if name in para:
                    # 截取 name 前后 40 字
                    idx = para.find(name)
                    s = max(0, idx - 40)
                    e = min(len(para), idx + len(name) + 40)
                    snippet = para[s:idx] + '【' + name + '】' + para[idx+len(name):e]
                    bundles[name]['sanjia_mentions'].append(snippet)
                    if len(bundles[name]['sanjia_mentions']) >= 3:
                        break   # 每条最多 3 处

    # 转换 Counter 为 dict（保留 top N）
    for name, b in bundles.items():
        b['cooccur_tags'] = dict(b['cooccur_tags'].most_common(10))
        b['verb_ops']     = dict(b['verb_ops'].most_common(10))
        # context 最多 6 条
        b['context_windows'] = b['context_windows'][:6]
    return bundles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--names', help='指定 names，逗号分隔；默认为全部 conf<0.9 条目')
    ap.add_argument('--conf-max', type=float, default=0.9)
    args = ap.parse_args()

    if args.names:
        target = set(args.names.split(','))
    else:
        # 载入 confidence_report 结果
        # 简化：直接加载分类 + 重算置信度
        sys.path.insert(0, str(_ROOT / 'kg' / 'entities' / 'scripts'))
        import classify_places as cp
        import confidence_report as cr
        idx = json.loads(INDEX_JSON.read_text(encoding='utf-8'))
        places = idx['place']
        cats = json.loads(CATS_JSON.read_text(encoding='utf-8'))
        hints = cp.build_context_hints(places.keys())
        for nm, cs in cp.build_sanjia_hints(places.keys()).items():
            for c, n in cs.items():
                hints[nm][c] += n
        peer_groups = cp.build_peer_groups(places.keys())
        peer_map = defaultdict(set)
        for g in peer_groups:
            for n in g:
                peer_map[n].update(x for x in g if x != n)
        all_places = set(places.keys())
        target = set()
        for name, clist in cats.items():
            refs = places[name]['refs']
            for cat in clist:
                ev = cr.score_evidence(name, cat, refs, hints,
                                       cp_mod=cp, all_places=all_places,
                                       peer_map_cache=peer_map)
                conf = max((e[1] for e in ev), default=0.30)
                if conf < args.conf_max:
                    target.add(name)
                    break
    print(f'目标 place 数: {len(target)}')
    bundles = build_bundle(target)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(bundles, ensure_ascii=False, indent=2),
                         encoding='utf-8')
    print(f'写入: {OUT_JSON}  ({OUT_JSON.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
