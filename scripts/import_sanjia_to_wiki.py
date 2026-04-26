#!/usr/bin/env python3
"""
import_sanjia_to_wiki.py — 将三家注数据追加到对应的章节 wiki 页面。

策略：
- 数据源：docs/notes_cache/NNN-notes.json（简体）
- 目标：wiki/public/pages/NNN_章节名.md（章节页）
- append-only：若目标页已有 ## 三家注 节，跳过
- 若对应章节页不存在，用 add_page.py 新建
- 通过 edit_page.py 写入（会自动记录修订历史）

用法：
    python3 scripts/import_sanjia_to_wiki.py           # 处理全部130章
    python3 scripts/import_sanjia_to_wiki.py 001       # 只处理第001章
    python3 scripts/import_sanjia_to_wiki.py --dry-run # 预览，不写入
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTES_CACHE = ROOT / 'docs' / 'notes_cache'
PAGES = ROOT / 'wiki' / 'public' / 'pages'
EDIT_PAGE = ROOT / 'wiki' / 'scripts' / 'butler' / 'edit_page.py'
ADD_PAGE = ROOT / 'wiki' / 'scripts' / 'butler' / 'add_page.py'

# 章节名称映射（NNN -> 章节名）
CHAPTER_NAMES = {
    '001': '五帝本纪', '002': '夏本纪', '003': '殷本纪', '004': '周本纪',
    '005': '秦本纪', '006': '秦始皇本纪', '007': '项羽本纪', '008': '高祖本纪',
    '009': '吕太后本纪', '010': '孝文本纪', '011': '孝景本纪', '012': '孝武本纪',
    '013': '三代世表', '014': '十二诸侯年表', '015': '六国年表',
    '016': '秦楚之际月表', '017': '汉兴以来诸侯王年表', '018': '高祖功臣侯者年表',
    '019': '惠景间侯者年表', '020': '建元以来侯者年表', '021': '建元已来王子侯者年表',
    '022': '汉兴以来将相名臣年表', '023': '礼书', '024': '乐书',
    '025': '律书', '026': '历书', '027': '天官书', '028': '封禅书',
    '029': '河渠书', '030': '平准书', '031': '吴太伯世家', '032': '齐太公世家',
    '033': '鲁周公世家', '034': '燕召公世家', '035': '管蔡世家', '036': '陈杞世家',
    '037': '卫康叔世家', '038': '宋微子世家', '039': '晋世家', '040': '楚世家',
    '041': '越王句践世家', '042': '郑世家', '043': '赵世家', '044': '魏世家',
    '045': '韩世家', '046': '田敬仲完世家', '047': '孔子世家', '048': '陈涉世家',
    '049': '外戚世家', '050': '楚元王世家', '051': '荆燕世家',
    '052': '齐悼惠王世家', '053': '萧相国世家', '054': '曹相国世家',
    '055': '留侯世家', '056': '陈丞相世家', '057': '绛侯周勃世家',
    '058': '梁孝王世家', '059': '五宗世家', '060': '三王世家',
    '061': '伯夷列传', '062': '管晏列传', '063': '老子韩非列传',
    '064': '司马穰苴列传', '065': '孙子吴起列传', '066': '伍子胥列传',
    '067': '仲尼弟子列传', '068': '商君列传', '069': '苏秦列传',
    '070': '张仪列传', '071': '樗里子甘茂列传', '072': '穰侯列传',
    '073': '白起王翦列传', '074': '孟子荀卿列传', '075': '孟尝君列传',
    '076': '平原君虞卿列传', '077': '魏公子列传', '078': '春申君列传',
    '079': '范睢蔡泽列传', '080': '乐毅列传', '081': '廉颇蔺相如列传',
    '082': '田单列传', '083': '鲁仲连邹阳列传', '084': '屈原贾生列传',
    '085': '吕不韦列传', '086': '刺客列传', '087': '李斯列传',
    '088': '蒙恬列传', '089': '张耳陈余列传', '090': '魏豹彭越列传',
    '091': '黥布列传', '092': '淮阴侯列传', '093': '韩信卢绾列传',
    '094': '田儋列传', '095': '樊郦滕灌列传', '096': '张丞相列传',
    '097': '郦生陆贾列传', '098': '傅靳蒯成列传', '099': '刘敬叔孙通列传',
    '100': '季布栾布列传', '101': '袁盎晁错列传', '102': '张释之冯唐列传',
    '103': '万石张叔列传', '104': '田叔列传', '105': '扁鹊仓公列传',
    '106': '吴王濞列传', '107': '魏其武安侯列传', '108': '韩长孺列传',
    '109': '李将军列传', '110': '匈奴列传', '111': '卫将军骠骑列传',
    '112': '平津侯主父列传', '113': '南越列传', '114': '东越列传',
    '115': '朝鲜列传', '116': '西南夷列传', '117': '司马相如列传',
    '118': '淮南衡山列传', '119': '循吏列传', '120': '汲郑列传',
    '121': '儒林列传', '122': '酷吏列传', '123': '大宛列传',
    '124': '游侠列传', '125': '佞幸列传', '126': '滑稽列传',
    '127': '日者列传', '128': '龟策列传', '129': '货殖列传',
    '130': '太史公自序',
}


def find_chapter_page(num: str) -> Path | None:
    """找到章节对应的 wiki 页面（文件名以 NNN_ 开头，排除 redirect）。"""
    candidates = list(PAGES.glob(f'{num}_*.md'))
    for p in sorted(candidates):
        content = p.read_text(encoding='utf-8')
        # 跳过 redirect 页
        if 'type: redirect' in content[:500]:
            continue
        return p
    return None


def build_anchor_display(note: dict) -> str:
    """构建原文上下文展示文字。"""
    anchor = note.get('anchor_text', '')
    before = note.get('before_context', '')
    after = note.get('after_context', '')

    if not anchor and not before and not after:
        return '（篇首总注）'

    # 显示：…before_context**anchor_text**after_context…
    parts = []
    if before:
        # 只保留最后15字
        parts.append(f'……{before[-15:]}' if len(before) > 15 else before)
    if anchor:
        parts.append(f'**{anchor}**')
    if after:
        # 只保留前15字
        parts.append(after[:15] + '……' if len(after) > 15 else after)

    return ''.join(parts)


def build_sanjia_section(notes_data: dict) -> str:
    """构建 ## 三家注 节的 markdown 内容。"""
    notes = notes_data.get('notes', [])
    chapter = notes_data.get('chapter', '')

    # 统计
    jijie_count = sum(
        1 for n in notes for item in n.get('items', []) if item['source'] == 'jijie'
    )
    suoyin_count = sum(
        1 for n in notes for item in n.get('items', []) if item['source'] == 'suoyin'
    )
    zhengyi_count = sum(
        1 for n in notes for item in n.get('items', []) if item['source'] == 'zhengyi'
    )

    lines = [
        '## 三家注',
        '',
        f'共 {len(notes)} 条注释（集解 {jijie_count} 条 · 索隐 {suoyin_count} 条 · 正义 {zhengyi_count} 条）。',
        '',
    ]

    source_labels = {
        'jijie': '集解',
        'suoyin': '索隐',
        'zhengyi': '正义',
    }

    for note in notes:
        note_id = note.get('id', '')
        anchor_display = build_anchor_display(note)
        items = note.get('items', [])

        if not items:
            continue

        lines.append(f'#### {note_id} · {anchor_display}')
        lines.append('')

        for item in items:
            label = source_labels.get(item['source'], item['label'])
            text = item['text'].strip()
            lines.append(f'> **【{label}】** {text}')
            lines.append('>')

        # 移除最后一个多余的 >
        if lines and lines[-1] == '>':
            lines.pop()

        lines.append('')

    return '\n'.join(lines)


def process_chapter(num: str, dry_run: bool = False) -> str:
    """处理单个章节，返回状态信息。"""
    notes_file = NOTES_CACHE / f'{num}-notes.json'
    if not notes_file.exists():
        return f'[{num}] 跳过：无 notes 文件'

    with notes_file.open(encoding='utf-8') as f:
        notes_data = json.load(f)

    notes = notes_data.get('notes', [])
    if not notes:
        return f'[{num}] 跳过：无注释数据'

    page_path = find_chapter_page(num)

    if page_path:
        # 检查是否已有 ## 三家注 节
        content = page_path.read_text(encoding='utf-8')
        if '## 三家注' in content:
            return f'[{num}] 跳过：已有三家注节 ({page_path.name})'

        # 追加三家注节
        new_section = build_sanjia_section(notes_data)
        new_content = content.rstrip() + '\n\n' + new_section + '\n'

        if dry_run:
            return f'[{num}] DRY-RUN: 将向 {page_path.name} 追加 {len(notes)} 条注释'

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', encoding='utf-8', delete=False
        ) as tmp:
            tmp.write(new_content)
            tmp_path = tmp.name

        slug = page_path.stem
        result = subprocess.run(
            [
                sys.executable, str(EDIT_PAGE),
                slug, tmp_path,
                '--summary', f'sanjia-import: 追加三家注 {len(notes)} 条',
                '--author', 'butler',
            ],
            capture_output=True, text=True, cwd=str(ROOT)
        )
        Path(tmp_path).unlink(missing_ok=True)

        if result.returncode != 0:
            return f'[{num}] 错误：edit_page 失败 ({result.stderr.strip()})'
        return f'[{num}] 完成：{page_path.name}，追加 {len(notes)} 条注释'

    else:
        # 章节页不存在，新建
        chapter_name = CHAPTER_NAMES.get(num, f'第{num}章')
        slug = f'{num}_{chapter_name}'

        new_content = f"""---
id: {slug}
type: chapter
label: {chapter_name}
chapter_no: {num}
aliases: [{chapter_name}, {num}]
sources: [{chapter_name}]
tags: [史记]
auto_generated: true
quality: stub
---

# {slug}

《史记》第 {int(num)} 篇

{build_sanjia_section(notes_data)}
"""

        if dry_run:
            return f'[{num}] DRY-RUN: 将新建页面 {slug}.md，含 {len(notes)} 条注释'

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', encoding='utf-8', delete=False
        ) as tmp:
            tmp.write(new_content)
            tmp_path = tmp.name

        result = subprocess.run(
            [
                sys.executable, str(ADD_PAGE),
                slug, tmp_path,
                '--summary', f'sanjia-import: 新建章节页并导入三家注 {len(notes)} 条',
                '--author', 'butler',
            ],
            capture_output=True, text=True, cwd=str(ROOT)
        )
        Path(tmp_path).unlink(missing_ok=True)

        if result.returncode != 0:
            return f'[{num}] 错误：add_page 失败 ({result.stderr.strip()})'
        return f'[{num}] 完成（新建）：{slug}.md，含 {len(notes)} 条注释'


def main() -> None:
    ap = argparse.ArgumentParser(description='将三家注导入章节 wiki 页面')
    ap.add_argument(
        'chapters', nargs='*', help='章节编号（如 001 002），不填则处理全部'
    )
    ap.add_argument('--dry-run', action='store_true', help='预览，不实际写入')
    args = ap.parse_args()

    if args.chapters:
        nums = [c.zfill(3) for c in args.chapters]
    else:
        # 找到所有存在的 notes 文件
        nums = sorted(
            p.stem.replace('-notes', '')
            for p in NOTES_CACHE.glob('*-notes.json')
            if p.stem != 'index-notes'
        )

    total = len(nums)
    done = 0
    skipped = 0
    errors = 0

    for num in nums:
        msg = process_chapter(num, dry_run=args.dry_run)
        print(msg)
        if '完成' in msg:
            done += 1
        elif '跳过' in msg or 'DRY-RUN' in msg:
            skipped += 1
        else:
            errors += 1

    print()
    print(f'处理完成：共 {total} 章，完成 {done}，跳过 {skipped}，错误 {errors}')


if __name__ == '__main__':
    main()
