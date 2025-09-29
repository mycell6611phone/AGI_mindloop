from __future__ import annotations
import math, re
from typing import List, Dict, Tuple
import numpy as np
from .vector_store import VectorStore
from .meta_store import MetaStore

_word = re.compile(r"[A-Za-z0-9_]+")

def _tokenize(t: str) -> List[str]:
    return [w.lower() for w in _word.findall(t or "")]

def _bm25_scores(query: str, docs: List[Tuple[int, str]], k1: float = 1.2, b: float = 0.75) -> Dict[int, float]:
    q_terms = _tokenize(query)
    if not q_terms or not docs: return {}
    # tokenize docs
    toks = {doc_id: _tokenize(txt) for doc_id, txt in docs}
    N = len(docs)
    dl = {doc_id: len(ts) for doc_id, ts in toks.items()}
    avgdl = (sum(dl.values()) / max(N, 1)) or 1.0
    # document frequencies
    df: Dict[str, int] = {}
    for ts in toks.values():
        for t in set(ts):
            if t in q_terms:
                df[t] = df.get(t, 0) + 1
    # compute
    scores: Dict[int, float] = {doc_id: 0.0 for doc_id, _ in docs}
    for t in q_terms:
        n_qi = df.get(t, 0)
        if n_qi == 0: continue
        idf = math.log((N - n_qi + 0.5) / (n_qi + 0.5) + 1.0)
        for doc_id, ts in toks.items():
            f_qi = ts.count(t)
            denom = f_qi + k1 * (1 - b + b * (dl[doc_id] / avgdl))
            scores[doc_id] += idf * ((f_qi * (k1 + 1)) / max(denom, 1e-9))
    return scores

def _norm_scores(d: Dict[int, float]) -> Dict[int, float]:
    if not d: return {}
    m = max(d.values()) or 1.0
    return {k: (v / m) for k, v in d.items()}

def hybrid_recall(sqlite_path: str, vs: VectorStore, q_emb: np.ndarray, query_text: str, k: int = 8, alpha: float = 0.7) -> List[Dict]:
    """
    Returns top-k mixed results from semantic (memories via FAISS) and keyword (artifacts via FTS).
    Output: [{kind: 'memory'|'artifact', id, cosine, bm25, score}]
    """
    # semantic
    sem_hits = vs.search(q_emb.reshape(1, -1), max(k * 3, k))
    sem = {mem_id: max(0.0, min(1.0, (cos))) for mem_id, cos in sem_hits}  # inner product on normalized vec ≈ cosine
    # keyword
    ms = MetaStore(sqlite_path)
    docs = ms.fts_candidates(query_text, limit=200)
    bm25_raw = _bm25_scores(query_text, docs)
    bm25 = _norm_scores(bm25_raw)

    # rank separately then fuse
    items: List[Dict] = []
    for mid, cos in sem.items():
        items.append({"kind": "memory", "id": mid, "cosine": cos, "bm25": 0.0, "score": alpha * cos})
    for aid, _txt in docs:
        b = bm25.get(aid, 0.0)
        items.append({"kind": "artifact", "id": aid, "cosine": 0.0, "bm25": b, "score": (1 - alpha) * b})

    # take top-k by score
    items.sort(key=lambda x: x["score"], reverse=True)
    return items[:k]

