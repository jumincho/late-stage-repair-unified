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
