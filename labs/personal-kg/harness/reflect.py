"""Reflection loop: check entity extraction quality and patch SKILLs."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

from .db import get_conn, get_segments, log_reflection, upsert_entity, insert_entity_mention
from .model import LocalModel, load_config
from .pipeline import load_skill, _setup_log
from .skill_patch import patch_skill

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:8]


def _get_segment_text_and_entities(conn: Any, session_id: int, seg: Any) -> tuple[str, list[dict]]:
    """Fetch cleaned text and existing entities for a segment."""
    lines = conn.execute(
        "SELECT cleaned_text, text FROM utterances"
        " WHERE session_id=? AND seq BETWEEN ? AND ? ORDER BY seq",
        (session_id, seg["start_seq"], seg["end_seq"]),
    ).fetchall()
    text = " ".join(r["cleaned_text"] or r["text"] for r in lines if (r["cleaned_text"] or r["text"]).strip())

    mentions = conn.execute(
        "SELECT e.name, e.type, em.context"
        " FROM entity_mentions em JOIN entities e ON e.id=em.entity_id"
        " WHERE em.segment_id=?",
        (seg["id"],),
    ).fetchall()
    entities = [
        {"type": r["type"], "name": r["name"], "evidence": r["context"]}
        for r in mentions
    ]
    return text, entities


def reflect_session(
    session_id: int,
    config: dict[str, Any] | None = None,
    max_rounds: int | None = None,
) -> dict[str, Any]:
    if config is None:
        config = load_config()

    db_path = PROJECT_ROOT / config.get("db", {}).get("path", "kg.db")
    skills_dir = PROJECT_ROOT / config.get("skill_dir", "skills")
    pipe_cfg = config.get("pipeline", {})
    skill_cfg = config.get("skill_management", {})
    max_rules = int(skill_cfg.get("max_rules_per_skill", 20))

    if max_rounds is None:
        max_rounds = int(pipe_cfg.get("reflect", {}).get("max_rounds", 3))
    max_rounds = max(1, max_rounds)  # 至少1轮

    model = LocalModel(config)
    reflect_skill = load_skill("SKILL-反思", skills_dir)
    extract_skill = load_skill("SKILL-实体提取", skills_dir)

    log = _setup_log("reflect")

    total_fixed = 0
    round_num = 0
    all_remaining: list[dict] = []
    accumulated_errors: list[dict] = []

    with get_conn(db_path) as conn:
        segments = get_segments(conn, session_id)

        if not segments:
            log.info("Session %d has no segments, skipping reflection", session_id)
            return {
                "session_id": session_id,
                "rounds_run": 0,
                "total_fixed": 0,
                "remaining_errors": [],
                "skill_patched": False,
            }

        for round_num in range(1, max_rounds + 1):
            round_errors = 0
            round_fixed = 0
            log.info("Reflect round %d/%d for session %d", round_num, max_rounds, session_id)

            for seg in segments:
                try:
                    text, entities = _get_segment_text_and_entities(conn, session_id, seg)
                except Exception as exc:
                    log.warning("Failed to load segment %d: %s", seg["seg_idx"], exc)
                    continue
                if not text:
                    continue

                # Ask model to reflect
                try:
                    payload = json.dumps({"text": text, "entities": entities}, ensure_ascii=False)
                    result = model.chat_json(payload, system=reflect_skill)
                except Exception as exc:
                    log.warning("Reflect model call failed for segment %d: %s", seg["seg_idx"], exc)
                    continue

                if not isinstance(result, dict) or "pass" not in result:
                    log.warning("Reflect parse failed for segment %d", seg["seg_idx"])
                    continue

                if result.get("pass") is True:
                    continue

                errors: list[dict] = result.get("errors", [])
                round_errors += len(errors)
                accumulated_errors.extend(errors)

                # Re-extract with current (possibly updated) SKILL
                try:
                    re_result = model.chat_json(
                        json.dumps({"text": text}, ensure_ascii=False),
                        system=extract_skill,
                    )
                except Exception as exc:
                    log.warning("Re-extract model call failed for segment %d: %s", seg["seg_idx"], exc)
                    continue

                if isinstance(re_result, dict) and "entities" in re_result:
                    conn.execute(
                        "DELETE FROM entity_mentions WHERE segment_id=?", (seg["id"],)
                    )
                    for ent in re_result["entities"]:
                        etype = ent.get("type", "")
                        ename = ent.get("name", "").strip()
                        if not etype or not ename:
                            continue
                        eid = upsert_entity(conn, ename, etype)
                        insert_entity_mention(conn, eid, seg["id"], ent.get("evidence", ""))
                    conn.commit()  # 确保每个修复的segment立即持久化
                    round_fixed += 1
                    total_fixed += 1

            log_reflection(conn, session_id, "extract", round_num,
                           round_errors, round_fixed)
            log.info("Round %d: %d errors, %d segments re-extracted", round_num, round_errors, round_fixed)

            if round_errors == 0:
                log.info("All segments passed reflection at round %d", round_num)
                break

            # Reload skills in case they were patched
            reflect_skill = load_skill("SKILL-反思", skills_dir)
            extract_skill = load_skill("SKILL-实体提取", skills_dir)

        # Patch SKILL-实体提取 with accumulated errors
        if accumulated_errors:
            patched = patch_skill(
                "SKILL-实体提取",
                accumulated_errors,
                skills_dir,
                db_path,
                max_rules=max_rules,
            )
            if patched:
                log.info("SKILL-实体提取 updated with %d error patterns", len(accumulated_errors))

        all_remaining = [
            e for seg in segments
            for e in _check_remaining(conn, session_id, seg, model, reflect_skill)
        ]

    return {
        "session_id": session_id,
        "rounds_run": round_num,
        "total_fixed": total_fixed,
        "remaining_errors": all_remaining[:20],
        "skill_patched": bool(accumulated_errors),
    }


def _check_remaining(conn: Any, session_id: int, seg: Any, model: LocalModel, skill: str) -> list[dict]:
    """Final pass check — returns any still-failing errors."""
    text, entities = _get_segment_text_and_entities(conn, session_id, seg)
    if not text:
        return []
    payload = json.dumps({"text": text, "entities": entities}, ensure_ascii=False)
    result = model.chat_json(payload, system=skill)
    if isinstance(result, dict) and result.get("pass") is False:
        return result.get("errors", [])
    return []
