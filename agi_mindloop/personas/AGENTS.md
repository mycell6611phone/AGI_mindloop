# Persona Notes

Persona prompts customize the planner/critic behavior while Neutral
remains the safety baseline.

- Markdown files (`analytical.md`, `focused.md`, `coder.md`, etc.) — Raw
  system prompts loaded verbatim. Filenames are lowercase persona names.
- `persona.py` — `PersonaRegistry` caches personas and falls back to a
  generic mood string if a file is missing. `load_current` convenience
  helper used by config/tests.
- `__init__.py` — Re-exports registry helpers.

Keep persona text concise; the planner and critic concatenate persona
system prompts with stage prompts per the outline.
