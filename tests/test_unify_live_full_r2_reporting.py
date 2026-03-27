from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")


def _math_row(question_id: str, *, surface: str, cluster: str, direct: int, local: int, global_restart: int) -> dict:
    return {
        "dataset": "gsm8k_train",
        "question_id": question_id,
        "question": f"Question {question_id}",
        "gold_answer": "1",
        "gold_normalized": "1",
        "task_type": "math_word_problem",
        "draft": {
            "answer": "0",
            "normalized_answer": "0",
            "scratch": "work",
            "correctness": int(direct),
            "latency_s": 1.0,
            "input_tokens": 10,
            "output_tokens": 10,
            "raw_paths": [],
        },
        "metadata": {
            "surface": surface,
            "cluster": cluster,
            "checker_target_score": 4 if local else 1,
            "checker_role_score": 1,
            "draft_source": "fresh",
        },
        "general_features": {
            "question_word_count": 10,
            "question_number_count": 2,
            "comparison_cue": 0,
            "rate_unit_cue": 1,
        },
        "baselines": {
            "self_refine_1": {
                "correctness": int(global_restart),
                "latency_s": 2.0,
            }
        },
        "actions": [
            {"action_name": "RAW_PYTHON", "correctness": 0, "latency_s": 1.1, "parse_ok": 1},
            {"action_name": "OPERATOR_SCHEMA_TO_CODE_BASE", "correctness": 0, "latency_s": 1.2, "parse_ok": 1},
            {"action_name": "ATLAS_FIELDWISE_SCHEMA_TO_CODE", "correctness": 0, "latency_s": 1.3, "parse_ok": 1},
            {"action_name": "CASS_TARGET_POSTPROCESS_PATCH", "correctness": int(local), "latency_s": 1.4, "parse_ok": 1},
            {"action_name": "GRANITE_POSTPROCESS_ONLY_PATCH", "correctness": int(local), "latency_s": 1.5, "parse_ok": 1},
        ],
    }


def _format_row(example_id: str, *, surface: str, direct: int, local: int, rewrite: int) -> dict:
    prompt = "Include the keyword apple and do not use commas."
    item = {
        "failed_instruction_count": 1 if not direct else 0,
        "success": int(direct),
        "latency_s": 1.0,
        "response_text": "apple",
    }
    return {
        "surface": surface,
        "example_id": example_id,
        "difficulty": "easy" if surface == "ifeval_screened" else "hard",
        "prompt": prompt,
        "instruction_example": {"instruction_id_list": ["detectable_content:keywords:existence"]},
        "direct_formatted": dict(item),
        "solve_then_format": {"success": int(local), "latency_s": 1.3, "response_text": "apple", "failed_instruction_count": 0},
        "full_rewrite_on_failure": {"success": int(rewrite), "latency_s": 1.8, "response_text": "apple", "failed_instruction_count": 0},
    }


def _write_manifest(shard_dir: Path, size: int) -> None:
    _write_json(shard_dir / "manifest.json", {"entries": [{"id": idx} for idx in range(size)]})
    (shard_dir / "completed.txt").write_text("ok", encoding="utf-8")


def _build_fake_root(root: Path) -> None:
    shard = "01of04"
    cluster_raw = [_math_row(f"c{index}", surface="hard_cluster_main_r2", cluster="cluster", direct=index % 5 == 0, local=index % 2 == 0, global_restart=index % 3 == 0) for index in range(10)]
    generic_raw = [_math_row(f"g{index}", surface="hard_generic_main_r2", cluster="generic", direct=index % 4 == 0, local=index % 2 == 1, global_restart=index % 3 == 1) for index in range(10)]
    ifeval_rows = [_format_row(f"i{index}", surface="ifeval_screened", direct=index % 4 == 0, local=index % 2 == 0, rewrite=index % 3 == 0) for index in range(10)]
    ifbench_rows = [_format_row(f"b{index}", surface="ifbench", direct=index % 5 == 0, local=index % 2 == 1, rewrite=index % 3 == 1) for index in range(10)]

    for path, rows in [
        (root / "math_replay" / f"gsm8k_train_cluster_live_full__shard{shard}" / "per_example.jsonl", cluster_raw),
        (root / "math_replay" / f"gsm8k_train_generic_live_full__shard{shard}" / "per_example.jsonl", generic_raw),
        (root / "math_raw" / f"gsm8k_train_cluster_live_full__shard{shard}" / "per_example.jsonl", cluster_raw),
        (root / "math_raw" / f"gsm8k_train_generic_live_full__shard{shard}" / "per_example.jsonl", generic_raw),
        (root / "format" / f"ifeval_shard{shard}" / "per_example.jsonl", ifeval_rows),
        (root / "format" / f"ifbench_shard{shard}" / "per_example.jsonl", ifbench_rows),
    ]:
        _write_jsonl(path, rows)
        _write_manifest(path.parent, len(rows))


def test_unify_live_full_r2_reporting_generates_outputs(tmp_path: Path) -> None:
    manifest_root = tmp_path / "manifests"
    manifest_root.mkdir(parents=True)
    (manifest_root / "split_seeds.json").write_text(json.dumps({"split_seeds": [13, 29, 47]}), encoding="utf-8")

    qwen_root = tmp_path / "qwen"
    mistral_root = tmp_path / "mistral"
    qwen14_root = tmp_path / "qwen14"
    for root in [qwen_root, mistral_root, qwen14_root]:
        _build_fake_root(root)

    report_dir = tmp_path / "reports"
    table_dir = tmp_path / "tables"
    figure_dir = tmp_path / "figures"
    qwen_results = tmp_path / "results_qwen"
    mistral_results = tmp_path / "results_mistral"
    qwen14_results = tmp_path / "results_qwen14"

    subprocess.run(
        [
            "python",
            "/workspace/project/scripts/unify_live_full_r2_make_reports.py",
            "--manifest-root",
            str(manifest_root),
            "--qwen-root",
            str(qwen_root),
            "--mistral-root",
            str(mistral_root),
            "--qwen14-root",
            str(qwen14_root),
            "--qwen-results",
            str(qwen_results),
            "--mistral-results",
            str(mistral_results),
            "--qwen14-results",
            str(qwen14_results),
            "--report-dir",
            str(report_dir),
            "--table-dir",
            str(table_dir),
            "--figure-dir",
            str(figure_dir),
        ],
        check=True,
    )

    transfer = pd.read_csv(table_dir / "summary.csv")
    assert not transfer.empty
    bundle_transfer = pd.read_csv(qwen_results / "transfer.csv")
    assert {"math_to_format", "format_to_math", "pooled_to_math", "pooled_to_format"} <= set(bundle_transfer["direction"])

    for path in [
        report_dir / "unify_live_full_r2_integrity_report.md",
        report_dir / "unify_live_full_r2_qwen_report.md",
        report_dir / "unify_live_full_r2_mistral_report.md",
        report_dir / "unify_live_full_r2_qwen14b_collection_report.md",
        report_dir / "unify_live_full_r2_qwen14b_report.md",
        report_dir / "unify_live_full_r2_synthesis.md",
        report_dir / "unify_live_full_r2_failure_notes.md",
        report_dir / "unify_live_full_r2_summary_memo.md",
    ]:
        assert path.exists()

    qwen_split_manifest = json.loads((qwen_results / "policy_split_manifest.json").read_text(encoding="utf-8"))
    assert len(qwen_split_manifest) == 3
