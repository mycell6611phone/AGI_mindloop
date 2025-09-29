from pathlib import Path
import sys
import builtins
import importlib

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from agi_mindloop.config import (
    Config,
    RuntimeCfg,
    GenDefaults,
    Models,
    PersonaCfg,
    PromptsCfg,
    MemoryCfg,
    SafetyCfg,
)


@pytest.fixture
def no_gpt4all(monkeypatch):
    """Force any attempt to import gpt4all to fail."""

    monkeypatch.delitem(sys.modules, "gpt4all", raising=False)

    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "gpt4all" or name.startswith("agi_mindloop.llm.adapters.gpt4all"):
            raise ModuleNotFoundError("No module named 'gpt4all'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)


def test_llm_import_without_gpt4all_when_using_llama_cpp(monkeypatch, no_gpt4all):
    monkeypatch.setenv("LLAMA_CLI", "/fake/llama-cli")

    import agi_mindloop.llm as llm

    llamaccp = importlib.import_module("agi_mindloop.llm.adapters.llamaccp")
    monkeypatch.setattr(llamaccp.shutil, "which", lambda _: "/fake/llama-cli")
    monkeypatch.setattr(llamaccp.os.path, "exists", lambda _: True)

    cfg = Config(
        runtime=RuntimeCfg(engine="llama.cpp"),
        gen=GenDefaults(),
        models=Models("neutral.bin", "mood.bin", "sum.bin", "code.bin"),
        persona=PersonaCfg(),
        prompts=PromptsCfg(),
        memory=MemoryCfg(),
        safety=SafetyCfg(),
    )

    bundle = llm.build_engines(cfg)

    assert bundle.neutral_a is not None
    assert "gpt4all" not in sys.modules
