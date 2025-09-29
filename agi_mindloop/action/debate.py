# Action evaluation: Neutral A veto; Persona B decides + scoring.

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from agi_mindloop.llm.engine import CompletionRequest, GenOptions, Engine
from agi_mindloop.debate import parse_eval

@dataclass
class ActionDecision:
    action: str
    accept: bool
    reason_b: str
    reason_a: str
    utility_b: float
    risk_b: float
    utility_a: float
    risk_a: float

def _eval(engine: Engine, system_text: str, eval_sys: str, eval_user: str, action: str, context: str, gen: GenOptions) -> dict:
    # Debug: show what eval_user looks like before formatting
    print("DEBUG eval_user template:", repr(eval_user))

    req = CompletionRequest(
        system=(system_text + "\n" + eval_sys).strip(),
        user=eval_user.format(action=action, context=context),
    )
    raw = engine.complete(req, gen)
    return parse_eval(raw)


def decide_actions(
    candidates: List[str],
    context: str,
    neutral_sys: str,
    persona_sys: str,
    eval_sys: str,
    eval_user: str,
    engine_a: Engine,
    engine_b: Engine,
    gen: GenOptions,
    veto_risk: float,
) -> Optional[ActionDecision]:
    """
    Evaluate each action with Neutral A and Persona B.
    - A vetoes if risk >= veto_risk.
    - Among non-vetoed ACCEPTs by B, pick max expected value: 0.7*B + 0.3*A.
    """
    best: Optional[ActionDecision] = None
    for act in candidates:
        eb = _eval(engine_b, persona_sys, eval_sys, eval_user, act, context, gen)
        ea = _eval(engine_a, neutral_sys, eval_sys, eval_user, act, context, gen)

        if ea.get("risk") is not None and float(ea["risk"]) >= float(veto_risk):
            accept = False
        else:
            accept = eb.get("label", "") == "ACCEPT"

        dec = ActionDecision(
            action=act,
            accept=accept,
            reason_b=eb.get("reason",""),
            reason_a=ea.get("reason",""),
            utility_b=float(eb.get("utility",0.0)),
            risk_b=float(eb.get("risk",0.0)),
            utility_a=float(ea.get("utility",0.0)),
            risk_a=float(ea.get("risk",0.0)),
        )

        if not accept:
            continue

        def expected(d: ActionDecision) -> float:
            b = d.utility_b * (1.0 - d.risk_b)
            a = d.utility_a * (1.0 - d.risk_a)
            return 0.7*b + 0.3*a

        if best is None or expected(dec) > expected(best):
            best = dec

    return best

