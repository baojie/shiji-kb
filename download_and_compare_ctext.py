#!/usr/bin/env python3
"""
下载ctext.org版本的完整史记，并与现有版本进行校对比较
考虑繁简体差异
"""

import requests
import time
import re
from pathlib import Path
from bs4 import BeautifulSoup
import difflib
from collections import defaultdict

# 简化的繁简转换字典（常用字）
TRAD_TO_SIMP = str.maketrans({
    '國': '国', '華': '华', '門': '门', '開': '开', '長': '长',
    '書': '书', '後': '后', '東': '东', '車': '车', '來': '来',
    '樂': '乐', '業': '业', '衛': '卫', '兩': '两', '關': '关',
    '點': '点', '無': '无', '爲': '为', '韓': '韩', '際': '际',
    '從': '从', '歷': '历', '歲': '岁', '時': '时', '說': '说',
    '軍': '军', '將': '将', '發': '发', '應': '应', '領': '领',
    '員': '员', '準': '准', '則': '则', '總': '总', '擊': '击',
    '稱': '称', '與': '与', '經': '经', '雖': '虽', '過': '过',
    '運': '运', '還': '还', '進': '进', '遠': '远', '違': '违',
    '連': '连', '適': '适', '選': '选', '邊': '边', '達': '达',
    '過': '过', '這': '这', '進': '进', '遲': '迟', '運': '运',
    '道': '道', '遙': '遥', '遇': '遇', '遍': '遍', '邪': '邪',
})

# 史记130章的URL slug映射
# 从ctext.org获取实际的URL
CHAPTER_MAPPING = {
    # 本纪
    "001_五帝本纪": "wu-di-ben-ji",
    "002_夏本纪": "xia-ben-ji",
    "003_殷本纪": "yin-ben-ji",
    "004_周本纪": "zhou-ben-ji",
    "005_秦本纪": "qin-ben-ji",
    "006_秦始皇本纪": "qin-shi-huang-ben-ji",
    "007_项羽本纪": "xiang-yu-ben-ji",
    "008_高祖本纪": "gao-zu-ben-ji",
    "009_吕太后本纪": "lu-tai-hou-ben-ji",
    "010_孝文本纪": "xiao-wen-ben-ji",
    "011_孝景本纪": "xiao-jing-ben-ji",
    "012_孝武本纪": "xiao-wu-ben-ji",
    # 表
    "013_三代世表": "san-dai-shi-biao",
    "014_十二诸侯年表": "shi-er-zhu-hou-nian-biao",
    "015_六国年表": "liu-guo-nian-biao",
    "016_秦楚之际月表": "qin-chu-zhi-ji-yue-biao",
    "017_汉兴以来诸侯王年表": "han-xing-yi-lai-zhu-hou",
    "018_高祖功臣侯者年表": "gao-zu-gong-chen-hou-zhe",
    "019_惠景间侯者年表": "hui-jing-xian-hou-zhe-nian-biao",
    "020_建元以来侯者年表": "jian-yuan-yi-lai-hou-zhe",
    "021_建元已来王子侯者年表": "jian-yuan-yi-lai-wang-zi",
    "022_汉兴以来将相名臣年表": "han-xing-yi-lai-jiang-xiang",
    # 书
    "023_礼书": "li-shu",
    "024_乐书": "yue-shu",
    "025_律书": "lv-shu1",
    "026_历书": "li-shu1",
    "027_天官书": "tian-guan-shu",
    "028_封禅书": "feng-shan-shu",
    "029_河渠书": "he-qu-shu",
    "030_平准书": "ping-zhun-shu",
}

def fetch_chapter_from_ctext(chapter_name, url_slug, output_dir):
    """从ctext.org下载单个章节"""
    url = f"https://ctext.org/shiji/{url_slug}/zh"
    output_file = output_dir / f"{chapter_name}_ctext.txt"

    try:
        print(f"下载: {chapter_name}...", end=" ")

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
            print("✗ 无法找到内容")
            return False

        # 移除script和style标签
        for script in content_div(['script', 'style', 'nav']):
            script.decompose()

        # 获取文本
        text = content_div.get_text(separator='\n', strip=True)

        # 清理多余的空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)

        print(f"✓ ({len(text)} 字)")
        return True

    except Exception as e:
        print(f"✗ {e}")
        return False

def compare_texts(original_file, ctext_file, output_file):
    """比较两个版本的文本，生成差异报告"""

    try:
        # 读取原始版本
        with open(original_file, 'r', encoding='utf-8') as f:
            original_text = f.read()

        # 读取ctext版本
        with open(ctext_file, 'r', encoding='utf-8') as f:
            ctext_text = f.read()

        # 将ctext版本(繁体)转为简体（使用自定义字典）
        ctext_simplified = ctext_text.translate(TRAD_TO_SIMP)

        # 分行比较
        original_lines = original_text.splitlines()
        ctext_lines = ctext_simplified.splitlines()

        # 生成差异
        diff = list(difflib.unified_diff(
            original_lines,
            ctext_lines,
            fromfile='原始版本',
            tofile='ctext版本（转简体后）',
            lineterm=''
        ))

        if len(diff) > 2:  # 有差异（除了头两行标识）
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(diff))
            return True, len(diff) - 2
        else:
            return False, 0

    except Exception as e:
        print(f"  比较出错: {e}")
        return False, -1

def main():
    """主函数"""

    # 设置目录
    ctext_dir = Path('/home/baojie/work/shiji-kb/resources/ctext版本')
    original_dir = Path('/home/baojie/work/shiji-kb/docs/original_text')
    diff_dir = Path('/home/baojie/work/shiji-kb/resources/差异报告')

    ctext_dir.mkdir(parents=True, exist_ok=True)
    diff_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("开始下载ctext.org版本的史记并进行校对")
    print("=" * 70)
    print()

    # 下载章节
    print("【阶段1】下载ctext.org版本")
    print("-" * 70)

    success_count = 0
    for chapter_name, url_slug in CHAPTER_MAPPING.items():
        if fetch_chapter_from_ctext(chapter_name, url_slug, ctext_dir):
            success_count += 1
        time.sleep(1)  # 避免请求过快

    print(f"\n下载完成：{success_count}/{len(CHAPTER_MAPPING)} 个章节")
    print()

    # 比较版本
    print("【阶段2】比较版本差异")
    print("-" * 70)

    diff_stats = defaultdict(int)

    for chapter_name in CHAPTER_MAPPING.keys():
        original_file = original_dir / f"{chapter_name}.txt"
        ctext_file = ctext_dir / f"{chapter_name}_ctext.txt"
        diff_file = diff_dir / f"{chapter_name}_diff.txt"

        if not original_file.exists():
            print(f"{chapter_name}: 原始文件不存在")
            diff_stats['缺失'] += 1
            continue

        if not ctext_file.exists():
            print(f"{chapter_name}: ctext文件下载失败")
            diff_stats['下载失败'] += 1
            continue

        has_diff, diff_count = compare_texts(original_file, ctext_file, diff_file)

        if diff_count == -1:
            print(f"{chapter_name}: 比较失败")
            diff_stats['比较失败'] += 1
        elif has_diff:
            print(f"{chapter_name}: 有差异 ({diff_count} 处)")
            diff_stats['有差异'] += 1
        else:
            print(f"{chapter_name}: 完全一致")
            diff_stats['一致'] += 1
            # 删除空的差异文件
            if diff_file.exists():
                diff_file.unlink()

    print()
    print("=" * 70)
    print("校对完成！统计结果：")
    print("-" * 70)
    for status, count in sorted(diff_stats.items()):
        print(f"  {status}: {count} 个")
    print("=" * 70)
    print(f"\n差异报告保存在: {diff_dir}")

if __name__ == '__main__':
    main()
