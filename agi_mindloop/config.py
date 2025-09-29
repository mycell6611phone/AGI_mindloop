from dataclasses import dataclass, field
from pathlib import Path
from importlib import resources
import yaml


def _package_root() -> Path:
    package = resources.files("agi_mindloop")
    try:
        return Path(package)
    except TypeError:
        return Path(__file__).resolve().parent


def _default_persona_dir() -> str:
    return str(_package_root() / "personas")


def _default_prompts_dir() -> str:
    return str(_package_root() / "prompts")

@dataclass
class GenDefaults:
    temp: float = 0.6
    top_p: float = 0.95
    repeat_penalty: float = 1.1
    max_tokens: int = 1024
    ctx: int = 16384

@dataclass
class Models:
    neutral_a: str
    mooded_b: str
    summarizer: str
    coder: str

@dataclass
class PersonaCfg:
    current: str = "Analytical"
    dir: str = field(default_factory=_default_persona_dir)

@dataclass
class PromptsCfg:
    dir: str = field(default_factory=_default_prompts_dir)
    files: dict = None

@dataclass
class MemoryCfg:
    faiss_path: str = "./data/vectors.faiss"
    sqlite_path: str = "./data/meta.sqlite3"
    recall_k: int = 8
    alpha: float = 0.7

@dataclass
class SafetyCfg:
    allowlist_tools: list = None
    veto_risk: float = 0.6

@dataclass
class RuntimeCfg:
    cycles: int = 10
    dry_run: bool = True
    seed: int = 42
    engine: str = "llama.cpp"  # or gpt4all | auto

@dataclass
class Config:
    runtime: RuntimeCfg
    gen: GenDefaults
    models: Models
    persona: PersonaCfg
    prompts: PromptsCfg
    memory: MemoryCfg
    safety: SafetyCfg

def load_config(path: str) -> Config:
    data = yaml.safe_load(Path(path).read_text())
    return Config(
        runtime=RuntimeCfg(**data.get("runtime", {}), engine=data.get("engine","llama.cpp")),
        gen=GenDefaults(**data.get("llm", {}).get("gen_defaults", {})),
        models=Models(**data.get("models", {})),
        persona=PersonaCfg(**data.get("persona", {})),
        prompts=PromptsCfg(**data.get("prompts", {})),
        memory=MemoryCfg(**data.get("memory", {})),
        safety=SafetyCfg(**data.get("safety", {})),
    )

