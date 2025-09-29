#  decider.py
# Persona-B decides. Neutral-A can veto on risk.

from __future__ import annotations
from typing import List, Optional
from agi_mindloop.llm.engine import GenOptions
from agi_mindloop.llm import EngineBundle
from agi_mindloop.prompts import PromptLoader
from agi_mindloop.action.debate import decide_actions, ActionDecision

def decide(*args, **kwargs):
    return choose_action(*args, **kwargs)

def choose_action(
    candidates: List[str],
    context: str,
    persona_sys: str,
    neutral_sys: str,
    engines: EngineBundle,
    gen: GenOptions,
    prompts: PromptLoader,
    veto_risk: float,
) -> Optional[ActionDecision]:
    P = prompts.load("evaluate")  # prompts/evaluate.md
    return decide_actions(
        candidates=candidates,
        context=context,
        neutral_sys=neutral_sys,
        persona_sys=persona_sys,
        eval_sys=P.system,
        eval_user=P.user,
        engine_a=engines.neutral_a,
        engine_b=engines.mooded_b,
        gen=gen,
        veto_risk=veto_risk,
    )


