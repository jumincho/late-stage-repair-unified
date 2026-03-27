from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from dart_research.cass_r4.runner import CASSR4Runner
from dart_research.datasets.loaders import load_examples
from dart_research.run_experiment import build_client
from dart_research.utils.config import load_yaml
from dart_research.utils.io import append_jsonl, ensure_dir, read_json, write_json, write_text
from dart_research.vchase.prm import ProcessRewardModelScorer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", choices=["hf_local", "vllm"], default="hf_local")
    parser.add_argument("--method-pack", choices=["full", "model_light"], default="full")
    parser.add_argument("--dataset")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--manifest")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--max-output-tokens", type=int, default=180)
    parser.add_argument("--local-quantization", choices=["none", "4bit", "8bit"], default="none")
    parser.add_argument("--local-dtype", default="float16")
    parser.add_argument("--local-device-map", default="auto")
    parser.add_argument("--local-max-model-len", type=int, default=4096)
    parser.add_argument("--local-max-memory", default=None)
    parser.add_argument("--local-trust-remote-code", action="store_true")
    parser.add_argument("--vllm-tensor-parallel-size", type=int, default=1)
    parser.add_argument("--hf-revision", default=None)
    parser.add_argument("--cache-namespace", default="")
    parser.add_argument("--disable-prm", action="store_true")
    parser.add_argument("--prm-model-name", default="Qwen/Qwen2.5-Math-PRM-7B")
    parser.add_argument("--teacher-seed")
    parser.add_argument("--problem-only", action="store_true")
    parser.add_argument("--retrieval-mode", choices=["global", "cluster_first"], default="cluster_first")
    parser.add_argument("--frozen-drafts", default=None)
    parser.add_argument("--save-drafts", default=None)
    return parser.parse_args()


def _load_examples(repo_root: Path, args: argparse.Namespace):
    cfg = repo_root / "configs" / "datasets.yaml"
    if args.manifest:
        manifest = read_json(Path(args.manifest))
        dataset = manifest["dataset"]
        entries = manifest["entries"]
        index = {example.question_id: example for example in load_examples(cfg, dataset)}
        selected = []
        for entry in entries:
            example = index[entry["question_id"]]
            for key, value in entry.items():
                if key != "question_id":
                    example.metadata[f"manifest_{key}"] = value
            example.metadata["surface"] = entry.get("surface", "")
            example.metadata["manifest_cluster"] = entry.get("cluster", "")
            example.metadata["sequence_index"] = int(entry.get("sequence_index", -1))
            selected.append(example)
        return dataset, selected
    if not args.dataset:
        raise ValueError("--dataset is required when --manifest is not provided")
    return args.dataset, load_examples(cfg, args.dataset, limit=args.limit, offset=args.offset)


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = ensure_dir(Path(args.output_dir))
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
    prm_scorer = None
    if not args.disable_prm:
        prm_scorer = ProcessRewardModelScorer(
            cache_dir=repo_root / "results" / "cache",
            model_name=args.prm_model_name,
            dtype=args.local_dtype,
            device_map=args.local_device_map,
            trust_remote_code=args.local_trust_remote_code or True,
            revision=args.hf_revision,
        )
    runner = CASSR4Runner(
        repo_root=repo_root,
        client=client,
        model_name=args.model_name,
        prm_scorer=prm_scorer,
        max_output_tokens=args.max_output_tokens,
        problem_only=args.problem_only,
        teacher_seed_path=Path(args.teacher_seed) if args.teacher_seed else None,
        retrieval_mode=args.retrieval_mode,
        frozen_drafts_path=Path(args.frozen_drafts) if args.frozen_drafts else None,
        save_drafts_path=Path(args.save_drafts) if args.save_drafts else None,
    )
    dataset, examples = _load_examples(repo_root, args)
    per_example = output_dir / "per_example.jsonl"
    if per_example.exists():
        per_example.unlink()
    for example in examples:
        if args.method_pack == "model_light":
            record = runner.collect_record_model_light(example)
        else:
            record = runner.collect_record(example)
        append_jsonl(per_example, record.to_dict())
    frame = pd.read_json(per_example, lines=True)
    write_json(
        output_dir / "manifest.json",
        {
            "created_at": datetime.now(UTC).isoformat(),
            "dataset": dataset,
            "limit": len(examples),
            "offset": args.offset,
            "model_name": args.model_name,
            "backend": args.client,
            "disable_prm": args.disable_prm,
            "problem_only": args.problem_only,
            "teacher_seed": args.teacher_seed or "",
            "retrieval_mode": args.retrieval_mode,
            "source_manifest": args.manifest or "",
            "frozen_drafts": args.frozen_drafts or "",
            "save_drafts": args.save_drafts or "",
            "method_pack": args.method_pack,
            "cache_namespace": args.cache_namespace,
        },
    )
    write_json(output_dir / f"{dataset}_sample_ids.json", [example.question_id for example in examples])
    write_text(
        output_dir / "completed.txt",
        (
            f"CASS-R4 records: {len(frame)}\n"
            f"Dataset: {dataset}\n"
            f"Model: {args.model_name}\n"
            f"Problem-only: {int(args.problem_only)}\n"
            f"Retrieval mode: {args.retrieval_mode}\n"
            f"Teacher seed: {args.teacher_seed or 'none'}\n"
            f"Frozen drafts: {args.frozen_drafts or 'none'}\n"
            f"Method pack: {args.method_pack}\n"
            f"Results: {per_example}\n"
        ),
    )


if __name__ == "__main__":
    main()
