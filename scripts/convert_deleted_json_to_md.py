#!/usr/bin/env python3
"""
将 git 历史中已删除的 JSON facts 转换为同名 .md 文件。
只处理当前工作区中不存在对应 .md 文件的情况（避免覆盖已有内容）。
"""
import subprocess
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def json_to_markdown(data, level=2) -> str:
    """递归将 JSON 数据结构转为 Markdown 文本。"""
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
                lines.append(json_to_markdown(item, level))
            else:
                lines.append(f"- {item}")
        return "\n".join(lines)
    if isinstance(data, dict):
        lines = []
        for key, val in data.items():
            if isinstance(val, dict):
                lines.append(f"{'#' * level} {key}\n")
                lines.append(json_to_markdown(val, level + 1))
            elif isinstance(val, list):
                lines.append(f"**{key}**：")
                for item in val:
                    if isinstance(item, (dict, list)):
                        lines.append(json_to_markdown(item, level + 1))
                    else:
                        lines.append(f"- {item}")
            else:
                lines.append(f"- **{key}**：{val}")
        return "\n".join(lines)
    return str(data)


def convert_json_to_md(json_path_in_git: str, json_content: str, md_path: Path):
    """将 JSON 内容转换为 .md 并写入文件。"""
    try:
        obj = json.loads(json_content)
    except json.JSONDecodeError as e:
        print(f"  ⚠ JSON 解析失败：{e}")
        return False

    name = obj.get("name", md_path.stem)
    description = obj.get("description", "")
    data = obj.get("data", {})

    # 构建 markdown
    lines = [
        "---",
        f"name: {name}",
        f"description: {description}",
        "---",
        "",
        f"# {description or name}",
        "",
    ]

    # 处理顶层非 data 字段（除 name/description 外）
    extra_fields = {k: v for k, v in obj.items() if k not in ("name", "description", "data")}

    if isinstance(data, dict):
        for key, val in data.items():
            lines.append(f"## {key}")
            lines.append("")
            lines.append(json_to_markdown(val, level=3))
            lines.append("")
    elif isinstance(data, list):
        lines.append(json_to_markdown(data, level=2))
        lines.append("")
    elif data:
        lines.append(str(data))
        lines.append("")

    # 追加额外顶层字段
    if extra_fields:
        lines.append("## 附加信息")
        lines.append("")
        lines.append(json_to_markdown(extra_fields, level=3))
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return True


def main():
    # 获取所有被删除的 json 文件（相对于 HEAD）
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    deleted_jsons = []
    for line in result.stdout.splitlines():
        # " D path" 或 "D  path"
        status = line[:2]
        path = line[3:].strip()
        if "D" in status and path.endswith(".json") and "ontology-v2" in path:
            deleted_jsons.append(path)

    if not deleted_jsons:
        print("没有找到已删除的 JSON 文件。")
        return

    print(f"找到 {len(deleted_jsons)} 个已删除的 JSON 文件，开始转换...\n")

    converted = 0
    skipped = 0
    failed = 0

    for rel_path in deleted_jsons:
        json_git_path = rel_path
        md_path = REPO_ROOT / rel_path.replace(".json", ".md")

        # 如果 .md 已存在，跳过（append-only 原则）
        if md_path.exists():
            print(f"  ⏭ 已存在，跳过：{rel_path.replace('.json', '.md')}")
            skipped += 1
            continue

        # 从 git HEAD 读取被删文件内容
        git_result = subprocess.run(
            ["git", "show", f"HEAD:{json_git_path}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if git_result.returncode != 0:
            print(f"  ✗ 无法从 git 读取：{rel_path}")
            failed += 1
            continue

        print(f"  → 转换：{rel_path}")
        ok = convert_json_to_md(json_git_path, git_result.stdout, md_path)
        if ok:
            converted += 1
        else:
            failed += 1

    print(f"\n完成：转换 {converted} 个，跳过 {skipped} 个，失败 {failed} 个。")


if __name__ == "__main__":
    main()
