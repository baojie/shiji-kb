"""SQLite knowledge graph — schema and operations."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_DDL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'processing'
);

CREATE TABLE IF NOT EXISTS utterances (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER NOT NULL REFERENCES sessions(id),
    seq          INTEGER NOT NULL,
    text         TEXT NOT NULL,
    cleaned_text TEXT
);

CREATE TABLE IF NOT EXISTS segments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES sessions(id),
    seg_idx     INTEGER NOT NULL,
    start_seq   INTEGER NOT NULL,
    end_seq     INTEGER NOT NULL,
    topic_label TEXT,
    summary     TEXT
);

CREATE TABLE IF NOT EXISTS entities (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    type           TEXT NOT NULL,  -- person/activity/location/emotion/decision/question
    canonical_name TEXT,           -- 人物追踪后的规范名
    first_seen     TEXT NOT NULL,
    last_seen      TEXT NOT NULL,
    mention_count  INTEGER NOT NULL DEFAULT 1,
    UNIQUE(name, type)
);

CREATE TABLE IF NOT EXISTS person_aliases (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id        INTEGER NOT NULL REFERENCES entities(id),
    alias            TEXT NOT NULL,
    first_segment_id INTEGER,
    confidence       REAL NOT NULL DEFAULT 1.0,
    UNIQUE(alias)
);

CREATE TABLE IF NOT EXISTS entity_mentions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id  INTEGER NOT NULL REFERENCES entities(id),
    segment_id INTEGER NOT NULL REFERENCES segments(id),
    context    TEXT
);

CREATE TABLE IF NOT EXISTS relations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    from_entity  TEXT NOT NULL,
    to_entity    TEXT NOT NULL,
    rel_type     TEXT NOT NULL,  -- 共同出现 / 参与 / 别名
    weight       INTEGER NOT NULL DEFAULT 1,
    first_seen   TEXT NOT NULL,
    last_seen    TEXT NOT NULL,
    UNIQUE(from_entity, to_entity, rel_type)
);

CREATE TABLE IF NOT EXISTS skill_versions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name  TEXT NOT NULL,
    version     TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    applied_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reflection_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL REFERENCES sessions(id),
    stage           TEXT NOT NULL,
    round_num       INTEGER NOT NULL,
    input_hash      TEXT,
    errors_found    INTEGER NOT NULL DEFAULT 0,
    patches_applied INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL
);
"""


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def get_conn(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path) -> None:
    """Create all tables (idempotent)."""
    with get_conn(db_path) as conn:
        conn.executescript(_DDL)


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

def insert_session(conn: sqlite3.Connection, source_file: str) -> int:
    cur = conn.execute(
        "INSERT INTO sessions(source_file, created_at, status) VALUES (?,?,?)",
        (source_file, _now(), "processing"),
    )
    conn.commit()
    return cur.lastrowid


def update_session_status(conn: sqlite3.Connection, session_id: int, status: str) -> None:
    conn.execute("UPDATE sessions SET status=? WHERE id=?", (status, session_id))
    conn.commit()


# ---------------------------------------------------------------------------
# Utterances
# ---------------------------------------------------------------------------

def insert_utterances(
    conn: sqlite3.Connection, session_id: int, lines: list[str]
) -> list[int]:
    ids = []
    for seq, text in enumerate(lines):
        cur = conn.execute(
            "INSERT INTO utterances(session_id, seq, text) VALUES (?,?,?)",
            (session_id, seq, text),
        )
        ids.append(cur.lastrowid)
    conn.commit()
    return ids


def update_cleaned(
    conn: sqlite3.Connection, session_id: int, cleaned: list[str]
) -> None:
    rows = conn.execute(
        "SELECT id, seq FROM utterances WHERE session_id=? ORDER BY seq",
        (session_id,),
    ).fetchall()
    for row in rows:
        idx = row["seq"]
        if idx < len(cleaned):
            conn.execute(
                "UPDATE utterances SET cleaned_text=? WHERE id=?",
                (cleaned[idx], row["id"]),
            )
    conn.commit()


def get_cleaned_lines(conn: sqlite3.Connection, session_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT cleaned_text, text FROM utterances WHERE session_id=? ORDER BY seq",
        (session_id,),
    ).fetchall()
    return [r["cleaned_text"] or r["text"] for r in rows]


# ---------------------------------------------------------------------------
# Segments
# ---------------------------------------------------------------------------

def insert_segment(
    conn: sqlite3.Connection,
    session_id: int,
    seg_idx: int,
    start_seq: int,
    end_seq: int,
    topic_label: str | None = None,
    summary: str | None = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO segments(session_id,seg_idx,start_seq,end_seq,topic_label,summary)"
        " VALUES (?,?,?,?,?,?)",
        (session_id, seg_idx, start_seq, end_seq, topic_label, summary),
    )
    conn.commit()
    return cur.lastrowid


def get_segments(conn: sqlite3.Connection, session_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM segments WHERE session_id=? ORDER BY seg_idx",
        (session_id,),
    ).fetchall()


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

def upsert_entity(
    conn: sqlite3.Connection,
    name: str,
    etype: str,
    canonical_name: str | None = None,
) -> int:
    now = _now()
    existing = conn.execute(
        "SELECT id FROM entities WHERE name=? AND type=?", (name, etype)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE entities SET mention_count=mention_count+1, last_seen=?"
            " WHERE id=?",
            (now, existing["id"]),
        )
        conn.commit()
        return existing["id"]
    cur = conn.execute(
        "INSERT INTO entities(name,type,canonical_name,first_seen,last_seen)"
        " VALUES (?,?,?,?,?)",
        (name, etype, canonical_name or name, now, now),
    )
    conn.commit()
    return cur.lastrowid


def insert_entity_mention(
    conn: sqlite3.Connection, entity_id: int, segment_id: int, context: str
) -> None:
    conn.execute(
        "INSERT INTO entity_mentions(entity_id,segment_id,context) VALUES (?,?,?)",
        (entity_id, segment_id, context),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Person aliases
# ---------------------------------------------------------------------------

def upsert_alias(
    conn: sqlite3.Connection,
    entity_id: int,
    alias: str,
    first_segment_id: int | None = None,
    confidence: float = 1.0,
) -> None:
    existing = conn.execute(
        "SELECT id FROM person_aliases WHERE alias=?", (alias,)
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO person_aliases(entity_id,alias,first_segment_id,confidence)"
            " VALUES (?,?,?,?)",
            (entity_id, alias, first_segment_id, confidence),
        )
        conn.commit()


def get_aliases_for_entity(
    conn: sqlite3.Connection, entity_id: int
) -> list[str]:
    rows = conn.execute(
        "SELECT alias FROM person_aliases WHERE entity_id=?", (entity_id,)
    ).fetchall()
    return [r["alias"] for r in rows]


# ---------------------------------------------------------------------------
# Relations
# ---------------------------------------------------------------------------

def upsert_relation(
    conn: sqlite3.Connection,
    from_entity: str,
    to_entity: str,
    rel_type: str,
) -> None:
    now = _now()
    existing = conn.execute(
        "SELECT id FROM relations WHERE from_entity=? AND to_entity=? AND rel_type=?",
        (from_entity, to_entity, rel_type),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE relations SET weight=weight+1, last_seen=? WHERE id=?",
            (now, existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO relations(from_entity,to_entity,rel_type,weight,first_seen,last_seen)"
            " VALUES (?,?,?,1,?,?)",
            (from_entity, to_entity, rel_type, now, now),
        )
    conn.commit()


# ---------------------------------------------------------------------------
# Reflection log
# ---------------------------------------------------------------------------

def log_reflection(
    conn: sqlite3.Connection,
    session_id: int,
    stage: str,
    round_num: int,
    errors_found: int,
    patches_applied: int,
    input_hash: str | None = None,
) -> None:
    conn.execute(
        "INSERT INTO reflection_log"
        "(session_id,stage,round_num,input_hash,errors_found,patches_applied,created_at)"
        " VALUES (?,?,?,?,?,?,?)",
        (session_id, stage, round_num, input_hash, errors_found, patches_applied, _now()),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def get_stats(conn: sqlite3.Connection) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    for table in ("sessions", "utterances", "segments", "entities", "relations"):
        stats[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    by_type = conn.execute(
        "SELECT type, COUNT(*) as n FROM entities GROUP BY type"
    ).fetchall()
    stats["entities_by_type"] = {r["type"]: r["n"] for r in by_type}
    return stats
