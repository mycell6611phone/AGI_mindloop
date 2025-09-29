# Memory gate: Neutral A vs Persona B. Prompt-only personas. Neutral veto on high risk.

from __future__ import annotations
from agi_mindloop.llm.engine import CompletionRequest, GenOptions, Engine
from agi_mindloop.debate import parse_judgment

def _ask(engine: Engine, system_text: str, judge_sys: str, judge_user: str, candidate_text: str, gen: GenOptions) -> dict:
    req = CompletionRequest(
        system=(system_text + "\n" + judge_sys).strip(),
        user=judge_user.format(candidate=candidate_text),
    )
    raw = engine.complete(req, gen)
    return parse_judgment(raw)

def should_store(
    candidate_text: str,
    neutral_sys: str,
    persona_sys: str,
    stage_sys: str,
    stage_user: str,
    engine_a: Engine,
    engine_b: Engine,
    gen: GenOptions,
    veto_risk: float,
) -> bool:
    """
    Returns True if Persona B says ACCEPT and Neutral A does not veto on risk.
    - neutral_sys: baseline model system text (usually empty)
    - persona_sys: persona system text (prompt-only)
    - stage_sys/stage_user: judge prompt blocks
    """
    a = _ask(engine_a, neutral_sys, stage_sys, stage_user, candidate_text, gen)
    b = _ask(engine_b, persona_sys, stage_sys, stage_user, candidate_text, gen)

    # Neutral safety veto
    if a.get("risk") is not None and float(a["risk"]) >= float(veto_risk):
        return False

    return b.get("label", "") == "ACCEPT"

