# Package Breadcrumbs

Reference: `Outline_mindloop.md` (root) describes the stage order this
package implements. Key modules here wire those stages together.

- `core_loop.py` — Canonical multi-cycle controller that calls planning,
  critique, action debate, sandbox execution, explanation, and memory
  gating. CLI entrypoint is `cli()`.
- `config.py` — Dataclass definitions (runtime, models, safety, etc.) and
  `load_config` helper used by the loop and tests.
- `action/` — Persona/neutral evaluation logic plus sandbox runner.
- `cognition/` — Planner, critic, and explainer stage prompts + helpers.
- `debate/` — JSON parsing utilities shared by action + memory debates.
- `io_mod/` — User interface abstraction (Tk fallback) and telemetry/log
  helpers.
- `llm/` — Engine abstractions, adapters (GPT4All, llama.cpp), and the
  `EngineBundle` container imported by the loop.
- `memory/` — Vector + metadata stores, debate gate, embeddings adapter.
- `memory_loop/` — Optional long-term debate memory (loaded lazily in the
  loop; keep import errors non-fatal).
- `personas/` — Persona prompt templates (`persona.py` orchestrates
  loading and defaults).
- `prompts/` — Stage-specific prompt markdown files plus loader.
- `training/` — Placeholder curation hook invoked after memory gate.

Editor backup files (`*.py~`, `*.md~`) sit next to the live versions;
ignore unless cleaning up history.
