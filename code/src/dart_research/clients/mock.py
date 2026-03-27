from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Type

from pydantic import BaseModel

from dart_research.clients.base import GenerationEnvelope, GenerationMetrics, ModelClient
from dart_research.parsing.schemas import (
    CandidateSet,
    DefenseSet,
    DraftAnswer,
    FinalAnswer,
    FreeformDevilAdvocate,
    FreeformRebuttal,
    RebuttalSet,
    SelectionDecision,
    SelfRefineCritique,
    ValidationSet,
)
from dart_research.utils.cache import DiskCache


class MockClient(ModelClient):
    """Deterministic mock backend for smoke tests."""

    def __init__(self, cache_dir: Path):
        self.cache = DiskCache(cache_dir / "mock")

    def _mock_payload(self, schema: Type[BaseModel]) -> dict[str, Any]:
        if schema is DraftAnswer:
            return {
                "answer": "mock-answer",
                "normalized_answer": "mock-answer",
                "constraints": ["mock constraint"],
                "confidence": "medium",
            }
        if schema is CandidateSet:
            return {
                "candidates": [
                    {
                        "option_id": "A",
                        "answer": "mock-answer",
                        "normalized_answer": "mock-answer",
                        "source": "mock",
                        "persona": "",
                        "short_rationale": "mock rationale",
                    },
                    {
                        "option_id": "B",
                        "answer": "mock-alt",
                        "normalized_answer": "mock-alt",
                        "source": "mock",
                        "persona": "",
                        "short_rationale": "mock alternative",
                    },
                ]
            }
        if schema is DefenseSet:
            return {"defenses": [{"option_id": "A", "defense": "mock defense"}, {"option_id": "B", "defense": "mock defense"}]}
        if schema is ValidationSet:
            return {
                "decisions": [
                    {"option_id": "A", "keep": True, "reason": "mock", "duplicate_of": None},
                    {"option_id": "B", "keep": True, "reason": "mock", "duplicate_of": None},
                ]
            }
        if schema is RebuttalSet:
            return {
                "entries": [
                    {
                        "option_id": "A",
                        "seems_right_because": "mock",
                        "likely_failure": "mock",
                        "decisive_test_or_constraint": "mock",
                        "verdict_for_now": "uncertain",
                    },
                    {
                        "option_id": "B",
                        "seems_right_because": "mock",
                        "likely_failure": "mock",
                        "decisive_test_or_constraint": "mock",
                        "verdict_for_now": "lean_reject",
                    },
                ]
            }
        if schema is FinalAnswer:
            return {
                "answer": "mock-answer",
                "normalized_answer": "mock-answer",
                "justification": "mock justification",
                "confidence": "medium",
            }
        if schema is SelectionDecision:
            return {"option_id": "A", "reason": "mock select"}
        if schema is SelfRefineCritique:
            return {"issues": ["mock issue"], "fix_hint": "mock fix"}
        if schema is FreeformDevilAdvocate:
            return {
                "counterargument": "mock counterargument",
                "alternative_path": "mock alternative path",
                "main_risk": "mock risk",
            }
        if schema is FreeformRebuttal:
            return {
                "accepted_points": ["mock accepted point"],
                "rejected_points": ["mock rejected point"],
                "decisive_constraint": "mock decisive constraint",
                "revised_plan": "mock revised plan",
            }
        raise ValueError(f"Unsupported schema for mock client: {schema}")

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
            "model_name": model_name,
            "prompt_name": prompt_name,
            "prompt_version": prompt_version,
            "prompt_text": prompt_text,
            "schema": schema.__name__,
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
        }
        cached = self.cache.get(request)
        if cached is None:
            payload = self._mock_payload(schema)
            cached = {
                "request": request,
                "response": payload,
                "usage": {"input_tokens": 10, "output_tokens": 10},
                "model": model_name,
                "metadata": metadata,
            }
            raw_path = str(self.cache.set(request, cached))
            cache_hit = False
        else:
            raw_path = str(self.cache.path_for(request))
            cache_hit = True

        time.sleep(0.01)
        parsed = schema.model_validate(cached["response"])
        metrics = GenerationMetrics(
            latency_s=0.01,
            input_tokens=cached["usage"]["input_tokens"],
            output_tokens=cached["usage"]["output_tokens"],
            cost_usd=0.0,
            cache_hit=cache_hit,
            raw_path=raw_path,
        )
        return GenerationEnvelope(parsed=parsed, raw_response=cached, metrics=metrics, prompt_version=prompt_version)
