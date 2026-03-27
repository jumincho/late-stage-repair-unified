from __future__ import annotations

import argparse
import json
from pathlib import Path

from dart_research.unify_live_full_r2 import MODEL_SPECS, audit_bank
from dart_research.utils.io import ensure_dir, write_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qwen-root", default="/workspace/project/results/unify_live_full_qwen/qwen7b_live_20260324a")
    parser.add_argument("--mistral-root", default="/workspace/project/results/unify_live_full_mistral/mistral7b_live_20260324a")
    parser.add_argument("--qwen14-root", default="/workspace/project/results/unify_live_full_qwen14b/qwen14b_live_20260324a")
    parser.add_argument("--qwen-out", default="/workspace/project/results/unify_live_full_r2_qwen")
    parser.add_argument("--mistral-out", default="/workspace/project/results/unify_live_full_r2_mistral")
    parser.add_argument("--qwen14-out", default="/workspace/project/results/unify_live_full_r2_qwen14b")
    return parser.parse_args()


def _write_audit(out_dir: Path, audit: dict) -> None:
    out_dir = ensure_dir(out_dir)
    audit["surface_summary"].to_csv(out_dir / "integrity_surface_summary.csv", index=False)
    audit["shard_summary"].to_csv(out_dir / "integrity_shard_summary.csv", index=False)
    issues_path = out_dir / "integrity_issues.csv"
    if not audit["issues"].empty:
        audit["issues"].to_csv(issues_path, index=False)
    elif issues_path.exists():
        issues_path.unlink()
    write_text(
        out_dir / "integrity_audit.json",
        json.dumps(
            {
                "model_name": audit["model_name"],
                "run_root": audit["run_root"],
                "paper_safe": audit["paper_safe"],
                "restart_logs": audit["restart_logs"],
            },
            indent=2,
        ),
    )


def main() -> None:
    args = parse_args()
    roots = {
        "qwen": Path(args.qwen_root),
        "mistral": Path(args.mistral_root),
        "qwen14b": Path(args.qwen14_root),
    }
    outs = {
        "qwen": Path(args.qwen_out),
        "mistral": Path(args.mistral_out),
        "qwen14b": Path(args.qwen14_out),
    }

    for spec in MODEL_SPECS:
        audit = audit_bank(roots[spec["key"]], model_name=spec["model_name"])
        _write_audit(outs[spec["key"]], audit)


if __name__ == "__main__":
    main()
