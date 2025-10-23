# IO / Telemetry Notes

Bridges between the core loop and the outside world.

- `interface.py` — Tkinter chat UI with model selectors; falls back to a
  headless console stub when Tk is unavailable. Provides `get_input` and
  `send_output`.
- `file_writer.py` — Simple helper that writes outputs into
  `./data/output/`, sanitizing filenames.
- `telemetry.py` — UTC timestamp logger used throughout the loop.

Interface failures must keep the loop alive in headless mode; avoid
adding imports that would prevent `Interface()` from instantiating.
