from __future__ import annotations

import json
from collections import Counter
from typing import Any

import pandas as pd

from dart_research.cass.schema import ROLE_FIELDS, repair_patch_fields, repair_role_patch
from dart_research.eir.types import ProbeRecord


TARGET_ONLY_FIELDS = {
    "target_variable",
    "final_target_type",
    "relation_chain",
}

POSTPROCESS_ONLY_FIELDS = {
    "postprocess_flags",
}

DISCRETIZATION_ONLY_FIELDS = {
    "discretization_flags",
}

TARGET_PLUS_POSTPROCESS_FIELDS = TARGET_ONLY_FIELDS | POSTPROCESS_ONLY_FIELDS

DIAGNOSIS_METHODS = [
    "GRANITE_TARGET_ONLY_PATCH",
    "GRANITE_POSTPROCESS_ONLY_PATCH",
    "GRANITE_DISCRETIZATION_ONLY_PATCH",
    "GRANITE_TARGET_PLUS_POSTPROCESS_PATCH",
    "GRANITE_ROLE_ONLY_REPLAY",
]

FAMILY_CORE_METHODS = [
    "ATLAS_RG_ROLE_REPAIR_ONLY",
    "CASS_TARGET_POSTPROCESS_PATCH",
    "CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH",
    "CASS_CONSERVATIVE_GATE",
]


def action_map(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("action_name", "")): item for item in record.get("actions", [])}


def probe_map(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("action_name", "")): item for item in record.get("probes", [])}


def operator_base_fields(record: dict[str, Any]) -> dict[str, Any]:
    actions = action_map(record)
    operator = actions.get("OPERATOR_SCHEMA_TO_CODE_BASE", {})
    schema_raw = str(operator.get("metadata", {}).get("schema_fields", "")).strip()
    if schema_raw:
        try:
            parsed = json.loads(schema_raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    probes = probe_map(record)
    base_probe = probes.get("OPERATOR_SCHEMA_TO_CODE", {})
    fields = dict(base_probe.get("fields", {}))
    return {
        "target_variable": "result",
        "final_target_type": str(fields.get("target_type", "other")).strip().lower() or "other",
        "quantities": "",
        "operator_family": str(fields.get("operator_family", "other")).strip().lower() or "other",
        "relation_chain": str(fields.get("mapping", "")).strip(),
        "discretization_flags": str(fields.get("discretization", "none")).strip().lower() or "none",
        "postprocess_flags": "none",
        "geometry_formula_family": str(fields.get("formula_family", "none")).strip().lower() or "none",
        "unresolved_items_count": "0",
        "complete": fields.get("complete", 0),
    }


def partial_repair_fields(base_fields: dict[str, Any], source_fields: dict[str, Any], *, variant: str) -> dict[str, Any]:
    if variant == "GRANITE_TARGET_ONLY_PATCH":
        repaired = repair_patch_fields(base_fields, source_fields, allowed_fields=TARGET_ONLY_FIELDS)
    elif variant == "GRANITE_POSTPROCESS_ONLY_PATCH":
        repaired = repair_patch_fields(base_fields, source_fields, allowed_fields=POSTPROCESS_ONLY_FIELDS)
    elif variant == "GRANITE_DISCRETIZATION_ONLY_PATCH":
        repaired = repair_patch_fields(base_fields, source_fields, allowed_fields=DISCRETIZATION_ONLY_FIELDS)
    elif variant == "GRANITE_TARGET_PLUS_POSTPROCESS_PATCH":
        repaired = repair_patch_fields(base_fields, source_fields, allowed_fields=TARGET_PLUS_POSTPROCESS_FIELDS)
    elif variant == "GRANITE_ROLE_ONLY_REPLAY":
        repaired = repair_role_patch(base_fields, source_fields)
    else:
        raise ValueError(f"Unknown Granite diagnosis variant: {variant}")
    return repaired


def build_partial_probe(record: dict[str, Any], *, variant: str) -> ProbeRecord:
    probes = probe_map(record)
    base_fields = operator_base_fields(record)
    if variant == "GRANITE_ROLE_ONLY_REPLAY":
        source = dict(probes["ATLAS_RG_ROLE_REPAIR_ONLY"]["fields"])
    else:
        source = dict(probes["CASS_TARGET_POSTPROCESS_PATCH"]["fields"])
    repaired_fields = partial_repair_fields(base_fields, source, variant=variant)
    repaired_fields.update(
        {
            "patch_group": variant.lower(),
            "patch_mode": "diagnosis_replay",
            "source_variant": variant,
            "source_action": "ATLAS_RG_ROLE_REPAIR_ONLY" if variant == "GRANITE_ROLE_ONLY_REPLAY" else "CASS_TARGET_POSTPROCESS_PATCH",
        }
    )
    if "checker_target_score" in source:
        repaired_fields["checker_target_score"] = source["checker_target_score"]
        repaired_fields["checker_target_tags"] = source.get("checker_target_tags", "")
    if "checker_role_score" in source:
        repaired_fields["checker_role_score"] = source["checker_role_score"]
        repaired_fields["checker_role_tags"] = source.get("checker_role_tags", "")
    return ProbeRecord(
        action_name=variant,
        fields=repaired_fields,
        parse_ok=1,
        input_tokens=0,
        output_tokens=0,
        latency_s=0.0,
        raw_paths=list(source.get("raw_paths", [])),
    )


def _field_changed(base_fields: dict[str, Any], patch_fields: dict[str, Any], key: str) -> int:
    return int(str(base_fields.get(key, "")).strip() != str(patch_fields.get(key, "")).strip())


def _failure_category(record: dict[str, Any], *, patch_method: str) -> dict[str, Any] | None:
    actions = action_map(record)
    probes = probe_map(record)
    base_action = actions.get("OPERATOR_SCHEMA_TO_CODE_BASE")
    patch_action = actions.get(patch_method)
    patch_probe = probes.get(patch_method)
    if not base_action or not patch_action or not patch_probe:
        return None
    if int(base_action.get("correctness", 0)) != 1 or int(patch_action.get("correctness", 0)) != 0:
        return None

    base_fields = operator_base_fields(record)
    patch_fields = dict(patch_probe.get("fields", {}))
    target_change = int(
        any(
            _field_changed(base_fields, patch_fields, key)
            for key in ["target_variable", "final_target_type", "relation_chain"]
        )
    )
    postprocess_change = _field_changed(base_fields, patch_fields, "postprocess_flags")
    discretization_change = _field_changed(base_fields, patch_fields, "discretization_flags")
    role_interaction = int(
        "fieldwise_role_disagreement" in str(patch_fields.get("checker_role_tags", ""))
        or "per_item_total_confusion" in str(patch_fields.get("checker_role_tags", ""))
        or float(patch_fields.get("checker_role_score", 0) or 0) >= 2
    )
    code_generation_after_correct_patch = int(
        int(patch_action.get("execution_success", 0)) == 0
        or int(patch_action.get("action_failed", 0)) == 1
    )

    if code_generation_after_correct_patch:
        dominant = "code_generation_after_correct_patch"
    elif role_interaction and target_change:
        dominant = "quantity_role_interaction"
    elif discretization_change and not target_change and not postprocess_change:
        dominant = "wrong_discretization_flag"
    elif postprocess_change and not target_change:
        dominant = "wrong_postprocess_handling"
    elif target_change:
        dominant = "wrong_target_binding"
    elif postprocess_change or discretization_change:
        dominant = "wrong_postprocess_handling"
    else:
        dominant = "code_generation_after_correct_patch"

    return {
        "dataset": str(record.get("dataset", "")),
        "question_id": str(record.get("question_id", "")),
        "surface": str(record.get("metadata", {}).get("surface", "")),
        "cluster": str(record.get("metadata", {}).get("cluster", "")),
        "family": str(record.get("model_name", "")),
        "patch_method": patch_method,
        "base_correct": int(base_action.get("correctness", 0)),
        "patch_correct": int(patch_action.get("correctness", 0)),
        "target_change": target_change,
        "postprocess_change": postprocess_change,
        "discretization_change": discretization_change,
        "role_interaction": role_interaction,
        "code_generation_after_correct_patch": code_generation_after_correct_patch,
        "dominant_category": dominant,
    }


def baseline_right_patch_wrong_rows(
    records: list[dict[str, Any]],
    *,
    family_label: str,
    patch_method: str = "CASS_TARGET_POSTPROCESS_PATCH",
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for record in records:
        item = _failure_category(record, patch_method=patch_method)
        if item is None:
            continue
        item["family_label"] = family_label
        rows.append(item)
    return pd.DataFrame(rows)


def summarize_failure_categories(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame(columns=["family_label", "surface", "dominant_category", "count", "fraction"])
    grouped = (
        rows.groupby(["family_label", "surface", "dominant_category"], dropna=False)
        .size()
        .reset_index(name="count")
    )
    totals = grouped.groupby(["family_label", "surface"], dropna=False)["count"].transform("sum")
    grouped["fraction"] = grouped["count"] / totals
    return grouped.sort_values(["family_label", "surface", "count"], ascending=[True, True, False]).reset_index(drop=True)


def cross_family_failure_table(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame(columns=["family_label", "surface", "baseline_right_patch_wrong_count", "dominant_category_top"])
    summary = summarize_failure_categories(rows)
    tops = (
        summary.sort_values(["family_label", "surface", "count"], ascending=[True, True, False])
        .drop_duplicates(["family_label", "surface"])[["family_label", "surface", "dominant_category"]]
        .rename(columns={"dominant_category": "dominant_category_top"})
    )
    counts = (
        rows.groupby(["family_label", "surface"], dropna=False)
        .size()
        .reset_index(name="baseline_right_patch_wrong_count")
    )
    return counts.merge(tops, on=["family_label", "surface"], how="left").sort_values(["family_label", "surface"]).reset_index(drop=True)
