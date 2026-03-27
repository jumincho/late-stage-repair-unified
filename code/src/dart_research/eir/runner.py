from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import re
from typing import Any

from dart_research.clients.hf_local import HFTransformersClient
from dart_research.confidence.runner import ChaseTraceRunner
from dart_research.datasets.loaders import BenchmarkExample
from dart_research.eir.prompts import EIRPromptBank
from dart_research.eir.python_exec import execute_python_snippet
from dart_research.eir.types import ActionBankRecord, ActionOutcome, BaselineOutcome, DraftRecord, ProbeRecord
from dart_research.parsing.normalization import extract_numeric, normalize_prediction
from dart_research.parsing.tagged import extract_tagged_fields
from dart_research.vchase.features import _arithmetic_feature_row
from dart_research.vchase.prm import ProcessRewardModelScorer


ACTION_NAMES = [
    "STOP",
    "FREEFORM_CRITIQUE",
    "EQUATION_REDERIVE",
    "CONSTRAINT_CHECKLIST",
    "PYTHON_RECOMPUTE",
    "LOCALIZE_BACKTRACK",
]


class EIRActionBankRunner:
    """Collect EIR action-bank records from a single frozen draft."""

    def __init__(
        self,
        *,
        repo_root: Path,
        client: HFTransformersClient,
        model_name: str,
        prm_scorer: ProcessRewardModelScorer | None = None,
        max_output_tokens: int = 180,
        use_constraint_checklist: bool = False,
    ) -> None:
        self.repo_root = repo_root
        self.client = client
        self.model_name = model_name
        self.prm_scorer = prm_scorer
        self.max_output_tokens = max_output_tokens
        self.use_constraint_checklist = use_constraint_checklist
        self.prompts = EIRPromptBank.load(repo_root)
        self.signal_runner = ChaseTraceRunner(
            repo_root=repo_root,
            client=client,
            model_name=model_name,
            max_output_tokens=max_output_tokens,
        )

    def collect_record(self, example: BenchmarkExample) -> ActionBankRecord:
        draft = self._draft(example)
        general_features = self._general_features(example, draft.answer, draft.scratch)
        state_features, _ = self._state_features(example, draft.answer, draft.scratch)
        probes = [
            self._freeform_probe(example, draft.answer, draft.scratch),
            self._python_probe(example, draft.answer, draft.scratch),
            self._localize_probe(example, draft.answer, draft.scratch),
        ]
        if self.use_constraint_checklist:
            probes.insert(1, self._checklist_probe(example, draft.answer, draft.scratch))
        else:
            probes.insert(1, self._equation_probe(example, draft.answer, draft.scratch))
        probe_map = {probe.action_name: probe for probe in probes}
        actions = [
            self._stop_action(example, draft),
            self._freeform_action(example, draft, probe_map["FREEFORM_CRITIQUE"]),
            self._python_action(example, draft, probe_map["PYTHON_RECOMPUTE"]),
            self._localize_action(example, draft, probe_map["LOCALIZE_BACKTRACK"]),
        ]
        if self.use_constraint_checklist:
            actions.insert(2, self._checklist_action(example, draft, probe_map["CONSTRAINT_CHECKLIST"]))
        else:
            actions.insert(2, self._equation_action(example, draft, probe_map["EQUATION_REDERIVE"]))
        baselines = {
            "direct_cot": BaselineOutcome(
                name="direct_cot",
                answer=draft.answer,
                normalized_answer=draft.normalized_answer,
                correctness=draft.correctness,
                input_tokens=draft.input_tokens,
                output_tokens=draft.output_tokens,
                latency_s=draft.latency_s,
                raw_paths=list(draft.raw_paths),
            ),
            "self_refine_1": self._baseline_self_refine(example, draft.answer, draft.scratch),
            "freeform_fixed2_same": self._baseline_freeform_fixed2(example, draft.answer, draft.scratch),
        }
        return ActionBankRecord(
            dataset=example.dataset,
            question_id=example.question_id,
            question=example.question,
            gold_answer=example.gold_answer,
            gold_normalized=example.gold_normalized,
            task_type=example.task_type,
            model_name=self.model_name,
            backend="hf_local",
            prompt_bundle=self.prompts.version_bundle(),
            draft=draft,
            general_features=general_features,
            state_features=state_features,
            probes=probes,
            actions=actions,
            baselines=baselines,
            metadata=example.metadata,
        )

    def collect_checklist_replacement(self, example: BenchmarkExample, draft: DraftRecord) -> tuple[ProbeRecord, ActionOutcome]:
        probe = self._checklist_probe(example, draft.answer, draft.scratch)
        action = self._checklist_action(example, draft, probe)
        return probe, action

    def _draft(self, example: BenchmarkExample) -> DraftRecord:
        prompt = self.prompts.draft.render(question=example.question)
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="eir_draft_tagged",
            prompt_version=self.prompts.draft.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 120),
            metadata={"branch": "eir", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly <answer> and <scratch> tags only. No markdown. No extra prose. No thinking.",
        )
        fields = extract_tagged_fields(response["text"])
        answer = self._fallback_answer(fields.get("answer", ""), response["text"], example.task_type)
        scratch = fields.get("scratch", self._fallback_scratch(response["text"]))
        normalized = normalize_prediction(answer, example.task_type)
        metrics = response["metrics"]
        return DraftRecord(
            answer=answer,
            normalized_answer=normalized,
            scratch=scratch,
            correctness=int(normalized == example.gold_normalized),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )

    def _state_features(self, example: BenchmarkExample, answer: str, scratch: str) -> tuple[dict[str, Any], dict[str, Any]]:
        signals, usage = self.signal_runner._collect_signals(
            example,
            answer=answer,
            scratch=scratch,
            include_vc100=False,
            dispersion_samples=2,
        )
        payload = asdict(signals)
        payload.update(_arithmetic_feature_row(answer=answer, scratch=scratch, task_type=example.task_type))
        if self.prm_scorer is not None:
            payload.update(self.prm_scorer.score_reasoning(question=example.question, scratch=scratch, answer=answer))
        return payload, usage

    def _freeform_probe(self, example: BenchmarkExample, answer: str, scratch: str) -> ProbeRecord:
        prompt = self.prompts.freeform_probe.render(question=example.question, answer=answer, scratch=scratch)
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="eir_freeform_probe",
            prompt_version=self.prompts.freeform_probe.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=100,
            metadata={"branch": "eir", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        metrics = response["metrics"]
        return ProbeRecord(
            action_name="FREEFORM_CRITIQUE",
            fields={
                "likely_error_type": fields.get("error_type", "unclear"),
                "target": fields.get("target", ""),
                "challenge": fields.get("challenge", ""),
                "specificity": self._parse_int(fields.get("specificity", "0")),
            },
            parse_ok=int(bool(fields.get("challenge"))),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )

    def _equation_probe(self, example: BenchmarkExample, answer: str, scratch: str) -> ProbeRecord:
        prompt = self.prompts.equation_probe.render(question=example.question, answer=answer, scratch=scratch)
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="eir_equation_probe",
            prompt_version=self.prompts.equation_probe.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=120,
            metadata={"branch": "eir", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        metrics = response["metrics"]
        return ProbeRecord(
            action_name="EQUATION_REDERIVE",
            fields={
                "variables": fields.get("variables", ""),
                "equations": fields.get("equations", ""),
                "parse_success": self._parse_yes_no(fields.get("parse_success", "")),
                "unresolved_count": self._parse_int(fields.get("unresolved_count", "0")),
                "complete_path": self._parse_yes_no(fields.get("complete_path", "")),
            },
            parse_ok=int(bool(fields)),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )

    def _python_probe(self, example: BenchmarkExample, answer: str, scratch: str) -> ProbeRecord:
        prompt = self.prompts.python_probe.render(question=example.question, answer=answer, scratch=scratch)
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="eir_python_probe",
            prompt_version=self.prompts.python_probe.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=120,
            metadata={"branch": "eir", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        exec_payload = execute_python_snippet(fields.get("code", "")) if fields.get("code") else {"success": 0, "result": "", "error": "no_code", "latency_s": 0.0}
        metrics = response["metrics"]
        return ProbeRecord(
            action_name="PYTHON_RECOMPUTE",
            fields={
                "code": fields.get("code", ""),
                "parse_success": self._parse_yes_no(fields.get("parse_success", "")),
                "exec_ready": self._parse_yes_no(fields.get("exec_ready", "")),
                "result_guess": fields.get("result_guess", ""),
                "mismatch": self._parse_tri(fields.get("mismatch", "unknown")),
                "execution_success": int(exec_payload["success"]),
                "execution_result": str(exec_payload["result"]),
            },
            parse_ok=int(bool(fields)),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s + float(exec_payload["latency_s"]),
            raw_paths=[metrics.raw_path],
        )

    def _checklist_probe(self, example: BenchmarkExample, answer: str, scratch: str) -> ProbeRecord:
        prompt = self.prompts.checklist_probe.render(question=example.question, answer=answer, scratch=scratch)
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="eir_checklist_probe",
            prompt_version=self.prompts.checklist_probe.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=120,
            metadata={"branch": "eir", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        metrics = response["metrics"]
        return ProbeRecord(
            action_name="CONSTRAINT_CHECKLIST",
            fields={
                "quantities": fields.get("quantities", ""),
                "constraints": fields.get("constraints", ""),
                "missing_or_conflicting": fields.get("missing_or_conflicting", ""),
                "complete": self._parse_yes_no(fields.get("complete", "")),
            },
            parse_ok=int(bool(fields.get("constraints") or fields.get("missing_or_conflicting"))),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )

    def _localize_probe(self, example: BenchmarkExample, answer: str, scratch: str) -> ProbeRecord:
        prompt = self.prompts.localize_probe.render(question=example.question, answer=answer, scratch=scratch)
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="eir_localize_probe",
            prompt_version=self.prompts.localize_probe.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=120,
            metadata={"branch": "eir", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        metrics = response["metrics"]
        return ProbeRecord(
            action_name="LOCALIZE_BACKTRACK",
            fields={
                "suspect": fields.get("suspect", ""),
                "reason_type": fields.get("reason_type", "unclear"),
                "backtrack_point": fields.get("backtrack_point", ""),
                "localized": self._parse_yes_no(fields.get("localized", "")),
            },
            parse_ok=int(bool(fields.get("suspect") or fields.get("backtrack_point"))),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )

    def _stop_action(self, example: BenchmarkExample, draft: DraftRecord) -> ActionOutcome:
        return self._make_action_outcome(
            example,
            action_name="STOP",
            answer=draft.answer,
            scratch=draft.scratch,
            draft_correct=draft.correctness,
            metrics={"input_tokens": 0, "output_tokens": 0, "latency_s": 0.0, "raw_paths": []},
        )

    def _freeform_action(self, example: BenchmarkExample, draft: DraftRecord, probe: ProbeRecord) -> ActionOutcome:
        challenge = str(probe.fields.get("challenge", "")).strip() or "Recheck the most likely arithmetic or assumption error."
        prompt = self.prompts.freeform_action.render(
            question=example.question,
            answer=draft.answer,
            scratch=draft.scratch,
            challenge=challenge,
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="eir_freeform_action",
            prompt_version=self.prompts.freeform_action.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 120),
            metadata={"branch": "eir", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly <answer>, <scratch>, and <decision> tags only.",
        )
        fields = extract_tagged_fields(response["text"])
        answer = self._fallback_answer(fields.get("answer", ""), response["text"], example.task_type, default=draft.answer)
        scratch = fields.get("scratch", self._fallback_scratch(response["text"], default=draft.scratch))
        return self._make_action_outcome(
            example,
            action_name="FREEFORM_CRITIQUE",
            answer=answer,
            scratch=scratch,
            draft_correct=draft.correctness,
            metrics=self._metrics_payload(response),
            metadata={"decision": fields.get("decision", "keep")},
        )

    def _equation_action(self, example: BenchmarkExample, draft: DraftRecord, probe: ProbeRecord) -> ActionOutcome:
        preview = str(probe.fields.get("equations", "")).strip() or "No complete equation skeleton identified."
        prompt = self.prompts.equation_action.render(
            question=example.question,
            answer=draft.answer,
            scratch=draft.scratch,
            equation_preview=preview,
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="eir_equation_action",
            prompt_version=self.prompts.equation_action.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 140),
            metadata={"branch": "eir", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly <answer>, <equations>, and <scratch> tags only.",
        )
        fields = extract_tagged_fields(response["text"])
        answer = self._fallback_answer(fields.get("answer", ""), response["text"], example.task_type, default=draft.answer)
        scratch = fields.get("scratch", self._fallback_scratch(response["text"], default=draft.scratch))
        return self._make_action_outcome(
            example,
            action_name="EQUATION_REDERIVE",
            answer=answer,
            scratch=scratch,
            draft_correct=draft.correctness,
            metrics=self._metrics_payload(response),
            metadata={"equations": fields.get("equations", "")},
        )

    def _python_action(self, example: BenchmarkExample, draft: DraftRecord, probe: ProbeRecord) -> ActionOutcome:
        preview = str(probe.fields.get("code", "")).strip() or "No executable sketch available."
        prompt = self.prompts.python_action.render(
            question=example.question,
            answer=draft.answer,
            scratch=draft.scratch,
            python_preview=preview,
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="eir_python_action",
            prompt_version=self.prompts.python_action.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 160),
            metadata={"branch": "eir", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly <code>, <answer>, and <scratch> tags only.",
        )
        fields = extract_tagged_fields(response["text"])
        exec_payload = execute_python_snippet(fields.get("code", ""))
        answer = str(exec_payload["result"]).strip() if exec_payload["success"] else self._fallback_answer(
            fields.get("answer", ""),
            response["text"],
            example.task_type,
            default=draft.answer,
        )
        scratch = fields.get("scratch", self._fallback_scratch(response["text"], default=draft.scratch))
        metrics = self._metrics_payload(response)
        metrics["latency_s"] += float(exec_payload["latency_s"])
        return self._make_action_outcome(
            example,
            action_name="PYTHON_RECOMPUTE",
            answer=answer,
            scratch=scratch,
            draft_correct=draft.correctness,
            metrics=metrics,
            metadata={"code": fields.get("code", ""), "model_answer": fields.get("answer", "")},
            execution_used=1,
            execution_success=int(exec_payload["success"]),
            execution_result=str(exec_payload["result"]),
            action_failed=int(not exec_payload["success"] and not fields.get("answer")),
        )

    def _checklist_action(self, example: BenchmarkExample, draft: DraftRecord, probe: ProbeRecord) -> ActionOutcome:
        preview = (
            f"quantities={probe.fields.get('quantities', '')}; "
            f"constraints={probe.fields.get('constraints', '')}; "
            f"missing={probe.fields.get('missing_or_conflicting', '')}"
        )
        prompt = self.prompts.checklist_action.render(
            question=example.question,
            answer=draft.answer,
            scratch=draft.scratch,
            checklist_preview=preview,
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="eir_checklist_action",
            prompt_version=self.prompts.checklist_action.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 140),
            metadata={"branch": "eir", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly <answer>, <checklist>, and <scratch> tags only.",
        )
        fields = extract_tagged_fields(response["text"])
        answer = self._fallback_answer(fields.get("answer", ""), response["text"], example.task_type, default=draft.answer)
        scratch = fields.get("scratch", self._fallback_scratch(response["text"], default=draft.scratch))
        return self._make_action_outcome(
            example,
            action_name="CONSTRAINT_CHECKLIST",
            answer=answer,
            scratch=scratch,
            draft_correct=draft.correctness,
            metrics=self._metrics_payload(response),
            metadata={"checklist": fields.get("checklist", "")},
        )

    def _localize_action(self, example: BenchmarkExample, draft: DraftRecord, probe: ProbeRecord) -> ActionOutcome:
        preview = f"suspect={probe.fields.get('suspect', '')}; backtrack={probe.fields.get('backtrack_point', '')}"
        prompt = self.prompts.localize_action.render(
            question=example.question,
            answer=draft.answer,
            scratch=draft.scratch,
            localize_preview=preview,
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="eir_localize_action",
            prompt_version=self.prompts.localize_action.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 160),
            metadata={"branch": "eir", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly <steps>, <suspect>, <answer>, and <scratch> tags only.",
        )
        fields = extract_tagged_fields(response["text"])
        answer = self._fallback_answer(fields.get("answer", ""), response["text"], example.task_type, default=draft.answer)
        scratch = fields.get("scratch", self._fallback_scratch(response["text"], default=draft.scratch))
        return self._make_action_outcome(
            example,
            action_name="LOCALIZE_BACKTRACK",
            answer=answer,
            scratch=scratch,
            draft_correct=draft.correctness,
            metrics=self._metrics_payload(response),
            metadata={"steps": fields.get("steps", ""), "suspect": fields.get("suspect", "")},
        )

    def _baseline_self_refine(self, example: BenchmarkExample, answer: str, scratch: str) -> BaselineOutcome:
        result = self.signal_runner._self_refine(example, answer, scratch)
        return BaselineOutcome(
            name="self_refine_1",
            answer=result.answer,
            normalized_answer=result.normalized_answer,
            correctness=result.correctness,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            latency_s=result.latency_s,
            raw_paths=list(result.raw_paths),
        )

    def _baseline_freeform_fixed2(self, example: BenchmarkExample, answer: str, scratch: str) -> BaselineOutcome:
        attack1, _, metrics1 = self.signal_runner._challenge(example, answer, scratch)
        answer1, scratch1, _, metrics2 = self.signal_runner._revise(example, answer=answer, scratch=scratch, attack=attack1)
        attack2, _, metrics3 = self.signal_runner._challenge(example, answer1, scratch1)
        answer2, _, _, metrics4 = self.signal_runner._revise(example, answer=answer1, scratch=scratch1, attack=attack2)
        normalized = normalize_prediction(answer2, example.task_type)
        return BaselineOutcome(
            name="freeform_fixed2_same",
            answer=answer2,
            normalized_answer=normalized,
            correctness=int(normalized == example.gold_normalized),
            input_tokens=int(metrics1["input_tokens"] + metrics2["input_tokens"] + metrics3["input_tokens"] + metrics4["input_tokens"]),
            output_tokens=int(metrics1["output_tokens"] + metrics2["output_tokens"] + metrics3["output_tokens"] + metrics4["output_tokens"]),
            latency_s=float(metrics1["latency_s"] + metrics2["latency_s"] + metrics3["latency_s"] + metrics4["latency_s"]),
            raw_paths=list(metrics1["raw_paths"] + metrics2["raw_paths"] + metrics3["raw_paths"] + metrics4["raw_paths"]),
        )

    def _baseline_freeform_fixed1(self, example: BenchmarkExample, answer: str, scratch: str) -> BaselineOutcome:
        attack, _, metrics1 = self.signal_runner._challenge(example, answer, scratch)
        revised_answer, _, _, metrics2 = self.signal_runner._revise(example, answer=answer, scratch=scratch, attack=attack)
        normalized = normalize_prediction(revised_answer, example.task_type)
        return BaselineOutcome(
            name="freeform_fixed1_same",
            answer=revised_answer,
            normalized_answer=normalized,
            correctness=int(normalized == example.gold_normalized),
            input_tokens=int(metrics1["input_tokens"] + metrics2["input_tokens"]),
            output_tokens=int(metrics1["output_tokens"] + metrics2["output_tokens"]),
            latency_s=float(metrics1["latency_s"] + metrics2["latency_s"]),
            raw_paths=list(metrics1["raw_paths"] + metrics2["raw_paths"]),
        )

    def _make_action_outcome(
        self,
        example: BenchmarkExample,
        *,
        action_name: str,
        answer: str,
        scratch: str,
        draft_correct: int,
        metrics: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        execution_used: int = 0,
        execution_success: int = 0,
        execution_result: str = "",
        action_failed: int = 0,
    ) -> ActionOutcome:
        normalized = normalize_prediction(answer, example.task_type)
        correctness = int(normalized == example.gold_normalized)
        helpful = int(correctness == 1 and draft_correct == 0)
        harmful = int(correctness == 0 and draft_correct == 1)
        return ActionOutcome(
            action_name=action_name,
            answer=answer,
            normalized_answer=normalized,
            scratch=scratch,
            correctness=correctness,
            helpful=helpful,
            harmful=harmful,
            neutral=int(not helpful and not harmful),
            parse_ok=int(bool(answer)),
            action_failed=action_failed,
            execution_used=execution_used,
            execution_success=execution_success,
            execution_result=execution_result,
            input_tokens=int(metrics["input_tokens"]),
            output_tokens=int(metrics["output_tokens"]),
            latency_s=float(metrics["latency_s"]),
            raw_paths=list(metrics["raw_paths"]),
            metadata=metadata or {},
        )

    def _general_features(self, example: BenchmarkExample, answer: str, scratch: str) -> dict[str, Any]:
        question = example.question
        numbers = re.findall(r"-?\d[\d,]*(?:\.\d+)?", question)
        lower = question.lower()
        rate_unit_cues = [" per ", " each ", " every ", " mph", " km", " hour", " minute", " second", " rate", " speed", " gallon", " liter", "%", "percent"]
        comparison_cues = [" more ", " less ", " fewer ", " than ", " difference ", " left ", " remain "]
        return {
            "question_word_count": len(question.split()),
            "question_number_count": len(numbers),
            "rate_unit_cue": float(any(cue in lower for cue in rate_unit_cues)),
            "comparison_cue": float(any(cue in lower for cue in comparison_cues)),
            "draft_has_equation": float("=" in scratch),
            "draft_scratch_word_count": len(scratch.split()),
            "draft_answer_char_len": len(answer.strip()),
            "draft_answer_numeric": float(bool(extract_numeric(answer))),
        }

    def _fallback_answer(self, tagged_answer: str, raw_text: str, task_type: str, default: str = "") -> str:
        text = tagged_answer.strip() or raw_text.strip() or default
        if task_type == "numeric_open":
            numeric = extract_numeric(text)
            return numeric if numeric else default
        return text or default

    def _fallback_scratch(self, raw_text: str, default: str = "") -> str:
        stripped = re.sub(r"</?[a-zA-Z0-9_]+>", " ", raw_text)
        compact = re.sub(r"\s+", " ", stripped).strip()
        return compact[:240] if compact else default

    def _parse_yes_no(self, value: str) -> int:
        lowered = str(value).strip().lower()
        if lowered.startswith("y"):
            return 1
        if lowered.startswith("n"):
            return 0
        return 0

    def _parse_tri(self, value: str) -> int:
        lowered = str(value).strip().lower()
        if lowered.startswith("y"):
            return 1
        if lowered.startswith("n"):
            return 0
        return -1

    def _parse_int(self, value: str) -> int:
        match = re.search(r"-?\d+", str(value))
        return int(match.group(0)) if match else 0

    def _metrics_payload(self, response: dict[str, Any]) -> dict[str, Any]:
        metrics = response["metrics"]
        return {
            "input_tokens": metrics.input_tokens,
            "output_tokens": metrics.output_tokens,
            "latency_s": metrics.latency_s,
            "raw_paths": [metrics.raw_path],
        }
