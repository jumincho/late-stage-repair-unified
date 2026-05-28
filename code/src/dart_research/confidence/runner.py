"""`ChaseTraceRunner` — fixed-budget same-context challenge trace collector.

Drives a local HF model through a fixed sequence of probe prompts on a
single benchmark example:

- initial draft,
- verbalized-confidence-20 and verbalized-confidence-100 probes,
- "challenge" question and a same-context revise,
- self-refine critique and revise,
- alternatives probe.

Each step is recorded as a `StageTrace` so the downstream confidence /
vchase analysis can stitch per-stage signals into trace-level features.
This was the inner loop of the earlier confidence-focused rounds.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import re
from typing import Any

from dart_research.clients.hf_local import HFTransformersClient
from dart_research.confidence.prompts import ConfidencePromptBank
from dart_research.confidence.types import SelfRefineResult, SignalSnapshot, StageTrace, TraceRecord
from dart_research.datasets.loaders import BenchmarkExample
from dart_research.parsing.normalization import extract_numeric, normalize_prediction
from dart_research.parsing.tagged import extract_tagged_fields, parse_int_tag


class ChaseTraceRunner:
    """Collect fixed-budget same-context challenge traces on local models."""

    def __init__(
        self,
        *,
        repo_root: Path,
        client: HFTransformersClient,
        model_name: str,
        max_output_tokens: int = 160,
    ) -> None:
        self.repo_root = repo_root
        self.client = client
        self.model_name = model_name
        self.max_output_tokens = max_output_tokens
        self.prompts = ConfidencePromptBank.load(repo_root)

    def collect_trace(
        self,
        example: BenchmarkExample,
        *,
        max_rounds: int = 2,
        include_vc100: bool = False,
        dispersion_samples: int = 2,
    ) -> TraceRecord:
        stages: list[StageTrace] = []
        answer_text, scratch_text, draft_meta = self._draft(example)
        current_answer = answer_text
        current_scratch = scratch_text
        for stage_index in range(max_rounds + 1):
            signals, usage = self._collect_signals(
                example,
                answer=current_answer,
                scratch=current_scratch,
                include_vc100=include_vc100,
                dispersion_samples=dispersion_samples,
            )
            normalized = normalize_prediction(current_answer, example.task_type)
            stage = StageTrace(
                stage_index=stage_index,
                answer=current_answer,
                normalized_answer=normalized,
                scratch=current_scratch,
                correctness=int(normalized == example.gold_normalized),
                input_tokens=draft_meta["input_tokens"] + usage["input_tokens"],
                output_tokens=draft_meta["output_tokens"] + usage["output_tokens"],
                latency_s=draft_meta["latency_s"] + usage["latency_s"],
                raw_paths=draft_meta["raw_paths"] + usage["raw_paths"],
                signals=signals,
            )
            if stages:
                stage.answer_changed = int(stage.normalized_answer != stages[-1].normalized_answer)
            stages.append(stage)
            if stage_index == max_rounds:
                break
            attack, risk_tag, attack_meta = self._challenge(example, current_answer, current_scratch)
            revised_answer, revised_scratch, decision, revise_meta = self._revise(
                example,
                answer=current_answer,
                scratch=current_scratch,
                attack=attack,
            )
            stages[-1].attack = attack
            stages[-1].risk_tag = risk_tag
            stages[-1].decision = decision
            stages[-1].transition_input_tokens = attack_meta["input_tokens"] + revise_meta["input_tokens"]
            stages[-1].transition_output_tokens = attack_meta["output_tokens"] + revise_meta["output_tokens"]
            stages[-1].transition_latency_s = attack_meta["latency_s"] + revise_meta["latency_s"]
            stages[-1].transition_raw_paths.extend(attack_meta["raw_paths"] + revise_meta["raw_paths"])
            current_answer = revised_answer
            current_scratch = revised_scratch
            draft_meta = {"input_tokens": 0, "output_tokens": 0, "latency_s": 0.0, "raw_paths": []}

        self_refine = self._self_refine(example, stages[0].answer, stages[0].scratch)
        return TraceRecord(
            dataset=example.dataset,
            question_id=example.question_id,
            question=example.question,
            gold_answer=example.gold_answer,
            gold_normalized=example.gold_normalized,
            task_type=example.task_type,
            model_name=self.model_name,
            backend="hf_local",
            prompt_bundle=self.prompts.version_bundle(),
            stages=stages,
            self_refine=self_refine,
            metadata=example.metadata,
        )

    def _draft(self, example: BenchmarkExample) -> tuple[str, str, dict[str, Any]]:
        prompt = self.prompts.draft.render(question=example.question)
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="draft_tagged",
            prompt_version=self.prompts.draft.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 80),
            metadata={"branch": "chase", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly these tags and nothing else: <answer>...</answer><scratch>...</scratch>. No prose outside tags. No markdown. No thinking.",
        )
        fields = extract_tagged_fields(response["text"])
        answer = self._fallback_answer(fields.get("answer", ""), response["text"], example.task_type)
        scratch = fields.get("scratch", self._fallback_scratch(response["text"]))
        return answer, scratch, self._metrics_payload(response)

    def _challenge(self, example: BenchmarkExample, answer: str, scratch: str) -> tuple[str, str, dict[str, Any]]:
        prompt = self.prompts.challenge.render(question=example.question, answer=answer, scratch=scratch)
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="challenge_tagged",
            prompt_version=self.prompts.challenge.version,
            prompt_text=prompt,
            temperature=0.2,
            max_output_tokens=100,
            metadata={"branch": "chase", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly these tags and nothing else: <attack>...</attack><risk>...</risk>. Keep the attack short. No prose outside tags. No markdown. No thinking.",
        )
        fields = extract_tagged_fields(response["text"])
        return fields.get("attack", response["text"].strip()), fields.get("risk", ""), self._metrics_payload(response)

    def _revise(self, example: BenchmarkExample, *, answer: str, scratch: str, attack: str) -> tuple[str, str, str, dict[str, Any]]:
        prompt = self.prompts.revise_same.render(question=example.question, answer=answer, scratch=scratch, attack=attack)
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="revise_same_tagged",
            prompt_version=self.prompts.revise_same.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 80),
            metadata={"branch": "chase", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly these tags and nothing else: <answer>...</answer><scratch>...</scratch><decision>keep|revise</decision>. No prose outside tags. No markdown. No thinking.",
        )
        fields = extract_tagged_fields(response["text"])
        revised_answer = self._fallback_answer(fields.get("answer", ""), response["text"], example.task_type, default=answer)
        revised_scratch = fields.get("scratch", self._fallback_scratch(response["text"], default=scratch))
        decision = fields.get("decision", "keep" if normalize_prediction(revised_answer, example.task_type) == normalize_prediction(answer, example.task_type) else "revise")
        return revised_answer, revised_scratch, decision, self._metrics_payload(response)

    def _self_refine(self, example: BenchmarkExample, answer: str, scratch: str) -> SelfRefineResult:
        critique_prompt = self.prompts.self_refine_critique.render(question=example.question, answer=answer, scratch=scratch)
        critique_response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="self_refine_critique_tagged",
            prompt_version=self.prompts.self_refine_critique.version,
            prompt_text=critique_prompt,
            temperature=0.2,
            max_output_tokens=120,
            metadata={"branch": "chase", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly these tags and nothing else: <critique>...</critique><fix>...</fix>. Keep both short. No prose outside tags. No markdown. No thinking.",
        )
        critique_fields = extract_tagged_fields(critique_response["text"])
        revise_prompt = self.prompts.self_refine_revise.render(
            question=example.question,
            answer=answer,
            scratch=scratch,
            critique=critique_fields.get("critique", critique_response["text"].strip()),
            fix_hint=critique_fields.get("fix", ""),
        )
        revise_response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="self_refine_revise_tagged",
            prompt_version=self.prompts.self_refine_revise.version,
            prompt_text=revise_prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 80),
            metadata={"branch": "chase", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly these tags and nothing else: <answer>...</answer><scratch>...</scratch>. No prose outside tags. No markdown. No thinking.",
        )
        revise_fields = extract_tagged_fields(revise_response["text"])
        revised_answer = self._fallback_answer(revise_fields.get("answer", ""), revise_response["text"], example.task_type, default=answer)
        revised_scratch = revise_fields.get("scratch", self._fallback_scratch(revise_response["text"], default=scratch))
        normalized = normalize_prediction(revised_answer, example.task_type)
        return SelfRefineResult(
            answer=revised_answer,
            normalized_answer=normalized,
            scratch=revised_scratch,
            correctness=int(normalized == example.gold_normalized),
            input_tokens=critique_response["metrics"].input_tokens + revise_response["metrics"].input_tokens,
            output_tokens=critique_response["metrics"].output_tokens + revise_response["metrics"].output_tokens,
            latency_s=critique_response["metrics"].latency_s + revise_response["metrics"].latency_s,
            raw_paths=[critique_response["metrics"].raw_path, revise_response["metrics"].raw_path],
        )

    def _collect_signals(
        self,
        example: BenchmarkExample,
        *,
        answer: str,
        scratch: str,
        include_vc100: bool,
        dispersion_samples: int,
    ) -> tuple[SignalSnapshot, dict[str, Any]]:
        usage = {"input_tokens": 0, "output_tokens": 0, "latency_s": 0.0, "raw_paths": []}
        verbal_20 = self._verbal_confidence(example, answer, scale="20")
        self._merge_usage(usage, verbal_20["metrics"])
        verbal_100 = None
        if include_vc100:
            verbal_100 = self._verbal_confidence(example, answer, scale="100")
            self._merge_usage(usage, verbal_100["metrics"])
        binary = self._self_eval(example, answer)
        answer_score = self._answer_logprob(example, answer)
        dispersion = self._dispersion(example, answer, dispersion_samples)
        dinco = self._dinco_lite(example, answer, scratch)
        for payload in (binary, answer_score, dispersion, dinco):
            self._merge_usage(usage, payload["metrics"])
        signals = SignalSnapshot(
            verbal_conf_20=float(verbal_20["value"]),
            verbal_conf_100=float(verbal_100["value"]) if verbal_100 else None,
            self_eval_yes_prob=float(binary["yes_prob"]),
            self_eval_margin=float(binary["margin"]),
            answer_logprob=float(answer_score["total_logprob"]),
            answer_logprob_mean=float(answer_score["mean_logprob"]),
            disagreement_fraction=float(dispersion["disagreement_fraction"]),
            unique_answer_count=int(dispersion["unique_answer_count"]),
            dinco_gap=float(dinco["current_minus_best_alt"]),
            alt_best_logprob=float(dinco["best_alt_logprob"]),
        )
        return signals, usage

    def _verbal_confidence(self, example: BenchmarkExample, answer: str, *, scale: str) -> dict[str, Any]:
        template = self.prompts.vc20 if scale == "20" else self.prompts.vc100
        max_value = 20 if scale == "20" else 100
        prompt = template.render(question=example.question, answer=answer)
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name=f"verbal_conf_{scale}",
            prompt_version=template.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=80,
            metadata={"branch": "chase", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly these tags and nothing else: <confidence>...</confidence><note>...</note>. No prose outside tags. No markdown. No thinking.",
        )
        try:
            value = parse_int_tag(response["text"], "confidence", 0, max_value)
        except ValueError:
            value = self._fallback_confidence(response["text"], max_value=max_value)
        return {"value": value / max_value, "metrics": response["metrics"]}

    def _self_eval(self, example: BenchmarkExample, answer: str) -> dict[str, Any]:
        prompt = (
            f"Question:\n{example.question}\n\n"
            f"Proposed answer:\n{answer}\n\n"
            "Is the exact proposed answer correct for the question? Reply with YES or NO."
        )
        scored = self.client.score_choices(
            model_name=self.model_name,
            prompt_name="self_eval_yes_no",
            prompt_version="self_eval_yes_no_v1",
            prompt_text=prompt,
            choices=["YES", "NO"],
            metadata={"branch": "chase", "dataset": example.dataset, "question_id": example.question_id},
        )
        yes_prob = next(item["probability"] for item in scored["choices"] if item["choice"] == "YES")
        no_prob = next(item["probability"] for item in scored["choices"] if item["choice"] == "NO")
        return {
            "yes_prob": yes_prob,
            "margin": yes_prob - no_prob,
            "metrics": {
                "input_tokens": sum(item["input_tokens"] for item in scored["choices"]),
                "output_tokens": sum(item["completion_tokens"] for item in scored["choices"]),
                "latency_s": 0.0,
                "raw_paths": [item["raw_path"] for item in scored["choices"]],
            },
        }

    def _answer_logprob(self, example: BenchmarkExample, answer: str) -> dict[str, Any]:
        prompt = f"Question:\n{example.question}\n\nFinal answer:"
        scored = self.client.score_completion(
            model_name=self.model_name,
            prompt_name="answer_logprob",
            prompt_version="answer_logprob_v1",
            prompt_text=prompt,
            completion_text=f" {answer}",
            metadata={"branch": "chase", "dataset": example.dataset, "question_id": example.question_id},
        )
        return {
            "total_logprob": scored["total_logprob"],
            "mean_logprob": scored["mean_logprob"],
            "metrics": {
                "input_tokens": scored["input_tokens"],
                "output_tokens": scored["completion_tokens"],
                "latency_s": 0.0,
                "raw_paths": [scored["raw_path"]],
            },
        }

    def _dispersion(self, example: BenchmarkExample, answer: str, samples: int) -> dict[str, Any]:
        answers = [normalize_prediction(answer, example.task_type)]
        metrics = {"input_tokens": 0, "output_tokens": 0, "latency_s": 0.0, "raw_paths": []}
        for sample_index in range(samples):
            prompt = self.prompts.draft.render(question=example.question)
            response = self.client.generate_text(
                model_name=self.model_name,
                prompt_name=f"draft_dispersion_{sample_index}",
                prompt_version=self.prompts.draft.version,
                prompt_text=prompt,
                temperature=0.8,
                max_output_tokens=min(self.max_output_tokens, 80),
                metadata={"branch": "chase", "dataset": example.dataset, "question_id": example.question_id},
                system_text="Return exactly these tags and nothing else: <answer>...</answer><scratch>...</scratch>. No prose outside tags. No markdown. No thinking.",
            )
            fields = extract_tagged_fields(response["text"])
            extra_answer = self._fallback_answer(fields.get("answer", ""), response["text"], example.task_type)
            answers.append(normalize_prediction(extra_answer, example.task_type))
            self._merge_usage(metrics, response["metrics"])
        disagreements = sum(1 for item in answers[1:] if item != answers[0])
        return {
            "disagreement_fraction": disagreements / max(1, len(answers) - 1),
            "unique_answer_count": len({item for item in answers if item}),
            "metrics": metrics,
        }

    def _dinco_lite(self, example: BenchmarkExample, answer: str, scratch: str) -> dict[str, Any]:
        prompt = self.prompts.alternatives.render(question=example.question, answer=answer, scratch=scratch)
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="alternatives_tagged",
            prompt_version=self.prompts.alternatives.version,
            prompt_text=prompt,
            temperature=0.4,
            max_output_tokens=120,
            metadata={"branch": "chase", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly these tags and nothing else: <alt1>...</alt1><alt2>...</alt2><why>...</why>. No prose outside tags. No markdown. No thinking.",
        )
        fields = extract_tagged_fields(response["text"])
        alternatives = [fields.get("alt1", "").strip(), fields.get("alt2", "").strip()]
        current_score = self._answer_logprob(example, answer)
        best_alt = None
        metrics = self._metrics_payload(response)
        self._merge_usage(metrics, current_score["metrics"])
        best_alt_logprob = current_score["total_logprob"]
        for alt in alternatives:
            if not alt:
                continue
            scored = self._answer_logprob(example, alt)
            self._merge_usage(metrics, scored["metrics"])
            if best_alt is None or scored["total_logprob"] > best_alt["total_logprob"]:
                best_alt = scored
                best_alt_logprob = scored["total_logprob"]
        return {
            "current_minus_best_alt": current_score["total_logprob"] - best_alt_logprob,
            "best_alt_logprob": best_alt_logprob,
            "metrics": metrics,
        }

    @staticmethod
    def _fallback_answer(tagged_answer: str, raw_text: str, task_type: str, default: str = "") -> str:
        if tagged_answer.strip():
            return tagged_answer.strip()
        if task_type == "numeric_open":
            numeric = extract_numeric(raw_text)
            if numeric and numeric != raw_text.strip().lower():
                return numeric
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        return lines[-1] if lines else default

    @staticmethod
    def _fallback_scratch(raw_text: str, default: str = "") -> str:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not lines:
            return default
        if len(lines) == 1:
            return default
        return lines[0][:200]

    @staticmethod
    def _fallback_confidence(raw_text: str, *, max_value: int) -> int:
        numbers = [int(match) for match in re.findall(r"-?\d+", raw_text)]
        if numbers:
            value = numbers[-1]
            return max(0, min(max_value, value))
        return max_value // 2

    @staticmethod
    def _merge_usage(target: dict[str, Any], payload: Any) -> None:
        if hasattr(payload, "input_tokens"):
            target["input_tokens"] += int(payload.input_tokens)
            target["output_tokens"] += int(payload.output_tokens)
            target["latency_s"] += float(payload.latency_s)
            target["raw_paths"].append(str(payload.raw_path))
            return
        target["input_tokens"] += int(payload.get("input_tokens", 0))
        target["output_tokens"] += int(payload.get("output_tokens", 0))
        target["latency_s"] += float(payload.get("latency_s", 0.0))
        target["raw_paths"].extend(list(payload.get("raw_paths", [])))

    @staticmethod
    def _metrics_payload(response: dict[str, Any]) -> dict[str, Any]:
        metrics = response["metrics"]
        return {
            "input_tokens": int(metrics.input_tokens),
            "output_tokens": int(metrics.output_tokens),
            "latency_s": float(metrics.latency_s),
            "raw_paths": [str(metrics.raw_path)],
        }
