#!/usr/bin/env python3
"""
史记成语典故提取批处理脚本

从已标注的 chapter_md/*.tagged.md 文件中提取成语、典故及经典名句，
输出结构化的成语索引到 kg/ 目录。

使用方法:
    python3 scripts/extract_idioms.py                # 处理所有章节
    python3 scripts/extract_idioms.py 001 002 003    # 只处理指定章节
    python3 scripts/extract_idioms.py --group 本纪    # 按章节分类处理
    python3 scripts/extract_idioms.py --dry-run       # 预览将处理的章节
    python3 scripts/extract_idioms.py --merge         # 仅合并已有结果（不调用API）

输出:
    kg/idioms/{章节号}_成语.md       — 单章结果
    kg/史记成语典故.md               — 合并后的总表
"""

import anthropic
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CHAPTER_DIR = _PROJECT_ROOT / "chapter_md"
OUTPUT_DIR = _PROJECT_ROOT / "kg" / "vocabularies" / "data" / "idioms"
MERGED_FILE = _PROJECT_ROOT / "kg" / "vocabularies" / "data" / "史记成语典故.md"
PROGRESS_FILE = OUTPUT_DIR / "progress.json"

# 章节分类
CHAPTER_GROUPS = {
    "本纪": list(range(1, 13)),      # 001-012
    "表":   list(range(13, 23)),      # 013-022
    "书":   list(range(23, 31)),      # 023-030
    "世家": list(range(31, 61)),      # 031-060
    "列传": list(range(61, 131)),     # 061-130
}

def get_chapter_group(chapter_num):
    """根据章节号判断分类"""
    n = int(chapter_num)
    for group, nums in CHAPTER_GROUPS.items():
        if n in nums:
            return group
    return "列传"


# ─── 提示词 ───

SYSTEM_PROMPT = """你是古汉语和成语典故研究专家。你的任务是从《史记》原文中识别和提取所有成语、典故及经典名句。

## 提取范围

1. **直接成语**：原文中直接出现的四字成语（如"网开一面"、"酒池肉林"）
2. **典故来源**：原文是后世成语/典故的出处，即使原文不是四字格式（如"指鹿为马"的故事、"卧薪尝胆"的叙述）
3. **经典名句**：虽非四字成语，但已成为经典引用的名句（如"王侯将相宁有种乎"、"燕雀安知鸿鹄之志"）
4. **后世演化**：原文的某个表述后来演化为成语，即使原文措辞不完全相同

## 不提取的内容

- 普通描述性短语，未成为成语或典故的
- 仅在学术文献中使用、大众不熟悉的生僻典故
- 纯人名/地名的简称

## 输出格式

对每个章节，输出一个Markdown表格：

### {章节号} {章节名}

| 成语 | 原文 | 释义 |
|------|------|------|
| 成语/典故名 | 原文中的相关语句（简短引用） | 简明释义（10-20字） |

要求：
- 成语名用现代通行写法
- 原文引用保持原文用字，取最关键的一句，不超过20字
- 释义简明扼要
- 按出现顺序排列
- 如果某章节没有成语典故，注明"本章未发现常见成语典故"
"""

def get_group_hint(group):
    """根据章节分类返回额外提示"""
    hints = {
        "本纪": "本纪记录帝王事迹，关注：帝王相关的成语（如指鹿为马、破釜沉舟）、政治典故、战争成语。",
        "表": "年表章节内容简短，成语较少，仔细筛选有典故价值的内容即可。",
        "书": "八书记载典章制度，关注：制度相关成语、经济成语（如奇货可居相关）、天文典故。",
        "世家": "世家记录诸侯历史，关注：春秋战国典故密集（如退避三舍、卧薪尝胆、围魏救赵）、谋略成语。",
        "列传": "列传人物事迹丰富，关注：人物品格成语（如完璧归赵）、处世哲学名句、历史故事成语。",
    }
    return hints.get(group, "")


def load_progress():
    """加载处理进度"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed": [], "failed": {}, "stats": {}}


def save_progress(progress):
    """保存处理进度"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def discover_chapters():
    """发现所有已标注的章节"""
    chapters = []
    for f in sorted(CHAPTER_DIR.glob("*.tagged.md")):
        name = f.stem.replace(".tagged", "")
        num = name.split("_")[0]
        chapters.append((num, name, f))
    return chapters


def process_chapters(client, chapters_batch):
    """调用大模型处理一批章节的成语提取

    Args:
        client: Anthropic client
        chapters_batch: list of (num, name, filepath) tuples

    Returns:
        output_text, idiom_count, tokens_in, tokens_out
    """
    # 组装输入文本
    combined_text = ""
    for num, name, filepath in chapters_batch:
        text = filepath.read_text(encoding="utf-8")
        combined_text += f"\n\n{'='*40}\n## 章节 {num} {name}\n{'='*40}\n\n{text}"

    group = get_chapter_group(chapters_batch[0][0])
    hint = get_group_hint(group)

    nums_str = ", ".join(n for n, _, _ in chapters_batch)
    user_prompt = f"""请从以下《史记》章节中提取所有成语、典故及经典名句。

处理章节：{nums_str}（{group}）

提示：{hint}

已标注原文如下：

{combined_text}

请按照系统提示中的格式要求，对每个章节分别输出成语表格。"""

    total_chars = len(combined_text)
    print(f"\n{'='*60}")
    print(f"  处理: {nums_str} ({group})")
    print(f"  输入长度: {total_chars} 字符")
    print(f"{'='*60}")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    output_text = response.content[0].text

    # 统计成语数
    idiom_count = output_text.count("| ") - output_text.count("| 成语")
    # 更精确的统计：数表格数据行
    lines = output_text.strip().split("\n")
    data_rows = [l for l in lines
                 if l.startswith("|") and not l.startswith("| 成语") and not l.startswith("|--")]
    idiom_count = len(data_rows)

    tokens_in = response.usage.input_tokens
    tokens_out = response.usage.output_tokens

    print(f"  -> 提取成语: {idiom_count}")
    print(f"  -> Token: {tokens_in} in / {tokens_out} out")

    return output_text, idiom_count, tokens_in, tokens_out


def group_chapters_for_batch(chapters, max_chars=150000):
    """将章节分组，避免单次请求过大

    Args:
        chapters: list of (num, name, filepath) tuples
        max_chars: 单批最大字符数

    Returns:
        list of batches, each batch is a list of (num, name, filepath)
    """
    batches = []
    current_batch = []
    current_size = 0

    for num, name, filepath in chapters:
        file_size = filepath.stat().st_size
        if current_batch and current_size + file_size > max_chars:
            batches.append(current_batch)
            current_batch = []
            current_size = 0
        current_batch.append((num, name, filepath))
        current_size += file_size

    if current_batch:
        batches.append(current_batch)

    return batches


def merge_results():
    """合并所有单章结果为总表"""
    if not OUTPUT_DIR.exists():
        print("错误: 没有找到单章结果目录 kg/idioms/")
        return

    result_files = sorted(OUTPUT_DIR.glob("*_成语.md"))
    if not result_files:
        print("错误: 没有找到任何成语结果文件")
        return

    # 按章节分类组织
    sections = {
        "本纪（001-012）": [],
        "表（013-022）": [],
        "书（023-030）": [],
        "世家（031-060）": [],
        "列传（061-130）": [],
    }

    total_idioms = 0
    chapter_count = 0

    for f in result_files:
        content = f.read_text(encoding="utf-8").strip()
        num = f.name.split("_")[0]
        n = int(num)

        if 1 <= n <= 12:
            key = "本纪（001-012）"
        elif 13 <= n <= 22:
            key = "表（013-022）"
        elif 23 <= n <= 30:
            key = "书（023-030）"
        elif 31 <= n <= 60:
            key = "世家（031-060）"
        else:
            key = "列传（061-130）"

        sections[key].append(content)
        chapter_count += 1

        # 统计行数
        lines = content.strip().split("\n")
        data_rows = [l for l in lines
                     if l.startswith("|") and not l.startswith("| 成语") and not l.startswith("|--")]
        total_idioms += len(data_rows)

    # 生成合并文件
    parts = [
        "# 史记成语典故\n",
        "从《史记》130章中提取的成语、典故及经典名句，按章节顺序排列。\n",
        "## 统计\n",
        f"- 成语/典故总数: 约{total_idioms}条",
        f"- 涵盖章节: {chapter_count}篇\n",
        "---\n",
    ]

    for section_name, contents in sections.items():
        if contents:
            parts.append(f"## {section_name}\n")
            parts.append("\n\n".join(contents))
            parts.append("")

    merged = "\n".join(parts)
    MERGED_FILE.write_text(merged, encoding="utf-8")
    print(f"\n已合并 {chapter_count} 章、约 {total_idioms} 条成语到: {MERGED_FILE}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="史记成语典故提取")
    parser.add_argument("chapters", nargs="*", help="要处理的章节号（如 001 002），不指定则处理所有")
    parser.add_argument("--group", help="按分类处理（本纪/表/书/世家/列传）")
    parser.add_argument("--dry-run", action="store_true", help="预览将处理的章节")
    parser.add_argument("--force", action="store_true", help="强制重新处理已完成的章节")
    parser.add_argument("--merge", action="store_true", help="仅合并已有结果为总表")
    parser.add_argument("--max-chars", type=int, default=150000, help="单批最大字符数（默认150000）")
    args = parser.parse_args()

    if args.merge:
        merge_results()
        return 0

    # 检查API密钥
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and not args.dry_run:
        print("错误: 未设置 ANTHROPIC_API_KEY 环境变量")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    progress = load_progress()
    all_chapters = discover_chapters()

    # 确定要处理的章节
    if args.chapters:
        target_nums = set(args.chapters)
        chapters_to_process = [(n, name, f) for n, name, f in all_chapters if n in target_nums]
    elif args.group:
        target_nums = set(str(n).zfill(3) for n in CHAPTER_GROUPS.get(args.group, []))
        chapters_to_process = [(n, name, f) for n, name, f in all_chapters if n in target_nums]
    else:
        chapters_to_process = all_chapters

    # 过滤已完成的章节
    if not args.force:
        completed = set(progress.get("completed", []))
        chapters_to_process = [(n, name, f) for n, name, f in chapters_to_process if name not in completed]

    print(f"{'='*60}")
    print(f"  史记成语典故提取")
    print(f"  待处理: {len(chapters_to_process)} 章")
    print(f"  已完成: {len(progress.get('completed', []))} 章")
    print(f"{'='*60}")

    if args.dry_run:
        batches = group_chapters_for_batch(chapters_to_process, args.max_chars)
        for i, batch in enumerate(batches):
            total_size = sum(f.stat().st_size for _, _, f in batch)
            nums = ", ".join(n for n, _, _ in batch)
            print(f"  批次{i+1}: [{nums}] ({total_size/1000:.0f}KB)")
        return 0

    if not chapters_to_process:
        print("  没有需要处理的章节。使用 --force 重新处理。")
        return 0

    client = anthropic.Anthropic(api_key=api_key)
    batches = group_chapters_for_batch(chapters_to_process, args.max_chars)

    total_idioms = 0
    total_tokens_in = 0
    total_tokens_out = 0

    for batch_idx, batch in enumerate(batches):
        print(f"\n[批次 {batch_idx+1}/{len(batches)}]")

        try:
            output_text, idiom_count, tokens_in, tokens_out = process_chapters(
                client, batch
            )

            # 保存每个章节的结果（拆分输出）
            # 尝试按 ### 标题拆分
            chapter_sections = re.split(r'(?=^### \d{3})', output_text, flags=re.MULTILINE)

            for section in chapter_sections:
                section = section.strip()
                if not section:
                    continue
                # 提取章节号
                m = re.match(r'### (\d{3})', section)
                if m:
                    ch_num = m.group(1)
                    # 找到对应的章节名
                    ch_name = None
                    for n, name, _ in batch:
                        if n == ch_num:
                            ch_name = name
                            break
                    if ch_name:
                        output_file = OUTPUT_DIR / f"{ch_name}_成语.md"
                        output_file.write_text(section, encoding="utf-8")
                        print(f"  -> 已保存: {output_file.name}")

                        if ch_name not in progress["completed"]:
                            progress["completed"].append(ch_name)
                        progress["failed"].pop(ch_name, None)

            # 如果无法拆分（单章节），直接保存
            if len(chapter_sections) <= 1 and len(batch) == 1:
                ch_num, ch_name, _ = batch[0]
                output_file = OUTPUT_DIR / f"{ch_name}_成语.md"
                output_file.write_text(output_text, encoding="utf-8")
                print(f"  -> 已保存: {output_file.name}")
                if ch_name not in progress["completed"]:
                    progress["completed"].append(ch_name)

            progress["stats"][f"batch_{batch_idx}"] = {
                "chapters": [n for n, _, _ in batch],
                "idioms": idiom_count,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "timestamp": datetime.now().isoformat(),
            }
            save_progress(progress)

            total_idioms += idiom_count
            total_tokens_in += tokens_in
            total_tokens_out += tokens_out

        except Exception as e:
            error_msg = str(e)
            print(f"\n  !! 批次失败: {error_msg}")
            for n, name, _ in batch:
                progress["failed"][name] = error_msg
            save_progress(progress)

    # 最终统计
    print(f"\n{'='*60}")
    print(f"  处理完成")
    print(f"  本次批次: {len(batches)}")
    print(f"  提取成语: {total_idioms}")
    print(f"  Token消耗: {total_tokens_in} in / {total_tokens_out} out")
    print(f"  累计完成: {len(progress['completed'])} 章")
    print(f"{'='*60}")

    # 自动合并
    print("\n正在合并结果...")
    merge_results()

    return 0


if __name__ == "__main__":
    sys.exit(main())
