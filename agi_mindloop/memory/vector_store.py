# FAISS index (CPU). Cosine similarity via inner product on L2-normalized vectors.

from __future__ import annotations
from pathlib import Path
from typing import Iterable, List, Tuple
import numpy as np
import faiss

def _norm(v: np.ndarray) -> np.ndarray:
    v = v.astype(np.float32)
    n = np.linalg.norm(v, axis=1, keepdims=True) + 1e-12
    return v / n

class VectorStore:
    def __init__(self, faiss_path: str, dim: int = 1024, M: int = 32):
        self.path = Path(faiss_path)
        self.dim = dim
        if self.path.exists():
            self.index = faiss.read_index(str(self.path))
            # index may already be an IDMap
            self.idmap = self.index
        else:
            base = faiss.IndexHNSWFlat(dim, M, faiss.METRIC_INNER_PRODUCT)
            idmap = faiss.IndexIDMap2(base)
            self.index = idmap
            self.idmap = idmap

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.path))

    def add(self, ids: Iterable[int], vectors: np.ndarray) -> None:
        ids = np.fromiter(ids, dtype=np.int64)
        vec = _norm(np.asarray(vectors))
        assert vec.shape[1] == self.dim, f"dim mismatch: {vec.shape[1]} != {self.dim}"
        self.idmap.add_with_ids(vec, ids)

    def search(self, query: np.ndarray, k: int) -> List[Tuple[int, float]]:
        q = _norm(np.asarray(query))
        D, I = self.index.search(q, k)
        # return for first query only (batch size 1 expected)
        scores = D[0].tolist()
        ids = I[0].tolist()
        out = [(int(i), float(s)) for i, s in zip(ids, scores) if i != -1]
        return out

