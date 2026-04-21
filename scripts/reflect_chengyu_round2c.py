#!/usr/bin/env python3
"""
成语第二轮反思 C：基于去标注纯文本的定位

方法：
1. 对每章构建 "stripped text" 及其到原文位置的映射
2. 在 stripped text 中搜索每个成语
3. 回查原文位置，看该片段是否横跨标注 / 或被实体标注覆盖
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHENGYU_MD = ROOT / "kg/vocabularies/data/史记成语典故.md"
CHAPTER_DIR = ROOT / "chapter_md"


def parse_chengyu_md(md_file):
    content = md_file.read_text(encoding='utf-8')
    entries = []
    current_chapter = None
    for line in content.split('\n'):
        line = line.strip()
        m = re.match(r'^###\s+(\d+)\s+', line)
        if m:
            current_chapter = m.group(1).zfill(3)
            continue
        if current_chapter and line.startswith('|') and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]
            if len(parts) >= 2 and parts[0] and parts[0] != '成语':
                name = parts[0]
                original = parts[1]
                if '…' in original or '...' in original:
                    continue
                if any(c in name for c in ['/', '/']):
                    continue
                if name.startswith(('（', '(')):
                    continue
                entries.append((current_chapter, name, original))
    return entries


def build_strip_map(content):
    """
    返回 (stripped_text, pos_map)
    pos_map[i] = 原 content 中的位置，表示 stripped_text[i] 对应原 content 中哪个位置
    """
    stripped_chars = []
    pos_map = []

    # 状态：是否在标注内
    # 标注括号：〖〗 ⟦⟧ 〘〙
    # 为简化，我们实际上保留内部文字但跳过括号符号和类型标记
    # 〖X text〗 → text（X 是单字类型标记，跳过）
    # ⟦X text⟧ → text
    # 〘※text〙 或 〘※text|other〙 → text

    i = 0
    N = len(content)
    while i < N:
        c = content[i]
        if c == '〖':
            # 找结束符
            end = content.find('〗', i)
            if end < 0:
                i += 1
                continue
            inner = content[i+1:end]
            # 首字符是类型标记
            if inner:
                inner_body = inner[1:]
                # 消歧：surface|canonical，取 surface
                if '|' in inner_body:
                    inner_body = inner_body.split('|')[0]
                # 记录每个字符
                # 这些字符在原文中的位置从 i+2 开始连续（如果没有消歧）
                # 但由于消歧情况，实际位置复杂，这里只记录从 i+2 到 i+2+len(surface)
                for j, ch in enumerate(inner_body):
                    stripped_chars.append(ch)
                    pos_map.append(i + 2 + j)
            i = end + 1
        elif c == '⟦':
            end = content.find('⟧', i)
            if end < 0:
                i += 1
                continue
            inner = content[i+1:end]
            if inner:
                inner_body = inner[1:]
                if '|' in inner_body:
                    inner_body = inner_body.split('|')[0]
                for j, ch in enumerate(inner_body):
                    stripped_chars.append(ch)
                    pos_map.append(i + 2 + j)
            i = end + 1
        elif c == '〘':
            end = content.find('〙', i)
            if end < 0:
                i += 1
                continue
            inner = content[i+1:end]
            # 〘※text〙 or 〘※text|other〙
            if inner.startswith('※'):
                inner_body = inner[1:]
                if '|' in inner_body:
                    inner_body = inner_body.split('|')[0]
                for j, ch in enumerate(inner_body):
                    stripped_chars.append(ch)
                    pos_map.append(i + 2 + j)
            i = end + 1
        else:
            stripped_chars.append(c)
            pos_map.append(i)
            i += 1

    return ''.join(stripped_chars), pos_map


def classify_span(content, orig_start, orig_end):
    """
    判断原文 [orig_start, orig_end) 区间的标注状态。
    返回 'idiom' | 'verb' | 'entity' | 'entity_partial' | 'clean' | 'mixed'
    """
    # 扫描该区间，看是否跨越任何标注括号
    # 更准确：判断 orig_start 和 orig_end-1 各自是否在标注内
    def ann_state_at(pos):
        before = content[:pos]
        open_i = before.rfind('〘')
        close_i = before.rfind('〙')
        if open_i > close_i:
            return 'idiom'
        open_v = before.rfind('⟦')
        close_v = before.rfind('⟧')
        if open_v > close_v:
            return 'verb'
        open_e = before.rfind('〖')
        close_e = before.rfind('〗')
        if open_e > close_e:
            return 'entity'
        return 'clean'

    s1 = ann_state_at(orig_start)
    s2 = ann_state_at(orig_end - 1) if orig_end > orig_start else s1

    # 检查区间内部是否有标注括号符号
    region = content[orig_start:orig_end]
    has_bracket = any(b in region for b in '〖〗⟦⟧〘〙')

    if s1 == s2 and not has_bracket:
        return s1
    return 'mixed'


def main():
    entries = parse_chengyu_md(CHENGYU_MD)
    print(f"# 成语词表：{len(entries)} 条\n")

    by_chapter = {}
    for chap, name, original in entries:
        by_chapter.setdefault(chap, []).append((name, original))

    # 每个分类的结果
    by_class = {
        'clean_untagged': [],      # 在干净文本中，未标注 → 可以直接补标
        'entity': [],              # 整体在实体标注内 → 应改为成语标注
        'entity_partial': [],      # 与实体部分重叠 → 需要人工判断
        'verb': [],
        'idiom_other': [],         # 在另一个成语标注内
        'mixed': [],
    }

    for chap_num, chap_entries in sorted(by_chapter.items()):
        if chap_num == '130':
            continue
        files = list(CHAPTER_DIR.glob(f"{chap_num}_*.tagged.md"))
        if not files:
            continue
        chapter_file = files[0]
        content = chapter_file.read_text(encoding='utf-8')

        stripped, pos_map = build_strip_map(content)

        for name, original in chap_entries:
            # 跳过已有 〘※name〙 标注的
            if f'〘※{name}' in content:
                continue

            # 在 stripped 中搜索 name
            start = 0
            while True:
                idx = stripped.find(name, start)
                if idx < 0:
                    break
                # 映射到原文区间
                orig_start = pos_map[idx]
                orig_end = pos_map[idx + len(name) - 1] + 1

                cls = classify_span(content, orig_start, orig_end)
                region = content[orig_start:orig_end]

                ctx_start = max(0, orig_start - 20)
                ctx_end = min(len(content), orig_end + 20)
                ctx = content[ctx_start:ctx_end].replace('\n', ' ')

                info = {
                    'chapter': chapter_file.name,
                    'name': name,
                    'region': region,
                    'orig_start': orig_start,
                    'ctx': ctx,
                }

                # 检查是否是 markdown 标题行
                line_start = content.rfind('\n', 0, orig_start) + 1
                line = content[line_start:content.find('\n', orig_end)]
                if line.startswith('#'):
                    # 在标题行里，跳过
                    start = idx + 1
                    continue

                if cls == 'clean':
                    by_class['clean_untagged'].append(info)
                elif cls == 'entity':
                    by_class['entity'].append(info)
                elif cls == 'verb':
                    by_class['verb'].append(info)
                elif cls == 'idiom':
                    by_class['idiom_other'].append(info)
                elif cls == 'mixed':
                    # 进一步判断是不是"部分在实体内"
                    by_class['entity_partial'].append(info)

                start = idx + 1

    for k, v in by_class.items():
        print(f"## {k}: {len(v)} 处")
    print()

    # 详细打印 entity / entity_partial
    for cat in ['entity', 'entity_partial', 'verb', 'idiom_other', 'clean_untagged']:
        if not by_class[cat]:
            continue
        print(f"\n### {cat} 明细（{len(by_class[cat])} 处）")
        for r in by_class[cat][:60]:
            print(f"  [{r['chapter']}] '{r['name']}'")
            print(f"    region: {r['region']}")
            print(f"    ctx:    ...{r['ctx']}...")
        if len(by_class[cat]) > 60:
            print(f"  ... 共 {len(by_class[cat])} 处，仅显示前 60")


if __name__ == '__main__':
    main()
