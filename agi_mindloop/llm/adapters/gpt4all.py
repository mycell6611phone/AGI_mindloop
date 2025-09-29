from pathlib import Path
from gpt4all import GPT4All
from agi_mindloop.llm.engine import Engine, CompletionRequest, GenOptions

class Gpt4AllEngine(Engine):
    def __init__(self, model_path: str):
        p = Path(model_path)
        self._m = GPT4All(model_name=p.name, model_path=str(p.parent))

    def complete(self, req: CompletionRequest, gen: GenOptions) -> str:
        prompt = f"<s>[SYSTEM]\n{req.system}\n[/SYSTEM]\n{req.user}"
        # gpt4all supports temp, top_p, tokens; repeat penalty varies by backend
        return self._m.generate(
            prompt,
            max_tokens=gen.max_tokens,
            temp=gen.temp,
            top_p=gen.top_p,
        )

