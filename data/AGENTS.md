# Data Artifacts

Binary stores backing the memory components.

- `vectors.faiss` — FAISS index persisted by `memory/vector_store.py`.
- `meta.sqlite3` — SQLite database populated via `memory/meta_store.py`.

Treat these as runtime artifacts. Tests may assume they exist but should
not rely on specific contents.
