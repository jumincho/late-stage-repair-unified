"""Prompt bank for the CASS patch heads (math domain).

CASS — "Cluster-And-Schema-Steered" — is the first math round that introduces
*localized* patch operators on top of ATLAS-RG. This module loads the six
patch prompts under `prompts/cass/`:

- `teacher_patch` — initial teacher-style patch generator,
- `target_postprocess_patch` — patches only the target / postprocess flags,
- `role_patch` — patches the role table,
- `combined_patch` — patches both,
- `critical_role_patch` — repairs only the critical-role subset,
- `nonrole_patch` — repairs only the non-role schema.

Consumed by `cass.runner.CASSPatchBankRunner`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dart_research.utils.prompts import PromptTemplate, load_prompt


@dataclass(slots=True)
class CASSPromptBank:
    teacher_patch: PromptTemplate
    target_postprocess_patch: PromptTemplate
    role_patch: PromptTemplate
    combined_patch: PromptTemplate
    critical_role_patch: PromptTemplate
    nonrole_patch: PromptTemplate

    @classmethod
    def load(cls, repo_root: Path) -> "CASSPromptBank":
        root = repo_root / "prompts" / "cass"
        return cls(
            teacher_patch=load_prompt(root / "teacher_patch_v1.txt"),
            target_postprocess_patch=load_prompt(root / "target_postprocess_patch_v1.txt"),
            role_patch=load_prompt(root / "role_patch_v1.txt"),
            combined_patch=load_prompt(root / "combined_patch_v1.txt"),
            critical_role_patch=load_prompt(root / "critical_role_patch_v1.txt"),
            nonrole_patch=load_prompt(root / "nonrole_patch_v1.txt"),
        )

    def version_bundle(self, *, base_bundle: dict[str, str]) -> dict[str, str]:
        bundle = dict(base_bundle)
        bundle.update(
            {
                "cass_teacher_patch": self.teacher_patch.version,
                "cass_target_postprocess_patch": self.target_postprocess_patch.version,
                "cass_role_patch": self.role_patch.version,
                "cass_combined_patch": self.combined_patch.version,
                "cass_critical_role_patch": self.critical_role_patch.version,
                "cass_nonrole_patch": self.nonrole_patch.version,
            }
        )
        return bundle
