#!/usr/bin/env python3
"""
将 Yann/Twenty-Four-Histories 仓库
(https://github.com/Yann-Chen/Twenty-Four-Histories) 中
《史记》的 .tex 文件转换为 corpus/shiji/点校本/NNN_章节名_点校本.txt。

源仓库本地路径：/home/baojie/work/thirdparty/Twenty-Four-Histories/史記/

此版本为：
- 繁体中文文言原文
- 基于"点校本二十四史"（中华书局）
- 仅包含 121 个文件：120 章正文（不含十表，表多为表格形式）+ 史记.tex 主文件

输出：
- 文件名按简体章名映射到 NNN 编号（与 chapter_md/ 一致）
- 繁体原文保留（不转简），便于需要繁体原貌的场景
- 同时在 corpus/shiji/繁体/README.md 注明来源
"""

import re
import sys
from pathlib import Path

try:
    import opencc
    T2S = opencc.OpenCC('t2s')
except ImportError:
    print('请先安装 opencc：pip install opencc-python-reimplemented', file=sys.stderr)
    sys.exit(1)

SOURCE_DIR = Path('/home/baojie/work/thirdparty/Twenty-Four-Histories/史記')
OUTPUT_DIR = Path('corpus/shiji/点校本')
CHAPTER_MD_DIR = Path('chapter_md')


def build_name_to_num() -> dict:
    """从 chapter_md/ 构建简体章名→章号 的映射。"""
    m = {}
    for f in CHAPTER_MD_DIR.glob('*.tagged.md'):
        # 文件名格式：NNN_章节名.tagged.md
        match = re.match(r'(\d{3})_(.+)\.tagged\.md', f.name)
        if match:
            m[match.group(2)] = int(match.group(1))
    return m


# opencc 转换与本库章节命名差异的手动映射
# (opencc 结果 → 本库文件名)
NAME_ALIASES = {
    '张耳陈余列传': '张耳陈馀列传',  # 馀/余 异体
    '袁盎鼌错列传': '袁盎晁错列传',  # 鼂→鼌 vs 本库 晁
}


def parse_tex(content: str) -> tuple:
    """
    解析 .tex 文件。返回 (title, paragraphs)。
    格式：
        \\article{章节名}
        \\begin{pinyinscope}
        段1
        段2
        ...
        \\end{pinyinscope}
    """
    title_match = re.search(r'\\article\{([^}]+)\}', content)
    title = title_match.group(1) if title_match else ''

    # 抓取 pinyinscope 之间的正文
    scope_match = re.search(
        r'\\begin\{pinyinscope\}(.*?)\\end\{pinyinscope\}',
        content, re.DOTALL
    )
    if scope_match:
        body = scope_match.group(1)
    else:
        body = content

    # 去除 LaTeX 命令（保留中文段落）
    body = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', body)
    body = re.sub(r'\\[a-zA-Z]+', '', body)
    body = body.replace('{', '').replace('}', '')

    # 按空行分段
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', body) if p.strip()]
    return title, paragraphs


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    name_to_num = build_name_to_num()

    matched = 0
    unmatched = []
    for tex in sorted(SOURCE_DIR.glob('*.tex')):
        if tex.stem == '史記':
            continue  # 跳过主文件
        title_trad = tex.stem
        title_simp = T2S.convert(title_trad)
        # 应用人工 alias 映射
        title_simp = NAME_ALIASES.get(title_simp, title_simp)
        ch_num = name_to_num.get(title_simp)
        if ch_num is None:
            unmatched.append((title_trad, title_simp))
            continue

        content = tex.read_text(encoding='utf-8', errors='replace')
        title, paragraphs = parse_tex(content)

        lines = [f'# {ch_num:03d} {title_simp}（繁體原文）', '']
        lines.append(f'來源：點校本二十四史（中華書局），via Yann-Chen/Twenty-Four-Histories')
        lines.append(f'原文名：{title_trad}')
        lines.append('')
        lines.append('---')
        lines.append('')
        for p in paragraphs:
            lines.append(p)
            lines.append('')

        out_path = OUTPUT_DIR / f'{ch_num:03d}_{title_simp}_点校本.txt'
        out_path.write_text('\n'.join(lines), encoding='utf-8')
        matched += 1

    print(f'导入 {matched} 章 → {OUTPUT_DIR}')
    if unmatched:
        print(f'未匹配 {len(unmatched)} 章:')
        for t, s in unmatched:
            print(f'  {t} (简：{s})')


if __name__ == '__main__':
    main()
