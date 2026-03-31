"""
跑完 process 后执行：python report.py
生成 run_report.txt，把这个文件内容发给 Claude 即可诊断质量问题。
"""
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent / "kg.db"
OUT = Path(__file__).parent / "run_report.txt"


def q(conn, sql, *args):
    return conn.execute(sql, args).fetchall()


def main():
    if not DB.exists():
        print("kg.db not found, run: python -m harness.cli process <file> first")
        sys.exit(1)

    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    lines = []

    def w(*parts):
        lines.append(" ".join(str(p) for p in parts))

    # ── 基础统计 ──────────────────────────────────────────
    w("=== 基础统计 ===")
    for t in ("sessions", "utterances", "segments", "entities", "relations"):
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        w(f"  {t:<20} {n}")

    w("")
    w("=== 实体分类 ===")
    for r in q(conn, "SELECT type, COUNT(*) n FROM entities GROUP BY type ORDER BY n DESC"):
        w(f"  {r['type']:<12} {r['n']}")

    # ── 分段索引检查（诊断 start_seq 是否重置）─────────────
    w("")
    w("=== 分段索引（前15条）===")
    w(f"  {'session':<8} {'seg_idx':<8} {'start_seq':<10} {'end_seq':<8} topic_label")
    rows = q(conn,
        "SELECT s.session_id, s.seg_idx, s.start_seq, s.end_seq, s.topic_label"
        " FROM segments s ORDER BY s.session_id, s.seg_idx LIMIT 15")
    for r in rows:
        w(f"  {r['session_id']:<8} {r['seg_idx']:<8} {r['start_seq']:<10} {r['end_seq']:<8} {r['topic_label'] or ''}")

    # ── activity 样本（重点看是否还有原子动词）─────────────
    w("")
    w("=== activity 实体（按提及次数，前25条）===")
    rows = q(conn,
        "SELECT name, mention_count FROM entities WHERE type='activity'"
        " ORDER BY mention_count DESC, name LIMIT 25")
    for r in rows:
        w(f"  [{r['mention_count']}] {r['name']}")

    # ── decision / question 样本 ─────────────────────────
    w("")
    w("=== decision 实体（前15条）===")
    rows = q(conn,
        "SELECT name, mention_count FROM entities WHERE type='decision'"
        " ORDER BY mention_count DESC LIMIT 15")
    for r in rows:
        w(f"  [{r['mention_count']}] {r['name']}")

    w("")
    w("=== question 实体（前15条）===")
    rows = q(conn,
        "SELECT name, mention_count FROM entities WHERE type='question'"
        " ORDER BY mention_count DESC LIMIT 15")
    for r in rows:
        w(f"  [{r['mention_count']}] {r['name']}")

    # ── person 样本 ──────────────────────────────────────
    w("")
    w("=== person 实体（前20条）===")
    rows = q(conn,
        "SELECT name, mention_count FROM entities WHERE type='person'"
        " ORDER BY mention_count DESC LIMIT 20")
    for r in rows:
        w(f"  [{r['mention_count']}] {r['name']}")

    # ── 关系表（噪音检查）───────────────────────────────
    w("")
    w("=== 关系（weight≥2，前20条）===")
    rows = q(conn,
        "SELECT from_entity, to_entity, rel_type, weight FROM relations"
        " WHERE weight >= 2 ORDER BY weight DESC LIMIT 20")
    for r in rows:
        w(f"  [{r['weight']}] {r['from_entity']} --{r['rel_type']}--> {r['to_entity']}")

    w("")
    w("=== 关系（全部，前30条）===")
    rows = q(conn,
        "SELECT from_entity, to_entity, rel_type, weight FROM relations"
        " ORDER BY weight DESC LIMIT 30")
    for r in rows:
        w(f"  [{r['weight']}] {r['from_entity']} --{r['rel_type']}--> {r['to_entity']}")

    # ── 反思日志 ─────────────────────────────────────────
    w("")
    w("=== 反思日志 ===")
    rows = q(conn,
        "SELECT session_id, stage, round_num, errors_found, patches_applied, created_at"
        " FROM reflection_log ORDER BY session_id, round_num")
    if rows:
        for r in rows:
            w(f"  session={r['session_id']} round={r['round_num']}"
              f" errors={r['errors_found']} fixed={r['patches_applied']} at={r['created_at']}")
    else:
        w("  (无反思记录)")

    # ── SKILL 版本 ────────────────────────────────────────
    w("")
    w("=== SKILL 版本历史 ===")
    rows = q(conn,
        "SELECT skill_name, version, content_hash, applied_at FROM skill_versions"
        " ORDER BY applied_at DESC LIMIT 10")
    if rows:
        for r in rows:
            w(f"  {r['skill_name']} v{r['version']} ({r['content_hash']}) at {r['applied_at']}")
    else:
        w("  (无版本记录)")

    # ── SKILL 文件当前大小 ────────────────────────────────
    w("")
    w("=== SKILL 文件状态 ===")
    skills_dir = Path(__file__).parent / "skills"
    for md in sorted(skills_dir.glob("*.md")):
        content = md.read_text(encoding="utf-8")
        rules = [l.strip() for l in content.splitlines() if l.strip().startswith("- [v")]
        w(f"  {md.name:<30} {md.stat().st_size} bytes  {len(rules)} 禁止规则")

    # ── 最新会话的错误日志（如有）────────────────────────
    w("")
    w("=== 最新 session 的实体 evidence 样本（随机10条）===")
    rows = q(conn,
        "SELECT e.type, e.name, em.context"
        " FROM entity_mentions em JOIN entities e ON e.id=em.entity_id"
        " WHERE em.segment_id IN ("
        "   SELECT id FROM segments WHERE session_id=("
        "     SELECT MAX(id) FROM sessions))"
        " ORDER BY RANDOM() LIMIT 10")
    for r in rows:
        ctx = (r['context'] or '')[:40]
        w(f"  [{r['type']:<8}] {r['name']:<15} | {ctx}")

    conn.close()

    text = "\n".join(lines)
    OUT.write_text(text, encoding="utf-8")
    print(f"报告已写入: {OUT}")
    print(f"共 {len(lines)} 行")
    print()
    print(text)


if __name__ == "__main__":
    main()
