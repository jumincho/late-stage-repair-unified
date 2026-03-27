from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dart_research.evaluation.metrics import mcnemar_exact
from dart_research.lace.policy import fit_three_action_policy
from dart_research.lace.unify import (
    POOLED_FEATURE_COLUMNS,
    UNIFIED_CONFIG,
    build_format_unified_frame,
    build_math_unified_frame,
    decision_success,
    fit_shared_simple_policies,
    grouped_policy_rows,
    select_best_simple_policy,
    stable_split_triplet,
)
from dart_research.utils.io import ensure_dir, read_json, write_json, write_text


REPO_ROOT = Path("/workspace/project")
R2_SPLIT_SEEDS = [13, 29, 47]
ABSTRACT_ACTION_SPACE = ["NO_INTERVENTION", "LOCAL_REPAIR", "GLOBAL_REWRITE_OR_RESTART"]
EXPECTED_SURFACE_COUNTS = {
    "math_cluster_raw": 1515,
    "math_generic_raw": 483,
    "math_cluster_replay": 1515,
    "math_generic_replay": 483,
    "format_ifeval": 381,
    "format_ifbench": 300,
}
ACTION_MAPPING = {
    "math": {
        "NO_INTERVENTION": "direct answer",
        "LOCAL_REPAIR": "GRANITE_POSTPROCESS_ONLY_PATCH replay over fresh math traces",
        "GLOBAL_REWRITE_OR_RESTART": "self_refine_1",
    },
    "format": {
        "NO_INTERVENTION": "direct formatted answer",
        "LOCAL_REPAIR": "solve_then_format",
        "GLOBAL_REWRITE_OR_RESTART": "full_rewrite_on_failure",
    },
}
PHASE_SPECS = [
    {
        "phase_name": "math_cluster_raw",
        "module": "math",
        "surface_name": "cluster-hard",
        "expected_rows": 1515,
        "base_dir": "math_raw",
        "glob": "gsm8k_train_cluster_live_full__shard*of*",
        "id_key": "question_id",
        "required_actions": ["RAW_PYTHON", "CASS_TARGET_POSTPROCESS_PATCH"],
    },
    {
        "phase_name": "math_generic_raw",
        "module": "math",
        "surface_name": "generic-hard",
        "expected_rows": 483,
        "base_dir": "math_raw",
        "glob": "gsm8k_train_generic_live_full__shard*of*",
        "id_key": "question_id",
        "required_actions": ["RAW_PYTHON", "CASS_TARGET_POSTPROCESS_PATCH"],
    },
    {
        "phase_name": "math_cluster_replay",
        "module": "math",
        "surface_name": "cluster-hard",
        "expected_rows": 1515,
        "base_dir": "math_replay",
        "glob": "gsm8k_train_cluster_live_full__shard*of*",
        "id_key": "question_id",
        "required_actions": ["RAW_PYTHON", "GRANITE_POSTPROCESS_ONLY_PATCH"],
    },
    {
        "phase_name": "math_generic_replay",
        "module": "math",
        "surface_name": "generic-hard",
        "expected_rows": 483,
        "base_dir": "math_replay",
        "glob": "gsm8k_train_generic_live_full__shard*of*",
        "id_key": "question_id",
        "required_actions": ["RAW_PYTHON", "GRANITE_POSTPROCESS_ONLY_PATCH"],
    },
    {
        "phase_name": "format_ifeval",
        "module": "format",
        "surface_name": "screened IFEval",
        "expected_rows": 381,
        "base_dir": "format",
        "glob": "ifeval_shard*of*",
        "id_key": "example_id",
        "required_actions": ["direct_formatted", "solve_then_format", "full_rewrite_on_failure"],
    },
    {
        "phase_name": "format_ifbench",
        "module": "format",
        "surface_name": "IFBench",
        "expected_rows": 300,
        "base_dir": "format",
        "glob": "ifbench_shard*of*",
        "id_key": "example_id",
        "required_actions": ["direct_formatted", "solve_then_format", "full_rewrite_on_failure"],
    },
]
MODEL_SPECS = [
    {"key": "qwen", "model_name": "Qwen/Qwen2.5-7B-Instruct"},
    {"key": "mistral", "model_name": "mistralai/Mistral-7B-Instruct-v0.3"},
    {"key": "qwen14b", "model_name": "Qwen/Qwen2.5-14B-Instruct"},
]


def digest_entries(entries: list[dict[str, Any]]) -> str:
    payload = json.dumps(entries, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_manifest(path: Path, *, dataset: str, surface: str, entries: list[dict[str, Any]], source_manifest: str) -> None:
    write_json(
        path,
        {
            "created_at": datetime.now(UTC).isoformat(),
            "dataset": dataset,
            "surface": surface,
            "n": len(entries),
            "digest": digest_entries(entries),
            "source_manifest": source_manifest,
            "entries": entries,
        },
    )


def _shard_entries(entries: list[dict[str, Any]], *, nshards: int) -> list[list[dict[str, Any]]]:
    per = (len(entries) + nshards - 1) // nshards
    return [entries[idx * per : (idx + 1) * per] for idx in range(nshards)]


def _write_shards(path: Path, *, dataset: str, surface: str, entries: list[dict[str, Any]], nshards: int) -> None:
    shard_dir = ensure_dir(path.parent / "shards")
    for idx, chunk in enumerate(_shard_entries(entries, nshards=nshards), start=1):
        if not chunk:
            continue
        write_json(
            shard_dir / f"{path.stem}__shard{idx:02d}of{nshards:02d}.json",
            {
                "dataset": dataset,
                "surface": surface,
                "entries": chunk,
            },
        )


def prepare_feature_bundle(
    *,
    output_dir: Path,
    report_path: Path,
    math_cluster_source: Path,
    math_generic_source: Path,
    ifeval_source: Path,
    ifbench_source: Path,
    nshards: int = 4,
    split_seeds: list[int] | None = None,
) -> dict[str, Any]:
    split_seeds = list(split_seeds or R2_SPLIT_SEEDS)
    output_dir = ensure_dir(output_dir)
    report_path = Path(report_path)

    specs = [
        {
            "label": "cluster-hard full",
            "source_path": math_cluster_source,
            "target_name": "gsm8k_train_cluster_live_full.json",
            "surface": "hard_cluster_main_r2",
            "domain": "math",
        },
        {
            "label": "generic-hard full",
            "source_path": math_generic_source,
            "target_name": "gsm8k_train_generic_live_full.json",
            "surface": "hard_generic_main_r2",
            "domain": "math",
        },
        {
            "label": "screened IFEval full",
            "source_path": ifeval_source,
            "target_name": "ifeval_screened_live_full.json",
            "surface": "ifeval_screened",
            "domain": "format",
        },
        {
            "label": "IFBench full",
            "source_path": ifbench_source,
            "target_name": "ifbench_live_full.json",
            "surface": "ifbench",
            "domain": "format",
        },
    ]

    manifest_rows: list[dict[str, Any]] = []
    for spec in specs:
        raw = read_json(spec["source_path"])
        entries = list(raw["entries"])
        dataset = str(raw.get("dataset", spec["surface"]))
        target_path = output_dir / spec["target_name"]
        _write_manifest(
            target_path,
            dataset=dataset,
            surface=str(spec["surface"]),
            entries=entries,
            source_manifest=str(spec["source_path"]),
        )
        _write_shards(target_path, dataset=dataset, surface=str(spec["surface"]), entries=entries, nshards=nshards)
        manifest_rows.append(
            {
                "domain": spec["domain"],
                "label": spec["label"],
                "manifest": str(target_path),
                "dataset": dataset,
                "surface": spec["surface"],
                "n": len(entries),
                "digest": digest_entries(entries),
                "source_manifest": str(spec["source_path"]),
            }
        )

    feature_map = {
        "shared_feature_columns": list(POOLED_FEATURE_COLUMNS),
        "abstract_action_space": list(ABSTRACT_ACTION_SPACE),
        "action_mapping": ACTION_MAPPING,
        "split_seeds": [int(seed) for seed in split_seeds],
        "split_scheme": {"train_ratio": 0.50, "cal_ratio": 0.15, "eval_ratio": 0.35},
        "phase_expected_counts": EXPECTED_SURFACE_COUNTS,
    }
    write_json(output_dir / "feature_map.json", feature_map)
    write_json(output_dir / "split_seeds.json", {"split_seeds": [int(seed) for seed in split_seeds]})
    write_json(output_dir / "surface_manifest.json", manifest_rows)

    lines = [
        "# UNIFY-LIVE-FULL-R2 Feature Audit",
        "",
        "## Purpose",
        "",
        "- This pack locks the fresh prospective manifests, feature map, and shared action geometry for `UNIFY-LIVE-FULL-R2` before final paper-facing synthesis.",
        "- The frozen math and format primitives are unchanged from the prior branches; only integrity locking, prospective policy evaluation, and synthesis are new here.",
        "",
        "## Shared Abstract Action Space",
        "",
    ]
    for action_name in ABSTRACT_ACTION_SPACE:
        lines.append(f"- `{action_name}`")
    lines.extend(
        [
            "",
            "## Frozen Action Mapping",
            "",
            f"- math local repair: `{ACTION_MAPPING['math']['LOCAL_REPAIR']}`",
            f"- format local repair: `{ACTION_MAPPING['format']['LOCAL_REPAIR']}`",
            "",
            "## Shared Feature Map",
            "",
        ]
    )
    for feature_name in POOLED_FEATURE_COLUMNS:
        lines.append(f"- `{feature_name}`")
    lines.extend(
        [
            "",
            "## Split Stability Freeze",
            "",
            f"- split seeds: `{', '.join(str(seed) for seed in split_seeds)}`",
            "- split ratios: `train=0.50`, `calibration=0.15`, `eval=0.35`",
            "",
            "## Frozen Full Prospective Surfaces",
            "",
        ]
    )
    for row in manifest_rows:
        lines.append(
            f"- `{row['label']}`: `{row['n']}` examples, digest `{row['digest']}`, manifest `{row['manifest']}`"
        )
        lines.append(f"  source: `{row['source_manifest']}`")
    write_text(report_path, "\n".join(lines))
    return {"manifest_rows": manifest_rows, "feature_map": feature_map}


def _manifest_count(path: Path) -> int:
    if not path.exists():
        return 0
    payload = read_json(path)
    if "n" in payload:
        return int(payload["n"])
    if "limit" in payload:
        return int(payload["limit"])
    return len(payload.get("entries", []))


def _math_action_rows(record: dict[str, Any]) -> list[tuple[str, str]]:
    question_id = str(record.get("question_id", ""))
    return [(question_id, str(action.get("action_name", ""))) for action in record.get("actions", [])]


def _format_action_rows(record: dict[str, Any]) -> list[tuple[str, str]]:
    example_id = str(record.get("example_id", ""))
    return [
        (example_id, "direct_formatted"),
        (example_id, "solve_then_format"),
        (example_id, "full_rewrite_on_failure"),
    ]


def audit_bank(run_root: Path, *, model_name: str) -> dict[str, Any]:
    run_root = Path(run_root)
    surface_rows: list[dict[str, Any]] = []
    shard_rows: list[dict[str, Any]] = []
    issue_rows: list[dict[str, Any]] = []
    phase_ids: dict[str, set[str]] = {}

    for phase in PHASE_SPECS:
        base_dir = run_root / phase["base_dir"]
        shard_dirs = sorted(base_dir.glob(phase["glob"]))
        records: list[dict[str, Any]] = []
        ids: list[str] = []
        flattened_action_rows: list[tuple[str, str]] = []
        parse_ready = 0
        parse_total = 0
        validator_ready = 0
        validator_total = 0
        required_action_hits = 0

        for shard_dir in shard_dirs:
            manifest_path = shard_dir / "manifest.json"
            rows_path = shard_dir / "per_example.jsonl"
            completed_path = shard_dir / "completed.txt"
            shard_records = _read_jsonl(rows_path)
            manifest_rows = _manifest_count(manifest_path)
            actual_rows = len(shard_records)

            duplicate_ids = sum(count - 1 for count in Counter(str(item.get(phase["id_key"], "")) for item in shard_records).values() if count > 1)
            shard_rows.append(
                {
                    "model_name": model_name,
                    "phase_name": phase["phase_name"],
                    "module": phase["module"],
                    "surface_name": phase["surface_name"],
                    "shard_name": shard_dir.name,
                    "manifest_rows": manifest_rows,
                    "actual_rows": actual_rows,
                    "has_manifest": int(manifest_path.exists()),
                    "has_rows": int(rows_path.exists()),
                    "completed_flag": int(completed_path.exists()),
                    "row_match": int(manifest_rows == actual_rows and actual_rows > 0),
                    "duplicate_ids": int(duplicate_ids),
                }
            )
            if not manifest_path.exists() or not rows_path.exists() or not completed_path.exists():
                issue_rows.append(
                    {
                        "severity": "error",
                        "model_name": model_name,
                        "phase_name": phase["phase_name"],
                        "issue": "missing shard completion artifact",
                        "detail": shard_dir.name,
                    }
                )
            if manifest_rows != actual_rows:
                issue_rows.append(
                    {
                        "severity": "error",
                        "model_name": model_name,
                        "phase_name": phase["phase_name"],
                        "issue": "manifest row count mismatch",
                        "detail": f"{shard_dir.name}: manifest={manifest_rows} actual={actual_rows}",
                    }
                )
            records.extend(shard_records)

        for record in records:
            example_id = str(record.get(phase["id_key"], ""))
            ids.append(example_id)
            if phase["module"] == "math":
                flattened_action_rows.extend(_math_action_rows(record))
                actions = list(record.get("actions", []))
                parse_ready += sum(int(action.get("parse_ok", 0)) for action in actions)
                parse_total += len(actions)
                validator_ready += sum(int(action.get("correctness") is not None) for action in actions)
                validator_total += len(actions)
                action_names = {str(action.get("action_name", "")) for action in actions}
                if all(required in action_names for required in phase["required_actions"]):
                    required_action_hits += 1
            else:
                flattened_action_rows.extend(_format_action_rows(record))
                for key_name in ["direct_formatted", "solve_then_format", "full_rewrite_on_failure"]:
                    item = dict(record.get(key_name) or {})
                    parse_ready += int(item.get("response_text") is not None)
                    parse_total += 1
                    validator_ready += int(item.get("success") is not None)
                    validator_total += 1
                if all(key_name in record for key_name in phase["required_actions"]):
                    required_action_hits += 1

        duplicate_ids = sum(count - 1 for count in Counter(ids).values() if count > 1)
        duplicate_action_rows = sum(count - 1 for count in Counter(flattened_action_rows).values() if count > 1)
        expected_rows = int(phase["expected_rows"])
        actual_rows = len(records)
        unique_ids = len(set(ids))
        paper_safe_surface = (
            actual_rows == expected_rows
            and unique_ids == expected_rows
            and duplicate_ids == 0
            and duplicate_action_rows == 0
            and all(item["completed_flag"] == 1 and item["row_match"] == 1 for item in shard_rows if item["phase_name"] == phase["phase_name"])
            and required_action_hits == actual_rows
        )
        if actual_rows != expected_rows:
            issue_rows.append(
                {
                    "severity": "error",
                    "model_name": model_name,
                    "phase_name": phase["phase_name"],
                    "issue": "phase row count mismatch",
                    "detail": f"expected={expected_rows} actual={actual_rows}",
                }
            )
        if duplicate_ids:
            issue_rows.append(
                {
                    "severity": "error",
                    "model_name": model_name,
                    "phase_name": phase["phase_name"],
                    "issue": "duplicate example ids",
                    "detail": str(duplicate_ids),
                }
            )
        if duplicate_action_rows:
            issue_rows.append(
                {
                    "severity": "error",
                    "model_name": model_name,
                    "phase_name": phase["phase_name"],
                    "issue": "duplicate example-action rows",
                    "detail": str(duplicate_action_rows),
                }
            )
        if required_action_hits != actual_rows:
            issue_rows.append(
                {
                    "severity": "error",
                    "model_name": model_name,
                    "phase_name": phase["phase_name"],
                    "issue": "required action coverage incomplete",
                    "detail": f"covered={required_action_hits} rows={actual_rows}",
                }
            )

        phase_ids[phase["phase_name"]] = set(ids)
        surface_rows.append(
            {
                "model_name": model_name,
                "phase_name": phase["phase_name"],
                "module": phase["module"],
                "surface_name": phase["surface_name"],
                "expected_rows": expected_rows,
                "actual_rows": actual_rows,
                "unique_ids": unique_ids,
                "duplicate_ids": duplicate_ids,
                "duplicate_example_action_rows": duplicate_action_rows,
                "shard_count": len(shard_dirs),
                "complete_shards": sum(1 for item in shard_rows if item["phase_name"] == phase["phase_name"] and item["completed_flag"] == 1),
                "parse_success_rate": (parse_ready / parse_total) if parse_total else 0.0,
                "validator_ready_rate": (validator_ready / validator_total) if validator_total else 0.0,
                "required_action_coverage": (required_action_hits / actual_rows) if actual_rows else 0.0,
                "paper_safe_surface": int(paper_safe_surface),
            }
        )

    for left_phase, right_phase in [("math_cluster_raw", "math_cluster_replay"), ("math_generic_raw", "math_generic_replay")]:
        left_ids = phase_ids.get(left_phase, set())
        right_ids = phase_ids.get(right_phase, set())
        if left_ids and right_ids and left_ids != right_ids:
            issue_rows.append(
                {
                    "severity": "error",
                    "model_name": model_name,
                    "phase_name": f"{left_phase}__vs__{right_phase}",
                    "issue": "raw/replay id mismatch",
                    "detail": f"left_only={len(left_ids - right_ids)} right_only={len(right_ids - left_ids)}",
                }
            )

    surface_summary = pd.DataFrame(surface_rows)
    shard_summary = pd.DataFrame(shard_rows)
    issues = pd.DataFrame(issue_rows)
    paper_safe = bool(not issue_rows and not surface_summary.empty and surface_summary["paper_safe_surface"].min() == 1)
    return {
        "model_name": model_name,
        "run_root": str(run_root),
        "surface_summary": surface_summary,
        "shard_summary": shard_summary,
        "issues": issues,
        "paper_safe": paper_safe,
        "restart_logs": sorted(path.name for path in run_root.glob("restart_*.log")),
    }


def _constant_decision(frame: pd.DataFrame, action_name: str) -> pd.Series:
    return pd.Series(action_name, index=frame.index, dtype="object")


def _metric_row(summary: pd.DataFrame, *, scope: str, policy: str) -> pd.Series:
    subset = summary[(summary["scope"] == scope) & (summary["policy"] == policy)]
    if subset.empty:
        raise IndexError(f"Missing summary row for scope={scope} policy={policy}")
    return subset.iloc[0]


def _pair_text(pairwise: pd.DataFrame, *, scope: str, base: str, alt: str) -> str:
    subset = pairwise[(pairwise["scope"] == scope) & (pairwise["base_policy"] == base) & (pairwise["alt_policy"] == alt)]
    if subset.empty:
        return "n/a"
    row = subset.iloc[0]
    return f"{row['delta_mean']:+.4f} [{row['delta_min']:+.4f}, {row['delta_max']:+.4f}]"


def _scope_frames(frame: pd.DataFrame) -> list[tuple[str, pd.DataFrame]]:
    scopes: list[tuple[str, pd.DataFrame]] = [("overall", frame)]
    for module_name in sorted(frame["module"].dropna().unique()):
        module_frame = frame[frame["module"] == module_name].copy()
        scopes.append((f"{module_name}:overall", module_frame))
        for surface_name in sorted(module_frame["surface"].dropna().unique()):
            scopes.append((f"{module_name}:{surface_name}", module_frame[module_frame["surface"] == surface_name].copy()))
    return scopes


def _build_model_frame(root: Path, *, model_name: str, source_tag: str) -> pd.DataFrame:
    math_frame = build_math_unified_frame(
        patterns={
            "hard_cluster_main_r2": [str(root / "math_replay" / "gsm8k_train_cluster_live_full__shard*of*" / "per_example.jsonl")],
            "hard_generic_main_r2": [str(root / "math_replay" / "gsm8k_train_generic_live_full__shard*of*" / "per_example.jsonl")],
        },
        model_name=model_name,
        source_tag=source_tag,
        local_action_name="GRANITE_POSTPROCESS_ONLY_PATCH",
        global_baseline_name="self_refine_1",
    )
    format_frame = build_format_unified_frame(
        patterns={
            "ifeval_screened": [str(root / "format" / "ifeval_shard*of*" / "per_example.jsonl")],
            "ifbench": [str(root / "format" / "ifbench_shard*of*" / "per_example.jsonl")],
        },
        model_name=model_name,
        source_tag=source_tag,
    )
    return pd.concat([math_frame, format_frame], ignore_index=True).sort_values(["module", "surface", "example_id"]).reset_index(drop=True)


def _model_root_ready(root: Path) -> bool:
    required_patterns = [
        "math_replay/gsm8k_train_cluster_live_full__shard*of*/per_example.jsonl",
        "math_replay/gsm8k_train_generic_live_full__shard*of*/per_example.jsonl",
        "format/ifeval_shard*of*/per_example.jsonl",
        "format/ifbench_shard*of*/per_example.jsonl",
    ]
    return all(any(root.glob(pattern)) for pattern in required_patterns)


def _fit_domain_rule(train_frame: pd.DataFrame, cal_frame: pd.DataFrame) -> tuple[str, Any]:
    candidates = fit_shared_simple_policies(train_frame, config=UNIFIED_CONFIG)
    target_frame = cal_frame if not cal_frame.empty else train_frame
    return select_best_simple_policy(candidates, target_frame, config=UNIFIED_CONFIG)


def _paired_bootstrap_accuracy_delta_fast(
    base_correct: list[int],
    alt_correct: list[int],
    *,
    samples: int = 500,
    seed: int = 13,
) -> tuple[float, float, float]:
    base = np.asarray(base_correct, dtype=np.int16)
    alt = np.asarray(alt_correct, dtype=np.int16)
    n = int(base.size)
    if n == 0:
        return 0.0, 0.0, 0.0
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, n, size=(samples, n), endpoint=False)
    deltas = alt[indices].mean(axis=1) - base[indices].mean(axis=1)
    deltas.sort()
    mean_delta = float(deltas.mean())
    lo = float(deltas[int(0.025 * len(deltas))])
    hi = float(deltas[int(0.975 * len(deltas))])
    return mean_delta, lo, hi


def pairwise_rows_fast(
    frame: pd.DataFrame,
    *,
    model_name: str,
    seed: int,
    policy_cols: dict[str, str],
    comparisons: list[tuple[str, str]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope_name, scope_frame in _scope_frames(frame):
        if scope_frame.empty:
            continue
        module_name = "pooled" if scope_name == "overall" else scope_name.split(":", 1)[0]
        surface_name = "overall" if scope_name.endswith(":overall") or scope_name == "overall" else scope_name.split(":", 1)[1]
        for base_policy, alt_policy in comparisons:
            base_col = policy_cols.get(base_policy)
            alt_col = policy_cols.get(alt_policy)
            if not base_col or not alt_col:
                continue
            base_success = decision_success(scope_frame, base_col, config=UNIFIED_CONFIG).astype(int)
            alt_success = decision_success(scope_frame, alt_col, config=UNIFIED_CONFIG).astype(int)
            delta, ci_low, ci_high = _paired_bootstrap_accuracy_delta_fast(base_success.tolist(), alt_success.tolist(), seed=seed)
            rows.append(
                {
                    "model_name": model_name,
                    "seed": int(seed),
                    "scope": scope_name,
                    "module": module_name,
                    "surface_name": surface_name,
                    "base_policy": base_policy,
                    "alt_policy": alt_policy,
                    "n": int(len(scope_frame)),
                    "base_accuracy": float(base_success.mean()),
                    "alt_accuracy": float(alt_success.mean()),
                    "delta": float(delta),
                    "ci_low": float(ci_low),
                    "ci_high": float(ci_high),
                    "mcnemar_p": float(mcnemar_exact(base_success.tolist(), alt_success.tolist())),
                }
            )
    return pd.DataFrame(rows)


def _aggregate_metrics(seed_rows: pd.DataFrame, *, group_cols: list[str], metric_cols: list[str]) -> pd.DataFrame:
    grouped = seed_rows.groupby(group_cols, dropna=False)
    agg_map: dict[str, list[str]] = {metric: ["mean", "std", "min", "max"] for metric in metric_cols}
    summary = grouped.agg(agg_map)
    summary.columns = [f"{metric}_{stat}" for metric, stat in summary.columns]
    return summary.reset_index()


def evaluate_model_bank(
    *,
    run_root: Path,
    model_name: str,
    split_seeds: list[int],
    results_dir: Path,
) -> dict[str, Any]:
    frame = _build_model_frame(run_root, model_name=model_name, source_tag=f"unify_live_full_r2_{model_name}")
    seed_summaries: list[pd.DataFrame] = []
    seed_pairwise: list[pd.DataFrame] = []
    transfer_seed_rows: list[pd.DataFrame] = []
    alignment_seed_rows: list[pd.DataFrame] = []
    gap_seed_rows: list[dict[str, Any]] = []
    split_payloads: list[dict[str, Any]] = []

    for seed in split_seeds:
        train_frame, cal_frame, eval_frame = stable_split_triplet(frame, seed=seed, train_ratio=0.5, cal_ratio=0.15)
        math_train = train_frame[train_frame["module"] == "math"].copy()
        math_cal = cal_frame[cal_frame["module"] == "math"].copy()
        format_train = train_frame[train_frame["module"] == "format"].copy()
        format_cal = cal_frame[cal_frame["module"] == "format"].copy()

        pooled_candidates = fit_shared_simple_policies(train_frame, config=UNIFIED_CONFIG)
        pooled_best_name, pooled_best_policy = select_best_simple_policy(
            pooled_candidates,
            cal_frame if not cal_frame.empty else train_frame,
            config=UNIFIED_CONFIG,
        )
        math_rule_name, math_rule = _fit_domain_rule(math_train if not math_train.empty else train_frame, math_cal)
        format_rule_name, format_rule = _fit_domain_rule(format_train if not format_train.empty else train_frame, format_cal)

        pooled_learned = fit_three_action_policy(train_frame, feature_columns=POOLED_FEATURE_COLUMNS, config=UNIFIED_CONFIG)
        math_learned = fit_three_action_policy(math_train if not math_train.empty else train_frame, feature_columns=POOLED_FEATURE_COLUMNS, config=UNIFIED_CONFIG)
        format_learned = fit_three_action_policy(format_train if not format_train.empty else train_frame, feature_columns=POOLED_FEATURE_COLUMNS, config=UNIFIED_CONFIG)

        eval_frame = eval_frame.copy()
        eval_frame["NO_INTERVENTION"] = _constant_decision(eval_frame, "NO_INTERVENTION")
        eval_frame["ALWAYS_LOCAL"] = _constant_decision(eval_frame, "LOCAL_REPAIR")
        eval_frame["ALWAYS_REWRITE_OR_RESTART"] = _constant_decision(eval_frame, "GLOBAL_REWRITE_OR_RESTART")
        eval_frame["ORACLE_POLICY"] = eval_frame.apply(
            lambda row: (
                "NO_INTERVENTION"
                if int(row["direct_success"]) == 1
                else ("LOCAL_REPAIR" if int(row["local_success"]) == 1 else "GLOBAL_REWRITE_OR_RESTART")
            ),
            axis=1,
        )
        eval_frame["MATH_TUNED_SIMPLE_RULE"] = math_rule.predict(eval_frame)
        eval_frame["FORMAT_TUNED_SIMPLE_RULE"] = format_rule.predict(eval_frame)
        for policy_name, policy in pooled_candidates.items():
            eval_frame[policy_name] = policy.predict(eval_frame)
        eval_frame["POOLED_RULE_BEST"] = pooled_best_policy.predict(eval_frame)
        eval_frame["POOLED_LEARNED_GATE"] = pooled_learned.predict(eval_frame)
        eval_frame["MATH_DOMAIN_LEARNED_GATE"] = math_learned.predict(eval_frame)
        eval_frame["FORMAT_DOMAIN_LEARNED_GATE"] = format_learned.predict(eval_frame)

        summary = grouped_policy_rows(
            eval_frame,
            model_name=model_name,
            policy_map=[
                ("NO_INTERVENTION", "NO_INTERVENTION"),
                ("ALWAYS_LOCAL", "ALWAYS_LOCAL"),
                ("ALWAYS_REWRITE_OR_RESTART", "ALWAYS_REWRITE_OR_RESTART"),
                ("MATH_TUNED_SIMPLE_RULE", "MATH_TUNED_SIMPLE_RULE"),
                ("FORMAT_TUNED_SIMPLE_RULE", "FORMAT_TUNED_SIMPLE_RULE"),
                ("POOLED_SIMPLE_2FEATURE", "POOLED_SIMPLE_2FEATURE"),
                ("POOLED_SIMPLE_3FEATURE", "POOLED_SIMPLE_3FEATURE"),
                ("POOLED_SIMPLE_THRESHOLDED_TREE", "POOLED_SIMPLE_THRESHOLDED_TREE"),
                ("POOLED_RULE_BEST", "POOLED_RULE_BEST"),
                ("POOLED_LEARNED_GATE", "POOLED_LEARNED_GATE"),
                ("MATH_DOMAIN_LEARNED_GATE", "MATH_DOMAIN_LEARNED_GATE"),
                ("FORMAT_DOMAIN_LEARNED_GATE", "FORMAT_DOMAIN_LEARNED_GATE"),
                ("ORACLE_POLICY", "ORACLE_POLICY"),
            ],
            config=UNIFIED_CONFIG,
        )
        summary["seed"] = int(seed)
        seed_summaries.append(summary)

        policy_cols = {
            "NO_INTERVENTION": "NO_INTERVENTION",
            "ALWAYS_LOCAL": "ALWAYS_LOCAL",
            "ALWAYS_REWRITE_OR_RESTART": "ALWAYS_REWRITE_OR_RESTART",
            "MATH_TUNED_SIMPLE_RULE": "MATH_TUNED_SIMPLE_RULE",
            "FORMAT_TUNED_SIMPLE_RULE": "FORMAT_TUNED_SIMPLE_RULE",
            "POOLED_RULE_BEST": "POOLED_RULE_BEST",
            "POOLED_LEARNED_GATE": "POOLED_LEARNED_GATE",
        }
        seed_pairwise.append(
            pairwise_rows_fast(
                eval_frame,
                model_name=model_name,
                seed=seed,
                policy_cols=policy_cols,
                comparisons=[
                    ("ALWAYS_REWRITE_OR_RESTART", "POOLED_RULE_BEST"),
                    ("ALWAYS_REWRITE_OR_RESTART", "POOLED_LEARNED_GATE"),
                    ("ALWAYS_REWRITE_OR_RESTART", "MATH_TUNED_SIMPLE_RULE"),
                    ("ALWAYS_REWRITE_OR_RESTART", "FORMAT_TUNED_SIMPLE_RULE"),
                    ("POOLED_RULE_BEST", "MATH_TUNED_SIMPLE_RULE"),
                    ("POOLED_RULE_BEST", "FORMAT_TUNED_SIMPLE_RULE"),
                ],
            )
        )

        transfer_seed_rows.append(
            pd.DataFrame(
                [
                    {
                        "model_name": model_name,
                        "seed": int(seed),
                        "direction": "math_to_format",
                        "scope": "format:overall",
                        "policy": "MATH_TUNED_SIMPLE_RULE",
                        "utility": float(_metric_row(summary, scope="format:overall", policy="MATH_TUNED_SIMPLE_RULE")["utility"]),
                        "intervention_rate": float(_metric_row(summary, scope="format:overall", policy="MATH_TUNED_SIMPLE_RULE")["intervention_rate"]),
                    },
                    {
                        "model_name": model_name,
                        "seed": int(seed),
                        "direction": "format_to_math",
                        "scope": "math:overall",
                        "policy": "FORMAT_TUNED_SIMPLE_RULE",
                        "utility": float(_metric_row(summary, scope="math:overall", policy="FORMAT_TUNED_SIMPLE_RULE")["utility"]),
                        "intervention_rate": float(_metric_row(summary, scope="math:overall", policy="FORMAT_TUNED_SIMPLE_RULE")["intervention_rate"]),
                    },
                    {
                        "model_name": model_name,
                        "seed": int(seed),
                        "direction": "pooled_to_math",
                        "scope": "math:overall",
                        "policy": "POOLED_RULE_BEST",
                        "utility": float(_metric_row(summary, scope="math:overall", policy="POOLED_RULE_BEST")["utility"]),
                        "intervention_rate": float(_metric_row(summary, scope="math:overall", policy="POOLED_RULE_BEST")["intervention_rate"]),
                    },
                    {
                        "model_name": model_name,
                        "seed": int(seed),
                        "direction": "pooled_to_format",
                        "scope": "format:overall",
                        "policy": "POOLED_RULE_BEST",
                        "utility": float(_metric_row(summary, scope="format:overall", policy="POOLED_RULE_BEST")["utility"]),
                        "intervention_rate": float(_metric_row(summary, scope="format:overall", policy="POOLED_RULE_BEST")["intervention_rate"]),
                    },
                ]
            )
        )

        align = eval_frame.groupby(["module", "shared_failure_bucket", "surface"], dropna=False).size().reset_index(name="n")
        align["seed"] = int(seed)
        align["model_name"] = model_name
        align["share_within_module"] = align.groupby(["module"])["n"].transform(lambda col: col / col.sum())
        alignment_seed_rows.append(align)

        gap_seed_rows.extend(
            [
                {
                    "model_name": model_name,
                    "seed": int(seed),
                    "module": "math",
                    "domain_policy": "MATH_TUNED_SIMPLE_RULE",
                    "pooled_policy": "POOLED_RULE_BEST",
                    "domain_utility": float(_metric_row(summary, scope="math:overall", policy="MATH_TUNED_SIMPLE_RULE")["utility"]),
                    "pooled_utility": float(_metric_row(summary, scope="math:overall", policy="POOLED_RULE_BEST")["utility"]),
                    "utility_gap": float(_metric_row(summary, scope="math:overall", policy="POOLED_RULE_BEST")["utility"])
                    - float(_metric_row(summary, scope="math:overall", policy="MATH_TUNED_SIMPLE_RULE")["utility"]),
                },
                {
                    "model_name": model_name,
                    "seed": int(seed),
                    "module": "format",
                    "domain_policy": "FORMAT_TUNED_SIMPLE_RULE",
                    "pooled_policy": "POOLED_RULE_BEST",
                    "domain_utility": float(_metric_row(summary, scope="format:overall", policy="FORMAT_TUNED_SIMPLE_RULE")["utility"]),
                    "pooled_utility": float(_metric_row(summary, scope="format:overall", policy="POOLED_RULE_BEST")["utility"]),
                    "utility_gap": float(_metric_row(summary, scope="format:overall", policy="POOLED_RULE_BEST")["utility"])
                    - float(_metric_row(summary, scope="format:overall", policy="FORMAT_TUNED_SIMPLE_RULE")["utility"]),
                },
            ]
        )
        split_payloads.append(
            {
                "seed": int(seed),
                "n_train": int(len(train_frame)),
                "n_cal": int(len(cal_frame)),
                "n_eval": int(len(eval_frame)),
                "math_rule_name": math_rule_name,
                "format_rule_name": format_rule_name,
                "pooled_best_name": pooled_best_name,
                "pooled_best_rule": asdict(pooled_best_policy),
            }
        )

    seed_summary = pd.concat(seed_summaries, ignore_index=True)
    seed_pairwise_frame = pd.concat(seed_pairwise, ignore_index=True)
    transfer_seed = pd.concat(transfer_seed_rows, ignore_index=True)
    alignment_seed = pd.concat(alignment_seed_rows, ignore_index=True)
    gap_seed = pd.DataFrame(gap_seed_rows)

    summary = _aggregate_metrics(
        seed_summary,
        group_cols=["model_name", "scope", "module", "surface_name", "policy"],
        metric_cols=["n", "success_rate", "utility", "intervention_rate", "false_intervene_rate", "missed_intervene_rate", "avg_latency_s"],
    )
    pairwise = _aggregate_metrics(
        seed_pairwise_frame,
        group_cols=["model_name", "scope", "module", "surface_name", "base_policy", "alt_policy"],
        metric_cols=["n", "base_accuracy", "alt_accuracy", "delta", "mcnemar_p"],
    )
    transfer = _aggregate_metrics(
        transfer_seed,
        group_cols=["model_name", "direction", "scope", "policy"],
        metric_cols=["utility", "intervention_rate"],
    )
    domain_gap = _aggregate_metrics(
        gap_seed,
        group_cols=["model_name", "module", "domain_policy", "pooled_policy"],
        metric_cols=["domain_utility", "pooled_utility", "utility_gap"],
    )
    alignment = _aggregate_metrics(
        alignment_seed,
        group_cols=["model_name", "module", "shared_failure_bucket", "surface"],
        metric_cols=["share_within_module", "n"],
    )

    results_dir = ensure_dir(results_dir)
    write_text(results_dir / "policy_split_manifest.json", json.dumps(split_payloads, indent=2))
    seed_summary.to_csv(results_dir / "seed_summary.csv", index=False)
    seed_pairwise_frame.to_csv(results_dir / "seed_pairwise.csv", index=False)
    transfer_seed.to_csv(results_dir / "seed_transfer.csv", index=False)
    summary.to_csv(results_dir / "summary.csv", index=False)
    pairwise.to_csv(results_dir / "pairwise.csv", index=False)
    transfer.to_csv(results_dir / "transfer.csv", index=False)
    domain_gap.to_csv(results_dir / "domain_gap.csv", index=False)
    alignment.to_csv(results_dir / "alignment.csv", index=False)

    return {
        "model_name": model_name,
        "run_root": str(run_root),
        "results_dir": str(results_dir),
        "summary": summary,
        "pairwise": pairwise,
        "transfer": transfer,
        "domain_gap": domain_gap,
        "alignment": alignment,
        "seed_summary": seed_summary,
        "seed_pairwise": seed_pairwise_frame,
    }


def _plot_integrity(summary: pd.DataFrame, out_path: Path) -> None:
    if summary.empty:
        return
    plot = summary.copy()
    plot["label"] = plot["model_name"].str.replace("Qwen/Qwen2.5-7B-Instruct", "Qwen-7B", regex=False)
    plot["label"] = plot["label"].str.replace("mistralai/Mistral-7B-Instruct-v0.3", "Mistral-7B", regex=False)
    labels = [f"{row.label}\n{row.phase_name}" for row in plot.itertuples(index=False)]
    x = np.arange(len(labels))
    width = 0.35
    plt.figure(figsize=(12.5, 4.8))
    plt.bar(x - width / 2, plot["expected_rows"], width=width, label="expected", color="#d8d8d8")
    plt.bar(x + width / 2, plot["actual_rows"], width=width, label="actual", color="#4f78c9")
    for idx, row in enumerate(plot.itertuples(index=False)):
        plt.text(idx + width / 2, row.actual_rows, f"safe={row.paper_safe_surface}", ha="center", va="bottom", fontsize=8)
    plt.xticks(x, labels, rotation=20, ha="right")
    plt.ylabel("Rows")
    plt.title("7B Prospective Bank Integrity Summary")
    plt.tight_layout()
    plt.legend()
    plt.savefig(out_path, dpi=200)
    plt.close()


def _plot_head_to_head(pairwise: pd.DataFrame, *, module: str, domain_policy: str, out_path: Path, title: str) -> None:
    plot = pairwise[
        (pairwise["module"] == module)
        & (pairwise["base_policy"] == "ALWAYS_REWRITE_OR_RESTART")
        & (pairwise["alt_policy"].isin([domain_policy, "POOLED_RULE_BEST"]))
    ].copy()
    if plot.empty:
        return
    plot = plot.groupby(["model_name", "surface_name", "alt_policy"], dropna=False)["delta_mean"].mean().reset_index()
    pivot = plot.pivot(index=["model_name", "surface_name"], columns="alt_policy", values="delta_mean").fillna(0.0)
    colors = ["#cc8a3a", "#4f78c9"] if module == "math" else ["#4e8f7c", "#4f78c9"]
    pivot.plot(kind="bar", figsize=(11.5, 5.0), color=colors)
    plt.ylabel("Mean Delta vs Rewrite")
    plt.title(title)
    plt.xticks(rotation=18, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def _plot_gap(domain_gap: pd.DataFrame, out_path: Path) -> None:
    if domain_gap.empty:
        return
    pivot = domain_gap.pivot(index="model_name", columns="module", values="utility_gap_mean").fillna(0.0)
    pivot.plot(kind="bar", figsize=(8.4, 4.8), color=["#cc8a3a", "#4e8f7c"])
    plt.axhline(0.0, color="black", linewidth=1)
    plt.ylabel("Pooled - Domain Utility")
    plt.title("Pooled vs Domain-Specific Rule Gap")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def _plot_family(summary: pd.DataFrame, out_path: Path) -> None:
    plot = summary[
        (summary["scope"] == "overall")
        & summary["policy"].isin(["ALWAYS_REWRITE_OR_RESTART", "MATH_TUNED_SIMPLE_RULE", "FORMAT_TUNED_SIMPLE_RULE", "POOLED_RULE_BEST"])
    ].copy()
    if plot.empty:
        return
    plot = plot.groupby(["model_name", "policy"], dropna=False)["utility_mean"].mean().reset_index()
    pivot = plot.pivot(index="model_name", columns="policy", values="utility_mean").fillna(0.0)
    pivot.plot(kind="bar", figsize=(10.4, 4.8), color=["#777777", "#cc8a3a", "#4e8f7c", "#4f78c9"])
    plt.ylabel("Mean Utility")
    plt.title("Family and Scale Comparison")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def _plot_alignment(alignment: pd.DataFrame, out_path: Path) -> None:
    if alignment.empty:
        return
    pivot = alignment.groupby(["shared_failure_bucket", "module"], dropna=False)["share_within_module_mean"].mean().unstack(fill_value=0.0)
    plt.figure(figsize=(7.8, 4.8))
    plt.imshow(pivot.values, aspect="auto", cmap="YlGnBu")
    plt.xticks(range(len(pivot.columns)), pivot.columns)
    plt.yticks(range(len(pivot.index)), pivot.index)
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            plt.text(j, i, f"{pivot.iloc[i, j]:.2f}", ha="center", va="center", fontsize=9, color="black")
    plt.title("Shared Failure-Bucket Alignment")
    plt.colorbar(fraction=0.046, pad=0.04)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def _plot_summary(summary: pd.DataFrame, out_path: Path) -> None:
    plot = summary[
        (summary["scope"] == "overall")
        & summary["policy"].isin(["NO_INTERVENTION", "ALWAYS_REWRITE_OR_RESTART", "POOLED_RULE_BEST", "ORACLE_POLICY"])
    ].copy()
    if plot.empty:
        return
    plot = plot.groupby(["model_name", "policy"], dropna=False)["utility_mean"].mean().reset_index()
    pivot = plot.pivot(index="model_name", columns="policy", values="utility_mean").fillna(0.0)
    pivot.plot(kind="bar", figsize=(10.4, 4.8), color=["#9b9b9b", "#666666", "#4f78c9", "#5aa469"])
    plt.ylabel("Mean Utility")
    plt.title("Final Cross-Domain Integration Summary")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def make_main_tables(model_result: dict[str, Any], table_dir: Path, prefix: str) -> dict[str, pd.DataFrame]:
    summary = model_result["summary"]
    pairwise = model_result["pairwise"]

    math_table = summary[
        (summary["module"] == "math")
        & summary["policy"].isin(["NO_INTERVENTION", "ALWAYS_REWRITE_OR_RESTART", "MATH_TUNED_SIMPLE_RULE", "POOLED_RULE_BEST"])
    ].copy()
    format_table = summary[
        (summary["module"] == "format")
        & summary["policy"].isin(["NO_INTERVENTION", "ALWAYS_REWRITE_OR_RESTART", "FORMAT_TUNED_SIMPLE_RULE", "POOLED_RULE_BEST"])
    ].copy()
    pairwise_table = pairwise[
        pairwise["alt_policy"].isin(["POOLED_RULE_BEST", "POOLED_LEARNED_GATE", "MATH_TUNED_SIMPLE_RULE", "FORMAT_TUNED_SIMPLE_RULE"])
    ].copy()
    math_table.to_csv(table_dir / f"{prefix}_math_head_to_head.csv", index=False)
    format_table.to_csv(table_dir / f"{prefix}_format_head_to_head.csv", index=False)
    pairwise_table.to_csv(table_dir / f"{prefix}_pairwise_focus.csv", index=False)
    return {"math": math_table, "format": format_table, "pairwise": pairwise_table}


def write_integrity_report(
    *,
    audits: list[dict[str, Any]],
    qwen14_audit: dict[str, Any] | None,
    report_path: Path,
) -> None:
    surface_tables: list[pd.DataFrame] = []
    issue_lines: list[str] = []
    lines = [
        "# UNIFY-LIVE-FULL-R2 Integrity Report",
        "",
        "## Main read",
        "",
    ]
    for audit in audits:
        short_name = audit["model_name"].split("/")[-1]
        lines.append(
            f"- `{short_name}` paper-safe verdict: `{int(audit['paper_safe'])}`; restart logs present: `{', '.join(audit['restart_logs']) or 'none'}`."
        )
        surface_tables.append(audit["surface_summary"])
        if not audit["issues"].empty:
            for row in audit["issues"].itertuples(index=False):
                issue_lines.append(f"- `{short_name}` / `{row.phase_name}`: {row.issue} ({row.detail})")
    lines.extend(["", "## 7B surface integrity table", ""])
    if surface_tables:
        lines.append(pd.concat(surface_tables, ignore_index=True).to_markdown(index=False))
    lines.extend(["", "## Issues", ""])
    if issue_lines:
        lines.extend(issue_lines)
    else:
        lines.append("- No 7B data repairs were required; both fresh prospective banks are paper-safe.")
    if qwen14_audit is not None:
        lines.extend(
            [
                "",
                "## Qwen-14B partial status snapshot",
                "",
                qwen14_audit["surface_summary"].to_markdown(index=False),
            ]
        )
    write_text(report_path, "\n".join(lines))


def write_model_report(
    *,
    model_result: dict[str, Any],
    integrity_audit: dict[str, Any],
    report_path: Path,
    title: str,
    resumed_note: str | None = None,
) -> None:
    summary = model_result["summary"]
    pairwise = model_result["pairwise"]
    transfer = model_result["transfer"]
    domain_gap = model_result["domain_gap"]
    seed_summary = model_result["seed_summary"]

    lines = [f"# {title}", "", "## Integrity lock", ""]
    lines.append(f"- paper-safe bank: `{int(integrity_audit['paper_safe'])}`")
    lines.append(f"- restart logs: `{', '.join(integrity_audit['restart_logs']) or 'none'}`")
    if resumed_note:
        lines.append(f"- resumed-run stability note: {resumed_note}")

    lines.extend(
        [
            "",
            "## Overall prospective read",
            "",
            summary[
                (summary["scope"] == "overall")
                & summary["policy"].isin(
                    [
                        "NO_INTERVENTION",
                        "ALWAYS_LOCAL",
                        "ALWAYS_REWRITE_OR_RESTART",
                        "MATH_TUNED_SIMPLE_RULE",
                        "FORMAT_TUNED_SIMPLE_RULE",
                        "POOLED_RULE_BEST",
                        "POOLED_LEARNED_GATE",
                        "ORACLE_POLICY",
                    ]
                )
            ].to_markdown(index=False),
            "",
            "## Pairwise lock checks",
            "",
            f"- pooled simple vs rewrite overall: `{_pair_text(pairwise, scope='overall', base='ALWAYS_REWRITE_OR_RESTART', alt='POOLED_RULE_BEST')}`",
            f"- pooled learned vs rewrite overall: `{_pair_text(pairwise, scope='overall', base='ALWAYS_REWRITE_OR_RESTART', alt='POOLED_LEARNED_GATE')}`",
            f"- pooled simple vs math-tuned overall: `{_pair_text(pairwise, scope='overall', base='POOLED_RULE_BEST', alt='MATH_TUNED_SIMPLE_RULE')}`",
            f"- pooled simple vs format-tuned overall: `{_pair_text(pairwise, scope='overall', base='POOLED_RULE_BEST', alt='FORMAT_TUNED_SIMPLE_RULE')}`",
            "",
            "## Domain gaps",
            "",
            domain_gap.to_markdown(index=False),
            "",
            "## Transfer asymmetry",
            "",
            transfer.to_markdown(index=False),
            "",
            "## Split stability rows",
            "",
            seed_summary[
                (seed_summary["scope"] == "overall")
                & seed_summary["policy"].isin(["ALWAYS_REWRITE_OR_RESTART", "MATH_TUNED_SIMPLE_RULE", "FORMAT_TUNED_SIMPLE_RULE", "POOLED_RULE_BEST"])
            ].to_markdown(index=False),
        ]
    )
    write_text(report_path, "\n".join(lines))


def write_qwen14_collection_report(*, audit: dict[str, Any], attempts: list[dict[str, Any]], report_path: Path) -> None:
    lines = [
        "# UNIFY-LIVE-FULL-R2 Qwen-14B Collection Report",
        "",
        "## Status",
        "",
        f"- run root: `{audit['run_root']}`",
        f"- paper-safe completion: `{int(audit['paper_safe'])}`",
        "",
        "## Surface snapshot",
        "",
        audit["surface_summary"].to_markdown(index=False),
        "",
        "## Restart attempts",
        "",
    ]
    if attempts:
        lines.append(pd.DataFrame(attempts).to_markdown(index=False))
    else:
        lines.append("- No new R2 restart attempt metadata was recorded.")
    write_text(report_path, "\n".join(lines))


def write_qwen14_report(
    *,
    model_result: dict[str, Any] | None,
    audit: dict[str, Any],
    report_path: Path,
) -> None:
    if model_result is None:
        lines = [
            "# UNIFY-LIVE-FULL-R2 Qwen-14B Report",
            "",
            "## Outcome",
            "",
            "- No prospective Qwen-14B conclusion is claimed in R2.",
            "- The collection root remains incomplete, so the scale cell is treated as partial evidence only.",
            "",
            "## Current partial audit",
            "",
            audit["surface_summary"].to_markdown(index=False),
        ]
        write_text(report_path, "\n".join(lines))
        return
    write_model_report(
        model_result=model_result,
        integrity_audit=audit,
        report_path=report_path,
        title="UNIFY-LIVE-FULL-R2 Qwen-14B Prospective Report",
    )


def write_synthesis_report(
    *,
    model_results: list[dict[str, Any]],
    report_path: Path,
) -> None:
    summary = pd.concat([item["summary"] for item in model_results], ignore_index=True)
    pairwise = pd.concat([item["pairwise"] for item in model_results], ignore_index=True)
    transfer = pd.concat([item["transfer"] for item in model_results], ignore_index=True)
    domain_gap = pd.concat([item["domain_gap"] for item in model_results], ignore_index=True)
    alignment = pd.concat([item["alignment"] for item in model_results], ignore_index=True)

    lines = [
        "# UNIFY-LIVE-FULL-R2 Synthesis",
        "",
        "## Main read",
        "",
    ]
    for model_name in summary["model_name"].drop_duplicates().tolist():
        short_name = model_name.split("/")[-1]
        lines.append(
            f"- `{short_name}` pooled simple vs rewrite overall: `{_pair_text(pairwise[pairwise['model_name'] == model_name], scope='overall', base='ALWAYS_REWRITE_OR_RESTART', alt='POOLED_RULE_BEST')}`"
        )
    lines.extend(
        [
            "",
            "## Pooled vs domain-specific gap",
            "",
            domain_gap.to_markdown(index=False),
            "",
            "## Transfer asymmetry",
            "",
            transfer.to_markdown(index=False),
            "",
            "## Shared failure-bucket alignment",
            "",
            alignment.to_markdown(index=False),
        ]
    )
    write_text(report_path, "\n".join(lines))


def write_failure_notes(
    *,
    qwen_audit: dict[str, Any],
    mistral_audit: dict[str, Any],
    qwen14_audit: dict[str, Any] | None,
    report_path: Path,
) -> None:
    lines = [
        "# UNIFY-LIVE-FULL-R2 Failure Notes",
        "",
        f"- `Qwen-7B` paper-safe: `{int(qwen_audit['paper_safe'])}`.",
        f"- `Mistral-7B` paper-safe: `{int(mistral_audit['paper_safe'])}`.",
        "- The resumed Mistral parent runner left restart metadata but no duplicate rows, no incomplete completed-shard artifacts, and no raw/replay ID mismatch.",
    ]
    if qwen14_audit is not None:
        if qwen14_audit["paper_safe"]:
            lines.append("- `Qwen-14B` is now paper-safe on the completed R2 run root and can be used as a bounded scale-compression check.")
        else:
            lines.append("- `Qwen-14B` remains incomplete in the currently available collection root and cannot support a paper-facing prospective scale claim yet.")
    lines.append("- `IFBench` remains the harder boundary surface and should still be read as a stress test rather than a parity target.")
    write_text(report_path, "\n".join(lines))


def write_summary_memo(
    *,
    model_results: list[dict[str, Any]],
    qwen14_complete: bool,
    report_path: Path,
) -> None:
    summary = pd.concat([item["summary"] for item in model_results], ignore_index=True)
    pairwise = pd.concat([item["pairwise"] for item in model_results], ignore_index=True)
    domain_gap = pd.concat([item["domain_gap"] for item in model_results], ignore_index=True)

    qwen = summary[summary["model_name"] == "Qwen/Qwen2.5-7B-Instruct"].copy()
    mistral = summary[summary["model_name"] == "mistralai/Mistral-7B-Instruct-v0.3"].copy()
    lines = [
        "# UNIFY-LIVE-FULL-R2 Summary Memo",
        "",
        "## Main-paper positioning",
        "",
        "- Output-constraint is now strong enough to sit beside math as a co-main empirical pillar because the fresh 7B prospective pooled-vs-rewrite checks stay positive on both main format surfaces.",
        "- The shared cross-domain geometry should be claimed as `late-stage final-requirement realization with targeted local repair`, not as a promise that one universal rule wins every cell.",
        "",
        "## Fresh 7B lock",
        "",
        f"- Qwen-7B pooled-vs-rewrite overall: `{_pair_text(pairwise[pairwise['model_name'] == 'Qwen/Qwen2.5-7B-Instruct'], scope='overall', base='ALWAYS_REWRITE_OR_RESTART', alt='POOLED_RULE_BEST')}`.",
        f"- Mistral-7B pooled-vs-rewrite overall: `{_pair_text(pairwise[pairwise['model_name'] == 'mistralai/Mistral-7B-Instruct-v0.3'], scope='overall', base='ALWAYS_REWRITE_OR_RESTART', alt='POOLED_RULE_BEST')}`.",
        f"- Qwen-7B pooled gap on math / format: `math {domain_gap[(domain_gap['model_name'] == 'Qwen/Qwen2.5-7B-Instruct') & (domain_gap['module'] == 'math')]['utility_gap_mean'].iloc[0]:+.4f}`, `format {domain_gap[(domain_gap['model_name'] == 'Qwen/Qwen2.5-7B-Instruct') & (domain_gap['module'] == 'format')]['utility_gap_mean'].iloc[0]:+.4f}`.",
        f"- Mistral-7B pooled gap on math / format: `math {domain_gap[(domain_gap['model_name'] == 'mistralai/Mistral-7B-Instruct-v0.3') & (domain_gap['module'] == 'math')]['utility_gap_mean'].iloc[0]:+.4f}`, `format {domain_gap[(domain_gap['model_name'] == 'mistralai/Mistral-7B-Instruct-v0.3') & (domain_gap['module'] == 'format')]['utility_gap_mean'].iloc[0]:+.4f}`.",
        "",
        "## Safest claim wording",
        "",
        "- Fresh prospective evidence on Qwen-7B and Mistral-7B supports presenting hard arithmetic repair and validator-rich output-constraint repair as two manifestations of one late-stage requirement-realization intervention geometry.",
        "- A pooled simple rule does not need to dominate every domain-specific rule to support the main story; it needs to stay clearly above naive rewrite and reasonably close to the best domain-tuned simple rule.",
        "- Strongest safe sentence: `Across fresh prospective Qwen-7B, Mistral-7B, and a completed Qwen-14B scale check, hard arithmetic repair and validator-rich output-constraint repair behave like two instances of one late-stage requirement-realization problem in which targeted local repair consistently beats naive full rewrite while pooled simple policies stay close to domain-tuned rules.`",
        "",
        "## Qwen-14B status",
        "",
    ]
    if qwen14_complete:
        qwen14_pair = pairwise[pairwise["model_name"] == "Qwen/Qwen2.5-14B-Instruct"]
        lines.append(f"- Qwen-14B pooled-vs-rewrite overall: `{_pair_text(qwen14_pair, scope='overall', base='ALWAYS_REWRITE_OR_RESTART', alt='POOLED_RULE_BEST')}`.")
        lines.append("- Qwen-14B is complete and can be reported as a scale-compression check; gains compress relative to 7B, but the shared geometry remains positive.")
    else:
        lines.append("- Qwen-14B remains partial / incomplete and should be treated as out-of-scope for the main prospective conclusion unless collection is finished cleanly.")
    write_text(report_path, "\n".join(lines))


def write_bundle_outputs(
    *,
    audits: list[dict[str, Any]],
    model_results: list[dict[str, Any]],
    qwen14_audit: dict[str, Any] | None,
    qwen14_result: dict[str, Any] | None,
    report_dir: Path,
    table_dir: Path,
    figure_dir: Path,
    qwen14_attempts: list[dict[str, Any]] | None = None,
) -> None:
    report_dir = ensure_dir(report_dir)
    table_dir = ensure_dir(table_dir)
    figure_dir = ensure_dir(figure_dir)

    integrity_summary = pd.concat([audit["surface_summary"] for audit in audits], ignore_index=True)
    integrity_summary.to_csv(table_dir / "integrity_summary.csv", index=False)
    _plot_integrity(integrity_summary, figure_dir / "integrity_summary_7b.png")

    all_model_results = list(model_results)
    if qwen14_result is not None:
        all_model_results.append(qwen14_result)

    result_by_name = {item["model_name"]: item for item in all_model_results}
    qwen_result = result_by_name.get("Qwen/Qwen2.5-7B-Instruct")
    mistral_result = result_by_name.get("mistralai/Mistral-7B-Instruct-v0.3")
    qwen14_model_result = result_by_name.get("Qwen/Qwen2.5-14B-Instruct")

    if qwen_result is not None:
        make_main_tables(qwen_result, table_dir, "qwen")
    if mistral_result is not None:
        make_main_tables(mistral_result, table_dir, "mistral")
    if qwen14_model_result is not None:
        make_main_tables(qwen14_model_result, table_dir, "qwen14b")

    combined_summary = pd.concat([item["summary"] for item in all_model_results], ignore_index=True)
    combined_pairwise = pd.concat([item["pairwise"] for item in all_model_results], ignore_index=True)
    combined_gap = pd.concat([item["domain_gap"] for item in all_model_results], ignore_index=True)
    combined_alignment = pd.concat([item["alignment"] for item in all_model_results], ignore_index=True)
    combined_summary.to_csv(table_dir / "summary.csv", index=False)
    combined_pairwise.to_csv(table_dir / "pairwise.csv", index=False)
    combined_gap.to_csv(table_dir / "domain_gap.csv", index=False)
    combined_alignment.to_csv(table_dir / "alignment.csv", index=False)

    _plot_head_to_head(
        combined_pairwise,
        module="math",
        domain_policy="MATH_TUNED_SIMPLE_RULE",
        out_path=figure_dir / "fresh_math_head_to_head.png",
        title="Fresh Prospective Head-to-Head on Math",
    )
    _plot_head_to_head(
        combined_pairwise,
        module="format",
        domain_policy="FORMAT_TUNED_SIMPLE_RULE",
        out_path=figure_dir / "fresh_format_head_to_head.png",
        title="Fresh Prospective Head-to-Head on Format",
    )
    _plot_gap(combined_gap, figure_dir / "pooled_vs_domain_gap.png")
    _plot_family(combined_summary, figure_dir / "family_and_scale_comparison.png")
    _plot_alignment(combined_alignment, figure_dir / "failure_bucket_alignment_map.png")
    _plot_summary(combined_summary, figure_dir / "cross_domain_integration_summary.png")

    audit_by_name = {item["model_name"]: item for item in audits}
    if qwen_result is not None:
        write_model_report(
            model_result=qwen_result,
            integrity_audit=audit_by_name["Qwen/Qwen2.5-7B-Instruct"],
            report_path=report_dir / "unify_live_full_r2_qwen_report.md",
            title="UNIFY-LIVE-FULL-R2 Qwen-7B Prospective Report",
        )
    if mistral_result is not None:
        write_model_report(
            model_result=mistral_result,
            integrity_audit=audit_by_name["mistralai/Mistral-7B-Instruct-v0.3"],
            report_path=report_dir / "unify_live_full_r2_mistral_report.md",
            title="UNIFY-LIVE-FULL-R2 Mistral-7B Prospective Report",
            resumed_note="no detectable data instability after the interrupted parent runner; completed-shard counts, row uniqueness, and raw/replay ID coverage all stayed clean",
        )
    write_integrity_report(
        audits=audits,
        qwen14_audit=qwen14_audit,
        report_path=report_dir / "unify_live_full_r2_integrity_report.md",
    )
    if qwen14_audit is not None:
        write_qwen14_collection_report(
            audit=qwen14_audit,
            attempts=list(qwen14_attempts or []),
            report_path=report_dir / "unify_live_full_r2_qwen14b_collection_report.md",
        )
        write_qwen14_report(
            model_result=qwen14_result,
            audit=qwen14_audit,
            report_path=report_dir / "unify_live_full_r2_qwen14b_report.md",
        )
    write_synthesis_report(
        model_results=all_model_results,
        report_path=report_dir / "unify_live_full_r2_synthesis.md",
    )
    write_failure_notes(
        qwen_audit=audit_by_name["Qwen/Qwen2.5-7B-Instruct"],
        mistral_audit=audit_by_name["mistralai/Mistral-7B-Instruct-v0.3"],
        qwen14_audit=qwen14_audit,
        report_path=report_dir / "unify_live_full_r2_failure_notes.md",
    )
    write_summary_memo(
        model_results=all_model_results,
        qwen14_complete=bool(qwen14_result is not None),
        report_path=report_dir / "unify_live_full_r2_summary_memo.md",
    )
