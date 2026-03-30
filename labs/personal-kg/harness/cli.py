"""Command-line interface for personal-kg."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT.parent.parent))  # reach shiji-kb root if needed


def cmd_process(args: argparse.Namespace) -> None:
    from harness.model import load_config
    from harness.pipeline import process_file
    from harness.reflect import reflect_session

    config = load_config(PROJECT_ROOT / "harness" / "config.yaml")
    src = Path(args.file)
    if not src.is_absolute():
        src = PROJECT_ROOT / src

    print(f"Processing {src} ...")
    result = process_file(src, config)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if config.get("pipeline", {}).get("reflect", {}).get("enabled", True):
        print("\nRunning reflection loop ...")
        reflect_result = reflect_session(result["session_id"], config)
        print(json.dumps(reflect_result, ensure_ascii=False, indent=2))


def cmd_query(args: argparse.Namespace) -> None:
    import sqlite3
    from harness.model import load_config

    config = load_config(PROJECT_ROOT / "harness" / "config.yaml")
    db_path = PROJECT_ROOT / config.get("db", {}).get("path", "kg.db")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(args.sql).fetchall()
        if not rows:
            print("(no results)")
            return
        keys = rows[0].keys()
        # header
        widths = {k: max(len(k), max(len(str(r[k])) for r in rows)) for k in keys}
        fmt = "  ".join(f"{{:<{widths[k]}}}" for k in keys)
        print(fmt.format(*keys))
        print("  ".join("-" * widths[k] for k in keys))
        for row in rows:
            print(fmt.format(*[str(row[k]) for k in keys]))
    except Exception as e:
        print(f"Query error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


def cmd_status(args: argparse.Namespace) -> None:
    from harness.model import load_config
    from harness.db import get_conn, get_stats, init_db

    config = load_config(PROJECT_ROOT / "harness" / "config.yaml")
    db_path = PROJECT_ROOT / config.get("db", {}).get("path", "kg.db")
    init_db(db_path)

    with get_conn(db_path) as conn:
        stats = get_stats(conn)

    print("=== Knowledge Graph Status ===")
    for k, v in stats.items():
        if k == "entities_by_type":
            print(f"  entities by type:")
            for t, n in v.items():
                print(f"    {t:12} {n}")
        else:
            print(f"  {k:20} {v}")


def cmd_test_model(args: argparse.Namespace) -> None:
    from harness.model import LocalModel, load_config

    config = load_config(PROJECT_ROOT / "harness" / "config.yaml")
    model = LocalModel(config)
    result = model.test_connection()
    if result["ok"]:
        print(f"✓ Model OK: {result['response'][:100]}")
    else:
        print(f"✗ Model FAILED: {result['error']}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(prog="personal-kg", description="Personal Recording KG")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("process", help="Process a txt file into the knowledge graph")
    p.add_argument("file", help="Path to input .txt file")

    q = sub.add_parser("query", help="Run a SQL query on the knowledge graph")
    q.add_argument("sql", help="SQL statement")

    sub.add_parser("status", help="Show knowledge graph statistics")
    sub.add_parser("test-model", help="Test connection to local model")

    args = parser.parse_args()
    {
        "process": cmd_process,
        "query": cmd_query,
        "status": cmd_status,
        "test-model": cmd_test_model,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
