#!/usr/bin/env python3
"""V4：修复 v3 中 集解/索隱 的 regex 过严导致大量条目漏抽的问题。

问题根因：v3 的 集解/索隱 pattern 要求注释内容被包在 <span style="color:green/deeppink">
内、且结束必须紧邻下一个 background-color: 标签或字符串末尾。当内容里嵌套了
<span style="text-decoration:underline">...</span>（专名下划线）时，.*? 会在遇到第一个
</span> 时想停下来，但后视断言 (?=<span[^>]*background-color:|$) 不满足，只能再延伸，
但因为有 </small> 边界，最终导致整条注释被丢弃。

V4 改为和 正義 完全对称的宽松模式：从标签 span 开始，一路贪非贪匹配直到遇到下一个
background-color 标签或 </small>。再用 BeautifulSoup 处理捕获到的 HTML 片段提取纯文。

与 v3 比对（抽样章节）：集解/索隱 提取条目数从 v3 的 ~40% 提升到与源 HTML 完全对齐。
"""

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString


# 对称宽松模式：三种标签都从 label span 起，匹配到下一个 label 或 </small>
PAT_JIJIE = re.compile(
    r'<span[^>]*background-color:\s*green[^>]*>集解</span>(.*?)(?=<span[^>]*background-color:|</small>)',
    re.DOTALL | re.IGNORECASE
)
PAT_SUOYIN = re.compile(
    r'<span[^>]*background-color:\s*deepPink[^>]*>索隱</span>(.*?)(?=<span[^>]*background-color:|</small>)',
    re.DOTALL | re.IGNORECASE
)
PAT_ZHENGYI = re.compile(
    r'<span[^>]*background-color:\s*#966[^>]*>正義</span>(.*?)(?=<span[^>]*background-color:|</small>)',
    re.DOTALL | re.IGNORECASE
)

# 三者统一按 "在 HTML 中的出现顺序" 收集，确保 items 顺序与原文一致
_ALL_LABELS = re.compile(
    r'<span[^>]*background-color:\s*(?P<bg>green|deepPink|#966)[^>]*>(?P<label>集解|索隱|正義)</span>(?P<rest>.*?)(?=<span[^>]*background-color:|</small>)',
    re.DOTALL | re.IGNORECASE
)

_LABEL_MAP = {
    '集解': ('jijie', '集解'),
    '索隱': ('suoyin', '索隱'),
    '正義': ('zhengyi', '正義'),
}


def _clean_html_to_text(html_fragment: str) -> str:
    text = BeautifulSoup(html_fragment, 'html.parser').get_text()
    # 规整空白（保留中英文标点）：压缩连续空白为单个空格，再 strip
    text = re.sub(r'\s+', '', text)
    return text.strip()


def extract_notes_from_html(html_path):
    """从 wikisource_sanjia HTML 中提取三家注。

    返回 [{id, anchor_text, before_context, after_context, items}]，每个 <small> 标记对应一条。
    一条可能有多个 items（集解/索隱/正義 并列）。
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    soup = BeautifulSoup(content, 'html.parser')

    # 找到所有包含三家注的 <small> 标签（通过特定样式过滤）
    small_tags = soup.find_all(
        'small',
        style=lambda value: value and 'color:var(--color-destructive--visited' in value
    )

    notes = []
    note_id = 0

    for small_tag in small_tags:
        note_items = []

        # 前后文 context（文字拼接），用于匹配定位
        before_parts = []
        chars_before = 0
        prev = small_tag.previous_sibling
        while prev and chars_before < 40:
            if isinstance(prev, NavigableString):
                txt = str(prev).strip()
            else:
                txt = prev.get_text().strip() if prev.name not in ('small', 'script', 'style') else ''
            if txt:
                before_parts.insert(0, txt)
                chars_before += len(txt)
            prev = prev.previous_sibling
        before_context = ''.join(before_parts)
        if len(before_context) > 30:
            before_context = '...' + before_context[-30:]

        after_parts = []
        chars_after = 0
        nxt = small_tag.next_sibling
        while nxt and chars_after < 40:
            if isinstance(nxt, NavigableString):
                txt = str(nxt).strip()
            else:
                txt = nxt.get_text().strip() if nxt.name not in ('small', 'script', 'style') else ''
                # 遇到下一个块级标签即截断，避免把下一个段落整段吞进来
                if nxt.name and nxt.name not in ('span', 'i', 'b', 'em', 'strong'):
                    if txt:
                        after_parts.append(txt)
                        chars_after += len(txt)
                    break
            if txt:
                after_parts.append(txt)
                chars_after += len(txt)
            nxt = nxt.next_sibling
        after_context = ''.join(after_parts)
        if len(after_context) > 30:
            after_context = after_context[:30] + '...'

        anchor_text = ''
        if before_parts:
            last = before_parts[-1]
            anchor_text = last[-20:] if len(last) > 20 else last

        # 提取 items：按在 HTML 中出现的先后顺序
        small_html = str(small_tag)
        for m in _ALL_LABELS.finditer(small_html):
            lab = m.group('label')
            src, disp = _LABEL_MAP[lab]
            raw = m.group('rest')
            text = _clean_html_to_text(raw)
            if not text:
                continue
            note_items.append({'source': src, 'label': disp, 'text': text})

        if not note_items:
            continue

        note_id += 1
        notes.append({
            'id': f'n{note_id:03d}',
            'anchor_text': anchor_text,
            'before_context': before_context,
            'after_context': after_context,
            'items': note_items,
            'sentence_id': None,
        })

    return notes


def main():
    root = Path(__file__).resolve().parent.parent
    input_dir = root / 'corpus' / 'shiji' / 'wikisource_sanjia'
    output_dir = root / 'data' / 'notes'
    output_dir.mkdir(parents=True, exist_ok=True)

    html_files = sorted(input_dir.glob('*.html'))
    print(f'找到 {len(html_files)} 个 HTML 文件，开始处理...\n')

    success = 0
    for html_file in html_files:
        name = html_file.stem
        num = name.split('_')[0]
        try:
            notes = extract_notes_from_html(html_file)
        except Exception as e:
            print(f'✗ [{num}] {name}: {e}')
            continue

        jj = sum(1 for n in notes for it in n['items'] if it['source'] == 'jijie')
        sy = sum(1 for n in notes for it in n['items'] if it['source'] == 'suoyin')
        zy = sum(1 for n in notes for it in n['items'] if it['source'] == 'zhengyi')

        out = {'chapter': name, 'notes': notes}
        with open(output_dir / f'{num}-notes.json', 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        success += 1
        print(f'✓ [{num}] {name}  锚点={len(notes):>4}  集解={jj:>4}  索隱={sy:>4}  正義={zy:>4}')

    print(f'\n完成：{success}/{len(html_files)}')


if __name__ == '__main__':
    main()
