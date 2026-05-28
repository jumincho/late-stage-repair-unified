"""Prompt bank for EIR (Early-Intervention-Repair) math probes.

EIR was the earliest math round in this codebase. Each probe/action pair
asks the model a different question about its own draft:

- `freeform_probe` / `freeform_action`,
- `equation_probe` / `equation_action`,
- `checklist_probe` / `checklist_action`,
- `python_probe` / `python_action`,
- `localize_probe` / `localize_action`.

This module wraps the eleven `.txt` files under `prompts/eir/` into a
versioned dataclass that `eir.runner.EIRActionBankRunner` loads once.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dart_research.utils.prompts import PromptTemplate, load_prompt


@dataclass(slots=True)
class EIRPromptBank:
    draft: PromptTemplate
    freeform_probe: PromptTemplate
    equation_probe: PromptTemplate
    checklist_probe: PromptTemplate
    python_probe: PromptTemplate
    localize_probe: PromptTemplate
    freeform_action: PromptTemplate
    equation_action: PromptTemplate
    checklist_action: PromptTemplate
    python_action: PromptTemplate
    localize_action: PromptTemplate

    @classmethod
    def load(cls, repo_root: Path) -> "EIRPromptBank":
        root = repo_root / "prompts" / "eir"
        return cls(
            draft=load_prompt(root / "draft_tagged_v1.txt"),
            freeform_probe=load_prompt(root / "freeform_probe_v1.txt"),
            equation_probe=load_prompt(root / "equation_probe_v1.txt"),
            checklist_probe=load_prompt(root / "checklist_probe_v1.txt"),
            python_probe=load_prompt(root / "python_probe_v1.txt"),
            localize_probe=load_prompt(root / "localize_probe_v1.txt"),
            freeform_action=load_prompt(root / "freeform_action_v1.txt"),
            equation_action=load_prompt(root / "equation_action_v1.txt"),
            checklist_action=load_prompt(root / "checklist_action_v1.txt"),
            python_action=load_prompt(root / "python_action_v1.txt"),
            localize_action=load_prompt(root / "localize_action_v1.txt"),
        )

    def version_bundle(self) -> dict[str, str]:
        return {
            "draft": self.draft.version,
            "freeform_probe": self.freeform_probe.version,
            "equation_probe": self.equation_probe.version,
            "checklist_probe": self.checklist_probe.version,
            "python_probe": self.python_probe.version,
            "localize_probe": self.localize_probe.version,
            "freeform_action": self.freeform_action.version,
            "equation_action": self.equation_action.version,
            "checklist_action": self.checklist_action.version,
            "python_action": self.python_action.version,
            "localize_action": self.localize_action.version,
        }
