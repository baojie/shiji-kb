#!/usr/bin/env python3
"""
将平行结构段落按句号拆分为每句一行。

核心算法：提取每句的"骨架"（标注类型序列 + 功能词），
骨架相似的句子 ≥ 3 则判定为平行结构。

拆分规则：
- 在每个"。"后换行
- [N] 编号只保留在第一行
- 跳过 backup 文件
"""

import glob
import os
import re
import sys
from collections import Counter


# ── 骨架提取 ──────────────────────────────────────────────

# 标注符号 → 类型标记
TAG_PATTERN = re.compile(
    r'〖([^〗]*?)〗'   # 〖...〗
    r'|'
    r'⟦([^⟧]*?)⟧'    # ⟦...⟧
)

def sentence_skeleton(sent: str) -> str:
    """将一个句子转化为骨架字符串。

    步骤：
    1. 将每个标注替换为其类型标记（@→P, %→T, ◆→S, etc.）
    2. 保留功能词（卒/立/生/封/即位/元年/弑/杀 等）
    3. 去除其余汉字，只留骨架

    示例：
      "〖@微仲〗卒，子〖@宋公〗〖@稽〗立" → "P卒，子PP立"
      "〖@共公〗〖%八年〗卒，子〖@德公〗立"  → "PT卒，子P立"
    """
    result = []
    pos = 0
    for m in TAG_PATTERN.finditer(sent):
        # 处理标注之前的普通文本：只保留功能词和标点
        before = sent[pos:m.start()]
        result.append(_keep_skeleton_chars(before))

        # 处理标注本身：映射为类型标记
        content = m.group(1) or m.group(2) or ""
        if content:
            type_char = content[0]  # 首字符是类型标记
            result.append(_tag_type_label(type_char))

        pos = m.end()

    # 处理最后一段普通文本
    if pos < len(sent):
        result.append(_keep_skeleton_chars(sent[pos:]))

    return "".join(result)


def _tag_type_label(type_char: str) -> str:
    """将标注类型首字符映射为单字母骨架标记"""
    mapping = {
        "@": "P",   # 人名
        "%": "T",   # 时间
        "◆": "S",   # 国家
        "=": "L",   # 地名
        ";": "R",   # 身份
        "#": "G",   # 群体
        "&": "F",   # 氏族
        "~": "E",   # 族群
        "◉": "K",   # 暴力事件
        "◈": "W",   # 军事事件
        "^": "C",   # 制度概念
        "•": "O",   # 名物
        "{": "B",   # 典籍
        "_": "A",   # 抽象概念
        "$": "N",   # 数量
        "+": "I",   # 动植物
        "!": "H",   # 天象
        ":": "X",   # 文化
        "[": "J",   # 法律
    }
    return mapping.get(type_char, "?")


# 功能词：在骨架中保留这些词，其余汉字去掉
FUNC_WORDS = re.compile(
    r'(卒|立|生|封|死|崩|薨|即位|元年|灭|弑|杀|诛|反|侯|王|公|相|'
    r'子|弟|兄|父|嗣|代|自立|除国|国除|来朝|年|岁|月|日|'
    r'[，。、；：\u201c\u201d\u2018\u2019（）\d])'
)

def _keep_skeleton_chars(text: str) -> str:
    """从普通文本中只保留功能词和标点"""
    return "".join(FUNC_WORDS.findall(text))


# ── 平行结构检测 ──────────────────────────────────────────

def _normalize_skeleton(skel: str) -> str:
    """将骨架进一步归一化，用于相似度比较。

    - 合并连续的同类型标记（PP→P+）
    - 去除数字
    """
    # 合并连续相同标记
    normalized = re.sub(r'([A-Z])\1+', r'\1+', skel)
    # 去除数字
    normalized = re.sub(r'\d+', '', normalized)
    return normalized


def has_parallel_structure(line: str, min_parallel: int = 3) -> bool:
    """检测段落是否含有 ≥ min_parallel 个结构相似的短句。

    算法：
    1. 按"。"拆分句子
    2. 提取每句的归一化骨架
    3. 统计骨架频次，最大频次 ≥ min_parallel 则判定为平行结构
    4. 额外约束：平均句长 ≤ 80字，对话"曰" ≤ 2次
    """
    sentences = [s.strip() for s in line.split("。") if s.strip()]

    if len(sentences) < min_parallel:
        return False

    # 平均句长约束
    avg_len = len(line) / len(sentences)
    if avg_len > 80:
        return False

    # 对话约束
    if line.count("曰") > 2:
        return False

    # 提取骨架并归一化
    skeletons = [_normalize_skeleton(sentence_skeleton(s)) for s in sentences]

    # 统计最大频次（排除过短的骨架：长度 < 3 的不算有意义的平行结构）
    meaningful = [s for s in skeletons if len(s) >= 3]
    if len(meaningful) < min_parallel:
        return False

    counter = Counter(meaningful)
    max_freq = counter.most_common(1)[0][1] if counter else 0

    return max_freq >= min_parallel


def has_dense_enumeration(line: str) -> bool:
    """检测段落是否为密集列举（命名列举或短对话）。

    典型模式：
    - "一曰X，二曰Y，三曰Z"（命名列举）
    - "X曰：'...'Y曰：'...'"（密集短对话）
    - 星宿/官职/祭祀等的密集枚举

    判定条件：
    - "曰" ≥ 5
    - 句子数 ≥ 5
    - 曰密度 ≤ 40（每40字一个曰）
    - 平均句长 ≤ 35字
    """
    n_yue = line.count("曰")
    if n_yue < 5:
        return False

    sentences = [s.strip() for s in line.split("。") if s.strip()]
    if len(sentences) < 5:
        return False

    yue_density = len(line) / n_yue
    if yue_density > 40:
        return False

    # 超长段落通常是叙事（如触龙说赵太后946字），排除
    if len(line) > 500:
        return False

    avg_len = len(line) / len(sentences)
    return avg_len <= 35


TAG_TIME = re.compile(r'〖%[^〗]*〗')


def has_chronological_entries(line: str) -> bool:
    """检测段落是否为密集纪年段落（大量时间标注+短句）。

    典型模式：
    - "〖%元年〗，...。〖%二年〗，...。〖%三年〗，...。"
    - "〖%十年〗，X伐Y。〖%十一年〗，Z败W。"

    判定条件：
    - 时间标注 〖%...〗 ≥ 5
    - 句子数 ≥ 5
    - 平均句长 ≤ 50字
    - 排除含大量对话的叙事段落（曰 ≤ 2）
    """
    n_time = len(TAG_TIME.findall(line))
    if n_time < 5:
        return False

    sentences = [s.strip() for s in line.split("。") if s.strip()]
    if len(sentences) < 5:
        return False

    avg_len = len(line) / len(sentences)
    if avg_len > 50:
        return False

    # 含大量对话的是叙事，不是纪年
    if line.count("曰") > 2:
        return False

    return True


def has_dense_short_sentences(line: str) -> bool:
    """检测段落是否为极短句密集列举。

    典型模式（龟策列传占卜条目、五脏对应等）：
    - "病者死。系者出。行者行。来者来。"
    - "肺气通於鼻，鼻和则知臭香矣。肝气通於目，..."

    判定条件：
    - 句子数 ≥ 6
    - 平均句长 ≤ 15字
    """
    sentences = [s.strip() for s in line.split("。") if s.strip()]
    if len(sentences) < 6:
        return False
    avg_len = len(line) / len(sentences)
    return avg_len <= 15


def should_split(line: str) -> str:
    """判定段落是否应拆行，返回原因字符串或空串。

    排除：表格行（含 | 分隔符）
    """
    # 表格单元格内部不回车
    if "|" in line:
        return ""

    if has_parallel_structure(line):
        return "parallel"
    if has_dense_enumeration(line):
        return "enumeration"
    if has_chronological_entries(line):
        return "chronicle"
    if has_dense_short_sentences(line):
        return "short-list"
    return ""


# ── 拆分逻辑 ──────────────────────────────────────────────

def split_paragraph(line: str) -> str:
    """将一行按句号拆分为多行，保留段首编号在第一行"""
    parts = line.split("。")

    if parts and parts[-1].strip() == "":
        parts = parts[:-1]

    if len(parts) <= 1:
        return line

    result_lines = []
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        if i < len(parts) - 1:
            result_lines.append(part + "。")
        else:
            if line.rstrip().endswith("。"):
                result_lines.append(part + "。")
            else:
                result_lines.append(part)

    return "\n".join(result_lines)


# ── 文件处理 ──────────────────────────────────────────────

def process_file(filepath, dry_run=False, verbose=False):
    """处理单个文件，返回修改的段落数"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    modified_count = 0
    new_lines = []

    for line in lines:
        stripped = line.strip()

        # 以 [N] 开头且含句号的段落
        if re.match(r'\[(\d+)\]', stripped) and "。" in stripped:
            reason = should_split(stripped)
            if reason:
                new_content = split_paragraph(stripped)
                if new_content != stripped:
                    modified_count += 1
                    if dry_run:
                        pn = re.match(r'\[(\d+)\]', stripped).group(0)
                        n_sent = len([s for s in stripped.split("。") if s.strip()])
                        if verbose:
                            sents = [s.strip() for s in stripped.split("。") if s.strip()]
                            skels = [_normalize_skeleton(sentence_skeleton(s)) for s in sents]
                            counter = Counter(skels)
                            top_skel, top_freq = counter.most_common(1)[0]
                            print(f"  {pn} [{reason}] ({n_sent}句, {len(stripped)}字, "
                                  f"最大平行={top_freq}, 骨架='{top_skel}')")
                        else:
                            print(f"  {pn} [{reason}] ({n_sent}句, {len(stripped)}字)")
                    new_lines.append(new_content)
                    continue

        new_lines.append(line)

    if not dry_run and modified_count > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))

    return modified_count


def main():
    dry_run = "--dry-run" in sys.argv
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    if dry_run:
        print("=== DRY RUN: 只显示将要拆分的段落 ===\n")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chapter_dir = os.path.join(base_dir, "chapter_md")

    files = sorted(glob.glob(os.path.join(chapter_dir, "*.tagged.md")))
    files = [f for f in files if "backup" not in f]

    total_modified = 0
    files_modified = 0

    for filepath in files:
        basename = os.path.basename(filepath)
        count = process_file(filepath, dry_run=dry_run, verbose=verbose)
        if count > 0:
            files_modified += 1
            total_modified += count
            if dry_run:
                print(f"  → {basename}: {count}个段落\n")

    print(f"\n{'将要' if dry_run else '已'}拆分 {files_modified} 个文件中的 "
          f"{total_modified} 个平行结构段落")

    if dry_run:
        print("\n运行不带 --dry-run 参数以实际执行修改")


if __name__ == "__main__":
    main()
