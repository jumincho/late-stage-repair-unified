"""Step 1 of the unified live full r2 pipeline: prepare the input bundle.

This script does the upstream work of the final round (`r2` = round 2 of the
unification effort): it pulls together the existing math and format manifests,
reshards them into per-GPU work units, and writes a shared "feature bundle"
that downstream collectors and the final report builder all consume.

Inputs (all overridable via flags, with `DART_REPO_ROOT` defaults preserved
for the closure reports):

- Two math manifests — `cluster_main` (the cluster-hard slice) and
  `generic_main` (the generic-hard slice).
- Two format manifests — screened `ifeval` and full `ifbench`.

Outputs:

- `--output-dir` with sharded manifest files and the `split_seeds.json`.
- `--report-path` markdown audit summarising counts and any drift.

The list of split seeds (`R2_SPLIT_SEEDS`) is the seed-of-seeds for the final
paired-bootstrap evaluation; changing it changes the stable triplet splits
used by `evaluate_model_bank`.
"""

from __future__ import annotations
import os

import argparse
from pathlib import Path

from dart_research.unify_live_full_r2 import R2_SPLIT_SEEDS, prepare_feature_bundle

DART_REPO_ROOT = os.environ.get("DART_REPO_ROOT", "/workspace/project")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=f"{DART_REPO_ROOT}/results/unify_live_full_r2_shared")
    parser.add_argument("--report-path", default=f"{DART_REPO_ROOT}/reports/unify_live_full_r2_feature_audit.md")
    parser.add_argument(
        "--math-cluster-source",
        default=f"{DART_REPO_ROOT}/data/cass_r3_manifests_20260315a/gsm8k_train_cluster_main_r3_full1515.json",
    )
    parser.add_argument(
        "--math-generic-source",
        default=f"{DART_REPO_ROOT}/data/cass_r3_manifests_20260315a/gsm8k_train_generic_main_r3_full.json",
    )
    parser.add_argument(
        "--ifeval-source",
        default=f"{DART_REPO_ROOT}/data/lace_full_format_manifests_20260324a/ifeval_screened_le150_381.json",
    )
    parser.add_argument(
        "--ifbench-source",
        default=f"{DART_REPO_ROOT}/data/lace_full_format_manifests_20260324a/ifbench_main_300.json",
    )
    parser.add_argument("--nshards", type=int, default=4)
    parser.add_argument("--split-seeds", nargs="+", type=int, default=R2_SPLIT_SEEDS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prepare_feature_bundle(
        output_dir=Path(args.output_dir),
        report_path=Path(args.report_path),
        math_cluster_source=Path(args.math_cluster_source),
        math_generic_source=Path(args.math_generic_source),
        ifeval_source=Path(args.ifeval_source),
        ifbench_source=Path(args.ifbench_source),
        nshards=int(args.nshards),
        split_seeds=[int(seed) for seed in args.split_seeds],
    )


if __name__ == "__main__":
    main()