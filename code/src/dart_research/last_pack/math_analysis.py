from __future__ import annotations
import os

import glob
import json
from pathlib import Path
from typing import Any

import pandas as pd

DART_REPO_ROOT = os.environ.get("DART_REPO_ROOT", "/workspace/project")


MATH_SURFACE_GLOBS = {
    "easy": f"{DART_REPO_ROOT}/results/cass_main/easy_main_teacher_20260315_shard*/per_example.jsonl",
    "medium": f"{DART_REPO_ROOT}/results/cass_main/generic_main_teacher_20260315_shard*/per_example.jsonl",
    "hard": f"{DART_REPO_ROOT}/results/cass_main/cluster_main_teacher_20260315_shard*/per_example.jsonl",
}


def load_math_records(surface_globs: dict[str, str] | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for surface, pattern in (surface_globs or MATH_SURFACE_GLOBS).items():
        for path_str in sorted(glob.glob(pattern)):
            path = Path(path_str)
            with path.open() as handle:
                for line in handle:
                    payload = json.loads(line)
                    payload["_registered_surface"] = surface
                    payload["_source_path"] = str(path)
                    records.append(payload)
    return records


def _action_correct(record: dict[str, Any], action_name: str) -> int:
    for action in record.get("actions", []):
        if action.get("action_name") == action_name:
            return int(action.get("correctness", 0))
    return 0


def _baseline_correct(record: dict[str, Any], baseline_name: str) -> int:
    baseline = record.get("baselines", {}).get(baseline_name, {})
    return int(baseline.get("correctness", 0))


def tag_math_failure_stage(record: dict[str, Any]) -> str:
    keep_correct = int(record["draft"]["correctness"])
    if keep_correct:
        return "already_correct"
    base_correct = _action_correct(record, "OPERATOR_SCHEMA_TO_CODE_BASE")
    field_correct = _action_correct(record, "ATLAS_FIELDWISE_SCHEMA_TO_CODE")
    raw_correct = _action_correct(record, "RAW_PYTHON")
    target_correct = _action_correct(record, "CASS_TARGET_POSTPROCESS_PATCH") or _action_correct(record, "CASS_NONROLE_PATCH")
    role_correct = _action_correct(record, "CASS_ROLE_PATCH") or _action_correct(record, "CASS_CRITICAL_ROLE_PATCH") or _action_correct(record, "ATLAS_RG_ROLE_REPAIR_ONLY")
    combined_correct = _action_correct(record, "CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH")
    metadata = record.get("metadata", {})
    target_score = int(metadata.get("checker_target_score", 0))
    role_score = int(metadata.get("checker_role_score", 0))

    if combined_correct and (target_correct or role_correct):
        return "late_target_role_interaction"
    if target_correct and not (base_correct or field_correct):
        return "late_target_postprocess_error"
    if role_correct and not (base_correct or field_correct):
        return "late_role_binding_error"
    if combined_correct and not (base_correct or field_correct or target_correct or role_correct):
        return "late_target_role_interaction"
    if max(target_score, role_score) >= 5 and not (base_correct or field_correct):
        if target_score >= role_score:
            return "late_target_postprocess_error"
        return "late_role_binding_error"
    if raw_correct or base_correct or field_correct:
        return "mid_executable_relation_error"
    return "early_structural_misunderstanding"


def build_math_intervention_rows(records: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for record in records:
        stage = tag_math_failure_stage(record)
        surface = str(record.get("_registered_surface", record.get("metadata", {}).get("surface", "")))
        metadata = record.get("metadata", {})
        rows.append(
            {
                "question_id": record["question_id"],
                "dataset": record["dataset"],
                "surface": surface,
                "cluster": metadata.get("cluster", ""),
                "draft_correct": int(record["draft"]["correctness"]),
                "failure_stage": stage,
                "checker_target_score": int(metadata.get("checker_target_score", 0)),
                "checker_role_score": int(metadata.get("checker_role_score", 0)),
                "keep_correct": int(record["draft"]["correctness"]),
                "raw_python_correct": _action_correct(record, "RAW_PYTHON"),
                "operator_schema_correct": _action_correct(record, "OPERATOR_SCHEMA_TO_CODE_BASE"),
                "atlas_fieldwise_correct": _action_correct(record, "ATLAS_FIELDWISE_SCHEMA_TO_CODE"),
                "target_patch_correct": _action_correct(record, "CASS_TARGET_POSTPROCESS_PATCH"),
                "combined_patch_correct": _action_correct(record, "CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH"),
                "self_refine_restart_correct": _baseline_correct(record, "self_refine_1"),
                "freeform_restart_correct": _baseline_correct(record, "freeform_fixed1_same"),
            }
        )
    return pd.DataFrame(rows)


def summarize_math_stage_distribution(intervention_rows: pd.DataFrame) -> pd.DataFrame:
    subset = intervention_rows[intervention_rows["keep_correct"] == 0].copy()
    if subset.empty:
        return pd.DataFrame(columns=["surface", "failure_stage", "n", "share"])
    summary = (
        subset.groupby(["surface", "failure_stage"], dropna=False)
        .agg(n=("question_id", "count"))
        .reset_index()
    )
    totals = summary.groupby("surface")["n"].transform("sum")
    summary["share"] = summary["n"] / totals
    return summary.sort_values(["surface", "failure_stage"]).reset_index(drop=True)