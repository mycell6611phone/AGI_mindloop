# Config Notes

- `config.yaml` — Default runtime configuration. Fields map directly to
  dataclasses in `agi_mindloop/config.py` (`runtime`, `models`, `llm`
  defaults, persona/prompt directories, memory paths, safety thresholds).

Treat this file as the baseline for tests; modifying keys requires
updating fixtures and possibly prompt directories.
