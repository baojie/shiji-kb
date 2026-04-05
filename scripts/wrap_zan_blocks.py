#!/usr/bin/env python3
"""
为17篇新发现的赞添加 ::: 赞 区块标记

策略：
1. 找到赞标题（## 赞、## 赞诗、## 太史公赞等）
2. 找到赞内容的开始（第一个段落编号[N]）
3. 找到赞内容的结束（下一个## 标题或文件末尾）
4. 在赞内容前后添加 ::: 赞 和 :::
"""

import re
from pathlib import Path


def wrap_zan_block(chapter_file):
    """
    为章节文件的赞内容添加 ::: 赞 包裹

    返回：是否进行了修改
    """
    with open(chapter_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 查找赞标题的位置
    zan_title_pattern = re.compile(r'^## .*赞')
    zan_title_pos = -1

    for i, line in enumerate(lines):
        if zan_title_pattern.match(line):
            zan_title_pos = i
            break

    if zan_title_pos == -1:
        return False, "未找到赞标题"

    # 检查是否已经有 ::: 标记
    # 向后查找5行内是否有 :::
    for i in range(zan_title_pos + 1, min(zan_title_pos + 6, len(lines))):
        if lines[i].strip().startswith(':::'):
            return False, "已有::: 标记"

    # 查找赞内容的开始位置（第一个段落编号）
    zan_start_pos = -1
    for i in range(zan_title_pos + 1, min(zan_title_pos + 10, len(lines))):
        if re.match(r'^\[\d+', lines[i].strip()):
            zan_start_pos = i
            break

    if zan_start_pos == -1:
        return False, "未找到赞内容起始段落"

    # 查找赞内容的结束位置
    # 规则：遇到下一个 ## 标题或文件末尾
    zan_end_pos = len(lines)
    for i in range(zan_start_pos + 1, len(lines)):
        line = lines[i].strip()
        if line.startswith('##'):
            zan_end_pos = i
            break

    # 向前查找最后一个非空行
    while zan_end_pos > zan_start_pos and not lines[zan_end_pos - 1].strip():
        zan_end_pos -= 1

    # 插入 ::: 赞 标记
    # 在赞标题后插入空行和 ::: 赞
    lines.insert(zan_title_pos + 1, '\n')
    lines.insert(zan_title_pos + 2, '::: 赞\n')
    lines.insert(zan_title_pos + 3, '\n')

    # 在赞内容后插入 ::: 和空行（注意索引已经偏移了3）
    zan_end_pos += 3
    lines.insert(zan_end_pos, '\n')
    lines.insert(zan_end_pos + 1, ':::\n')

    # 写回文件
    with open(chapter_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return True, f"已添加 ::: 赞 标记（标题行{zan_title_pos+1}，内容行{zan_start_pos+1}-{zan_end_pos-3}）"


def main():
    """处理所有需要添加赞标记的章节"""

    chapters = {
        '019': '惠景间侯者年表',
        '033': '鲁周公世家',
        '034': '燕召公世家',
        '085': '吕不韦列传',
        # '088': '蒙恬列传',  # 已有标记，跳过
        '102': '张释之冯唐列传',
        '103': '万石张叔列传',
        '104': '田叔列传',
        '105': '扁鹊仓公列传',
        '106': '吴王濞列传',
        '107': '魏其武安侯列传',
        '108': '韩长孺列传',
        '109': '李将军列传',
        '125': '佞幸列传',
        '126': '滑稽列传',
        '128': '龟策列传',
        '130': '太史公自序'
    }

    project_root = Path(__file__).parent.parent
    chapter_dir = project_root / "chapter_md"

    success_count = 0
    skip_count = 0
    error_count = 0

    for chapter_num, chapter_title in chapters.items():
        # 查找章节文件
        chapter_files = list(chapter_dir.glob(f"{chapter_num}_*.tagged.md"))
        if not chapter_files:
            print(f"⚠ 跳过 {chapter_num}: 找不到文件")
            error_count += 1
            continue

        chapter_file = chapter_files[0]

        # 处理
        success, message = wrap_zan_block(chapter_file)

        if success:
            print(f"✓ {chapter_num} {chapter_title}: {message}")
            success_count += 1
        else:
            print(f"⊙ {chapter_num} {chapter_title}: {message}")
            skip_count += 1

    print(f"\n{'='*60}")
    print(f"处理完成:")
    print(f"  成功: {success_count} 篇")
    print(f"  跳过: {skip_count} 篇")
    print(f"  错误: {error_count} 篇")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
