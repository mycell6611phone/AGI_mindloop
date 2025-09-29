# explainer.py
# Explainer runs on Neutral A for auditing clarity.

from __future__ import annotations
from agi_mindloop.llm.engine import CompletionRequest, GenOptions, Engine
from agi_mindloop.prompts import StagePrompt

def explain(
    input_text: str,
    plan_text: str,
    critique_text: str,
    neutral_sys: str,
    stage: StagePrompt,
    engine_a: Engine,
    gen: GenOptions,
) -> str:
    # Keep user block generic. Avoid leaking internal prompts.
    req = CompletionRequest(
        system=(neutral_sys + "\n" + stage.system).strip(),
        user=stage.user,
    )
    _ = engine_a.complete(req, gen)  # optional future use
    # Deterministic summary assembled locally for logs
    return (
        "Input: " + input_text.strip() + "\n"
        "Plan:\n" + plan_text.strip() + "\n"
        "Critique:\n" + critique_text.strip()
    )

