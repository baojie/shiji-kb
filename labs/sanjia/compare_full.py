"""全 130 章三家注完整比对：wikisource_sanjia 源 HTML vs data/notes/*.json。

统计口径：只计算"非空内容"的条目（与 v4 抽取一致：label 后没有实际文字的空标签不计）。
输出：
  1) 每章三类条目数（wiki / ours / diff）
  2) 总计合计
  3) 不一致章节详情
"""
import json, re
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path('/home/baojie/work/knowledge/shiji-kb')
WIKI_DIR = ROOT / 'corpus' / 'shiji' / 'wikisource_sanjia'
NOTES_DIR = ROOT / 'data' / 'notes'

LABEL_SRC = {'集解':'jijie', '索隱':'suoyin', '正義':'zhengyi'}

ALL_LABELS = re.compile(
    r'<span[^>]*background-color:\s*(?P<bg>green|deepPink|#966)[^>]*>(?P<label>集解|索隱|正義)</span>(?P<rest>.*?)(?=<span[^>]*background-color:|</small>)',
    re.DOTALL | re.IGNORECASE
)


def count_wiki(html):
    soup = BeautifulSoup(html, 'html.parser')
    smalls = soup.find_all('small', style=lambda v: v and 'color:var(--color-destructive--visited' in v)
    counts = {'jijie':0,'suoyin':0,'zhengyi':0}
    for st in smalls:
        for m in ALL_LABELS.finditer(str(st)):
            text = BeautifulSoup(m.group('rest'), 'html.parser').get_text().strip()
            if text:
                counts[LABEL_SRC[m.group('label')]] += 1
    return counts


def count_ours(notes_json):
    counts = {'jijie':0,'suoyin':0,'zhengyi':0}
    for n in notes_json.get('notes', []):
        for it in n.get('items', []):
            if it.get('source') in counts:
                counts[it['source']] += 1
    return counts


def main():
    wiki_files = {}
    for f in WIKI_DIR.glob('*.html'):
        num = f.stem.split('_')[0]
        if num.isdigit():
            wiki_files[num] = f

    nums = sorted(wiki_files.keys())
    print(f'{"章":<4}{"名称":<28}{"wiki 集":>6}{"我 集":>6}{"diff":>5}  {"wiki 索":>6}{"我 索":>6}{"diff":>5}  {"wiki 正":>6}{"我 正":>6}{"diff":>5}')
    print('-' * 100)

    tot_w = {'jijie':0,'suoyin':0,'zhengyi':0}
    tot_o = {'jijie':0,'suoyin':0,'zhengyi':0}
    mism = []
    for num in nums:
        wiki_f = wiki_files[num]
        notes_f = NOTES_DIR / f'{num}-notes.json'
        if not notes_f.exists():
            print(f'{num}: notes 文件缺失')
            continue
        wiki = count_wiki(wiki_f.read_text())
        with open(notes_f) as f:
            ours = count_ours(json.load(f))
        dj = wiki['jijie'] - ours['jijie']
        ds = wiki['suoyin'] - ours['suoyin']
        dz = wiki['zhengyi'] - ours['zhengyi']
        mark = '  ⚠' if (dj or ds or dz) else ''
        name = wiki_f.stem.split('_', 1)[1]
        print(f'{num:<4}{name:<28}{wiki["jijie"]:>6}{ours["jijie"]:>6}{dj:>+5}  {wiki["suoyin"]:>6}{ours["suoyin"]:>6}{ds:>+5}  {wiki["zhengyi"]:>6}{ours["zhengyi"]:>6}{dz:>+5}{mark}')
        for k in tot_w: tot_w[k] += wiki[k]
        for k in tot_o: tot_o[k] += ours[k]
        if dj or ds or dz:
            mism.append((num, wiki, ours))

    print('-' * 100)
    print(f'{"合计":<32}{tot_w["jijie"]:>6}{tot_o["jijie"]:>6}{tot_w["jijie"]-tot_o["jijie"]:>+5}  {tot_w["suoyin"]:>6}{tot_o["suoyin"]:>6}{tot_w["suoyin"]-tot_o["suoyin"]:>+5}  {tot_w["zhengyi"]:>6}{tot_o["zhengyi"]:>6}{tot_w["zhengyi"]-tot_o["zhengyi"]:>+5}')
    grand_wiki = sum(tot_w.values())
    grand_ours = sum(tot_o.values())
    print(f'\n合计笺注条目: wiki {grand_wiki}  /  ours {grand_ours}  /  diff {grand_wiki - grand_ours:+d}')
    print(f'不一致章节: {len(mism)}')
    if mism:
        for num, w, o in mism:
            print(f'  {num}: wiki={w} ours={o}')

if __name__ == '__main__':
    main()
