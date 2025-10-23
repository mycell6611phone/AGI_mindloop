# Memory & Retrieval Notes

Implements the experience storage pieces invoked by the memory gate.

- `debate_gate.py` — Persona vs. Neutral judge that decides whether to
  store an explanation. Uses `parse_judgment` to interpret LLM output.
- `embeddings.py` — Wrapper around BGE-M3 embeddings (lazy import of
  `FlagEmbedding`).
- `vector_store.py` — FAISS HNSW index for semantic recall (1024-dim).
- `meta_store.py` — SQLite persistence for artifacts, memories, and
  debate telemetry (creates schema on demand).
- `recall.py` — Hybrid recall routine that fuses FAISS results with
  BM25-style search over stored artifacts.
- `json_schema.py` — Duplicate of debate JSON parsing kept for backward
  compatibility; prefer `agi_mindloop.debate` helpers when possible.
- `__init__.py` — Re-exports key classes/functions.

Default paths for the stores live in `config.MemoryCfg` (see
`config.yaml`).
