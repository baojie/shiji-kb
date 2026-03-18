#!/usr/bin/env python3
"""
修复动词标注格式错误：将 ⟦TYPE动词⟧[动词〗 这种混合格式改为 ⟦TYPE动词⟧

错误模式：新格式动词标注后面跟着旧格式的残留部分
正确格式：只保留新格式 ⟦TYPE动词⟧
"""

import re
import sys
from pathlib import Path

def fix_mixed_verb_format(text):
    r"""
    修复混合的动词标注格式

    错误示例：⟦◉诛⟧[诛〗
    修复后：⟦◉诛⟧

    模式说明：
    - ⟦[◈◉○◇] - 新格式开始，后跟动词类型符号
    - ([^⟧]+) - 捕获动词内容（不含结束符）
    - ⟧ - 新格式结束
    - \[ - 旧格式残留开始
    - [^\〗]+ - 旧格式内容（通常是重复的动词）
    - 〗 - 旧格式结束
    """
    pattern = r'(⟦[◈◉○◇]([^⟧]+)⟧)\[([^\〗]+)〗'

    def replace_func(match):
        new_format = match.group(1)  # ⟦TYPE动词⟧
        verb = match.group(2)         # 动词
        old_verb = match.group(3)     # 旧格式中的动词（应该与verb相同）

        # 验证：旧格式中的动词应该与新格式中的相同
        if verb != old_verb:
            print(f"⚠️  警告：动词不匹配 - 新:{verb} vs 旧:{old_verb}", file=sys.stderr)

        return new_format

    result, count = re.subn(pattern, replace_func, text)
    return result, count

def process_file(file_path):
    """处理单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        fixed_content, count = fix_mixed_verb_format(content)

        if count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"✅ {file_path.name}: 修复 {count} 处")
            return count
        else:
            print(f"   {file_path.name}: 无需修复")
            return 0
    except Exception as e:
        print(f"❌ {file_path.name}: 错误 - {e}", file=sys.stderr)
        return 0

def main():
    if len(sys.argv) > 1:
        # 处理指定文件
        files = [Path(arg) for arg in sys.argv[1:]]
    else:
        # 处理所有tagged.md文件
        base_dir = Path(__file__).parent.parent.parent / 'chapter_md'
        files = sorted(base_dir.glob('*.tagged.md'))

    print(f"检查 {len(files)} 个文件...\n")

    total_fixes = 0
    files_fixed = 0

    for file_path in files:
        count = process_file(file_path)
        if count > 0:
            files_fixed += 1
            total_fixes += count

    print(f"\n{'='*60}")
    print(f"完成！")
    print(f"修复文件数: {files_fixed}/{len(files)}")
    print(f"修复总数: {total_fixes} 处")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
