# Robust JSON extractors for judge/evaluate outputs.

from __future__ import annotations
import json
import re
from typing import Any, Dict

_OBJ = re.compile(r"\{.*\}", re.DOTALL)

def _first_json_obj(text: str) -> Dict[str, Any]:
    for m in _OBJ.finditer(text or ""):
        blob = m.group(0).strip()
        try:
            return json.loads(blob)
        except Exception:
            continue
    return {}

def parse_judgment(text: str) -> Dict[str, Any]:
    """
    Expected:
      {"label":"ACCEPT|REJECT","reason":"...","risk":0.x,"importance":0.x,"uncertainty":0.x}
    """
    obj = _first_json_obj(text)
    label = str(obj.get("label", "")).upper()
    reason = str(obj.get("reason", "")).strip()[:200]
    risk = float(obj.get("risk", 0.0)) if isinstance(obj.get("risk", None), (int, float)) else None
    importance = float(obj.get("importance", 0.0)) if isinstance(obj.get("importance", None), (int, float)) else 0.0
    uncertainty = float(obj.get("uncertainty", 0.0)) if isinstance(obj.get("uncertainty", None), (int, float)) else 0.0
    return {"label": label, "reason": reason, "risk": risk, "importance": importance, "uncertainty": uncertainty}

def parse_eval(text: str) -> Dict[str, Any]:
    """
    Expected:
      {"label":"ACCEPT|REJECT","reason":"...","utility":0.x,"risk":0.x}
    """
    obj = _first_json_obj(text)
    label = str(obj.get("label", "")).upper()
    reason = str(obj.get("reason", "")).strip()[:200]
    utility = float(obj.get("utility", 0.0)) if isinstance(obj.get("utility", None), (int, float)) else 0.0
    risk = float(obj.get("risk", 0.0)) if isinstance(obj.get("risk", None), (int, float)) else 0.0
    return {"label": label, "reason": reason, "utility": utility, "risk": risk}


