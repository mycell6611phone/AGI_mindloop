from pathlib import Path
from agi_mindloop.config import load_config, GenDefaults
from agi_mindloop.io_mod.interface import Interface
from agi_mindloop.io_mod.telemetry import log
from agi_mindloop.llm.engine import StubEngine, GenOptions
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


def _format_sandbox_command(action_text: str) -> str:
    text = (action_text or "").strip()
    if not text:
        return text
    if text.startswith(("sh:", "!")):
        return text
    return f"sh: {text}"


def _execute_action_decision(action: ActionDecision, sandbox: Sandbox):
    command = _format_sandbox_command(action.action)
    return sandbox.run(command)


def main(config_path: str):
    cfg = load_config(config_path)
    iface = Interface()

    # Engines (stub for now)
    engine_a = StubEngine("neutral_a")
    engine_b = StubEngine("mooded_b")
    engine_summarizer = StubEngine("summarizer")
    engine_coder = StubEngine("coder")
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
    sandbox = Sandbox(allowlist=["ls", "echo"])  # adjust allowlist as needed

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
        log("cycle.end", id=cycle)

    return 0


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "config/config.yaml"
    raise SystemExit(main(path))

