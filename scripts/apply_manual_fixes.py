#!/usr/bin/env python3
"""
对剩余未定位的成语应用手动修正
"""

import json
from pathlib import Path

# 手动定位的成语修正
# 格式: "成语名": (正确章节号, 正确章节名, 段落号)
MANUAL_FIXES = {
    "焚书坑儒": ("006", "秦始皇本纪", "64.3"),
    "易子而食，析骨而炊": ("038", "宋微子世家", "34.46"),
    "唇亡齿寒": ("039", "晋世家", "30.33"),  # 原记录043赵世家有误
    "当断不断，反受其乱": ("052", "齐悼惠王世家", "10"),  # 原记录046有误
    "以貌取人": ("067", "仲尼弟子列传", "63"),  # 原记录047孔子世家有误
    "重足而立，侧目而视": ("120", "汲郑列传", "5"),  # 原记录122酷吏列传有误
    "过犹不及": ("067", "仲尼弟子列传", "52"),  # 原记录047孔子世家有误
}

def main():
    project_root = Path(__file__).parent.parent
    json_file = project_root / "data/chengyu.json"
    chapter_dir = project_root / "chapter_md"

    # 读取JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 应用手动修正
    fixed_count = 0
    for item in data:
        chengyu = item['chengyu']

        if chengyu in MANUAL_FIXES:
            correct_chapter_num, correct_chapter_title, paragraph = MANUAL_FIXES[chengyu]

            # 更新章节信息（如果有误）
            item['chapter_num'] = correct_chapter_num
            item['chapter_title'] = correct_chapter_title

            # 读取对应章节
            chapter_file = chapter_dir / f"{correct_chapter_num}_{correct_chapter_title}.tagged.md"

            if not chapter_file.exists():
                print(f"⚠️  {chengyu}: 章节文件不存在 {chapter_file}")
                continue

            content = chapter_file.read_text(encoding='utf-8')

            # 查找段落
            para_pattern = f"[{paragraph}]"
            if para_pattern in content:
                # 提取上下文
                pos = content.index(para_pattern)
                start = max(0, pos - 100)
                end = min(len(content), pos + 300)
                context = content[start:end]

                item['paragraph'] = paragraph
                item['context'] = context.strip()
                fixed_count += 1
                print(f"✓ {chengyu}: {correct_chapter_num}_{correct_chapter_title} [{paragraph}]")
            else:
                print(f"⚠️  {chengyu}: 未找到段落 {paragraph}")

    # 保存更新后的JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 共修正 {fixed_count} 条成语")

    # 统计定位率
    located = sum(1 for x in data if x['paragraph'])
    total = len(data)
    print(f"定位率: {located}/{total} ({located*100//total}%)")

if __name__ == "__main__":
    main()
