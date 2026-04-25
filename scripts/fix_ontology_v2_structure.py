#!/usr/bin/env python3
"""
修复 ontology-v2 目录结构：
1. 合并 eureka 文件夹 → eureka.md (chapter_018, chapter_053)
2. chapter_053: 将 root facts/skills 合并进 skus/
3. 删除所有空文件夹
"""
import json
import os
import shutil
from pathlib import Path

CHAPTERS = Path(__file__).parent.parent / "kg/ontology/ontology-v2/chapters"


# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────

def json_to_md_body(data) -> str:
    """递归将 JSON data 转为 Markdown。"""
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, (int, float, bool)):
        return str(data)
    if isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(json_to_md_body(item))
            else:
                lines.append(f"- {item}")
        return "\n".join(lines)
    if isinstance(data, dict):
        lines = []
        for k, v in data.items():
            if isinstance(v, dict):
                lines.append(f"### {k}\n")
                lines.append(json_to_md_body(v))
            elif isinstance(v, list):
                lines.append(f"**{k}**：")
                for item in v:
                    if isinstance(item, (dict, list)):
                        lines.append(json_to_md_body(item))
                    else:
                        lines.append(f"- {item}")
            else:
                lines.append(f"- **{k}**：{v}")
        return "\n".join(lines)
    return str(data)


def convert_json_to_md_content(json_path: Path) -> str:
    """将 JSON fact 文件转为 .md 字符串。"""
    obj = json.loads(json_path.read_text(encoding="utf-8"))
    name = obj.get("name", json_path.stem)
    description = obj.get("description", "")
    data = obj.get("data", {})
    extra = {k: v for k, v in obj.items() if k not in ("name", "description", "data")}

    lines = [
        "---",
        f"name: {name}",
        f"description: {description}",
        "---",
        "",
        f"# {description or name}",
        "",
    ]
    if isinstance(data, dict):
        for k, v in data.items():
            lines.append(f"## {k}\n")
            lines.append(json_to_md_body(v))
            lines.append("")
    elif isinstance(data, list):
        lines.append(json_to_md_body(data))
        lines.append("")
    elif data:
        lines.append(str(data))
        lines.append("")

    if extra:
        for k, v in extra.items():
            if k in ("significance", "modern_relevance", "historical_impact"):
                lines.append(f"## {k}\n")
                if isinstance(v, dict):
                    lines.append(json_to_md_body(v))
                elif isinstance(v, list):
                    for item in v:
                        lines.append(f"- {item}")
                else:
                    lines.append(str(v))
                lines.append("")
    return "\n".join(lines)


def ensure_frontmatter(md_path: Path, name: str, description: str) -> None:
    """若 .md 文件没有 frontmatter，在头部插入。"""
    content = md_path.read_text(encoding="utf-8")
    if content.startswith("---"):
        return
    fm = f"---\nname: {name}\ndescription: {description}\n---\n\n"
    md_path.write_text(fm + content, encoding="utf-8")


def delete_empty_dirs(root: Path) -> int:
    """递归删除空目录，返回删除数量。"""
    count = 0
    # 从深到浅
    for dirpath in sorted(root.rglob("*"), key=lambda p: -len(p.parts)):
        if dirpath.is_dir():
            try:
                dirpath.rmdir()  # 只有空目录才会成功
                print(f"  🗑 删除空目录：{dirpath.relative_to(CHAPTERS)}")
                count += 1
            except OSError:
                pass
    return count


# ─────────────────────────────────────────────
# 1. 合并 eureka 文件夹 → eureka.md
# ─────────────────────────────────────────────

def merge_eureka_folder(chapter_dir: Path) -> None:
    eureka_dir = chapter_dir / "eureka"
    eureka_md = chapter_dir / "eureka.md"
    if not eureka_dir.is_dir():
        return
    files = sorted(eureka_dir.glob("*.md"))
    if not files:
        return

    print(f"\n  合并 eureka/ → eureka.md ({chapter_dir.name})")

    # 读取现有 eureka.md（若有）
    existing = eureka_md.read_text(encoding="utf-8") if eureka_md.exists() else ""

    # 追加各文件内容（去除已存在的内容）
    appended = []
    for f in files:
        text = f.read_text(encoding="utf-8").strip()
        # 取第一行标题作为标识
        first_line = text.split("\n")[0].strip("# ").strip()
        if first_line and first_line not in existing:
            appended.append(f"\n---\n\n{text}\n")
            print(f"    ✓ 追加：{f.name}")
        else:
            print(f"    ⏭ 已存在，跳过：{f.name}")

    if appended:
        new_content = existing.rstrip() + "\n" + "".join(appended)
        eureka_md.write_text(new_content, encoding="utf-8")


# ─────────────────────────────────────────────
# 2. chapter_053：合并 root facts/skills → skus/
# ─────────────────────────────────────────────

def next_fact_number(skus_facts: Path) -> int:
    nums = []
    for f in skus_facts.glob("fact_*.md"):
        try:
            n = int(f.name.split("_")[1])
            nums.append(n)
        except (IndexError, ValueError):
            pass
    return max(nums, default=0) + 1


def next_skill_number(skus_skills: Path) -> int:
    nums = []
    for f in skus_skills.glob("skill_*.md"):
        try:
            n = int(f.name.split("_")[1])
            nums.append(n)
        except (IndexError, ValueError):
            pass
    return max(nums, default=0) + 1


# 哪些 root fact 与 skus 高度重叠，直接丢弃（skus 版本更丰富）
OVERLAPPING_ROOT_FACTS = {
    "002_xiao_he_self_preservation.md",   # → skus/fact_005
    "003_moon_chase_han_xin.md",          # → skus/fact_004
}

# 哪些 root skill 与 skus 高度重叠
OVERLAPPING_ROOT_SKILLS = {
    # root/003_self_preservation → skus/skill_002（附加 checklist）
}


def merge_chapter_053(chapter_dir: Path) -> None:
    root_facts = chapter_dir / "facts"
    root_skills = chapter_dir / "skills"
    skus_facts = chapter_dir / "skus" / "facts"
    skus_skills = chapter_dir / "skus" / "skills"

    if not root_facts.exists():
        return

    print(f"\n  合并 chapter_053 root facts/skills → skus/")

    # ── facts ──
    seq = next_fact_number(skus_facts)
    for f in sorted(root_facts.iterdir()):
        if f.name in OVERLAPPING_ROOT_FACTS:
            print(f"    ⏭ 与 skus 高度重叠，丢弃：{f.name}")
            continue

        if f.suffix == ".json":
            # 转换 JSON
            try:
                content = convert_json_to_md_content(f)
            except Exception as e:
                print(f"    ✗ JSON 解析失败 {f.name}: {e}")
                continue
            out_name = f"fact_{seq:03d}_{f.stem}.md"
            dest = skus_facts / out_name
            dest.write_text(content, encoding="utf-8")
            print(f"    ✓ 转换 JSON → {out_name}")
            seq += 1

        elif f.suffix == ".md":
            # 特殊处理：root/007 家族遗产 → 追加"成语典故"到 fact_006
            if f.name == "007_family_legacy.json":
                pass  # 不会走到这里（是 .json 后缀）
            else:
                out_name = f"fact_{seq:03d}_{f.stem}.md"
                dest = skus_facts / out_name
                content = f.read_text(encoding="utf-8")
                # 确保有 frontmatter
                if not content.startswith("---"):
                    stem_name = f.stem
                    content = f"---\nname: {stem_name}\ndescription: \n---\n\n" + content
                dest.write_text(content, encoding="utf-8")
                print(f"    ✓ 复制 MD → {out_name}")
                seq += 1

    # 特殊处理：root/007_family_legacy.json → 追加历史影响节到 skus/fact_006
    legacy_json = root_facts / "007_family_legacy.json"
    fact006 = skus_facts / "fact_006_hereditary_marquis.md"
    if legacy_json.exists() and fact006.exists():
        obj = json.loads(legacy_json.read_text(encoding="utf-8"))
        hist = obj.get("historical_impact", {})
        existing = fact006.read_text(encoding="utf-8")
        if hist and "成语" not in existing:
            addition = "\n\n## 历史影响\n\n"
            chengyu = hist.get("成语", [])
            if chengyu:
                addition += "**相关成语**：" + "、".join(chengyu) + "\n\n"
            diangu = hist.get("典故", [])
            if diangu:
                addition += "**相关典故**：" + "、".join(diangu) + "\n\n"
            pingjia = hist.get("评价", "")
            if pingjia:
                addition += f"**太史公评价**：{pingjia}\n"
            fact006.write_text(existing.rstrip() + addition, encoding="utf-8")
            print(f"    ✓ 追加历史影响节 → fact_006_hereditary_marquis.md")

    # ── skills ──
    seq_s = next_skill_number(skus_skills)

    # 特殊处理：root/003_self_preservation → 追加 checklist 到 skus/skill_002
    skill003 = root_skills / "003_self_preservation.md"
    skill002 = skus_skills / "skill_002_self_diminishment.md"
    if skill003.exists() and skill002.exists():
        root_text = skill003.read_text(encoding="utf-8")
        existing = skill002.read_text(encoding="utf-8")
        # 找 "检查清单" 段落
        if "检查清单" in root_text and "## 检查清单" not in existing:
            # 提取检查清单部分
            idx = root_text.find("## 检查清单")
            checklist_section = root_text[idx:].split("\n## ")[0].strip()
            skill002.write_text(
                existing.rstrip() + "\n\n" + checklist_section + "\n",
                encoding="utf-8"
            )
            print(f"    ✓ 追加检查清单 → skill_002_self_diminishment.md")
        else:
            print(f"    ⏭ skill_002 已含检查清单或 root/003 无此节")

    for f in sorted(root_skills.iterdir()):
        if f.name == "003_self_preservation.md":
            print(f"    ⏭ 已合并到 skill_002，丢弃：{f.name}")
            continue
        if f.suffix == ".md":
            out_name = f"skill_{seq_s:03d}_{f.stem}.md"
            dest = skus_skills / out_name
            content = f.read_text(encoding="utf-8")
            if not content.startswith("---"):
                content = f"---\nname: {f.stem}\ndescription: \n---\n\n" + content
            dest.write_text(content, encoding="utf-8")
            print(f"    ✓ 复制 Skill MD → {out_name}")
            seq_s += 1

    # 删除 root facts/ 和 skills/
    shutil.rmtree(root_facts)
    shutil.rmtree(root_skills)
    print(f"    🗑 删除 root facts/ 和 skills/")


# ─────────────────────────────────────────────
# 3. 处理异常的 chapter_ 空目录
# ─────────────────────────────────────────────

def cleanup_anomalous_chapter(chapters_dir: Path) -> None:
    anomaly = chapters_dir / "chapter_"
    if anomaly.exists() and anomaly.is_dir():
        shutil.rmtree(anomaly)
        print(f"\n  🗑 删除异常目录：chapter_/")


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────

def main():
    print("=== ontology-v2 结构修复 ===\n")

    # 1. 合并 eureka 文件夹
    for ch_name in ("chapter_018", "chapter_053"):
        ch = CHAPTERS / ch_name
        merge_eureka_folder(ch)

    # 2. chapter_053 root facts/skills 合并进 skus/
    merge_chapter_053(CHAPTERS / "chapter_053")

    # 3. 删除异常 chapter_ 目录
    cleanup_anomalous_chapter(CHAPTERS)

    # 4. 删除所有空目录
    print("\n=== 清理空目录 ===")
    n = delete_empty_dirs(CHAPTERS)
    print(f"\n共删除 {n} 个空目录")

    print("\n✅ 结构修复完成")


if __name__ == "__main__":
    main()
