#!/usr/bin/env python3
"""
修复058章的剩余标注问题
"""

import re

file_path = 'chapter_md/058_梁孝王世家.tagged.md'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 修复 韩安国 - 姓氏不应标注为地名
content = content.replace('〖=韩〗〖@安国〗', '〖@韩安国〗')

# 2. 修复 四十馀城 - 数量词应完整标注
content = content.replace('四〖$十馀城〗', '〖$四十馀城〗')

# 3. 修复 千乘万骑 - "千乘"不是地名，是数量
content = content.replace('〖=千乘〗〖$万骑〗', '〖$千乘万骑〗')

# 4. 修复 出言跸 - 应标注为礼仪用语
content = content.replace('出言跸', '出言〖:跸〗')

# 5. 统一 长公主 标注 - 全部改为人名消歧
content = content.replace('长〖;公主〗', '〖@长公主|窦太主〗')

# 6. 修复 亚夫 消歧
content = content.replace('〖@亚夫〗', '〖@亚夫|周亚夫〗')

# 7. 修复第88行的"幸臣" - 从职官改为身份
content = content.replace('其〖;幸臣〗〖@羊胜〗', '其〖#幸臣〗〖@羊胜〗')

# 8. 修复 袁将军 消歧
content = content.replace('〖;袁将军〗', '〖@袁将军|袁盎〗')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 修复完成：058_梁孝王世家.tagged.md")
print("  - 韩安国：姓氏标注修正")
print("  - 四十馀城：数量词完整标注")
print("  - 千乘万骑：统一为数量标注")
print("  - 出言跸：添加礼仪标注")
print("  - 长公主：统一消歧为窦太主")
print("  - 亚夫：消歧为周亚夫")
print("  - 幸臣：职官改为身份")
print("  - 袁将军：消歧为袁盎")
