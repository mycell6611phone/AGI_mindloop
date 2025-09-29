from __future__ import annotations
import json, sqlite3
from pathlib import Path
from typing import Optional, Iterable, Tuple, List, Dict

INIT_SQL = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS cycles (
  id INTEGER PRIMARY KEY, started_at TEXT, ended_at TEXT, seed INTEGER, config_hash TEXT
);
CREATE TABLE IF NOT EXISTS artifacts (
  id INTEGER PRIMARY KEY, cycle_id INTEGER, kind TEXT, content TEXT,
  created_at TEXT, FOREIGN KEY(cycle_id) REFERENCES cycles(id)
);
CREATE TABLE IF NOT EXISTS memories (
  id INTEGER PRIMARY KEY, embedding BLOB, meta JSON,
  importance REAL, uncertainty REAL, recall_count INTEGER DEFAULT 0,
  created_at TEXT, provenance TEXT
);
CREATE TABLE IF NOT EXISTS debates (
  id INTEGER PRIMARY KEY, cycle_id INTEGER, candidate_kind TEXT,
  a_label TEXT, a_reason TEXT, a_risk REAL,
  b_label TEXT, b_reason TEXT, b_risk REAL, b_persona TEXT,
  consensus TEXT, created_at TEXT,
  FOREIGN KEY(cycle_id) REFERENCES cycles(id)
);
CREATE VIRTUAL TABLE IF NOT EXISTS fts_artifacts USING fts5(content, content='artifacts', content_rowid='id');
"""

class MetaStore:
    def __init__(self, sqlite_path: str):
        self.path = Path(sqlite_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(INIT_SQL)

    def close(self): self.conn.close()

    # Artifacts + FTS
    def add_artifact(self, cycle_id: int, kind: str, content: str, created_at: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO artifacts(cycle_id,kind,content,created_at) VALUES(?,?,?,?)",
            (cycle_id, kind, content, created_at),
        )
        rid = cur.lastrowid
        cur.execute("INSERT INTO fts_artifacts(rowid, content) VALUES(?,?)", (rid, content))
        self.conn.commit()
        return int(rid)

    def get_artifacts_text(self, ids: Iterable[int]) -> Dict[int, str]:
        ids_list = list(ids)
        if not ids_list:
            return {}
        placeholders = ",".join(["?"] * len(ids_list))
        rows = self.conn.execute(
            f"SELECT id, content FROM artifacts WHERE id IN ({placeholders})",
            tuple(ids_list),
        ).fetchall()
        return {int(i): c for i, c in rows}

    # Memories
    def add_memory(self, embedding: bytes, meta: dict, importance: float, uncertainty: float, created_at: str, provenance: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO memories(embedding,meta,importance,uncertainty,created_at,provenance) VALUES(?,?,?,?,?,?)",
            (embedding, json.dumps(meta), importance, uncertainty, created_at, provenance),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def inc_recall(self, mem_id: int, by: int = 1) -> None:
        self.conn.execute("UPDATE memories SET recall_count = recall_count + ? WHERE id = ?", (by, mem_id))
        self.conn.commit()

    # FTS search candidates (raw)
    def fts_candidates(self, query: str, limit: int = 200) -> List[Tuple[int, str]]:
        # naive OR query to broaden coverage
        q = " OR ".join([t for t in query.split() if t.strip()])
        if not q: return []
        rows = self.conn.execute(
            "SELECT rowid, content FROM fts_artifacts WHERE fts_artifacts MATCH ? LIMIT ?",
            (q, limit)
        ).fetchall()
        return [(int(r[0]), r[1]) for r in rows]

