# faiss_indexer.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

try:
    import faiss  # type: ignore
except Exception as e:  # pragma: no cover
    faiss = None  # type: ignore


@dataclass
class FaissIndexer:
    """
    Thin wrapper over FAISS IndexIDMap2 + IndexFlatL2 for add/search/remove and persistence.
    """

    dimension: int
    _index: Optional["faiss.Index"] = None

    def __post_init__(self) -> None:
        if faiss is None:
            raise RuntimeError("faiss is not installed. Install faiss-cpu or faiss-gpu.")
        if self.dimension <= 0:
            raise ValueError("dimension must be positive")
        base = faiss.IndexFlatL2(self.dimension)
        self._index = faiss.IndexIDMap2(base)

    @property
    def ntotal(self) -> int:
        return int(self._index.ntotal) if self._index is not None else 0

    @property
    def index(self):  # exposed for advanced users
        return self._index

    def add_vector(self, vector: np.ndarray, ids: Optional[np.ndarray] = None) -> None:
        if self._index is None:
            raise RuntimeError("index not initialized")
        vec = vector.astype(np.float32)
        if vec.ndim == 1:
            vec = vec.reshape(1, -1)
        if ids is None:
            self._index.add(vec)
        else:
            if ids.dtype != np.int64:
                ids = ids.astype(np.int64)
            self._index.add_with_ids(vec, ids)

    def search(self, query_vector: np.ndarray, k: int = 5) -> tuple[np.ndarray, np.ndarray]:
        if self._index is None or self.ntotal == 0:
            return np.array([], dtype=np.int64), np.array([], dtype=np.float32)
        q = query_vector.astype(np.float32)
        if q.ndim == 1:
            q = q.reshape(1, -1)
        distances, ids = self._index.search(q, k)
        # Return flat arrays for convenience
        return ids[0], distances[0]

    def save_index(self, path: str) -> None:
        if self._index is None:
            raise RuntimeError("index not initialized")
        faiss.write_index(self._index, path)

    @classmethod
    def load_index(cls, path: str) -> "FaissIndexer":
        if faiss is None:
            raise RuntimeError("faiss is not installed. Install faiss-cpu or faiss-gpu.")
        index = faiss.read_index(path)
        # Determine dimension
        if hasattr(index, "d"):
            dim = int(index.d)
        else:
            # Fallback
            dim = getattr(index, "dim", None) or 0
            dim = int(dim)
        obj = cls(dimension=dim)
        obj._index = index
        return obj

    def remove_vector(self, vector_id: int) -> None:
        if self._index is None:
            raise RuntimeError("index not initialized")
        selector = faiss.IDSelectorBatch(np.array([vector_id], dtype=np.int64))
        self._index.remove_ids(selector)

