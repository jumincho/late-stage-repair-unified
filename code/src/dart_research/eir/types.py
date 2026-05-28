"""Typed record shapes for the EIR / HEIR / OSCAR / ATLAS / CASS pipeline.

These dataclasses are the on-disk shape every math-side runner serialises
into `per_example.jsonl`:

- `DraftRecord` — the initial answer + scratch + correctness label.
- `ProbeRecord` — one probe's parsed fields, with optional raw text.
- `ActionOutcome` and `BaselineOutcome` — what one action produced and how
  it compares to the baseline.
- `ActionBankRecord` — the whole per-example record bundling draft +
  probes + actions + prompt bundle versions.

Used by every math runner from `eir` all the way to `cass_r4`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class DraftRecord:
    answer: str
    normalized_answer: str
    scratch: str
    correctness: int
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    raw_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ProbeRecord:
    action_name: str
    fields: dict[str, Any]
    parse_ok: int
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    raw_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ActionOutcome:
    action_name: str
    answer: str
    normalized_answer: str
    scratch: str
    correctness: int
    helpful: int
    harmful: int
    neutral: int
    parse_ok: int = 1
    action_failed: int = 0
    execution_used: int = 0
    execution_success: int = 0
    execution_result: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    raw_paths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BaselineOutcome:
    name: str
    answer: str
    normalized_answer: str
    correctness: int
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    raw_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ActionBankRecord:
    dataset: str
    question_id: str
    question: str
    gold_answer: str
    gold_normalized: str
    task_type: str
    model_name: str
    backend: str
    prompt_bundle: dict[str, str]
    draft: DraftRecord
    general_features: dict[str, Any]
    state_features: dict[str, Any]
    probes: list[ProbeRecord]
    actions: list[ActionOutcome]
    baselines: dict[str, BaselineOutcome]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "question_id": self.question_id,
            "question": self.question,
            "gold_answer": self.gold_answer,
            "gold_normalized": self.gold_normalized,
            "task_type": self.task_type,
            "model_name": self.model_name,
            "backend": self.backend,
            "prompt_bundle": self.prompt_bundle,
            "draft": self.draft.to_dict(),
            "general_features": self.general_features,
            "state_features": self.state_features,
            "probes": [probe.to_dict() for probe in self.probes],
            "actions": [action.to_dict() for action in self.actions],
            "baselines": {name: outcome.to_dict() for name, outcome in self.baselines.items()},
            "metadata": self.metadata,
        }
