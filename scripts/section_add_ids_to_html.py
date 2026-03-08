#!/usr/bin/env python3
"""
给HTML文件中的h2和h3标签添加id属性，便于锚点链接
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
import unicodedata

def slugify(text):
    """将中文文本转换为合适的URL slug"""
    # 移除特殊字符，只保留中文、字母、数字
    text = re.sub(r'[^\w\s-]', '', text)
    # 替换空格为短横线
    text = re.sub(r'[-\s]+', '-', text)
    # 转为小写并去掉首尾空格
    text = text.strip().lower()
    # 限制长度
    return text[:50]

def add_ids_to_headings(html_file):
    """给HTML文件中的h2和h3标签添加id"""

    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')

        # 找到所有h2和h3标签
        modified = False
        section_counter = {}  # 用于避免重复id

        for tag in soup.find_all(['h2', 'h3']):
            # 如果已经有id，跳过
            if tag.get('id'):
                continue

            # 获取文本内容
            text = tag.get_text(strip=True)
            if not text:
                continue

            # 生成id
            base_id = f"section-{slugify(text)}"

            # 处理重复id
            if base_id in section_counter:
                section_counter[base_id] += 1
                section_id = f"{base_id}-{section_counter[base_id]}"
            else:
                section_counter[base_id] = 0
                section_id = base_id

            # 添加id属性
            tag['id'] = section_id
            modified = True

        if modified:
            # 写回文件
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            print(f"✓ 已更新 {html_file.name}")
            return True
        else:
            print(f"- {html_file.name} 无需更新")
            return False

    except Exception as e:
        print(f"✗ 处理 {html_file} 时出错: {e}")
        return False

def process_all_html_files(chapters_dir):
    """处理目录中的所有HTML文件"""
    html_files = sorted(Path(chapters_dir).glob('*.tagged.html'))

    if not html_files:
        print("未找到HTML文件")
        return

    updated_count = 0
    for html_file in html_files:
        if add_ids_to_headings(html_file):
            updated_count += 1

    print(f"\n处理完成：共更新 {updated_count}/{len(html_files)} 个文件")

if __name__ == '__main__':
    chapters_dir = '/home/baojie/work/shiji-kb/docs/chapters'
    process_all_html_files(chapters_dir)
