from __future__ import annotations

from dataclasses import dataclass
import glob
import json
from pathlib import Path
from typing import Any

import pandas as pd

from dart_research.last_pack.formatting import parse_prompt_constraint_spec
from dart_research.last_pack.math_analysis import tag_math_failure_stage
from dart_research.lace.policy import ActionPolicyConfig, PolicyMetrics, evaluate_policy, stable_hash_bucket


UNIFIED_CONFIG = ActionPolicyConfig(
    action_names=("NO_INTERVENTION", "LOCAL_REPAIR", "GLOBAL_REWRITE_OR_RESTART"),
    success_columns={
        "NO_INTERVENTION": "direct_success",
        "LOCAL_REPAIR": "local_success",
        "GLOBAL_REWRITE_OR_RESTART": "global_success",
    },
    latency_columns={
        "NO_INTERVENTION": "direct_latency_s",
        "LOCAL_REPAIR": "local_latency_s",
        "GLOBAL_REWRITE_OR_RESTART": "global_latency_s",
    },
    direct_action="NO_INTERVENTION",
    local_actions=("LOCAL_REPAIR",),
    restart_actions=("GLOBAL_REWRITE_OR_RESTART",),
    tie_break_order=("NO_INTERVENTION", "LOCAL_REPAIR", "GLOBAL_REWRITE_OR_RESTART"),
)

POOLED_FEATURE_COLUMNS = [
    "localized_failure_count",
    "repairable_local_signal",
    "final_stage_suspicion",
    "localized_enough",
    "surface_bucket",
    "shared_failure_bucket",
]

MATH_FEATURE_COLUMNS = [
    "checker_target_score",
    "checker_role_score",
    "question_word_count",
    "question_number_count",
    "comparison_cue",
    "rate_unit_cue",
    "late_failure",
    "failure_stage",
]

FORMAT_FEATURE_COLUMNS = [
    "failed_instruction_count",
    "constraint_count",
    "response_word_count",
    "min_words",
    "num_bullets",
    "has_highlight_requirement",
    "has_keyword_requirement",
    "no_commas_requirement",
    "surface_bucket",
    "shared_failure_bucket",
]


def _load_jsonl_patterns(patterns: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pattern in patterns:
        for path_str in sorted(glob.glob(pattern)):
            with Path(path_str).open(encoding="utf-8") as handle:
                rows.extend(json.loads(line) for line in handle)
    return rows


def _action_correct(record: dict[str, Any], action_name: str) -> int:
    for action in record.get("actions", []):
        if action.get("action_name") == action_name:
            return int(action.get("correctness", 0))
    return 0


def _action_latency(record: dict[str, Any], action_name: str) -> float:
    for action in record.get("actions", []):
        if action.get("action_name") == action_name:
            return float(action.get("latency_s", 0.0))
    return 0.0


def _baseline_correct(record: dict[str, Any], baseline_name: str) -> int:
    return int(record.get("baselines", {}).get(baseline_name, {}).get("correctness", 0))


def _baseline_latency(record: dict[str, Any], baseline_name: str) -> float:
    return float(record.get("baselines", {}).get(baseline_name, {}).get("latency_s", 0.0))


def _constraint_category(prompt: str, instruction_ids: list[str]) -> str:
    spec = parse_prompt_constraint_spec(prompt)
    ids = [item.lower() for item in instruction_ids]
    lower_prompt = prompt.lower()
    if len(ids) > 1:
        return "multi_part_instructions"
    if spec["keyword_counts"] or any("keyword" in item for item in ids):
        return "keyword_inclusion"
    if spec["no_commas"] or any(token in item for item in ids for token in ["comma", "punct", "punctuation"]):
        return "punctuation_comma"
    if any(token in lower_prompt for token in ["json", "yaml", "xml"]) or any(
        token in item for item in ids for token in ["json", "format", "placeholder", "section", "bullet", "highlight"]
    ):
        return "json_or_structural_formatting"
    if any(token in item for item in ids for token in ["order", "first", "last", "nth", "ratio", "sentence_type", "position", "postscript"]):
        return "ordering_or_position"
    if spec["num_bullets"] is not None or spec["min_words"] is not None or any(
        token in item for item in ids for token in ["num_words", "num_sentences", "paragraph", "list", "bullet", "length", "frequency"]
    ):
        return "list_length_or_count"
    return "other_constraint"


def shared_failure_bucket_math(failure_stage: str) -> str:
    if failure_stage == "direct_correct":
        return "direct_correct"
    if failure_stage == "late_target_postprocess_error":
        return "final_requirement_realization"
    if failure_stage in {"late_target_role_interaction", "late_role_binding_error"}:
        return "binding_or_alignment"
    if failure_stage == "mid_executable_relation_error":
        return "executable_relation"
    return "structural_or_broad"


def shared_failure_bucket_format(constraint_category: str, direct_success: int) -> str:
    if int(direct_success) == 1:
        return "direct_correct"
    if constraint_category in {
        "keyword_inclusion",
        "punctuation_comma",
        "list_length_or_count",
        "json_or_structural_formatting",
        "ordering_or_position",
    }:
        return "final_requirement_realization"
    if constraint_category == "multi_part_instructions":
        return "binding_or_alignment"
    return "structural_or_broad"


def build_math_unified_frame(
    *,
    patterns: dict[str, list[str]],
    model_name: str,
    source_tag: str,
    local_action_name: str = "GRANITE_POSTPROCESS_ONLY_PATCH",
    global_baseline_name: str = "self_refine_1",
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for surface_name, surface_patterns in patterns.items():
        for record in _load_jsonl_patterns(surface_patterns):
            metadata = dict(record.get("metadata", {}))
            general_features = dict(record.get("general_features", {}))
            draft = dict(record.get("draft", {}))
            direct_success = int(draft.get("correctness", 0))
            failure_stage = "direct_correct" if direct_success else tag_math_failure_stage(record)
            target_score = int(metadata.get("checker_target_score", 0))
            role_score = int(metadata.get("checker_role_score", 0))
            local_signal = max(target_score, role_score)
            late_failure = int(failure_stage.startswith("late_"))
            rows.append(
                {
                    "module": "math",
                    "model_name": model_name,
                    "surface": surface_name,
                    "surface_bucket": "primary" if "cluster" in surface_name else "boundary",
                    "difficulty": "primary_math" if "cluster" in surface_name else "secondary_math",
                    "example_id": f"{surface_name}:{record['question_id']}",
                    "source_tag": source_tag,
                    "draft_source": str(metadata.get("draft_source", "fresh")),
                    "direct_success": direct_success,
                    "local_success": _action_correct(record, local_action_name),
                    "global_success": _baseline_correct(record, global_baseline_name),
                    "direct_latency_s": float(draft.get("latency_s", 0.0)),
                    "local_latency_s": _action_latency(record, local_action_name),
                    "global_latency_s": _baseline_latency(record, global_baseline_name),
                    "checker_target_score": target_score,
                    "checker_role_score": role_score,
                    "question_word_count": int(general_features.get("question_word_count", 0)),
                    "question_number_count": int(general_features.get("question_number_count", 0)),
                    "comparison_cue": int(general_features.get("comparison_cue", 0)),
                    "rate_unit_cue": int(general_features.get("rate_unit_cue", 0)),
                    "failure_stage": failure_stage,
                    "late_failure": late_failure,
                    "localized_failure_count": local_signal,
                    "repairable_local_signal": local_signal,
                    "final_stage_suspicion": late_failure,
                    "localized_enough": int(late_failure == 1 and local_signal >= 1),
                    "shared_failure_bucket": shared_failure_bucket_math(failure_stage),
                    "local_action_name": local_action_name,
                    "global_action_name": global_baseline_name,
                }
            )
    frame = pd.DataFrame(rows).drop_duplicates(subset=["example_id"]).reset_index(drop=True)
    return frame


def build_format_unified_frame(
    *,
    patterns: dict[str, list[str]],
    model_name: str,
    source_tag: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for surface_name, surface_patterns in patterns.items():
        for record in _load_jsonl_patterns(surface_patterns):
            direct = dict(record["direct_formatted"])
            prompt = str(record["prompt"])
            instruction_example = dict(record.get("instruction_example") or {})
            instruction_ids = [str(item) for item in instruction_example.get("instruction_id_list", [])]
            constraint_category = _constraint_category(prompt, instruction_ids)
            spec = parse_prompt_constraint_spec(prompt)
            direct_success = int(direct["success"])
            failed_instruction_count = int(direct.get("failed_instruction_count", 0))
            constraint_count = (
                len(spec["keyword_counts"])
                + int(spec["no_commas"])
                + int(spec["min_words"] is not None)
                + int(spec["min_highlight_sections"] is not None)
                + int(spec["num_bullets"] is not None)
            )
            repairable_local_signal = 0 if direct_success else max(0, 3 - failed_instruction_count)
            rows.append(
                {
                    "module": "format",
                    "model_name": model_name,
                    "surface": surface_name,
                    "surface_bucket": "primary" if surface_name == "ifeval_screened" else "boundary",
                    "difficulty": "primary_format" if surface_name == "ifeval_screened" else "boundary_format",
                    "example_id": f"{surface_name}:{record['example_id']}",
                    "source_tag": source_tag,
                    "direct_success": direct_success,
                    "local_success": int(record["solve_then_format"]["success"]),
                    "global_success": int(record["full_rewrite_on_failure"]["success"]),
                    "direct_latency_s": float(direct.get("latency_s", 0.0)),
                    "local_latency_s": float(record["solve_then_format"].get("latency_s", 0.0)),
                    "global_latency_s": float(record["full_rewrite_on_failure"].get("latency_s", 0.0)),
                    "failed_instruction_count": failed_instruction_count,
                    "constraint_count": int(constraint_count),
                    "response_word_count": len(str(direct.get("response_text", "")).split()),
                    "min_words": int(spec["min_words"] or 0),
                    "num_bullets": int(spec["num_bullets"] or 0),
                    "has_highlight_requirement": int(spec["min_highlight_sections"] is not None),
                    "has_keyword_requirement": int(bool(spec["keyword_counts"])),
                    "no_commas_requirement": int(bool(spec["no_commas"])),
                    "constraint_category": constraint_category,
                    "localized_failure_count": failed_instruction_count,
                    "repairable_local_signal": repairable_local_signal,
                    "final_stage_suspicion": int(direct_success == 0 and failed_instruction_count > 0),
                    "localized_enough": int(direct_success == 0 and failed_instruction_count <= 1),
                    "shared_failure_bucket": shared_failure_bucket_format(constraint_category, direct_success),
                    "local_action_name": "solve_then_format",
                    "global_action_name": "full_rewrite_on_failure",
                }
            )
    frame = pd.DataFrame(rows).drop_duplicates(subset=["example_id"]).reset_index(drop=True)
    return frame


def stable_split_manifest(frame: pd.DataFrame, *, ratio: float = 0.35) -> tuple[pd.DataFrame, pd.DataFrame]:
    if frame.empty:
        return frame.copy(), frame.copy()
    working = frame.copy()
    working["_bucket"] = [
        stable_hash_bucket(f"{row.model_name}::{row.module}::{row.surface}::{row.example_id}")
        for row in working.itertuples(index=False)
    ]
    eval_frame = working[working["_bucket"] < ratio].drop(columns="_bucket").reset_index(drop=True)
    train_frame = working[working["_bucket"] >= ratio].drop(columns="_bucket").reset_index(drop=True)
    return train_frame, eval_frame


def stable_split_triplet(
    frame: pd.DataFrame,
    *,
    seed: int,
    train_ratio: float = 0.5,
    cal_ratio: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if frame.empty:
        empty = frame.copy()
        return empty, empty, empty
    if train_ratio <= 0 or cal_ratio <= 0 or train_ratio + cal_ratio >= 1:
        raise ValueError("train_ratio and cal_ratio must be positive and leave non-zero eval mass.")
    working = frame.copy()
    working["_bucket"] = [
        stable_hash_bucket(f"{seed}::{row.model_name}::{row.module}::{row.surface}::{row.example_id}")
        for row in working.itertuples(index=False)
    ]
    train_cut = float(train_ratio)
    cal_cut = float(train_ratio + cal_ratio)
    train_frame = working[working["_bucket"] < train_cut].drop(columns="_bucket").reset_index(drop=True)
    cal_frame = working[(working["_bucket"] >= train_cut) & (working["_bucket"] < cal_cut)].drop(columns="_bucket").reset_index(drop=True)
    eval_frame = working[working["_bucket"] >= cal_cut].drop(columns="_bucket").reset_index(drop=True)
    return train_frame, cal_frame, eval_frame


@dataclass(slots=True)
class SharedSimpleRulePolicy:
    name: str
    kind: str
    params: dict[str, Any]
    config: ActionPolicyConfig
    rule_text: str

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        if frame.empty:
            return pd.Series(dtype="object")
        decisions = pd.Series(self.config.direct_action, index=frame.index, dtype="object")
        direct_success = frame["direct_success"].fillna(0).astype(int)
        final_stage = frame["final_stage_suspicion"].fillna(0).astype(int)
        localized = frame["localized_enough"].fillna(0).astype(int)
        signal = frame["repairable_local_signal"].fillna(0).astype(float)
        bucket = frame["shared_failure_bucket"].fillna("structural_or_broad").astype(str)
        surface_bucket = frame["surface_bucket"].fillna("boundary").astype(str)
        fail_mask = direct_success == 0
        decisions.loc[fail_mask] = self.config.restart_actions[0]
        if self.kind == "shared_2feature":
            local_mask = fail_mask & (final_stage >= int(self.params["late_required"])) & (localized >= int(self.params["localized_required"]))
            decisions.loc[local_mask] = self.config.local_actions[0]
            return decisions
        if self.kind == "shared_3feature":
            local_mask = (
                fail_mask
                & (final_stage >= int(self.params["late_required"]))
                & (localized >= int(self.params["localized_required"]))
                & (signal >= float(self.params["signal_threshold"]))
            )
            decisions.loc[local_mask] = self.config.local_actions[0]
            return decisions
        if self.kind == "shared_tree":
            allowed_buckets = set(self.params["allowed_buckets"])
            local_mask = (
                fail_mask
                & bucket.isin(allowed_buckets)
                & (
                    ((surface_bucket == "primary") & (signal >= float(self.params["primary_threshold"])))
                    | ((surface_bucket == "boundary") & (signal >= float(self.params["boundary_threshold"])))
                )
            )
            decisions.loc[local_mask] = self.config.local_actions[0]
            return decisions
        raise ValueError(f"Unsupported shared simple rule kind: {self.kind}")


def _metric_better(candidate: PolicyMetrics, best: PolicyMetrics | None) -> bool:
    if best is None:
        return True
    if candidate.utility != best.utility:
        return candidate.utility > best.utility
    if candidate.intervention_rate != best.intervention_rate:
        return candidate.intervention_rate < best.intervention_rate
    return candidate.avg_latency_s < best.avg_latency_s


def fit_shared_simple_policies(train_frame: pd.DataFrame, config: ActionPolicyConfig = UNIFIED_CONFIG) -> dict[str, SharedSimpleRulePolicy]:
    policies: dict[str, SharedSimpleRulePolicy] = {}

    best_policy: SharedSimpleRulePolicy | None = None
    best_metrics: PolicyMetrics | None = None
    for late_required in [0, 1]:
        for localized_required in [0, 1]:
            candidate = SharedSimpleRulePolicy(
                name="POOLED_SIMPLE_2FEATURE",
                kind="shared_2feature",
                params={"late_required": late_required, "localized_required": localized_required},
                config=config,
                rule_text=(
                    "if direct validator passes: NO_INTERVENTION; "
                    f"elif final_stage_suspicion >= {late_required} and localized_enough >= {localized_required}: LOCAL_REPAIR; "
                    "else: GLOBAL_REWRITE_OR_RESTART"
                ),
            )
            working = train_frame.copy()
            working["decision"] = candidate.predict(working)
            metrics = evaluate_policy(working, decision_col="decision", config=config)
            if _metric_better(metrics, best_metrics):
                best_policy = candidate
                best_metrics = metrics
    assert best_policy is not None
    policies[best_policy.name] = best_policy

    best_policy = None
    best_metrics = None
    for late_required in [0, 1]:
        for localized_required in [0, 1]:
            for signal_threshold in [1, 2, 3, 4, 5]:
                candidate = SharedSimpleRulePolicy(
                    name="POOLED_SIMPLE_3FEATURE",
                    kind="shared_3feature",
                    params={
                        "late_required": late_required,
                        "localized_required": localized_required,
                        "signal_threshold": signal_threshold,
                    },
                    config=config,
                    rule_text=(
                        "if direct validator passes: NO_INTERVENTION; "
                        f"elif final_stage_suspicion >= {late_required} and localized_enough >= {localized_required} and repairable_local_signal >= {signal_threshold}: LOCAL_REPAIR; "
                        "else: GLOBAL_REWRITE_OR_RESTART"
                    ),
                )
                working = train_frame.copy()
                working["decision"] = candidate.predict(working)
                metrics = evaluate_policy(working, decision_col="decision", config=config)
                if _metric_better(metrics, best_metrics):
                    best_policy = candidate
                    best_metrics = metrics
    assert best_policy is not None
    policies[best_policy.name] = best_policy

    best_policy = None
    best_metrics = None
    allowed_sets = [
        ["final_requirement_realization"],
        ["final_requirement_realization", "binding_or_alignment"],
        ["final_requirement_realization", "binding_or_alignment", "executable_relation"],
    ]
    for allowed in allowed_sets:
        for primary_threshold in [1, 2, 3, 4, 5]:
            for boundary_threshold in [1, 2, 3, 4, 5]:
                candidate = SharedSimpleRulePolicy(
                    name="POOLED_SIMPLE_THRESHOLDED_TREE",
                    kind="shared_tree",
                    params={
                        "allowed_buckets": allowed,
                        "primary_threshold": primary_threshold,
                        "boundary_threshold": boundary_threshold,
                    },
                    config=config,
                    rule_text=(
                        "if direct validator passes: NO_INTERVENTION; "
                        f"elif shared_failure_bucket in {allowed} and primary/local signal thresholds are ({primary_threshold}, {boundary_threshold}): LOCAL_REPAIR; "
                        "else: GLOBAL_REWRITE_OR_RESTART"
                    ),
                )
                working = train_frame.copy()
                working["decision"] = candidate.predict(working)
                metrics = evaluate_policy(working, decision_col="decision", config=config)
                if _metric_better(metrics, best_metrics):
                    best_policy = candidate
                    best_metrics = metrics
    assert best_policy is not None
    policies[best_policy.name] = best_policy
    return policies


def select_best_simple_policy(policies: dict[str, SharedSimpleRulePolicy], frame: pd.DataFrame, config: ActionPolicyConfig = UNIFIED_CONFIG) -> tuple[str, SharedSimpleRulePolicy]:
    best_name = ""
    best_policy = None
    best_metrics = None
    for name, policy in policies.items():
        working = frame.copy()
        working["decision"] = policy.predict(working)
        metrics = evaluate_policy(working, decision_col="decision", config=config)
        if _metric_better(metrics, best_metrics):
            best_name = name
            best_policy = policy
            best_metrics = metrics
    assert best_policy is not None
    return best_name, best_policy


def grouped_policy_rows(
    frame: pd.DataFrame,
    *,
    model_name: str,
    policy_map: list[tuple[str, str]],
    config: ActionPolicyConfig = UNIFIED_CONFIG,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    scopes: list[tuple[str, pd.DataFrame]] = [("overall", frame)]
    for module_name in sorted(frame["module"].dropna().unique()):
        module_frame = frame[frame["module"] == module_name].copy()
        scopes.append((f"{module_name}:overall", module_frame))
        for surface_name in sorted(module_frame["surface"].dropna().unique()):
            scopes.append((f"{module_name}:{surface_name}", module_frame[module_frame["surface"] == surface_name].copy()))
    for scope_name, scope_frame in scopes:
        if scope_frame.empty:
            continue
        module_name = "pooled" if scope_name == "overall" else scope_name.split(":", 1)[0]
        surface_name = "overall" if scope_name.endswith(":overall") or scope_name == "overall" else scope_name.split(":", 1)[1]
        for policy_name, decision_col in policy_map:
            metrics = evaluate_policy(scope_frame, decision_col=decision_col, config=config)
            row = metrics.to_row(scope=scope_name, policy=policy_name, n=len(scope_frame))
            row["model_name"] = model_name
            row["module"] = module_name
            row["surface_name"] = surface_name
            rows.append(row)
    return pd.DataFrame(rows)


def decision_success(frame: pd.DataFrame, decision_col: str, config: ActionPolicyConfig = UNIFIED_CONFIG) -> pd.Series:
    mapping = config.success_columns
    values = []
    for row in frame.itertuples(index=False):
        action_name = getattr(row, decision_col)
        values.append(int(getattr(row, mapping[action_name])))
    return pd.Series(values, index=frame.index)
