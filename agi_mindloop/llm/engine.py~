# Interface + shared types. Prompt-only personas (system text), fixed gen options.

from dataclasses import dataclass
from typing import Optional, Sequence, Protocol

@dataclass
class CompletionRequest:
    system: str
    user: str
    stop: Optional[Sequence[str]] = None

@dataclass
class GenOptions:
    temp: float = 0.6
    top_p: float = 0.95
    repeat_penalty: float = 1.1
    max_tokens: int = 1024
    ctx: int = 16384

class Engine(Protocol):
    def complete(self, req: CompletionRequest, gen: GenOptions) -> str: ...

# Simple stub (kept for tests)
class StubEngine:
    def __init__(self, name: str): self.name = name
    def complete(self, req: CompletionRequest, gen: GenOptions) -> str:
        return f"[{self.name}] {req.user[:120]}"

