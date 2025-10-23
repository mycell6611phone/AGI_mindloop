# memory_debate.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple


DebateTurn = Dict[str, str]  # {"role": "permissive"|"critical", "content": str}


@dataclass
class DebateResult:
    decision: str  # 'accept' | 'reject' | 'needs_review'
    transcript: List[DebateTurn]


class MemoryDebate:
    """
    Orchestrate a two-agent debate to validate candidate memories before storage.

    Supply two callables that take a prompt string and return a model response string.
    Example signature: Callable[[str], str]
    """

    def __init__(self, permissive_client: Callable[[str], str], critical_client: Callable[[str], str], rounds: int = 3):
        if rounds < 1:
            raise ValueError("rounds must be >= 1")
        self.permissive = permissive_client
        self.critical = critical_client
        self.rounds = rounds

    def validate_memory(self, candidate_content: str) -> DebateResult:
        transcript: List[DebateTurn] = []

        base_instruction_perm = (
            "You are the Permissive Reviewer. Argue for the utility, accuracy, and relevance of the candidate memory. "
            "Be concrete about how it can improve future performance or decisions."
        )
        base_instruction_crit = (
            "You are the Critical Reviewer. Identify flaws, inaccuracies, privacy risks, duplication, or irrelevance in the candidate memory. "
            "Be rigorous and skeptical."
        )

        # Round 1: Initial analyses
        p_prompt = f"{base_instruction_perm}\n\nCandidate Memory:\n{candidate_content}"
        c_prompt = f"{base_instruction_crit}\n\nCandidate Memory:\n{candidate_content}"
        p_resp = self.permissive(p_prompt)
        c_resp = self.critical(c_prompt)
        transcript.append({"role": "permissive", "content": p_resp})
        transcript.append({"role": "critical", "content": c_resp})

        # Rebuttal rounds
        for r in range(1, self.rounds):
            p_rebuttal_prompt = (
                f"{base_instruction_perm}\n\nOpponent argument to address:\n{c_resp}\n\nCandidate Memory:\n{candidate_content}"
            )
            c_rebuttal_prompt = (
                f"{base_instruction_crit}\n\nOpponent argument to address:\n{p_resp}\n\nCandidate Memory:\n{candidate_content}"
            )
            p_resp = self.permissive(p_rebuttal_prompt)
            c_resp = self.critical(c_rebuttal_prompt)
            transcript.append({"role": "permissive", "content": p_resp})
            transcript.append({"role": "critical", "content": c_resp})

        # Simple aggregation heuristic for decision
        decision = self._decide(transcript)
        return DebateResult(decision=decision, transcript=transcript)

    def _decide(self, transcript: List[DebateTurn]) -> str:
        """
        Heuristic: If the last critical message contains any of these tokens, lean reject. If last permissive contains strong tokens, lean accept. Else needs_review.
        """
        if not transcript:
            return "needs_review"
        last_perm = next((t for t in reversed(transcript) if t["role"] == "permissive"), None)
        last_crit = next((t for t in reversed(transcript) if t["role"] == "critical"), None)
        crit_flags = ["inaccurate", "irrelevant", "duplicate", "privacy", "unsafe", "hallucination", "speculative"]
        perm_flags = ["high utility", "actionable", "accurate", "novel", "non-duplicative", "safe"]
        if last_crit and any(tok in last_crit["content"].lower() for tok in crit_flags):
            return "reject"
        if last_perm and any(tok in last_perm["content"].lower() for tok in [t.lower() for t in perm_flags]):
            return "accept"
        return "needs_review"

