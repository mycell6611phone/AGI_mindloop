from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agi_mindloop.action import *  # type: ignore[F401,F403]
from agi_mindloop.action import __all__ as action_all


EXPECTED_EXPORTS = {"choose_action", "ActionDecision", "Sandbox", "parse_action"}


def test_action_star_import_exports_expected_names():
    assert set(action_all) == EXPECTED_EXPORTS
    for name in EXPECTED_EXPORTS:
        assert name in globals(), f"{name} not found in star import globals"
