"""Prompt bank for the TIER probe layer (math domain).

TIER is the probe layer that sits between EIR / HEIR (free-form repairs)
and OSCAR (compiled schemas). It asks four typed probes about the draft —
quantities, operators, equations, normalized values — and a matching action
for each. This module wraps the eight `.txt` files under `prompts/tier/`
into a versioned dataclass. The `OSCARPromptBank` merges TIER's version
bundle into its own so the schema-compile rounds pin the probe versions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dart_research.eir.prompts import EIRPromptBank
from dart_research.heir.prompts import HEIRPromptBank
from dart_research.utils.prompts import PromptTemplate, load_prompt


@dataclass(slots=True)
class TIERPromptBank:
    quantity_probe: PromptTemplate
    quantity_action: PromptTemplate
    operator_probe: PromptTemplate
    operator_action: PromptTemplate
    equation_probe: PromptTemplate
    equation_action: PromptTemplate
    normalized_probe: PromptTemplate
    normalized_action: PromptTemplate

    @classmethod
    def load(cls, repo_root: Path) -> "TIERPromptBank":
        root = repo_root / "prompts" / "tier"
        return cls(
            quantity_probe=load_prompt(root / "quantity_probe_v1.txt"),
            quantity_action=load_prompt(root / "quantity_action_v1.txt"),
            operator_probe=load_prompt(root / "operator_probe_v1.txt"),
            operator_action=load_prompt(root / "operator_action_v1.txt"),
            equation_probe=load_prompt(root / "equation_probe_v1.txt"),
            equation_action=load_prompt(root / "equation_action_v1.txt"),
            normalized_probe=load_prompt(root / "normalized_probe_v1.txt"),
            normalized_action=load_prompt(root / "normalized_action_v1.txt"),
        )

    def version_bundle(self, *, eir_prompts: EIRPromptBank, heir_prompts: HEIRPromptBank) -> dict[str, str]:
        bundle = heir_prompts.version_bundle(eir_prompts=eir_prompts)
        bundle.update(
            {
                "tier_quantity_probe": self.quantity_probe.version,
                "tier_quantity_action": self.quantity_action.version,
                "tier_operator_probe": self.operator_probe.version,
                "tier_operator_action": self.operator_action.version,
                "tier_equation_probe": self.equation_probe.version,
                "tier_equation_action": self.equation_action.version,
                "tier_normalized_probe": self.normalized_probe.version,
                "tier_normalized_action": self.normalized_action.version,
            }
        )
        return bundle
