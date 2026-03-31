#!/usr/bin/env python3
"""
将HTML文件中的多个script引用替换为统一的 shiji-imports.js

清理：
1. OpenCC.js CDN
2. purple-numbers.js
3. heading-pinyin.js
4. simp-trad-converter.js
5. settings-panel-config.js

替换为：
- shiji-imports.js（在</head>前）
"""

import re
from pathlib import Path


# 需要移除的脚本引用模式
SCRIPTS_TO_REMOVE = [
    r'<script src="https://cdn\.jsdelivr\.net/npm/opencc-js.*?"></script>\s*',
    r'<script src="\.\./js/purple-numbers\.js"></script>\s*',
    r'<script\s+defer\s+src="\.\./js/heading-pinyin\.js"></script>\s*',
    r'<script src="\.\./js/simp-trad-converter\.js"></script>\s*',
    r'<script src="\.\./js/settings-panel-config\.js"></script>\s*',
]

# 统一导入模块引用
UNIFIED_IMPORT = '    <script src="../js/shiji-imports.js"></script>\n'


def clean_and_replace(filepath):
    """清理旧引用并替换为统一导入"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    modified = False

    # 1. 移除所有旧的脚本引用
    for pattern in SCRIPTS_TO_REMOVE:
        if re.search(pattern, content):
            content = re.sub(pattern, '', content)
            modified = True

    # 2. 检查是否已有 shiji-imports.js
    if 'shiji-imports.js' in content:
        print(f"  - 跳过（已有统一导入）: {filepath.name}")
        if modified:
            # 虽然已有统一导入，但仍然移除了冗余引用
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"    （已清理冗余引用）")
        return False

    # 3. 在 </head> 前添加统一导入
    head_end_pattern = r'(</head>)'
    if re.search(head_end_pattern, content):
        content = re.sub(head_end_pattern, UNIFIED_IMPORT + r'\1', content, count=1)
        modified = True
        print(f"  ✓ 替换为统一导入: {filepath.name}")
    else:
        print(f"  ⚠ 未找到 </head> 标签: {filepath.name}")
        return False

    # 写回文件
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    else:
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
        if clean_and_replace(filepath):
            success_count += 1

    print(f"\n处理完成：")
    print(f"  修改文件: {success_count} 个")
    print(f"  总计: {len(html_files)} 个文件")


if __name__ == '__main__':
    main()
