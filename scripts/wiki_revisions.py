"""Wiki 修订系统的核心数据模型与文件 I/O.

修订记录是 append-only 的 JSONL：data/wiki/revisions/<page>.jsonl
每行一条记录:
  {
    "rev_id":      "YYYYMMDD-HHMMSS-<6位hash>",
    "timestamp":   ISO 8601 (本地时区, 含偏移),
    "author":      str,
    "summary":     str,
    "parent_rev":  str | null,
    "content_hash": "sha256:...",
    "content":     str
  }

不依赖 git。所有版本均存于 jsonl，git 只是顺带备份。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REVISIONS_DIR = REPO_ROOT / "data" / "wiki" / "revisions"


@dataclass
class Revision:
    rev_id: str
    timestamp: str
    author: str
    summary: str
    parent_rev: str | None
    content_hash: str
    content: str

    def to_json_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False) + "\n"

    @classmethod
    def from_dict(cls, d: dict) -> "Revision":
        return cls(
            rev_id=d["rev_id"],
            timestamp=d["timestamp"],
            author=d["author"],
            summary=d.get("summary", ""),
            parent_rev=d.get("parent_rev"),
            content_hash=d["content_hash"],
            content=d["content"],
        )


def now_local_iso() -> str:
    """本地时区的 ISO 8601 时间戳, 含偏移 (eg. 2026-04-22T15:30:00+08:00)."""
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def content_hash(content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def make_rev_id(timestamp_iso: str, c_hash: str) -> str:
    """rev_id = YYYYMMDD-HHMMSS-<6位hash>.

    timestamp_iso: ISO 8601, 取年月日时分秒
    c_hash: content_hash, 取 sha256: 后的前 6 位
    """
    dt = datetime.fromisoformat(timestamp_iso)
    short = c_hash.split(":", 1)[1][:6]
    return f"{dt.strftime('%Y%m%d-%H%M%S')}-{short}"


def revisions_path(page: str) -> Path:
    return REVISIONS_DIR / f"{page}.jsonl"


def load_revisions(page: str) -> list[Revision]:
    """读取一个页面的全部修订（按文件顺序，即时间顺序）."""
    p = revisions_path(page)
    if not p.exists():
        return []
    revs = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            revs.append(Revision.from_dict(json.loads(line)))
    return revs


def latest_revision(page: str) -> Revision | None:
    revs = load_revisions(page)
    return revs[-1] if revs else None


def append_revision(
    page: str,
    content: str,
    author: str,
    summary: str,
    timestamp_iso: str | None = None,
) -> Revision:
    """追加一条新修订。如果与最新修订内容相同（hash 相等），抛 ValueError."""
    REVISIONS_DIR.mkdir(parents=True, exist_ok=True)

    ts = timestamp_iso or now_local_iso()
    h = content_hash(content)
    parent = latest_revision(page)

    if parent and parent.content_hash == h:
        raise ValueError(f"内容未改变, 不写入新修订 (page={page})")

    rev = Revision(
        rev_id=make_rev_id(ts, h),
        timestamp=ts,
        author=author,
        summary=summary,
        parent_rev=parent.rev_id if parent else None,
        content_hash=h,
        content=content,
    )

    with revisions_path(page).open("a", encoding="utf-8") as f:
        f.write(rev.to_json_line())
    return rev


def list_pages() -> list[str]:
    """返回所有有 revision 文件的页面名."""
    if not REVISIONS_DIR.exists():
        return []
    return sorted(p.stem for p in REVISIONS_DIR.glob("*.jsonl"))
