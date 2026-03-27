from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dart_research.utils.prompts import PromptTemplate, load_prompt


@dataclass(slots=True)
class ATLASRGPromptBank:
    teacher_role_schema: PromptTemplate
    retrieval_role_schema: PromptTemplate
    role_table: PromptTemplate
    nonrole_semantics: PromptTemplate
    role_repair: PromptTemplate
    nonrole_repair: PromptTemplate
    critical_role_repair: PromptTemplate

    @classmethod
    def load(cls, repo_root: Path) -> "ATLASRGPromptBank":
        root = repo_root / "prompts" / "atlas_rg"
        return cls(
            teacher_role_schema=load_prompt(root / "teacher_role_schema_v1.txt"),
            retrieval_role_schema=load_prompt(root / "retrieval_role_schema_v1.txt"),
            role_table=load_prompt(root / "role_table_v1.txt"),
            nonrole_semantics=load_prompt(root / "nonrole_semantics_v1.txt"),
            role_repair=load_prompt(root / "role_repair_v1.txt"),
            nonrole_repair=load_prompt(root / "nonrole_repair_v1.txt"),
            critical_role_repair=load_prompt(root / "critical_role_repair_v1.txt"),
        )

    def version_bundle(self, *, base_bundle: dict[str, str]) -> dict[str, str]:
        bundle = dict(base_bundle)
        bundle.update(
            {
                "atlas_rg_teacher_role_schema": self.teacher_role_schema.version,
                "atlas_rg_retrieval_role_schema": self.retrieval_role_schema.version,
                "atlas_rg_role_table": self.role_table.version,
                "atlas_rg_nonrole_semantics": self.nonrole_semantics.version,
                "atlas_rg_role_repair": self.role_repair.version,
                "atlas_rg_nonrole_repair": self.nonrole_repair.version,
                "atlas_rg_critical_role_repair": self.critical_role_repair.version,
            }
        )
        return bundle
