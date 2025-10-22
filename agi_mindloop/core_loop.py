from pathlib import Path
from typing import Optional
from agi_mindloop.config import load_config, GenDefaults
from agi_mindloop.io_mod.interface import Interface
from agi_mindloop.io_mod.telemetry import log
from agi_mindloop.llm.engine import Gpt4AllAPIEngine, GenOptions
from agi_mindloop.llm import EngineBundle
from agi_mindloop.personas.persona import PersonaRegistry
from agi_mindloop.prompts import PromptLoader
from agi_mindloop.cognition.planner import make_plan
from agi_mindloop.cognition.self_critic import critique
from agi_mindloop.cognition.explainer import explain
from agi_mindloop.action.decider import choose_action
from agi_mindloop.action.experimenter import Sandbox
from agi_mindloop.action.debate import ActionDecision
from agi_mindloop.memory.debate_gate import should_store
from agi_mindloop.training.curate_debate import curate_if_needed

def cli():
    """CLI entry point wrapper for mindloop command"""
    from pathlib import Path
    default_config = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
    return main(str(default_config))


def _format_sandbox_command(action_text: str) -> str:
    text = (action_text or "").strip()
    if not text:
        return text
    if text.startswith(("sh:", "!")):
        return text
    return f"sh: {text}"


def _execute_action_decision(action: ActionDecision, sandbox: Sandbox):
    text = (action.action or "").strip()
    if text.startswith("do:"):
        idea = text[3:].strip()
        return {"detail": f"Simulated conceptual action: {idea}"}
    command = _format_sandbox_command(text)
    return sandbox.run(command)




def main(config_path: str):
    cfg = load_config(config_path)
    iface = Interface()

    def _model_name(models: Optional[object], key: str) -> str:
        if not models:
            return key
        value = getattr(models, key, None)
        if not value:
            return key
        try:
            path = Path(value)
            if path.name:
                return path.name
        except TypeError:
            pass
        return str(value)

    # Engines: talk to the locally running GPT4All server
    engine_a = Gpt4AllAPIEngine(_model_name(getattr(cfg, "models", None), "neutral_a"))
    engine_b = Gpt4AllAPIEngine(_model_name(getattr(cfg, "models", None), "mooded_b"))
    engine_summarizer = Gpt4AllAPIEngine(_model_name(getattr(cfg, "models", None), "summarizer"))
    engine_coder = Gpt4AllAPIEngine(_model_name(getattr(cfg, "models", None), "coder"))
    engines = EngineBundle(
        neutral_a=engine_a,
        mooded_b=engine_b,
        summarizer=engine_summarizer,
        coder=engine_coder,
    )

    # Personas
    preg = PersonaRegistry(Path(cfg.persona.dir))
    neutral = preg.load("Neutral")
    persona = preg.load(cfg.persona.current)

    # Prompts
    pl = PromptLoader(cfg.prompts.dir)
    P_plan = pl.load("planner")
    P_critic = pl.load("critic")
    P_explain = pl.load("explainer")
    P_judge = pl.load("judge")

    gen = GenOptions(**cfg.gen.__dict__)
    pool = []

    # Initialize sandbox once
    sandbox = Sandbox(
    allowlist=[
        "ls", "echo", "cat", "python3", "pip", "mkdir", "touch"
    ]
)
 # adjust allowlist as needed

    for cycle in range(cfg.runtime.cycles):
        log("cycle.start", id=cycle)

        inp = iface.get_input()
        recall = "(stub recall)"

        # pass the StagePrompt object P_plan, not its .system/.user
        plan = make_plan(inp, recall, persona.system_prompt, P_plan, engine_b, gen)

        crit = critique(plan, persona.system_prompt, P_critic, engine_b, gen)

        action = choose_action(
            [f"do:{inp}"],
            context=inp,
            persona_sys=persona.system_prompt,
            neutral_sys=neutral.system_prompt,
            engines=engines,
            gen=gen,
            prompts=pl,
            veto_risk=cfg.safety.veto_risk,
        )

        result = None
        if isinstance(action, ActionDecision):
            result = _execute_action_decision(action, sandbox)
        elif isinstance(action, str) and action.strip():
            result = sandbox.run(_format_sandbox_command(action))

        expl = explain(inp, plan, crit, neutral.system_prompt, P_explain, engine_a, gen)

        # memory gate (stub)
        stored = should_store(
            f"{inp}\n{plan}\n{crit}\n{result}",
            neutral.system_prompt,
            persona.system_prompt,
            P_judge.system,
            P_judge.user,
            engine_a,
            engine_b,
            gen,
            cfg.safety.veto_risk,
        )
        if stored:
            pool.append(expl)

        # training debate (stub)
        curate_if_needed(pool)

        result_summary = None
        if isinstance(result, dict):
            result_summary = result.get("stdout") or result.get("detail") or result.get("reason")
            if result_summary is None:
                result_summary = result
        elif result is not None:
            result_summary = result

        iface.send_output(f"[cycle {cycle}] action={action} result={result_summary}")

        # ---- Stability Drift Check ----
        try:
            # equilibrium means (set to whatever you consider baseline)
            muU, muR = 0.90, 0.10

            # extract actual metrics if available; fall back to placeholders
            try:
                Ut = getattr(action, "utility_a", 0.9)
                Rt = getattr(action, "risk_a", 0.1)
            except Exception:
                Ut, Rt = 0.9, 0.1

            def compute_drift(Ut, Rt, muU, muR):
                dU = abs(Ut - muU) / muU
                dR = abs(Rt - muR) / muR
                return max(dU, dR)

            drift = compute_drift(Ut, Rt, muU, muR)
            log("stability.check", drift=drift, util=Ut, risk=Rt)

            if drift > 0.10:
                log("stability.violation", drift=drift, cycle=cycle)
                # optional: restore safe parameters or flag for re-learning
                # alpha, tau = 1.2, 3.7
        except Exception as e:
            log("stability.error", error=str(e))
        # ---- End Stability Drift Check ----

        log("cycle.end", id=cycle)


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "config/config.yaml"
    raise SystemExit(main(path))

