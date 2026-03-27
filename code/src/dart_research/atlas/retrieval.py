from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from dart_research.oscar.compiler import parse_schema_fields, schema_to_preview


TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(slots=True)
class TeacherSeedExample:
    dataset: str
    question_id: str
    question: str
    cluster: str
    schema_fields: dict[str, Any]
    schema_preview: str
    audit_ok: int
    source_model: str


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_RE.findall(str(text).lower()))


def _overlap_score(query: str, candidate: str) -> float:
    query_tokens = _tokenize(query)
    cand_tokens = _tokenize(candidate)
    if not query_tokens or not cand_tokens:
        return 0.0
    return len(query_tokens & cand_tokens) / max(len(query_tokens), 1)


def load_teacher_seed(path: Path | str) -> list[TeacherSeedExample]:
    records = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        fields = dict(raw.get("schema_fields", {}))
        preview = str(raw.get("schema_preview", "")).strip()
        if not preview and fields:
            preview = schema_to_preview(parse_schema_fields(fields))
        records.append(
            TeacherSeedExample(
                dataset=str(raw.get("dataset", "gsm8k_train")),
                question_id=str(raw["question_id"]),
                question=str(raw["question"]),
                cluster=str(raw.get("cluster", "unknown")),
                schema_fields=fields,
                schema_preview=preview,
                audit_ok=int(raw.get("audit_ok", 0)),
                source_model=str(raw.get("source_model", "")),
            )
        )
    return records


def retrieve_teacher_exemplars(
    *,
    question: str,
    cluster: str,
    seed_examples: list[TeacherSeedExample],
    mode: str = "global",
    top_k: int = 3,
    exclude_question_id: str | None = None,
) -> list[TeacherSeedExample]:
    candidates = [item for item in seed_examples if item.audit_ok]
    if exclude_question_id is not None:
        candidates = [item for item in candidates if item.question_id != exclude_question_id]
    if mode == "cluster_first":
        cluster_only = [item for item in candidates if item.cluster == cluster]
        if cluster_only:
            candidates = cluster_only
    ranked = sorted(
        candidates,
        key=lambda item: (_overlap_score(question, item.question), int(item.cluster == cluster)),
        reverse=True,
    )
    return ranked[:top_k]


def render_teacher_exemplars(examples: list[TeacherSeedExample]) -> str:
    lines: list[str] = []
    for idx, item in enumerate(examples, start=1):
        critical = {
            "target_type": item.schema_fields.get("final_target_type", ""),
            "operator_family": item.schema_fields.get("operator_family", ""),
            "discretization_flags": item.schema_fields.get("discretization_flags", ""),
            "postprocess_flags": item.schema_fields.get("postprocess_flags", ""),
        }
        lines.append(
            (
                f"Example {idx} | id={item.question_id} | cluster={item.cluster}\n"
                f"Question: {item.question}\n"
                f"Critical fields: {json.dumps(critical, ensure_ascii=True)}\n"
                f"Schema preview: {item.schema_preview}"
            )
        )
    return "\n\n".join(lines) if lines else "No retrieved exemplars."


def field_match(extracted_fields: dict[str, Any], teacher_fields: dict[str, Any]) -> dict[str, int]:
    def _norm(value: Any) -> str:
        if isinstance(value, list):
            return ",".join(sorted(str(item).strip().lower() for item in value if str(item).strip()))
        return str(value).strip().lower()

    return {
        "operator_family_match": int(_norm(extracted_fields.get("operator_family")) == _norm(teacher_fields.get("operator_family"))),
        "target_type_match": int(_norm(extracted_fields.get("final_target_type")) == _norm(teacher_fields.get("final_target_type"))),
        "discretization_match": int(_norm(extracted_fields.get("discretization_flags")) == _norm(teacher_fields.get("discretization_flags"))),
        "postprocess_match": int(_norm(extracted_fields.get("postprocess_flags")) == _norm(teacher_fields.get("postprocess_flags"))),
        "quantity_role_match": int(_norm(extracted_fields.get("quantities")) == _norm(teacher_fields.get("quantities"))),
    }
