# experimenter.py
# Minimal sandbox. Allowlist binaries only. CPU/mem caps. Dry-run if disallowed.

from __future__ import annotations
import os, shlex, shutil, subprocess, sys
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

try:
    import resource  # Linux
except Exception:
    resource = None

def parse_action(text: str) -> Dict[str, Any]:
    """
    Conventions:
      - "sh: <command line>" -> run shell command safely (no shell=True)
      - "!<command line>"    -> same as sh:
      - otherwise            -> noop
    """
    t = text.strip()
    if t.startswith("sh:"):
        return {"type": "sh", "argv": shlex.split(t[3:].strip())}
    if t.startswith("!"):
        return {"type": "sh", "argv": shlex.split(t[1:].strip())}
    return {"type": "noop", "text": t}

@dataclass
class Sandbox:
    allowlist: List[str]
    cpu_seconds: int = 5
    mem_mb: int = 512
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None

    def _set_limits(self):
        if resource is None:
            return
        # CPU time
        resource.setrlimit(resource.RLIMIT_CPU, (self.cpu_seconds, self.cpu_seconds))
        # Address space (approx)
        bytes_lim = int(self.mem_mb) * 1024 * 1024
        try:
            resource.setrlimit(resource.RLIMIT_AS, (bytes_lim, bytes_lim))
        except ValueError:
            pass  # some systems disallow lowering AS in Python

    def _allowed(self, argv: List[str]) -> bool:
        if not argv:
            return False
        head = os.path.basename(argv[0])
        return head in set(self.allowlist)

    def run(self, action_text: str, timeout_sec: int = 10) -> Dict[str, Any]:
        spec = parse_action(action_text)
        if spec["type"] != "sh":
            return {"ok": True, "type": spec["type"], "detail": spec}

        argv = spec["argv"]
        if not self._allowed(argv) or not shutil.which(argv[0]):
            return {"ok": False, "type": "dry_run", "reason": "disallowed or missing binary", "argv": argv}

        try:
            # no shell=True
            proc = subprocess.Popen(
                argv,
                cwd=self.cwd or os.getcwd(),
                env=self.env or os.environ.copy(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=self._set_limits if resource is not None else None,
            )
            out, err = proc.communicate(timeout=timeout_sec)
            return {
                "ok": proc.returncode == 0,
                "code": proc.returncode,
                "stdout": out[-8000:],  # cap
                "stderr": err[-8000:],
                "argv": argv,
            }
        except subprocess.TimeoutExpired:
            proc.kill()
            return {"ok": False, "error": "timeout", "argv": argv}
        except Exception as e:
            return {"ok": False, "error": repr(e), "argv": argv}

