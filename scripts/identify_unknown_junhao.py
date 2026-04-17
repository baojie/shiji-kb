#!/usr/bin/env python3
"""
对 data/jun_titles.json 中 name="不详" 的封号，
在 tag_forms 所指章节里扫描封号出现位置附近的上下文，
抽取可能的人名候选（〖@XX〗 距离封号 ≤ 80 字内）。

只输出报告，不直接修改 JSON（需要人工确认后手工修）。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CH = ROOT / "chapter_md"


def scan_title(title: str, tag_forms: list, chapters: list) -> list:
    """对封号扫描指定章节，返回候选人名列表 [(chapter, context, nearby_names)]"""
    results = []
    # 用最长匹配的 tag_form 或纯标题
    search_terms = set(tag_forms) | {title}
    # 去掉 〖;/〖@ 前后缀，得到纯文字
    for t in list(search_terms):
        for pat in ("〖;", "〖@", "〗"):
            t2 = t.replace(pat, "")
        if t2 != t:
            search_terms.add(t2)

    for ch in chapters:
        ch_files = list(CH.glob(f"{ch.split('_')[0]}_*.tagged.md"))
        if not ch_files:
            continue
        text = ch_files[0].read_text(encoding="utf-8")
        for term in search_terms:
            for m in re.finditer(re.escape(term), text):
                start = max(0, m.start() - 100)
                end = min(len(text), m.end() + 100)
                ctx = text[start:end]
                # 提取上下文里的 〖@人名〗（去消歧后半部分）
                names = set()
                for nm in re.finditer(r'〖@([^〗|]+)(?:\|[^〗]+)?〗', ctx):
                    name = nm.group(1)
                    # 排除等同于封号本身
                    if name == title or name in title:
                        continue
                    # 排除封地名（即含邦国/地名特征的）
                    names.add(name)
                # 只取最近的 3 个
                if names:
                    results.append({
                        "chapter": ch,
                        "context": ctx.replace("\n", " ")[:200],
                        "candidate_names": list(names)[:5],
                    })
    return results


def main():
    jt_path = ROOT / "data" / "jun_titles.json"
    data = json.loads(jt_path.read_text(encoding="utf-8"))

    unclear = []
    for cat in data["categories"]:
        for e in cat.get("entries", []):
            name = e.get("name", "").strip()
            if ("不详" in name or "未知" in name or "待考" in name or
                    "史失其名" in name or name == ""):
                unclear.append((cat["category"], e))

    print(f"# 封号索引人名补全候选扫描\n")
    print(f"待补 {len(unclear)} 条\n")
    out_lines = [f"# 封号索引 name=不详 候选扫描\n", f"> 共 {len(unclear)} 条待补全\n"]

    for cat_name, e in unclear:
        print(f"\n## [{e['id']}] {e['title']}")
        print(f"分类: {cat_name}")
        print(f"当前 name: {e['name']}")
        print(f"tag_forms: {e.get('tag_forms', [])}")
        out_lines.append(f"\n## [{e['id']}] {e['title']}")
        out_lines.append(f"- 分类: {cat_name}")
        out_lines.append(f"- 当前 name: `{e['name']}`")
        out_lines.append(f"- tag_forms: {e.get('tag_forms', [])}")

        candidates = scan_title(e["title"], e.get("tag_forms", []),
                                e.get("chapters", []))
        if not candidates:
            print("  (无上下文可找)")
            out_lines.append("- 扫描结果: **无上下文候选**")
            continue

        # 统计邻近人名频率
        name_freq = {}
        for c in candidates:
            for nm in c["candidate_names"]:
                name_freq[nm] = name_freq.get(nm, 0) + 1
        top = sorted(name_freq.items(), key=lambda x: -x[1])[:5]
        print(f"  候选人名（按频率）: {top}")
        out_lines.append(f"- **候选人名**: {top}")
        for c in candidates[:3]:
            print(f"  [{c['chapter']}] ...{c['context'][:120]}...")
            out_lines.append(f"  - [{c['chapter']}] `...{c['context'][:150]}...`")

    out_path = ROOT / "labs/planning/junhao_unknown_scan.md"
    out_path.parent.mkdir(exist_ok=True, parents=True)
    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"\n报告已保存: {out_path}")


if __name__ == "__main__":
    main()
