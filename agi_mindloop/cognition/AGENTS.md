# Cognition Stage Notes

Planner → Critic → Explainer pipeline executed before action debate.

- `planner.py` — Builds the planning `CompletionRequest`. Supports a
  direct-question bypass (`[direct-answer]` marker) so downstream stages
  can skip action selection when the user only needs an answer.
- `self_critic.py` — Persona B critiques the plan using the critic prompt.
- `explainer.py` — Neutral A produces an audit-friendly textual summary;
  the LLM call is currently used for parity/logging.
- `__init__.py` — Exports helper functions for package-level imports.

All functions expect `StagePrompt` objects from `PromptLoader` (see
`prompts/AGENTS.md`).
