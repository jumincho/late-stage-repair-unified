"""HuggingFace `transformers` local client (`hf_local`).

The primary client used in the live full r2 collection runs. Loads a HF
causal-LM checkpoint with optional `bitsandbytes` quantization (4-bit /
8-bit), routes generation through a tokenizer-aware chat template, caches
the raw model output on disk by content hash, and exposes the unified
`generate_text` / `generate_structured` (pydantic-validated) surface. The
backend overrides (`dtype`, `device_map`, `max_model_len`, `quantization`,
`trust_remote_code`, etc.) come from the CLI flags on the collection
scripts.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Type

import torch
from pydantic import BaseModel
from pydantic import ValidationError

from dart_research.clients.base import GenerationEnvelope, GenerationMetrics, ModelClient
from dart_research.parsing.json_tools import extract_first_json
from dart_research.utils.cache import DiskCache

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
except ImportError:  # pragma: no cover - optional dependency guard
    AutoModelForCausalLM = None
    AutoTokenizer = None
    BitsAndBytesConfig = None


def _resolve_dtype(name: str) -> torch.dtype:
    mapping = {
        "float16": torch.float16,
        "fp16": torch.float16,
        "bfloat16": torch.bfloat16,
        "bf16": torch.bfloat16,
        "float32": torch.float32,
        "fp32": torch.float32,
    }
    return mapping.get(name.lower(), torch.float16)


def _schema_fields_hint(schema: Type[BaseModel]) -> str:
    fields = []
    for name, field in schema.model_fields.items():
        annotation = getattr(field, "annotation", str(field.annotation))
        type_name = getattr(annotation, "__name__", str(annotation))
        fields.append(f"{name}: {type_name}")
    return ", ".join(fields)


def _parse_max_memory(raw_value: Any) -> dict[str, str] | None:
    if raw_value in (None, "", "none"):
        return None
    if isinstance(raw_value, dict):
        return {str(key): str(value) for key, value in raw_value.items()}
    text = str(raw_value).strip()
    if not text:
        return None
    parts = [part.strip() for part in text.split(",") if part.strip()]
    if len(parts) == 1:
        count = torch.cuda.device_count()
        return {index: parts[0] for index in range(count)}
    return {index: value for index, value in enumerate(parts)}


def _render_messages(tokenizer: Any, system_text: str, user_text: str) -> str:
    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    chat_template = getattr(tokenizer, "chat_template", None)
    if chat_template:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return f"System: {system_text}\n\nUser: {user_text}\n\nAssistant:"


def _render_prompt(tokenizer: Any, prompt_text: str, schema: Type[BaseModel]) -> str:
    system_text = (
        "Return exactly one valid JSON object. "
        "Do not output markdown, code fences, analysis, or <think> tags. "
        "Do not show hidden reasoning. Keep fields concise. "
        f"Target schema: {schema.__name__}. "
        f"Required fields: {_schema_fields_hint(schema)}."
    )
    return _render_messages(tokenizer, system_text, prompt_text)


def _first_device(model: Any) -> torch.device:
    device_map = getattr(model, "hf_device_map", None)
    if isinstance(device_map, dict):
        for device in device_map.values():
            if isinstance(device, str) and device not in {"cpu", "disk"}:
                return torch.device(device)
            if isinstance(device, int):
                return torch.device(f"cuda:{device}")
    return next(model.parameters()).device


def _repair_prompt(raw_text: str, schema: Type[BaseModel]) -> str:
    schema_hint = schema.model_json_schema()
    return (
        "Convert the following assistant output into exactly one valid JSON object.\n"
        "Do not add commentary, markdown, or <think> tags.\n"
        f"Target schema name: {schema.__name__}\n"
        f"Target schema JSON Schema: {schema_hint}\n\n"
        "Assistant output to convert:\n"
        f"{raw_text}"
    )


def _object_only_repair_prompt(raw_text: str, schema: Type[BaseModel]) -> str:
    return (
        "Rewrite the following content as exactly one JSON object matching the target schema.\n"
        "The top-level value must be a JSON object, not a list or string.\n"
        "Do not include markdown, prose, or code fences.\n"
        f"Target schema name: {schema.__name__}\n"
        f"Required fields: {_schema_fields_hint(schema)}\n\n"
        "Content to convert:\n"
        f"{raw_text}"
    )


def _coerce_payload_for_schema(schema: Type[BaseModel], payload: Any) -> Any:
    if isinstance(payload, list) and len(schema.model_fields) == 1:
        field_name = next(iter(schema.model_fields))
        return {field_name: payload}
    return payload


class HFTransformersClient(ModelClient):
    """Local Hugging Face generation backend with disk caching."""

    CACHE_VERSION = "hf_local_v3"

    def __init__(self, cache_dir: Path, backend_config: dict[str, Any] | None = None):
        if AutoModelForCausalLM is None or AutoTokenizer is None:
            raise RuntimeError("transformers is not installed. Install local dependencies first.")
        self.cache = DiskCache(cache_dir / "hf_local")
        self.backend_config = backend_config or {}
        self._loaded: dict[str, tuple[Any, Any, dict[str, Any]]] = {}

    def _cache_namespace(self) -> str:
        return str(self.backend_config.get("cache_namespace", "")).strip()

    def _quantization_config(self) -> Any | None:
        quantization = str(self.backend_config.get("quantization", "none")).lower()
        if quantization == "none":
            return None
        if BitsAndBytesConfig is None:
            raise RuntimeError("bitsandbytes is not installed but quantization was requested.")
        if quantization == "4bit":
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=_resolve_dtype(str(self.backend_config.get("dtype", "float16"))),
            )
        if quantization == "8bit":
            return BitsAndBytesConfig(load_in_8bit=True)
        raise ValueError(f"Unsupported quantization mode: {quantization}")

    def _load_model(self, model_name: str) -> tuple[Any, Any, dict[str, Any]]:
        if model_name in self._loaded:
            return self._loaded[model_name]
        token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
        revision = self.backend_config.get("revision")
        dtype_name = str(self.backend_config.get("dtype", "float16"))
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            revision=revision,
            token=token,
            trust_remote_code=bool(self.backend_config.get("trust_remote_code", True)),
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        quantization_config = self._quantization_config()
        model_kwargs: dict[str, Any] = {
            "revision": revision,
            "token": token,
            "trust_remote_code": bool(self.backend_config.get("trust_remote_code", True)),
            "device_map": self.backend_config.get("device_map", "auto"),
            "low_cpu_mem_usage": True,
            "dtype": _resolve_dtype(dtype_name),
        }
        max_memory = _parse_max_memory(self.backend_config.get("max_memory"))
        if max_memory:
            model_kwargs["max_memory"] = max_memory
        if quantization_config is not None:
            model_kwargs["quantization_config"] = quantization_config
        model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
        model.eval()
        device_map = getattr(model, "hf_device_map", {})
        distinct_devices = sorted(
            {
                str(device)
                for device in device_map.values()
                if isinstance(device, (str, int)) and str(device) not in {"cpu", "disk"}
            }
        )
        metadata = {
            "backend": "hf_local",
            "model_name": model_name,
            "revision": revision or "",
            "dtype": dtype_name,
            "quantization": str(self.backend_config.get("quantization", "none")),
            "device_map": str(self.backend_config.get("device_map", "auto")),
            "max_memory": self.backend_config.get("max_memory", ""),
            "resolved_device_count": len(distinct_devices),
            "resolved_devices": distinct_devices,
            "max_model_len": int(self.backend_config.get("max_model_len", getattr(tokenizer, "model_max_length", 0) or 0)),
            "trust_remote_code": bool(self.backend_config.get("trust_remote_code", True)),
            "padding_side": str(getattr(tokenizer, "padding_side", "right")),
        }
        self._loaded[model_name] = (tokenizer, model, metadata)
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
        tokenizer, model, backend_meta = self._load_model(model_name)
        rendered_prompt = _render_prompt(tokenizer, prompt_text, schema)
        request = {
            "cache_version": self.CACHE_VERSION,
            "cache_namespace": self._cache_namespace(),
            "backend": "hf_local",
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
        repaired = False
        if cached is not None:
            raw_response = cached["raw_response"]
            raw_path = str(self.cache.path_for(request))
            cache_hit = True
            latency_s = float(cached["metrics"]["latency_s"])
        else:
            raw_response, latency_s = self._generate_once(
                tokenizer=tokenizer,
                model=model,
                model_name=model_name,
                backend_meta=backend_meta,
                rendered_prompt=rendered_prompt,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
            text = str(raw_response.get("output_text", ""))
            try:
                payload = extract_first_json(text)
                payload = _coerce_payload_for_schema(schema, payload)
                schema.model_validate(payload)
            except (Exception, ValidationError):
                repair_attempts: list[str] = []
                total_input_tokens = int(raw_response["usage"]["input_tokens"])
                total_output_tokens = int(raw_response["usage"]["output_tokens"])
                current_text = text
                for repair_prompt in (_repair_prompt, _object_only_repair_prompt):
                    repair_response, repair_latency_s = self._generate_once(
                        tokenizer=tokenizer,
                        model=model,
                        model_name=model_name,
                        backend_meta=backend_meta,
                        rendered_prompt=_render_prompt(tokenizer, repair_prompt(current_text, schema), schema),
                        temperature=0.0,
                        max_output_tokens=min(int(max_output_tokens), 256),
                    )
                    repair_text = str(repair_response.get("output_text", ""))
                    repair_attempts.append(repair_text)
                    total_input_tokens += int(repair_response["usage"]["input_tokens"])
                    total_output_tokens += int(repair_response["usage"]["output_tokens"])
                    latency_s += repair_latency_s
                    repaired = True
                    try:
                        payload = extract_first_json(repair_text)
                        payload = _coerce_payload_for_schema(schema, payload)
                        schema.model_validate(payload)
                        current_text = repair_text
                        break
                    except (Exception, ValidationError):
                        current_text = repair_text
                        continue
                raw_response = {
                    "backend": "hf_local",
                    "model": model_name,
                    "backend_config": backend_meta,
                    "initial_output_text": text,
                    "repair_outputs": repair_attempts,
                    "repair_output_text": current_text,
                    "output_text": current_text,
                    "usage": {
                        "input_tokens": total_input_tokens,
                        "output_tokens": total_output_tokens,
                    },
                    "repair_attempted": True,
                }
            raw_path = str(
                self.cache.set(
                    request,
                    {
                        "raw_response": raw_response,
                        "metrics": {"latency_s": latency_s, "repaired": repaired},
                        "metadata": metadata,
                    },
                )
            )
            cache_hit = False

        text = str(raw_response.get("output_text", ""))
        payload = extract_first_json(text)
        payload = _coerce_payload_for_schema(schema, payload)
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
        tokenizer, model, backend_meta = self._load_model(model_name)
        rendered_prompt = _render_messages(
            tokenizer,
            system_text or "Return only the requested tagged fields. Do not use markdown or hidden reasoning.",
            prompt_text,
        )
        request = {
            "cache_version": f"{self.CACHE_VERSION}_text_v1",
            "cache_namespace": self._cache_namespace(),
            "backend": "hf_local",
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
            latency_s = float(cached["metrics"]["latency_s"])
            cache_hit = True
            raw_path = str(self.cache.path_for(request))
        else:
            raw_response, latency_s = self._generate_once(
                tokenizer=tokenizer,
                model=model,
                model_name=model_name,
                backend_meta=backend_meta,
                rendered_prompt=rendered_prompt,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
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
        tokenizer, model, backend_meta = self._load_model(model_name)
        prompt_names = prompt_names or [prompt_name or "batch_prompt"] * len(prompt_texts)
        prompt_versions = prompt_versions or [prompt_version or "v1"] * len(prompt_texts)
        system_texts = system_texts or [
            system_text or "Return only the requested tagged fields. Do not use markdown or hidden reasoning."
        ] * len(prompt_texts)
        rendered_prompts = [
            _render_messages(tokenizer, sys_text, prompt_text)
            for sys_text, prompt_text in zip(system_texts, prompt_texts, strict=True)
        ]

        results: list[dict[str, Any] | None] = [None] * len(prompt_texts)
        uncached_indices: list[int] = []
        uncached_requests: list[dict[str, Any]] = []
        uncached_rendered_prompts: list[str] = []
        for idx, rendered_prompt in enumerate(rendered_prompts):
            request = {
                "cache_version": f"{self.CACHE_VERSION}_text_v1",
                "backend": "hf_local",
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
            raw_responses, latency_s = self._generate_batch_once(
                tokenizer=tokenizer,
                model=model,
                model_name=model_name,
                backend_meta=backend_meta,
                rendered_prompts=uncached_rendered_prompts,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
            for idx, request, raw_response, metadata in zip(
                uncached_indices, uncached_requests, raw_responses, [metadata_list[i] for i in uncached_indices], strict=True
            ):
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

    def score_completion(
        self,
        *,
        model_name: str,
        prompt_name: str,
        prompt_version: str,
        prompt_text: str,
        completion_text: str,
        metadata: dict[str, Any],
        system_text: str | None = None,
    ) -> dict[str, Any]:
        tokenizer, model, backend_meta = self._load_model(model_name)
        rendered_prompt = _render_messages(
            tokenizer,
            system_text or "Answer with the requested text only.",
            prompt_text,
        )
        request = {
            "cache_version": f"{self.CACHE_VERSION}_score_v1",
            "backend": "hf_local",
            "model_name": model_name,
            "prompt_name": prompt_name,
            "prompt_version": prompt_version,
            "prompt_text": rendered_prompt,
            "completion_text": completion_text,
            "backend_config": backend_meta,
        }
        cached = self.cache.get(request)
        if cached is not None:
            payload = cached["payload"]
            raw_path = str(self.cache.path_for(request))
        else:
            payload = self._score_completion_once(
                tokenizer=tokenizer,
                model=model,
                rendered_prompt=rendered_prompt,
                completion_text=completion_text,
            )
            raw_path = str(self.cache.set(request, {"payload": payload, "metadata": metadata}))
        payload["raw_path"] = raw_path
        return payload

    def score_choices(
        self,
        *,
        model_name: str,
        prompt_name: str,
        prompt_version: str,
        prompt_text: str,
        choices: list[str],
        metadata: dict[str, Any],
        system_text: str | None = None,
    ) -> dict[str, Any]:
        scores = []
        for choice in choices:
            payload = self.score_completion(
                model_name=model_name,
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                prompt_text=prompt_text,
                completion_text=choice,
                metadata=metadata,
                system_text=system_text,
            )
            scores.append({"choice": choice, **payload})
        max_score = max(item["total_logprob"] for item in scores)
        exp_scores = [torch.exp(torch.tensor(item["total_logprob"] - max_score)).item() for item in scores]
        total = sum(exp_scores) or 1.0
        probabilities = [value / total for value in exp_scores]
        for item, probability in zip(scores, probabilities, strict=True):
            item["probability"] = probability
        best = max(scores, key=lambda item: item["probability"])
        return {"choices": scores, "best_choice": best["choice"]}

    def _generate_once(
        self,
        *,
        tokenizer: Any,
        model: Any,
        model_name: str,
        backend_meta: dict[str, Any],
        rendered_prompt: str,
        temperature: float,
        max_output_tokens: int,
    ) -> tuple[dict[str, Any], float]:
        input_device = _first_device(model)
        encoded = tokenizer(rendered_prompt, return_tensors="pt", truncation=True)
        encoded = {key: value.to(input_device) for key, value in encoded.items()}
        input_tokens = int(encoded["input_ids"].shape[-1])
        do_sample = float(temperature) >= 0.5
        generate_kwargs: dict[str, Any] = {
            "max_new_tokens": int(max_output_tokens),
            "do_sample": do_sample,
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": tokenizer.eos_token_id,
        }
        if do_sample:
            generate_kwargs["temperature"] = float(temperature)
            generate_kwargs["top_p"] = float(self.backend_config.get("top_p", 0.9))
        start = time.perf_counter()
        with torch.inference_mode():
            output = model.generate(**encoded, **generate_kwargs)
        latency_s = time.perf_counter() - start
        generated_ids = output[0][encoded["input_ids"].shape[-1] :]
        text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        output_tokens = int(generated_ids.shape[-1])
        response = {
            "backend": "hf_local",
            "model": model_name,
            "backend_config": backend_meta,
            "output_text": text,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        }
        return response, latency_s

    def _generate_batch_once(
        self,
        *,
        tokenizer: Any,
        model: Any,
        model_name: str,
        backend_meta: dict[str, Any],
        rendered_prompts: list[str],
        temperature: float,
        max_output_tokens: int,
    ) -> tuple[list[dict[str, Any]], float]:
        input_device = _first_device(model)
        encoded = tokenizer(rendered_prompts, return_tensors="pt", truncation=True, padding=True)
        encoded = {key: value.to(input_device) for key, value in encoded.items()}
        input_lengths = encoded["attention_mask"].sum(dim=1).tolist()
        do_sample = float(temperature) >= 0.5
        generate_kwargs: dict[str, Any] = {
            "max_new_tokens": int(max_output_tokens),
            "do_sample": do_sample,
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": tokenizer.eos_token_id,
        }
        if do_sample:
            generate_kwargs["temperature"] = float(temperature)
            generate_kwargs["top_p"] = float(self.backend_config.get("top_p", 0.9))
        start = time.perf_counter()
        with torch.inference_mode():
            output = model.generate(**encoded, **generate_kwargs)
        latency_s = time.perf_counter() - start

        rows: list[dict[str, Any]] = []
        for row_idx, input_len in enumerate(input_lengths):
            generated_ids = output[row_idx][int(input_len) :]
            text = tokenizer.decode(generated_ids, skip_special_tokens=True)
            rows.append(
                {
                    "backend": "hf_local",
                    "model": model_name,
                    "backend_config": backend_meta,
                    "output_text": text,
                    "usage": {
                        "input_tokens": int(input_len),
                        "output_tokens": int(generated_ids.shape[-1]),
                    },
                }
            )
        return rows, latency_s

    def _score_completion_once(
        self,
        *,
        tokenizer: Any,
        model: Any,
        rendered_prompt: str,
        completion_text: str,
    ) -> dict[str, Any]:
        input_device = _first_device(model)
        prompt_ids = tokenizer(rendered_prompt, return_tensors="pt", add_special_tokens=False)
        completion_ids = tokenizer(completion_text, return_tensors="pt", add_special_tokens=False)
        prompt_ids = prompt_ids["input_ids"].to(input_device)
        completion_ids = completion_ids["input_ids"].to(input_device)
        full_ids = torch.cat([prompt_ids, completion_ids], dim=1)
        attention_mask = torch.ones_like(full_ids, device=input_device)
        with torch.inference_mode():
            logits = model(input_ids=full_ids, attention_mask=attention_mask).logits
        log_probs = torch.log_softmax(logits[:, :-1, :], dim=-1)
        completion_len = int(completion_ids.shape[1])
        if completion_len == 0:
            return {
                "total_logprob": 0.0,
                "mean_logprob": 0.0,
                "completion_tokens": 0,
                "input_tokens": int(prompt_ids.shape[1]),
            }
        start_index = int(prompt_ids.shape[1]) - 1
        token_logprobs: list[float] = []
        for offset in range(completion_len):
            position = start_index + offset
            target_token = int(full_ids[0, prompt_ids.shape[1] + offset])
            token_logprobs.append(float(log_probs[0, position, target_token].item()))
        total_logprob = float(sum(token_logprobs))
        mean_logprob = float(total_logprob / completion_len)
        return {
            "total_logprob": total_logprob,
            "mean_logprob": mean_logprob,
            "completion_tokens": completion_len,
            "input_tokens": int(prompt_ids.shape[1]),
        }
