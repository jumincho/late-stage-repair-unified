from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dart_research.utils.prompts import PromptTemplate, load_prompt


@dataclass(slots=True)
class CASSR2PromptBank:
    f1_lite: PromptTemplate
    prism_lite: PromptTemplate

    @classmethod
    def load(cls, repo_root: Path) -> "CASSR2PromptBank":
        root = repo_root / "prompts" / "cass_r2"
        return cls(
            f1_lite=load_prompt(root / "f1_lite_v1.txt"),
            prism_lite=load_prompt(root / "prism_lite_v1.txt"),
        )

    def version_bundle(self, *, base_bundle: dict[str, str]) -> dict[str, str]:
        bundle = dict(base_bundle)
        bundle.update(
            {
                "cass_r2_f1_lite": self.f1_lite.version,
                "cass_r2_prism_lite": self.prism_lite.version,
            }
        )
        return bundle
