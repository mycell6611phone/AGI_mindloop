import os, shutil
from dataclasses import dataclass
from agi_mindloop.config import Config
from agi_mindloop.llm.engine import Engine



@dataclass
class EngineBundle:
    neutral_a: Engine
    mooded_b: Engine
    summarizer: Engine
    coder: Engine

def _choice(cfg: Config) -> str:
    choice = cfg.runtime.engine
    if choice == "auto":
        llama_cli = os.getenv("LLAMA_CLI", "./llama-cli")
        return "llama.cpp" if (shutil.which(llama_cli) or os.path.exists(llama_cli)) else "gpt4all"
    return choice

def build_engines(cfg: Config) -> EngineBundle:
    kind = _choice(cfg)
    if kind == "llama.cpp":
        from agi_mindloop.llm.adapters.llamaccp import LlamaCppEngine
        llama_cli = os.getenv("LLAMA_CLI", "./llama-cli")
        mk = lambda path: LlamaCppEngine(path, llama_cli=llama_cli)
    elif kind == "gpt4all":
        from agi_mindloop.llm.adapters.gpt4all import Gpt4AllEngine
        mk = lambda path: Gpt4AllEngine(path)
    else:
        raise ValueError(f"unknown engine: {kind}")
    return EngineBundle(
        neutral_a = mk(cfg.models.neutral_a),
        mooded_b  = mk(cfg.models.mooded_b),
        summarizer= mk(cfg.models.summarizer),
        coder     = mk(cfg.models.coder),
    )

