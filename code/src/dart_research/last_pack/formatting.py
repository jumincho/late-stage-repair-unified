"""Format-domain evaluation, repair, and dataset loading helpers.

Owns the format-domain (output-constraint) side of the last-pack module.
Loads the upstream instruction-following datasets (IFEval, IFBench) via
HuggingFace, dynamically imports the dataset's own `evaluation_lib.py`
evaluator from a local checkout under `--ifeval-repo` / `--ifbench-repo`,
and provides:

- `load_instruction_dataset`, `load_instruction_eval_module`,
- `evaluate_instruction_response` (runs the upstream evaluator),
- `apply_instruction_patch` — deterministic format-only patch attempts,
- `summarize_instruction_feedback` — text feedback for the LLM patch path,
- `build_bridge_prompt`, `validate_bridge_response`, `classify_bridge_failure`
  — same surface for the in-house `planning_bridge` task,
- `parse_prompt_constraint_spec` — extract the constraint metadata used by
  the unified `lace.unify` feature columns.
"""

from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path
import re
from typing import Any

from datasets import load_dataset

from dart_research.last_pack.planning import PlanningTask, load_task_from_dict, validate_plan
from dart_research.parsing.json_tools import extract_first_json


def load_instruction_dataset(dataset_name: str, *, limit: int | None = None) -> list[dict[str, Any]]:
    if dataset_name == "ifeval":
        dataset = load_dataset("google/IFEval", split="train")
    elif dataset_name == "ifbench":
        dataset = load_dataset("allenai/IFBench_test", split="train")
    else:
        raise ValueError(f"Unsupported instruction dataset: {dataset_name}")
    if limit is not None:
        dataset = dataset.select(range(min(limit, len(dataset))))
    return [dict(item) for item in dataset]


@lru_cache(maxsize=8)
def load_instruction_eval_module(surface: str, repo_path: Path):
    if surface == "ifeval":
        module_path = repo_path / "instruction_following_eval" / "evaluation_lib.py"
        sys_path = repo_path
        module_name = "ifeval_evaluation_lib"
    elif surface == "ifbench":
        module_path = repo_path / "evaluation_lib.py"
        sys_path = repo_path
        module_name = "ifbench_evaluation_lib"
    else:
        raise ValueError(f"Unsupported evaluation surface: {surface}")
    if not module_path.exists():
        raise FileNotFoundError(f"Evaluation module not found for {surface}: {module_path}")
    import sys

    sys.path.insert(0, str(sys_path))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load IFBench evaluation module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate_instruction_response(
    example: dict[str, Any],
    response: str,
    *,
    surface: str,
    repo_path: Path,
) -> dict[str, Any]:
    evaluation_lib = load_instruction_eval_module(surface, repo_path)
    clean_kwargs = [{key: value for key, value in item.items() if value is not None} for item in example["kwargs"]]
    input_example = evaluation_lib.InputExample(
        key=example["key"],
        instruction_id_list=list(example["instruction_id_list"]),
        prompt=str(example["prompt"]),
        kwargs=clean_kwargs,
    )
    prompt_to_response = {str(example["prompt"]): response}
    strict = evaluation_lib.test_instruction_following_strict(input_example, prompt_to_response)
    failed_ids = [
        instruction_id
        for instruction_id, ok in zip(example["instruction_id_list"], strict.follow_instruction_list, strict=True)
        if not ok
    ]
    return {
        "strict_follow_all": int(strict.follow_all_instructions),
        "loose_follow_all": None,
        "strict_follow_list": list(strict.follow_instruction_list),
        "loose_follow_list": [],
        "failed_instruction_ids": failed_ids,
        "failed_instruction_count": len(failed_ids),
    }


def summarize_instruction_feedback(example: dict[str, Any], evaluation: dict[str, Any]) -> str:
    failed_ids = evaluation.get("failed_instruction_ids", [])
    prompt = str(example.get("prompt", ""))
    prompt_constraints = extract_prompt_constraints(prompt)
    if not failed_ids:
        return "All instructions satisfied under the strict validator."
    lines = [
        f"Failed strict instruction ids: {', '.join(str(item) for item in failed_ids)}",
        f"Failed instruction count: {evaluation.get('failed_instruction_count', 0)}",
    ]
    if prompt_constraints:
        lines.append("Explicit prompt constraints to satisfy exactly:")
        lines.extend(f"- {item}" for item in prompt_constraints)
    return "\n".join(lines)


def parse_prompt_constraint_spec(prompt: str) -> dict[str, Any]:
    text = " ".join(prompt.strip().split())
    lower = text.lower()
    keyword_map = {
        "once": 1,
        "twice": 2,
        "three times": 3,
        "four times": 4,
        "five times": 5,
        "six times": 6,
        "seven times": 7,
        "eight times": 8,
        "nine times": 9,
        "ten times": 10,
    }
    keyword_counts: list[tuple[str, int]] = []
    for match in re.finditer(
        r"keyword\s+([A-Za-z0-9_\-]+)\s+(once|twice|three times|four times|five times|six times|seven times|eight times|nine times|ten times)",
        lower,
    ):
        keyword_counts.append((match.group(1), keyword_map[match.group(2)]))
    word_match = re.search(r"(\d+)\+\s*word", lower) or re.search(r"at least\s+(\d+)\s+word", lower)
    section_match = re.search(r"highlight at least\s+(\d+)\s+sections?", lower)
    bullet_match = re.search(r"(\d+)\s+bullet", lower)
    return {
        "no_commas": "do not use any commas" in lower,
        "keyword_counts": keyword_counts,
        "min_words": int(word_match.group(1)) if word_match else None,
        "min_highlight_sections": int(section_match.group(1)) if section_match else None,
        "num_bullets": int(bullet_match.group(1)) if bullet_match else None,
    }


def extract_prompt_constraints(prompt: str) -> list[str]:
    constraints: list[str] = []
    spec = parse_prompt_constraint_spec(prompt)
    if spec["no_commas"]:
        constraints.append("Do not use any commas.")
    for keyword, count in spec["keyword_counts"]:
        constraints.append(f"Include keyword '{keyword}' exactly {count} time(s).")
    if spec["min_words"] is not None:
        constraints.append(f"Use at least {spec['min_words']} words.")
    if spec["min_highlight_sections"] is not None:
        constraints.append(f"Highlight at least {spec['min_highlight_sections']} sections.")
    if spec["num_bullets"] is not None:
        constraints.append(f"Use {spec['num_bullets']} bullet(s) if requested.")
    return constraints


def _count_word_occurrences(text: str, keyword: str) -> int:
    return text.lower().count(keyword.lower())


def _remove_extra_keyword_occurrences(text: str, keyword: str, *, target_count: int) -> str:
    matches = list(re.finditer(rf"(?i){re.escape(keyword)}", text))
    if len(matches) <= target_count:
        return text
    drop = len(matches) - target_count
    chars = list(text)
    for match in reversed(matches[-drop:]):
        for idx in range(match.start(), match.end()):
            chars[idx] = ""
    return re.sub(r"\s{2,}", " ", "".join(chars)).strip()


def _append_missing_keywords(text: str, keyword: str, *, missing_count: int) -> str:
    addition = " ".join([keyword] * missing_count).strip()
    if not addition:
        return text
    suffix = "" if not text.strip() else " "
    return f"{text.rstrip()}{suffix}{addition}".strip()


def apply_instruction_patch(example: dict[str, Any], response: str, evaluation: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    patched = str(response)
    spec = parse_prompt_constraint_spec(str(example.get("prompt", "")))
    operations: list[str] = []
    if spec["no_commas"] and "," in patched:
        patched = patched.replace(",", "")
        operations.append("removed_commas")
    for keyword, target_count in spec["keyword_counts"]:
        observed = _count_word_occurrences(patched, keyword)
        if observed > target_count:
            patched = _remove_extra_keyword_occurrences(patched, keyword, target_count=target_count)
            operations.append(f"trimmed_{keyword}")
        elif observed < target_count:
            patched = _append_missing_keywords(patched, keyword, missing_count=target_count - observed)
            operations.append(f"added_{keyword}")
    if spec["min_highlight_sections"] is not None:
        observed = len(re.findall(r"\*[^*]+\*", patched))
        missing = max(0, spec["min_highlight_sections"] - observed)
        if missing:
            additions = " ".join(f"*highlighted section part {idx + 1}*" for idx in range(observed, observed + missing))
            patched = f"{patched.rstrip()} {additions}".strip()
            operations.append("added_highlight_sections")
    if spec["min_words"] is not None:
        words = re.findall(r"\b\w+\b", patched)
        if len(words) < spec["min_words"]:
            filler_sentence = " Additional detail stays consistent with the original request."
            while len(re.findall(r"\b\w+\b", patched)) < spec["min_words"]:
                patched += filler_sentence
            operations.append("extended_word_count")
    return patched.strip(), {"used_deterministic_patch": int(bool(operations)), "patch_operations": operations}


def _coerce_task(task: PlanningTask | dict[str, Any]) -> PlanningTask:
    if isinstance(task, dict):
        return load_task_from_dict(task)
    return task


def build_bridge_prompt(task: PlanningTask | dict[str, Any]) -> str:
    task = _coerce_task(task)
    return (
        f"{task.prompt}\n"
        "Return only valid JSON with exactly two keys: "
        '{"plan": "comma-separated moves using U,D,L,R", "summary": "under 12 words"}'
    )


def validate_bridge_response(task: PlanningTask | dict[str, Any], response: str) -> dict[str, Any]:
    task = _coerce_task(task)
    try:
        payload = extract_first_json(response)
        if not isinstance(payload, dict):
            raise ValueError("Bridge response is not a JSON object")
        keys = set(payload.keys())
        format_valid = int(keys == {"plan", "summary"} and isinstance(payload.get("summary"), str))
        plan_text = str(payload.get("plan", ""))
        plan_eval = validate_plan(task, plan_text)
    except Exception as error:
        current_state = list(task.start) if isinstance(task.start, tuple) else [int(task.start), 0]
        return {
            "format_valid": 0,
            "semantic_valid": 0,
            "both_valid": 0,
            "format_error": str(error),
            "semantic_error": "unparseable_format",
            "plan_eval": {
                "success": 0,
                "failure_type": "unparseable_format",
                "first_invalid_step": 1,
                "failure_position_ratio": 0.0,
                "valid_prefix_length": 0,
                "valid_prefix_text": "",
                "current_state": current_state,
            },
        }
    semantic_valid = int(plan_eval["success"])
    return {
        "format_valid": int(format_valid),
        "semantic_valid": semantic_valid,
        "both_valid": int(format_valid and semantic_valid),
        "format_error": "" if format_valid else "schema_or_json_mismatch",
        "semantic_error": "" if semantic_valid else str(plan_eval["failure_type"]),
        "plan_eval": plan_eval,
    }


def classify_bridge_failure(evaluation: dict[str, Any]) -> str:
    format_valid = int(evaluation.get("format_valid", 0))
    semantic_valid = int(evaluation.get("semantic_valid", 0))
    if format_valid and semantic_valid:
        return "success"
    if semantic_valid and not format_valid:
        return "format_only_failure"
    if format_valid and not semantic_valid:
        return "semantic_only_failure"
    return "joint_failure"
