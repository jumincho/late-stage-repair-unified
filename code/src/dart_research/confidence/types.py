"""Typed record shapes for confidence / chase traces.

Three dataclasses make up the per-example record:

- `SignalSnapshot` — one stage's measured signals (verbal conf, self-eval,
  answer log-prob, disagreement fraction, dinco gap, critique severity,
  ...). Every field is optional because not every stage produces every
  signal.
- `StageTrace` — the model's text + parsed fields at one stage plus its
  `SignalSnapshot`.
- `SelfRefineResult` and `TraceRecord` — wrappers that the runner
  serialises into the `per_example.jsonl` record for downstream analysis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class SignalSnapshot:
    verbal_conf_20: float | None = None
    verbal_conf_100: float | None = None
    self_eval_yes_prob: float | None = None
    self_eval_margin: float | None = None
    answer_logprob: float | None = None
    answer_logprob_mean: float | None = None
    disagreement_fraction: float | None = None
    unique_answer_count: int = 0
    dinco_gap: float | None = None
    alt_best_logprob: float | None = None
    critique_severity: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StageTrace:
    stage_index: int
    answer: str
    normalized_answer: str
    scratch: str
    attack: str = ""
    risk_tag: str = ""
    decision: str = ""
    signals: SignalSnapshot = field(default_factory=SignalSnapshot)
    correctness: int = 0
    answer_changed: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    raw_paths: list[str] = field(default_factory=list)
    transition_input_tokens: int = 0
    transition_output_tokens: int = 0
    transition_latency_s: float = 0.0
    transition_raw_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["signals"] = self.signals.to_dict()
        return payload


@dataclass(slots=True)
class SelfRefineResult:
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
class TraceRecord:
    dataset: str
    question_id: str
    question: str
    gold_answer: str
    gold_normalized: str
    task_type: str
    model_name: str
    backend: str
    prompt_bundle: dict[str, str]
    stages: list[StageTrace]
    self_refine: SelfRefineResult
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
            "stages": [stage.to_dict() for stage in self.stages],
            "self_refine": self.self_refine.to_dict(),
            "metadata": self.metadata,
        }
