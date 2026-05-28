"""Step 3 of the unified live full r2 pipeline: build the final reports.

Once the per-model live runs have finished and `unify_live_full_r2_integrity`
has been re-run cleanly, this script does the final synthesis. For each of
the three required models it:

- re-audits the bank (so the report references match the latest state),
- builds the unified `(math, format)` evaluation frames,
- fits pooled vs domain-specific simple policies,
- writes the per-model markdown reports under `reports/final/`,
- writes the cross-domain synthesis memo,
- writes summary tables (CSV in `tables/unify_live_full_r2/`) and figures
  (PNG in `figures/unify_live_full_r2/`) used by the writeup.

`qwen14b` is handled separately because its restart timeline is recorded in a
dedicated collection report; pass that JSON via `--qwen14-attempts-json` if
you want the timeline of GPU sharding attempts included in the report. All
path defaults route through `DART_REPO_ROOT`.
"""

from __future__ import annotations
import os

import argparse
import json
from pathlib import Path

from dart_research.unify_live_full_r2 import (
    MODEL_SPECS,
    _model_root_ready,
    audit_bank,
    evaluate_model_bank,
    write_bundle_outputs,
)
from dart_research.utils.io import read_json

DART_REPO_ROOT = os.environ.get("DART_REPO_ROOT", "/workspace/project")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-root", default=f"{DART_REPO_ROOT}/results/unify_live_full_r2_shared")
    parser.add_argument("--qwen-root", default=f"{DART_REPO_ROOT}/results/unify_live_full_qwen/qwen7b_live_20260324a")
    parser.add_argument("--mistral-root", default=f"{DART_REPO_ROOT}/results/unify_live_full_mistral/mistral7b_live_20260324a")
    parser.add_argument("--qwen14-root", default=f"{DART_REPO_ROOT}/results/unify_live_full_qwen14b/qwen14b_live_20260324a")
    parser.add_argument("--qwen-results", default=f"{DART_REPO_ROOT}/results/unify_live_full_r2_qwen")
    parser.add_argument("--mistral-results", default=f"{DART_REPO_ROOT}/results/unify_live_full_r2_mistral")
    parser.add_argument("--qwen14-results", default=f"{DART_REPO_ROOT}/results/unify_live_full_r2_qwen14b")
    parser.add_argument("--report-dir", default=f"{DART_REPO_ROOT}/reports")
    parser.add_argument("--table-dir", default=f"{DART_REPO_ROOT}/tables/unify_live_full_r2")
    parser.add_argument("--figure-dir", default=f"{DART_REPO_ROOT}/figures/unify_live_full_r2")
    parser.add_argument("--qwen14-attempts-json", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_root = Path(args.manifest_root)
    split_seeds = [int(seed) for seed in read_json(manifest_root / "split_seeds.json")["split_seeds"]]
    roots = {
        "qwen": Path(args.qwen_root),
        "mistral": Path(args.mistral_root),
        "qwen14b": Path(args.qwen14_root),
    }
    results_dirs = {
        "qwen": Path(args.qwen_results),
        "mistral": Path(args.mistral_results),
        "qwen14b": Path(args.qwen14_results),
    }

    audits = []
    model_results = []
    qwen14_audit = None
    qwen14_result = None

    for spec in MODEL_SPECS:
        audit = audit_bank(roots[spec["key"]], model_name=spec["model_name"])
        if spec["key"] == "qwen14b":
            qwen14_audit = audit
        else:
            audits.append(audit)
        if _model_root_ready(roots[spec["key"]]):
            result = evaluate_model_bank(
                run_root=roots[spec["key"]],
                model_name=spec["model_name"],
                split_seeds=split_seeds,
                results_dir=results_dirs[spec["key"]],
            )
            if spec["key"] == "qwen14b":
                qwen14_result = result
            else:
                model_results.append(result)

    qwen14_attempts = []
    if args.qwen14_attempts_json:
        qwen14_attempts = list(json.loads(Path(args.qwen14_attempts_json).read_text(encoding="utf-8")))

    write_bundle_outputs(
        audits=audits,
        model_results=model_results,
        qwen14_audit=qwen14_audit,
        qwen14_result=qwen14_result,
        report_dir=Path(args.report_dir),
        table_dir=Path(args.table_dir),
        figure_dir=Path(args.figure_dir),
        qwen14_attempts=qwen14_attempts,
    )


if __name__ == "__main__":
    main()