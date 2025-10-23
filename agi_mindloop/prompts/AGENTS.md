# Prompt Loader Notes

Stage prompt templates consumed by cognition/action/memory components.

- Markdown files (e.g., `planner.md`, `critic.md`, `evaluate.md`) follow
  the `---system` / `---user` delimiter format consumed by
  `PromptLoader`.
- `__init__.py` — Defines `StagePrompt` dataclass, built-in defaults for
  all stages, and the `PromptLoader` utility.

If a file is missing, the loader falls back to the hard-coded defaults.
Keep placeholders (`{input}`, `{plan}`, `{candidate}`, etc.) stable to
match the expectations in cognition/action/memory modules.
