from pathlib import Path
from typing import Optional
from types import SimpleNamespace

from agi_mindloop.config import load_config
from agi_mindloop.io_mod.interface import Interface
from agi_mindloop.io_mod.telemetry import log
from agi_mindloop.llm.engine import StubEngine, Gpt4AllAPIEngine, GenOptions
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
from agi_mindloop.memoryloop import Memory, MemoryLogger, MemoryDebate

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


def _engine_mode(cfg_runtime: object) -> str:
    raw = getattr(cfg_runtime, "engine", "gpt4all")
    text = str(raw).strip().lower()
    if not text:
        return "gpt4all"
    if text == "llama.cpp":
        return "gpt4all"
    return text


def _make_engine(model_key: str, cfg) -> Gpt4AllAPIEngine | StubEngine:
    model_name = _model_name(getattr(cfg, "models", None), model_key)
    runtime_cfg = getattr(cfg, "runtime", SimpleNamespace(engine="gpt4all"))
    mode = _engine_mode(runtime_cfg)
    if mode in {"gpt4all", "auto"}:
        return Gpt4AllAPIEngine(model_name)
    if mode in {"stub", "test"}:
        return StubEngine(model_name)
    return Gpt4AllAPIEngine(model_name)


def main(config_path: str):
    cfg = load_config(config_path)
    iface = Interface()

    engine_a = _make_engine("neutral_a", cfg)
    engine_b = _make_engine("mooded_b", cfg)
    engine_summarizer = _make_engine("summarizer", cfg)
    engine_coder = _make_engine("coder", cfg)
    engines = EngineBundle(
        neutral_a=engine_a,
        mooded_b=engine_b,
        summarizer=engine_summarizer,
        coder=engine_coder,
    )

    preg = PersonaRegistry(Path(cfg.persona.dir))
    neutral = preg.load("Neutral")
    persona = preg.load(cfg.persona.current)

    pl = PromptLoader(cfg.prompts.dir)
    P_plan = pl.load("planner")
    P_critic = pl.load("critic")
    P_explain = pl.load("explainer")
    P_judge = pl.load("judge")

    gen = GenOptions(**cfg.gen.__dict__)
    pool = []

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
