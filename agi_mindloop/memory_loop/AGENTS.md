# Legacy Memory Loop Notes

Optional long-term memory components referenced conditionally in
`core_loop`. These modules predate the newer `memory/` package but remain
importable for backward compatibility.

- `memory.py` — Hybrid FAISS + SQLite memory system with debate-based
  validation pipeline.
- `memory_debate.py` — Lightweight debate orchestrator used by the legacy
  memory validator.
- `memory_logger.py` — JSONL logger for capturing debate/recall events.
- `faiss_indexer.py` — Thin wrapper around FAISS `IndexIDMap2`.

Treat these as optional extensions; guard imports so missing FAISS or
sentence-transformers packages do not crash the main loop.
