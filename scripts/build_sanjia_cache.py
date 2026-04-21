#!/usr/bin/env python3
"""为三家注数据生成简体缓存，供前端快速加载。

输入：data/notes/*-notes.json（繁体原始数据）
输出：docs/notes_cache/*-notes.json（简体缓存）

说明：
- 原始数据保留为繁体（史记三家注是繁体，这是正式学术版本）
- 简体版通过 opencc t2s 转换生成
- 前端默认加载简体缓存；繁体显示时由 simp-trad-converter (opencc s2t) 再次转换
  （或未来可扩展为直接加载繁体原始数据以保真）
"""
import json
import sys
from pathlib import Path

try:
    import opencc
except ImportError:
    print("缺少 opencc 包。请运行: pip install opencc", file=sys.stderr)
    sys.exit(1)


# 基本字段：opencc t2s 转换（繁→简）
CONV_KEYS = {'anchor_text', 'before_context', 'after_context', 'text', 'label'}
# 匹配用字段：再套用章节自定义变体词表（把简体恢复到章节里混用的传统字形）
# 作用：章节里 "然後" "於是" 等保留传统字形，经 t2s 后 notes 是 "然后" "于是"，无法匹配。
# 对 anchor/before/after 三个匹配字段再做一次 dict 替换，使其与章节用字对齐。
MATCH_KEYS = {'anchor_text', 'before_context', 'after_context'}


def convert_obj(obj, cc):
    if isinstance(obj, dict):
        return {
            k: (cc.convert(v) if k in CONV_KEYS and isinstance(v, str) else convert_obj(v, cc))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [convert_obj(x, cc) for x in obj]
    return obj


def main():
    cc = opencc.OpenCC('t2s')
    root = Path(__file__).resolve().parent.parent
    src_dir = root / 'data' / 'notes'
    out_dir = root / 'docs' / 'notes_cache'
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for src in sorted(src_dir.glob('*-notes.json')):
        with open(src, 'r', encoding='utf-8') as f:
            data = json.load(f)
        out = convert_obj(data, cc)
        out_path = out_dir / src.name
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        count += 1

    print(f"转换完成: {count} 个文件 → {out_dir.relative_to(root)}")


if __name__ == '__main__':
    main()
