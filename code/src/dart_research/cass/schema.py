from __future__ import annotations

import re
from typing import Any

from dart_research.atlas_ms.schema import (
    SCHEMA_DEFAULTS,
    bundle_field_match,
    operator_bundle_signature,
    role_bundle_signature,
    target_bundle_signature,
)
from dart_research.atlas_rg.schema import (
    CRITICAL_ROLE_ROLES,
    filter_quantities_by_roles,
    parse_quantity_rows,
)


TARGET_POSTPROCESS_FIELDS = {
    "target_variable",
    "final_target_type",
    "relation_chain",
    "discretization_flags",
    "postprocess_flags",
}

ROLE_FIELDS = {
    "target_variable",
    "quantities",
    "relation_chain",
    "unresolved_items_count",
}

NONROLE_FIELDS = {
    "final_target_type",
    "operator_family",
    "discretization_flags",
    "postprocess_flags",
    "geometry_formula_family",
}


def baseline_schema_from_operator_probe(probe_fields: dict[str, Any]) -> dict[str, Any]:
    relation_chain = str(probe_fields.get("mapping", "")).strip()
    return {
        "target_variable": "result",
        "final_target_type": str(probe_fields.get("target_type", "other")).strip().lower() or "other",
        "quantities": "",
        "operator_family": str(probe_fields.get("operator_family", "other")).strip().lower() or "other",
        "relation_chain": relation_chain if relation_chain.lower() != "none" else "",
        "discretization_flags": str(probe_fields.get("discretization", "none")).strip().lower() or "none",
        "postprocess_flags": "none",
        "geometry_formula_family": str(probe_fields.get("formula_family", "none")).strip().lower() or "none",
        "unresolved_items_count": "0",
        "complete": "yes" if int(probe_fields.get("complete", 0)) else "no",
    }


def repair_patch_fields(base_fields: dict[str, Any], repair_fields: dict[str, Any], *, allowed_fields: set[str]) -> dict[str, Any]:
    repaired = dict(SCHEMA_DEFAULTS)
    repaired.update(base_fields)
    for key in allowed_fields:
        value = str(repair_fields.get(key, "")).strip()
        if value:
            repaired[key] = value
    if str(repair_fields.get("complete", "")).strip():
        repaired["complete"] = repair_fields["complete"]
    return repaired


def repair_target_postprocess_patch(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
    return repair_patch_fields(base_fields, repair_fields, allowed_fields=TARGET_POSTPROCESS_FIELDS)


def repair_role_patch(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
    return repair_patch_fields(base_fields, repair_fields, allowed_fields=ROLE_FIELDS)


def repair_target_postprocess_plus_role_patch(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
    repaired = repair_target_postprocess_patch(base_fields, repair_fields)
    return repair_role_patch(repaired, repair_fields)


def repair_critical_role_patch(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
    repaired = dict(SCHEMA_DEFAULTS)
    repaired.update(base_fields)
    target_variable = str(repair_fields.get("target_variable", "")).strip()
    if target_variable:
        repaired["target_variable"] = target_variable
    quantities = filter_quantities_by_roles(str(repair_fields.get("quantities", "")), allowed_roles=CRITICAL_ROLE_ROLES)
    if quantities:
        repaired["quantities"] = quantities
    relation_chain = str(repair_fields.get("relation_chain", "")).strip()
    if relation_chain:
        repaired["relation_chain"] = relation_chain
    if str(repair_fields.get("complete", "")).strip():
        repaired["complete"] = repair_fields["complete"]
    return repaired


def repair_nonrole_patch(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
    return repair_patch_fields(base_fields, repair_fields, allowed_fields=NONROLE_FIELDS)


def apply_teacher_patch_fields(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
    repaired = repair_target_postprocess_plus_role_patch(base_fields, repair_fields)
    return repair_nonrole_patch(repaired, repair_fields)


def target_postprocess_signature(fields: dict[str, Any]) -> str:
    return "|".join(
        [
            str(fields.get("final_target_type", "other")).strip().lower() or "other",
            str(fields.get("target_variable", "result")).strip().lower() or "result",
            str(fields.get("discretization_flags", "none")).strip().lower() or "none",
            str(fields.get("postprocess_flags", "none")).strip().lower() or "none",
        ]
    )


def nonrole_signature(fields: dict[str, Any]) -> str:
    return " || ".join(
        [
            operator_bundle_signature(fields),
            target_postprocess_signature(fields),
            str(fields.get("geometry_formula_family", "none")).strip().lower() or "none",
        ]
    )


def role_signature(fields: dict[str, Any]) -> str:
    return role_bundle_signature(fields)


def patch_field_match(extracted_fields: dict[str, Any], teacher_fields: dict[str, Any]) -> dict[str, int]:
    return bundle_field_match(extracted_fields, teacher_fields)


def _has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def target_postprocess_suspicion(
    question: str,
    *,
    base_fields: dict[str, Any],
    fieldwise_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = str(question).lower()
    tags: list[str] = []
    score = 0
    postprocess = str(base_fields.get("postprocess_flags", "none")).lower()
    discretization = str(base_fields.get("discretization_flags", "none")).lower()
    target_variable = str(base_fields.get("target_variable", "result")).lower()

    if _has_any(text, [r"\bhow many more\b", r"\bdifference\b", r"\bmore than\b", r"\bless than\b"]) and "difference" not in postprocess:
        tags.append("comparison_target_missing")
        score += 2
    if _has_any(text, [r"\bleft\b", r"\bleftover\b", r"\bremain\b", r"\bremaining\b", r"\brest\b", r"\bcomplement\b"]) and not _has_any(postprocess, [r"leftover", r"complement", r"difference"]):
        tags.append("leftover_complement_missing")
        score += 2
    if _has_any(text, [r"\bpercent\b", r"%", r"\bhalf\b", r"\bthird\b", r"\bquarter\b"]) and not _has_any(postprocess, [r"complement", r"total", r"difference"]):
        tags.append("percent_postprocess_weak")
        score += 1
    if _has_any(text, [r"\bat least\b", r"\bminimum\b", r"\bfull\b", r"\bwhole\b", r"\bround up\b", r"\bnext multiple\b"]) and not _has_any(discretization, [r"ceil", r"divisible", r"remainder"]):
        tags.append("ceil_signal_missing")
        score += 2
    if _has_any(text, [r"\bremainder\b", r"\bleft to\b", r"\bleft unloaded\b", r"\bleft to load\b"]) and not _has_any(discretization, [r"remainder", r"floor", r"ceil"]):
        tags.append("remainder_signal_missing")
        score += 2
    if target_variable in {"result", "value"} and _has_any(text, [r"\bhow many\b", r"\bhow much\b", r"\bwhat percentage\b", r"\bwhat fraction\b"]):
        tags.append("generic_target_binding")
        score += 1

    if fieldwise_fields is not None:
        if str(fieldwise_fields.get("target_variable", "")).strip() and str(fieldwise_fields.get("target_variable", "")).strip() != str(base_fields.get("target_variable", "")).strip():
            tags.append("fieldwise_target_disagreement")
            score += 1
        if str(fieldwise_fields.get("postprocess_flags", "")).strip() and str(fieldwise_fields.get("postprocess_flags", "")).strip() != str(base_fields.get("postprocess_flags", "")).strip():
            tags.append("fieldwise_postprocess_disagreement")
            score += 1
        if str(fieldwise_fields.get("discretization_flags", "")).strip() and str(fieldwise_fields.get("discretization_flags", "")).strip() != str(base_fields.get("discretization_flags", "")).strip():
            tags.append("fieldwise_discretization_disagreement")
            score += 1

    return {
        "checker_target_score": score,
        "checker_target_tags": ",".join(tags) if tags else "none",
        "checker_target_suspicious": int(score >= 2),
    }


def role_suspicion(
    question: str,
    *,
    base_fields: dict[str, Any],
    fieldwise_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = str(question).lower()
    tags: list[str] = []
    score = 0
    base_rows = parse_quantity_rows(str(base_fields.get("quantities", "")))
    base_roles = {row.get("role", "") for row in base_rows}
    field_rows = parse_quantity_rows(str(fieldwise_fields.get("quantities", ""))) if fieldwise_fields is not None else []
    field_roles = {row.get("role", "") for row in field_rows}

    if not base_rows and field_rows:
        tags.append("fieldwise_has_roles_baseline_empty")
        score += 1
    if _has_any(text, [r"\bfor every\b", r"\beach\b", r"\bper\b", r"\bper item\b", r"\bper day\b", r"\bper hour\b"]) and not ({"per_item", "total", "num_items", "group_size"} & base_roles):
        tags.append("per_item_total_confusion")
        score += 2
    if _has_any(text, [r"\bratio\b", r"\brate\b", r"\bproportion\b", r"\bmiles per\b"]) and not ({"rate_numerator", "rate_denominator", "base", "delta"} & base_roles):
        tags.append("rate_base_delta_missing")
        score += 2
    if _has_any(text, [r"\baverage\b", r"\bon average\b", r"\btwice\b", r"\bdouble\b", r"\btriple\b", r"\bthree times\b"]) and not ({"base", "delta", "total", "per_item", "num_items"} & base_roles):
        tags.append("average_repeated_role_missing")
        score += 1
    if _has_any(text, [r"\bleft\b", r"\bremaining\b", r"\bleftover\b", r"\bremainder\b"]) and not ({"remaining", "removed", "part", "target"} & base_roles):
        tags.append("remaining_role_missing")
        score += 2
    if fieldwise_fields is not None:
        if str(fieldwise_fields.get("target_variable", "")).strip() and str(fieldwise_fields.get("target_variable", "")).strip() != str(base_fields.get("target_variable", "")).strip():
            tags.append("fieldwise_target_binding_disagreement")
            score += 1
        if field_roles and field_roles != base_roles:
            tags.append("fieldwise_role_disagreement")
            score += 1

    return {
        "checker_role_score": score,
        "checker_role_tags": ",".join(tags) if tags else "none",
        "checker_role_suspicious": int(score >= 2),
    }
