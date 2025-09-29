#  persona.py
# Prompt-only personas. No temperature changes. Baseline "Neutral" = empty system text.

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

@dataclass(frozen=True)
class Persona:
    name: str
    system_prompt: str  # text appended before stage system prompt

class PersonaRegistry:
    def __init__(self, root: Path):
        self.root = root
        self._cache: Dict[str, Persona] = {}

    def load(self, name: str) -> Persona:
        key = name.strip()
        if key in self._cache:
            return self._cache[key]
        if key.lower() == "neutral":
            p = Persona("Neutral", "")
        else:
            path = self.root / f"{key.lower()}.md"
            if path.exists():
                p = Persona(key, path.read_text(encoding="utf-8"))
            else:
                # Fallback minimal persona text to avoid crashes
                p = Persona(key, f"You are in a {key} mood.")
        self._cache[key] = p
        return p

    def reload(self, name: str) -> Persona:
        self._cache.pop(name.strip(), None)
        return self.load(name)

def load_current(root: str, name: str) -> Persona:
    return PersonaRegistry(Path(root)).load(name)

