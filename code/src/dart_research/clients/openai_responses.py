"""OpenAI Responses API client.

Optional API-hosted backend used during early teacher-seed collection (the
teacher patches the CASS retrieval round consumes). Wraps the official
`openai` SDK's Responses API with retry-on-transient-error, a content-hash
disk cache, and the unified `GenerationEnvelope` return type. Pricing is
read from `configs/models.yaml` so per-call cost is recorded alongside the
tokens. Not used in the final live full r2 run, which is local-only.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Type

from openai import OpenAI
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from dart_research.clients.base import GenerationEnvelope, GenerationMetrics, ModelClient
from dart_research.parsing.json_tools import extract_first_json
from dart_research.utils.cache import DiskCache


def _extract_text(raw_response: dict[str, Any]) -> str:
    output = raw_response.get("output", [])
    chunks: list[str] = []
    for item in output:
        contents = item.get("content") or []
        for content in contents:
            if content.get("type") == "output_text":
                chunks.append(content.get("text", ""))
    if chunks:
        return "\n".join(chunks)
    return raw_response.get("output_text", "")


def _extract_usage(raw_response: dict[str, Any]) -> tuple[int, int]:
    usage = raw_response.get("usage", {})
    input_tokens = int(usage.get("input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    return input_tokens, output_tokens


class OpenAIResponsesClient(ModelClient):
    """Thin Responses API wrapper with disk caching and JSON parsing."""

    def __init__(self, cache_dir: Path, pricing: dict[str, dict[str, float]]):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in the environment.")
        self.client = OpenAI(api_key=api_key)
        self.cache = DiskCache(cache_dir / "openai")
        self.pricing = pricing

    def _estimate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        price_cfg = self.pricing.get(model_name, {})
        input_cost = price_cfg.get("input_cost_per_1m", 0.0) * input_tokens / 1_000_000
        output_cost = price_cfg.get("output_cost_per_1m", 0.0) * output_tokens / 1_000_000
        return round(input_cost + output_cost, 8)

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _call_api(self, request: dict[str, Any]):
        return self.client.responses.create(**request)

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
        request = {
            "model": model_name,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": "Return valid JSON only. Do not wrap it in markdown."}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt_text}],
                },
            ],
            "max_output_tokens": max_output_tokens,
        }
        if model_name.startswith("gpt-5"):
            request["reasoning"] = {"effort": "minimal"}
            request["text"] = {"verbosity": "low"}
        else:
            request["temperature"] = temperature
        cache_key = {
            "request": request,
            "schema": schema.__name__,
            "prompt_name": prompt_name,
            "prompt_version": prompt_version,
            "requested_temperature": temperature,
        }
        cached = self.cache.get(cache_key)
        if cached is not None:
            raw_response = cached["raw_response"]
            raw_path = str(self.cache.path_for(cache_key))
            cache_hit = True
            latency_s = float(cached["metrics"]["latency_s"])
        else:
            start = time.perf_counter()
            response = self._call_api(request)
            latency_s = time.perf_counter() - start
            raw_response = response.model_dump()
            raw_path = str(
                self.cache.set(
                    cache_key,
                    {
                        "raw_response": raw_response,
                        "metrics": {"latency_s": latency_s},
                        "metadata": metadata,
                    },
                )
            )
            cache_hit = False

        text = _extract_text(raw_response)
        payload = extract_first_json(text)
        parsed = schema.model_validate(payload)
        input_tokens, output_tokens = _extract_usage(raw_response)
        metrics = GenerationMetrics(
            latency_s=latency_s,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=self._estimate_cost(model_name, input_tokens, output_tokens),
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
        request = {
            "model": model_name,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": system_text or "Return only the requested tagged fields. Do not use markdown or hidden reasoning.",
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt_text}],
                },
            ],
            "max_output_tokens": max_output_tokens,
        }
        if model_name.startswith("gpt-5"):
            request["reasoning"] = {"effort": "minimal"}
            request["text"] = {"verbosity": "low"}
        else:
            request["temperature"] = temperature
        cache_key = {
            "request": request,
            "prompt_name": prompt_name,
            "prompt_version": prompt_version,
            "requested_temperature": temperature,
            "system_text": system_text or "",
            "text_only": True,
        }
        cached = self.cache.get(cache_key)
        if cached is not None:
            raw_response = cached["raw_response"]
            raw_path = str(self.cache.path_for(cache_key))
            cache_hit = True
            latency_s = float(cached["metrics"]["latency_s"])
        else:
            start = time.perf_counter()
            response = self._call_api(request)
            latency_s = time.perf_counter() - start
            raw_response = response.model_dump()
            raw_path = str(
                self.cache.set(
                    cache_key,
                    {
                        "raw_response": raw_response,
                        "metrics": {"latency_s": latency_s},
                        "metadata": metadata,
                    },
                )
            )
            cache_hit = False
        text = _extract_text(raw_response)
        input_tokens, output_tokens = _extract_usage(raw_response)
        return {
            "text": text,
            "raw_response": raw_response,
            "metrics": GenerationMetrics(
                latency_s=latency_s,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=self._estimate_cost(model_name, input_tokens, output_tokens),
                cache_hit=cache_hit,
                raw_path=raw_path,
            ),
            "prompt_version": prompt_version,
        }
