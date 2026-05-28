"""Prompt bank for the same-context chase / confidence traces.

Loads the eight `.txt` prompt files under `prompts/confidence/` (draft,
verbalized-confidence-20, verbalized-confidence-100, challenge,
revise-same, self-refine critique, self-refine revise, alternatives) into a
versioned dataclass for `ChaseTraceRunner`. Each prompt carries its own
`v1` version header so the trace records can pin exact prompt versions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dart_research.utils.prompts import PromptTemplate, load_prompt


@dataclass(slots=True)
class ConfidencePromptBank:
    draft: PromptTemplate
    vc20: PromptTemplate
    vc100: PromptTemplate
    challenge: PromptTemplate
    revise_same: PromptTemplate
    self_refine_critique: PromptTemplate
    self_refine_revise: PromptTemplate
    alternatives: PromptTemplate

    @classmethod
    def load(cls, repo_root: Path) -> "ConfidencePromptBank":
        root = repo_root / "prompts" / "confidence"
        return cls(
            draft=load_prompt(root / "draft_tagged_v1.txt"),
            vc20=load_prompt(root / "verbal_conf_20_v1.txt"),
            vc100=load_prompt(root / "verbal_conf_100_v1.txt"),
            challenge=load_prompt(root / "challenge_tagged_v1.txt"),
            revise_same=load_prompt(root / "revise_same_tagged_v1.txt"),
            self_refine_critique=load_prompt(root / "self_refine_critique_tagged_v1.txt"),
            self_refine_revise=load_prompt(root / "self_refine_revise_tagged_v1.txt"),
            alternatives=load_prompt(root / "alternatives_tagged_v1.txt"),
        )

    def version_bundle(self) -> dict[str, str]:
        return {
            "draft": self.draft.version,
            "vc20": self.vc20.version,
            "vc100": self.vc100.version,
            "challenge": self.challenge.version,
            "revise_same": self.revise_same.version,
            "self_refine_critique": self.self_refine_critique.version,
            "self_refine_revise": self.self_refine_revise.version,
            "alternatives": self.alternatives.version,
        }
