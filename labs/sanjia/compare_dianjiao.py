"""与 corpus/shiji/史记集解三家注索隐正义.txt（中华书局点校本格式）比对。

格式说明：
  正文：... 某词〔一〕某词〔二〕 ...
  注条：〔一〕集解 ... / 〔一〕索隐 ... / 〔一〕正义 ...
  所以一个 anchor 编号 〔N〕 下可能有多条 annotations（最多 3 种 source）。

章节分隔：
  每章以 "史记卷N\n<title>第X" 形式开始（N = 1..130）。
  查找 "^史记卷N$" 连续两行后，取到下一个这种标志前。
"""

import re
from pathlib import Path
from collections import Counter

TXT = Path('/home/baojie/work/knowledge/shiji-kb/corpus/shiji/史记集解三家注索隐正义.txt')

CNUM_MAP = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,'百':100,'０':0}

def cnum(s):
    """中文数字转 int，处理 一 / 十 / 二十 / 二十三 / 一百 / 一百二十三 等"""
    if not s:
        return 0
    # 单字符
    if len(s) == 1:
        return CNUM_MAP.get(s, 0)
    # 含百
    if '百' in s:
        parts = s.split('百', 1)
        h = CNUM_MAP.get(parts[0], 1) if parts[0] else 1
        rest = parts[1]
        if not rest:
            return h * 100
        # rest 可以是 "二十三" 等
        if rest[0] in '零０' or (len(rest) == 1 and rest in CNUM_MAP):
            # "一百二" = 120? 还是 102?
            # 古文一般 "一百二"=120,"一百零二"=102
            return h * 100 + CNUM_MAP.get(rest, 0) * (10 if len(rest) == 1 and rest not in '零０' else 1)
        return h * 100 + cnum(rest)
    # 含十
    if '十' in s:
        parts = s.split('十', 1)
        t = CNUM_MAP.get(parts[0], 1) if parts[0] else 1
        rest = parts[1]
        return t * 10 + (CNUM_MAP.get(rest, 0) if rest else 0)
    return CNUM_MAP.get(s, 0)


def find_chapter_bodies(txt):
    """找到每章正文起止位置。"""
    # 匹配形如 "史记卷[一..百三十]" 单独一行 + 紧跟的 "<title>第X"
    # 注意：前面 TOC 里也会出现，要排除纯 TOC 区域；实际上章首有 "集解" / 正文内容，
    # TOC 里则是连续的 "卷X\n卷Y\n" 罗列。
    # 用行级搜索
    lines = txt.split('\n')
    line_starts = []
    offset = 0
    for line in lines:
        line_starts.append(offset)
        offset += len(line) + 1

    chapters = []
    for i, line in enumerate(lines):
        m = re.match(r'^史记卷([一二三四五六七八九十百]+)$', line)
        if not m: continue
        num = cnum(m.group(1))
        if not (1 <= num <= 130): continue
        # 下一行应是 "<title>第X"
        if i + 1 >= len(lines): continue
        next_line = lines[i + 1]
        if not re.match(r'^[^\n]{1,40}第[一二三四五六七八九十百]+$', next_line): continue
        # 检查不是 TOC 区域（TOC 里连续多个 "史记卷X\t<page>" 形式，或 "史记卷X\n<title>...\n史记卷Y"）
        # 通过 line i+2 不能再是 "史记卷N" 来判断
        if i + 2 < len(lines) and re.match(r'^史记卷[一二三四五六七八九十百]+$', lines[i + 2]):
            continue
        chapters.append((num, line_starts[i]))

    # 按 num 去重，保留最早出现的那个（即最靠前的正文开始）
    seen = set()
    unique = []
    for num, pos in chapters:
        if num in seen: continue
        seen.add(num)
        unique.append((num, pos))
    unique.sort(key=lambda x: x[1])

    # 生成 (num, start, end)
    result = []
    for i, (num, pos) in enumerate(unique):
        end = unique[i+1][1] if i+1 < len(unique) else len(txt)
        result.append((num, pos, end))
    return sorted(result, key=lambda x: x[0])


def count_chapter(chapter_text):
    """统计本章内注条数（集解/索隐/正义）。

    注条格式：每条以 "〔N〕集解"/"〔N〕索隐"/"〔N〕正义" 开头。
    注意：同一 anchor N 下若有多种 source，会出现并列形式 "〔一〕集解...索隐..." 或分行。
    规则：count every occurrence of "集解"/"索隐"/"正义" 紧跟在 "〔...〕" 之后 OR 在注释行内与另一种连用。
    """
    # 最稳妥：在注条行里，匹配 "(?:〔[^〕]+〕|^|。\s)集解|索隐|正义" 之后是内容
    # 但我们需要非重复计数。最实际做法：
    #   1) 找到所有注条 span：从 "〔数字〕" 行起到下一个 〔数字〕 行或正文
    #   2) 在每个注条文本中，按顺序出现的 "集解/索隐/正义" 视作一个 item
    # 因为源 HTML 对照已经证实 v4 抽取与 HTML 完全对齐，所以这里只是独立校验。
    counts = {'集解':0, '索隐':0, '正义':0}

    # 策略：抽出所有"注条块"——从 "〔N〕" 开始到下一个 "〔N〕" 或章节末。
    # 在每块内，按顺序统计 集解/索隐/正义 label 的出现次数。
    # 关键：label 之后紧随的必须是正文（非空白），且前方通常为块首 / 。 / 」 / 〕。
    # 用简化近似：在注条块内直接 findall 这三个词作为标签（这批文本几乎不会在正文中随意出现它们）。
    annot_pat = re.compile(r'〔([一二三四五六七八九十百０]+)〕([\s\S]*?)(?=〔[一二三四五六七八九十百０]+〕|\Z)')
    for am in annot_pat.finditer(chapter_text):
        block = am.group(2)
        # 只算真正的 label: 开头或紧邻结束标点后出现的
        for m in re.finditer(r'(?:^|[。」〕\s])\s*(集解|索隐|正义)(?=[^\w]|[^\s])', block):
            lab = m.group(1)
            if lab in counts:
                counts[lab] += 1
    return counts


def main():
    txt = TXT.read_text()
    chapters = find_chapter_bodies(txt)
    print(f'找到章节: {len(chapters)}')
    if len(chapters) < 120:
        print('章节识别不全，前 10 个：')
        for c in chapters[:10]: print('  ', c)

    print(f'\n{"章":<4}{"集解":>8}{"索隐":>8}{"正义":>8}')
    print('-' * 34)
    tot = Counter()
    for num, start, end in chapters:
        seg = txt[start:end]
        c = count_chapter(seg)
        tot['集解'] += c['集解']; tot['索隐'] += c['索隐']; tot['正义'] += c['正义']
        if num <= 10 or num in [27, 63, 74, 100, 117, 130]:
            print(f'{num:>3}  {c["集解"]:>7}  {c["索隐"]:>7}  {c["正义"]:>7}')
    print('-' * 34)
    print(f'合计  {tot["集解"]:>7}  {tot["索隐"]:>7}  {tot["正义"]:>7}')


if __name__ == '__main__':
    main()
