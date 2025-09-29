from __future__ import annotations

from pathlib import Path
from typing import Optional


class Interface:
    """Interactive interface backed by a Tkinter chat-style window.

    The GUI is only initialised when a display is available; otherwise the
    implementation gracefully falls back to the previous stub behaviour so
    that automated tests or headless environments keep working.
    """

    def __init__(self) -> None:
        self._headless = False
        self._closed = False
        self._pending_value: Optional[str] = None
        self._root = None
        self._chat = None
        self._entry_var = None
        self._input_var = None
        self._filedialog = None

        try:
            import tkinter as tk
            from tkinter import filedialog, scrolledtext

            self._root = tk.Tk()
            self._root.title("AGI MindLoop Chat")
            self._root.geometry("720x520")
            self._root.minsize(480, 360)

            self._chat = scrolledtext.ScrolledText(
                self._root,
                state="disabled",
                wrap="word",
                padx=12,
                pady=12,
            )
            self._chat.grid(row=0, column=0, sticky="nsew")
            self._chat.configure(font=("TkDefaultFont", 20))

            self._entry_var = tk.StringVar()

            input_frame = tk.Frame(self._root)
            input_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
            input_frame.grid_columnconfigure(1, weight=1)

            attach_btn = tk.Button(
                input_frame,
                text="+",
                width=2,
                command=self._on_attach,
                font=("TkDefaultFont", 20, "bold"),
            )
            attach_btn.grid(row=0, column=0, padx=(0, 8))

            entry = tk.Entry(
                input_frame, textvariable=self._entry_var, font=("TkDefaultFont", 20)
            )
            entry.grid(row=0, column=1, sticky="ew")
            entry.bind("<Return>", self._on_send_event)

            send_btn = tk.Button(
                input_frame,
                text="Send",
                command=self._on_send,
                font=("TkDefaultFont", 20),
            )
            send_btn.grid(row=0, column=2, padx=(8, 0))

            self._root.grid_rowconfigure(0, weight=1)
            self._root.grid_columnconfigure(0, weight=1)

            # Configure text styling for chat history.
            label_font = ("TkDefaultFont", 20, "bold")
            self._chat.tag_configure(
                "user_label", foreground="#0b5394", font=label_font
            )
            self._chat.tag_configure(
                "assistant_label", foreground="#38761d", font=label_font
            )
            self._chat.tag_configure(
                "system_label", foreground="#666666", font=label_font
            )
            self._chat.tag_configure("user_text", foreground="#0b5394")
            self._chat.tag_configure("assistant_text", foreground="#38761d")
            self._chat.tag_configure("system_text", foreground="#666666")

            self._input_var = tk.StringVar(value="")
            self._filedialog = filedialog
            self._root.protocol("WM_DELETE_WINDOW", self._on_close)

            self._append_message("System", "Welcome to AGI MindLoop!", "system")
            entry.focus_set()

        except Exception:
            # Fall back to the stub behaviour when Tk cannot be initialised
            # (e.g. running tests on a headless CI server).
            self._headless = True

    # ------------------------------------------------------------------
    # Public API used by the core loop
    # ------------------------------------------------------------------
    def get_input(self) -> str:
        if self._headless:
            return "demo input"

        if self._closed:
            raise RuntimeError("Interface window has been closed by the user.")

        assert self._input_var is not None

        # Reset the input variable so wait_variable blocks until new text.
        self._input_var.set("")
        self._pending_value = None

        # Ensure the window is visible and focused for the user.
        self._root.deiconify()
        self._root.lift()
        self._root.after(0, lambda: self._root.focus_force())

        self._root.wait_variable(self._input_var)

        if self._closed:
            raise RuntimeError("Interface window has been closed by the user.")

        value = self._pending_value or ""
        self._pending_value = None
        return value

    def send_output(self, text: str) -> None:
        if self._headless or self._closed:
            print(text)
            return

        self._append_message("MindLoop", text, "assistant")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _append_message(self, speaker: str, message: str, role: str) -> None:
        if self._headless or self._chat is None:
            return

        assert self._chat is not None
        self._chat.configure(state="normal")
        label_tag = f"{role}_label"
        text_tag = f"{role}_text"
        self._chat.insert("end", f"{speaker}: ", label_tag)
        self._chat.insert("end", f"{message}\n", text_tag)
        self._chat.configure(state="disabled")
        self._chat.see("end")
        if self._root is not None:
            self._root.update_idletasks()

    def _on_send_event(self, event) -> None:  # type: ignore[override]
        self._on_send()
        return "break"

    def _on_send(self) -> None:
        if self._headless or self._closed:
            return

        assert self._entry_var is not None
        text = self._entry_var.get().strip()
        if not text:
            return

        self._entry_var.set("")
        self._submit_text(text)

    def _on_attach(self) -> None:
        if self._headless or self._closed or self._filedialog is None:
            return

        filename = self._filedialog.askopenfilename(title="Select a file to import")
        if not filename:
            return

        path = Path(filename)
        try:
            data = path.read_bytes()
        except Exception as exc:  # pragma: no cover - GUI error reporting only
            self._append_message(
                "System", f"Failed to import '{path.name}': {exc}", "system"
            )
            return

        content = data.decode("utf-8", errors="replace")
        char_limit = 4000
        truncated = len(content) > char_limit
        display_content = content[:char_limit]
        message = f"[Imported file: {path.name}]\n{display_content}"
        if truncated:
            message += "\n...[truncated]..."

        assert self._entry_var is not None
        existing_text = self._entry_var.get().strip()
        if existing_text:
            combined = f"{existing_text}\n\n{message}"
        else:
            combined = message

        self._entry_var.set("")
        self._submit_text(combined)

    def _on_close(self) -> None:
        if self._closed or self._headless:
            return

        self._closed = True
        if self._input_var is not None:
            # Ensure wait_variable unblocks by updating the tracked variable.
            self._input_var.set("__CLOSED__")
        if self._root is not None:
            self._root.destroy()
            self._root = None
        self._chat = None

    def _submit_text(self, text: str) -> None:
        if self._headless or self._closed:
            return

        text = text.strip()
        if not text:
            return

        assert self._input_var is not None
        self._append_message("You", text, "user")
        self._pending_value = text
        # Trigger wait_variable listeners.
        self._input_var.set(text)

