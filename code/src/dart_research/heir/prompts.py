from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dart_research.eir.prompts import EIRPromptBank
from dart_research.utils.prompts import PromptTemplate, load_prompt


@dataclass(slots=True)
class HEIRPromptBank:
    keep_probe: PromptTemplate

    @classmethod
    def load(cls, repo_root: Path) -> "HEIRPromptBank":
        root = repo_root / "prompts" / "heir"
        return cls(keep_probe=load_prompt(root / "keep_probe_v1.txt"))

    def version_bundle(self, *, eir_prompts: EIRPromptBank) -> dict[str, str]:
        bundle = eir_prompts.version_bundle()
        bundle["keep_probe"] = self.keep_probe.version
        return bundle
