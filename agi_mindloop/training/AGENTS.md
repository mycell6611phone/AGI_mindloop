# Training Stub Notes

Hooks for future self-training/curation workflows.

- `curate_debate.py` — Currently returns placeholders (validated,
  rejected, pending). The core loop calls this after the memory gate; any
  future implementation should preserve the tuple contract.

Keep this module side-effect free so tests can import it without heavy
dependencies.
