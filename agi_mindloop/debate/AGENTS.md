# Debate Utilities

Shared JSON extractors used by action and memory debates.

- `json_schema.py` — Provides `_first_json_obj`, `parse_eval`, and
  `parse_judgment` helpers that recover structured scores from LLM output.
- `__init__.py` — Re-exports the parsing functions for convenient imports.

When adjusting schemas, keep them in sync with prompt expectations (see
`prompts/evaluate.md` and `prompts/judge.md`).
