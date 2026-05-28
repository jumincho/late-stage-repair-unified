"""V-chase feature builders for arithmetic / math draft examples.

V-chase ("value-chase") is the bridge layer that flattens the confidence /
chase traces into the feature columns the downstream policy fitter
consumes. Provides per-stage feature builders and the legacy
`CURRENT_FEATURES_OLD` column list, plus the helper that pulls PRM scores
out of `ProcessRewardModelScorer` and merges them in. The feature columns
emitted here feed `lace.unify` and the final unified policy.
"""

from __future__ import annotations

import ast
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd

from dart_research.confidence.analysis import flatten_stage_rows
from dart_research.parsing.normalization import extract_numeric, normalize_prediction
from dart_research.vchase.prm import ProcessRewardModelScorer


CURRENT_FEATURES_OLD = [
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
    "stage_index",
]

PRM_FEATURE_COLUMNS = [
    "prm_score_current",
    "prm_score_mean",
    "prm_score_min",
    "delta_prm_score_current",
    "prm_score_min_so_far",
]

ARITH_FEATURE_COLUMNS = [
    "arith_support_score",
    "equation_consistent",
    "last_calc_matches_answer",
    "answer_mentioned_in_scratch",
]

CURRENT_FEATURES_VERIFIER = CURRENT_FEATURES_OLD + [
    *PRM_FEATURE_COLUMNS,
    *ARITH_FEATURE_COLUMNS,
]

UTILITY_FEATURES_OLD = CURRENT_FEATURES_OLD + [
    "critique_severity",
]

CURRENT_FEATURES_ARITH = CURRENT_FEATURES_OLD + [
    *ARITH_FEATURE_COLUMNS,
]

CURRENT_FEATURES_PRM = CURRENT_FEATURES_OLD + [
    *PRM_FEATURE_COLUMNS,
]

UTILITY_FEATURES_ARITH = CURRENT_FEATURES_ARITH + [
    "critique_severity",
    "arith_inconsistency_flag",
    "has_equation",
    "has_next_stage",
]

UTILITY_FEATURES_PRM = CURRENT_FEATURES_PRM + [
    "critique_severity",
    "prm_score_repair_gain",
    "has_next_stage",
]

UTILITY_FEATURES_VERIFIER = CURRENT_FEATURES_VERIFIER + [
    "prm_score_repair_gain",
    "arith_inconsistency_flag",
    "has_equation",
    "has_next_stage",
]


def load_trace_frame(trace_dirs: list[str | Path]) -> pd.DataFrame:
    frames = [pd.read_json(Path(path) / "per_example.jsonl", lines=True) for path in trace_dirs]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def flatten_trace_rows(trace_frame: pd.DataFrame) -> pd.DataFrame:
    base = flatten_stage_rows(trace_frame)
    extras: list[dict[str, Any]] = []
    for record in trace_frame.to_dict(orient="records"):
        stages = record["stages"]
        for stage_index, stage in enumerate(stages):
            future = stages[stage_index + 1 :]
            next_correct = future[0]["correctness"] if future else None
            best_future_correct = max([item["correctness"] for item in future], default=stage["correctness"])
            best_stage = _earliest_best_stage(stages)
            extras.append(
                {
                    "dataset": record["dataset"],
                    "question_id": record["question_id"],
                    "model_name": record["model_name"],
                    "stage_index": stage_index,
                    "question": record["question"],
                    "task_type": record["task_type"],
                    "gold_answer": record["gold_answer"],
                    "gold_normalized": record["gold_normalized"],
                    "answer_text": stage["answer"],
                    "normalized_answer_text": stage["normalized_answer"],
                    "scratch_text": stage.get("scratch", ""),
                    "attack_text": stage.get("attack", ""),
                    "risk_tag": stage.get("risk_tag", ""),
                    "decision": stage.get("decision", ""),
                    "critique_severity": stage.get("signals", {}).get("critique_severity"),
                    "has_next_stage": int(next_correct is not None),
                    "next_correct": float(next_correct) if next_correct is not None else math.nan,
                    "best_future_correct": float(best_future_correct),
                    "helpful_next": _float_label(next_correct is not None and next_correct > stage["correctness"]),
                    "harmful_next": _float_label(next_correct is not None and next_correct < stage["correctness"]),
                    "any_future_helpful": _float_label(any(item["correctness"] > stage["correctness"] for item in future)),
                    "oracle_best_stage": best_stage,
                }
            )
    extra_frame = pd.DataFrame(extras)
    merged = base.merge(extra_frame, on=["dataset", "question_id", "model_name", "stage_index"], how="left")
    return merged.sort_values(["dataset", "question_id", "model_name", "stage_index"]).reset_index(drop=True)


def add_verifier_features(stage_frame: pd.DataFrame, *, prm_scorer: ProcessRewardModelScorer | None = None) -> pd.DataFrame:
    frame = stage_frame.copy()
    arithmetic_rows = [
        _arithmetic_feature_row(
            answer=str(row.answer_text),
            scratch=str(row.scratch_text),
            task_type=str(row.task_type),
        )
        for row in frame.itertuples(index=False)
    ]
    arithmetic_frame = pd.DataFrame(arithmetic_rows)
    frame = pd.concat([frame.reset_index(drop=True), arithmetic_frame], axis=1)
    if prm_scorer is not None:
        prm_rows = [
            prm_scorer.score_reasoning(
                question=str(row.question),
                scratch=str(row.scratch_text),
                answer=str(row.answer_text),
            )
            for row in frame.itertuples(index=False)
        ]
        prm_frame = pd.DataFrame(prm_rows)
        frame = pd.concat([frame.reset_index(drop=True), prm_frame], axis=1)
    else:
        frame["prm_score_current"] = 0.5
        frame["prm_score_mean"] = 0.5
        frame["prm_score_min"] = 0.5
        frame["prm_step_count"] = 0
    frame["prm_score_current"] = frame["prm_score_current"].fillna(0.5)
    frame["prm_score_mean"] = frame["prm_score_mean"].fillna(0.5)
    frame["prm_score_min"] = frame["prm_score_min"].fillna(0.5)
    frame["delta_prm_score_current"] = _group_delta(frame, "prm_score_current")
    frame["prm_score_min_so_far"] = (
        frame.sort_values("stage_index")
        .groupby(["dataset", "question_id", "model_name"], dropna=False)["prm_score_current"]
        .cummin()
        .reset_index(drop=True)
    )
    frame["prm_score_repair_gain"] = frame["delta_prm_score_current"].clip(lower=0.0)
    frame["arith_support_score"] = frame["arith_support_score"].fillna(0.5)
    frame["equation_consistent"] = frame["equation_consistent"].fillna(0.5)
    frame["last_calc_matches_answer"] = frame["last_calc_matches_answer"].fillna(0.0)
    frame["answer_mentioned_in_scratch"] = frame["answer_mentioned_in_scratch"].fillna(0.0)
    frame["arith_inconsistency_flag"] = ((frame["has_equation"] == 1.0) & (frame["equation_consistent"] == 0.0)).astype(float)
    return frame


def _group_delta(frame: pd.DataFrame, column: str) -> pd.Series:
    ordered = frame.sort_values(["dataset", "question_id", "model_name", "stage_index"]).copy()
    deltas = (
        ordered.groupby(["dataset", "question_id", "model_name"], dropna=False)[column]
        .diff()
        .fillna(0.0)
        .astype(float)
    )
    ordered[f"{column}_delta_tmp"] = deltas
    return ordered.sort_index()[f"{column}_delta_tmp"]


def _earliest_best_stage(stages: list[dict[str, Any]]) -> int:
    best = max(int(stage["correctness"]) for stage in stages)
    for index, stage in enumerate(stages):
        if int(stage["correctness"]) == best:
            return index
    return len(stages) - 1


def _float_label(value: bool) -> float:
    return float(int(value))


def _arithmetic_feature_row(*, answer: str, scratch: str, task_type: str) -> dict[str, float]:
    normalized_answer = normalize_prediction(answer, task_type)
    has_equation, equation_consistent, last_rhs = _last_equation_status(scratch)
    answer_mentioned = 0.0
    last_calc_matches = 0.0
    if task_type == "numeric_open":
        numbers = re.findall(r"-?\d[\d,]*(?:\.\d+)?", scratch)
        normalized_numbers = {extract_numeric(item) for item in numbers}
        answer_mentioned = float(normalized_answer in normalized_numbers) if normalized_answer else 0.0
        if last_rhs:
            last_calc_matches = float(extract_numeric(last_rhs) == normalized_answer)
        else:
            last_calc_matches = float(extract_numeric(scratch) == normalized_answer) if scratch.strip() else 0.0
    support_values: list[float] = []
    if has_equation:
        support_values.append(float(equation_consistent if equation_consistent is not None else 0.5))
    if scratch.strip():
        support_values.append(answer_mentioned)
        support_values.append(last_calc_matches)
    arith_support = 0.5 if not support_values else sum(support_values) / len(support_values)
    return {
        "has_equation": float(has_equation),
        "equation_consistent": float(0.5 if equation_consistent is None else equation_consistent),
        "answer_mentioned_in_scratch": float(answer_mentioned),
        "last_calc_matches_answer": float(last_calc_matches),
        "arith_support_score": float(arith_support),
    }


def _last_equation_status(text: str) -> tuple[bool, bool | None, str]:
    candidates = []
    for line in re.split(r"[\n\r]+", text):
        if "=" in line:
            candidates.append(line.strip())
    if not candidates:
        inline = re.findall(r"[^.\n]*=[^.\n]*", text)
        candidates.extend(item.strip() for item in inline if "=" in item)
    if not candidates:
        return False, None, ""
    candidate = candidates[-1]
    parts = [part.strip() for part in re.split(r"\s*=\s*", candidate) if part.strip()]
    if len(parts) < 2:
        return True, None, parts[-1] if parts else ""
    values = [_safe_eval_expression(part) for part in parts]
    comparable = [value for value in values if value is not None]
    if len(comparable) < 2:
        return True, None, parts[-1]
    consistent = True
    previous = values[0]
    for current in values[1:]:
        if previous is None or current is None:
            previous = current
            continue
        if not math.isclose(previous, current, rel_tol=1e-6, abs_tol=1e-6):
            consistent = False
            break
        previous = current
    return True, consistent, parts[-1]


def _safe_eval_expression(expr: str) -> float | None:
    cleaned = expr.replace(",", "")
    cleaned = cleaned.replace("×", "*").replace("x", "*").replace("X", "*").replace("÷", "/")
    cleaned = cleaned.replace("$", "")
    cleaned = re.sub(r"(\d+(?:\.\d+)?)%", r"(\1/100)", cleaned)
    if not re.fullmatch(r"[\d\.\+\-\*\/\(\)\s]+", cleaned):
        return None
    try:
        node = ast.parse(cleaned, mode="eval")
        return float(_eval_ast(node.body))
    except Exception:
        return None


def _eval_ast(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _eval_ast(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        return left / right
    raise ValueError("Unsupported expression")
