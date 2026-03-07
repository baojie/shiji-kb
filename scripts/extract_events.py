#!/usr/bin/env python3
"""
史记事件识别批处理脚本

从已标注的 chapter_md/*.tagged.md 文件中提取历史事件，
输出结构化的事件索引到 kg/events/ 目录。

使用方法:
    python3 scripts/extract_events.py                # 处理所有未完成章节
    python3 scripts/extract_events.py 003 004 005    # 只处理指定章节
    python3 scripts/extract_events.py --retry-failed  # 重试失败的章节
    python3 scripts/extract_events.py --dry-run       # 预览将处理的章节
"""

import anthropic
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHAPTER_DIR = _PROJECT_ROOT / "chapter_md"
OUTPUT_DIR = _PROJECT_ROOT / "kg" / "events"
PROGRESS_FILE = _PROJECT_ROOT / "kg" / "events" / "progress.json"

# 章节分类，影响提示词的微调
CHAPTER_TYPES = {
    "本纪": list(range(1, 13)),      # 001-012
    "表":   list(range(13, 23)),      # 013-022
    "书":   list(range(23, 31)),      # 023-030
    "世家": list(range(31, 61)),      # 031-060
    "列传": list(range(61, 131)),     # 061-130
}

def get_chapter_type(chapter_num):
    """根据章节号判断类型"""
    n = int(chapter_num)
    for ctype, nums in CHAPTER_TYPES.items():
        if n in nums:
            return ctype
    return "列传"

# ─── 提示词 ───

SYSTEM_PROMPT = """你是《史记》历史事件识别专家。你的任务是从已标注的《史记》章节中识别和提取所有历史事件。

## 输出格式

输出一个Markdown文件，包含两部分：

### 第一部分：事件列表概览（表格）

| 事件ID | 事件名称 | 事件类型 | 时间 | 地点 | 主要人物 | 朝代 |
|--------|---------|---------|------|------|---------|------|

- 事件ID格式：`{章节号}-{序号}`，如 `003-001`、`003-002`
- 事件名称：4-8字概括，动宾结构优先（如"阪泉之战"、"汤伐桀"、"盘庚迁殷"）
- 事件类型：见下方分类
- 时间：使用原文中的时间标注（%时间%格式），无则填 `-`
- 地点：使用原文中的地名标注（=地名=格式），无则填 `-`
- 主要人物：使用@人名@格式，多人用中文顿号分隔
- 朝代：使用&朝代&格式，无则填 `-`

### 第二部分：详细事件记录

每个事件用三级标题，包含以下字段：

### {事件ID} {事件名称}
- **事件类型**: {类型}
- **时间**: {时间}
- **地点**: {地点}
- **主要人物**: {人物}
- **涉及朝代**: {朝代}
- **事件描述**: 2-4句话概括事件的起因、经过、结果
- **原文引用**: 引用原文中最关键的1-2句（保留实体标注）
- **段落位置**: [{段落号}]

### 第三部分：统计信息和关键事件链

- 统计各类事件数量
- 梳理2-5条关键事件链（因果关系或时间顺序的事件序列）

## 事件类型分类

主要类型：
- **战争**: 战役、军事征伐、平叛
- **继位**: 即位、崩逝、禅让、篡位、废立
- **政治活动**: 朝会、外交、联盟、谏言、决策
- **政治改革**: 变法、制度建设、任命
- **政治整顿**: 惩处、流放、诛杀、清洗
- **家族事件**: 婚姻、生子、世系、家族纷争
- **建设**: 治水、筑城、迁都、工程
- **文化活动**: 礼乐、祭祀、著述、教育
- **经济活动**: 商贸、赋税、盐铁、货殖
- **自然灾害**: 洪水、地震、旱灾、天象异变
- **改革**: 法律变革、官制改革

## 事件识别原则

1. **粒度适中**：一个事件是一个有完整起因-经过-结果的行为单元。不要把整段文字算作一个事件，也不要拆得过细（如每句话一个事件）
2. **世系简化**：连续的"X崩，子Y立"可以合并为一个"世系传承"事件，除非有额外叙述
3. **重复判别**：同一事件在不同段落被提及时，只记录主要叙述处，在事件描述中注明
4. **保留标注**：原文引用中保留所有实体标注（@人名@、=地名=等）
5. **太史公曰**：太史公的评论本身不是事件，但如果评论中提到了新的史实，应当提取
6. **因果关联**：在事件链中体现事件之间的因果和时序关系"""

def get_chapter_specific_prompt(chapter_type):
    """根据章节类型返回额外提示"""
    prompts = {
        "本纪": """
特别注意：本纪记录帝王事迹，事件密度高。
- 重点关注：继位、崩逝、征伐、制度建设、重大政治决策
- 注意区分同一帝王的不同时期事件
- 年表部分的"X年，Y事"格式中，每条有独立意义的记录都应提取""",
        "表": """
特别注意：年表章节以表格/条目形式记载，事件提取方式不同。
- 提取有叙事性的重大事件，忽略纯粹的年月记录
- 关注跨国并列的重大事件（如合纵连横、灭国战争）
- 如果内容主要是年代列表，只提取其中有叙述的关键事件""",
        "书": """
特别注意：八书记载典章制度，事件识别侧重制度变革。
- 重点提取制度的创建、变革、废止等关键节点
- 天文书中的天象记录可作为"天象事件"提取
- 封禅书中的历次封禅是重要事件
- 河渠书中的水利工程建设是重要事件""",
        "世家": """
特别注意：世家记录诸侯国历史，时间跨度长。
- 建国、迁都、灭国是关键事件
- 注意区分同一国号下不同君主的事件
- 重大战役（如城濮之战、长平之战）需详细记录
- 世系传承可适当合并""",
        "列传": """
特别注意：列传记录个人事迹，关注人物生平关键节点。
- 合传中不同人物的事件分别提取
- 关注人物的关键转折点：出仕、建功、获罪、结局
- 对话/谏言中反映的事件也应提取
- 类传（循吏、酷吏等）中每个人物单独处理""",
    }
    return prompts.get(chapter_type, "")


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


def process_chapter(client, chapter_num, chapter_name, tagged_text):
    """调用大模型处理单个章节的事件识别"""
    chapter_type = get_chapter_type(chapter_num)
    extra_prompt = get_chapter_specific_prompt(chapter_type)

    user_prompt = f"""请从以下《史记》章节中识别和提取所有历史事件。

章节：{chapter_name}（{chapter_type}）
{extra_prompt}

已标注原文如下：

{tagged_text}

请按照系统提示中的格式要求，输出完整的事件索引。事件ID前缀使用 `{chapter_num}`。"""

    print(f"\n{'='*60}")
    print(f"  处理: {chapter_num}_{chapter_name} ({chapter_type})")
    print(f"  输入长度: {len(tagged_text)} 字符")
    print(f"{'='*60}")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    output_text = response.content[0].text

    # 基本统计
    event_count = len(re.findall(r'^### \d{3}-\d{3}', output_text, re.MULTILINE))
    tokens_in = response.usage.input_tokens
    tokens_out = response.usage.output_tokens

    print(f"  -> 识别事件: {event_count}")
    print(f"  -> Token: {tokens_in} in / {tokens_out} out")

    return output_text, event_count, tokens_in, tokens_out


def main():
    import argparse
    parser = argparse.ArgumentParser(description="史记事件识别批处理")
    parser.add_argument("chapters", nargs="*", help="要处理的章节号（如 003 004），不指定则处理所有")
    parser.add_argument("--retry-failed", action="store_true", help="重试之前失败的章节")
    parser.add_argument("--dry-run", action="store_true", help="预览将处理的章节，不实际执行")
    parser.add_argument("--force", action="store_true", help="强制重新处理已完成的章节")
    args = parser.parse_args()

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
    elif args.retry_failed:
        failed_names = set(progress.get("failed", {}).keys())
        chapters_to_process = [(n, name, f) for n, name, f in all_chapters if name in failed_names]
    else:
        chapters_to_process = all_chapters

    # 过滤已完成的章节
    if not args.force:
        completed = set(progress.get("completed", []))
        chapters_to_process = [(n, name, f) for n, name, f in chapters_to_process if name not in completed]

    print(f"{'='*60}")
    print(f"  史记事件识别批处理")
    print(f"  待处理: {len(chapters_to_process)} 章")
    print(f"  已完成: {len(progress.get('completed', []))} 章")
    print(f"  已失败: {len(progress.get('failed', {}))} 章")
    print(f"{'='*60}")

    if args.dry_run:
        for n, name, f in chapters_to_process:
            ctype = get_chapter_type(n)
            print(f"  {n} {name} ({ctype})")
        return 0

    if not chapters_to_process:
        print("  没有需要处理的章节。")
        return 0

    client = anthropic.Anthropic(api_key=api_key)
    total_events = 0
    total_tokens_in = 0
    total_tokens_out = 0

    for i, (chapter_num, chapter_name, chapter_file) in enumerate(chapters_to_process):
        print(f"\n[{i+1}/{len(chapters_to_process)}]", end="")

        # 读取已标注原文
        tagged_text = chapter_file.read_text(encoding="utf-8")

        try:
            output_text, event_count, tokens_in, tokens_out = process_chapter(
                client, chapter_num, chapter_name, tagged_text
            )

            # 添加文件头
            header = f"# {chapter_name} 事件索引\n\n"
            if not output_text.startswith("# "):
                output_text = header + output_text

            # 保存事件索引
            output_file = OUTPUT_DIR / f"{chapter_name}_事件索引.md"
            output_file.write_text(output_text, encoding="utf-8")
            print(f"  -> 已保存: {output_file.name}")

            # 更新进度
            if chapter_name not in progress["completed"]:
                progress["completed"].append(chapter_name)
            progress["failed"].pop(chapter_name, None)
            progress["stats"][chapter_name] = {
                "events": event_count,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "timestamp": datetime.now().isoformat(),
            }
            save_progress(progress)

            total_events += event_count
            total_tokens_in += tokens_in
            total_tokens_out += tokens_out

        except Exception as e:
            error_msg = str(e)
            print(f"\n  !! 失败: {error_msg}")
            progress["failed"][chapter_name] = error_msg
            save_progress(progress)

    # 最终统计
    print(f"\n{'='*60}")
    print(f"  处理完成")
    print(f"  本次处理: {len(chapters_to_process)} 章")
    print(f"  识别事件: {total_events}")
    print(f"  Token消耗: {total_tokens_in} in / {total_tokens_out} out")
    print(f"  累计完成: {len(progress['completed'])}/130 章")
    print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
