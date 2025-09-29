# self_critic.py
# Critique runs on Persona B. Short and structured per prompt.

from __future__ import annotations
from agi_mindloop.llm.engine import CompletionRequest, GenOptions, Engine
from agi_mindloop.prompts import StagePrompt

def critique(
    plan_text: str,
    persona_sys: str,
    stage: StagePrompt,
    engine_b: Engine,
    gen: GenOptions,
) -> str:
    req = CompletionRequest(
        system=(persona_sys + "\n" + stage.system).strip(),
        user=stage.user.format(plan=plan_text),
    )
    out = engine_b.complete(req, gen)
    return out.strip()

