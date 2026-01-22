#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small semantic tagger that builds gazetteers from existing HTML spans
and applies token-wrapping to a source Markdown file.

Usage:
  python3 tools/semantic_tagger.py --source chapter_md/002_夏本纪.md --htmls chapter_md/*.simple.html --out chapter_md/002_夏本纪.simple.md

The script is conservative: it matches whole-name occurrences (not inside other Han characters)
and replaces longer names first to avoid partial overlaps.
"""

import re
import sys
import glob
import argparse
from pathlib import Path


CLASS_TO_TOKEN = {
    'person': ('@', '@'),
    'place': ('=', '='),
    'official': ('$', '$'),
    'time': ('%', '%'),
    'dynasty': ('&', '&'),
    'institution': ('^', '^'),
    'tribe': ('~', '~'),
    'artifact': ('*', '*'),
    'astronomy': ('!', '!'),
    'mythical': ('?', '?'),
}


def extract_gazetteers(html_paths):
    gaz = {k: set() for k in CLASS_TO_TOKEN.keys()}
    span_re = re.compile(r'<span[^>]*class="([^"]+)"[^>]*>([^<]+)</span>')
    for path in html_paths:
        try:
            text = Path(path).read_text(encoding='utf-8')
        except Exception:
            continue
        for m in span_re.finditer(text):
            cls = m.group(1).split()[0]
            val = m.group(2).strip()
            if cls in gaz and val:
                gaz[cls].add(val)
    return gaz


def tag_text(content, gazetteers):
    # Build list of (name, token_start, token_end)
    entries = []
    for cls, names in gazetteers.items():
        token = CLASS_TO_TOKEN.get(cls)
        if not token:
            continue
        for name in names:
            entries.append((name, token[0], token[1], cls))

    # sort by name length desc to avoid partial overlap
    entries.sort(key=lambda e: len(e[0]), reverse=True)

    def make_safe_pattern(name):
        # Match the name when not surrounded by other Han characters (avoid mid-word replacement)
        return re.compile(rf'(?<![\u4e00-\u9fff])({re.escape(name)})(?![\u4e00-\u9fff])')

    # Avoid re-wrapping already tokenized text: we will skip matches that are adjacent to token chars
    token_chars = ''.join(set([c for pair in CLASS_TO_TOKEN.values() for c in pair]))

    for name, start_t, end_t, cls in entries:
        pat = make_safe_pattern(name)

        def repl(m):
            s = m.group(1)
            # check surrounding chars in content to avoid replacing inside existing tokens
            i = m.start(1)
            j = m.end(1)
            left = content[i-1] if i-1 >= 0 else ''
            right = content[j] if j < len(content) else ''
            if left in token_chars or right in token_chars:
                return s
            return f'{start_t}{s}{end_t}'

        content = pat.sub(repl, content)

    return content


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True)
    p.add_argument('--htmls', nargs='+', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()

    htmls = []
    for g in args.htmls:
        htmls.extend(glob.glob(g))

    gaz = extract_gazetteers(htmls)

    # read source
    src = Path(args.source)
    if not src.exists():
        print('source not found:', args.source)
        sys.exit(1)
    content = src.read_text(encoding='utf-8')

    tagged = tag_text(content, gaz)

    outp = Path(args.out)
    outp.write_text(tagged, encoding='utf-8')
    print('Tagged:', args.source, '->', str(outp))


if __name__ == '__main__':
    main()
