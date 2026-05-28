"""Local vLLM client (optional, import-guarded).

Alternative to `hf_local` for runs where vLLM's tensor-parallel sharding is a
better fit (the 14B run originally tried this path before settling on a
hand-rolled 8-way HF shard). The vLLM import is guarded so missing the
dependency does not block the rest of the package from being usable.

`_render_messages` is re-used from `hf_local` so the chat template applied
here matches what the HF path produces on the same model.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Type

from pydantic import BaseModel

from dart_research.clients.base import GenerationEnvelope, GenerationMetrics, ModelClient
from dart_research.clients.hf_local import _render_messages
from dart_research.parsing.json_tools import extract_first_json
from dart_research.utils.cache import DiskCache

os.environ.setdefault("MKL_THREADING_LAYER", "GNU")

try:
    from vllm import LLM, SamplingParams
except ImportError:  # pragma: no cover - optional dependency guard
    LLM = None
    SamplingParams = None


class LocalVLLMClient(ModelClient):
    """Optional vLLM backend. Kept import-guarded so it does not block hf_local usage."""

    CACHE_VERSION = "vllm_local_v1"

    def __init__(self, cache_dir: Path, backend_config: dict[str, Any] | None = None):
        if LLM is None or SamplingParams is None:
            raise RuntimeError("vllm is not installed. Use hf_local or install vllm separately.")
        self.cache = DiskCache(cache_dir / "vllm")
        self.backend_config = backend_config or {}
        self._loaded: dict[str, tuple[Any, dict[str, Any]]] = {}

    def _cache_namespace(self) -> str:
        return str(self.backend_config.get("cache_namespace", "")).strip()

    def _load_model(self, model_name: str) -> tuple[Any, dict[str, Any]]:
        if model_name in self._loaded:
            return self._loaded[model_name]
        metadata = {
            "backend": "vllm",
            "model_name": model_name,
            "revision": self.backend_config.get("revision", ""),
            "tensor_parallel_size": int(self.backend_config.get("tensor_parallel_size", 1)),
            "max_model_len": int(self.backend_config.get("max_model_len", 4096)),
            "dtype": str(self.backend_config.get("dtype", "float16")),
            "quantization": str(self.backend_config.get("quantization", "none")),
        }
        llm = LLM(
            model=model_name,
            revision=self.backend_config.get("revision"),
            tensor_parallel_size=metadata["tensor_parallel_size"],
            max_model_len=metadata["max_model_len"],
            dtype=metadata["dtype"],
            quantization=None if metadata["quantization"] == "none" else metadata["quantization"],
            trust_remote_code=bool(self.backend_config.get("trust_remote_code", True)),
            download_dir=self.backend_config.get("download_dir"),
        )
        self._loaded[model_name] = (llm, metadata)
        return self._loaded[model_name]

    def generate_json(
        self,
        *,
        model_name: str,
        prompt_name: str,
        prompt_version: str,
        prompt_text: str,
        schema: Type[BaseModel],
        temperature: float,
        max_output_tokens: int,
        metadata: dict[str, Any],
    ) -> GenerationEnvelope:
        llm, backend_meta = self._load_model(model_name)
        rendered_prompt = (
            "System: Return exactly one valid JSON object. Do not output markdown, code fences, analysis, or <think> tags. "
            f"Do not show hidden reasoning. Keep fields concise. Target schema: {schema.__name__}.\n\n"
            f"User: {prompt_text}\n\nAssistant:"
        )
        request = {
            "cache_version": self.CACHE_VERSION,
            "cache_namespace": self._cache_namespace(),
            "backend": "vllm",
            "model_name": model_name,
            "prompt_name": prompt_name,
            "prompt_version": prompt_version,
            "prompt_text": rendered_prompt,
            "schema": schema.__name__,
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "backend_config": backend_meta,
        }
        cached = self.cache.get(request)
        if cached is not None:
            raw_response = cached["raw_response"]
            raw_path = str(self.cache.path_for(request))
            cache_hit = True
            latency_s = float(cached["metrics"]["latency_s"])
        else:
            params = SamplingParams(
                temperature=max(float(temperature), 0.0),
                top_p=float(self.backend_config.get("top_p", 0.9)),
                max_tokens=int(max_output_tokens),
            )
            start = time.perf_counter()
            outputs = llm.generate([rendered_prompt], params)
            latency_s = time.perf_counter() - start
            first = outputs[0]
            text = first.outputs[0].text if first.outputs else ""
            raw_response = {
                "backend": "vllm",
                "model": model_name,
                "backend_config": backend_meta,
                "output_text": text,
                "usage": {
                    "input_tokens": len(first.prompt_token_ids),
                    "output_tokens": len(first.outputs[0].token_ids) if first.outputs else 0,
                },
            }
            raw_path = str(
                self.cache.set(
                    request,
                    {
                        "raw_response": raw_response,
                        "metrics": {"latency_s": latency_s},
                        "metadata": metadata,
                    },
                )
            )
            cache_hit = False

        payload = extract_first_json(str(raw_response.get("output_text", "")))
        parsed = schema.model_validate(payload)
        usage = raw_response.get("usage", {})
        metrics = GenerationMetrics(
            latency_s=latency_s,
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            cost_usd=0.0,
            cache_hit=cache_hit,
            raw_path=raw_path,
        )
        return GenerationEnvelope(parsed=parsed, raw_response=raw_response, metrics=metrics, prompt_version=prompt_version)

    def generate_text(
        self,
        *,
        model_name: str,
        prompt_name: str,
        prompt_version: str,
        prompt_text: str,
        temperature: float,
        max_output_tokens: int,
        metadata: dict[str, Any],
        system_text: str | None = None,
    ) -> dict[str, Any]:
        llm, backend_meta = self._load_model(model_name)
        rendered_prompt = _render_messages(
            tokenizer=llm.get_tokenizer(),
            system_text=system_text or "Return only the requested tagged fields. Do not use markdown or hidden reasoning.",
            user_text=prompt_text,
        )
        request = {
            "cache_version": f"{self.CACHE_VERSION}_text_v1",
            "cache_namespace": self._cache_namespace(),
            "backend": "vllm",
            "model_name": model_name,
            "prompt_name": prompt_name,
            "prompt_version": prompt_version,
            "prompt_text": rendered_prompt,
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "backend_config": backend_meta,
        }
        cached = self.cache.get(request)
        if cached is not None:
            raw_response = cached["raw_response"]
            raw_path = str(self.cache.path_for(request))
            cache_hit = True
            latency_s = float(cached["metrics"]["latency_s"])
        else:
            params = SamplingParams(
                temperature=max(float(temperature), 0.0),
                top_p=float(self.backend_config.get("top_p", 0.9)),
                max_tokens=int(max_output_tokens),
            )
            start = time.perf_counter()
            outputs = llm.generate([rendered_prompt], params)
            latency_s = time.perf_counter() - start
            first = outputs[0]
            text = first.outputs[0].text if first.outputs else ""
            raw_response = {
                "backend": "vllm",
                "model": model_name,
                "backend_config": backend_meta,
                "output_text": text,
                "usage": {
                    "input_tokens": len(first.prompt_token_ids),
                    "output_tokens": len(first.outputs[0].token_ids) if first.outputs else 0,
                },
            }
            raw_path = str(
                self.cache.set(
                    request,
                    {
                        "raw_response": raw_response,
                        "metrics": {"latency_s": latency_s},
                        "metadata": metadata,
                    },
                )
            )
            cache_hit = False
        usage = raw_response.get("usage", {})
        return {
            "text": str(raw_response.get("output_text", "")),
            "raw_response": raw_response,
            "metrics": GenerationMetrics(
                latency_s=latency_s,
                input_tokens=int(usage.get("input_tokens", 0)),
                output_tokens=int(usage.get("output_tokens", 0)),
                cost_usd=0.0,
                cache_hit=cache_hit,
                raw_path=raw_path,
            ),
            "prompt_version": prompt_version,
        }

    def generate_text_batch(
        self,
        *,
        model_name: str,
        prompt_texts: list[str],
        temperature: float,
        max_output_tokens: int,
        metadata_list: list[dict[str, Any]],
        prompt_names: list[str] | None = None,
        prompt_versions: list[str] | None = None,
        system_texts: list[str] | None = None,
        prompt_name: str | None = None,
        prompt_version: str | None = None,
        system_text: str | None = None,
    ) -> list[dict[str, Any]]:
        if len(prompt_texts) != len(metadata_list):
            raise ValueError("prompt_texts and metadata_list must have the same length.")
        if prompt_names is not None and len(prompt_names) != len(prompt_texts):
            raise ValueError("prompt_names must match prompt_texts length.")
        if prompt_versions is not None and len(prompt_versions) != len(prompt_texts):
            raise ValueError("prompt_versions must match prompt_texts length.")
        if system_texts is not None and len(system_texts) != len(prompt_texts):
            raise ValueError("system_texts must match prompt_texts length.")
        llm, backend_meta = self._load_model(model_name)
        prompt_names = prompt_names or [prompt_name or "batch_prompt"] * len(prompt_texts)
        prompt_versions = prompt_versions or [prompt_version or "v1"] * len(prompt_texts)
        system_texts = system_texts or [
            system_text or "Return only the requested tagged fields. Do not use markdown or hidden reasoning."
        ] * len(prompt_texts)
        rendered_prompts = [
            _render_messages(tokenizer=llm.get_tokenizer(), system_text=sys_text, user_text=prompt_text)
            for sys_text, prompt_text in zip(system_texts, prompt_texts, strict=True)
        ]

        results: list[dict[str, Any] | None] = [None] * len(prompt_texts)
        uncached_indices: list[int] = []
        uncached_requests: list[dict[str, Any]] = []
        uncached_rendered_prompts: list[str] = []
        for idx, rendered_prompt in enumerate(rendered_prompts):
            request = {
                "cache_version": f"{self.CACHE_VERSION}_text_v1",
                "backend": "vllm",
                "model_name": model_name,
                "prompt_name": prompt_names[idx],
                "prompt_version": prompt_versions[idx],
                "prompt_text": rendered_prompt,
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
                "backend_config": backend_meta,
            }
            cached = self.cache.get(request)
            if cached is not None:
                raw_response = cached["raw_response"]
                usage = raw_response.get("usage", {})
                results[idx] = {
                    "text": str(raw_response.get("output_text", "")),
                    "raw_response": raw_response,
                    "metrics": GenerationMetrics(
                        latency_s=float(cached["metrics"]["latency_s"]),
                        input_tokens=int(usage.get("input_tokens", 0)),
                        output_tokens=int(usage.get("output_tokens", 0)),
                        cost_usd=0.0,
                        cache_hit=True,
                        raw_path=str(self.cache.path_for(request)),
                    ),
                    "prompt_version": prompt_versions[idx],
                }
            else:
                uncached_indices.append(idx)
                uncached_requests.append(request)
                uncached_rendered_prompts.append(rendered_prompt)

        if uncached_indices:
            params = SamplingParams(
                temperature=max(float(temperature), 0.0),
                top_p=float(self.backend_config.get("top_p", 0.9)),
                max_tokens=int(max_output_tokens),
            )
            start = time.perf_counter()
            outputs = llm.generate(uncached_rendered_prompts, params)
            latency_s = time.perf_counter() - start
            for idx, request, output, metadata in zip(
                uncached_indices, uncached_requests, outputs, [metadata_list[i] for i in uncached_indices], strict=True
            ):
                text = output.outputs[0].text if output.outputs else ""
                raw_response = {
                    "backend": "vllm",
                    "model": model_name,
                    "backend_config": backend_meta,
                    "output_text": text,
                    "usage": {
                        "input_tokens": len(output.prompt_token_ids),
                        "output_tokens": len(output.outputs[0].token_ids) if output.outputs else 0,
                    },
                }
                raw_path = str(
                    self.cache.set(
                        request,
                        {
                            "raw_response": raw_response,
                            "metrics": {"latency_s": latency_s},
                            "metadata": metadata,
                        },
                    )
                )
                usage = raw_response.get("usage", {})
                results[idx] = {
                    "text": str(raw_response.get("output_text", "")),
                    "raw_response": raw_response,
                    "metrics": GenerationMetrics(
                        latency_s=latency_s,
                        input_tokens=int(usage.get("input_tokens", 0)),
                        output_tokens=int(usage.get("output_tokens", 0)),
                        cost_usd=0.0,
                        cache_hit=False,
                        raw_path=raw_path,
                    ),
                    "prompt_version": prompt_versions[idx],
                }

        return [result for result in results if result is not None]
