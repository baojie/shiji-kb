"""三源对比：wikisource_sanjia HTML（我们的源） vs 史记集解三家注索隐正义.txt（另一底本） vs 我们的 notes JSON。

抽 10 章随机样本，列出三者对齐程度。
"""
import json, re, random
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path('/home/baojie/work/knowledge/shiji-kb')
WIKI_DIR = ROOT / 'corpus' / 'shiji' / 'wikisource_sanjia'
TXT = ROOT / 'corpus' / 'shiji' / '史记集解三家注索隐正义.txt'
NOTES_DIR = ROOT / 'data' / 'notes'

ALL_LABELS = re.compile(
    r'<span[^>]*background-color:\s*(?P<bg>green|deepPink|#966)[^>]*>(?P<label>集解|索隱|正義)</span>(?P<rest>.*?)(?=<span[^>]*background-color:|</small>)',
    re.DOTALL | re.IGNORECASE
)
LABEL_SRC = {'集解':'jijie', '索隱':'suoyin', '正義':'zhengyi'}

# ---- wiki HTML ----
def count_wiki(html):
    soup = BeautifulSoup(html, 'html.parser')
    smalls = soup.find_all('small', style=lambda v: v and 'color:var(--color-destructive--visited' in v)
    c = {'jijie':0,'suoyin':0,'zhengyi':0}
    for st in smalls:
        for m in ALL_LABELS.finditer(str(st)):
            text = BeautifulSoup(m.group('rest'), 'html.parser').get_text().strip()
            if text:
                c[LABEL_SRC[m.group('label')]] += 1
    return c

# ---- dianjiao TXT chapter split ----
CNUM = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,'百':100}
def cnum(s):
    if not s: return 0
    if len(s) == 1: return CNUM.get(s, 0)
    if '百' in s:
        parts = s.split('百', 1)
        h = CNUM.get(parts[0], 1) if parts[0] else 1
        return h * 100 + (cnum(parts[1]) if parts[1] else 0)
    if '十' in s:
        parts = s.split('十', 1)
        t = CNUM.get(parts[0], 1) if parts[0] else 1
        r = CNUM.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
        return t * 10 + r
    return CNUM.get(s, 0)

def find_chapters_in_txt(txt):
    lines = txt.split('\n')
    starts = []
    offset = 0
    for line in lines:
        starts.append(offset)
        offset += len(line) + 1
    result = {}
    for i, line in enumerate(lines):
        m = re.match(r'^史记卷([一二三四五六七八九十百]+)$', line)
        if not m: continue
        num = cnum(m.group(1))
        if not (1 <= num <= 130): continue
        if i + 1 >= len(lines): continue
        if not re.match(r'^[^\n]{1,40}第[一二三四五六七八九十百]+$', lines[i+1]): continue
        if i + 2 < len(lines) and re.match(r'^史记卷[一二三四五六七八九十百]+$', lines[i+2]):
            continue  # TOC
        if num not in result:
            result[num] = starts[i]
    # 生成 (num, start, end)
    items = sorted(result.items())
    chapters = {}
    for i, (num, pos) in enumerate(items):
        end = items[i+1][1] if i+1 < len(items) else len(txt)
        chapters[num] = (pos, end)
    return chapters

def count_dianjiao(chapter_text):
    counts = {'集解':0, '索隐':0, '正义':0}
    annot_pat = re.compile(r'〔([一二三四五六七八九十百０]+)〕([\s\S]*?)(?=〔[一二三四五六七八九十百０]+〕|\Z)')
    for am in annot_pat.finditer(chapter_text):
        block = am.group(2)
        for m in re.finditer(r'(?:^|[。」〕\s])\s*(集解|索隐|正义)', block):
            counts[m.group(1)] += 1
    return {'jijie': counts['集解'], 'suoyin': counts['索隐'], 'zhengyi': counts['正义']}

def count_ours(json_data):
    c = {'jijie':0,'suoyin':0,'zhengyi':0}
    for n in json_data.get('notes', []):
        for it in n.get('items', []):
            if it.get('source') in c:
                c[it['source']] += 1
    return c

def main():
    txt = TXT.read_text()
    dj_chapters = find_chapters_in_txt(txt)

    # 可对比的章节：wiki 有 + dianjiao 有 + 我们有
    # 年表章节 wiki 就是空的，略掉
    candidates = []
    for num_str in sorted(p.stem.split('-')[0] for p in NOTES_DIR.glob('*-notes.json')):
        if num_str == 'index': continue
        num = int(num_str)
        if num in dj_chapters:
            wiki_h = list(WIKI_DIR.glob(f'{num_str}_*.html'))
            if wiki_h:
                candidates.append((num_str, num))

    random.seed(20260422)
    # 从非年表（13-22）抽 10
    pool = [c for c in candidates if not (13 <= c[1] <= 22)]
    sample = sorted(random.sample(pool, 10), key=lambda x: x[1])

    print(f'抽样 10 章对比三源（wiki HTML / 点校本 TXT / 我们的 notes JSON）：\n')
    cols = ['章', '章名', 'wiki集', 'dj集', '我集', 'wiki索', 'dj索', '我索', 'wiki正', 'dj正', '我正', '三者一致']
    print(f'{"章":<4}{"章名":<24}{"wiki集":>7}{"dj集":>6}{"我集":>6}  {"wiki索":>7}{"dj索":>6}{"我索":>6}  {"wiki正":>7}{"dj正":>6}{"我正":>6}  备注')
    print('-' * 110)

    def colcmp(a, b, c):
        if a == b == c: return 'all match'
        diffs = []
        if a != c: diffs.append(f'wiki-我={a-c:+d}')
        if b != c: diffs.append(f'dj-我={b-c:+d}')
        if a != b: diffs.append(f'wiki-dj={a-b:+d}')
        return ', '.join(diffs)

    for num_str, num in sample:
        wiki_html = list(WIKI_DIR.glob(f'{num_str}_*.html'))[0]
        w = count_wiki(wiki_html.read_text())
        ds, de = dj_chapters[num]
        dj = count_dianjiao(txt[ds:de])
        with open(NOTES_DIR / f'{num_str}-notes.json') as f:
            ours = count_ours(json.load(f))

        name = wiki_html.stem.split('_', 1)[1][:22]
        row = f'{num_str:<4}{name:<24}{w["jijie"]:>7}{dj["jijie"]:>6}{ours["jijie"]:>6}  {w["suoyin"]:>7}{dj["suoyin"]:>6}{ours["suoyin"]:>6}  {w["zhengyi"]:>7}{dj["zhengyi"]:>6}{ours["zhengyi"]:>6}  '
        remarks = []
        for label in ('jijie', 'suoyin', 'zhengyi'):
            r = colcmp(w[label], dj[label], ours[label])
            if r != 'all match':
                lab_cn = {'jijie':'集','suoyin':'索','zhengyi':'正'}[label]
                remarks.append(f'{lab_cn}:{r}')
        print(row + ('; '.join(remarks) if remarks else '✓ 三源一致'))

if __name__ == '__main__':
    main()
