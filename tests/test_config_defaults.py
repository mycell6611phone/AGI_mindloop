from agi_mindloop.config import load_config
from agi_mindloop.personas import load_current
from agi_mindloop.prompts import PromptLoader


def test_default_config_loads_packaged_resources():
    cfg = load_config("config/config.yaml")

    persona = load_current(cfg.persona.dir, cfg.persona.current)
    assert "Behaviors:" in persona.system_prompt

    loader = PromptLoader(cfg.prompts.dir, cfg.prompts.files)
    planner_prompt = loader.load("planner")
    assert "You are a planner" in planner_prompt.system
    assert "{input}" in planner_prompt.user
