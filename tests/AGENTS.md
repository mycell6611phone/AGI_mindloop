# Test Suite Notes

Pytest-based smoke tests for configuration and core components.

- `test_config_defaults.py` — Validates default config dataclasses and
  YAML loading.
- `test_prompt_loader.py` — Ensures prompt defaults and file overrides
  behave as expected.
- `test_action_init.py` — Confirms action package exports.
- `test_core_loop_sandbox.py` — Exercises sandbox allowlist behavior.
- `test_meta_store.py` — Covers the SQLite metastore schema and basic ops.
- `test_llm_import.py` — Verifies optional dependencies fail gracefully.

Add new tests alongside the relevant stage so breadcrumbs stay aligned
with `Outline_mindloop.md`.
