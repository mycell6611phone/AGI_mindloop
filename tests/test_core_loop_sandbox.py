from pathlib import Path
from types import SimpleNamespace
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agi_mindloop.core_loop import _execute_action_decision
from agi_mindloop.core_loop import main as core_main
from agi_mindloop.prompts import StagePrompt
from agi_mindloop.action.debate import ActionDecision
from agi_mindloop.action.experimenter import Sandbox as RealSandbox
from agi_mindloop.config import GenDefaults


def test_action_decision_executes_in_sandbox(tmp_path):
    sandbox = RealSandbox(allowlist=["echo"], cwd=str(tmp_path))
    decision = ActionDecision(
        action="echo hello sandbox",
        accept=True,
        reason_b="",
        reason_a="",
        utility_b=1.0,
        risk_b=0.0,
        utility_a=1.0,
        risk_a=0.0,
    )

    result = _execute_action_decision(decision, sandbox)

    assert result["ok"] is True
    assert "hello sandbox" in (result.get("stdout") or "")


def test_explain_receives_neutral_prompt(monkeypatch):
    neutral_prompt = "neutral system prompt"
    persona_prompt = "persona system prompt"

    class DummyRegistry:
        def __init__(self, root):
            self.root = root

        def load(self, name: str):
            if name == "Neutral":
                return SimpleNamespace(system_prompt=neutral_prompt)
            return SimpleNamespace(system_prompt=persona_prompt)

    class DummyPromptLoader:
        def __init__(self, root):
            self.root = root

        def load(self, stage: str) -> StagePrompt:
            return StagePrompt(system=f"{stage}-system", user=f"{stage}-user")

    class DummyInterface:
        def __init__(self):
            self.outputs = []

        def get_input(self) -> str:
            return "user input"

        def send_output(self, text: str) -> None:
            self.outputs.append(text)

    class DummySandbox:
        def __init__(self, allowlist=None, **kwargs):
            self.allowlist = allowlist or []
            self.runs = []

        def run(self, command: str):
            self.runs.append(command)
            return {"ok": True, "stdout": command}

    cfg = SimpleNamespace(
        runtime=SimpleNamespace(cycles=1),
        persona=SimpleNamespace(dir="unused", current="Analytical"),
        prompts=SimpleNamespace(dir="unused"),
        gen=GenDefaults(),
        safety=SimpleNamespace(veto_risk=0.5),
    )

    monkeypatch.setattr("agi_mindloop.core_loop.PersonaRegistry", DummyRegistry)
    monkeypatch.setattr("agi_mindloop.core_loop.PromptLoader", DummyPromptLoader)
    monkeypatch.setattr("agi_mindloop.core_loop.Interface", DummyInterface)
    monkeypatch.setattr("agi_mindloop.core_loop.Sandbox", DummySandbox)
    monkeypatch.setattr("agi_mindloop.core_loop.load_config", lambda path: cfg)
    monkeypatch.setattr("agi_mindloop.core_loop.make_plan", lambda *a, **kw: "PLAN")
    monkeypatch.setattr("agi_mindloop.core_loop.critique", lambda *a, **kw: "CRIT")
    monkeypatch.setattr("agi_mindloop.core_loop.choose_action", lambda *a, **kw: None)
    monkeypatch.setattr("agi_mindloop.core_loop.should_store", lambda *a, **kw: False)
    monkeypatch.setattr("agi_mindloop.core_loop.curate_if_needed", lambda *a, **kw: None)

    captured = {}

    def fake_explain(input_text, plan, critique_text, neutral_sys, stage, engine_a, gen):
        captured["args"] = (input_text, plan, critique_text, neutral_sys)
        return "EXPLANATION"

    monkeypatch.setattr("agi_mindloop.core_loop.explain", fake_explain)

    result = core_main("dummy-path")

    assert result == 0
    assert captured["args"][3] == neutral_prompt
    assert captured["args"][3] != persona_prompt
