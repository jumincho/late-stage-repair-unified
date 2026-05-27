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