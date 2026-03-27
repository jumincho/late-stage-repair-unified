from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


def sigmoid(value: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(value, -30.0, 30.0)))


@dataclass(slots=True)
class LogisticCalibrator:
    weights: list[float]
    bias: float
    feature_names: list[str]

    def predict_proba(self, rows: list[dict[str, float]]) -> list[float]:
        matrix = np.asarray([[row.get(name, 0.0) for name in self.feature_names] for row in rows], dtype=float)
        logits = matrix @ np.asarray(self.weights, dtype=float) + float(self.bias)
        return sigmoid(logits).tolist()


def fit_logistic_calibrator(
    rows: list[dict[str, float]],
    labels: list[int],
    feature_names: list[str],
    *,
    epochs: int = 1200,
    lr: float = 0.05,
    l2: float = 1e-3,
) -> LogisticCalibrator:
    matrix = np.asarray([[row.get(name, 0.0) for name in feature_names] for row in rows], dtype=float)
    target = np.asarray(labels, dtype=float)
    weights = np.zeros(matrix.shape[1], dtype=float)
    bias = 0.0
    if len(matrix) == 0:
        return LogisticCalibrator(weights=[], bias=0.0, feature_names=list(feature_names))
    for _ in range(epochs):
        logits = matrix @ weights + bias
        probs = sigmoid(logits)
        error = probs - target
        grad_w = (matrix.T @ error) / len(matrix) + l2 * weights
        grad_b = float(error.mean())
        weights -= lr * grad_w
        bias -= lr * grad_b
    return LogisticCalibrator(weights=weights.tolist(), bias=float(bias), feature_names=list(feature_names))


def brier_score(probs: list[float], labels: list[int]) -> float:
    values = [(prob - label) ** 2 for prob, label in zip(probs, labels, strict=True)]
    return sum(values) / len(values) if values else 0.0


def auroc(probs: list[float], labels: list[int]) -> float:
    pairs = sorted(zip(probs, labels, strict=True), key=lambda item: item[0], reverse=True)
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return 0.5
    tp = 0
    fp = 0
    prev_tp_rate = 0.0
    prev_fp_rate = 0.0
    area = 0.0
    for _, label in pairs:
        if label:
            tp += 1
        else:
            fp += 1
        tp_rate = tp / positives
        fp_rate = fp / negatives
        area += (fp_rate - prev_fp_rate) * (tp_rate + prev_tp_rate) / 2
        prev_tp_rate = tp_rate
        prev_fp_rate = fp_rate
    return area


def average_precision(probs: list[float], labels: list[int]) -> float:
    pairs = sorted(zip(probs, labels, strict=True), key=lambda item: item[0], reverse=True)
    positives = sum(labels)
    if positives == 0:
        return 0.0
    tp = 0
    fp = 0
    ap = 0.0
    for _, label in pairs:
        if label:
            tp += 1
            ap += tp / (tp + fp)
        else:
            fp += 1
    return ap / positives


def expected_calibration_error(probs: list[float], labels: list[int], bins: int = 10) -> float:
    if not probs:
        return 0.0
    total = len(probs)
    error = 0.0
    for index in range(bins):
        lo = index / bins
        hi = (index + 1) / bins
        bucket = [(prob, label) for prob, label in zip(probs, labels, strict=True) if lo <= prob < hi or (index == bins - 1 and prob == 1.0)]
        if not bucket:
            continue
        mean_prob = sum(prob for prob, _ in bucket) / len(bucket)
        mean_acc = sum(label for _, label in bucket) / len(bucket)
        error += (len(bucket) / total) * abs(mean_prob - mean_acc)
    return error


def aurc(probs: list[float], labels: list[int]) -> float:
    pairs = sorted(zip(probs, labels, strict=True), key=lambda item: item[0], reverse=True)
    if not pairs:
        return 0.0
    risks: list[float] = []
    for end in range(1, len(pairs) + 1):
        covered = pairs[:end]
        coverage = end / len(pairs)
        accuracy = sum(label for _, label in covered) / len(covered)
        risk = 1.0 - accuracy
        risks.append(risk)
    return sum(risks) / len(risks)


def risk_coverage_curve(probs: list[float], labels: list[int], thresholds: list[float]) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for threshold in thresholds:
        kept = [label for prob, label in zip(probs, labels, strict=True) if prob >= threshold]
        coverage = len(kept) / len(labels) if labels else 0.0
        risk = 1.0 - (sum(kept) / len(kept)) if kept else 0.0
        rows.append({"threshold": threshold, "coverage": coverage, "risk": risk})
    return rows


def choose_threshold_for_accuracy_rounds(
    stage_probs: list[list[float]],
    stage_correct: list[list[int]],
    *,
    abstain_allowed: bool,
    thresholds: list[float] | None = None,
    penalty_per_round: float = 0.03,
) -> float:
    if thresholds is None:
        thresholds = [round(value, 2) for value in np.linspace(0.3, 0.9, 25)]
    best_threshold = thresholds[0]
    best_utility = -math.inf
    for threshold in thresholds:
        correct_total = 0.0
        answered_total = 0.0
        round_total = 0.0
        for probs, correctness in zip(stage_probs, stage_correct, strict=True):
            stop_stage = len(probs) - 1
            for stage_index, prob in enumerate(probs):
                if prob >= threshold:
                    stop_stage = stage_index
                    break
            round_total += stop_stage
            final_correct = correctness[stop_stage]
            if abstain_allowed and probs[stop_stage] < threshold:
                continue
            answered_total += 1.0
            correct_total += float(final_correct)
        if answered_total == 0:
            utility = -1.0
        else:
            accuracy = correct_total / answered_total
            avg_rounds = round_total / len(stage_probs)
            utility = accuracy - penalty_per_round * avg_rounds
        if utility > best_utility:
            best_utility = utility
            best_threshold = threshold
    return float(best_threshold)
