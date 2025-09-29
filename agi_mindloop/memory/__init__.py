from importlib import import_module
from typing import Any

__all__ = ["VectorStore", "MetaStore", "Embedder", "hybrid_recall"]

def __getattr__(name: str) -> Any:
    if name == "VectorStore":
        return _optional_import(".vector_store", "VectorStore")
    if name == "MetaStore":
        return _optional_import(".meta_store", "MetaStore")
    if name == "Embedder":
        return _optional_import(".embeddings", "Embedder")
    if name == "hybrid_recall":
        return _optional_import(".recall", "hybrid_recall")
    raise AttributeError(f"module {__name__} has no attribute {name}")


def _optional_import(module: str, attr: str) -> Any:
    try:
        mod = import_module(module, package=__name__)
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            f"Optional dependency required for agi_mindloop.memory.{attr} is missing: {exc.name}"
        ) from exc
    return getattr(mod, attr)

