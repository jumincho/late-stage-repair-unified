from __future__ import annotations
import os

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from dart_research.unify_live_full_r2 import PHASE_SPECS

DART_REPO_ROOT = os.environ.get("DART_REPO_ROOT", "/workspace/project")


DEFAULT_RUN_ROOT = Path(f"{DART_REPO_ROOT}/results/unify_live_full_r2_qwen14b/qwen14b_attempt2_20260326b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    parser.add_argument("--gpu-util-threshold", type=float, default=80.0)
    parser.add_argument("--output-json", default="")
    return parser.parse_args()


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _phase_root(run_root: Path, phase: dict[str, Any]) -> Path:
    return run_root / phase["base_dir"]


def _phase_dirs(run_root: Path, phase: dict[str, Any]) -> list[Path]:
    phase_root = _phase_root(run_root, phase)
    if not phase_root.exists():
        return []
    return sorted(p for p in phase_root.glob(f"{phase['glob']}") if p.is_dir())


def _phase_snapshot(run_root: Path, phase: dict[str, Any]) -> dict[str, Any]:
    shard_dirs = _phase_dirs(run_root, phase)
    completed = 0
    row_count = 0
    for shard_dir in shard_dirs:
        rows_path = shard_dir / "per_example.jsonl"
        if rows_path.exists():
            row_count += _count_jsonl(rows_path)
        if (shard_dir / "completed.txt").exists():
            completed += 1
    expected = int(phase["expected_rows"])
    return {
        "phase_name": phase["phase_name"],
        "module": phase["module"],
        "surface_name": phase["surface_name"],
        "expected_rows": expected,
        "actual_rows": row_count,
        "complete_shards": completed,
        "shard_count": len(shard_dirs),
        "progress": 0.0 if expected == 0 else round(row_count / expected * 100.0, 1),
        "paper_safe": int(row_count >= expected and completed > 0),
    }


def _gpu_snapshot() -> list[dict[str, Any]]:
    cmd = [
        "nvidia-smi",
        "--query-gpu=index,name,memory.used,memory.total,utilization.gpu,power.draw,power.limit",
        "--format=csv,noheader,nounits",
    ]
    try:
        raw = subprocess.check_output(cmd, text=True)
    except Exception:
        return []
    rows = []
    for line in raw.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 7:
            continue
        try:
            rows.append(
                {
                    "gpu": int(parts[0]),
                    "name": parts[1],
                    "memory_used_mb": int(float(parts[2])),
                    "memory_total_mb": int(float(parts[3])),
                    "gpu_util": int(float(parts[4])),
                    "power_draw_w": float(parts[5]),
                    "power_limit_w": float(parts[6]),
                }
            )
        except ValueError:
            continue
    return rows


def _current_phase(phases: list[dict[str, Any]]) -> str:
    for phase in phases:
        if phase["actual_rows"] < phase["expected_rows"]:
            return f"{phase['phase_name']} ({phase['actual_rows']}/{phase['expected_rows']})"
    return "complete"


def main() -> None:
    args = parse_args()
    run_root = Path(args.run_root)
    phase_rows = [_phase_snapshot(run_root, phase) for phase in PHASE_SPECS]
    gpus = _gpu_snapshot()
    current_phase = _current_phase(phase_rows)
    threshold = float(args.gpu_util_threshold)
    hot_gpus = sum(1 for gpu in gpus if gpu.get("gpu_util", 0) >= threshold)
    if gpus:
        avg_util = sum(gpu["gpu_util"] for gpu in gpus) / len(gpus)
        avg_mem = sum(gpu["memory_used_mb"] for gpu in gpus) / len(gpus)
    else:
        avg_util = 0.0
        avg_mem = 0.0

    lines = [
        f"run_root: {run_root}",
        f"current_phase: {current_phase}",
        f"gpu_util_hot_count: {hot_gpus}/{len(gpus)}",
        f"gpu_util_mean: {avg_util:.1f}%",
        f"gpu_memory_mean: {avg_mem:.0f} MB",
        "",
        "phase_snapshot:",
    ]
    for row in phase_rows:
        lines.append(
            f"- {row['phase_name']}: {row['actual_rows']}/{row['expected_rows']} rows, "
            f"{row['complete_shards']} completed shards, {row['shard_count']} shard dirs, "
            f"{row['progress']:.1f}%"
        )
    lines.append("")
    lines.append("gpu_snapshot:")
    if gpus:
        for gpu in gpus:
            lines.append(
                f"- gpu{gpu['gpu']}: util {gpu['gpu_util']}%, mem {gpu['memory_used_mb']}/{gpu['memory_total_mb']} MB, "
                f"pwr {gpu['power_draw_w']:.0f}/{gpu['power_limit_w']:.0f} W"
            )
    else:
        lines.append("- nvidia-smi query failed")

    print("\n".join(lines))

    if args.output_json:
        payload = {
            "run_root": str(run_root),
            "current_phase": current_phase,
            "gpu_snapshot": gpus,
            "phase_snapshot": phase_rows,
        }
        Path(args.output_json).write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()