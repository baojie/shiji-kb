#!/usr/bin/env python3
"""
check_size_loss.py — 原子操作后的字数损失审查。

比较页面最新版本与上一版本：
  - 「史记引文」节丢失：无条件 critical，不受任何阈值参数影响
  - 其他关键节（## 生平大事 等）丢失：critical
  - 字数缩减 ≥ 阈值（默认 20%）：critical
  - 字数轻度缩减 10%–阈值：warning
  - 结果写入 stderr（供 butler 管道捕获），stdout 输出机器可读 JSON

用法:
    python3 wiki/scripts/butler/check_size_loss.py <slug> [--threshold 0.20]
    python3 wiki/scripts/butler/check_size_loss.py <slug> --quiet   # 仅返回退出码

退出码:
    0  — safe（字数正常或增加，无关键节丢失）
    1  — warning（轻度缩减 10%~阈值，需反思）
    2  — critical（史记引文节丢失 / 其他关键节丢失 / 严重缩减，应 rollback）
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HISTORY = ROOT / 'wiki' / 'public' / 'history'

# 铁律：丢失即 critical，与字数阈值无关，不受任何参数控制
IRON_SECTION = '## 史记引文'

# 其他关键节（丢失即 critical）
OTHER_PROTECTED_SECTIONS = [
    '## 生平大事',
    '## 引文',
]

# 需要保护的 frontmatter 字段（丢失即 critical）
PROTECTED_FM_FIELDS = [
    'pn:',
    'sources:',
    'event_ids:',
]


def extract_sections(content: str) -> set[str]:
    """返回页面中存在的所有 ## 级节标题。"""
    return {line.strip() for line in content.splitlines()
            if line.strip().startswith('## ')}


def extract_fm_fields(content: str) -> set[str]:
    """返回 frontmatter 中存在的字段名（以 'key:' 形式）。"""
    in_fm = False
    fields: set[str] = set()
    for line in content.splitlines():
        if line.strip() == '---':
            in_fm = not in_fm
            continue
        if in_fm and ':' in line:
            key = line.split(':')[0].strip() + ':'
            fields.add(key)
    return fields


def check(slug: str, threshold: float, quiet: bool) -> int:
    h_file = HISTORY / f'{slug}.json'
    if not h_file.exists():
        if not quiet:
            print(json.dumps({'slug': slug, 'verdict': 'skip', 'reason': 'no_history'}))
        return 0

    try:
        data = json.loads(h_file.read_text(encoding='utf-8'))
    except Exception as e:
        print(f'check_size_loss: 读取历史失败 {slug}: {e}', file=sys.stderr)
        return 0

    revs = data.get('revisions', [])
    if len(revs) < 2:
        if not quiet:
            print(json.dumps({'slug': slug, 'verdict': 'skip', 'reason': 'only_one_revision'}))
        return 0

    new_rev = revs[0]
    old_rev = revs[1]

    new_size = new_rev.get('size', 0)
    old_size = old_rev.get('size', 0)

    if old_size == 0:
        if not quiet:
            print(json.dumps({'slug': slug, 'verdict': 'skip', 'reason': 'old_size_zero'}))
        return 0

    loss_ratio = (old_size - new_size) / old_size  # 正数 = 缩减

    new_content = new_rev.get('content', '')
    old_content = old_rev.get('content', '')

    old_sections = extract_sections(old_content)
    new_sections = extract_sections(new_content)

    verdict = 'safe'
    reasons = []

    # 铁律：史记引文节丢失 — 无条件 critical，独立判定，不受阈值参数影响
    if IRON_SECTION in old_sections and IRON_SECTION not in new_sections:
        verdict = 'critical'
        reasons.append(f'⛔ 铁律违反："{IRON_SECTION}" 节丢失（永远禁止，仅去重/纠错可用 --allow-citation-edit）')

    # 其他关键节丢失
    lost_other = [s for s in OTHER_PROTECTED_SECTIONS
                  if s in old_sections and s not in new_sections]
    if lost_other:
        verdict = 'critical'
        reasons.append(f'关键节丢失: {", ".join(lost_other)}')

    # 关键 frontmatter 字段丢失
    old_fm = extract_fm_fields(old_content)
    new_fm = extract_fm_fields(new_content)
    lost_fm = [f for f in PROTECTED_FM_FIELDS if f in old_fm and f not in new_fm]
    if lost_fm:
        verdict = 'critical'
        reasons.append(f'frontmatter字段丢失: {", ".join(lost_fm)}')

    # 字数缩减检查
    if loss_ratio >= threshold:
        verdict = 'critical'
        reasons.append(f'字数缩减 {loss_ratio:.0%}（阈值 {threshold:.0%}）'
                       f'：{old_size} → {new_size} bytes')
    elif loss_ratio >= 0.10:
        if verdict == 'safe':
            verdict = 'warning'
        reasons.append(f'字数轻度缩减 {loss_ratio:.0%}：{old_size} → {new_size} bytes')

    result = {
        'slug': slug,
        'verdict': verdict,
        'old_size': old_size,
        'new_size': new_size,
        'loss_ratio': round(loss_ratio, 4),
        'iron_violation': (IRON_SECTION in old_sections and IRON_SECTION not in new_sections),
        'lost_sections': ([IRON_SECTION] if (IRON_SECTION in old_sections
                           and IRON_SECTION not in new_sections) else []) + lost_other,
        'lost_fm_fields': lost_fm,
        'reasons': reasons,
        'action': new_rev.get('summary', ''),
    }

    if not quiet:
        print(json.dumps(result, ensure_ascii=False))

    if verdict == 'critical':
        print(f'⛔ [check_size_loss] CRITICAL {slug}: {"; ".join(reasons)}', file=sys.stderr)
        return 2
    elif verdict == 'warning':
        print(f'⚠️  [check_size_loss] WARNING {slug}: {"; ".join(reasons)}', file=sys.stderr)
        return 1
    else:
        return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('slug', help='页面 slug')
    ap.add_argument('--threshold', type=float, default=0.20,
                    help='缩减比例阈值，超过则 critical（默认 0.20 = 20%%）')
    ap.add_argument('--quiet', action='store_true', help='不输出 JSON，仅返回退出码')
    args = ap.parse_args()

    sys.exit(check(args.slug, args.threshold, args.quiet))


if __name__ == '__main__':
    main()
