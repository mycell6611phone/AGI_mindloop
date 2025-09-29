# BGE-M3 embeddings. CPU by default to save VRAM.

from __future__ import annotations
from typing import List
import numpy as np

class Embedder:
    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu", use_fp16: bool = True):
        from FlagEmbedding import BGEM3FlagModel  # lazy import
        self.model = BGEM3FlagModel(model_name, use_fp16=use_fp16, device=device)

    @property
    def dim(self) -> int: return 1024

    def encode(self, texts: List[str]) -> np.ndarray:
        out = self.model.encode(texts, batch_size=32)["dense_vecs"]
        return np.asarray(out, dtype=np.float32)

