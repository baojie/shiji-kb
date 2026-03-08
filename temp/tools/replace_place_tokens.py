#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replace place name tokens from # to = in markdown files"""

import re
import sys
from pathlib import Path


def replace_place_tokens(content):
    """Replace #地名# with =地名= while preserving markdown headings
    Also remove =地名= from headings"""

    # Split content into lines to process each line
    lines = content.split('\n')
    result_lines = []

    for line in lines:
        # Check if this is a markdown heading
        heading_match = re.match(r'^(#{1,6}\s+)', line)

        if heading_match:
            # This is a heading line
            # First replace #text# with =text= in case there are any
            line = re.sub(r'#([^#\n]+)#', r'=\1=', line)
            # Then remove =text= markers from headings
            line = re.sub(r'=([^=\n]+)=', r'\1', line)
            result_lines.append(line)
            continue

        # For non-heading lines, replace #text# with =text=
        line = re.sub(r'#([^#\n]+)#', r'=\1=', line)
        result_lines.append(line)

    return '\n'.join(result_lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python replace_place_tokens.py <file1> [file2] ...")
        sys.exit(1)

    for file_path in sys.argv[1:]:
        path = Path(file_path)

        if not path.exists():
            print(f"File not found: {file_path}")
            continue

        # Read content
        content = path.read_text(encoding='utf-8')

        # Replace tokens
        new_content = replace_place_tokens(content)

        # Write back
        path.write_text(new_content, encoding='utf-8')

        print(f"✓ Updated: {file_path}")


if __name__ == '__main__':
    main()
