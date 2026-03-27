from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from dart_research.cass_bd import DIAGNOSIS_METHODS, build_partial_probe
from dart_research.cass_r2.runner import CASSR2Runner
from dart_research.datasets.loaders import BenchmarkExample
from dart_research.run_experiment import build_client
from dart_research.utils.config import load_yaml
from dart_research.utils.io import append_jsonl, ensure_dir, read_json, write_json, write_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dirs", nargs="+", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model-name", default="ibm-granite/granite-3.1-8b-instruct")
    parser.add_argument("--client", choices=["hf_local", "vllm"], default="hf_local")
    parser.add_argument("--local-quantization", choices=["none", "4bit", "8bit"], default="none")
    parser.add_argument("--local-dtype", default="float16")
    parser.add_argument("--local-device-map", default="auto")
    parser.add_argument("--local-max-model-len", type=int, default=4096)
    parser.add_argument("--local-max-memory", default=None)
    parser.add_argument("--local-trust-remote-code", action="store_true")
    parser.add_argument("--vllm-tensor-parallel-size", type=int, default=1)
    parser.add_argument("--hf-revision", default=None)
    parser.add_argument("--cache-namespace", default="")
    parser.add_argument("--max-output-tokens", type=int, default=180)
    parser.add_argument("--teacher-seed", default="/workspace/project/results/cass_api_diag/teacher_seed_gpt5mini_20260315_merged/teacher_seed.jsonl")
    return parser.parse_args()


def _load_index(input_dirs: list[str]) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for input_dir in input_dirs:
        path = Path(input_dir) / "per_example.jsonl"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            index[str(record["question_id"])] = record
    return index


def _example_from_record(record: dict) -> BenchmarkExample:
    return BenchmarkExample(
        dataset=str(record["dataset"]),
        question_id=str(record["question_id"]),
        question=str(record["question"]),
        gold_answer=str(record["gold_answer"]),
        gold_normalized=str(record["gold_normalized"]),
        task_type=str(record["task_type"]),
        metadata=dict(record.get("metadata", {})),
    )


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = ensure_dir(Path(args.output_dir))
    manifest = read_json(Path(args.manifest))
    entries = list(manifest["entries"])
    index = _load_index(args.input_dirs)

    models_cfg = load_yaml(repo_root / "configs/models.yaml")
    client = build_client(
        args.client,
        repo_root,
        models_cfg,
        backend_overrides={
            "quantization": args.local_quantization,
            "dtype": args.local_dtype,
            "device_map": args.local_device_map,
            "max_model_len": args.local_max_model_len,
            "max_memory": args.local_max_memory,
            "trust_remote_code": args.local_trust_remote_code,
            "revision": args.hf_revision,
            "tensor_parallel_size": args.vllm_tensor_parallel_size,
            "cache_namespace": args.cache_namespace,
        },
    )
    runner = CASSR2Runner(
        repo_root=repo_root,
        client=client,
        model_name=args.model_name,
        prm_scorer=None,
        max_output_tokens=args.max_output_tokens,
        problem_only=False,
        teacher_seed_path=Path(args.teacher_seed) if args.teacher_seed else None,
        retrieval_mode="cluster_first",
    )

    per_example_path = output_dir / "per_example.jsonl"
    if per_example_path.exists():
        per_example_path.unlink()

    for entry in entries:
        question_id = str(entry["question_id"])
        raw = json.loads(json.dumps(index[question_id]))
        example = _example_from_record(raw)
        draft = raw["draft"]
        draft_obj = SimpleNamespace(
            answer=str(draft["answer"]),
            scratch=str(draft["scratch"]),
            correctness=int(draft["correctness"]),
        )
        new_probes = []
        new_actions = []
        for method_name in DIAGNOSIS_METHODS:
            probe = build_partial_probe(raw, variant=method_name)
            action = runner._schema_action(example, draft_obj, probe, action_name=method_name)
            new_probes.append(probe.to_dict())
            new_actions.append(action.to_dict())
        raw["probes"] = list(raw.get("probes", [])) + new_probes
        raw["actions"] = list(raw.get("actions", [])) + new_actions
        raw.setdefault("metadata", {})
        raw["metadata"]["boundary_pack"] = "cass_bd"
        append_jsonl(per_example_path, raw)

    frame = pd.read_json(per_example_path, lines=True)
    write_json(
        output_dir / "manifest.json",
        {
            "dataset": manifest["dataset"],
            "surface": manifest["surface"],
            "limit": len(entries),
            "model_name": args.model_name,
            "backend": args.client,
            "source_manifest": args.manifest,
            "source_raw_dirs": args.input_dirs,
            "diagnosis_methods": DIAGNOSIS_METHODS,
            "cache_namespace": args.cache_namespace,
        },
    )
    write_json(output_dir / f"{manifest['dataset']}_sample_ids.json", [entry["question_id"] for entry in entries])
    write_text(
        output_dir / "completed.txt",
        (
            f"Granite diagnosis replay records: {len(frame)}\n"
            f"Dataset: {manifest['dataset']}\n"
            f"Surface: {manifest['surface']}\n"
            f"Model: {args.model_name}\n"
            f"Results: {per_example_path}\n"
        ),
    )


if __name__ == "__main__":
    main()
