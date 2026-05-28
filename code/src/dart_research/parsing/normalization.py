"""Text and answer normalization for paired correctness scoring.

The single place that decides "are these two answers the same answer".
Provides:

- `normalize_text` — whitespace + case folding,
- `normalize_yes_no` — fold yes/true/1 and no/false/0 onto canonical forms,
- `extract_numeric` — pick the answer-shaped number out of free text,
- `normalize_prediction` / `normalize_from_answer_fields` / `normalize_gold_answer`
  — the entry points used by `evaluation.metrics.is_correct`.

All of `is_correct`, the math runners, and the format evaluator rely on
these normalizers, so changes here propagate to every reported number.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


def normalize_text(value: str) -> str:
    """Lowercase and collapse whitespace."""
    collapsed = re.sub(r"\s+", " ", value.strip().lower())
    return collapsed


def normalize_yes_no(value: str) -> str:
    """Normalize yes/no variants."""
    value = normalize_text(value)
    if value in {"yes", "true", "1"}:
        return "yes"
    if value in {"no", "false", "0"}:
        return "no"
    if value.startswith("yes"):
        return "yes"
    if value.startswith("no"):
        return "no"
    return value


def extract_numeric(value: str) -> str:
    """Extract a stable numeric answer string."""
    matches = re.findall(r"-?\d[\d,]*(?:\.\d+)?", value)
    if not matches:
        return normalize_text(value)
    candidate = matches[-1].replace(",", "")
    try:
        number = Decimal(candidate)
    except InvalidOperation:
        return candidate
    normalized = format(number.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized or "0"


def normalize_choice(value: str) -> str:
    """Normalize multiple-choice option labels."""
    value = normalize_text(value)
    match = re.search(r"\b([a-e])\b", value)
    if match:
        return match.group(1).upper()
    if value and value[0] in "abcde":
        return value[0].upper()
    return value.upper()


def normalize_gold_answer(raw_answer: str, task_type: str) -> str:
    """Normalize a gold answer according to task type."""
    if task_type == "numeric_open":
        return extract_numeric(raw_answer)
    if task_type == "yes_no_open":
        return normalize_yes_no(raw_answer)
    if task_type == "multiple_choice":
        return normalize_choice(raw_answer)
    return normalize_text(raw_answer)


def normalize_prediction(raw_answer: str, task_type: str) -> str:
    """Normalize a prediction according to task type."""
    return normalize_gold_answer(raw_answer, task_type)


def normalize_from_answer_fields(answer: str, normalized_answer: str, task_type: str) -> str:
    """Prefer the actual answer field when deriving the evaluation normalization."""
    primary = answer if str(answer).strip() else normalized_answer
    return normalize_prediction(primary, task_type)
