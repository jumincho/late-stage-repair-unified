from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import dart_research.unify_live_full_r2 as r2


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")


def _math_record(question_id: str) -> dict:
    return {
        "question_id": question_id,
        "draft": {"correctness": 0, "normalized_answer": "0"},
        "actions": [
            {"action_name": "RAW_PYTHON", "parse_ok": 1, "correctness": 1},
            {"action_name": "GRANITE_POSTPROCESS_ONLY_PATCH", "parse_ok": 1, "correctness": 1},
            {"action_name": "CASS_TARGET_POSTPROCESS_PATCH", "parse_ok": 1, "correctness": 1},
        ],
    }


def _format_record(example_id: str) -> dict:
    base = {"response_text": "x", "success": 1}
    return {
        "example_id": example_id,
        "direct_formatted": dict(base),
        "solve_then_format": dict(base),
        "full_rewrite_on_failure": dict(base),
    }


def _write_phase(root: Path, phase: dict, rows: list[dict], manifest_size: int | None = None) -> None:
    shard_dir = root / phase["base_dir"] / phase["glob"].replace("*of*", "01of01").replace("*", "")
    manifest_rows = manifest_size if manifest_size is not None else len(rows)
    _write_json(
        shard_dir / "manifest.json",
        {"entries": [{"id": idx} for idx in range(manifest_rows)]},
    )
    _write_jsonl(shard_dir / "per_example.jsonl", rows)
    (shard_dir / "completed.txt").write_text("ok", encoding="utf-8")


def test_unify_live_full_r2_prepare_freezes_action_map(tmp_path: Path) -> None:
    math_cluster = tmp_path / "math_cluster.json"
    math_generic = tmp_path / "math_generic.json"
    ifeval = tmp_path / "ifeval.json"
    ifbench = tmp_path / "ifbench.json"
    out_dir = tmp_path / "out"
    report_path = tmp_path / "feature_audit.md"

    payloads = [
        (math_cluster, "gsm8k_train", "hard_cluster_main_r2"),
        (math_generic, "gsm8k_train", "hard_generic_main_r2"),
        (ifeval, "ifeval", "ifeval_screened"),
        (ifbench, "ifbench", "ifbench"),
    ]
    for path, dataset, surface in payloads:
        _write_json(path, {"dataset": dataset, "surface": surface, "entries": [{"id": "a"}]})

    r2.prepare_feature_bundle(
        output_dir=out_dir,
        report_path=report_path,
        math_cluster_source=math_cluster,
        math_generic_source=math_generic,
        ifeval_source=ifeval,
        ifbench_source=ifbench,
        nshards=2,
        split_seeds=[13, 29, 47],
    )

    feature_map = json.loads((out_dir / "feature_map.json").read_text(encoding="utf-8"))
    split_seeds = json.loads((out_dir / "split_seeds.json").read_text(encoding="utf-8"))
    assert feature_map["abstract_action_space"] == ["NO_INTERVENTION", "LOCAL_REPAIR", "GLOBAL_REWRITE_OR_RESTART"]
    assert split_seeds["split_seeds"] == [13, 29, 47]
    assert report_path.exists()


def test_audit_bank_clean_and_duplicate_detection(tmp_path: Path, monkeypatch) -> None:
    phase_specs = [
        {
            "phase_name": "math_cluster_raw",
            "module": "math",
            "surface_name": "cluster-hard",
            "expected_rows": 2,
            "base_dir": "math_raw",
            "glob": "gsm8k_train_cluster_live_full__shard*of*",
            "id_key": "question_id",
            "required_actions": ["RAW_PYTHON", "CASS_TARGET_POSTPROCESS_PATCH"],
        },
        {
            "phase_name": "math_generic_raw",
            "module": "math",
            "surface_name": "generic-hard",
            "expected_rows": 1,
            "base_dir": "math_raw",
            "glob": "gsm8k_train_generic_live_full__shard*of*",
            "id_key": "question_id",
            "required_actions": ["RAW_PYTHON", "CASS_TARGET_POSTPROCESS_PATCH"],
        },
        {
            "phase_name": "math_cluster_replay",
            "module": "math",
            "surface_name": "cluster-hard",
            "expected_rows": 2,
            "base_dir": "math_replay",
            "glob": "gsm8k_train_cluster_live_full__shard*of*",
            "id_key": "question_id",
            "required_actions": ["RAW_PYTHON", "GRANITE_POSTPROCESS_ONLY_PATCH"],
        },
        {
            "phase_name": "math_generic_replay",
            "module": "math",
            "surface_name": "generic-hard",
            "expected_rows": 1,
            "base_dir": "math_replay",
            "glob": "gsm8k_train_generic_live_full__shard*of*",
            "id_key": "question_id",
            "required_actions": ["RAW_PYTHON", "GRANITE_POSTPROCESS_ONLY_PATCH"],
        },
        {
            "phase_name": "format_ifeval",
            "module": "format",
            "surface_name": "screened IFEval",
            "expected_rows": 2,
            "base_dir": "format",
            "glob": "ifeval_shard*of*",
            "id_key": "example_id",
            "required_actions": ["direct_formatted", "solve_then_format", "full_rewrite_on_failure"],
        },
        {
            "phase_name": "format_ifbench",
            "module": "format",
            "surface_name": "IFBench",
            "expected_rows": 1,
            "base_dir": "format",
            "glob": "ifbench_shard*of*",
            "id_key": "example_id",
            "required_actions": ["direct_formatted", "solve_then_format", "full_rewrite_on_failure"],
        },
    ]
    monkeypatch.setattr(r2, "PHASE_SPECS", phase_specs)

    root = tmp_path / "clean_root"
    _write_phase(root, phase_specs[0], [_math_record("c1"), _math_record("c2")])
    _write_phase(root, phase_specs[1], [_math_record("g1")])
    _write_phase(root, phase_specs[2], [_math_record("c1"), _math_record("c2")])
    _write_phase(root, phase_specs[3], [_math_record("g1")])
    _write_phase(root, phase_specs[4], [_format_record("i1"), _format_record("i2")])
    _write_phase(root, phase_specs[5], [_format_record("b1")])

    clean_audit = r2.audit_bank(root, model_name="qwen")
    assert clean_audit["paper_safe"] is True
    assert clean_audit["issues"].empty

    dup_root = tmp_path / "dup_root"
    _write_phase(dup_root, phase_specs[0], [_math_record("c1"), _math_record("c2")])
    _write_phase(dup_root, phase_specs[1], [_math_record("g1")])
    _write_phase(dup_root, phase_specs[2], [_math_record("c1"), _math_record("c2")])
    _write_phase(dup_root, phase_specs[3], [_math_record("g1")])
    _write_phase(dup_root, phase_specs[4], [_format_record("i1"), _format_record("i1")])
    _write_phase(dup_root, phase_specs[5], [_format_record("b1")])

    dup_audit = r2.audit_bank(dup_root, model_name="qwen")
    assert dup_audit["paper_safe"] is False
    assert not dup_audit["issues"].empty
    assert "duplicate example ids" in set(dup_audit["issues"]["issue"])
