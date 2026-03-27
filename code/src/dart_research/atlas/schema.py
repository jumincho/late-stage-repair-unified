from __future__ import annotations

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


def compose_fieldwise_schema_fields(semantic_fields: dict[str, Any], quantity_fields: dict[str, Any]) -> dict[str, Any]:
    combined = dict(SCHEMA_DEFAULTS)
    combined.update(
        {
            "final_target_type": semantic_fields.get("final_target_type", combined["final_target_type"]),
            "operator_family": semantic_fields.get("operator_family", combined["operator_family"]),
            "discretization_flags": semantic_fields.get("discretization_flags", combined["discretization_flags"]),
            "postprocess_flags": semantic_fields.get("postprocess_flags", combined["postprocess_flags"]),
            "geometry_formula_family": semantic_fields.get("geometry_formula_family", combined["geometry_formula_family"]),
            "target_variable": quantity_fields.get("target_variable", combined["target_variable"]),
            "quantities": quantity_fields.get("quantities", combined["quantities"]),
            "relation_chain": quantity_fields.get("relation_chain", combined["relation_chain"]),
            "unresolved_items_count": quantity_fields.get("unresolved_items_count", combined["unresolved_items_count"]),
        }
    )
    semantic_complete = str(semantic_fields.get("complete", "")).strip().lower() in {"yes", "true", "1"}
    quantity_complete = str(quantity_fields.get("complete", "")).strip().lower() in {"yes", "true", "1"}
    combined["complete"] = "yes" if semantic_complete and quantity_complete else "no"
    return combined


def repair_critical_schema_fields(base_fields: dict[str, Any], repair_fields: dict[str, Any]) -> dict[str, Any]:
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
    return repaired
