#!/usr/bin/env python3
"""
从ctext.org下载史记十表的完整内容
"""

import requests
import time
from pathlib import Path
from bs4 import BeautifulSoup

# 十表的URL和文件名映射
TABLES = [
    ("san-dai-shi-biao", "013_三代世表"),
    ("shi-er-zhu-hou-nian-biao", "014_十二诸侯年表"),
    ("liu-guo-nian-biao", "015_六国年表"),
    ("qin-chu-zhi-ji-yue-biao", "016_秦楚之际月表"),
    ("han-xing-yi-lai-zhu-hou", "017_汉兴以来诸侯王年表"),
    ("gao-zu-gong-chen-hou-zhe", "018_高祖功臣侯者年表"),
    ("hui-jing-xian-hou-zhe-nian-biao", "019_惠景间侯者年表"),
    ("jian-yuan-yi-lai-hou-zhe", "020_建元以来侯者年表"),
    ("jian-yuan-yi-lai-wang-zi", "021_建元已来王子侯者年表"),
    ("han-xing-yi-lai-jiang-xiang", "022_汉兴以来将相名臣年表"),
]

def fetch_table_from_ctext(url_slug, output_file):
    """从ctext.org获取表的内容"""
    url = f"https://ctext.org/shiji/{url_slug}/zh"

    try:
        print(f"正在获取: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找主要内容区域
        content_div = soup.find('div', {'id': 'content3'})
        if not content_div:
            content_div = soup.find('div', class_='main')
        if not content_div:
            content_div = soup.find('body')

        if not content_div:
            print(f"  ✗ 无法找到内容区域")
            return False

        # 提取文本内容
        # 移除script和style标签
        for script in content_div(['script', 'style']):
            script.decompose()

        # 获取文本
        text = content_div.get_text(separator='\n', strip=True)

        # 清理多余的空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)

        print(f"  ✓ 已保存: {output_file}")
        print(f"  内容长度: {len(text)} 字符")
        return True

    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False

def main():
    """主函数"""
    output_dir = Path('/home/baojie/work/shiji-kb/resources/十表原始数据')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("开始下载史记十表完整内容")
    print("=" * 60)

    success_count = 0

    for url_slug, filename in TABLES:
        output_file = output_dir / f"{filename}_ctext.txt"

        if fetch_table_from_ctext(url_slug, output_file):
            success_count += 1

        # 避免请求过快
        time.sleep(2)
        print()

    print("=" * 60)
    print(f"完成！成功下载 {success_count}/{len(TABLES)} 个表")
    print("=" * 60)

if __name__ == '__main__':
    main()
