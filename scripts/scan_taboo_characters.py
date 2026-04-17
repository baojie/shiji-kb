#!/usr/bin/env python3
"""扫描《史记》130 章，按 data/taboo_characters.rules.json 所列避讳规则，
定位每个改字词组（如『田常』『微子开』『端月』『蒯通』等）的所有出现位置，
输出 data/taboo_characters.json 与 data/taboo_characters.md。

用法：
    python scripts/scan_taboo_characters.py

依赖：
    - data/taboo_characters.rules.json  （规则表，需先存在）
    - chapter_md/NNN_*.tagged.md        （标注源文件，130 章）
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
RULES_FILE = ROOT / "data" / "taboo_characters.rules.json"
CHAPTER_DIR = ROOT / "chapter_md"
OUT_JSON = ROOT / "data" / "taboo_characters.json"
OUT_MD = ROOT / "data" / "taboo_characters.md"

# 段落编号形如 [1] [1.1] [r8] 等
PARA_RE = re.compile(r"^\[([0-9r][0-9.]*)\]")
CHAPTER_FNAME_RE = re.compile(r"^(\d{3})_(.+)\.tagged\.md$")

SNIPPET_RADIUS = 40  # 摘录窗口左右字符数


def load_rules() -> dict:
    with RULES_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def list_chapters() -> List[Path]:
    files = []
    for f in sorted(CHAPTER_DIR.glob("*.tagged.md")):
        if "backup" in f.name or "_backup_" in f.name:
            continue
        if CHAPTER_FNAME_RE.match(f.name):
            files.append(f)
    return files


def parse_chapter(path: Path) -> Tuple[str, str, List[Tuple[str, int, str]]]:
    """返回 (chapter_id, chapter_name, [(para_id, line_no, line_text), ...])"""
    m = CHAPTER_FNAME_RE.match(path.name)
    chapter_id = m.group(1)
    chapter_name = m.group(2)
    lines_out: List[Tuple[str, int, str]] = []
    current_para = "0"
    with path.open(encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.rstrip("\n")
            # 段首识别
            stripped = line.lstrip()
            m2 = PARA_RE.match(stripped)
            if m2:
                current_para = m2.group(1)
            lines_out.append((current_para, lineno, line))
    return chapter_id, chapter_name, lines_out


def strip_tags(text: str) -> str:
    """去除 〖TYPE 内容〗 〖TYPE 显示|规范〗 ⟦TYPE 内容⟧ 等标记符号，
    保留 display 部分（消歧语法取 `|` 前的显示名）。"""
    # 消歧语法：〖TYPE display|canonical〗 -> display
    text = re.sub(r"〖[^〖〗|]*?\|([^〖〗]*?)〗", lambda m: m.group(0), text)  # noop keep pipe form
    # 普通：〖TYPE content〗 或 〖content〗
    # 取最内层标记的内容字段（第一个空格后）；保守做法：只剥离两端符号和 type 前缀
    def _unwrap(match: re.Match) -> str:
        body = match.group(1)
        # body 形如 "@人名" 或 "@display|canonical" 或 "content"
        if "|" in body:
            body = body.split("|", 1)[0]
        # 去除类型前缀 @ # & % _ ; ^ + = { * ? $ • 等
        return re.sub(r"^[@#&%_;\^+={*?$•◆○◈◉◇◆]+\s*", "", body)
    text = re.sub(r"〖([^〖〗]*?)〗", _unwrap, text)
    text = re.sub(r"⟦([^⟦⟧]*?)⟧", _unwrap, text)
    return text


def make_snippet(line: str, match_start: int, match_end: int, radius: int = SNIPPET_RADIUS) -> str:
    left = max(0, match_start - radius)
    right = min(len(line), match_end + radius)
    prefix = "…" if left > 0 else ""
    suffix = "…" if right < len(line) else ""
    return prefix + line[left:right] + suffix


def scan_pattern(changed: str, chapters: List[Tuple[str, str, List[Tuple[str, int, str]]]]) -> List[dict]:
    results: List[dict] = []
    for chapter_id, chapter_name, lines in chapters:
        for para_id, lineno, line in lines:
            start = 0
            while True:
                idx = line.find(changed, start)
                if idx < 0:
                    break
                snippet = make_snippet(line, idx, idx + len(changed))
                results.append({
                    "chapter_id": chapter_id,
                    "chapter_name": chapter_name,
                    "para_id": para_id,
                    "line_no": lineno,
                    "snippet": snippet,
                })
                start = idx + len(changed)
    return results


def build_output(rules_data: dict, chapters) -> dict:
    rules = rules_data["rules"]
    total_instances = 0
    for rule in rules:
        rule_instances: List[dict] = []
        for pattern in rule["patterns"]:
            occ = scan_pattern(pattern["form"], chapters)
            pattern["occurrences"] = occ
            pattern["occurrence_count"] = len(occ)
            total_instances += len(occ)
            rule_instances.extend(occ)
        rule["instance_count"] = len(rule_instances)
        rule["chapter_count"] = len({(x["chapter_id"]) for x in rule_instances})
    rules_data["_stats"] = {
        "total_rules": len(rules),
        "total_instances": total_instances,
        "chapters_scanned": len(chapters),
    }
    return rules_data


def render_markdown(data: dict) -> str:
    stats = data["_stats"]
    buf: List[str] = []
    buf.append("# 史记避讳改字专题\n")
    buf.append("《史记》因时代禁忌，对帝王、父祖之名有所回避，常以同义或同音之字代换本字。此专题按避讳类别收录改字规则，并穷举其在全书 130 篇中的实际出现位置。\n")
    buf.append("## 统计概览\n")
    buf.append(f"- **规则条数**：{stats['total_rules']}")
    buf.append(f"- **改字实例总数**：{stats['total_instances']}")
    buf.append(f"- **扫描章数**：{stats['chapters_scanned']}\n")
    buf.append("## 避讳类别\n")

    # 类别归并
    categories: Dict[str, List[dict]] = {}
    for rule in data["rules"]:
        categories.setdefault(rule["category"], []).append(rule)

    # 目录
    buf.append("| 类别 | 被讳者 | 本字 → 改字 | 实例数 | 覆盖章数 | 确信度 |")
    buf.append("|------|--------|------------|------:|--------:|--------|")
    for rule in data["rules"]:
        buf.append(
            f"| {rule['category']} | {rule['taboo_for']} | "
            f"{rule['taboo_char']} → {rule['replaced_by']} | "
            f"{rule['instance_count']} | {rule['chapter_count']} | {rule['confidence']} |"
        )
    buf.append("")

    # 正文
    for cat, rules in categories.items():
        buf.append(f"## {cat}\n")
        for rule in rules:
            buf.append(f"### {rule['id']}　{rule['taboo_for']}（讳『{rule['taboo_char']}』，改『{rule['replaced_by']}』）\n")
            buf.append(f"- **生效范围**：{rule['scope']}")
            buf.append(f"- **确信度**：{rule['confidence']}")
            buf.append(f"- **说明**：{rule['note']}\n")
            if not rule["patterns"]:
                buf.append("_本条规则在《史记》中未发现具体改字实例。_\n")
                continue
            for pat in rule["patterns"]:
                form = pat["form"]
                orig = pat["original"]
                if form == orig:
                    buf.append(f"#### 词组：『{form}』（本字；类别：{pat['kind']}）\n")
                else:
                    buf.append(f"#### 词组：『{form}』（本作『{orig}』，类别：{pat['kind']}）\n")
                buf.append(f"_{pat['note']}_\n")
                occ = pat["occurrences"]
                if not occ:
                    buf.append("（全书无匹配）\n")
                    continue
                buf.append(f"共 **{len(occ)}** 处：\n")
                buf.append("| 章 | 段 | 行 | 原文片段 |")
                buf.append("|----|----|---:|----------|")
                for o in occ:
                    ch = f"{o['chapter_id']} {o['chapter_name']}"
                    snippet = o["snippet"].replace("|", "\\|")
                    buf.append(f"| {ch} | [{o['para_id']}] | {o['line_no']} | {snippet} |")
                buf.append("")
        buf.append("")

    buf.append("---\n")
    buf.append("## 数据与脚本\n")
    buf.append("- 规则表：`data/taboo_characters.rules.json`")
    buf.append("- 机读结果：`data/taboo_characters.json`")
    buf.append("- 扫描脚本：`scripts/scan_taboo_characters.py`\n")
    buf.append("## 参考文献\n")
    buf.append("- 陈垣《史讳举例》")
    buf.append("- 王彦坤《历代避讳字汇典》")
    buf.append("- 顾炎武《日知录·卷二十三·避讳》")
    return "\n".join(buf) + "\n"


def main() -> None:
    rules_data = load_rules()
    chapter_files = list_chapters()
    print(f"[扫描] 共 {len(chapter_files)} 章")
    chapters = [parse_chapter(f) for f in chapter_files]
    data = build_output(rules_data, chapters)

    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[输出] {OUT_JSON.relative_to(ROOT)}")

    md = render_markdown(data)
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"[输出] {OUT_MD.relative_to(ROOT)}")

    stats = data["_stats"]
    print(f"[统计] 规则 {stats['total_rules']} 条，改字实例 {stats['total_instances']} 处")


if __name__ == "__main__":
    main()
