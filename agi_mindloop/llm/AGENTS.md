# LLM Engine Notes

Abstractions for swapping local/remote language models used across the
loop.

- `engine.py` — Defines `CompletionRequest`, `GenOptions`, the `Engine`
  protocol, and built-in engine implementations (OpenAI, GPT4All REST,
  stub).
- `__init__.py` — Provides `EngineBundle` and `build_engines` factory that
  selects adapters based on config (`runtime.engine`).
- `util.py` — Utility helper for invoking llama.cpp CLI binaries.
- `adapters/` — Concrete adapters:
  - `gpt4all.py` wraps the Python `gpt4all` bindings for local models.
  - `llamaccp.py` shells out to `llama-cli`, honoring generation options.

Keep interfaces pure (no side effects beyond model calls) so tests can
replace engines with stubs easily.
