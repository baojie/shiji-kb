#!/usr/bin/env python3
"""
095 樊郦滕灌列传的军功短剧拆行。
对长度 > 200 字且未含引号对话的段落，按句号（。/！/？）拆成多行。
保留 Purple Number [N]，不改动原文字符。
"""
import re
from pathlib import Path

PATH = Path("chapter_md/095_樊郦滕灌列传.tagged.md")

# 引号内不断行（全角左右双引号）
QUOTE_L = "\u201c"
QUOTE_R = "\u201d"


def split_by_sentence(text: str) -> str:
    """在段落文本中，按 。（不在引号对内）拆行"""
    out = []
    in_quote = False
    buf = []
    for ch in text:
        buf.append(ch)
        if ch == QUOTE_L:
            in_quote = True
        elif ch == QUOTE_R:
            in_quote = False
        elif ch in "。！？" and not in_quote:
            # 断句：把 buf 切下成一行，但下一字不能是右引号（已包含）
            pass  # 延迟处理
    # 简化：用正则在句号后换行（引号外）
    # 先遮蔽引号内的文本
    result = []
    masked = []
    stack = 0
    for ch in text:
        if ch == QUOTE_L:
            stack += 1
        elif ch == QUOTE_R:
            stack -= 1 if stack > 0 else 0
        masked.append(ch if stack == 0 else "X")
    masked_str = "".join(masked)
    # 在 masked 中找 。 后的位置，在原文相同位置插入 \n
    i = 0
    out_chars = []
    while i < len(text):
        out_chars.append(text[i])
        if masked_str[i] in "。！？" and i + 1 < len(text):
            # 如果下一个字符是右引号，推迟断行
            nxt = text[i + 1]
            if nxt == QUOTE_R:
                # 下一轮处理完 " 再断
                pass
            else:
                out_chars.append("\n")
        i += 1
    return "".join(out_chars)


def process():
    content = PATH.read_text(encoding="utf-8")
    lines = content.split("\n")
    result_lines = []
    changed = 0
    for line in lines:
        m = re.match(r'^(\[\d+(?:\.\d+)?\]\s*)(.+)$', line)
        if m and len(line) > 300:
            prefix = m.group(1)
            body = m.group(2)
            # 如果含引号对话且有多对引号，不拆（保留叙事完整性）
            quote_pairs = min(body.count(QUOTE_L), body.count(QUOTE_R))
            # 只对军功短剧类（无引号对话）拆行
            if quote_pairs == 0:
                new_body = split_by_sentence(body)
                if "\n" in new_body:
                    result_lines.append(prefix + new_body)
                    changed += 1
                    continue
        result_lines.append(line)
    PATH.write_text("\n".join(result_lines), encoding="utf-8")
    print(f"拆行 {changed} 个段落")


if __name__ == "__main__":
    process()
