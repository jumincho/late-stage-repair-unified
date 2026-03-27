from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dart_research.utils.prompts import PromptTemplate, load_prompt


@dataclass(slots=True)
class CASSR4PromptBank:
    f1_plan: PromptTemplate
    f1_execute: PromptTemplate

    @classmethod
    def load(cls, repo_root: Path) -> "CASSR4PromptBank":
        root = repo_root / "prompts" / "cass_r4"
        return cls(
            f1_plan=load_prompt(root / "f1_plan_v1.txt"),
            f1_execute=load_prompt(root / "f1_execute_v1.txt"),
        )

    def version_bundle(self, *, base_bundle: dict[str, str]) -> dict[str, str]:
        bundle = dict(base_bundle)
        bundle.update(
            {
                "cass_r4_f1_plan": self.f1_plan.version,
                "cass_r4_f1_execute": self.f1_execute.version,
            }
        )
        return bundle
