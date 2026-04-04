#!/usr/bin/env python3
"""
批量为所有史记章节 HTML 文件添加配置面板
"""

import os
import re
from pathlib import Path

# HTML 代码片段
SETTINGS_HTML = '''<!-- 浮动配置按钮 -->
<button id="settings-toggle" title="显示设置">⚙️</button>

<!-- 配置面板 -->
<div id="settings-panel">
    <h3>显示设置</h3>

    <div class="setting-group">
        <label class="setting-item">
            <input type="checkbox" id="syntax-highlight" checked>
            <span>语法高亮</span>
        </label>
    </div>
</div>

'''

SCRIPT_TAG = '<script src="../js/settings-panel.js"></script>\n'


def add_settings_to_file(filepath):
    """为单个 HTML 文件添加配置面板"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经添加过
    if 'settings-toggle' in content:
        print(f"跳过（已存在配置面板）: {filepath.name}")
        return False

    # 在 <body> 标签后添加配置面板 HTML
    body_pattern = r'(<body>)'
    if not re.search(body_pattern, content):
        print(f"警告：未找到 <body> 标签: {filepath.name}")
        return False

    content = re.sub(body_pattern, r'\1\n' + SETTINGS_HTML, content, count=1)

    # 在 </body> 前添加 script 标签
    # 先检查是否已有 settings-panel.js
    if 'settings-panel.js' not in content:
        body_end_pattern = r'(</body>)'
        content = re.sub(body_end_pattern, SCRIPT_TAG + r'\1', content, count=1)

    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 已添加配置面板: {filepath.name}")
    return True


def main():
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    chapters_dir = project_root / 'docs' / 'chapters'

    if not chapters_dir.exists():
        print(f"错误：目录不存在 {chapters_dir}")
        return

    # 获取所有 HTML 文件
    html_files = sorted(chapters_dir.glob('*.html'))

    if not html_files:
        print("未找到 HTML 文件")
        return

    print(f"找到 {len(html_files)} 个 HTML 文件\n")

    # 处理每个文件
    success_count = 0
    skip_count = 0

    for filepath in html_files:
        if add_settings_to_file(filepath):
            success_count += 1
        else:
            skip_count += 1

    print(f"\n处理完成：")
    print(f"  成功添加: {success_count} 个文件")
    print(f"  跳过: {skip_count} 个文件")
    print(f"  总计: {len(html_files)} 个文件")


if __name__ == '__main__':
    main()
