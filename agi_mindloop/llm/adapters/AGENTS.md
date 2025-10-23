# LLM Adapter Notes

Backends used by `llm.build_engines` when selecting non-REST execution.

- `gpt4all.py` — Uses the `gpt4all` Python bindings. Expects a local
  model path; splits `model_name` and directory.
- `llamaccp.py` — Launches the `llama-cli` binary with generation options
  mapped from `GenOptions`. Relies on `llm.util.run_and_capture`.

Adapters should implement the shared `Engine` protocol and avoid keeping
global state beyond cached model handles.
