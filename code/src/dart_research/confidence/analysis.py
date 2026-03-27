from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from dart_research.confidence.calibration import (
    LogisticCalibrator,
    aurc,
    auroc,
    average_precision,
    brier_score,
    choose_threshold_for_accuracy_rounds,
    expected_calibration_error,
    fit_logistic_calibrator,
    risk_coverage_curve,
)
from dart_research.evaluation.metrics import mcnemar_exact, paired_bootstrap_accuracy_delta
from dart_research.utils.io import read_json, write_json


PRIMARY_FEATURES = [
    "verbal_conf_20",
    "self_eval_yes_prob",
    "self_eval_margin",
    "answer_logprob_mean",
    "disagreement_fraction",
    "unique_answer_count",
    "dinco_gap",
    "delta_verbal_conf_20",
    "delta_self_eval_margin",
    "delta_answer_logprob_mean",
    "answer_changed",
]


def load_trace_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_json(path, lines=True)
    return frame


def flatten_stage_rows(trace_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for record in trace_frame.to_dict(orient="records"):
        stages = record["stages"]
        previous = None
        for stage in stages:
            signals = stage["signals"]
            row = {
                "dataset": record["dataset"],
                "question_id": record["question_id"],
                "model_name": record["model_name"],
                "stage_index": stage["stage_index"],
                "correct": stage["correctness"],
                "answer_changed": stage.get("answer_changed", 0),
                "verbal_conf_20": signals.get("verbal_conf_20"),
                "verbal_conf_100": signals.get("verbal_conf_100"),
                "self_eval_yes_prob": signals.get("self_eval_yes_prob"),
                "self_eval_margin": signals.get("self_eval_margin"),
                "answer_logprob": signals.get("answer_logprob"),
                "answer_logprob_mean": signals.get("answer_logprob_mean"),
                "disagreement_fraction": signals.get("disagreement_fraction"),
                "unique_answer_count": signals.get("unique_answer_count"),
                "dinco_gap": signals.get("dinco_gap"),
                "alt_best_logprob": signals.get("alt_best_logprob"),
            }
            if previous is None:
                row["delta_verbal_conf_20"] = 0.0
                row["delta_self_eval_margin"] = 0.0
                row["delta_answer_logprob_mean"] = 0.0
            else:
                row["delta_verbal_conf_20"] = _delta(signals.get("verbal_conf_20"), previous["signals"].get("verbal_conf_20"))
                row["delta_self_eval_margin"] = _delta(signals.get("self_eval_margin"), previous["signals"].get("self_eval_margin"))
                row["delta_answer_logprob_mean"] = _delta(signals.get("answer_logprob_mean"), previous["signals"].get("answer_logprob_mean"))
            rows.append(row)
            previous = stage
    return pd.DataFrame(rows)


def _delta(current: Any, previous: Any) -> float:
    current_value = float(current or 0.0)
    previous_value = float(previous or 0.0)
    return current_value - previous_value


def benchmark_signals(stage_frame: pd.DataFrame) -> pd.DataFrame:
    metrics: list[dict[str, Any]] = []
    for signal in [
        "verbal_conf_20",
        "self_eval_yes_prob",
        "answer_logprob_mean",
        "dinco_gap",
    ]:
        subset = stage_frame[stage_frame[signal].notna()].copy()
        probs = _normalize_signal(subset[signal].tolist())
        labels = subset["correct"].astype(int).tolist()
        metrics.append(
            {
                "signal": signal,
                "n": len(subset),
                "auroc": auroc(probs, labels),
                "auprc": average_precision(probs, labels),
                "brier": brier_score(probs, labels),
                "ece": expected_calibration_error(probs, labels),
                "aurc": aurc(probs, labels),
            }
        )
    return pd.DataFrame(metrics).sort_values("auroc", ascending=False).reset_index(drop=True)


def _normalize_signal(values: list[float]) -> list[float]:
    if not values:
        return []
    low = min(values)
    high = max(values)
    if high - low < 1e-8:
        return [0.5 for _ in values]
    return [(value - low) / (high - low) for value in values]


def fit_primary_calibrator(stage_frame: pd.DataFrame, feature_names: list[str] | None = None) -> LogisticCalibrator:
    feature_names = feature_names or list(PRIMARY_FEATURES)
    subset = stage_frame.copy()
    rows = subset[feature_names].fillna(0.0).to_dict(orient="records")
    labels = subset["correct"].astype(int).tolist()
    return fit_logistic_calibrator(rows, labels, feature_names)


def attach_calibrated_score(stage_frame: pd.DataFrame, calibrator: LogisticCalibrator) -> pd.DataFrame:
    frame = stage_frame.copy()
    rows = frame[calibrator.feature_names].fillna(0.0).to_dict(orient="records")
    frame["chase_score"] = calibrator.predict_proba(rows)
    return frame


def rule_score(frame: pd.DataFrame) -> pd.Series:
    vc = frame["verbal_conf_20"].fillna(0.0)
    yes_prob = frame["self_eval_yes_prob"].fillna(0.0)
    disagreement = frame["disagreement_fraction"].fillna(1.0)
    dinco = _normalize_signal(frame["dinco_gap"].fillna(0.0).tolist())
    base = pd.Series(dinco, index=frame.index)
    return pd.concat([vc, yes_prob, 1.0 - disagreement, base], axis=1).min(axis=1)


def choose_thresholds_from_stage_scores(stage_frame: pd.DataFrame, score_column: str, *, abstain_allowed: bool) -> float:
    by_example = []
    by_correct = []
    for _, group in stage_frame.sort_values("stage_index").groupby(["dataset", "question_id"], dropna=False):
        by_example.append(group[score_column].fillna(0.0).tolist())
        by_correct.append(group["correct"].astype(int).tolist())
    return choose_threshold_for_accuracy_rounds(by_example, by_correct, abstain_allowed=abstain_allowed)


def evaluate_methods(trace_frame: pd.DataFrame, stage_frame: pd.DataFrame, *, tau_vc: float, tau_rule: float, tau_chase: float) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    stage_lookup = {
        (record["dataset"], record["question_id"], record["model_name"]): record
        for record in trace_frame.to_dict(orient="records")
    }
    grouped = stage_frame.sort_values("stage_index").groupby(["dataset", "question_id", "model_name"], dropna=False)
    for key, group in grouped:
        record = stage_lookup[key]
        stages = record["stages"]
        rows.extend(
            [
                _stage_method_row(record, stages, "direct_cot", stage_index=0, abstained=False),
                _self_refine_row(record),
                _stage_method_row(record, stages, "freeform_fixed1_same", stage_index=min(1, len(stages) - 1), abstained=False),
                _stage_method_row(record, stages, "freeform_fixed2_same", stage_index=min(2, len(stages) - 1), abstained=False),
            ]
        )
        rows.append(_adaptive_row(record, group, "confidence_only_selective_abstain", "verbal_conf_20", tau_vc, max_stage=0, abstain_allowed=True))
        rows.append(_adaptive_row(record, group, "raw_vc_gate", "verbal_conf_20", tau_vc, max_stage=2, abstain_allowed=False))
        rows.append(_adaptive_row(record, group, "robust_rule_gate", "rule_score", tau_rule, max_stage=2, abstain_allowed=False))
        rows.append(_adaptive_row(record, group, "CHASE_calibrated", "chase_score", tau_chase, max_stage=2, abstain_allowed=False))
        rows.append(_adaptive_row(record, group, "CHASE_calibrated_selective", "chase_score", tau_chase, max_stage=2, abstain_allowed=True))
    return pd.DataFrame(rows)


def _stage_method_row(record: dict[str, Any], stages: list[dict[str, Any]], method: str, *, stage_index: int, abstained: bool) -> dict[str, Any]:
    stage = stages[stage_index]
    usage = _cumulative_usage(stages, stage_index)
    return {
        "dataset": record["dataset"],
        "question_id": record["question_id"],
        "model_name": record["model_name"],
        "method": method,
        "prediction": stage["answer"],
        "prediction_normalized": stage["normalized_answer"],
        "correct": int(stage["correctness"]),
        "direct_correct": int(stages[0]["correctness"]),
        "rounds": stage_index,
        "latency_s": usage["latency_s"],
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "abstained": int(abstained),
        "answered": int(not abstained),
    }


def _self_refine_row(record: dict[str, Any]) -> dict[str, Any]:
    result = record["self_refine"]
    return {
        "dataset": record["dataset"],
        "question_id": record["question_id"],
        "model_name": record["model_name"],
        "method": "self_refine_1",
        "prediction": result["answer"],
        "prediction_normalized": result["normalized_answer"],
        "correct": int(result["correctness"]),
        "direct_correct": int(record["stages"][0]["correctness"]),
        "rounds": 1,
        "latency_s": float(result["latency_s"]),
        "input_tokens": int(result["input_tokens"]),
        "output_tokens": int(result["output_tokens"]),
        "abstained": 0,
        "answered": 1,
    }


def _adaptive_row(
    record: dict[str, Any],
    group: pd.DataFrame,
    method: str,
    score_column: str,
    threshold: float,
    *,
    max_stage: int,
    abstain_allowed: bool,
) -> dict[str, Any]:
    ordered = group.sort_values("stage_index")
    chosen = min(max_stage, len(ordered) - 1)
    for _, row in ordered.iterrows():
        stage_index = int(row["stage_index"])
        if stage_index > max_stage:
            break
        if float(row[score_column]) >= threshold:
            chosen = stage_index
            break
        chosen = stage_index
    stages = record["stages"]
    stage = stages[chosen]
    abstained = abstain_allowed and float(ordered.iloc[chosen][score_column]) < threshold
    usage = _cumulative_usage(stages, chosen)
    return {
        "dataset": record["dataset"],
        "question_id": record["question_id"],
        "model_name": record["model_name"],
        "method": method,
        "prediction": stage["answer"],
        "prediction_normalized": stage["normalized_answer"],
        "correct": int(stage["correctness"]) if not abstained else 0,
        "forced_correct": int(stage["correctness"]),
        "direct_correct": int(stages[0]["correctness"]),
        "rounds": chosen,
        "latency_s": usage["latency_s"],
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "abstained": int(abstained),
        "answered": int(not abstained),
        "controller_score": float(ordered.iloc[chosen][score_column]),
    }


def _cumulative_usage(stages: list[dict[str, Any]], chosen_stage: int) -> dict[str, float]:
    input_tokens = 0
    output_tokens = 0
    latency = 0.0
    for index in range(chosen_stage + 1):
        stage = stages[index]
        input_tokens += int(stage.get("input_tokens", 0))
        output_tokens += int(stage.get("output_tokens", 0))
        latency += float(stage.get("latency_s", 0.0))
        if index < chosen_stage:
            input_tokens += int(stage.get("transition_input_tokens", 0))
            output_tokens += int(stage.get("transition_output_tokens", 0))
            latency += float(stage.get("transition_latency_s", 0.0))
    return {"input_tokens": input_tokens, "output_tokens": output_tokens, "latency_s": latency}


def summarize_method_frame(method_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (dataset, model_name, method), group in method_frame.groupby(["dataset", "model_name", "method"], dropna=False):
        answered_group = group[group["answered"] == 1]
        answered_accuracy = answered_group["correct"].mean() if len(answered_group) else 0.0
        rows.append(
            {
                "dataset": dataset,
                "model_name": model_name,
                "method": method,
                "n": len(group),
                "accuracy": group["correct"].mean(),
                "forced_accuracy": group.get("forced_correct", group["correct"]).mean(),
                "answered_accuracy": answered_accuracy,
                "coverage": group["answered"].mean(),
                "repair_rate": ((group["direct_correct"] == 0) & (group["correct"] == 1)).mean(),
                "corruption_rate": ((group["direct_correct"] == 1) & (group["correct"] == 0)).mean(),
                "net_gain": ((group["direct_correct"] == 0) & (group["correct"] == 1)).mean()
                - ((group["direct_correct"] == 1) & (group["correct"] == 0)).mean(),
                "avg_rounds": group["rounds"].mean(),
                "avg_input_tokens": group["input_tokens"].mean(),
                "avg_output_tokens": group["output_tokens"].mean(),
                "avg_latency_s": group["latency_s"].mean(),
            }
        )
    return pd.DataFrame(rows).sort_values(["dataset", "model_name", "method"]).reset_index(drop=True)


def pairwise_comparison(method_frame: pd.DataFrame, *, dataset: str, model_name: str, base: str, alt: str) -> dict[str, Any]:
    subset = method_frame[(method_frame["dataset"] == dataset) & (method_frame["model_name"] == model_name)]
    pivot = subset.pivot_table(index="question_id", columns="method", values="correct", aggfunc="first").reset_index()
    if base not in pivot or alt not in pivot:
        return {}
    base_correct = pivot[base].astype(int).tolist()
    alt_correct = pivot[alt].astype(int).tolist()
    mean_delta, ci_lo, ci_hi = paired_bootstrap_accuracy_delta(base_correct, alt_correct)
    return {
        "dataset": dataset,
        "model_name": model_name,
        "base": base,
        "alt": alt,
        "delta": mean_delta,
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "mcnemar_p": mcnemar_exact(base_correct, alt_correct),
    }


def save_calibrator(path: Path, calibrator: LogisticCalibrator, thresholds: dict[str, float]) -> None:
    write_json(path, {"weights": calibrator.weights, "bias": calibrator.bias, "feature_names": calibrator.feature_names, "thresholds": thresholds})


def load_calibrator(path: Path) -> tuple[LogisticCalibrator, dict[str, float]]:
    payload = read_json(path)
    calibrator = LogisticCalibrator(
        weights=list(payload["weights"]),
        bias=float(payload["bias"]),
        feature_names=list(payload["feature_names"]),
    )
    return calibrator, dict(payload.get("thresholds", {}))


def signal_risk_curves(stage_frame: pd.DataFrame, signal_columns: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    thresholds = [round(value, 2) for value in [i / 20 for i in range(1, 20)]]
    for signal in signal_columns:
        subset = stage_frame[stage_frame[signal].notna()].copy()
        probs = subset[signal].astype(float).tolist()
        labels = subset["correct"].astype(int).tolist()
        if not probs:
            continue
        normalized = _normalize_signal(probs)
        for row in risk_coverage_curve(normalized, labels, thresholds):
            rows.append({"signal": signal, **row})
    return pd.DataFrame(rows)
