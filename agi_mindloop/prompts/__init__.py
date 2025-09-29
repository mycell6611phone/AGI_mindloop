# File-based prompt loader. Two-block format:
# ---system
# <system text>
# ---user
# <user text with {placeholders}>
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re

@dataclass(frozen=True)
class StagePrompt:
    system: str
    user: str

_MARKER = re.compile(r"(?s)^---system\s*(.*?)\s*---user\s*(.*)\s*$")

_DEFAULTS: dict[str, StagePrompt] = {
    "planner": StagePrompt(
        system="Plan concisely. Output numbered steps. Ask for missing facts at the end as questions.",
        user="Input:\n{input}\n\nRelevant recall:\n{recall}\n\nProduce a 3–7 step plan."
    ),
    "critic": StagePrompt(
        system="Critique tersely. Identify 2 risks and 2 improvements. Keep ≤120 words.",
        user="Plan:\n{plan}\n\nList risks and improvements. End with a one-line revision suggestion."
    ),
    "explainer": StagePrompt(
        system="Explain decisions clearly. Avoid fluff.",
        user="Summarize: input, plan, critique, and chosen action."
    ),
    "evaluate": StagePrompt(
        system=(
            "You evaluate a proposed action for the current context. Respond with strict JSON "
            "only containing label('ACCEPT'|'REJECT'), reason(≤30 words), utility(0..1), and "
            "risk(0..1). Be concise and realistic."
        ),
        user=(
            "Context:\n{context}\n\n"
            "Action:\n{action}\n\n"
            "Return only one JSON object."
        ),
    ),
    "judge": StagePrompt(
        system=("Decide ACCEPT or REJECT for memory storage. Respond in strict JSON.\n"
                "Fields: label('ACCEPT'|'REJECT'), reason(str, ≤30 words), "
                "risk(float 0..1), importance(float 0..1), uncertainty(float 0..1)."),
        user=("Candidate artifact:\n{candidate}\n\n"
              "Reply JSON only, no prose, e.g. "
              "{\"label\":\"ACCEPT\",\"reason\":\"...\",\"risk\":0.2,\"importance\":0.6,\"uncertainty\":0.3}")
    ),
    "curate": StagePrompt(
        system=("Curate 5 memories for self-training. Respond JSON per id: "
                "{id:{decision:'VALIDATE'|'PASS'|'REJECT', reason:str≤30}}. "
                "Prioritize relevance, accuracy, novelty."),
        user="{candidates}"
    ),
}

class PromptLoader:
    def __init__(self, root: str, mapping: dict[str, str] | None = None):
        self.root = Path(root)
        self.mapping = mapping or {
            "planner": "planner.md",
            "critic": "critic.md",
            "explainer": "explainer.md",
            "judge": "judge.md",
            "curate": "curate.md",
        }

    def load(self, stage: str) -> StagePrompt:
        fname = self.mapping.get(stage, f"{stage}.md")
        path = (self.root / fname)
        if not path.exists():
            return _DEFAULTS.get(stage, StagePrompt(system="", user="{text}"))
        text = path.read_text(encoding="utf-8")
        m = _MARKER.match(text)
        if not m:
            # If file lacks markers, treat whole file as user block
            return StagePrompt(system="", user=text)
        return StagePrompt(system=m.group(1).strip(), user=m.group(2).strip())

