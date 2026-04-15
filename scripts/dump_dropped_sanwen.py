#!/usr/bin/env python3
"""导出 build_sanwen_manifest.py 中 DROP 掉的条目原文，供审阅。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_sanwen_manifest import DROP  # noqa: E402
from extract_sanwen import extract_range, CHAPTER_DIR  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CANDS = ROOT / "labs" / "planning" / "sanwen_candidates.json"
OUT = ROOT / "labs" / "planning" / "sanwen_dropped.md"


def main() -> int:
    cands = {(c["chapter_num"], c["start_para"]): c
             for c in json.loads(CANDS.read_text(encoding="utf-8"))}

    with OUT.open("w", encoding="utf-8") as f:
        f.write(f"# 散文集·已剔除条目（共 {len(DROP)} 条）\n\n")
        f.write("> 按用户指示剔除的叙事性/对话性段落。如需恢复，"
                "请从 `build_sanwen_manifest.py` 的 `DROP` 集合中移除对应键。\n\n")

        for key in sorted(DROP):
            ch, sp = key
            c = cands.get(key)
            if not c:
                f.write(f"## [{ch}] 起段 {sp}  （不在候选清单，可能是手工 DROP）\n\n")
                continue
            files = list(CHAPTER_DIR.glob(f"{ch}_*.tagged.md"))
            text = files[0].read_text(encoding="utf-8") if files else ""
            content = extract_range(text, c["start_para"], c["end_para"]) if text else ""

            f.write(f"## {ch} {c['chapter_title']} · {c.get('suggested_title','')} "
                    f"`[{c['start_para']}-{c['end_para']}]` "
                    f"类型：{c['type']} · {c['char_count']}字\n\n")
            if c.get("section_heading"):
                f.write(f"_章内 H2：{c['section_heading']}_\n\n")
            f.write(f"触发：`{c.get('trigger','')}`\n\n")
            f.write("```\n")
            f.write(content.strip() + "\n")
            f.write("```\n\n---\n\n")

    print(f"已生成 {OUT}（{len(DROP)} 条）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
