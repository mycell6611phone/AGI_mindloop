# Action Stage Notes

This folder holds everything used once the planner/critic propose actions.

- `decider.py` — High-level wrapper that loads the evaluation prompt and
  delegates to `debate.decide_actions`, returning an `ActionDecision`.
- `debate.py` — Dataclass for the chosen action plus the persona/neutral
  scoring routine. Consumes `agi_mindloop.debate.parse_eval` JSON helper.
- `experimenter.py` — Resource-limited sandbox runner. Parses commands
  (`sh:` / `!`) and enforces an allowlist when launching subprocesses.
- `__init__.py` — Re-exports `choose_action`, `ActionDecision`, and the
  `Sandbox` utilities.

Persona B supplies approvals; Neutral A can veto when risk exceeds the
configured threshold (`safety.veto_risk`).
