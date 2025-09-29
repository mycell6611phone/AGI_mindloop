# Planner runs on Persona B (prompt-only). Neutral A is reserved for vetoes and logging.

from __future__ import annotations
import re
from typing import List
from agi_mindloop.llm.engine import CompletionRequest, GenOptions, Engine
from agi_mindloop.prompts import StagePrompt

_NUM = re.compile(r"^\s*(\d+)[\).\:-]\s*(.+)$")

def _format_recall(recall: str | List[str]) -> str:
    if isinstance(recall, list):
        return "- " + "\n- ".join(recall[:10])
    return recall or "(none)"

def make_plan(
    input_text: str,
    recall: str | list[str],
    persona_sys: str,
    stage: StagePrompt,
    engine_b: Engine,
    gen: GenOptions,
) -> str:
    req = CompletionRequest(
        system=(persona_sys + "\n" + stage.system).strip(),
        user=stage.user.format(input=input_text, recall=_format_recall(recall)),
    )
    out = engine_b.complete(req, gen)
    return out.strip()

def extract_actions(plan_text: str) -> List[str]:
    actions: List[str] = []
    for line in plan_text.splitlines():
        m = _NUM.match(line)
        if m:
            actions.append(m.group(2).strip())
    # fallback to single “do:<summary>”
    if not actions and plan_text:
        actions = [plan_text.splitlines()[0][:120]]
    return actions[:7]

