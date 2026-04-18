#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从《汉书·地理志》提取郡名和县名。

输出两个集合：
  - KNOWN_COMMANDERIES: 所有郡/国/尹/内史
  - KNOWN_HAN_XIAN:     所有县

输入:  corpus/other/汉书.txt（需要包含地理志章节）
输出:  kg/entities/data/hanshu_dili.json
       {
         "commanderies": [name, ...],   # 排序
         "counties": [name, ...],
       }
"""

import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
HANSHU = _ROOT / 'corpus' / 'other' / '汉书.txt'
OUT = _ROOT / 'kg' / 'entities' / 'data' / 'hanshu_dili.json'

# 地理志节段标记
SEC_START = '卷二十八上'
SEC_END = '卷二十九'   # 下一卷开头


def load_dili_text():
    text = HANSHU.read_text(encoding='utf-8')
    # 取地理志正文（第一次出现的 "卷二十八上" 到 "卷二十九" 之间）
    # 注意目录里也有 "卷二十八上"，所以取第二次出现作为正文开始
    idx1 = text.find(SEC_START)
    idx2 = text.find(SEC_START, idx1 + 1)
    start = idx2 if idx2 != -1 else idx1
    end = text.find(SEC_END, start)
    if end == -1:
        end = len(text)
    body = text[start:end]
    # 去掉卷标题行和地理志标题行
    body = re.sub(r'^.*?地理志第八[上下]', '', body, count=2, flags=re.DOTALL).strip()
    return body


# 郡/国类型后缀（用于识别郡段起始）
JUN_TYPES = ['郡', '国', '尹', '内史', '冯翊', '扶风']

# 明确不是县名的描述性片段（补充黑名单）
DESC_TOKENS_BLACKLIST = {
    '户', '口', '王莽', '县', '无', '其', '又',
    '太华山', '集灵宫', '大华山', '龙门山', '禹贡',
    '薛山', '梁山', '周', '秦', '汉', '商', '莽',
    '故', '有', '属', '治', '都', '分', '自',
    '高祖', '高帝', '惠帝', '文帝', '景帝', '武帝',
    '昭帝', '宣帝', '元帝', '成帝', '哀帝', '平帝',
    '太守', '都尉', '县官',
}


# 郡首模式：出现在行首或 。 之后的 "XX郡，" / "XX国，" 等
# 需要区分："京兆尹"、"左冯翊"、"右扶风" 等特殊
JUN_PATTERN = re.compile(
    r'(?:^|(?<=。))'
    r'([\u4e00-\u9fa5]{1,5}?'
    r'(?:郡|国|尹|内史|冯翊|扶风)'
    r')，'
)


def normalize(text):
    """清理文本：替换全角空格、合并行内换行造成的断字。
    《汉书》原文可能在县条目中插入换行，合并后再解析。"""
    # 去除换行（地理志内部不应有段落换行）
    text = text.replace('\n', '').replace('\r', '')
    # 去除常见注记噪声
    return text


def extract(body):
    body = normalize(body)
    commanderies = []
    counties = []

    # 按郡段拆分：找到所有郡名起始位置
    starts = [(m.start(), m.group(1)) for m in JUN_PATTERN.finditer(body)]
    starts.append((len(body), None))  # sentinel

    for i, (pos, jun_name) in enumerate(starts[:-1]):
        next_pos = starts[i + 1][0]
        section = body[pos:next_pos]
        # 过滤掉明显不是郡名的片段（描述末尾误匹配）
        if jun_name:
            bad = (
                jun_name.startswith(('故', '虽', '其', '此', '以', '至', '本', '凡', '者'))
                or '至于' in jun_name
                or len(jun_name) > 5
            )
            if not bad:
                commanderies.append(jun_name)

        # 该郡的县列表：取 "县N：" 之后到段末
        m = re.search(r'县[一二三四五六七八九十百零两〇]+[：:]', section)
        if not m:
            continue
        tail = section[m.end():]

        # 县条目按 。 分隔；每条目第一个 ，前的 token 候选为县名
        for entry in tail.split('。'):
            entry = entry.strip()
            if not entry:
                continue
            # 取第一个 ，前的 token
            parts = re.split(r'[，,]', entry, maxsplit=1)
            token = parts[0].strip()
            # 过滤条件（力求高精度）：
            # 1) 长度 1-3（汉代县名多为单字或双字，少数三字如 新丰/下邳/临淄）
            # 2) 纯汉字
            # 3) 不含动词/介词（在/出/置/更/有/自/属/分）
            # 4) 不以描述性前缀起头
            if not (1 <= len(token) <= 3):
                continue
            if not re.fullmatch(r'[\u4e00-\u9fa5]+', token):
                continue
            # 剔除含"描述性动词/名词"的 token，但保留"都"（成都/阳都/临都 等含都地名）
            if re.search(r'[在出置更有自属分為为治曰与山水祠官]', token):
                continue
            if token in DESC_TOKENS_BLACKLIST:
                continue
            # 描述性前缀首字（单字以此判定会误伤过多，故仅排除完整匹配）
            counties.append(token)

    # 去重保序
    seen = set()
    uniq_jun = []
    for n in commanderies:
        if n not in seen:
            seen.add(n); uniq_jun.append(n)
    seen = set()
    uniq_xian = []
    for n in counties:
        if n not in seen:
            seen.add(n); uniq_xian.append(n)
    return uniq_jun, uniq_xian


def main():
    body = load_dili_text()
    print(f'地理志正文长度: {len(body)} 字符')
    jun, xian = extract(body)
    print(f'提取 郡/国/尹: {len(jun)}')
    print(f'提取 县:     {len(xian)}')
    print('郡样本:', jun[:20])
    print('县样本:', xian[:40])

    out = {
        'commanderies': sorted(jun),
        'counties': sorted(xian),
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'写入: {OUT}')


if __name__ == '__main__':
    main()
