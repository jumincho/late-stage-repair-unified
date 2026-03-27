from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dart_research.utils.prompts import PromptTemplate, load_prompt


@dataclass(slots=True)
class ATLASPromptBank:
    teacher_schema: PromptTemplate
    retrieval_schema: PromptTemplate
    field_semantics: PromptTemplate
    field_quantities: PromptTemplate
    critical_field_repair: PromptTemplate

    @classmethod
    def load(cls, repo_root: Path) -> "ATLASPromptBank":
        root = repo_root / "prompts" / "atlas"
        return cls(
            teacher_schema=load_prompt(root / "teacher_schema_v1.txt"),
            retrieval_schema=load_prompt(root / "retrieval_schema_v1.txt"),
            field_semantics=load_prompt(root / "field_semantics_v1.txt"),
            field_quantities=load_prompt(root / "field_quantities_v1.txt"),
            critical_field_repair=load_prompt(root / "critical_field_repair_v1.txt"),
        )

    def version_bundle(self, *, base_bundle: dict[str, str]) -> dict[str, str]:
        bundle = dict(base_bundle)
        bundle.update(
            {
                "atlas_teacher_schema": self.teacher_schema.version,
                "atlas_retrieval_schema": self.retrieval_schema.version,
                "atlas_field_semantics": self.field_semantics.version,
                "atlas_field_quantities": self.field_quantities.version,
                "atlas_critical_field_repair": self.critical_field_repair.version,
            }
        )
        return bundle
