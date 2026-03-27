from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from dart_research.clients.base import GenerationEnvelope, ModelClient
from dart_research.datasets.loaders import BenchmarkExample
from dart_research.evaluation.metrics import majority_vote
from dart_research.parsing.normalization import normalize_from_answer_fields, normalize_prediction, normalize_text
from dart_research.parsing.schemas import (
    CandidateOption,
    CandidateSet,
    DefenseSet,
    DraftAnswer,
    FinalAnswer,
    FreeformDevilAdvocate,
    FreeformRebuttal,
    RebuttalEntry,
    RebuttalSet,
    SelectionDecision,
    SelfRefineCritique,
    ValidationSet,
)
from dart_research.utils.io import ensure_dir, write_json
from dart_research.utils.prompts import PromptTemplate, load_prompt


PROMPT_FILES = {
    "draft_direct": "prompts/draft/direct_v1.txt",
    "draft_candidates": "prompts/draft/candidates_v2.txt",
    "adversary_alternatives": "prompts/adversary/alternatives_v2.txt",
    "adversary_persona_slot": "prompts/adversary/persona_slot_v1.txt",
    "adversary_repair": "prompts/adversary/repair_v1.txt",
    "defense": "prompts/defense/defense_v1.txt",
    "validator": "prompts/validator/validate_v2.txt",
    "rebuttal": "prompts/rebuttal/rebuttal_v1.txt",
    "final": "prompts/final/final_v1.txt",
    "final_same_context": "prompts/final/final_same_context_v1.txt",
    "final_option_fresh": "prompts/final/final_option_fresh_v1.txt",
    "final_option_same_context": "prompts/final/final_option_same_context_v1.txt",
    "select": "prompts/final/select_v1.txt",
    "self_refine_critique": "prompts/rebuttal/self_refine_critique_v1.txt",
    "self_refine_revise": "prompts/final/self_refine_revise_v1.txt",
    "freeform_counter": "prompts/adversary/freeform_counter_v1.txt",
    "freeform_rebuttal": "prompts/rebuttal/freeform_rebuttal_v1.txt",
    "freeform_final_same_context": "prompts/final/freeform_final_same_context_v1.txt",
}


@dataclass(slots=True)
class MethodResult:
    method: str
    final_answer: str
    final_normalized: str
    direct_normalized: str
    candidate_set: list[dict[str, Any]]
    stage_records: list[dict[str, Any]]
    malformed: int
    duplicates: int
    trivial: int
    kept_options: int
    candidate_coverage: int | None
    latency_s: float
    input_tokens: int
    output_tokens: int
    cost_usd: float


@dataclass(slots=True)
class CandidateArtifact:
    artifact_id: str
    kind: str
    draft: DraftAnswer
    raw_candidates: list[CandidateOption]
    kept_candidates: list[CandidateOption]
    rebuttals: list[RebuttalEntry]
    stage_records: list[dict[str, Any]]
    duplicates: int
    trivial: int
    malformed: int

    def to_payload(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "kind": self.kind,
            "draft": self.draft.model_dump(),
            "raw_candidates": [candidate.model_dump() for candidate in self.raw_candidates],
            "kept_candidates": [candidate.model_dump() for candidate in self.kept_candidates],
            "rebuttals": [entry.model_dump() for entry in self.rebuttals],
            "duplicates": self.duplicates,
            "trivial": self.trivial,
            "malformed": self.malformed,
            "stage_records": self.stage_records,
        }


class PromptBank:
    """Load prompt templates from disk once."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.prompts = {name: load_prompt(repo_root / rel_path) for name, rel_path in PROMPT_FILES.items()}

    def __getitem__(self, item: str) -> PromptTemplate:
        return self.prompts[item]


class MethodRunner:
    """Runs configured reasoning methods for one example."""

    def __init__(
        self,
        client: ModelClient,
        prompt_bank: PromptBank,
        models_cfg: dict[str, Any],
        methods_cfg: dict[str, Any],
        artifact_dir: Path | None = None,
    ):
        self.client = client
        self.prompts = prompt_bank
        self.models_cfg = models_cfg
        self.methods_cfg = methods_cfg["methods"]
        self.artifact_dir = ensure_dir(artifact_dir) if artifact_dir else None
        self._artifact_cache: dict[tuple[str, str], CandidateArtifact] = {}
        self._draft_cache: dict[str, tuple[DraftAnswer, dict[str, Any]]] = {}

    def _options_block(self, example: BenchmarkExample) -> str:
        if not example.options:
            return "N/A"
        return "\n".join(f"{item['label']}. {item['text']}" for item in example.options)

    def _local_stage(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "stage": name,
            "prompt_version": "local",
            "metrics": {
                "latency_s": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "cache_hit": True,
                "raw_path": "",
            },
            "parsed": payload,
        }

    def _generate(
        self,
        *,
        prompt_key: str,
        schema,
        model_slot: str,
        example: BenchmarkExample,
        render_kwargs: dict[str, str],
        method: str,
    ) -> GenerationEnvelope:
        prompt = self.prompts[prompt_key]
        model_cfg = self.models_cfg["models"][model_slot]
        text = prompt.render(**render_kwargs)
        return self.client.generate_json(
            model_name=model_cfg["name"],
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            prompt_text=text,
            schema=schema,
            temperature=float(model_cfg["temperature"]),
            max_output_tokens=int(model_cfg["max_output_tokens"]),
            metadata={"dataset": example.dataset, "question_id": example.question_id, "method": method},
        )

    def _record_stage(self, name: str, envelope: GenerationEnvelope) -> dict[str, Any]:
        return {
            "stage": name,
            "prompt_version": envelope.prompt_version,
            "metrics": asdict(envelope.metrics),
            "parsed": envelope.parsed.model_dump(),
        }

    def _merge_metrics(self, stages: list[dict[str, Any]]) -> tuple[float, int, int, float]:
        latency = sum(float(stage["metrics"]["latency_s"]) for stage in stages)
        input_tokens = sum(int(stage["metrics"]["input_tokens"]) for stage in stages)
        output_tokens = sum(int(stage["metrics"]["output_tokens"]) for stage in stages)
        cost = sum(float(stage["metrics"]["cost_usd"]) for stage in stages)
        return latency, input_tokens, output_tokens, cost

    def _artifact_key(self, example: BenchmarkExample, kind: str) -> tuple[str, str]:
        return example.question_id, kind

    def _artifact_path(self, example: BenchmarkExample, kind: str) -> Path | None:
        if not self.artifact_dir:
            return None
        safe_question_id = example.question_id.replace("/", "_")
        return self.artifact_dir / f"{example.dataset}_{safe_question_id}_{kind}.json"

    def _write_artifact(self, example: BenchmarkExample, artifact: CandidateArtifact) -> None:
        path = self._artifact_path(example, artifact.kind)
        if path is not None:
            write_json(path, artifact.to_payload())

    def _is_binary_yes_no(self, example: BenchmarkExample) -> bool:
        return example.task_type == "yes_no_open"

    def _candidate_coverage(self, example: BenchmarkExample, candidates: list[CandidateOption]) -> int | None:
        if not candidates:
            return None
        return int(example.gold_normalized in {candidate.normalized_answer for candidate in candidates})

    def _dedupe_candidates(self, candidates: list[CandidateOption]) -> tuple[list[CandidateOption], int]:
        """Drop duplicates by normalized answer and repeated failure mode."""
        deduped: list[CandidateOption] = []
        seen_answers: set[str] = set()
        seen_failures: set[str] = set()
        duplicates = 0
        for candidate in candidates:
            answer_key = normalize_text(candidate.normalized_answer or candidate.answer)
            failure_key = normalize_text(candidate.failure_mode)
            is_duplicate = False
            if answer_key and answer_key in seen_answers:
                is_duplicate = True
            elif failure_key and failure_key in seen_failures:
                is_duplicate = True
            if is_duplicate:
                duplicates += 1
                continue
            if answer_key:
                seen_answers.add(answer_key)
            if failure_key:
                seen_failures.add(failure_key)
            deduped.append(candidate)
        return deduped, duplicates

    def _next_option_id(self, existing_count: int) -> str:
        return chr(ord("A") + existing_count)

    def _normalize_candidates(self, candidates: list[CandidateOption], task_type: str) -> list[CandidateOption]:
        normalized: list[CandidateOption] = []
        for candidate in candidates:
            normalized_answer = normalize_from_answer_fields(candidate.answer, candidate.normalized_answer, task_type)
            normalized.append(candidate.model_copy(update={"normalized_answer": normalized_answer}))
        return normalized

    def _validation_feedback(self, validation_stages: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
        reasons: list[str] = []
        duplicate_refs: list[str] = []
        for stage in validation_stages:
            if stage.get("stage") != "validation":
                continue
            for decision in stage.get("parsed", {}).get("decisions", []):
                keep = decision.get("keep")
                if keep:
                    continue
                option_id = str(decision.get("option_id", ""))
                reason = str(decision.get("reason", "")).strip()
                duplicate_of = decision.get("duplicate_of")
                if reason:
                    reasons.append(f"{option_id}: {reason}")
                if duplicate_of:
                    duplicate_refs.append(f"{option_id}->{duplicate_of}")
        return reasons, duplicate_refs

    def _binary_candidates(self) -> list[CandidateOption]:
        return [
            CandidateOption(
                option_id="YES",
                answer="Yes",
                normalized_answer="yes",
                source="closed_label",
                failure_mode="affirmative_case",
                short_rationale="affirmative hypothesis",
            ),
            CandidateOption(
                option_id="NO",
                answer="No",
                normalized_answer="no",
                source="closed_label",
                failure_mode="negative_case",
                short_rationale="negative hypothesis",
            ),
        ]

    def _human_option_candidates(self, example: BenchmarkExample) -> list[CandidateOption]:
        return [
            CandidateOption(
                option_id=option["label"],
                answer=option["text"],
                normalized_answer=normalize_prediction(option["label"], example.task_type),
                source="human_options",
                short_rationale="provided benchmark option",
            )
            for option in example.options
        ]

    def _candidate_payload(
        self,
        candidates: list[CandidateOption],
        *,
        rebuttals: list[RebuttalEntry] | None = None,
        include_defense: bool = True,
        include_rebuttal: bool = False,
    ) -> dict[str, Any]:
        rebuttal_map = {entry.option_id: entry.model_dump() for entry in (rebuttals or [])}
        payload_candidates: list[dict[str, Any]] = []
        for candidate in candidates:
            candidate_payload = candidate.model_dump()
            if not include_defense:
                candidate_payload.pop("defense", None)
            if include_rebuttal:
                candidate_payload["rebuttal"] = rebuttal_map.get(candidate.option_id, {})
            payload_candidates.append(candidate_payload)
        return {"candidates": payload_candidates}

    def _draft(
        self,
        example: BenchmarkExample,
        method: str,
        *,
        use_shared_cache: bool = True,
        sample_tag: str | None = None,
    ) -> tuple[DraftAnswer, dict[str, Any]]:
        if use_shared_cache and example.question_id in self._draft_cache:
            return self._draft_cache[example.question_id]
        question_text = example.question
        if sample_tag is not None:
            question_text = f"{example.question}\nIndependent sample tag: {sample_tag}"
        envelope = self._generate(
            prompt_key="draft_direct",
            schema=DraftAnswer,
            model_slot="primary",
            example=example,
            render_kwargs={"question": question_text, "options_block": self._options_block(example)},
            method=method,
        )
        draft = envelope.parsed
        draft.normalized_answer = normalize_from_answer_fields(draft.answer, draft.normalized_answer, example.task_type)
        result = draft, self._record_stage("draft", envelope)
        if use_shared_cache:
            self._draft_cache[example.question_id] = result
        return result

    def _candidate_set_self(self, example: BenchmarkExample, method: str) -> tuple[list[CandidateOption], list[dict[str, Any]]]:
        if self._is_binary_yes_no(example):
            candidates = self._binary_candidates()
            return candidates, [self._local_stage("candidate_generation", {"kind": "binary_closed_labels"})]
        candidate_env = self._generate(
            prompt_key="draft_candidates",
            schema=CandidateSet,
            model_slot="cheap",
            example=example,
            render_kwargs={
                "question": example.question,
                "options_block": self._options_block(example),
                "max_candidates": str(self.methods_cfg.get(method, {}).get("max_candidates", 4)),
            },
            method=method,
        )
        candidates = candidate_env.parsed.candidates
        for candidate in candidates:
            candidate.normalized_answer = normalize_from_answer_fields(candidate.answer, candidate.normalized_answer, example.task_type)
        return candidates, [self._record_stage("candidate_generation", candidate_env)]

    def _candidate_set_adv(self, example: BenchmarkExample, draft: DraftAnswer, method: str) -> tuple[list[CandidateOption], list[dict[str, Any]]]:
        if self._is_binary_yes_no(example):
            candidates = self._binary_candidates()
            return candidates, [self._local_stage("candidate_generation", {"kind": "binary_closed_labels"})]
        personas = self.methods_cfg["dart_adv"].get("personas", [])
        candidate_env = self._generate(
            prompt_key="adversary_alternatives",
            schema=CandidateSet,
            model_slot="cheap",
            example=example,
            render_kwargs={
                "question": example.question,
                "draft_json": json.dumps(draft.model_dump(), ensure_ascii=False),
                "personas_block": "\n".join(personas),
                "options_block": self._options_block(example),
                "max_candidates": str(self.methods_cfg.get(method, {}).get("max_candidates", 4)),
            },
            method=method,
        )
        candidates = self._normalize_candidates(candidate_env.parsed.candidates, example.task_type)
        draft_candidate = CandidateOption(
            option_id="A",
            answer=draft.answer,
            normalized_answer=draft.normalized_answer,
            source="draft",
            failure_mode="original_draft",
            short_rationale="original draft hypothesis",
        )
        merged = [draft_candidate] + candidates
        return merged, [self._record_stage("adversary_generation", candidate_env)]

    def _candidate_set_adv_v2(
        self,
        example: BenchmarkExample,
        draft: DraftAnswer,
        method: str,
    ) -> tuple[list[CandidateOption], list[CandidateOption], list[dict[str, Any]], int, int, int]:
        if self._is_binary_yes_no(example):
            candidates = self._binary_candidates()
            return candidates, candidates, [self._local_stage("candidate_generation", {"kind": "binary_closed_labels"})], 0, 0, 0
        config = self.methods_cfg.get("dart_adv_v2", {})
        error_types = list(config.get("error_types", []))
        target_min_unique = int(config.get("target_min_unique", 3))
        raw_candidates: list[CandidateOption] = [
            CandidateOption(
                option_id="A",
                answer=draft.answer,
                normalized_answer=draft.normalized_answer,
                source="draft",
                persona="draft_anchor",
                failure_mode="original_draft",
                short_rationale="original draft hypothesis",
            )
        ]
        stages: list[dict[str, Any]] = []
        seen_answers: set[str] = {normalize_text(draft.normalized_answer)}
        seen_error_types: set[str] = {"original_draft"}

        for slot_index, error_type in enumerate(error_types, start=1):
            option_id = self._next_option_id(len(raw_candidates))
            envelope = self._generate(
                prompt_key="adversary_persona_slot",
                schema=CandidateSet,
                model_slot="cheap",
                example=example,
                render_kwargs={
                    "question": example.question,
                    "draft_json": json.dumps(draft.model_dump(), ensure_ascii=False),
                    "slot_option_id": option_id,
                    "error_type": error_type,
                    "forbidden_answers": ", ".join(sorted(answer for answer in seen_answers if answer)) or "none",
                    "forbidden_error_types": ", ".join(sorted(error for error in seen_error_types if error)) or "none",
                    "options_block": self._options_block(example),
                },
                method=method,
            )
            stages.append(self._record_stage(f"adversary_generation_{slot_index}", envelope))
            candidates = self._normalize_candidates(envelope.parsed.candidates, example.task_type)
            if not candidates:
                continue
            candidate = candidates[0].model_copy(
                update={
                    "option_id": option_id,
                    "source": candidates[0].source or "adversary_v2",
                    "persona": candidates[0].persona or error_type,
                    "failure_mode": candidates[0].failure_mode or error_type,
                }
            )
            raw_candidates.append(candidate)
            normalized_key = normalize_text(candidate.normalized_answer or candidate.answer)
            if normalized_key:
                seen_answers.add(normalized_key)
            seen_error_types.add(normalize_text(candidate.failure_mode or error_type))

        deduped, local_duplicates = self._dedupe_candidates(raw_candidates)
        stages.append(
            self._local_stage(
                "local_dedupe_round_1",
                {"raw_count": len(raw_candidates), "kept_after_local_dedupe": len(deduped), "duplicates_removed": local_duplicates},
            )
        )
        kept, validation_stages, model_duplicates, trivial, malformed = self._validate_candidates(
            example,
            deduped,
            method,
            permissive=True,
        )
        stages.extend(validation_stages)
        duplicate_count = local_duplicates + model_duplicates

        if len(kept) < target_min_unique:
            rejection_reasons, duplicate_refs = self._validation_feedback(validation_stages)
            repair_env = self._generate(
                prompt_key="adversary_repair",
                schema=CandidateSet,
                model_slot="cheap",
                example=example,
                render_kwargs={
                    "question": example.question,
                    "draft_json": json.dumps(draft.model_dump(), ensure_ascii=False),
                    "target_min_unique": str(target_min_unique),
                    "current_candidates_json": json.dumps(self._candidate_payload(kept or deduped, include_defense=False), ensure_ascii=False),
                    "forbidden_answers": ", ".join(sorted(normalize_text(candidate.normalized_answer or candidate.answer) for candidate in raw_candidates if (candidate.normalized_answer or candidate.answer))) or "none",
                    "used_error_types": ", ".join(sorted(normalize_text(candidate.failure_mode) for candidate in raw_candidates if candidate.failure_mode)) or "none",
                    "rejected_reasons_block": "\n".join(rejection_reasons) or "none",
                    "duplicate_refs_block": "\n".join(duplicate_refs) or "none",
                    "options_block": self._options_block(example),
                },
                method=method,
            )
            stages.append(self._record_stage("adversary_repair", repair_env))
            repair_candidates = self._normalize_candidates(repair_env.parsed.candidates, example.task_type)
            for candidate in repair_candidates:
                option_id = self._next_option_id(len(raw_candidates))
                raw_candidates.append(
                    candidate.model_copy(
                        update={
                            "option_id": option_id,
                            "source": candidate.source or "adversary_v2_repair",
                            "persona": candidate.persona or "repair_pass",
                        }
                    )
                )
            deduped, repair_duplicates = self._dedupe_candidates(raw_candidates)
            stages.append(
                self._local_stage(
                    "local_dedupe_round_2",
                    {"raw_count": len(raw_candidates), "kept_after_local_dedupe": len(deduped), "duplicates_removed": repair_duplicates},
                )
            )
            kept, validation_stages, model_duplicates, trivial, malformed = self._validate_candidates(
                example,
                deduped,
                method,
                permissive=True,
            )
            stages.extend(validation_stages)
            duplicate_count = repair_duplicates + model_duplicates

        return raw_candidates, kept, stages, duplicate_count, trivial, malformed

    def _validate_candidates(
        self,
        example: BenchmarkExample,
        candidates: list[CandidateOption],
        method: str,
        *,
        permissive: bool = False,
    ) -> tuple[list[CandidateOption], list[dict[str, Any]], int, int, int]:
        if not candidates:
            return [], [self._local_stage("validation", {"kept": 0})], 0, 0, 0
        validation_env = self._generate(
            prompt_key="validator",
            schema=ValidationSet,
            model_slot="validator",
            example=example,
            render_kwargs={"question": example.question, "candidates_json": json.dumps(self._candidate_payload(candidates, include_defense=False), ensure_ascii=False)},
            method=method,
        )
        decisions = {item.option_id: item for item in validation_env.parsed.decisions}
        kept = [candidate for candidate in candidates if decisions.get(candidate.option_id) and decisions[candidate.option_id].keep]
        duplicates = sum(1 for item in validation_env.parsed.decisions if item.duplicate_of)
        trivial = sum(1 for item in validation_env.parsed.decisions if "trivial" in item.reason.lower() or "silly" in item.reason.lower())
        malformed = sum(1 for item in validation_env.parsed.decisions if "malformed" in item.reason.lower())
        stages = [self._record_stage("validation", validation_env)]
        if permissive:
            recovered: list[str] = []
            duplicate_ids = {item.option_id for item in validation_env.parsed.decisions if item.duplicate_of}
            for candidate in candidates:
                decision = decisions.get(candidate.option_id)
                if decision is None or decision.keep or candidate in kept:
                    continue
                reason = decision.reason.lower()
                if candidate.option_id in duplicate_ids:
                    continue
                if "malformed" in reason or "trivial" in reason or "silly" in reason or "ambiguous" in reason or "non-actionable" in reason:
                    continue
                kept.append(candidate)
                recovered.append(candidate.option_id)
            if recovered:
                stages.append(self._local_stage("validation_permissive_keep", {"recovered_option_ids": recovered}))
        if not kept and candidates:
            kept = candidates[:1]
            stages.append(self._local_stage("validation_fallback", {"reason": "kept first candidate after over-filtering"}))
        return kept, stages, duplicates, trivial, malformed

    def _attach_defenses(self, example: BenchmarkExample, candidates: list[CandidateOption], method: str) -> tuple[list[CandidateOption], list[dict[str, Any]]]:
        if not candidates:
            return [], [self._local_stage("defense", {"count": 0})]
        defense_env = self._generate(
            prompt_key="defense",
            schema=DefenseSet,
            model_slot="cheap",
            example=example,
            render_kwargs={"question": example.question, "candidates_json": json.dumps(self._candidate_payload(candidates, include_defense=False), ensure_ascii=False)},
            method=method,
        )
        defense_map = {item.option_id: item.defense for item in defense_env.parsed.defenses}
        defended = [candidate.model_copy(update={"defense": defense_map.get(candidate.option_id, "")}) for candidate in candidates]
        return defended, [self._record_stage("defense", defense_env)]

    def _run_rebuttal(self, example: BenchmarkExample, candidates: list[CandidateOption], method: str) -> tuple[list[RebuttalEntry], list[dict[str, Any]]]:
        if not candidates:
            return [], [self._local_stage("rebuttal", {"count": 0})]
        rebuttal_env = self._generate(
            prompt_key="rebuttal",
            schema=RebuttalSet,
            model_slot="validator",
            example=example,
            render_kwargs={
                "question": example.question,
                "candidates_json": json.dumps(self._candidate_payload(candidates, include_defense=True), ensure_ascii=False),
            },
            method=method,
        )
        return rebuttal_env.parsed.entries, [self._record_stage("rebuttal", rebuttal_env)]

    def _build_shared_artifact(self, example: BenchmarkExample, kind: str, method: str) -> CandidateArtifact:
        cache_key = self._artifact_key(example, kind)
        if cache_key in self._artifact_cache:
            return self._artifact_cache[cache_key]

        draft, draft_stage = self._draft(example, method)
        stages = [draft_stage]

        if kind == "binary":
            raw_candidates = self._binary_candidates()
            kept_base = raw_candidates
            stages.append(self._local_stage("candidate_generation", {"kind": "binary_closed_labels", "count": len(raw_candidates)}))
            duplicates = 0
            trivial = 0
            malformed = 0
        elif kind == "human_options":
            raw_candidates = self._human_option_candidates(example)
            kept_base = raw_candidates
            stages.append(self._local_stage("candidate_generation", {"kind": "human_options", "count": len(raw_candidates)}))
            duplicates = 0
            trivial = 0
            malformed = 0
        elif kind == "self":
            raw_candidates, generation_stages = self._candidate_set_self(example, method)
            stages.extend(generation_stages)
            deduped, local_duplicates = self._dedupe_candidates(raw_candidates)
            stages.append(
                self._local_stage(
                    "local_dedupe",
                    {"raw_count": len(raw_candidates), "kept_after_local_dedupe": len(deduped), "duplicates_removed": local_duplicates},
                )
            )
            kept_base, validation_stages, model_duplicates, trivial, malformed = self._validate_candidates(example, deduped, method)
            stages.extend(validation_stages)
            duplicates = local_duplicates + model_duplicates
        elif kind == "adv":
            raw_candidates, generation_stages = self._candidate_set_adv(example, draft, method)
            stages.extend(generation_stages)
            deduped, local_duplicates = self._dedupe_candidates(raw_candidates)
            stages.append(
                self._local_stage(
                    "local_dedupe",
                    {"raw_count": len(raw_candidates), "kept_after_local_dedupe": len(deduped), "duplicates_removed": local_duplicates},
                )
            )
            kept_base, validation_stages, model_duplicates, trivial, malformed = self._validate_candidates(example, deduped, method)
            stages.extend(validation_stages)
            duplicates = local_duplicates + model_duplicates
        elif kind == "adv_v2":
            raw_candidates, kept_base, generation_stages, duplicates, trivial, malformed = self._candidate_set_adv_v2(example, draft, method)
            stages.extend(generation_stages)
        else:
            raise ValueError(f"Unknown artifact kind: {kind}")

        defended, defense_stages = self._attach_defenses(example, kept_base, method)
        rebuttals, rebuttal_stages = self._run_rebuttal(example, defended, method)
        stages.extend(defense_stages + rebuttal_stages)

        artifact = CandidateArtifact(
            artifact_id=f"{example.dataset}:{example.question_id}:{kind}",
            kind=kind,
            draft=draft,
            raw_candidates=raw_candidates,
            kept_candidates=defended,
            rebuttals=rebuttals,
            stage_records=stages,
            duplicates=duplicates,
            trivial=trivial,
            malformed=malformed,
        )
        self._artifact_cache[cache_key] = artifact
        self._write_artifact(example, artifact)
        return artifact

    def _binary_artifact(self, example: BenchmarkExample, method: str) -> CandidateArtifact:
        return self._build_shared_artifact(example, "binary", method)

    def _self_artifact(self, example: BenchmarkExample, method: str) -> CandidateArtifact:
        if self._is_binary_yes_no(example):
            return self._binary_artifact(example, method)
        if example.options:
            return self._build_shared_artifact(example, "human_options", method)
        return self._build_shared_artifact(example, "self", method)

    def _adv_artifact(self, example: BenchmarkExample, method: str) -> CandidateArtifact:
        if self._is_binary_yes_no(example):
            return self._binary_artifact(example, method)
        if example.options:
            return self._build_shared_artifact(example, "human_options", method)
        return self._build_shared_artifact(example, "adv", method)

    def _adv_artifact_v2(self, example: BenchmarkExample, method: str) -> CandidateArtifact:
        if self._is_binary_yes_no(example):
            return self._binary_artifact(example, method)
        if example.options:
            return self._build_shared_artifact(example, "human_options", method)
        return self._build_shared_artifact(example, "adv_v2", method)

    def _freeform_summary(self, rebuttal: FreeformRebuttal) -> str:
        return "\n".join(
            [
                f"accepted_points: {', '.join(rebuttal.accepted_points)}",
                f"rejected_points: {', '.join(rebuttal.rejected_points)}",
                f"decisive_constraint: {rebuttal.decisive_constraint}",
                f"revised_plan: {rebuttal.revised_plan}",
            ]
        )

    def _select_candidate(
        self,
        example: BenchmarkExample,
        candidates: list[CandidateOption],
        method: str,
        *,
        include_defense: bool = False,
        rebuttals: list[RebuttalEntry] | None = None,
    ) -> tuple[CandidateOption, list[dict[str, Any]]]:
        if not candidates:
            raise ValueError(f"{method} has no candidates for selection.")
        select_env = self._generate(
            prompt_key="select",
            schema=SelectionDecision,
            model_slot="validator",
            example=example,
            render_kwargs={
                "question": example.question,
                "candidates_json": json.dumps(
                    self._candidate_payload(
                        candidates,
                        rebuttals=rebuttals,
                        include_defense=include_defense,
                        include_rebuttal=rebuttals is not None,
                    ),
                    ensure_ascii=False,
                ),
            },
            method=method,
        )
        choice = select_env.parsed.option_id
        selected = next((candidate for candidate in candidates if candidate.option_id == choice), candidates[0])
        return selected, [self._record_stage("selection", select_env)]

    def _rebuttal_summary(self, artifact: CandidateArtifact) -> str:
        rebuttal_map = {entry.option_id: entry for entry in artifact.rebuttals}
        lines = []
        for candidate in artifact.kept_candidates:
            rebuttal = rebuttal_map.get(candidate.option_id)
            if rebuttal is None:
                lines.append(f"{candidate.option_id}: {candidate.answer} | defense={candidate.defense}")
                continue
            lines.append(
                f"{candidate.option_id}: {candidate.answer} | defense={candidate.defense} | "
                f"likely_failure={rebuttal.likely_failure} | decisive_test={rebuttal.decisive_test_or_constraint} | "
                f"verdict={rebuttal.verdict_for_now}"
            )
        return "\n".join(lines)

    def _final_regeneration(
        self,
        example: BenchmarkExample,
        artifact: CandidateArtifact,
        method: str,
    ) -> tuple[FinalAnswer, list[dict[str, Any]]]:
        final_env = self._generate(
            prompt_key="final",
            schema=FinalAnswer,
            model_slot="primary",
            example=example,
            render_kwargs={
                "question": example.question,
                "constraints_block": "\n".join(artifact.draft.constraints),
                "rebuttal_summary": self._rebuttal_summary(artifact),
                "options_block": self._options_block(example),
            },
            method=method,
        )
        final = final_env.parsed
        final.normalized_answer = normalize_from_answer_fields(final.answer, final.normalized_answer, example.task_type)
        return final, [self._record_stage("final", final_env)]

    def _final_same_context(
        self,
        example: BenchmarkExample,
        artifact: CandidateArtifact,
        method: str,
    ) -> tuple[FinalAnswer, list[dict[str, Any]]]:
        final_env = self._generate(
            prompt_key="final_same_context",
            schema=FinalAnswer,
            model_slot="primary",
            example=example,
            render_kwargs={
                "question": example.question,
                "candidate_artifact_json": json.dumps(artifact.to_payload(), ensure_ascii=False),
                "options_block": self._options_block(example),
            },
            method=method,
        )
        final = final_env.parsed
        final.normalized_answer = normalize_from_answer_fields(final.answer, final.normalized_answer, example.task_type)
        return final, [self._record_stage("final_same_context", final_env)]

    def _final_option_fresh(
        self,
        example: BenchmarkExample,
        artifact: CandidateArtifact,
        method: str,
    ) -> tuple[CandidateOption, list[dict[str, Any]]]:
        final_env = self._generate(
            prompt_key="final_option_fresh",
            schema=SelectionDecision,
            model_slot="primary",
            example=example,
            render_kwargs={
                "question": example.question,
                "constraints_block": "\n".join(artifact.draft.constraints),
                "rebuttal_summary": self._rebuttal_summary(artifact),
                "options_block": self._options_block(example),
            },
            method=method,
        )
        choice = final_env.parsed.option_id
        selected = next((candidate for candidate in artifact.kept_candidates if candidate.option_id == choice), artifact.kept_candidates[0])
        return selected, [self._record_stage("final_option_fresh", final_env)]

    def _final_option_same_context(
        self,
        example: BenchmarkExample,
        artifact: CandidateArtifact,
        method: str,
    ) -> tuple[CandidateOption, list[dict[str, Any]]]:
        final_env = self._generate(
            prompt_key="final_option_same_context",
            schema=SelectionDecision,
            model_slot="primary",
            example=example,
            render_kwargs={
                "question": example.question,
                "candidate_artifact_json": json.dumps(artifact.to_payload(), ensure_ascii=False),
                "options_block": self._options_block(example),
            },
            method=method,
        )
        choice = final_env.parsed.option_id
        selected = next((candidate for candidate in artifact.kept_candidates if candidate.option_id == choice), artifact.kept_candidates[0])
        return selected, [self._record_stage("final_option_same_context", final_env)]

    def _build_result_from_selection(
        self,
        method: str,
        example: BenchmarkExample,
        artifact: CandidateArtifact,
        selected: CandidateOption,
        extra_stages: list[dict[str, Any]],
    ) -> MethodResult:
        stages = artifact.stage_records + extra_stages
        latency, input_tokens, output_tokens, cost = self._merge_metrics(stages)
        return MethodResult(
            method=method,
            final_answer=selected.answer,
            final_normalized=selected.normalized_answer,
            direct_normalized=artifact.draft.normalized_answer,
            candidate_set=[candidate.model_dump() for candidate in artifact.raw_candidates],
            stage_records=stages,
            malformed=artifact.malformed,
            duplicates=artifact.duplicates,
            trivial=artifact.trivial,
            kept_options=len(artifact.kept_candidates),
            candidate_coverage=self._candidate_coverage(example, artifact.raw_candidates),
            latency_s=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def _build_result_from_final(
        self,
        method: str,
        example: BenchmarkExample,
        artifact: CandidateArtifact,
        final_answer: str,
        final_normalized: str,
        extra_stages: list[dict[str, Any]],
    ) -> MethodResult:
        stages = artifact.stage_records + extra_stages
        latency, input_tokens, output_tokens, cost = self._merge_metrics(stages)
        return MethodResult(
            method=method,
            final_answer=final_answer,
            final_normalized=final_normalized,
            direct_normalized=artifact.draft.normalized_answer,
            candidate_set=[candidate.model_dump() for candidate in artifact.raw_candidates],
            stage_records=stages,
            malformed=artifact.malformed,
            duplicates=artifact.duplicates,
            trivial=artifact.trivial,
            kept_options=len(artifact.kept_candidates),
            candidate_coverage=self._candidate_coverage(example, artifact.raw_candidates),
            latency_s=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def direct_cot(self, example: BenchmarkExample) -> MethodResult:
        draft, draft_stage = self._draft(example, "direct_cot")
        latency, input_tokens, output_tokens, cost = self._merge_metrics([draft_stage])
        return MethodResult(
            method="direct_cot",
            final_answer=draft.answer,
            final_normalized=draft.normalized_answer,
            direct_normalized=draft.normalized_answer,
            candidate_set=[],
            stage_records=[draft_stage],
            malformed=0,
            duplicates=0,
            trivial=0,
            kept_options=0,
            candidate_coverage=None,
            latency_s=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def self_consistency_5(self, example: BenchmarkExample) -> MethodResult:
        sample_count = int(self.methods_cfg["self_consistency_5"]["samples"])
        stages: list[dict[str, Any]] = []
        answers: list[str] = []
        first_answer = ""
        direct_normalized = ""
        for sample_index in range(sample_count):
            draft, stage = self._draft(
                example,
                f"self_consistency_5_{sample_index}",
                use_shared_cache=False,
                sample_tag=str(sample_index + 1),
            )
            if sample_index == 0:
                direct_normalized = draft.normalized_answer
                first_answer = draft.answer
            answers.append(draft.normalized_answer)
            stages.append(stage)
        majority = majority_vote(answers)
        latency, input_tokens, output_tokens, cost = self._merge_metrics(stages)
        return MethodResult(
            method="self_consistency_5",
            final_answer=first_answer if majority == direct_normalized else majority,
            final_normalized=majority,
            direct_normalized=direct_normalized or majority,
            candidate_set=[],
            stage_records=stages,
            malformed=0,
            duplicates=0,
            trivial=0,
            kept_options=0,
            candidate_coverage=None,
            latency_s=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def self_refine_1(self, example: BenchmarkExample) -> MethodResult:
        draft, draft_stage = self._draft(example, "self_refine_1")
        critique_env = self._generate(
            prompt_key="self_refine_critique",
            schema=SelfRefineCritique,
            model_slot="validator",
            example=example,
            render_kwargs={
                "question": example.question,
                "draft_json": json.dumps(draft.model_dump(), ensure_ascii=False),
                "options_block": self._options_block(example),
            },
            method="self_refine_1",
        )
        revise_env = self._generate(
            prompt_key="self_refine_revise",
            schema=FinalAnswer,
            model_slot="primary",
            example=example,
            render_kwargs={
                "question": example.question,
                "draft_json": json.dumps(draft.model_dump(), ensure_ascii=False),
                "critique_json": json.dumps(critique_env.parsed.model_dump(), ensure_ascii=False),
                "options_block": self._options_block(example),
            },
            method="self_refine_1",
        )
        final = revise_env.parsed
        final.normalized_answer = normalize_from_answer_fields(final.answer, final.normalized_answer, example.task_type)
        stages = [draft_stage, self._record_stage("critique", critique_env), self._record_stage("revise", revise_env)]
        latency, input_tokens, output_tokens, cost = self._merge_metrics(stages)
        return MethodResult(
            method="self_refine_1",
            final_answer=final.answer,
            final_normalized=final.normalized_answer,
            direct_normalized=draft.normalized_answer,
            candidate_set=[],
            stage_records=stages,
            malformed=0,
            duplicates=0,
            trivial=0,
            kept_options=0,
            candidate_coverage=None,
            latency_s=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def self_refine_2_budgetmatched(self, example: BenchmarkExample) -> MethodResult:
        draft, draft_stage = self._draft(example, "self_refine_2_budgetmatched")
        critique1_env = self._generate(
            prompt_key="self_refine_critique",
            schema=SelfRefineCritique,
            model_slot="validator",
            example=example,
            render_kwargs={
                "question": example.question,
                "draft_json": json.dumps(draft.model_dump(), ensure_ascii=False),
                "options_block": self._options_block(example),
            },
            method="self_refine_2_budgetmatched",
        )
        revise1_env = self._generate(
            prompt_key="self_refine_revise",
            schema=FinalAnswer,
            model_slot="primary",
            example=example,
            render_kwargs={
                "question": example.question,
                "draft_json": json.dumps(draft.model_dump(), ensure_ascii=False),
                "critique_json": json.dumps(critique1_env.parsed.model_dump(), ensure_ascii=False),
                "options_block": self._options_block(example),
            },
            method="self_refine_2_budgetmatched",
        )
        revise1 = revise1_env.parsed
        revise1.normalized_answer = normalize_from_answer_fields(revise1.answer, revise1.normalized_answer, example.task_type)
        revised_draft = DraftAnswer(
            answer=revise1.answer,
            normalized_answer=revise1.normalized_answer,
            constraints=draft.constraints,
            confidence=revise1.confidence,
        )
        critique2_env = self._generate(
            prompt_key="self_refine_critique",
            schema=SelfRefineCritique,
            model_slot="validator",
            example=example,
            render_kwargs={
                "question": example.question,
                "draft_json": json.dumps(revised_draft.model_dump(), ensure_ascii=False),
                "options_block": self._options_block(example),
            },
            method="self_refine_2_budgetmatched",
        )
        revise2_env = self._generate(
            prompt_key="self_refine_revise",
            schema=FinalAnswer,
            model_slot="primary",
            example=example,
            render_kwargs={
                "question": example.question,
                "draft_json": json.dumps(revised_draft.model_dump(), ensure_ascii=False),
                "critique_json": json.dumps(critique2_env.parsed.model_dump(), ensure_ascii=False),
                "options_block": self._options_block(example),
            },
            method="self_refine_2_budgetmatched",
        )
        final = revise2_env.parsed
        final.normalized_answer = normalize_from_answer_fields(final.answer, final.normalized_answer, example.task_type)
        stages = [
            draft_stage,
            self._record_stage("critique_round_1", critique1_env),
            self._record_stage("revise_round_1", revise1_env),
            self._record_stage("critique_round_2", critique2_env),
            self._record_stage("revise_round_2", revise2_env),
        ]
        latency, input_tokens, output_tokens, cost = self._merge_metrics(stages)
        return MethodResult(
            method="self_refine_2_budgetmatched",
            final_answer=final.answer,
            final_normalized=final.normalized_answer,
            direct_normalized=draft.normalized_answer,
            candidate_set=[],
            stage_records=stages,
            malformed=0,
            duplicates=0,
            trivial=0,
            kept_options=0,
            candidate_coverage=None,
            latency_s=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def freeform_devil_advocate_fresh(self, example: BenchmarkExample) -> MethodResult:
        draft, draft_stage = self._draft(example, "freeform_devil_advocate_fresh")
        counter_env = self._generate(
            prompt_key="freeform_counter",
            schema=FreeformDevilAdvocate,
            model_slot="cheap",
            example=example,
            render_kwargs={
                "question": example.question,
                "draft_json": json.dumps(draft.model_dump(), ensure_ascii=False),
                "options_block": self._options_block(example),
            },
            method="freeform_devil_advocate_fresh",
        )
        rebuttal_env = self._generate(
            prompt_key="freeform_rebuttal",
            schema=FreeformRebuttal,
            model_slot="validator",
            example=example,
            render_kwargs={
                "question": example.question,
                "draft_json": json.dumps(draft.model_dump(), ensure_ascii=False),
                "counter_json": json.dumps(counter_env.parsed.model_dump(), ensure_ascii=False),
                "options_block": self._options_block(example),
            },
            method="freeform_devil_advocate_fresh",
        )
        rebuttal_summary = self._freeform_summary(rebuttal_env.parsed)
        final_env = self._generate(
            prompt_key="final",
            schema=FinalAnswer,
            model_slot="primary",
            example=example,
            render_kwargs={
                "question": example.question,
                "constraints_block": "\n".join(draft.constraints),
                "rebuttal_summary": rebuttal_summary,
                "options_block": self._options_block(example),
            },
            method="freeform_devil_advocate_fresh",
        )
        final = final_env.parsed
        final.normalized_answer = normalize_from_answer_fields(final.answer, final.normalized_answer, example.task_type)
        stages = [
            draft_stage,
            self._record_stage("freeform_counter", counter_env),
            self._record_stage("freeform_rebuttal", rebuttal_env),
            self._record_stage("final", final_env),
        ]
        latency, input_tokens, output_tokens, cost = self._merge_metrics(stages)
        return MethodResult(
            method="freeform_devil_advocate_fresh",
            final_answer=final.answer,
            final_normalized=final.normalized_answer,
            direct_normalized=draft.normalized_answer,
            candidate_set=[],
            stage_records=stages,
            malformed=0,
            duplicates=0,
            trivial=0,
            kept_options=0,
            candidate_coverage=None,
            latency_s=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def freeform_devil_advocate_same(self, example: BenchmarkExample) -> MethodResult:
        draft, draft_stage = self._draft(example, "freeform_devil_advocate_same")
        counter_env = self._generate(
            prompt_key="freeform_counter",
            schema=FreeformDevilAdvocate,
            model_slot="cheap",
            example=example,
            render_kwargs={
                "question": example.question,
                "draft_json": json.dumps(draft.model_dump(), ensure_ascii=False),
                "options_block": self._options_block(example),
            },
            method="freeform_devil_advocate_same",
        )
        rebuttal_env = self._generate(
            prompt_key="freeform_rebuttal",
            schema=FreeformRebuttal,
            model_slot="validator",
            example=example,
            render_kwargs={
                "question": example.question,
                "draft_json": json.dumps(draft.model_dump(), ensure_ascii=False),
                "counter_json": json.dumps(counter_env.parsed.model_dump(), ensure_ascii=False),
                "options_block": self._options_block(example),
            },
            method="freeform_devil_advocate_same",
        )
        final_env = self._generate(
            prompt_key="freeform_final_same_context",
            schema=FinalAnswer,
            model_slot="primary",
            example=example,
            render_kwargs={
                "question": example.question,
                "draft_json": json.dumps(draft.model_dump(), ensure_ascii=False),
                "counter_json": json.dumps(counter_env.parsed.model_dump(), ensure_ascii=False),
                "rebuttal_json": json.dumps(rebuttal_env.parsed.model_dump(), ensure_ascii=False),
                "rebuttal_summary": self._freeform_summary(rebuttal_env.parsed),
                "options_block": self._options_block(example),
            },
            method="freeform_devil_advocate_same",
        )
        final = final_env.parsed
        final.normalized_answer = normalize_from_answer_fields(final.answer, final.normalized_answer, example.task_type)
        stages = [
            draft_stage,
            self._record_stage("freeform_counter", counter_env),
            self._record_stage("freeform_rebuttal", rebuttal_env),
            self._record_stage("freeform_final_same_context", final_env),
        ]
        latency, input_tokens, output_tokens, cost = self._merge_metrics(stages)
        return MethodResult(
            method="freeform_devil_advocate_same",
            final_answer=final.answer,
            final_normalized=final.normalized_answer,
            direct_normalized=draft.normalized_answer,
            candidate_set=[],
            stage_records=stages,
            malformed=0,
            duplicates=0,
            trivial=0,
            kept_options=0,
            candidate_coverage=None,
            latency_s=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def mc_select_only(self, example: BenchmarkExample) -> MethodResult:
        if example.options:
            candidates = self._human_option_candidates(example)
            draft, draft_stage = self._draft(example, "mc_select_only")
            selected, selection_stages = self._select_candidate(example, candidates, "mc_select_only", include_defense=False)
            stages = [draft_stage] + selection_stages
            latency, input_tokens, output_tokens, cost = self._merge_metrics(stages)
            return MethodResult(
                method="mc_select_only",
                final_answer=selected.answer,
                final_normalized=selected.normalized_answer,
                direct_normalized=draft.normalized_answer,
                candidate_set=[candidate.model_dump() for candidate in candidates],
                stage_records=stages,
                malformed=0,
                duplicates=0,
                trivial=0,
                kept_options=len(candidates),
                candidate_coverage=self._candidate_coverage(example, candidates),
                latency_s=latency,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
            )
        artifact = self._self_artifact(example, "mc_select_only")
        selected, selection_stages = self._select_candidate(example, artifact.kept_candidates, "mc_select_only", include_defense=False)
        return self._build_result_from_selection("mc_select_only", example, artifact, selected, selection_stages)

    def dart_self(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._self_artifact(example, "dart_self")
        if example.options:
            selected, final_stages = self._final_option_fresh(example, artifact, "dart_self")
            return self._build_result_from_selection("dart_self", example, artifact, selected, final_stages)
        final, final_stages = self._final_regeneration(example, artifact, "dart_self")
        return self._build_result_from_final("dart_self", example, artifact, final.answer, final.normalized_answer, final_stages)

    def dart_adv(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._adv_artifact(example, "dart_adv")
        if example.options:
            selected, final_stages = self._final_option_fresh(example, artifact, "dart_adv")
            return self._build_result_from_selection("dart_adv", example, artifact, selected, final_stages)
        final, final_stages = self._final_regeneration(example, artifact, "dart_adv")
        return self._build_result_from_final("dart_adv", example, artifact, final.answer, final.normalized_answer, final_stages)

    def dart_human_options(self, example: BenchmarkExample) -> MethodResult:
        if not example.options:
            raise ValueError("dart_human_options requires a native multiple-choice example.")
        artifact = self._build_shared_artifact(example, "human_options", "dart_human_options")
        selected, final_stages = self._final_option_fresh(example, artifact, "dart_human_options")
        return self._build_result_from_selection("dart_human_options", example, artifact, selected, final_stages)

    def mc_select_only_binary(self, example: BenchmarkExample) -> MethodResult:
        if not self._is_binary_yes_no(example):
            raise ValueError("mc_select_only_binary requires a yes/no example.")
        draft, draft_stage = self._draft(example, "mc_select_only_binary")
        candidates = self._binary_candidates()
        selected, selection_stages = self._select_candidate(example, candidates, "mc_select_only_binary", include_defense=False)
        stages = [draft_stage] + selection_stages
        latency, input_tokens, output_tokens, cost = self._merge_metrics(stages)
        return MethodResult(
            method="mc_select_only_binary",
            final_answer=selected.answer,
            final_normalized=selected.normalized_answer,
            direct_normalized=draft.normalized_answer,
            candidate_set=[candidate.model_dump() for candidate in candidates],
            stage_records=stages,
            malformed=0,
            duplicates=0,
            trivial=0,
            kept_options=len(candidates),
            candidate_coverage=self._candidate_coverage(example, candidates),
            latency_s=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def dart_adv_binary_fresh(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._binary_artifact(example, "dart_adv_binary_fresh")
        final, final_stages = self._final_regeneration(example, artifact, "dart_adv_binary_fresh")
        return self._build_result_from_final(
            "dart_adv_binary_fresh",
            example,
            artifact,
            final.answer,
            final.normalized_answer,
            final_stages,
        )

    def dart_self_binary(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._binary_artifact(example, "dart_self_binary")
        final, final_stages = self._final_regeneration(example, artifact, "dart_self_binary")
        return self._build_result_from_final(
            "dart_self_binary",
            example,
            artifact,
            final.answer,
            final.normalized_answer,
            final_stages,
        )

    def mc_select_only_shared_candidates(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._adv_artifact(example, "mc_select_only_shared_candidates")
        selected, selection_stages = self._select_candidate(
            example,
            artifact.kept_candidates,
            "mc_select_only_shared_candidates",
            include_defense=False,
        )
        return self._build_result_from_selection("mc_select_only_shared_candidates", example, artifact, selected, selection_stages)

    def dart_adv_fresh(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._adv_artifact(example, "dart_adv_fresh")
        final, final_stages = self._final_regeneration(example, artifact, "dart_adv_fresh")
        return self._build_result_from_final("dart_adv_fresh", example, artifact, final.answer, final.normalized_answer, final_stages)

    def dart_adv_same(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._adv_artifact(example, "dart_adv_same")
        final, final_stages = self._final_same_context(example, artifact, "dart_adv_same")
        return self._build_result_from_final("dart_adv_same", example, artifact, final.answer, final.normalized_answer, final_stages)

    def dart_adv_same_v1(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._adv_artifact(example, "dart_adv_same_v1")
        final, final_stages = self._final_same_context(example, artifact, "dart_adv_same_v1")
        return self._build_result_from_final("dart_adv_same_v1", example, artifact, final.answer, final.normalized_answer, final_stages)

    def adv_select_only_shared_v2(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._adv_artifact_v2(example, "adv_select_only_shared_v2")
        selected, selection_stages = self._select_candidate(example, artifact.kept_candidates, "adv_select_only_shared_v2", include_defense=False)
        return self._build_result_from_selection("adv_select_only_shared_v2", example, artifact, selected, selection_stages)

    def adv_rebuttal_then_select_shared_v2(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._adv_artifact_v2(example, "adv_rebuttal_then_select_shared_v2")
        selected, selection_stages = self._select_candidate(
            example,
            artifact.kept_candidates,
            "adv_rebuttal_then_select_shared_v2",
            include_defense=True,
            rebuttals=artifact.rebuttals,
        )
        return self._build_result_from_selection("adv_rebuttal_then_select_shared_v2", example, artifact, selected, selection_stages)

    def dart_adv_same_v2(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._adv_artifact_v2(example, "dart_adv_same_v2")
        final, final_stages = self._final_same_context(example, artifact, "dart_adv_same_v2")
        return self._build_result_from_final("dart_adv_same_v2", example, artifact, final.answer, final.normalized_answer, final_stages)

    def adv_select_only_shared(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._adv_artifact(example, "adv_select_only_shared")
        selected, selection_stages = self._select_candidate(example, artifact.kept_candidates, "adv_select_only_shared", include_defense=False)
        return self._build_result_from_selection("adv_select_only_shared", example, artifact, selected, selection_stages)

    def adv_rebuttal_then_select_shared(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._adv_artifact(example, "adv_rebuttal_then_select_shared")
        selected, selection_stages = self._select_candidate(
            example,
            artifact.kept_candidates,
            "adv_rebuttal_then_select_shared",
            include_defense=True,
            rebuttals=artifact.rebuttals,
        )
        return self._build_result_from_selection("adv_rebuttal_then_select_shared", example, artifact, selected, selection_stages)

    def adv_rebuttal_then_same_context_final(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._adv_artifact(example, "adv_rebuttal_then_same_context_final")
        final, final_stages = self._final_same_context(example, artifact, "adv_rebuttal_then_same_context_final")
        return self._build_result_from_final(
            "adv_rebuttal_then_same_context_final",
            example,
            artifact,
            final.answer,
            final.normalized_answer,
            final_stages,
        )

    def adv_rebuttal_then_fresh_context_final(self, example: BenchmarkExample) -> MethodResult:
        artifact = self._adv_artifact(example, "adv_rebuttal_then_fresh_context_final")
        final, final_stages = self._final_regeneration(example, artifact, "adv_rebuttal_then_fresh_context_final")
        return self._build_result_from_final(
            "adv_rebuttal_then_fresh_context_final",
            example,
            artifact,
            final.answer,
            final.normalized_answer,
            final_stages,
        )

    def mc_select_only_human_options(self, example: BenchmarkExample) -> MethodResult:
        if not example.options:
            raise ValueError("mc_select_only_human_options requires a native multiple-choice example.")
        draft, draft_stage = self._draft(example, "mc_select_only_human_options")
        candidates = self._human_option_candidates(example)
        selected, selection_stages = self._select_candidate(example, candidates, "mc_select_only_human_options", include_defense=False)
        stages = [draft_stage] + selection_stages
        latency, input_tokens, output_tokens, cost = self._merge_metrics(stages)
        return MethodResult(
            method="mc_select_only_human_options",
            final_answer=selected.answer,
            final_normalized=selected.normalized_answer,
            direct_normalized=draft.normalized_answer,
            candidate_set=[candidate.model_dump() for candidate in candidates],
            stage_records=stages,
            malformed=0,
            duplicates=0,
            trivial=0,
            kept_options=len(candidates),
            candidate_coverage=self._candidate_coverage(example, candidates),
            latency_s=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def dart_human_defense_select(self, example: BenchmarkExample) -> MethodResult:
        if not example.options:
            raise ValueError("dart_human_defense_select requires a native multiple-choice example.")
        draft, draft_stage = self._draft(example, "dart_human_defense_select")
        candidates = self._human_option_candidates(example)
        defended, defense_stages = self._attach_defenses(example, candidates, "dart_human_defense_select")
        selected, selection_stages = self._select_candidate(example, defended, "dart_human_defense_select", include_defense=True)
        stages = [draft_stage] + defense_stages + selection_stages
        latency, input_tokens, output_tokens, cost = self._merge_metrics(stages)
        return MethodResult(
            method="dart_human_defense_select",
            final_answer=selected.answer,
            final_normalized=selected.normalized_answer,
            direct_normalized=draft.normalized_answer,
            candidate_set=[candidate.model_dump() for candidate in candidates],
            stage_records=stages,
            malformed=0,
            duplicates=0,
            trivial=0,
            kept_options=len(defended),
            candidate_coverage=self._candidate_coverage(example, candidates),
            latency_s=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def dart_human_rebuttal_same(self, example: BenchmarkExample) -> MethodResult:
        if not example.options:
            raise ValueError("dart_human_rebuttal_same requires a native multiple-choice example.")
        artifact = self._build_shared_artifact(example, "human_options", "dart_human_rebuttal_same")
        selected, final_stages = self._final_option_same_context(example, artifact, "dart_human_rebuttal_same")
        return self._build_result_from_selection("dart_human_rebuttal_same", example, artifact, selected, final_stages)

    def dart_human_rebuttal_fresh(self, example: BenchmarkExample) -> MethodResult:
        if not example.options:
            raise ValueError("dart_human_rebuttal_fresh requires a native multiple-choice example.")
        artifact = self._build_shared_artifact(example, "human_options", "dart_human_rebuttal_fresh")
        selected, final_stages = self._final_option_fresh(example, artifact, "dart_human_rebuttal_fresh")
        return self._build_result_from_selection("dart_human_rebuttal_fresh", example, artifact, selected, final_stages)

    def run_method(self, method_name: str, example: BenchmarkExample) -> MethodResult:
        dispatch = {
            "direct_cot": self.direct_cot,
            "self_consistency_5": self.self_consistency_5,
            "self_refine_1": self.self_refine_1,
            "self_refine_2_budgetmatched": self.self_refine_2_budgetmatched,
            "freeform_devil_advocate_same": self.freeform_devil_advocate_same,
            "mc_select_only": self.mc_select_only,
            "dart_self": self.dart_self,
            "dart_adv": self.dart_adv,
            "freeform_devil_advocate_fresh": self.freeform_devil_advocate_fresh,
            "dart_human_options": self.dart_human_options,
            "mc_select_only_binary": self.mc_select_only_binary,
            "dart_adv_binary_fresh": self.dart_adv_binary_fresh,
            "dart_self_binary": self.dart_self_binary,
            "mc_select_only_shared_candidates": self.mc_select_only_shared_candidates,
            "dart_adv_fresh": self.dart_adv_fresh,
            "dart_adv_same": self.dart_adv_same,
            "dart_adv_same_v1": self.dart_adv_same_v1,
            "adv_select_only_shared_v2": self.adv_select_only_shared_v2,
            "adv_rebuttal_then_select_shared_v2": self.adv_rebuttal_then_select_shared_v2,
            "dart_adv_same_v2": self.dart_adv_same_v2,
            "adv_select_only_shared": self.adv_select_only_shared,
            "adv_rebuttal_then_select_shared": self.adv_rebuttal_then_select_shared,
            "adv_rebuttal_then_same_context_final": self.adv_rebuttal_then_same_context_final,
            "adv_rebuttal_then_fresh_context_final": self.adv_rebuttal_then_fresh_context_final,
            "mc_select_only_human_options": self.mc_select_only_human_options,
            "dart_human_defense_select": self.dart_human_defense_select,
            "dart_human_rebuttal_same": self.dart_human_rebuttal_same,
            "dart_human_rebuttal_fresh": self.dart_human_rebuttal_fresh,
        }
        return dispatch[method_name](example)
