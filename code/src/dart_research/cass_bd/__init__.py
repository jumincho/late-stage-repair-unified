"""CASS boundary-diagnosis (`cass_bd`) public API.

`cass_bd` is the boundary-diagnosis extension on top of the CASS math round.
It is not a fresh model run; it operates on already-collected math records
and asks "if we only patched a small slice of the schema, would the draft
have recovered?" — the partial-probe / partial-repair version of CASS.

This package only re-exports the analysis helpers used by
`scripts/cass_bd_collect_partial_replay.py` and the offline diagnosis
notebooks.
"""

from .analysis import (
    DIAGNOSIS_METHODS,
    FAMILY_CORE_METHODS,
    baseline_right_patch_wrong_rows,
    build_partial_probe,
    cross_family_failure_table,
    operator_base_fields,
    partial_repair_fields,
    summarize_failure_categories,
)

__all__ = [
    "DIAGNOSIS_METHODS",
    "FAMILY_CORE_METHODS",
    "baseline_right_patch_wrong_rows",
    "build_partial_probe",
    "cross_family_failure_table",
    "operator_base_fields",
    "partial_repair_fields",
    "summarize_failure_categories",
]
