from __future__ import annotations

import re
from typing import Any


SCHEMA_DEFAULTS = {
    "target_variable": "result",
    "final_target_type": "other",
    "quantities": "",
    "operator_family": "other",
    "relation_chain": "",
    "discretization_flags": "none",
    "postprocess_flags": "none",
    "geometry_formula_family": "none",
    "unresolved_items_count": "0",
    "complete": "no",
}

ROLE_PRIORITY = [
    "target",
    "total",
    "part",
    "remaining",
    "removed",
    "added",
    "base",
    "delta",
    "per_item",
    "num_items",
    "rate_numerator",
    "rate_denominator",
    "group_size",
    "num_groups",
    "comparison_base",
    "comparison_difference",
    "geometric_measure",
]

BASE_DELTA_ROLES = {
    "base",
    "delta",
    "comparison_base",
    "comparison_difference",
    "rate_numerator",
    "rate_denominator",
}

COUNTING_ROLES = {
    "per_item",
    "total",
    "part",
    "remaining",
    "removed",
    "added",
    "group_size",
    "num_groups",
    "num_items",
}

G1_FIELDS = {
    "operator_family",
    "discretization_flags",
    "geometry_formula_family",
}

G2_FIELDS = {
    "target_variable",
    "final_target_type",
    "relation_chain",
    "postprocess_flags",
}

G3_FIELDS = {
    "quantities",
    "unresolved_items_count",
}


def parse_quantity_rows(raw: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for chunk in re.split(r"[;\n]+", str(raw).strip()):
        chunk = chunk.strip()
        if not chunk:
            continue
        payload: dict[str, str] = {"name": "", "value": "", "unit": "none", "role": "none", "entity": "none"}
        for idx, part in enumerate(chunk.split("|")):
            piece = part.strip()
            if not piece:
                continue
            if idx == 0 and "=" in piece and not piece.lower().startswith(("name=", "value=", "unit=", "role=", "entity=")):
                left, right = piece.split("=", 1)
                payload["name"] = left.strip()
                payload["value"] = right.strip()
                continue
            if "=" in piece:
                key, value = piece.split("=", 1)
                payload[key.strip().lower()] = value.strip()
        if payload["name"] or payload["value"]:
            rows.append(
                {
                    "name": payload["name"].strip().lower(),
                    "value": payload["value"].strip().lower(),
                    "unit": payload["unit"].strip().lower(),
                    "role": payload["role"].strip().lower(),
                    "entity": payload["entity"].strip().lower(),
                }
            )
    return rows


def serialize_quantity_rows(rows: list[dict[str, str]]) -> str:
    rendered: list[str] = []
    for row in rows:
        rendered.append(
            (
                f"{row.get('name', '')}={row.get('value', '')}"
                f"|unit={row.get('unit', 'none')}"
                f"|role={row.get('role', 'none')}"
                f"|entity={row.get('entity', 'none')}"
            )
        )
    return "; ".join(rendered)


def normalize_quantities(raw: str) -> str:
    rows = parse_quantity_rows(raw)
    normalized = sorted(
        (
            row["role"],
            row["entity"],
            row["name"],
            row["value"],
            row["unit"],
        )
        for row in rows
    )
    return ";".join("|".join(item) for item in normalized)


def _subset_signature(raw: str, *, roles: set[str]) -> str:
    rows = [row for row in parse_quantity_rows(raw) if row["role"] in roles]
    normalized = sorted((row["role"], row["entity"], row["value"], row["unit"]) for row in rows)
    return ";".join("|".join(item) for item in normalized)


def _normalize_relation_chain(raw: str) -> str:
    return re.sub(r"\s+", "", str(raw).strip().lower())


def operator_bundle_signature(fields: dict[str, Any]) -> str:
    return "|".join(
        [
            str(fields.get("operator_family", "other")).strip().lower() or "other",
            str(fields.get("discretization_flags", "none")).strip().lower() or "none",
            str(fields.get("geometry_formula_family", "none")).strip().lower() or "none",
        ]
    )


def target_bundle_signature(fields: dict[str, Any]) -> str:
    return "|".join(
        [
            str(fields.get("final_target_type", "other")).strip().lower() or "other",
            str(fields.get("target_variable", "result")).strip().lower() or "result",
            str(fields.get("postprocess_flags", "none")).strip().lower() or "none",
            _normalize_relation_chain(fields.get("relation_chain", "")) or "none",
        ]
    )


def role_bundle_signature(fields: dict[str, Any]) -> str:
    roles = sorted(f"{row['role']}:{row['entity']}" for row in parse_quantity_rows(str(fields.get("quantities", ""))) if row.get("role"))
    unresolved = str(fields.get("unresolved_items_count", "0")).strip().lower() or "0"
    return "|".join([",".join(roles), unresolved])


def full_bundle_signature(fields: dict[str, Any]) -> str:
    return " || ".join(
        [
            operator_bundle_signature(fields),
            target_bundle_signature(fields),
            role_bundle_signature(fields),
        ]
    )


def repair_bundle_fields(base_fields: dict[str, Any], repair_fields: dict[str, Any], *, groups: tuple[str, ...]) -> dict[str, Any]:
    repaired = dict(SCHEMA_DEFAULTS)
    repaired.update(base_fields)
    allowed_keys: set[str] = set()
    if "g1" in groups:
        allowed_keys |= G1_FIELDS
    if "g2" in groups:
        allowed_keys |= G2_FIELDS
    if "g3" in groups:
        allowed_keys |= G3_FIELDS
    for key in allowed_keys:
        value = str(repair_fields.get(key, "")).strip()
        if value:
            repaired[key] = value
    if str(repair_fields.get("complete", "")).strip():
        repaired["complete"] = repair_fields["complete"]
    return repaired


def repair_operator_discretization_fields(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
    return repair_bundle_fields(base_fields, repair_fields, groups=("g1",))


def repair_target_postprocess_fields(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
    return repair_bundle_fields(base_fields, repair_fields, groups=("g2",))


def repair_role_only_fields(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
    return repair_bundle_fields(base_fields, repair_fields, groups=("g3",))


def repair_operator_plus_target_fields(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
    return repair_bundle_fields(base_fields, repair_fields, groups=("g1", "g2"))


def repair_target_plus_role_fields(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
    return repair_bundle_fields(base_fields, repair_fields, groups=("g2", "g3"))


def repair_operator_plus_role_fields(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
    return repair_bundle_fields(base_fields, repair_fields, groups=("g1", "g3"))


def repair_full_bundle_fields(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
    return repair_bundle_fields(base_fields, repair_fields, groups=("g1", "g2", "g3"))


def compose_fieldwise_bundle_fields(
    base_fields: dict[str, Any],
    *,
    operator_fields: dict[str, Any] | None = None,
    target_fields: dict[str, Any] | None = None,
    role_fields: dict[str, Any] | None = None,
    include_g1: bool = False,
    include_g2: bool = False,
    include_g3: bool = False,
) -> dict[str, Any]:
    repaired = dict(SCHEMA_DEFAULTS)
    repaired.update(base_fields)
    if include_g1 and operator_fields is not None:
        repaired = repair_operator_discretization_fields(repaired, operator_fields)
    if include_g2 and target_fields is not None:
        repaired = repair_target_postprocess_fields(repaired, target_fields)
    if include_g3 and role_fields is not None:
        repaired = repair_role_only_fields(repaired, role_fields)
    for fields in (operator_fields, target_fields, role_fields):
        if fields and str(fields.get("complete", "")).strip():
            repaired["complete"] = fields["complete"]
    return repaired


def bundle_field_match(extracted_fields: dict[str, Any], teacher_fields: dict[str, Any]) -> dict[str, int]:
    extracted_quantities = str(extracted_fields.get("quantities", ""))
    teacher_quantities = str(teacher_fields.get("quantities", ""))
    operator_family_match = int(
        str(extracted_fields.get("operator_family", "")).strip().lower()
        == str(teacher_fields.get("operator_family", "")).strip().lower()
    )
    discretization_match = int(
        str(extracted_fields.get("discretization_flags", "")).strip().lower()
        == str(teacher_fields.get("discretization_flags", "")).strip().lower()
    )
    geometry_formula_match = int(
        str(extracted_fields.get("geometry_formula_family", "")).strip().lower()
        == str(teacher_fields.get("geometry_formula_family", "")).strip().lower()
    )
    target_type_match = int(
        str(extracted_fields.get("final_target_type", "")).strip().lower()
        == str(teacher_fields.get("final_target_type", "")).strip().lower()
    )
    target_variable_match = int(
        str(extracted_fields.get("target_variable", "")).strip().lower()
        == str(teacher_fields.get("target_variable", "")).strip().lower()
    )
    postprocess_match = int(
        str(extracted_fields.get("postprocess_flags", "")).strip().lower()
        == str(teacher_fields.get("postprocess_flags", "")).strip().lower()
    )
    relation_chain_match = int(
        _normalize_relation_chain(extracted_fields.get("relation_chain", ""))
        == _normalize_relation_chain(teacher_fields.get("relation_chain", ""))
    )
    quantity_role_match = int(normalize_quantities(extracted_quantities) == normalize_quantities(teacher_quantities))
    base_delta_match = int(_subset_signature(extracted_quantities, roles=BASE_DELTA_ROLES) == _subset_signature(teacher_quantities, roles=BASE_DELTA_ROLES))
    counting_role_match = int(_subset_signature(extracted_quantities, roles=COUNTING_ROLES) == _subset_signature(teacher_quantities, roles=COUNTING_ROLES))
    g1_bundle_match = int(operator_family_match and discretization_match and geometry_formula_match)
    g2_bundle_match = int(target_type_match and target_variable_match and postprocess_match)
    g3_bundle_match = int(quantity_role_match)
    full_bundle_match = int(g1_bundle_match and g2_bundle_match and g3_bundle_match)
    return {
        "operator_family_match": operator_family_match,
        "discretization_match": discretization_match,
        "geometry_formula_match": geometry_formula_match,
        "target_type_match": target_type_match,
        "target_variable_match": target_variable_match,
        "postprocess_match": postprocess_match,
        "relation_chain_match": relation_chain_match,
        "quantity_role_match": quantity_role_match,
        "base_delta_match": base_delta_match,
        "counting_role_match": counting_role_match,
        "g1_bundle_match": g1_bundle_match,
        "g2_bundle_match": g2_bundle_match,
        "g3_bundle_match": g3_bundle_match,
        "full_bundle_match": full_bundle_match,
    }
