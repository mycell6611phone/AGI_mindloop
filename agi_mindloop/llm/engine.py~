# Interface + shared types. Prompt-only personas (system text), fixed gen options.

import json
from dataclasses import dataclass
from typing import Optional, Sequence, Protocol
from urllib import request as _request
from urllib import error as _error

GPT4ALL_API_PATH = "/v1/chat/completions"

@dataclass
class CompletionRequest:
    system: str
    user: str
    stop: Optional[Sequence[str]] = None

@dataclass
class GenOptions:
    temp: float = 0.6
    top_p: float = 0.95
    repeat_penalty: float = 1.1
    max_tokens: int = 1024
    ctx: int = 16384

class Engine(Protocol):
    def complete(self, req: CompletionRequest, gen: GenOptions) -> str: ...

# Simple stub (kept for tests)
class StubEngine:
    def __init__(self, name: str): self.name = name
    def complete(self, req: CompletionRequest, gen: GenOptions) -> str:
        return f"[{self.name}] {req.user[:120]}"


class Gpt4AllAPIEngine:
    """HTTP client for a locally running GPT4All REST server.

    The GPT4All desktop application exposes an OpenAI-compatible API that
    listens on ``http://localhost:4891`` by default.  We talk to that API
    directly using the standard library so no optional dependencies are
    required.  Responses are validated to ensure that a sensible error is
    raised when the server is unreachable or returns malformed JSON.
    """

    def __init__(self, model: str, host: str = "127.0.0.1", port: int = 4891, timeout: float = 30.0):
        self.model = model
        self.base_url = f"http://{host}:{port}{GPT4ALL_API_PATH}"
        self.timeout = timeout

    def complete(self, req: CompletionRequest, gen: GenOptions) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": req.system},
                {"role": "user", "content": req.user},
            ],
            "temperature": gen.temp,
            "top_p": gen.top_p,
            "max_tokens": gen.max_tokens,
        }
        if req.stop:
            payload["stop"] = list(req.stop)

        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        http_req = _request.Request(self.base_url, data=data, headers=headers, method="POST")

        try:
            with _request.urlopen(http_req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except _error.URLError as exc:
            raise RuntimeError(f"Failed to reach GPT4All API at {self.base_url}: {exc}") from exc

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("GPT4All API returned invalid JSON") from exc

        try:
            return parsed["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("GPT4All API response missing completion text") from exc

