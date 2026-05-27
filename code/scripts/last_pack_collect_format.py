from __future__ import annotations
import os

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from dart_research.last_pack.formatting import (
    apply_instruction_patch,
    build_bridge_prompt,
    classify_bridge_failure,
    evaluate_instruction_response,
    load_instruction_dataset,
    summarize_instruction_feedback,
    validate_bridge_response,
)
from dart_research.last_pack.planning import load_task_from_dict
from dart_research.last_pack.prompts import LastPackPromptBank
from dart_research.parsing.tagged import extract_tagged_fields
from dart_research.run_experiment import build_client
from dart_research.utils.config import load_yaml
from dart_research.utils.io import append_jsonl, ensure_dir, read_json, write_json, write_text

DART_REPO_ROOT = os.environ.get("DART_REPO_ROOT", "/workspace/project")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", choices=["hf_local", "vllm"], default="hf_local")
    parser.add_argument("--surface", choices=["ifeval", "ifbench", "planning_bridge"], required=True)
    parser.add_argument("--ifeval-repo", default=f"{DART_REPO_ROOT}/external/google-research")
    parser.add_argument("--ifbench-repo", default=f"{DART_REPO_ROOT}/external/IFBench")
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--max-output-tokens", type=int, default=220)
    parser.add_argument("--local-quantization", choices=["none", "4bit", "8bit"], default="none")
    parser.add_argument("--local-dtype", default="float16")
    parser.add_argument("--local-device-map", default="auto")
    parser.add_argument("--local-max-model-len", type=int, default=4096)
    parser.add_argument("--local-max-memory", default=None)
    parser.add_argument("--local-trust-remote-code", action="store_true")
    parser.add_argument("--vllm-tensor-parallel-size", type=int, default=1)
    parser.add_argument("--hf-revision", default=None)
    parser.add_argument("--cache-namespace", default="")
    return parser.parse_args()


def _metrics_payload(response: dict) -> dict[str, object]:
    metrics = response["metrics"]
    return {
        "input_tokens": int(metrics.input_tokens),
        "output_tokens": int(metrics.output_tokens),
        "latency_s": float(metrics.latency_s),
        "raw_paths": [metrics.raw_path],
        "response_text": response["text"],
    }


def _generate(client, *, model_name: str, prompt_text: str, prompt_name: str, prompt_version: str, max_output_tokens: int, metadata: dict[str, object], system_text: str | None = None) -> dict[str, object]:
    response = client.generate_text(
        model_name=model_name,
        prompt_name=prompt_name,
        prompt_version=prompt_version,
        prompt_text=prompt_text,
        temperature=0.0,
        max_output_tokens=max_output_tokens,
        metadata=metadata,
        system_text=system_text,
    )
    payload = _metrics_payload(response)
    payload["fields"] = extract_tagged_fields(response["text"])
    return payload


def _instruction_eval(example: dict, response_text: str, *, surface: str, repo_path: Path) -> dict[str, object]:
    evaluation = evaluate_instruction_response(example, response_text, surface=surface, repo_path=repo_path)
    evaluation["success"] = int(evaluation["strict_follow_all"])
    return evaluation


def _bridge_eval(task: GridTask, response_text: str) -> dict[str, object]:
    evaluation = validate_bridge_response(task, response_text)
    evaluation["success"] = int(evaluation["both_valid"])
    evaluation["bridge_failure_type"] = classify_bridge_failure(evaluation)
    return evaluation


def _build_feedback(surface: str, example_or_task, evaluation: dict[str, object], *, repo_path: Path) -> str:
    if surface in {"ifeval", "ifbench"}:
        return summarize_instruction_feedback(example_or_task, evaluation)
    plan_eval = evaluation["plan_eval"]
    return (
        f"format_valid={evaluation['format_valid']}; semantic_valid={evaluation['semantic_valid']}; "
        f"bridge_failure_type={evaluation['bridge_failure_type']}; "
        f"plan_failure_type={plan_eval['failure_type']}; first_invalid_step={plan_eval['first_invalid_step']}"
    )


def _load_surface_examples(args: argparse.Namespace):
    if args.manifest:
        manifest = read_json(Path(args.manifest))
        entries = manifest["entries"][args.offset :]
        if args.limit is not None:
            entries = entries[: args.limit]
        if manifest["surface"] in {"planning_bridge", "planning_format_bridge"}:
            return "planning_bridge", [load_task_from_dict(item) for item in entries]
        return manifest["surface"], entries
    examples = load_instruction_dataset(args.surface, limit=None)
    examples = examples[args.offset :]
    if args.limit is not None:
        examples = examples[: args.limit]
    return args.surface, examples


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = ensure_dir(Path(args.output_dir))
    prompt_bank = LastPackPromptBank.load(repo_root)
    surface_name, examples = _load_surface_examples(args)
    ifeval_repo = Path(args.ifeval_repo)
    ifbench_repo = Path(args.ifbench_repo)

    models_cfg = load_yaml(repo_root / "configs" / "models.yaml")
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

    per_example_path = output_dir / "per_example.jsonl"
    if per_example_path.exists():
        per_example_path.unlink()

    for item in examples:
        if surface_name == "planning_bridge":
            task = item
            prompt_text = build_bridge_prompt(task)
            example_id = task.task_id
            difficulty = task.split
        else:
            task = None
            prompt_text = str(item["prompt"])
            example_id = str(item["key"])
            difficulty = "easy" if args.surface == "ifeval" else "hard"

        direct_payload = _generate(
            client,
            model_name=args.model_name,
            prompt_text=prompt_text,
            prompt_name=f"last_pack_{args.surface}_direct",
            prompt_version="v1",
            max_output_tokens=args.max_output_tokens,
            metadata={"branch": "last_pack", "module": "format", "surface": args.surface, "example_id": example_id, "method": "direct"},
            system_text="Follow the user's instructions exactly.",
        )
        eval_repo = ifeval_repo if args.surface == "ifeval" else ifbench_repo
        direct_eval = _bridge_eval(task, direct_payload["response_text"]) if task is not None else _instruction_eval(item, direct_payload["response_text"], surface=args.surface, repo_path=eval_repo)
        direct = {**direct_payload, **direct_eval, "intervened": 0}

        if direct["success"]:
            full_rewrite = dict(direct)
            format_patch = dict(direct)
        else:
            feedback = _build_feedback(args.surface, item if task is None else task, direct_eval, repo_path=eval_repo)
            rewrite_payload = _generate(
                client,
                model_name=args.model_name,
                prompt_text=prompt_bank.format_full_rewrite.render(prompt=prompt_text, response=str(direct["response_text"]), validator_feedback=feedback),
                prompt_name=f"last_pack_{args.surface}_full_rewrite",
                prompt_version=prompt_bank.format_full_rewrite.version,
                max_output_tokens=args.max_output_tokens,
                metadata={"branch": "last_pack", "module": "format", "surface": args.surface, "example_id": example_id, "method": "full_rewrite"},
                system_text="Return only the final corrected answer.",
            )
            rewrite_eval = _bridge_eval(task, rewrite_payload["response_text"]) if task is not None else _instruction_eval(item, rewrite_payload["response_text"], surface=args.surface, repo_path=eval_repo)
            full_rewrite = {**rewrite_payload, **rewrite_eval, "intervened": 1}

            if task is None:
                deterministic_text, patch_info = apply_instruction_patch(item, str(direct["response_text"]), direct_eval)
                deterministic_eval = _instruction_eval(item, deterministic_text, surface=args.surface, repo_path=eval_repo)
                if deterministic_eval["success"]:
                    format_patch = {
                        "response_text": deterministic_text,
                        "fields": {},
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "latency_s": 0.0,
                        "raw_paths": [],
                        **patch_info,
                        **deterministic_eval,
                        "intervened": 1,
                        "patch_mode": "deterministic",
                    }
                else:
                    patch_payload = _generate(
                        client,
                        model_name=args.model_name,
                        prompt_text=prompt_bank.format_only_patch.render(prompt=prompt_text, response=deterministic_text, validator_feedback=feedback),
                        prompt_name=f"last_pack_{args.surface}_format_patch",
                        prompt_version=prompt_bank.format_only_patch.version,
                        max_output_tokens=args.max_output_tokens,
                        metadata={"branch": "last_pack", "module": "format", "surface": args.surface, "example_id": example_id, "method": "format_patch"},
                        system_text="Return only the minimally patched final answer.",
                    )
                    patch_eval = _instruction_eval(item, patch_payload["response_text"], surface=args.surface, repo_path=eval_repo)
                    format_patch = {
                        **patch_payload,
                        **patch_eval,
                        **patch_info,
                        "intervened": 1,
                        "patch_mode": "llm_fallback",
                        "deterministic_patch_preview": deterministic_text,
                    }
            else:
                patch_payload = _generate(
                    client,
                    model_name=args.model_name,
                    prompt_text=prompt_bank.format_only_patch.render(prompt=prompt_text, response=str(direct["response_text"]), validator_feedback=feedback),
                    prompt_name=f"last_pack_{args.surface}_format_patch",
                    prompt_version=prompt_bank.format_only_patch.version,
                    max_output_tokens=args.max_output_tokens,
                    metadata={"branch": "last_pack", "module": "format", "surface": args.surface, "example_id": example_id, "method": "format_patch"},
                    system_text="Return only the minimally patched final answer.",
                )
                patch_eval = _bridge_eval(task, patch_payload["response_text"])
                format_patch = {**patch_payload, **patch_eval, "intervened": 1, "patch_mode": "llm_only"}

        solve_payload = _generate(
            client,
            model_name=args.model_name,
            prompt_text=prompt_bank.format_solve_first.render(prompt=prompt_text),
            prompt_name=f"last_pack_{args.surface}_solve_first",
            prompt_version=prompt_bank.format_solve_first.version,
            max_output_tokens=args.max_output_tokens,
            metadata={"branch": "last_pack", "module": "format", "surface": args.surface, "example_id": example_id, "method": "solve_first"},
            system_text="Return exactly the requested tags and nothing else.",
        )
        content = str(solve_payload["fields"].get("content", "")).strip() or str(solve_payload["response_text"])
        apply_payload = _generate(
            client,
            model_name=args.model_name,
            prompt_text=prompt_bank.format_apply_constraints.render(prompt=prompt_text, content=content),
            prompt_name=f"last_pack_{args.surface}_apply_constraints",
            prompt_version=prompt_bank.format_apply_constraints.version,
            max_output_tokens=args.max_output_tokens,
            metadata={"branch": "last_pack", "module": "format", "surface": args.surface, "example_id": example_id, "method": "solve_then_format"},
            system_text="Return only the final answer.",
        )
        solve_eval = _bridge_eval(task, apply_payload["response_text"]) if task is not None else _instruction_eval(item, apply_payload["response_text"], surface=args.surface, repo_path=eval_repo)
        solve_then_format = {
            **apply_payload,
            **solve_eval,
            "intervened": 1,
            "stage1_content": content,
            "stage1_latency_s": float(solve_payload["latency_s"]),
            "stage1_input_tokens": int(solve_payload["input_tokens"]),
            "stage1_output_tokens": int(solve_payload["output_tokens"]),
            "stage1_raw_paths": list(solve_payload["raw_paths"]),
            "latency_s": float(solve_payload["latency_s"]) + float(apply_payload["latency_s"]),
            "input_tokens": int(solve_payload["input_tokens"]) + int(apply_payload["input_tokens"]),
            "output_tokens": int(solve_payload["output_tokens"]) + int(apply_payload["output_tokens"]),
            "raw_paths": list(solve_payload["raw_paths"]) + list(apply_payload["raw_paths"]),
        }

        append_jsonl(
            per_example_path,
            {
                "surface": surface_name,
                "example_id": example_id,
                "difficulty": difficulty,
                "model_name": args.model_name,
                "prompt_versions": prompt_bank.version_bundle(),
                "prompt": prompt_text,
                "instruction_example": item if task is None else None,
                "bridge_task": task.to_dict() if task is not None else None,
                "direct_formatted": direct,
                "full_rewrite_on_failure": full_rewrite,
                "solve_then_format": solve_then_format,
                "format_only_patch": format_patch,
            },
        )

    frame = pd.read_json(per_example_path, lines=True)
    write_json(
        output_dir / "manifest.json",
        {
            "created_at": datetime.now(UTC).isoformat(),
            "surface": surface_name,
            "n": len(frame),
            "model_name": args.model_name,
            "backend": args.client,
            "source_manifest": args.manifest or "",
            "ifbench_repo": str(ifbench_repo),
            "ifeval_repo": str(ifeval_repo),
            "cache_namespace": args.cache_namespace,
        },
    )
    write_text(
        output_dir / "completed.txt",
        (
            f"LAST-PACK format records: {len(frame)}\n"
            f"Surface: {surface_name}\n"
            f"Model: {args.model_name}\n"
            f"Results: {per_example_path}\n"
        ),
    )


if __name__ == "__main__":
    main()