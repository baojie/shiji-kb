"""Main processing pipeline: audio/txt file → knowledge graph."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from .asr import ASRClient, is_audio_file
from .db import (
    get_cleaned_lines,
    get_segments,
    init_db,
    insert_entity_mention,
    insert_segment,
    insert_session,
    insert_utterances,
    update_cleaned,
    update_session_status,
    upsert_alias,
    upsert_entity,
    upsert_relation,
    get_conn,
)
from .model import LocalModel, load_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _setup_log(name: str) -> logging.Logger:
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    today = time.strftime("%Y-%m-%d")
    handler = logging.FileHandler(log_dir / f"pipeline_{today}.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(handler)
        logger.addHandler(logging.StreamHandler())
    return logger


def load_skill(skill_name: str, skills_dir: Path) -> str:
    """Return full content of a SKILL markdown file."""
    path = skills_dir / f"{skill_name}.md"
    if not path.exists():
        raise FileNotFoundError(f"SKILL not found: {path}")
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Step 2 — Clean
# ---------------------------------------------------------------------------

def _step_clean(
    session_id: int,
    lines: list[str],
    model: LocalModel,
    skill: str,
    batch_size: int,
    conn: Any,
    log: logging.Logger,
) -> None:
    t0 = time.perf_counter()
    cleaned: list[str] = []

    for i in range(0, len(lines), batch_size):
        batch = lines[i: i + batch_size]
        result = model.chat_json(
            json.dumps({"lines": batch}, ensure_ascii=False),
            system=skill,
        )
        if isinstance(result, dict) and "cleaned" in result:
            batch_cleaned = result["cleaned"]
            if len(batch_cleaned) == len(batch):
                cleaned.extend(batch_cleaned)
            else:
                # 行数不匹配：逐行对齐，多余丢弃，不足用原文补
                log.warning("Clean batch %d line count mismatch (%d vs %d), aligning",
                            i // batch_size, len(batch_cleaned), len(batch))
                for j in range(len(batch)):
                    cleaned.append(batch_cleaned[j] if j < len(batch_cleaned) else batch[j])
        else:
            log.warning("Clean batch %d parse failed, using originals", i // batch_size)
            cleaned.extend(batch)

    update_cleaned(conn, session_id, cleaned)
    log.info("Step2 clean: %d lines, %.1fs", len(lines), time.perf_counter() - t0)


# ---------------------------------------------------------------------------
# Step 3 — Segment
# ---------------------------------------------------------------------------

def _step_segment(
    session_id: int,
    lines: list[str],
    model: LocalModel,
    skill: str,
    max_lines: int,
    conn: Any,
    log: logging.Logger,
) -> list[int]:
    """Returns list of inserted segment IDs."""
    t0 = time.perf_counter()
    segment_ids: list[int] = []
    seg_idx = 0

    # 分批送给模型，每批 max_lines 行
    i = 0
    while i < len(lines):
        batch = lines[i: i + max_lines]
        payload = json.dumps(
            {"lines": batch, "line_start_idx": i}, ensure_ascii=False
        )
        result = model.chat_json(payload, system=skill)

        if isinstance(result, dict) and "segments" in result:
            for seg in result["segments"]:
                raw_start = int(seg.get("start", 0))
                raw_end = int(seg.get("end", len(batch) - 1))
                # 模型可能返回相对索引（从0开始）或绝对索引
                # 如果 start < i，说明是相对索引，需要加偏移
                if raw_start < i:
                    raw_start += i
                    raw_end += i
                # 安全边界：不超过总行数
                start = max(i, min(raw_start, len(lines) - 1))
                end = max(start, min(raw_end, len(lines) - 1))
                label = seg.get("topic_hint", "")
                sid = insert_segment(conn, session_id, seg_idx, start, end, label)
                segment_ids.append(sid)
                seg_idx += 1
            # 下一批从当前批次末尾继续
            i += len(batch)
        else:
            log.warning("Segment batch at line %d parse failed, using full batch", i)
            sid = insert_segment(conn, session_id, seg_idx, i, i + len(batch) - 1, "未分段")
            segment_ids.append(sid)
            seg_idx += 1
            i += len(batch)

    log.info("Step3 segment: %d segments, %.1fs", len(segment_ids), time.perf_counter() - t0)
    return segment_ids


# ---------------------------------------------------------------------------
# Step 4 — Extract entities
# ---------------------------------------------------------------------------

def _step_extract(
    session_id: int,
    lines: list[str],
    model: LocalModel,
    skill: str,
    conn: Any,
    log: logging.Logger,
) -> dict[int, list[dict]]:
    """Returns {segment_id: [entity_dict, ...]}"""
    t0 = time.perf_counter()
    segments = get_segments(conn, session_id)
    seg_entities: dict[int, list[dict]] = {}

    for seg in segments:
        seg_lines = lines[seg["start_seq"]: seg["end_seq"] + 1]
        text = " ".join(l for l in seg_lines if l.strip())
        if not text:
            continue

        result = model.chat_json(
            json.dumps({"text": text}, ensure_ascii=False),
            system=skill,
        )

        entities: list[dict] = []
        if isinstance(result, dict) and "entities" in result:
            entities = result["entities"]
        else:
            log.warning("Extract failed for segment %d", seg["seg_idx"])

        seg_entities[seg["id"]] = entities

        # 写入DB
        for ent in entities:
            etype = ent.get("type", "")
            ename = ent.get("name", "").strip()
            if not etype or not ename:
                continue
            entity_id = upsert_entity(conn, ename, etype)
            insert_entity_mention(conn, entity_id, seg["id"], ent.get("evidence", ""))

    log.info("Step4 extract: %d segments processed, %.1fs",
             len(segments), time.perf_counter() - t0)
    return seg_entities


# ---------------------------------------------------------------------------
# Step 4.5 — Track persons across segments
# ---------------------------------------------------------------------------

def _step_track_persons(
    session_id: int,
    seg_entities: dict[int, list[dict]],
    model: LocalModel,
    skill: str,
    conn: Any,
    log: logging.Logger,
) -> None:
    t0 = time.perf_counter()

    # 收集所有 person 实体，附带 ASR speaker_id 提示（如果有）
    all_persons: list[dict] = []
    for seg_id, entities in seg_entities.items():
        # 查这个 segment 里出现过哪些 speaker_id
        asr_speakers = list({
            r["speaker_id"]
            for r in conn.execute(
                "SELECT DISTINCT u.speaker_id FROM utterances u"
                " JOIN segments s ON s.session_id=u.session_id"
                " AND u.seq BETWEEN s.start_seq AND s.end_seq"
                " WHERE s.id=? AND u.speaker_id IS NOT NULL",
                (seg_id,),
            ).fetchall()
            if r["speaker_id"]
        })
        for ent in entities:
            if ent.get("type") == "person":
                all_persons.append({
                    "name": ent["name"],
                    "segment_id": seg_id,
                    "context": ent.get("evidence", ""),
                    "asr_speakers": asr_speakers,  # 提示：该段涉及哪些 ASR 说话人
                })

    if not all_persons:
        return

    result = model.chat_json(
        json.dumps({"persons": all_persons}, ensure_ascii=False),
        system=skill,
    )

    if not (isinstance(result, dict) and "groups" in result):
        log.warning("Person tracking parse failed")
        return

    for group in result["groups"]:
        canonical = group.get("canonical_name", "").strip()
        aliases: list[str] = group.get("aliases", [])
        if not canonical:
            continue

        # 确保规范名在 entities 表存在
        canonical_id = upsert_entity(conn, canonical, "person", canonical)

        # 注册所有别名
        for alias in aliases:
            alias = alias.strip()
            if alias and alias != canonical:
                upsert_alias(conn, canonical_id, alias)
                # 把别名指向的旧实体关系也建一条 alias 关系
                upsert_relation(conn, alias, canonical, "别名")

    log.info("Step4.5 track_persons: %d groups, %.1fs",
             len(result.get("groups", [])), time.perf_counter() - t0)


# ---------------------------------------------------------------------------
# Step 5 — Build relations (rule-based, no model call)
# ---------------------------------------------------------------------------

# 过滤过于泛化的实体名（不进入关系表）
_NOISE_NAMES = {"他", "她", "它", "他们", "她们", "客户", "同事", "财务", "朋友",
                "说", "问", "做", "看", "听", "改", "想", "走", "坐", "站",
                "吃", "喝", "写", "跑", "叫", "算", "排队", "叫住"}


def _step_relations(
    session_id: int,
    seg_entities: dict[int, list[dict]],
    conn: Any,
    log: logging.Logger,
) -> None:
    t0 = time.perf_counter()
    total = 0
    for seg_id, entities in seg_entities.items():
        persons = [e["name"] for e in entities
                   if e.get("type") == "person" and e["name"] not in _NOISE_NAMES]
        activities = [e["name"] for e in entities
                      if e.get("type") == "activity" and e["name"] not in _NOISE_NAMES
                      and len(e["name"]) >= 2]

        # 人物共同出现
        for i in range(len(persons)):
            for j in range(i + 1, len(persons)):
                a, b = sorted([persons[i], persons[j]])
                upsert_relation(conn, a, b, "共同出现")
                total += 1

        # 人物参与活动（第一人称，隐含主语是"我"）
        for act in activities:
            for p in persons:
                upsert_relation(conn, p, act, "参与")
                total += 1

    log.info("Step5 relations: %d relation updates, %.1fs",
             total, time.perf_counter() - t0)


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def process_file(
    source_file: str | Path,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_file = Path(source_file)
    if config is None:
        config = load_config()

    db_path = PROJECT_ROOT / config.get("db", {}).get("path", "kg.db")
    skills_dir = PROJECT_ROOT / config.get("skill_dir", "skills")
    pipe_cfg = config.get("pipeline", {})
    batch_size = pipe_cfg.get("clean", {}).get("batch_size", 30)
    max_seg = pipe_cfg.get("segment", {}).get("max_lines_per_segment", 30)

    init_db(db_path)
    log = _setup_log("pipeline")
    model = LocalModel(config)

    # Step 0 — transcribe if input is audio
    asr_utterances: list[dict] | None = None
    if is_audio_file(source_file):
        if not pipe_cfg.get("asr", {}).get("enabled", True):
            raise ValueError(f"Audio input given but asr.enabled=false in config: {source_file}")
        log.info("Step0 ASR: transcribing %s", source_file.name)
        t0 = time.perf_counter()
        try:
            asr_client = ASRClient.from_config(config)
            asr_utterances = asr_client.transcribe(source_file)
            log.info("Step0 ASR: %d utterances in %.1fs", len(asr_utterances), time.perf_counter() - t0)
        except Exception as exc:
            log.error("Step0 ASR failed: %s", exc)
            raise

    # Lines for downstream steps: plain text
    if asr_utterances is not None:
        lines: list[str] = [u["text"] for u in asr_utterances]
    else:
        lines = [l for l in source_file.read_text(encoding="utf-8").splitlines()]

    log.info("Processing %s: %d lines", source_file.name, len(lines))

    with get_conn(db_path) as conn:
        session_id = insert_session(conn, str(source_file))

        # Step 1 — insert raw utterances (with ASR metadata if available)
        insert_utterances(conn, session_id, asr_utterances if asr_utterances is not None else lines)

        errors: list[str] = []

        # Step 2 — clean
        if pipe_cfg.get("clean", {}).get("enabled", True):
            try:
                _step_clean(session_id, lines, model,
                            load_skill("SKILL-清洗", skills_dir),
                            batch_size, conn, log)
            except Exception as e:
                log.error("Step2 failed: %s", e)
                update_session_status(conn, session_id, "error_step2")
                errors.append(f"step2: {e}")

        cleaned = get_cleaned_lines(conn, session_id)

        # Step 3 — segment
        segment_ids: list[int] = []
        if pipe_cfg.get("segment", {}).get("enabled", True):
            try:
                segment_ids = _step_segment(session_id, cleaned, model,
                                            load_skill("SKILL-分割", skills_dir),
                                            max_seg, conn, log)
            except Exception as e:
                log.error("Step3 failed: %s", e)
                update_session_status(conn, session_id, "error_step3")
                errors.append(f"step3: {e}")

        # Step 4 — extract
        seg_entities: dict[int, list[dict]] = {}
        if pipe_cfg.get("extract", {}).get("enabled", True):
            try:
                seg_entities = _step_extract(session_id, cleaned, model,
                                             load_skill("SKILL-实体提取", skills_dir),
                                             conn, log)
            except Exception as e:
                log.error("Step4 failed: %s", e)
                update_session_status(conn, session_id, "error_step4")
                errors.append(f"step4: {e}")

        # Step 4.5 — track persons
        if pipe_cfg.get("track_persons", {}).get("enabled", True) and seg_entities:
            try:
                _step_track_persons(session_id, seg_entities, model,
                                    load_skill("SKILL-人物追踪", skills_dir),
                                    conn, log)
            except Exception as e:
                log.error("Step4.5 failed: %s", e)
                errors.append(f"step4.5: {e}")

        # Step 5 — relations (rule-based)
        if seg_entities:
            try:
                _step_relations(session_id, seg_entities, conn, log)
            except Exception as e:
                log.error("Step5 failed: %s", e)
                errors.append(f"step5: {e}")

        status = "done" if not errors else f"done_with_errors"
        update_session_status(conn, session_id, status)

    log.info("Done: session_id=%d status=%s", session_id, status)
    return {
        "session_id": session_id,
        "status": status,
        "lines": len(lines),
        "segments": len(segment_ids),
        "errors": errors,
    }
