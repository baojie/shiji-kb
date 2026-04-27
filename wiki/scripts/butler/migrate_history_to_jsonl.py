#!/usr/bin/env python3
"""一次性迁移脚本：将 wiki/public/history/*.json 转换为 JSONL 格式。

每个 PAGE.json（revisions 倒序，最新在 index 0）→ PAGE.jsonl（每行一条，正序，最旧在首行）
迁移完成后删除原 .json 文件。
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HIST = ROOT / "wiki/public/history"


def main():
    json_files = sorted(HIST.glob("*.json"))
    if not json_files:
        print("没有找到 .json 文件，退出。")
        return

    print(f"找到 {len(json_files)} 个 .json 文件，开始迁移...")
    ok = skip = 0

    for json_file in json_files:
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"✗ {json_file.name} 读取失败: {e}")
            skip += 1
            continue

        revisions = data.get("revisions", [])
        # revisions 倒序（最新在 index 0），反转为正序（最旧在首行）
        ordered = list(reversed(revisions))

        jsonl_file = json_file.with_suffix(".jsonl")
        lines = [json.dumps(rev, ensure_ascii=False) for rev in ordered]
        jsonl_file.write_text(
            "\n".join(lines) + "\n" if lines else "",
            encoding="utf-8",
        )

        json_file.unlink()
        print(f"✓ {json_file.stem} ({len(ordered)} 条修订)")
        ok += 1

    print(f"\n迁移完成：{ok} 个文件成功，{skip} 个跳过。")


if __name__ == "__main__":
    main()
