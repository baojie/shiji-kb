"""分析所有章节中未能定位的三家注：揭示不匹配类型，为算法改进提供依据。

步骤：
1. 对每章加载 HTML，提取章节全文（走 JS 相同的过滤：去拼音、去 para-num、去标注容器）
2. 对每条 note 尝试三策略匹配（含变体归一）
3. 对未匹配的 notes，找 note.before_context 最后 N 字符在章节中的"最近"位置，
   输出最长公共后缀 / 字符差异统计
4. 全局汇总：
   - 变体字（notes 用 A 章节用 B）频次
   - 未匹配长度分布
   - 短匹配成功率（如 last 6 字符 indexOf）
"""
import json
import re
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path('/home/baojie/work/knowledge/shiji-kb')
CACHE_DIR = ROOT / 'docs' / 'notes_cache'
CHAPTERS_DIR = ROOT / 'docs' / 'chapters'

# 与 JS 同步的变体映射
VARIANT_MAP = {
    '於':'于','後':'后','蟲':'虫','衛':'卫','衞':'卫','擒':'禽',
    '䇲':'策','䝙':'貙','徧':'遍','悳':'德','辠':'罪','愬':'诉',
}

def norm(s):
    return ''.join(VARIANT_MAP.get(c, c) for c in s or '')

def strip_leading_ellipsis(s):
    return re.sub(r'^(\.{3}|…)', '', s or '')

def extract_clean_text(html):
    """粗略模拟 JS walker：去标签、去拼音 <rt>、去 para-num、去注释容器。"""
    # 去三家注容器（容易残留）
    html = re.sub(r'<div class="sanjia-notes-container[^"]*".*?</div>\s*</div>', '', html, flags=re.DOTALL)
    # 去 rt 拼音
    html = re.sub(r'<rt[^>]*>.*?</rt>', '', html, flags=re.DOTALL)
    # 去 para-num 段落编号
    html = re.sub(r'<a [^>]*class="para-num"[^>]*>.*?</a>', '', html, flags=re.DOTALL)
    # 去 original-text-link 原文按钮
    html = re.sub(r'<a [^>]*class="original-text-link"[^>]*>.*?</a>', '', html, flags=re.DOTALL)
    # 去 h1-h6 标题
    html = re.sub(r'<h[1-6][^>]*>.*?</h[1-6]>', '', html, flags=re.DOTALL)
    # 去 nav
    html = re.sub(r'<nav.*?</nav>', '', html, flags=re.DOTALL)
    # 去 settings-panel 等
    html = re.sub(r'<button id="settings[^"]*".*?</button>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div id="settings[^"]*".*?</div>', '', html, flags=re.DOTALL)
    # 去所有剩余标签
    text = re.sub(r'<[^>]+>', '', html)
    # 去 &nbsp; 等实体
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    # 折叠空白
    return re.sub(r'\s+', '', text)

def longest_common_suffix(s, chapter_text, max_len=30):
    """尝试从 s 的末尾截取子串做 indexOf；返回能命中的最长后缀。"""
    best = 0
    for l in range(len(s), 0, -1):
        if s[-l:] in chapter_text:
            return l
    return 0

def main():
    # 收集所有章节
    chapters = sorted(f for f in CACHE_DIR.glob('*-notes.json'))

    total_notes = 0
    total_matched = 0
    total_unmatched = 0
    unmatched_len_dist = Counter()
    unmatched_suffix_hit = Counter()  # {suffix_len: count}
    chapter_stats = []
    variant_pairs = Counter()  # (notes_char, chapter_char) 对比某位置的差异

    for cache_file in chapters:
        num = cache_file.stem.split('-')[0]
        if num == 'index':
            continue
        chapter_html_files = list(CHAPTERS_DIR.glob(f'{num}_*.html'))
        if not chapter_html_files:
            continue
        html = chapter_html_files[0].read_text()
        chapter_text = extract_clean_text(html)
        chapter_norm = norm(chapter_text)

        with open(cache_file) as f:
            notes = json.load(f)['notes']

        matched_ch = 0
        unmatched_ch = []
        for note in notes:
            before = strip_leading_ellipsis(note.get('before_context', ''))
            after = note.get('after_context', '')
            anchor = note.get('anchor_text', '')

            if not (before or after or anchor):
                continue  # 章首（无锚）

            bN = norm(before)
            aN = norm(after)
            matched = False
            if bN and aN and (bN + aN) in chapter_norm:
                matched = True
            elif bN and len(bN) >= 4 and bN in chapter_norm:
                matched = True

            if matched:
                matched_ch += 1
            else:
                unmatched_ch.append(note)

        total_notes += matched_ch + len(unmatched_ch)
        total_matched += matched_ch
        total_unmatched += len(unmatched_ch)

        # 分析这章的 unmatched
        for note in unmatched_ch:
            before = strip_leading_ellipsis(note.get('before_context', ''))
            bN = norm(before)
            unmatched_len_dist[len(bN)] += 1

            # 从尾部找最长可匹配后缀
            best_l = 0
            for l in range(min(len(bN), 20), 0, -1):
                if bN[-l:] in chapter_norm:
                    best_l = l
                    break
            unmatched_suffix_hit[best_l] += 1

            # 如果能命中 last N >= 4 chars，比较 (N+1) 的第一个差异字符
            if best_l >= 4 and best_l < len(bN):
                # last best_l chars match, char at bN[-best_l-1] doesn't
                note_ch = bN[-best_l-1]
                # 找所在位置的 chapter char
                pos = chapter_norm.rfind(bN[-best_l:])
                if pos > 0:
                    ch_ch = chapter_norm[pos-1]
                    if note_ch != ch_ch and '\u4e00' <= note_ch <= '\u9fff' and '\u4e00' <= ch_ch <= '\u9fff':
                        variant_pairs[(note_ch, ch_ch)] += 1

        chapter_stats.append({
            'num': num,
            'total': matched_ch + len(unmatched_ch),
            'matched': matched_ch,
            'unmatched': len(unmatched_ch),
        })

    print(f'\n全量统计：')
    print(f'  已匹配（含归一化后）: {total_matched}')
    print(f'  未匹配: {total_unmatched}')
    print(f'  总笺注（有锚）: {total_notes}')
    print(f'  匹配率: {total_matched*100//max(total_notes,1)}%')

    print(f'\n未匹配 note 的 before_context 长度分布（前 15）:')
    for l, c in sorted(unmatched_len_dist.items())[:15]:
        print(f'  len={l:>3}: {c}')

    print(f'\n未匹配 note 的最长可命中后缀分布：')
    for l in sorted(unmatched_suffix_hit.keys(), reverse=True):
        c = unmatched_suffix_hit[l]
        print(f'  可命中后缀 ≥ {l:>2}: {c}')

    # 从"可命中后缀"统计能看出：如果绝大多数能命中 >= 6 字符后缀，则
    # 可用"截短 before_context 到后 N 字符"的 fallback 补回绝大部分

    cumul = 0
    for l in sorted(unmatched_suffix_hit.keys(), reverse=True):
        cumul += unmatched_suffix_hit[l]
        if l in (8, 6, 4, 2):
            print(f'  累计（≥{l}）: {cumul}')

    print(f'\n差异字符对（notes ch → chapter ch，前 50）:')
    for (a, b), c in variant_pairs.most_common(50):
        print(f'  {a!r}  →  {b!r}   ×{c}')

if __name__ == '__main__':
    main()
