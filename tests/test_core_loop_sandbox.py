from agi_mindloop.core_loop import _execute_action_decision
from agi_mindloop.action.debate import ActionDecision
from agi_mindloop.action.experimenter import Sandbox


def test_action_decision_executes_in_sandbox(tmp_path):
    sandbox = Sandbox(allowlist=["echo"], cwd=str(tmp_path))
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
