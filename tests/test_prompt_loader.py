from agi_mindloop.prompts import PromptLoader


def test_evaluate_prompt_defaults_when_missing(tmp_path):
    loader = PromptLoader(root=str(tmp_path))

    prompt = loader.load("evaluate")

    assert "evaluate a proposed action" in prompt.system
    assert "{context}" in prompt.user
    assert "{action}" in prompt.user
