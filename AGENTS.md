# Repository Breadcrumbs

These notes summarize the layout of **AGI Mindloop**. Consult
`Outline_mindloop.md` in the repository root for the canonical end-to-end
description of the reasoning cycle.

- `agi_mindloop/` — Main runtime package; each subdirectory has its own
  `AGENTS.md` with stage-level details (planning, action evaluation,
  memory, LLM access, etc.). The core orchestrator lives in
  `agi_mindloop/core_loop.py` as described in the outline.
- `core_loop.py` (root) — Legacy, simplified loop kept for reference and
  tests. Prefer touching the package version unless a change explicitly
  targets this fallback script.
- `config/config.yaml` — Default configuration loaded by
  `agi_mindloop.config.load_config`. Mirrors the dataclasses in
  `agi_mindloop/config.py`.
- `data/` — Persistent artifacts for the vector store (FAISS index) and
  metadata SQLite database.
- `tests/` — Pytest suite covering configuration loading, prompt loader,
  action wiring, sandbox behavior, and LLM import stubs.
- `lua` — Text description of the Lua sandbox policy shipped alongside
  the Python sandbox wrapper.
- Backup files with a trailing `~` are editor artifacts; ignore them when
  making changes.

When adding features, keep the outline-aligned phase order:
configuration → persona/prompt loading → planning/critique → action
selection → sandbox execution → explanation → memory/curation.
