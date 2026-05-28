"""Role-grounded teacher-exemplar retrieval for the ATLAS-RG math runner.

Same shape as `atlas.retrieval`, but the exemplar records carry an extra
`role_signature` field. Retrieval prefers exemplars that share both the
semantic cluster *and* the role signature, so the role-grounded patch heads
have role-consistent demonstrations to imitate. Used only by
`atlas_rg.runner`.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from dart_research.oscar.compiler import parse_schema_fields, schema_to_preview

from .schema import parse_quantity_rows


TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(slots=True)
class TeacherRoleSeedExample:
    dataset: str
    question_id: str
    question: str
    cluster: str
    schema_fields: dict[str, Any]
    schema_preview: str
    role_signature: str
    audit_ok: int
    source_model: str


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_RE.findall(str(text).lower()))


def _role_signature(fields: dict[str, Any]) -> str:
    rows = parse_quantity_rows(str(fields.get("quantities", "")))
    signature = sorted(f"{row['role']}:{row['entity']}" for row in rows if row.get("role"))
    return ",".join(signature)


def _overlap_score(query: str, candidate: str) -> float:
    query_tokens = _tokenize(query)
    cand_tokens = _tokenize(candidate)
    if not query_tokens or not cand_tokens:
        return 0.0
    return len(query_tokens & cand_tokens) / max(len(query_tokens), 1)


def _role_overlap(query_roles: str, candidate_roles: str) -> float:
    query = set(filter(None, str(query_roles).split(",")))
    candidate = set(filter(None, str(candidate_roles).split(",")))
    if not query or not candidate:
        return 0.0
    return len(query & candidate) / max(len(query), 1)


def load_teacher_seed(path: Path | str) -> list[TeacherRoleSeedExample]:
    records: list[TeacherRoleSeedExample] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        fields = dict(raw.get("schema_fields", {}))
        preview = str(raw.get("schema_preview", "")).strip()
        if not preview and fields:
            preview = schema_to_preview(parse_schema_fields(fields))
        records.append(
            TeacherRoleSeedExample(
                dataset=str(raw.get("dataset", "gsm8k_train")),
                question_id=str(raw["question_id"]),
                question=str(raw["question"]),
                cluster=str(raw.get("cluster", "unknown")),
                schema_fields=fields,
                schema_preview=preview,
                role_signature=_role_signature(fields),
                audit_ok=int(raw.get("audit_ok", 0)),
                source_model=str(raw.get("source_model", "")),
            )
        )
    return records


def retrieve_teacher_exemplars(
    *,
    question: str,
    cluster: str,
    role_signature: str,
    seed_examples: list[TeacherRoleSeedExample],
    mode: str = "global",
    top_k: int = 3,
    exclude_question_id: str | None = None,
) -> list[TeacherRoleSeedExample]:
    candidates = [item for item in seed_examples if item.audit_ok]
    if exclude_question_id is not None:
        candidates = [item for item in candidates if item.question_id != exclude_question_id]
    if mode == "cluster_first":
        cluster_only = [item for item in candidates if item.cluster == cluster]
        if cluster_only:
            candidates = cluster_only
    ranked = sorted(
        candidates,
        key=lambda item: (
            _role_overlap(role_signature, item.role_signature),
            _overlap_score(question, item.question),
            int(item.cluster == cluster),
        ),
        reverse=True,
    )
    return ranked[:top_k]


def render_teacher_exemplars(examples: list[TeacherRoleSeedExample]) -> str:
    lines: list[str] = []
    for idx, item in enumerate(examples, start=1):
        critical = {
            "target_type": item.schema_fields.get("final_target_type", ""),
            "operator_family": item.schema_fields.get("operator_family", ""),
            "discretization_flags": item.schema_fields.get("discretization_flags", ""),
            "postprocess_flags": item.schema_fields.get("postprocess_flags", ""),
            "role_signature": item.role_signature,
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
