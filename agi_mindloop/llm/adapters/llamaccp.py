import os
import shutil
from typing import Sequence
from agi_mindloop.llm.engine import Engine, CompletionRequest, GenOptions
from agi_mindloop.llm.util import run_and_capture

class LlamaCppEngine(Engine):
    def __init__(self, model_path: str, llama_cli: str | None = None):
        self.model = model_path
        self.llama_cli = llama_cli or os.getenv("LLAMA_CLI", "./llama-cli")
        if not shutil.which(self.llama_cli) and not os.path.exists(self.llama_cli):
            raise FileNotFoundError(f"llama-cli not found: {self.llama_cli}")

    def _base_args(self, gen: GenOptions) -> list[str]:
        args = [
            self.llama_cli, "-m", self.model,
            "--ctx-size", str(gen.ctx),
            "--temp", str(gen.temp),
            "--top-p", str(gen.top_p),
            "--repeat-penalty", str(gen.repeat_penalty),
            "-n", str(gen.max_tokens),
            "--ngl", "auto",
            "--type-kv", "q8_0",
        ]
        return args

    def _apply_stops(self, args: list[str], stops: Sequence[str] | None) -> list[str]:
        if stops:
            for s in stops:
                if s:
                    args += ["--stop", s]
        return args

    def complete(self, req: CompletionRequest, gen: GenOptions) -> str:
        prompt = f"<s>[SYSTEM]\n{req.system}\n[/SYSTEM]\n{req.user}"
        args = self._apply_stops(self._base_args(gen), req.stop)
        return run_and_capture(args, prompt)

