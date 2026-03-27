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

CRITICAL_ROLE_ROLES = {
    "target",
    "base",
    "delta",
    "per_item",
    "total",
    "remaining",
    "group_size",
    "num_groups",
}


def compose_role_grounded_schema(nonrole_fields: dict[str, Any], role_fields: dict[str, Any]) -> dict[str, Any]:
    combined = dict(SCHEMA_DEFAULTS)
    combined.update(
        {
            "final_target_type": nonrole_fields.get("final_target_type", combined["final_target_type"]),
            "operator_family": nonrole_fields.get("operator_family", combined["operator_family"]),
            "discretization_flags": nonrole_fields.get("discretization_flags", combined["discretization_flags"]),
            "postprocess_flags": nonrole_fields.get("postprocess_flags", combined["postprocess_flags"]),
            "geometry_formula_family": nonrole_fields.get("geometry_formula_family", combined["geometry_formula_family"]),
            "target_variable": role_fields.get("target_variable", combined["target_variable"]),
            "quantities": role_fields.get("quantities", combined["quantities"]),
            "relation_chain": role_fields.get("relation_chain", combined["relation_chain"]),
            "unresolved_items_count": role_fields.get("unresolved_items_count", combined["unresolved_items_count"]),
        }
    )
    nonrole_complete = str(nonrole_fields.get("complete", "")).strip().lower() in {"yes", "true", "1"}
    role_complete = str(role_fields.get("complete", "")).strip().lower() in {"yes", "true", "1"}
    combined["complete"] = "yes" if nonrole_complete and role_complete else "no"
    return combined


def repair_role_fields(base_fields: dict[str, Any], role_fields: dict[str, Any]) -> dict[str, Any]:
    repaired = dict(base_fields)
    for key in ["target_variable", "quantities", "relation_chain", "unresolved_items_count"]:
        value = str(role_fields.get(key, "")).strip()
        if value:
            repaired[key] = value
    if str(role_fields.get("complete", "")).strip():
        repaired["complete"] = role_fields["complete"]
    return repaired


def repair_nonrole_fields(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
    repaired = dict(base_fields)
    for key in [
        "final_target_type",
        "operator_family",
        "discretization_flags",
        "postprocess_flags",
        "geometry_formula_family",
    ]:
        value = str(repair_fields.get(key, "")).strip()
        if value:
            repaired[key] = value
    if str(repair_fields.get("complete", "")).strip():
        repaired["complete"] = repair_fields["complete"]
    return repaired


def repair_critical_role_fields(base_fields: dict[str, Any], role_fields: dict[str, Any]) -> dict[str, Any]:
    repaired = dict(base_fields)
    target_variable = str(role_fields.get("target_variable", "")).strip()
    if target_variable:
        repaired["target_variable"] = target_variable
    quantities = filter_quantities_by_roles(str(role_fields.get("quantities", "")), allowed_roles=CRITICAL_ROLE_ROLES)
    if quantities:
        repaired["quantities"] = quantities
    relation_chain = str(role_fields.get("relation_chain", "")).strip()
    if relation_chain:
        repaired["relation_chain"] = relation_chain
    if str(role_fields.get("complete", "")).strip():
        repaired["complete"] = role_fields["complete"]
    return repaired


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


def filter_quantities_by_roles(raw: str, *, allowed_roles: set[str]) -> str:
    rows = [row for row in parse_quantity_rows(raw) if row["role"] in allowed_roles]
    return serialize_quantity_rows(rows)


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


def _subset_signature(raw: str, *, roles: set[str]) -> str:
    rows = [row for row in parse_quantity_rows(raw) if row["role"] in roles]
    normalized = sorted((row["role"], row["entity"], row["value"], row["unit"]) for row in rows)
    return ";".join("|".join(item) for item in normalized)


def role_field_match(extracted_fields: dict[str, Any], teacher_fields: dict[str, Any]) -> dict[str, int]:
    extracted_quantities = str(extracted_fields.get("quantities", ""))
    teacher_quantities = str(teacher_fields.get("quantities", ""))
    return {
        "target_variable_match": int(
            str(extracted_fields.get("target_variable", "")).strip().lower()
            == str(teacher_fields.get("target_variable", "")).strip().lower()
        ),
        "quantity_role_match": int(normalize_quantities(extracted_quantities) == normalize_quantities(teacher_quantities)),
        "base_delta_match": int(_subset_signature(extracted_quantities, roles=BASE_DELTA_ROLES) == _subset_signature(teacher_quantities, roles=BASE_DELTA_ROLES)),
        "counting_role_match": int(_subset_signature(extracted_quantities, roles=COUNTING_ROLES) == _subset_signature(teacher_quantities, roles=COUNTING_ROLES)),
        "critical_role_match": int(_subset_signature(extracted_quantities, roles=CRITICAL_ROLE_ROLES) == _subset_signature(teacher_quantities, roles=CRITICAL_ROLE_ROLES)),
    }
