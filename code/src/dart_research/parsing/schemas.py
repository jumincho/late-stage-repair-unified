"""Pydantic response schemas used by the generic method pipelines.

The structured-output contracts the generic `methods/pipelines.py` and the
mock client expect to receive. One pydantic model per logical response
shape: drafts, candidate sets, validation sets, rebuttals, selection
decisions, defenses, self-refine critiques, freeform devil's advocate /
rebuttal. Field validators coerce non-string values into strings so an LLM
returning numbers where strings were expected still parses.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field, field_validator


Confidence = Literal["low", "medium", "high"]
Verdict = Literal["lean_accept", "lean_reject", "uncertain"]


class DraftAnswer(BaseModel):
    answer: str
    normalized_answer: str
    constraints: list[str] = Field(default_factory=list)
    confidence: Confidence

    @field_validator("answer", "normalized_answer", mode="before")
    @classmethod
    def _coerce_text_fields(cls, value: object) -> str:
        return str(value)

    @field_validator("confidence", mode="before")
    @classmethod
    def _coerce_confidence(cls, value: object) -> str:
        text = str(value).strip().lower()
        if text in {"high", "medium", "low"}:
            return text
        if text in {"med", "moderate"}:
            return "medium"
        return "medium"


class CandidateOption(BaseModel):
    option_id: str = ""
    answer: str = ""
    normalized_answer: str = ""
    source: str = ""
    persona: str = ""
    failure_mode: str = ""
    short_rationale: str = ""
    defense: str = ""

    @field_validator("option_id", "answer", "normalized_answer", "source", "persona", "failure_mode", "short_rationale", "defense", mode="before")
    @classmethod
    def _coerce_candidate_text_fields(cls, value: object) -> str:
        return "" if value is None else str(value)


class CandidateSet(BaseModel):
    candidates: list[CandidateOption] = Field(default_factory=list)

    @field_validator("candidates", mode="before")
    @classmethod
    def _coerce_candidates(cls, value: object) -> list[object]:
        if value is None:
            return []
        if not isinstance(value, list):
            return []
        cleaned: list[object] = []
        for item in value:
            if isinstance(item, (CandidateOption, dict)):
                candidate_like = item if isinstance(item, CandidateOption) else dict(item)
                if isinstance(candidate_like, dict):
                    allowed_keys = {"option_id", "answer", "normalized_answer", "source", "persona", "failure_mode", "short_rationale", "defense"}
                    if not any(key in candidate_like for key in allowed_keys):
                        continue
                cleaned.append(candidate_like)
                continue
            if isinstance(item, str):
                text = item.strip()
                if not text.startswith("{"):
                    continue
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    cleaned.append(parsed)
        return cleaned


class DefenseEntry(BaseModel):
    option_id: str = ""
    defense: str = ""

    @field_validator("option_id", "defense", mode="before")
    @classmethod
    def _coerce_text_fields(cls, value: object) -> str:
        return "" if value is None else str(value)


class DefenseSet(BaseModel):
    defenses: list[DefenseEntry] = Field(default_factory=list)


class ValidationDecision(BaseModel):
    option_id: str = ""
    keep: bool = False
    reason: str = ""
    duplicate_of: str | None = None

    @field_validator("option_id", "reason", mode="before")
    @classmethod
    def _coerce_text_fields(cls, value: object) -> str:
        return "" if value is None else str(value)

    @field_validator("duplicate_of", mode="before")
    @classmethod
    def _coerce_optional_duplicate(cls, value: object) -> str | None:
        return None if value is None else str(value)


class ValidationSet(BaseModel):
    decisions: list[ValidationDecision] = Field(default_factory=list)


class RebuttalEntry(BaseModel):
    option_id: str
    seems_right_because: str = ""
    likely_failure: str = ""
    decisive_test_or_constraint: str = ""
    verdict_for_now: Verdict = "uncertain"

    @field_validator("option_id", "seems_right_because", "likely_failure", "decisive_test_or_constraint", mode="before")
    @classmethod
    def _coerce_text_fields(cls, value: object) -> str:
        return "" if value is None else str(value)

    @field_validator("verdict_for_now", mode="before")
    @classmethod
    def _coerce_verdict(cls, value: object) -> str:
        text = str(value).strip().lower().replace(" ", "_").replace("-", "_")
        if text in {"lean_accept", "lean_reject", "uncertain"}:
            return text
        if text in {"accept", "likely_accept"}:
            return "lean_accept"
        if text in {"reject", "likely_reject"}:
            return "lean_reject"
        return "uncertain"


class RebuttalSet(BaseModel):
    entries: list[RebuttalEntry]


class FinalAnswer(BaseModel):
    answer: str
    normalized_answer: str
    justification: str = ""
    confidence: Confidence = "medium"

    @field_validator("answer", "normalized_answer", "justification", mode="before")
    @classmethod
    def _coerce_text_fields(cls, value: object) -> str:
        return str(value)

    @field_validator("confidence", mode="before")
    @classmethod
    def _coerce_confidence(cls, value: object) -> str:
        text = str(value).strip().lower()
        if text in {"high", "medium", "low"}:
            return text
        if text in {"med", "moderate"}:
            return "medium"
        return "medium"


class SelectionDecision(BaseModel):
    option_id: str
    reason: str = ""

    @field_validator("option_id", "reason", mode="before")
    @classmethod
    def _coerce_text_fields(cls, value: object) -> str:
        return str(value)


class SelfRefineCritique(BaseModel):
    issues: list[str] = Field(default_factory=list)
    fix_hint: str = ""

    @field_validator("issues", mode="before")
    @classmethod
    def _coerce_issues(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]

    @field_validator("fix_hint", mode="before")
    @classmethod
    def _coerce_fix_hint(cls, value: object) -> str:
        return str(value)


class FreeformDevilAdvocate(BaseModel):
    counterargument: str = ""
    alternative_path: str = ""
    main_risk: str = ""

    @field_validator("counterargument", "alternative_path", "main_risk", mode="before")
    @classmethod
    def _coerce_text_fields(cls, value: object) -> str:
        return "" if value is None else str(value)


class FreeformRebuttal(BaseModel):
    accepted_points: list[str] = Field(default_factory=list)
    rejected_points: list[str] = Field(default_factory=list)
    decisive_constraint: str = ""
    revised_plan: str = ""

    @field_validator("accepted_points", "rejected_points", mode="before")
    @classmethod
    def _coerce_lists(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]

    @field_validator("decisive_constraint", "revised_plan", mode="before")
    @classmethod
    def _coerce_text_fields(cls, value: object) -> str:
        return "" if value is None else str(value)
