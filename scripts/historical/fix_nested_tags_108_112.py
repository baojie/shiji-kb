#!/usr/bin/env python3
"""
修复108-112章嵌套标注问题
〖#〖#兄〗弟〗 → 〖#兄弟〗
〖=〖~马〗邑〗 → 〖=马邑〗
〖;〖~车〗骑将军〗 → 〖;车骑将军〗
"""

import re
import shutil
from pathlib import Path
from datetime import datetime

WORK_DIR = Path("/home/baojie/work/shiji-kb")
CHAPTER_DIR = WORK_DIR / "chapter_md"

CHAPTERS = [
    ("108", "韩长孺列传"),
    ("109", "李将军列传"),
    ("110", "匈奴列传"),
    ("111", "卫将军骠骑列传"),
    ("112", "平津侯主父列传"),
]

def fix_nested_tags(text):
    """修复嵌套标注"""
    # 记录修改
    fixes = []

    # 模式1: 〖X〖X内容〗外〗 → 〖X内容外〗
    # 例如: 〖#〖#兄〗弟〗 → 〖#兄弟〗
    pattern1 = r'〖([^〗〖]+)〖\1([^〗]+)〗([^〗]*)〗'

    def replace1(match):
        marker = match.group(1)
        inner = match.group(2)
        outer = match.group(3)
        original = match.group(0)
        fixed = f'〖{marker}{inner}{outer}〗'
        fixes.append((original, fixed, '同类标记嵌套'))
        return fixed

    text = re.sub(pattern1, replace1, text)

    # 模式2: 〖X〖Y内容〗外〗 → 〖X内容外〗
    # 例如: 〖=〖~马〗邑〗 → 〖=马邑〗
    pattern2 = r'〖([^〗〖]+)〖[^〗〖]+([^〗]+)〗([^〗]*)〗'

    def replace2(match):
        outer_marker = match.group(1)
        inner_content = match.group(2)
        tail = match.group(3)
        original = match.group(0)
        fixed = f'〖{outer_marker}{inner_content}{tail}〗'
        fixes.append((original, fixed, '异类标记嵌套'))
        return fixed

    text = re.sub(pattern2, replace2, text)

    return text, fixes

def process_chapter(chapter_num, chapter_name):
    """处理单个章节"""
    filepath = CHAPTER_DIR / f"{chapter_num}_{chapter_name}.tagged.md"

    if not filepath.exists():
        print(f"文件不存在: {filepath}")
        return []

    # 读取
    with open(filepath, 'r', encoding='utf-8') as f:
        original_text = f.read()

    # 修复
    fixed_text, fixes = fix_nested_tags(original_text)

    if not fixes:
        print(f"{chapter_num}_{chapter_name}: 无嵌套标注")
        return []

    # 备份
    backup_path = filepath.with_suffix(filepath.suffix + f".nested_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(filepath, backup_path)
    print(f"已备份: {backup_path.name}")

    # 写回
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed_text)

    print(f"{chapter_num}_{chapter_name}: 修复 {len(fixes)} 处嵌套标注")

    for original, fixed, reason in fixes[:5]:  # 仅显示前5个
        print(f"  - {reason}: {original} → {fixed}")

    if len(fixes) > 5:
        print(f"  ... 还有 {len(fixes) - 5} 处修复")

    return fixes

def main():
    """主函数"""
    print("=" * 70)
    print("修复108-112章嵌套标注")
    print("=" * 70)

    total_fixes = []
    for chapter_num, chapter_name in CHAPTERS:
        fixes = process_chapter(chapter_num, chapter_name)
        total_fixes.extend(fixes)

    print("=" * 70)
    print(f"总计修复: {len(total_fixes)} 处嵌套标注")
    print("=" * 70)

if __name__ == "__main__":
    main()
