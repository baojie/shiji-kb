#!/usr/bin/env python3
"""修正 045 韩世家：谥号 ;→@ 消歧 + 单字名消歧"""

import re

FILE = "chapter_md/045_韩世家.tagged.md"

SHIHO_MAP = {
    # 韩国君主谥号
    "〖;宣子〗": "〖@宣子|韩宣子〗",
    "〖;贞子〗": "〖@贞子|韩贞子〗",
    "〖;康子〗": "〖@康子|韩康子〗",
    "〖;武子〗": "〖@武子|韩武子〗",
    "〖;景侯〗": "〖@景侯|韩景侯〗",
    "〖;列侯〗": "〖@列侯|韩列侯〗",
    "〖;文侯〗": "〖@文侯|韩文侯〗",
    "〖;哀侯〗": "〖@哀侯|韩哀侯〗",
    "〖;懿侯〗": "〖@懿侯|韩懿侯〗",
    "〖;昭侯〗": "〖@昭侯|韩昭侯〗",
    "〖;宣惠王〗": "〖@宣惠王|韩宣惠王〗",
    "〖;襄王〗": "〖@襄王|韩襄王〗",
    "〖;釐王〗": "〖@釐王|韩釐王〗",
    "〖;桓惠王〗": "〖@桓惠王|韩桓惠王〗",
    "〖;王安〗": "〖@王安|韩王安〗",
    "〖;献子〗": "〖@献子|韩献子〗",
    "〖;简子〗": "〖@简子|韩简子〗",
    "〖;庄子〗": "〖@庄子|韩庄子〗",
    # 人名误标
    "〖;太子仓〗": "〖@太子仓〗",
    "〖;太子婴〗": "〖@太子婴〗",
    "〖;太子咎〗": "〖@太子咎〗",
    "〖;宣〗": "〖@宣|韩宣子〗",
    # 单字名
    "〖@宧〗": "〖@宧|韩宧〗",
}

def main():
    content = open(FILE, "r", encoding="utf-8").read()
    total = 0
    for old, new in SHIHO_MAP.items():
        if old in content:
            cnt = content.count(old)
            content = content.replace(old, new)
            print(f"  {old} → {new}  ({cnt}处)")
            total += cnt

    open(FILE, "w", encoding="utf-8").write(content)
    print(f"\n共 {total} 处替换")

    # 验证
    remaining_semi = []
    for m in re.finditer(r'〖;([^〗]+)〗', content):
        remaining_semi.append(m.group(1))
    from collections import Counter
    print("\n残留 〖;X〗:")
    for k, v in Counter(remaining_semi).most_common():
        print(f"  〖;{k}〗: {v}")

    remaining_single = re.findall(r'〖@(.)〗', content)
    if remaining_single:
        print(f"\n残留单字名: {Counter(remaining_single).most_common()}")
    else:
        print("\n单字名: 已全部消歧")

if __name__ == "__main__":
    main()
