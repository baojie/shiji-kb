"""Append learned rules to SKILL documents and manage version tracking."""
from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from typing import Any

from .db import get_conn

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# check_id → 规则前缀模板
_CHECK_TEMPLATES = {
    1: "禁止遗漏person实体",
    2: "禁止把时间词标为location",
    3: "activity主语必须是说话人自己",
    4: "emotion必须有原文词语支撑",
    5: "decision必须是已决定事项，不确定表达不算",
    6: "question必须是未解决的疑问",
    7: "禁止重复标注同一实体",
    8: "evidence必须来自原文",
    9: "注意",  # 开放错误
}

_RULE_SECTION = "# 禁止规则区"


def _current_rules(content: str) -> list[str]:
    """Extract existing rules from the 禁止规则区 section."""
    idx = content.find(_RULE_SECTION)
    if idx == -1:
        return []
    after = content[idx + len(_RULE_SECTION):]
    rules = [
        line.strip()
        for line in after.splitlines()
        if line.strip().startswith("-")
    ]
    return rules


def _rule_count(content: str) -> int:
    return len(_current_rules(content))


def _make_rule(check_id: int, detail: str, version: str, date: str) -> str:
    prefix = _CHECK_TEMPLATES.get(check_id, "注意")
    return f"- [v{version} {date}] {prefix}：{detail}"


def _bump_version(version: str) -> str:
    """Increment the minor version: '1.0' → '1.1', '1.9' → '1.10'."""
    parts = version.split(".")
    if len(parts) == 2 and parts[1].isdigit():
        return f"{parts[0]}.{int(parts[1]) + 1}"
    return version + ".1"


def _update_frontmatter_version(content: str, new_version: str, date: str) -> str:
    content = re.sub(r"(version:\s*)[\d.]+", f"\\g<1>{new_version}", content)
    content = re.sub(r"(last_updated:\s*)[\d-]+", f"\\g<1>{date}", content)
    return content


def _distill_rules(rules: list[str], max_rules: int) -> list[str]:
    """
    Simple distillation: deduplicate by prefix similarity, keep latest N.
    Real production version would call the LLM to merge rules.
    """
    seen_prefixes: set[str] = set()
    deduped: list[str] = []
    for rule in reversed(rules):  # newest first
        prefix = re.sub(r"\[v[\d.]+ [\d-]+\]", "", rule)[:30]
        if prefix not in seen_prefixes:
            seen_prefixes.add(prefix)
            deduped.append(rule)
    # keep max_rules newest
    return list(reversed(deduped[:max_rules]))


def patch_skill(
    skill_name: str,
    errors: list[dict],
    skills_dir: Path,
    db_path: Path,
    max_rules: int = 20,
) -> bool:
    """
    Append new prohibition rules from reflection errors to the SKILL document.
    Returns True if the file was modified.
    """
    path = skills_dir / f"{skill_name}.md"
    if not path.exists():
        return False

    content = path.read_text(encoding="utf-8")
    existing_rules = _current_rules(content)
    date = time.strftime("%Y-%m-%d")

    # Extract current version
    m = re.search(r"version:\s*([\d.]+)", content)
    version = m.group(1) if m else "1.0"

    new_rules: list[str] = []
    seen_details: set[str] = set()  # dedup within this batch too
    for err in errors:
        check_id = int(err.get("check_id", 9))
        detail = str(err.get("detail", "")).strip()
        if not detail:
            continue
        detail_lower = detail.lower()
        # Idempotency: skip if similar rule already in file OR in this batch
        already_in_file = any(detail_lower in r.lower() for r in existing_rules)
        already_in_batch = detail_lower in seen_details
        if already_in_file or already_in_batch:
            continue
        seen_details.add(detail_lower)
        new_rules.append(_make_rule(check_id, detail, version, date))

    if not new_rules:
        return False

    # Append rules to section
    all_rules = existing_rules + new_rules

    # Distill if over limit
    if len(all_rules) > max_rules:
        all_rules = _distill_rules(all_rules, max_rules)

    # Rebuild the 禁止规则区 section
    idx = content.find(_RULE_SECTION)
    if idx == -1:
        content += f"\n\n{_RULE_SECTION}\n"
        idx = content.find(_RULE_SECTION)

    before = content[: idx + len(_RULE_SECTION)]
    rules_block = "\n" + "\n".join(all_rules)
    after_section = content[idx + len(_RULE_SECTION):]
    # Strip old rules from after_section (everything up to next ## heading or EOF)
    after_section = re.sub(r"^[\s\S]*?(?=\n##|\Z)", "", after_section)
    content = before + rules_block + after_section

    # Bump version
    new_version = _bump_version(version)
    content = _update_frontmatter_version(content, new_version, date)

    path.write_text(content, encoding="utf-8")

    # Record in DB
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO skill_versions(skill_name,version,content_hash,applied_at)"
            " VALUES (?,?,?,?)",
            (skill_name, new_version, content_hash, time.strftime("%Y-%m-%dT%H:%M:%S")),
        )
        conn.commit()

    return True
