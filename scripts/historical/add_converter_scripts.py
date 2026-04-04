#!/usr/bin/env python3
"""
为所有HTML文件添加繁简转换相关的脚本引用

添加内容：
1. 在 <head> 中添加 OpenCC.js CDN
2. 在 </body> 前添加 simp-trad-converter.js 引用
"""

import re
from pathlib import Path


# OpenCC.js CDN 引用（在 <head> 中添加）
OPENCC_CDN = '    <script src="https://cdn.jsdelivr.net/npm/opencc-js@1.0.5/dist/umd/full.min.js"></script>\n'

# 繁简转换器引用（在 </body> 前添加）
CONVERTER_SCRIPT = '<script src="../js/simp-trad-converter.js"></script>\n'


def add_scripts_to_file(filepath):
    """为单个 HTML 文件添加脚本引用"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    modified = False

    # 1. 检查并添加 OpenCC.js CDN（在 </head> 前）
    if 'opencc-js' not in content:
        # 在 </head> 前插入
        head_end_pattern = r'(</head>)'
        if re.search(head_end_pattern, content):
            content = re.sub(head_end_pattern, OPENCC_CDN + r'\1', content, count=1)
            modified = True
            print(f"  ✓ 添加 OpenCC.js CDN: {filepath.name}")
        else:
            print(f"  ⚠ 未找到 </head> 标签: {filepath.name}")

    # 2. 检查并添加繁简转换器脚本（在 settings-panel-config.js 之前）
    if 'simp-trad-converter.js' not in content:
        # 在 settings-panel-config.js 之前插入
        settings_pattern = r'(<script src="../js/settings-panel-config\.js"></script>)'
        if re.search(settings_pattern, content):
            content = re.sub(settings_pattern, CONVERTER_SCRIPT + r'\1', content, count=1)
            modified = True
            print(f"  ✓ 添加繁简转换器: {filepath.name}")
        else:
            # 如果没有 settings-panel-config.js，在 </body> 前插入
            body_end_pattern = r'(</body>)'
            if re.search(body_end_pattern, content):
                content = re.sub(body_end_pattern, CONVERTER_SCRIPT + r'\1', content, count=1)
                modified = True
                print(f"  ✓ 添加繁简转换器（在 </body> 前）: {filepath.name}")

    # 写回文件
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    else:
        print(f"  - 跳过（已存在脚本引用）: {filepath.name}")
        return False


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    chapters_dir = project_root / 'docs' / 'chapters'

    if not chapters_dir.exists():
        print(f"错误：目录不存在 {chapters_dir}")
        return

    # 获取所有 HTML 文件（排除 index.html）
    html_files = sorted([f for f in chapters_dir.glob('*.html') if f.name != 'index.html'])

    if not html_files:
        print("未找到 HTML 文件")
        return

    print(f"找到 {len(html_files)} 个 HTML 文件\n")

    # 处理每个文件
    success_count = 0

    for filepath in html_files:
        if add_scripts_to_file(filepath):
            success_count += 1

    print(f"\n处理完成：")
    print(f"  修改文件: {success_count} 个")
    print(f"  总计: {len(html_files)} 个文件")


if __name__ == '__main__':
    main()
