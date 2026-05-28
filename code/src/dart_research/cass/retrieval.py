"""Teacher-patch retrieval for the CASS math runner.

Where `atlas.retrieval` retrieves whole teacher schemas, CASS retrieves
teacher *patch deltas* — the (base_schema, patch_fields, patched_schema)
triples a previous teacher pass produced. The signatures used for matching
(`role_signature`, `target_postprocess_signature`, `nonrole_signature`) are
imported from `cass.schema`. The math runner uses this to ground its
localized patches in actually-observed teacher repairs.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from dart_research.oscar.compiler import parse_schema_fields, schema_to_preview

from .schema import nonrole_signature, role_signature, target_postprocess_signature


TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(slots=True)
class TeacherPatchSeedExample:
    dataset: str
    question_id: str
    question: str
    cluster: str
    base_schema_fields: dict[str, Any]
    patch_fields: dict[str, Any]
    patched_schema_fields: dict[str, Any]
    base_schema_preview: str
    patched_schema_preview: str
    target_signature: str
    role_signature: str
    nonrole_signature: str
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


def _signature_overlap(query: str, candidate: str) -> float:
    if not query or not candidate:
        return 0.0
    query_tokens = set(filter(None, re.split(r"[|,; ]+", str(query))))
    cand_tokens = set(filter(None, re.split(r"[|,; ]+", str(candidate))))
    if not query_tokens or not cand_tokens:
        return 0.0
    return len(query_tokens & cand_tokens) / max(len(query_tokens), 1)


def _subset_patch_fields(fields: dict[str, Any], *, patch_group: str) -> dict[str, Any]:
    if patch_group == "target_postprocess":
        keys = ["target_variable", "final_target_type", "relation_chain", "discretization_flags", "postprocess_flags", "complete"]
    elif patch_group == "role":
        keys = ["target_variable", "quantities", "relation_chain", "unresolved_items_count", "complete"]
    elif patch_group == "critical_role":
        keys = ["target_variable", "quantities", "relation_chain", "complete"]
    elif patch_group == "combined":
        keys = [
            "target_variable",
            "final_target_type",
            "quantities",
            "relation_chain",
            "discretization_flags",
            "postprocess_flags",
            "unresolved_items_count",
            "complete",
        ]
    else:
        keys = ["final_target_type", "operator_family", "discretization_flags", "postprocess_flags", "geometry_formula_family", "complete"]
    return {key: fields.get(key, "") for key in keys if str(fields.get(key, "")).strip()}


def load_teacher_seed(path: Path | str) -> list[TeacherPatchSeedExample]:
    records: list[TeacherPatchSeedExample] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        base_fields = dict(raw.get("base_schema_fields", {}))
        patch_fields = dict(raw.get("patch_fields", {}))
        patched_fields = dict(raw.get("patched_schema_fields", {}))
        base_preview = str(raw.get("base_schema_preview", "")).strip()
        if not base_preview and base_fields:
            base_preview = schema_to_preview(parse_schema_fields(base_fields))
        patched_preview = str(raw.get("patched_schema_preview", "")).strip()
        if not patched_preview and patched_fields:
            patched_preview = schema_to_preview(parse_schema_fields(patched_fields))
        records.append(
            TeacherPatchSeedExample(
                dataset=str(raw.get("dataset", "gsm8k_train")),
                question_id=str(raw["question_id"]),
                question=str(raw["question"]),
                cluster=str(raw.get("cluster", "unknown")),
                base_schema_fields=base_fields,
                patch_fields=patch_fields,
                patched_schema_fields=patched_fields,
                base_schema_preview=base_preview,
                patched_schema_preview=patched_preview,
                target_signature=target_postprocess_signature(base_fields),
                role_signature=role_signature(base_fields),
                nonrole_signature=nonrole_signature(base_fields),
                audit_ok=int(raw.get("audit_ok", 0)),
                source_model=str(raw.get("source_model", "")),
            )
        )
    return records


def retrieve_teacher_exemplars(
    *,
    question: str,
    cluster: str,
    base_fields: dict[str, Any],
    patch_group: str,
    seed_examples: list[TeacherPatchSeedExample],
    mode: str = "cluster_first",
    top_k: int = 3,
    exclude_question_id: str | None = None,
) -> list[TeacherPatchSeedExample]:
    candidates = [item for item in seed_examples if item.audit_ok]
    if exclude_question_id is not None:
        candidates = [item for item in candidates if item.question_id != exclude_question_id]
    if mode == "cluster_first":
        cluster_only = [item for item in candidates if item.cluster == cluster]
        if cluster_only:
            candidates = cluster_only

    query_target = target_postprocess_signature(base_fields)
    query_role = role_signature(base_fields)
    query_nonrole = nonrole_signature(base_fields)

    def _score(item: TeacherPatchSeedExample) -> tuple[float, float, int]:
        if patch_group == "target_postprocess":
            signature = _signature_overlap(query_target, item.target_signature)
        elif patch_group in {"role", "critical_role"}:
            signature = _signature_overlap(query_role, item.role_signature)
        elif patch_group == "combined":
            signature = 0.5 * _signature_overlap(query_target, item.target_signature) + 0.5 * _signature_overlap(query_role, item.role_signature)
        else:
            signature = _signature_overlap(query_nonrole, item.nonrole_signature)
        return (
            signature,
            _overlap_score(question, item.question),
            int(item.cluster == cluster),
        )

    ranked = sorted(candidates, key=_score, reverse=True)
    return ranked[:top_k]


def render_teacher_exemplars(examples: list[TeacherPatchSeedExample], *, patch_group: str) -> str:
    lines: list[str] = []
    for idx, item in enumerate(examples, start=1):
        lines.append(
            (
                f"Example {idx} | id={item.question_id}\n"
                f"Question: {item.question}\n"
                f"Base schema: {item.base_schema_preview}\n"
                f"Suggested patch fields: {json.dumps(_subset_patch_fields(item.patch_fields, patch_group=patch_group), ensure_ascii=True)}\n"
                f"Patched schema: {item.patched_schema_preview}"
            )
        )
    return "\n\n".join(lines) if lines else "No retrieved exemplars."
