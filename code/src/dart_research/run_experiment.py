"""Generic experiment harness used by the smoke / regression tests.

This is *not* the entry point for the final unify_live_full r2 pipeline —
the collectors under `code/scripts/` are. This module is the older generic
harness that runs the methods in `methods/pipelines.py` (`direct_cot`,
`self_consistency_5`, `self_refine_1`, `mc_select_only`, `dart_self`,
`dart_adv`, `dart_human_options`) over the datasets listed in
`configs/datasets.yaml` and writes a per-example JSONL plus the rolled-up
tables.

`build_client` is the only function the per-domain collectors import from
this module — it is how every script in `code/scripts/` chooses between
`mock`, `openai`, `hf_local`, and `vllm` backends. The rest of the module
backs `main()` for `python -m dart_research.run_experiment`.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dart_research.analysis.reporting import write_tables
from dart_research.clients.hf_local import HFTransformersClient
from dart_research.clients.mock import MockClient
from dart_research.clients.openai_responses import OpenAIResponsesClient
from dart_research.clients.vllm_local import LocalVLLMClient
from dart_research.datasets.loaders import BenchmarkExample, load_examples
from dart_research.evaluation.metrics import is_correct
from dart_research.methods.pipelines import MethodRunner, PromptBank
from dart_research.utils.config import load_yaml
from dart_research.utils.io import append_jsonl, ensure_dir, write_json, write_text


DEFAULT_METHODS = [
    "direct_cot",
    "self_consistency_5",
    "self_refine_1",
    "mc_select_only",
    "dart_self",
    "dart_adv",
]


def build_client(client_name: str, repo_root: Path, models_cfg: dict[str, Any], backend_overrides: dict[str, Any] | None = None):
    cache_dir = repo_root / models_cfg["cache_dir"]
    backend_overrides = backend_overrides or {}
    if client_name == "mock":
        return MockClient(cache_dir)
    if client_name == "openai":
        return OpenAIResponsesClient(cache_dir=cache_dir, pricing=models_cfg["pricing"])
    if client_name == "hf_local":
        return HFTransformersClient(cache_dir=cache_dir, backend_config=backend_overrides)
    if client_name == "vllm":
        return LocalVLLMClient(cache_dir=cache_dir, backend_config=backend_overrides)
    raise ValueError(f"Unknown client: {client_name}")


def apply_model_overrides(
    models_cfg: dict[str, Any],
    *,
    client_name: str,
    model_name: str | None,
    primary_model_name: str | None,
    cheap_model_name: str | None,
    validator_model_name: str | None,
    primary_max_output_tokens: int | None,
    cheap_max_output_tokens: int | None,
    validator_max_output_tokens: int | None,
) -> dict[str, Any]:
    updated = json.loads(json.dumps(models_cfg))
    shared_name = model_name
    for slot, override in {
        "primary": primary_model_name or shared_name,
        "cheap": cheap_model_name or shared_name,
        "validator": validator_model_name or shared_name,
    }.items():
        if override:
            updated["models"][slot]["name"] = override
        if client_name in {"hf_local", "vllm"}:
            updated["models"][slot]["provider"] = client_name
            updated["models"][slot]["temperature"] = updated["models"][slot].get("temperature", 0.0)
    for slot, override in {
        "primary": primary_max_output_tokens,
        "cheap": cheap_max_output_tokens,
        "validator": validator_max_output_tokens,
    }.items():
        if override is not None:
            updated["models"][slot]["max_output_tokens"] = int(override)
    return updated


def create_run_dir(base_dir: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    run_dir = ensure_dir(base_dir / timestamp)
    latest = base_dir / "latest"
    if latest.is_symlink() or latest.exists():
        if latest.is_dir() and not latest.is_symlink():
            latest.rmdir()
        else:
            latest.unlink()
    latest.symlink_to(run_dir.name)
    return run_dir


def eligible_methods(example: BenchmarkExample, method_names: list[str] | None = None) -> list[str]:
    if method_names is not None:
        methods = list(method_names)
        if "direct_cot" in methods:
            methods = ["direct_cot"] + [method for method in methods if method != "direct_cot"]
        return methods
    methods = list(DEFAULT_METHODS)
    if example.options:
        methods.append("dart_human_options")
    return methods


def run_experiment(
    *,
    repo_root: Path,
    run_dir: Path,
    datasets: list[str],
    client_name: str,
    limit: int,
    split_override: str | None,
    offset: int,
    methods_by_dataset: dict[str, list[str]] | None = None,
    model_name: str | None = None,
    primary_model_name: str | None = None,
    cheap_model_name: str | None = None,
    validator_model_name: str | None = None,
    primary_max_output_tokens: int | None = None,
    cheap_max_output_tokens: int | None = None,
    validator_max_output_tokens: int | None = None,
    backend_overrides: dict[str, Any] | None = None,
) -> Path:
    models_cfg = load_yaml(repo_root / "configs/models.yaml")
    models_cfg = apply_model_overrides(
        models_cfg,
        client_name=client_name,
        model_name=model_name,
        primary_model_name=primary_model_name,
        cheap_model_name=cheap_model_name,
        validator_model_name=validator_model_name,
        primary_max_output_tokens=primary_max_output_tokens,
        cheap_max_output_tokens=cheap_max_output_tokens,
        validator_max_output_tokens=validator_max_output_tokens,
    )
    methods_cfg = load_yaml(repo_root / "configs/methods.yaml")
    prompt_bank = PromptBank(repo_root)
    client = build_client(client_name, repo_root, models_cfg, backend_overrides=backend_overrides)
    runner = MethodRunner(client, prompt_bank, models_cfg, methods_cfg, artifact_dir=run_dir / "artifacts")
    results_path = run_dir / "per_example.jsonl"
    if results_path.exists():
        results_path.unlink()

    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "datasets": datasets,
        "client": client_name,
        "limit": limit,
        "offset": offset,
        "split_override": split_override,
        "methods_by_dataset": methods_by_dataset or {dataset: list(DEFAULT_METHODS) for dataset in datasets},
        "models": models_cfg["models"],
        "backend_overrides": backend_overrides or {},
    }
    write_json(run_dir / "manifest.json", manifest)

    for dataset_name in datasets:
        examples = load_examples(
            repo_root / "configs/datasets.yaml",
            dataset_name,
            split_override=split_override,
            limit=limit,
            offset=offset,
        )
        write_json(run_dir / f"{dataset_name}_sample_ids.json", [example.question_id for example in examples])
        direct_map: dict[str, int] = {}
        dataset_methods = methods_by_dataset.get(dataset_name) if methods_by_dataset else None
        for example in examples:
            for method_name in eligible_methods(example, dataset_methods):
                result = runner.run_method(method_name, example)
                correct = int(is_correct(result.final_normalized, example.gold_normalized))
                if method_name == "direct_cot":
                    direct_map[example.question_id] = correct
                record = {
                    "dataset": example.dataset,
                    "question_id": example.question_id,
                    "method": method_name,
                    "client": client_name,
                    "primary_model": models_cfg["models"]["primary"]["name"],
                    "cheap_model": models_cfg["models"]["cheap"]["name"],
                    "validator_model": models_cfg["models"]["validator"]["name"],
                    "question": example.question,
                    "gold_answer": example.gold_answer,
                    "gold_normalized": example.gold_normalized,
                    "prediction": result.final_answer,
                    "prediction_normalized": result.final_normalized,
                    "correct": correct,
                    "direct_correct": direct_map.get(example.question_id, correct),
                    "task_type": example.task_type,
                    "candidate_coverage": result.candidate_coverage,
                    "malformed": result.malformed,
                    "duplicates": result.duplicates,
                    "trivial": result.trivial,
                    "kept_options": result.kept_options,
                    "latency_s": result.latency_s,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "cost_usd": result.cost_usd,
                    "candidate_set": result.candidate_set,
                    "stage_records": result.stage_records,
                    "metadata": example.metadata,
                }
                append_jsonl(results_path, record)

    return results_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", choices=["mock", "openai", "hf_local", "vllm"], default="mock")
    parser.add_argument("--datasets", nargs="+", default=["gsm8k", "strategyqa", "arc_challenge"])
    parser.add_argument("--methods", nargs="*", default=None)
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--split-override", default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--primary-model-name", default=None)
    parser.add_argument("--cheap-model-name", default=None)
    parser.add_argument("--validator-model-name", default=None)
    parser.add_argument("--primary-max-output-tokens", type=int, default=None)
    parser.add_argument("--cheap-max-output-tokens", type=int, default=None)
    parser.add_argument("--validator-max-output-tokens", type=int, default=None)
    parser.add_argument("--local-quantization", choices=["none", "4bit", "8bit"], default="none")
    parser.add_argument("--local-dtype", default="float16")
    parser.add_argument("--local-device-map", default="auto")
    parser.add_argument("--local-max-model-len", type=int, default=4096)
    parser.add_argument("--local-max-memory", default=None)
    parser.add_argument("--local-top-p", type=float, default=0.9)
    parser.add_argument("--local-trust-remote-code", action="store_true")
    parser.add_argument("--vllm-tensor-parallel-size", type=int, default=1)
    parser.add_argument("--hf-revision", default=None)
    return parser.parse_args()


def main(base_subdir: str) -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    results_base = repo_root / "results" / base_subdir
    run_dir = Path(args.output_dir) if args.output_dir else create_run_dir(results_base)
    results_path = run_experiment(
        repo_root=repo_root,
        run_dir=run_dir,
        datasets=args.datasets,
        client_name=args.client,
        limit=args.limit,
        split_override=args.split_override,
        offset=args.offset,
        methods_by_dataset={dataset: args.methods for dataset in args.datasets} if args.methods else None,
        model_name=args.model_name,
        primary_model_name=args.primary_model_name,
        cheap_model_name=args.cheap_model_name,
        validator_model_name=args.validator_model_name,
        primary_max_output_tokens=args.primary_max_output_tokens,
        cheap_max_output_tokens=args.cheap_max_output_tokens,
        validator_max_output_tokens=args.validator_max_output_tokens,
        backend_overrides={
            "quantization": args.local_quantization,
            "dtype": args.local_dtype,
            "device_map": args.local_device_map,
            "max_model_len": args.local_max_model_len,
            "max_memory": args.local_max_memory,
            "top_p": args.local_top_p,
            "trust_remote_code": args.local_trust_remote_code,
            "tensor_parallel_size": args.vllm_tensor_parallel_size,
            "revision": args.hf_revision,
        },
    )
    import pandas as pd

    frame = pd.read_json(results_path, lines=True)
    csv_path, md_path = write_tables(frame, run_dir)
    write_text(run_dir / "completed.txt", f"Results: {results_path}\nTables: {csv_path}\nMarkdown: {md_path}\n")


if __name__ == "__main__":
    main("smoke")
