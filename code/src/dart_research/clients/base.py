"""Common model client envelope and base interface.

Every backend client in the `clients/` package (HuggingFace transformers,
vLLM, OpenAI Responses, mock) returns a `GenerationEnvelope` so the rest of
the codebase can ignore where the answer came from. `GenerationMetrics`
collects latency, token usage, cost, and the on-disk path of the cached raw
response — that path is what the closure reports cite when they say
"raw at ...". `ModelClient` is the abstract surface the backends implement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Type

from pydantic import BaseModel


@dataclass(slots=True)
class GenerationMetrics:
    latency_s: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    cache_hit: bool
    raw_path: str


@dataclass(slots=True)
class GenerationEnvelope:
    parsed: BaseModel
    raw_response: dict[str, Any]
    metrics: GenerationMetrics
    prompt_version: str


class ModelClient:
    """Base client for structured generation."""

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
        raise NotImplementedError
