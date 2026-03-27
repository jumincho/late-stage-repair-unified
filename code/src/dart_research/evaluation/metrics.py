from __future__ import annotations

import math
import random
from collections import Counter
from typing import Iterable

import pandas as pd


def dataset_display_name(dataset: str, metadata: object) -> str:
    """Return an honest reporting label for a dataset."""
    if dataset == "strategyqa":
        if isinstance(metadata, dict) and "boolq" in str(metadata.get("hf_source", "")).lower():
            return "boolq"
        return "yes/no benchmark"
    return dataset


def is_correct(predicted: str, gold: str) -> bool:
    """Binary exact-match correctness on normalized answers."""
    return predicted == gold


def majority_vote(values: Iterable[str]) -> str:
    """Return the most common normalized answer."""
    counts = Counter(value for value in values if value)
    if not counts:
        return ""
    return counts.most_common(1)[0][0]


def paired_bootstrap_accuracy_delta(
    base_correct: list[int],
    alt_correct: list[int],
    samples: int = 2000,
    seed: int = 13,
) -> tuple[float, float, float]:
    """Bootstrap CI for accuracy delta."""
    rng = random.Random(seed)
    n = len(base_correct)
    deltas: list[float] = []
    for _ in range(samples):
        indices = [rng.randrange(n) for _ in range(n)]
        base_acc = sum(base_correct[i] for i in indices) / n
        alt_acc = sum(alt_correct[i] for i in indices) / n
        deltas.append(alt_acc - base_acc)
    deltas.sort()
    mean_delta = sum(deltas) / len(deltas)
    lo = deltas[int(0.025 * len(deltas))]
    hi = deltas[int(0.975 * len(deltas))]
    return mean_delta, lo, hi


def mcnemar_exact(base_correct: list[int], alt_correct: list[int]) -> float:
    """Two-sided exact McNemar p-value using a binomial tail."""
    b01 = sum(1 for b, a in zip(base_correct, alt_correct, strict=True) if b == 0 and a == 1)
    b10 = sum(1 for b, a in zip(base_correct, alt_correct, strict=True) if b == 1 and a == 0)
    n = b01 + b10
    if n == 0:
        return 1.0
    k = min(b01, b10)
    cumulative = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2 * cumulative)


def summarize_results(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate method x dataset metrics from per-example results."""
    frame = frame.copy()
    frame["dataset_label"] = frame.apply(lambda row: dataset_display_name(row["dataset"], row.get("metadata")), axis=1)
    frame["raw_candidate_count"] = frame["candidate_set"].apply(lambda value: len(value) if isinstance(value, list) else 0)
    frame["distinct_error_type_count"] = frame["candidate_set"].apply(
        lambda value: len(
            {
                str(item.get("failure_mode", "")).strip().lower()
                for item in value
                if isinstance(item, dict) and str(item.get("failure_mode", "")).strip() and str(item.get("failure_mode", "")).strip().lower() != "original_draft"
            }
        )
        if isinstance(value, list)
        else 0
    )
    frame["duplicate_fraction"] = frame.apply(
        lambda row: (row["duplicates"] / row["raw_candidate_count"]) if row["raw_candidate_count"] else None,
        axis=1,
    )
    frame["trivial_fraction"] = frame.apply(
        lambda row: (row["trivial"] / row["raw_candidate_count"]) if row["raw_candidate_count"] else None,
        axis=1,
    )
    frame["malformed_fraction"] = frame.apply(
        lambda row: (row["malformed"] / row["raw_candidate_count"]) if row["raw_candidate_count"] else None,
        axis=1,
    )
    grouping_columns = ["dataset", "dataset_label"]
    optional_columns = ["client", "primary_model"]
    for column in optional_columns:
        if column in frame.columns and frame[column].notna().any():
            grouping_columns.append(column)
    grouping_columns.append("method")

    metrics = []
    grouped = frame.groupby(grouping_columns, dropna=False)
    for group_values, group in grouped:
        if not isinstance(group_values, tuple):
            group_values = (group_values,)
        group_key = dict(zip(grouping_columns, group_values, strict=True))
        dataset_key = str(group_key["dataset"])
        dataset = str(group_key["dataset_label"])
        method = str(group_key["method"])
        total = len(group)
        accuracy = group["correct"].mean() if total else 0.0
        repair = ((group["direct_correct"] == 0) & (group["correct"] == 1)).mean()
        corruption = ((group["direct_correct"] == 1) & (group["correct"] == 0)).mean()
        net_gain = repair - corruption
        row = {
            "dataset": dataset,
            "dataset_key": dataset_key,
            "method": method,
            "n": total,
            "accuracy": accuracy,
            "repair_rate": repair,
            "corruption_rate": corruption,
            "net_gain": net_gain,
            "avg_latency_s": group["latency_s"].mean(),
            "avg_input_tokens": group["input_tokens"].mean(),
            "avg_output_tokens": group["output_tokens"].mean(),
            "avg_cost_usd": group["cost_usd"].mean(),
            "candidate_coverage": group["candidate_coverage"].dropna().mean() if "candidate_coverage" in group else None,
            "avg_raw_candidates": group["raw_candidate_count"].mean(),
            "avg_kept_candidates": group["kept_options"].mean(),
            "avg_duplicate_count": group["duplicates"].mean(),
            "distinct_error_type_count": group["distinct_error_type_count"].mean(),
            "duplicate_fraction": group["duplicate_fraction"].dropna().mean(),
            "trivial_fraction": group["trivial_fraction"].dropna().mean(),
            "malformed_fraction": group["malformed_fraction"].dropna().mean(),
        }
        for column in optional_columns:
            if column in group_key:
                row[column] = group_key[column]
        metrics.append(row)
    return pd.DataFrame(metrics).sort_values(["dataset", "method"]).reset_index(drop=True)
