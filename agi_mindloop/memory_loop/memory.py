# memory.py
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore

from faiss_indexer import FaissIndexer


ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


@dataclass
class MemoryRecord:
    id: str
    content: str
    timestamp: str
    type: str
    metadata: Dict


class Memory:
    """
    Hybrid memory system combining FAISS vector search with SQLite metadata storage.

    Schema:
        memories(
            id TEXT PRIMARY KEY,           -- external ID (UUID4 string)
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,       -- ISO 8601 UTC
            type TEXT NOT NULL,            -- 'observation' | 'code' | 'reflection' | ...
            metadata TEXT NOT NULL         -- JSON string conforming to memory_schema.json
        )

        faiss_map(
            id TEXT PRIMARY KEY,           -- same as memories.id
            vector_id INTEGER NOT NULL     -- numeric ID used in FAISS IndexIDMap
        )

    The FAISS index is persisted to `index_path`.
    """

    def __init__(self, db_path: str, index_path: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.db_path = db_path
        self.index_path = index_path
        self.model_name = model_name

        # SQLite init
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self._init_db()

        # Model init (lazy)
        self._model: Optional[SentenceTransformer] = None

        # Determine embedding dimension by probing model lazily when needed
        self._dimension: Optional[int] = None

        # FAISS indexer
        # If an index exists, dimensionality will be read from it on load
        self.indexer: Optional[FaissIndexer] = None
        self._load_or_create_indexer()

    # ------------------------------
    # Public API
    # ------------------------------
    def add_memory(self, content: str, metadata: Dict) -> MemoryRecord:
        """
        Add a memory. Generate text embedding. Add vector to FAISS. Store content and metadata in SQLite.

        The memory `type` is taken from metadata.get('type', 'observation') and also duplicated in the `type` column.
        Returns the full MemoryRecord.
        """
        if not isinstance(metadata, dict):
            raise TypeError("metadata must be a dict")

        mem_type = str(metadata.get("type", "observation"))

        # Ensure model and dimension
        vec = self._embed_text(content)
        dim = vec.shape[0]
        if self._dimension is None:
            self._dimension = dim

        # Ensure indexer exists and matches dim
        if self.indexer is None or self.indexer.dimension != dim:
            # Create new indexer and save
            self.indexer = FaissIndexer(dimension=dim)

        # Generate IDs
        ext_id = str(uuid.uuid4())
        vector_id = self._next_vector_id()

        # Persist to FAISS
        self.indexer.add_vector(vec.astype(np.float32), ids=np.array([vector_id], dtype=np.int64))
        self.indexer.save_index(self.index_path)

        # Persist to SQLite
        ts = _utc_now_iso()
        metadata_json = json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))
        with self.conn:
            self.conn.execute(
                "INSERT INTO memories(id, content, timestamp, type, metadata) VALUES(?,?,?,?,?)",
                (ext_id, content, ts, mem_type, metadata_json),
            )
            self.conn.execute(
                "INSERT INTO faiss_map(id, vector_id) VALUES(?,?)",
                (ext_id, vector_id),
            )

        return MemoryRecord(id=ext_id, content=content, timestamp=ts, type=mem_type, metadata=metadata)

    def recall_memories(self, query_text: str, k: int = 5) -> List[MemoryRecord]:
        """
        Embed the query. Retrieve k nearest vectors. Fetch full rows from SQLite. Return as MemoryRecord list.
        """
        if not self.indexer or self.indexer.ntotal == 0:
            return []

        qvec = self._embed_text(query_text).astype(np.float32)
        ids, distances = self.indexer.search(qvec, k=k)
        if ids.size == 0:
            return []

        # Map vector IDs to external IDs
        ext_ids = self._external_ids_for_vector_ids(list(map(int, ids.tolist())))
        if not ext_ids:
            return []

        # Fetch records preserving search order
        placeholders = ",".join(["?"] * len(ext_ids))
        rows = self.conn.execute(
            f"SELECT id, content, timestamp, type, metadata FROM memories WHERE id IN ({placeholders})",
            ext_ids,
        ).fetchall()
        row_map = {row[0]: row for row in rows}

        results: List[MemoryRecord] = []
        for ext_id in ext_ids:
            row = row_map.get(ext_id)
            if not row:
                continue
            meta = json.loads(row[4]) if row[4] else {}
            results.append(MemoryRecord(id=row[0], content=row[1], timestamp=row[2], type=row[3], metadata=meta))
        return results

    def forget_memory(self, memory_id: str) -> bool:
        """
        Remove a memory from SQLite and FAISS. Returns True if something was removed.
        """
        # Lookup vector_id
        row = self.conn.execute("SELECT vector_id FROM faiss_map WHERE id=?", (memory_id,)).fetchone()
        if not row:
            return False
        vector_id = int(row[0])

        # Remove from FAISS
        if self.indexer is not None:
            self.indexer.remove_vector(vector_id)
            self.indexer.save_index(self.index_path)

        # Remove from SQLite
        with self.conn:
            self.conn.execute("DELETE FROM memories WHERE id=?", (memory_id,))
            self.conn.execute("DELETE FROM faiss_map WHERE id=?", (memory_id,))
        return True

    # ------------------------------
    # Internals
    # ------------------------------
    def _init_db(self) -> None:
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL,
                    metadata TEXT NOT NULL
                );
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS faiss_map (
                    id TEXT PRIMARY KEY,
                    vector_id INTEGER NOT NULL
                );
                """
            )

    def _load_or_create_indexer(self) -> None:
        if os.path.exists(self.index_path):
            try:
                self.indexer = FaissIndexer.load_index(self.index_path)
                self._dimension = self.indexer.dimension
                return
            except Exception:
                # Fallback to create empty
                pass
        # If we get here, create an empty indexer lazily when we know dimension
        self.indexer = None

    def _external_ids_for_vector_ids(self, vector_ids: List[int]) -> List[str]:
        if not vector_ids:
            return []
        placeholders = ",".join(["?"] * len(vector_ids))
        rows = self.conn.execute(
            f"SELECT id, vector_id FROM faiss_map WHERE vector_id IN ({placeholders})",
            vector_ids,
        ).fetchall()
        # Preserve order according to vector_ids
        vid_to_ext = {int(r[1]): r[0] for r in rows}
        return [vid_to_ext[v] for v in vector_ids if v in vid_to_ext]

    def _next_vector_id(self) -> int:
        row = self.conn.execute("SELECT MAX(vector_id) FROM faiss_map").fetchone()
        max_id = int(row[0]) if row and row[0] is not None else -1
        return max_id + 1

    def _embed_text(self, text: str) -> np.ndarray:
        if self._model is None:
            if SentenceTransformer is None:
                raise RuntimeError(
                    "sentence-transformers is not installed. Install it to use embeddings."
                )
            self._model = SentenceTransformer(self.model_name)
        vec = self._model.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]
        return vec.astype(np.float32)

    def close(self) -> None:
        if self.conn:
            self.conn.close()
        # No explicit close needed for FAISS or model
