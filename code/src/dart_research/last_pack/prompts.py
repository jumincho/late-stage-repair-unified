from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dart_research.utils.prompts import PromptTemplate, load_prompt


@dataclass(slots=True)
class LastPackPromptBank:
    planning_direct: PromptTemplate
    planning_restart: PromptTemplate
    planning_suffix_repair: PromptTemplate
    format_full_rewrite: PromptTemplate
    format_solve_first: PromptTemplate
    format_apply_constraints: PromptTemplate
    format_only_patch: PromptTemplate

    @classmethod
    def load(cls, repo_root: Path) -> "LastPackPromptBank":
        root = repo_root / "prompts" / "last_pack"
        return cls(
            planning_direct=load_prompt(root / "planning_direct_v1.txt"),
            planning_restart=load_prompt(root / "planning_restart_v1.txt"),
            planning_suffix_repair=load_prompt(root / "planning_suffix_repair_v1.txt"),
            format_full_rewrite=load_prompt(root / "format_full_rewrite_v1.txt"),
            format_solve_first=load_prompt(root / "format_solve_first_v1.txt"),
            format_apply_constraints=load_prompt(root / "format_apply_constraints_v1.txt"),
            format_only_patch=load_prompt(root / "format_only_patch_v1.txt"),
        )

    def version_bundle(self) -> dict[str, str]:
        return {
            "planning_direct": self.planning_direct.version,
            "planning_restart": self.planning_restart.version,
            "planning_suffix_repair": self.planning_suffix_repair.version,
            "format_full_rewrite": self.format_full_rewrite.version,
            "format_solve_first": self.format_solve_first.version,
            "format_apply_constraints": self.format_apply_constraints.version,
            "format_only_patch": self.format_only_patch.version,
        }
