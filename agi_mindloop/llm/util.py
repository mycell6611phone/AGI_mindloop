import subprocess
from typing import List, Optional

def run_and_capture(args: List[str], prompt: str, timeout: Optional[int] = None) -> str:
    proc = subprocess.run(
        args + ["-p", prompt],
        input="",
        capture_output=True,
        text=True,
        timeout=timeout if timeout else None,
        check=False,
    )
    # Prefer stdout; llama.cpp prints generations to stdout.
    out = proc.stdout or ""
    # Fallback append stderr if empty
    if not out and proc.stderr:
        out = proc.stderr
    return out.strip()

