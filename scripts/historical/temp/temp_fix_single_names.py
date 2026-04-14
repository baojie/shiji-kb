#!/usr/bin/env python3
"""
补充修复058章的单字名消歧
"""

import re

file_path = 'chapter_md/058_梁孝王世家.tagged.md'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 单字名消歧规则
# 注意：需要排除一些特殊情况，避免误替换

# 1. 武 → 刘武（梁孝王）
content = re.sub(r'次子〖@武〗', '次子〖@武|刘武〗', content)
content = re.sub(r'以〖@武〗为', '以〖@武|刘武〗为', content)
content = re.sub(r'〖;王〗〖@武〗为', '〖;王〗〖@武|刘武〗为', content)
content = re.sub(r'初，〖@武〗为', '初，〖@武|刘武〗为', content)

# 2. 参 → 刘参（代孝王）
content = content.replace('次子〖@参〗', '次子〖@参|刘参〗')
content = content.replace('以〖@参〗为', '以〖@参|刘参〗为')
content = content.replace('。〖@参〗立', '。〖@参|刘参〗立')

# 3. 胜 → 刘胜（梁怀王）
content = content.replace('次子〖@胜〗', '次子〖@胜|刘胜〗')
content = content.replace('以〖@胜〗为', '以〖@胜|刘胜〗为')
content = content.replace('王〖@胜〗卒', '王〖@胜|刘胜〗卒')
# 注意：第33行的"〖@胜〗"是指"羊胜"，不是刘胜，需要保留
content = content.replace('王乃令〖@胜〗、', '王乃令〖@胜|羊胜〗、')

# 4. 登 → 刘登（代共王）
content = content.replace('子〖@登〗嗣立', '子〖@登|刘登〗嗣立')

# 5. 义 → 刘义（代王）
content = content.replace('子〖@义〗立', '子〖@义|刘义〗立')

# 6. 买 → 刘买（梁共王）
content = content.replace('长子〖@买〗为', '长子〖@买|刘买〗为')

# 7. 明 → 刘明（济川王）
content = content.replace('子〖@明〗为', '子〖@明|刘明〗为')
content = content.replace('〖;王〗〖@明〗者', '〖;王〗〖@明|刘明〗者')
content = content.replace('⟦◉废⟧〖@明〗为', '⟦◉废⟧〖@明|刘明〗为')

# 8. 彭离 → 刘彭离（济东王）
content = content.replace('子〖@彭离〗为', '子〖@彭离|刘彭离〗为')
# 第61行的〖@彭离〗已经正确

# 9. 定 → 刘定（山阳哀王）
content = content.replace('子〖@定〗为', '子〖@定|刘定〗为')
content = content.replace('〖@山阳哀王〗〖@定〗者', '〖@山阳哀王〗〖@定|刘定〗者')

# 10. 不识 → 刘不识（济阴哀王）
content = content.replace('子〖@不识〗为', '子〖@不识|刘不识〗为')
content = content.replace('〖@济阴哀王〗〖@不识〗者', '〖@济阴哀王〗〖@不识|刘不识〗者')

# 11. 襄 → 刘襄（梁平王）
content = content.replace('子〖@襄〗立', '子〖@襄|刘襄〗立')
content = content.replace('〖@梁平王〗〖@襄〗〖%十四年〗', '〖@梁平王〗〖@襄|刘襄〗〖%十四年〗')
content = content.replace('〖@平王|梁平王〗〖@襄〗', '〖@平王|梁平王〗〖@襄|刘襄〗')
content = content.replace('〖[请废〗〖@襄〗为', '〖[请废〗〖@襄|刘襄〗为')
content = content.replace('〖@梁王|梁平王〗〖@襄〗', '〖@梁王|梁平王〗〖@襄|刘襄〗')
content = content.replace('。〖@襄〗立', '。〖@襄|刘襄〗立')

# 12. 无伤 → 刘无伤
content = content.replace('子〖@无伤〗立为', '子〖@无伤|刘无伤〗立为')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 单字名消歧修复完成")
print("  - 武 → 刘武")
print("  - 参 → 刘参")
print("  - 胜 → 刘胜/羊胜（区分上下文）")
print("  - 登 → 刘登")
print("  - 义 → 刘义")
print("  - 买 → 刘买")
print("  - 明 → 刘明")
print("  - 彭离 → 刘彭离")
print("  - 定 → 刘定")
print("  - 不识 → 刘不识")
print("  - 襄 → 刘襄")
print("  - 无伤 → 刘无伤")
