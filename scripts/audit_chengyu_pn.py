#!/usr/bin/env python3
"""
审计 chengyu.json + chengyu_summarized.json 中每条的 paragraph（PN）映射是否正确。

检查方法：
1. 加载对应章节原文
2. 在纯文本中定位该成语（tagged: 用 shiji_form 或 chengyu；summarized: 用 anchor）
3. 向上扫描到最近的 [N.M.K] PN
4. 与 JSON 中记录的 paragraph 比对

输出:
  logs/chengyu_pn_audit.txt
"""

import re
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHAPTER_DIR = ROOT / 'chapter_md'
LOG = ROOT / 'logs/chengyu_pn_audit.txt'

PN_PATTERN = re.compile(r'^\s*\[(\d+(?:\.\d+)*)\]')


def strip_all_markup(text):
    t = text
    t = re.sub(r'〘※([^〘〙|]+)(?:\|[^〘〙]*)?〙', r'\1', t)
    t = re.sub(r'〖.([^〖〗|]+)(?:\|[^〖〗]*)?〗', r'\1', t)
    t = re.sub(r'⟦.([^⟦⟧|]+)(?:\|[^⟦⟧]*)?⟧', r'\1', t)
    return t


def find_pn_at(pure, idx):
    chunk = pure[max(0, idx - 2000):idx]
    for line in reversed(chunk.split('\n')):
        m = PN_PATTERN.match(line.strip())
        if m:
            return m.group(1)
    return None


def locate(pure, phrase):
    idx = pure.find(phrase)
    if idx >= 0:
        return idx
    segments = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]{3,}', phrase)
    for seg in sorted(set(segments), key=len, reverse=True):
        i = pure.find(seg)
        if i >= 0:
            return i
    head = phrase[:3] if len(phrase) >= 3 else phrase
    return pure.find(head)


def main():
    pure_cache = {}

    def get_pure(chap):
        if chap not in pure_cache:
            files = list(CHAPTER_DIR.glob(f'{chap}_*.tagged.md'))
            if not files:
                pure_cache[chap] = ''
            else:
                pure_cache[chap] = strip_all_markup(files[0].read_text(encoding='utf-8'))
        return pure_cache[chap]

    report = []
    errors = []

    raw_cache = {}

    def get_raw(chap):
        if chap not in raw_cache:
            files = list(CHAPTER_DIR.glob(f'{chap}_*.tagged.md'))
            if not files:
                raw_cache[chap] = ''
            else:
                raw_cache[chap] = files[0].read_text(encoding='utf-8')
        return raw_cache[chap]

    def find_pn_in_raw(raw, raw_idx):
        """在原始 tagged 内容中向上扫最近的 PN"""
        chunk = raw[max(0, raw_idx - 2000):raw_idx]
        for line in reversed(chunk.split('\n')):
            m = PN_PATTERN.match(line.strip())
            if m:
                return m.group(1)
        return None

    # 审计 chengyu.json (tagged): 在 raw 中查找实际 〘※〙 marker 位置
    tagged = json.load(open(ROOT / 'data/chengyu.json'))
    for item in tagged:
        chap = item['chapter_num']
        raw = get_raw(chap)
        shiji = item.get('shiji_form') or item['chengyu']
        # 查找 〘※shiji〙 或 〘※shiji|...〙 的确切位置
        marker_exact = f'〘※{shiji}〙'
        marker_with_disamb = f'〘※{shiji}|'
        idx = raw.find(marker_exact)
        if idx < 0:
            idx = raw.find(marker_with_disamb)
        if idx < 0:
            errors.append(f"[tagged {chap}] {item['chengyu']}: 未找到 marker (shiji={shiji!r})")
            continue
        real_pn = find_pn_in_raw(raw, idx)
        stored = item.get('paragraph') or ''
        if stored != (real_pn or ''):
            errors.append(f"[tagged {chap}] {item['chengyu']}: stored={stored!r} vs real={real_pn!r}")

    # 审计 chengyu_summarized.json
    summ = json.load(open(ROOT / 'data/chengyu_summarized.json'))['entries']
    for item in summ:
        chap = item['chapter_num']
        pure = get_pure(chap)
        phrase = item.get('anchor') or ''
        if not phrase:
            continue  # narrative 无 anchor 跳过
        idx = locate(pure, phrase)
        if idx < 0:
            errors.append(f"[summarized {chap}] {item['chengyu']}: 定位失败 anchor={phrase!r}")
            continue
        real_pn = find_pn_at(pure, idx)
        stored = item.get('paragraph') or ''
        if stored != (real_pn or ''):
            errors.append(f"[summarized {chap}] {item['chengyu']}: stored={stored!r} vs real={real_pn!r}  "
                          f"(anchor={phrase!r})")

    report.append(f"tagged 条目: {len(tagged)}")
    report.append(f"summarized 条目: {len(summ)}")
    report.append(f"PN 不匹配: {len(errors)}\n")
    report.extend(errors)

    LOG.write_text('\n'.join(report), encoding='utf-8')
    print(f'tagged: {len(tagged)}  summarized: {len(summ)}')
    print(f'PN 不匹配: {len(errors)}')
    print(f'详情: {LOG}')


if __name__ == '__main__':
    main()
