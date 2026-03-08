#!/usr/bin/env python3
"""通用：将reflect JSON中的修正应用到事件索引文件

用法：
    python apply_reflect_fixes.py 001              # 应用单章
    python apply_reflect_fixes.py 001 002 003      # 应用多章
    python apply_reflect_fixes.py --all             # 应用所有已有reflect结果
"""
import json, re, sys, os, glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
EVENTS_DIR = os.path.join(BASE_DIR, "kg", "events", "data")
REPORTS_DIR = os.path.join(BASE_DIR, "kg", "events", "reports")


def strip_years(text):
    """移除所有年代标注，保留纪年标记如%九岁%"""
    t = text
    t = re.sub(r'（公元前\d+年(?:—前\d+年)?）', '', t)
    t = re.sub(r'\(公元前\d+年(?:—前\d+年)?\)', '', t)
    t = re.sub(r'(?<![（\[])公元前\d+年(?:—前\d+年)?(?![）\]])', '', t)
    t = re.sub(r'\[约?公元前\d+年(?:—前\d+年)?\]', '', t)
    return t.strip()


def has_reign_year(text):
    return bool(re.search(r'%[^%]+%', text))


def replace_time(old_text, suggested_year):
    if has_reign_year(suggested_year):
        return suggested_year
    else:
        cleaned = strip_years(old_text)
        if cleaned:
            return f"{cleaned} {suggested_year}"
        return suggested_year


def apply_fixes(chapter_id):
    reflect_path = os.path.join(REPORTS_DIR, f"reflect_{chapter_id}.json")
    if not os.path.exists(reflect_path):
        print(f"  {chapter_id}: 无反思结果，跳过")
        return 0

    with open(reflect_path, "r") as f:
        reflect = json.load(f)

    corrections = {c["event_id"]: c for c in reflect.get("corrections", [])}
    if not corrections:
        print(f"  {chapter_id}: 无修正项")
        return 0

    # Find index file
    pattern = os.path.join(EVENTS_DIR, f"{chapter_id}_*_事件索引.md")
    matches = glob.glob(pattern)
    if not matches:
        print(f"  {chapter_id}: 找不到事件索引文件")
        return 0
    index_path = matches[0]

    with open(index_path, "r") as f:
        content = f.read()

    lines = content.split("\n")
    new_lines = []
    changes = 0

    def find_current_event():
        for j in range(len(new_lines)-1, -1, -1):
            m = re.match(r'^### (' + re.escape(chapter_id) + r'-\d+) ', new_lines[j])
            if m:
                return m.group(1)
        return None

    for line in lines:
        # Overview table
        m = re.match(r'^\| (' + re.escape(chapter_id) + r'-\d+) \|', line)
        if m and m.group(1) in corrections:
            c = corrections[m.group(1)]
            cols = line.split("|")
            if len(cols) >= 6:
                new_time = replace_time(cols[4].strip(), c["suggested_year"])
                cols[4] = f" {new_time} "
                line = "|".join(cols)
                changes += 1
            new_lines.append(line)
            continue

        if line.startswith('- **时间**'):
            cur = find_current_event()
            if cur and cur in corrections:
                c = corrections[cur]
                sep = "：" if "：" in line else ":"
                old_val = line.split(sep, 1)[1].strip()
                new_val = replace_time(old_val, c["suggested_year"])
                line = f"- **时间**{sep} {new_val}"
                changes += 1
            new_lines.append(line)
            continue

        if line.startswith('- **年代推断**'):
            cur = find_current_event()
            if cur and cur in corrections:
                c = corrections[cur]
                sep = "：" if "：" in line else ":"
                line = f"- **年代推断**{sep} {c['reason']}"
                changes += 1
            new_lines.append(line)
            continue

        new_lines.append(line)

    with open(index_path, "w") as f:
        f.write("\n".join(new_lines))
    n_corrections = len(corrections)
    print(f"  {chapter_id}: {n_corrections}处修正，{changes}行变更")
    return changes


def main():
    args = sys.argv[1:]
    if not args:
        print("用法: python apply_reflect_fixes.py [--all | 001 002 ...]")
        return

    if "--all" in args:
        # Find all reflect files
        files = sorted(glob.glob(os.path.join(REPORTS_DIR, "reflect_*.json")))
        chapter_ids = [os.path.basename(f).replace("reflect_", "").replace(".json", "") for f in files]
    else:
        chapter_ids = [a.zfill(3) for a in args]

    total = 0
    for cid in chapter_ids:
        total += apply_fixes(cid)
    print(f"\n总计: {len(chapter_ids)}章, {total}行变更")


if __name__ == "__main__":
    main()
