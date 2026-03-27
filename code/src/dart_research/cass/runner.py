from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from dart_research.atlas_rg.runner import ATLASRGInterfaceBankRunner
from dart_research.datasets.loaders import BenchmarkExample
from dart_research.eir.types import ActionBankRecord, ActionOutcome, BaselineOutcome, ProbeRecord
from dart_research.oscar.compiler import assign_semantic_cluster, parse_schema_fields, schema_to_preview
from dart_research.parsing.tagged import extract_tagged_fields

from .prompts import CASSPromptBank
from .retrieval import TeacherPatchSeedExample, load_teacher_seed, render_teacher_exemplars, retrieve_teacher_exemplars
from .schema import (
    apply_teacher_patch_fields,
    baseline_schema_from_operator_probe,
    repair_critical_role_patch,
    repair_nonrole_patch,
    repair_role_patch,
    repair_target_postprocess_patch,
    repair_target_postprocess_plus_role_patch,
    role_suspicion,
    target_postprocess_suspicion,
)


CASS_METHOD_NAMES = [
    "KEEP",
    "RAW_PYTHON",
    "OPERATOR_SCHEMA_TO_CODE_BASE",
    "ATLAS_FIELDWISE_SCHEMA_TO_CODE",
    "ATLAS_RG_ROLE_REPAIR_ONLY",
    "CASS_TARGET_POSTPROCESS_PATCH",
    "CASS_ROLE_PATCH",
    "CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH",
    "CASS_CRITICAL_ROLE_PATCH",
    "CASS_NONROLE_PATCH",
    "TEACHER_PATCHED_BASELINE",
]


class CASSPatchBankRunner(ATLASRGInterfaceBankRunner):
    def __init__(
        self,
        *,
        repo_root: Path,
        client,
        model_name: str,
        prm_scorer=None,
        max_output_tokens: int = 180,
        problem_only: bool = False,
        teacher_seed_path: Path | None = None,
        retrieval_mode: str = "cluster_first",
        fieldwise_combined_patch: bool = False,
        frozen_drafts_path: Path | None = None,
        save_drafts_path: Path | None = None,
    ) -> None:
        super().__init__(
            repo_root=repo_root,
            client=client,
            model_name=model_name,
            prm_scorer=prm_scorer,
            max_output_tokens=max_output_tokens,
            problem_only=problem_only,
            teacher_seed_path=None,
            retrieval_mode=retrieval_mode,
            enable_critical_role_repair=False,
            frozen_drafts_path=frozen_drafts_path,
            save_drafts_path=save_drafts_path,
        )
        self.cass_prompts = CASSPromptBank.load(repo_root)
        self.retrieval_mode = retrieval_mode
        self.fieldwise_combined_patch = fieldwise_combined_patch
        self.teacher_seed_source = "none"
        self.teacher_seed_examples: list[TeacherPatchSeedExample] = []
        self.teacher_by_id: dict[str, TeacherPatchSeedExample] = {}
        if teacher_seed_path is not None and teacher_seed_path.exists():
            parent_name = teacher_seed_path.parent.name.strip()
            stem = teacher_seed_path.stem.strip()
            self.teacher_seed_source = parent_name or stem or "seed"
            self.teacher_seed_examples = load_teacher_seed(teacher_seed_path)
            self.teacher_by_id = {item.question_id: item for item in self.teacher_seed_examples}

    def build_patch_context(self, example: BenchmarkExample) -> dict[str, Any]:
        draft, draft_source = self._draft_for_example(example)
        cluster = assign_semantic_cluster(example.question)
        base_probe = self._operator_probe(example, draft.answer, draft.scratch)
        base_schema_probe = self._baseline_schema_probe(base_probe)
        fieldwise_probe = self._fieldwise_schema_probe(example, draft.answer, draft.scratch, cluster)
        target_checker = target_postprocess_suspicion(
            example.question,
            base_fields=base_schema_probe.fields,
            fieldwise_fields=fieldwise_probe.fields,
        )
        role_checker = role_suspicion(
            example.question,
            base_fields=base_schema_probe.fields,
            fieldwise_fields=fieldwise_probe.fields,
        )
        return {
            "draft": draft,
            "draft_source": draft_source,
            "cluster": cluster,
            "base_probe": base_probe,
            "base_schema_probe": base_schema_probe,
            "fieldwise_probe": fieldwise_probe,
            "target_checker": target_checker,
            "role_checker": role_checker,
        }

    def collect_record(self, example: BenchmarkExample) -> ActionBankRecord:
        ctx = self.build_patch_context(example)
        draft = ctx["draft"]
        cluster = ctx["cluster"]
        general_features = self._general_features(example, draft.answer, draft.scratch)
        state_features, _ = self._state_features(example, draft.answer, draft.scratch)

        keep_probe = self._keep_probe(example, draft.answer, draft.scratch)
        raw_probe = self._raw_python_probe(example, draft.answer, draft.scratch)
        base_probe = ctx["base_probe"]
        fieldwise_probe = ctx["fieldwise_probe"]
        role_reference_probe = self._role_repair_probe(example, draft.answer, draft.scratch, fieldwise_probe, cluster)
        target_patch_probe = self._patch_probe(
            example,
            answer=draft.answer,
            scratch=draft.scratch,
            cluster=cluster,
            base_schema_probe=ctx["base_schema_probe"],
            action_name="CASS_TARGET_POSTPROCESS_PATCH",
            patch_group="target_postprocess",
            prompt_template=self.cass_prompts.target_postprocess_patch,
            max_output_tokens=160,
            repair_fn=repair_target_postprocess_patch,
            target_checker=ctx["target_checker"],
            role_checker=ctx["role_checker"],
        )
        role_patch_probe = self._patch_probe(
            example,
            answer=draft.answer,
            scratch=draft.scratch,
            cluster=cluster,
            base_schema_probe=ctx["base_schema_probe"],
            action_name="CASS_ROLE_PATCH",
            patch_group="role",
            prompt_template=self.cass_prompts.role_patch,
            max_output_tokens=200,
            repair_fn=repair_role_patch,
            target_checker=ctx["target_checker"],
            role_checker=ctx["role_checker"],
        )
        if self.fieldwise_combined_patch:
            combined_patch_probe = self._compose_fieldwise_combined_probe(
                base_schema_probe=ctx["base_schema_probe"],
                target_patch_probe=target_patch_probe,
                role_patch_probe=role_patch_probe,
                target_checker=ctx["target_checker"],
                role_checker=ctx["role_checker"],
            )
        else:
            combined_patch_probe = self._patch_probe(
                example,
                answer=draft.answer,
                scratch=draft.scratch,
                cluster=cluster,
                base_schema_probe=ctx["base_schema_probe"],
                action_name="CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH",
                patch_group="combined",
                prompt_template=self.cass_prompts.combined_patch,
                max_output_tokens=240,
                repair_fn=repair_target_postprocess_plus_role_patch,
                target_checker=ctx["target_checker"],
                role_checker=ctx["role_checker"],
            )
        critical_role_probe = self._patch_probe(
            example,
            answer=draft.answer,
            scratch=draft.scratch,
            cluster=cluster,
            base_schema_probe=ctx["base_schema_probe"],
            action_name="CASS_CRITICAL_ROLE_PATCH",
            patch_group="critical_role",
            prompt_template=self.cass_prompts.critical_role_patch,
            max_output_tokens=160,
            repair_fn=repair_critical_role_patch,
            target_checker=ctx["target_checker"],
            role_checker=ctx["role_checker"],
        )
        nonrole_patch_probe = self._patch_probe(
            example,
            answer=draft.answer,
            scratch=draft.scratch,
            cluster=cluster,
            base_schema_probe=ctx["base_schema_probe"],
            action_name="CASS_NONROLE_PATCH",
            patch_group="nonrole",
            prompt_template=self.cass_prompts.nonrole_patch,
            max_output_tokens=150,
            repair_fn=repair_nonrole_patch,
            target_checker=ctx["target_checker"],
            role_checker=ctx["role_checker"],
        )

        probes = [
            keep_probe,
            raw_probe,
            base_probe,
            fieldwise_probe,
            role_reference_probe,
            target_patch_probe,
            role_patch_probe,
            combined_patch_probe,
            critical_role_probe,
            nonrole_patch_probe,
        ]
        actions = [
            self._keep_action(example, draft),
            self._raw_python_action(example, draft, raw_probe),
            self._base_operator_action(example, draft, base_probe),
            self._schema_action(example, draft, fieldwise_probe, action_name="ATLAS_FIELDWISE_SCHEMA_TO_CODE"),
            self._schema_action(example, draft, role_reference_probe, action_name="ATLAS_RG_ROLE_REPAIR_ONLY"),
            self._schema_action(example, draft, target_patch_probe, action_name="CASS_TARGET_POSTPROCESS_PATCH"),
            self._schema_action(example, draft, role_patch_probe, action_name="CASS_ROLE_PATCH"),
            self._schema_action(example, draft, combined_patch_probe, action_name="CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH"),
            self._schema_action(example, draft, critical_role_probe, action_name="CASS_CRITICAL_ROLE_PATCH"),
            self._schema_action(example, draft, nonrole_patch_probe, action_name="CASS_NONROLE_PATCH"),
        ]

        teacher_probe = self._teacher_probe(example)
        if teacher_probe is not None:
            probes.append(teacher_probe)
            actions.append(self._schema_action(example, draft, teacher_probe, action_name="TEACHER_PATCHED_BASELINE"))

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
            "freeform_fixed1_same": self._baseline_freeform_fixed1(example, draft.answer, draft.scratch),
        }
        prompt_bundle = self.tier_prompts.version_bundle(eir_prompts=self.prompts, heir_prompts=self.heir_prompts)
        prompt_bundle = self.atlas_rg_prompts.version_bundle(base_bundle=prompt_bundle)
        prompt_bundle = self.cass_prompts.version_bundle(base_bundle=prompt_bundle)
        prompt_bundle.update(
            {
                "atlas_field_semantics": self.atlas_prompts.field_semantics.version,
                "atlas_field_quantities": self.atlas_prompts.field_quantities.version,
            }
        )
        return ActionBankRecord(
            dataset=example.dataset,
            question_id=example.question_id,
            question=example.question,
            gold_answer=example.gold_answer,
            gold_normalized=example.gold_normalized,
            task_type=example.task_type,
            model_name=self.model_name,
            backend="hf_local",
            prompt_bundle=prompt_bundle,
            draft=draft,
            general_features=general_features,
            state_features=state_features,
            probes=probes,
            actions=actions,
            baselines=baselines,
            metadata={
                **example.metadata,
                "cluster": cluster,
                "problem_only": int(self.problem_only),
                "retrieval_mode": self.retrieval_mode,
                "teacher_seed_available": int(bool(self.teacher_seed_examples)),
                "teacher_covered": int(example.question_id in self.teacher_by_id),
                "teacher_seed_source": self.teacher_seed_source,
                "draft_source": ctx["draft_source"],
                "fieldwise_combined_patch": int(self.fieldwise_combined_patch),
                "checker_target_score": int(ctx["target_checker"]["checker_target_score"]),
                "checker_role_score": int(ctx["role_checker"]["checker_role_score"]),
            },
        )

    def _baseline_schema_probe(self, base_probe: ProbeRecord) -> ProbeRecord:
        return ProbeRecord(
            action_name="CASS_BASELINE_SCHEMA",
            fields=baseline_schema_from_operator_probe(base_probe.fields),
            parse_ok=base_probe.parse_ok,
            input_tokens=base_probe.input_tokens,
            output_tokens=base_probe.output_tokens,
            latency_s=base_probe.latency_s,
            raw_paths=list(base_probe.raw_paths),
        )

    def _checker_summary(self, checker: dict[str, Any], *, prefix: str) -> str:
        score = checker.get(f"checker_{prefix}_score", 0)
        tags = checker.get(f"checker_{prefix}_tags", "none")
        suspicious = checker.get(f"checker_{prefix}_suspicious", 0)
        return f"score={score}; suspicious={suspicious}; tags={tags}"

    def _patch_probe(
        self,
        example: BenchmarkExample,
        *,
        answer: str,
        scratch: str,
        cluster: str,
        base_schema_probe: ProbeRecord,
        action_name: str,
        patch_group: str,
        prompt_template,
        max_output_tokens: int,
        repair_fn,
        target_checker: dict[str, Any],
        role_checker: dict[str, Any],
    ) -> ProbeRecord:
        exemplars = retrieve_teacher_exemplars(
            question=example.question,
            cluster=cluster,
            base_fields=base_schema_probe.fields,
            patch_group=patch_group,
            seed_examples=self.teacher_seed_examples,
            mode=self.retrieval_mode,
            top_k=3,
            exclude_question_id=example.question_id,
        )
        prompt = prompt_template.render(
            cluster_hint=cluster,
            retrieved_examples=render_teacher_exemplars(exemplars, patch_group=patch_group),
            question=example.question,
            answer=self._ctx_answer(answer),
            scratch=self._ctx_scratch(scratch),
            current_schema=schema_to_preview(parse_schema_fields(base_schema_probe.fields)),
            target_checker=self._checker_summary(target_checker, prefix="target"),
            role_checker=self._checker_summary(role_checker, prefix="role"),
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name=action_name.lower(),
            prompt_version=prompt_template.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=max_output_tokens,
            metadata={"branch": "cass", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        repaired = repair_fn(dict(base_schema_probe.fields), fields)
        repaired.update(
            {
                "retrieval_mode": self.retrieval_mode,
                "retrieved_ids": ",".join(item.question_id for item in exemplars),
                "retrieved_clusters": ",".join(item.cluster for item in exemplars),
                "patch_group": patch_group,
                "patch_mode": "monolithic",
                "checker_target_score": int(target_checker["checker_target_score"]),
                "checker_target_tags": target_checker["checker_target_tags"],
                "checker_target_suspicious": int(target_checker["checker_target_suspicious"]),
                "checker_role_score": int(role_checker["checker_role_score"]),
                "checker_role_tags": role_checker["checker_role_tags"],
                "checker_role_suspicious": int(role_checker["checker_role_suspicious"]),
            }
        )
        metrics = response["metrics"]
        return ProbeRecord(
            action_name=action_name,
            fields=repaired,
            parse_ok=int(bool(fields)),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )

    def _compose_fieldwise_combined_probe(
        self,
        *,
        base_schema_probe: ProbeRecord,
        target_patch_probe: ProbeRecord,
        role_patch_probe: ProbeRecord,
        target_checker: dict[str, Any],
        role_checker: dict[str, Any],
    ) -> ProbeRecord:
        repaired = repair_target_postprocess_plus_role_patch(
            dict(base_schema_probe.fields),
            {**target_patch_probe.fields, **role_patch_probe.fields},
        )
        repaired.update(
            {
                "retrieval_mode": self.retrieval_mode,
                "retrieved_ids": ",".join(
                    item
                    for item in [
                        str(target_patch_probe.fields.get("retrieved_ids", "")),
                        str(role_patch_probe.fields.get("retrieved_ids", "")),
                    ]
                    if item
                ),
                "retrieved_clusters": ",".join(
                    item
                    for item in [
                        str(target_patch_probe.fields.get("retrieved_clusters", "")),
                        str(role_patch_probe.fields.get("retrieved_clusters", "")),
                    ]
                    if item
                ),
                "patch_group": "combined",
                "patch_mode": "fieldwise",
                "checker_target_score": int(target_checker["checker_target_score"]),
                "checker_target_tags": target_checker["checker_target_tags"],
                "checker_target_suspicious": int(target_checker["checker_target_suspicious"]),
                "checker_role_score": int(role_checker["checker_role_score"]),
                "checker_role_tags": role_checker["checker_role_tags"],
                "checker_role_suspicious": int(role_checker["checker_role_suspicious"]),
            }
        )
        return ProbeRecord(
            action_name="CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH",
            fields=repaired,
            parse_ok=int(target_patch_probe.parse_ok and role_patch_probe.parse_ok),
            input_tokens=target_patch_probe.input_tokens + role_patch_probe.input_tokens,
            output_tokens=target_patch_probe.output_tokens + role_patch_probe.output_tokens,
            latency_s=target_patch_probe.latency_s + role_patch_probe.latency_s,
            raw_paths=list(target_patch_probe.raw_paths) + list(role_patch_probe.raw_paths),
        )

    def _teacher_probe(self, example: BenchmarkExample) -> ProbeRecord | None:
        teacher = self.teacher_by_id.get(example.question_id)
        if teacher is None:
            return None
        fields = dict(teacher.patched_schema_fields)
        fields.update(
            {
                "patch_group": "teacher",
                "patch_mode": "teacher",
                "retrieval_mode": "teacher",
            }
        )
        return ProbeRecord(
            action_name="TEACHER_PATCHED_BASELINE",
            fields=fields,
            parse_ok=int(teacher.audit_ok),
            input_tokens=0,
            output_tokens=0,
            latency_s=0.0,
            raw_paths=[],
        )

    def _schema_action(self, example: BenchmarkExample, draft, probe: ProbeRecord, *, action_name: str) -> ActionOutcome:
        schema = parse_schema_fields(probe.fields)
        schema_preview = schema_to_preview(schema)
        prompt = self.tier_prompts.operator_action.render(
            question=example.question,
            answer=self._ctx_answer(draft.answer),
            scratch=self._ctx_scratch(draft.scratch),
            operator_preview=schema_preview,
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name=f"cass_{action_name.lower()}_action",
            prompt_version=self.tier_prompts.operator_action.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 180),
            metadata={"branch": "cass", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        exec_payload = self._exec_payload(fields.get("code", ""))
        answer = self._exec_answer_or_fallback(exec_payload, fields, response["text"], draft.answer, example.task_type)
        scratch = fields.get("scratch", self._fallback_scratch(response["text"], default=draft.scratch))
        metrics = self._metrics_payload(response)
        metrics["latency_s"] += float(exec_payload["latency_s"]) + float(probe.latency_s)
        metrics["input_tokens"] += probe.input_tokens
        metrics["output_tokens"] += probe.output_tokens
        metrics["raw_paths"] = list(probe.raw_paths) + metrics["raw_paths"]
        metadata = {
            "code": fields.get("code", ""),
            "schema": fields.get("schema", ""),
            "model_answer": fields.get("answer", ""),
            "schema_preview": schema_preview,
            "schema_fields": json.dumps(probe.fields, ensure_ascii=True),
            "retrieval_mode": probe.fields.get("retrieval_mode", ""),
            "retrieved_ids": probe.fields.get("retrieved_ids", ""),
            "retrieved_clusters": probe.fields.get("retrieved_clusters", ""),
            "patch_group": probe.fields.get("patch_group", ""),
            "patch_mode": probe.fields.get("patch_mode", ""),
            "checker_target_score": probe.fields.get("checker_target_score", 0),
            "checker_target_tags": probe.fields.get("checker_target_tags", ""),
            "checker_role_score": probe.fields.get("checker_role_score", 0),
            "checker_role_tags": probe.fields.get("checker_role_tags", ""),
        }
        return self._make_action_outcome(
            example,
            action_name=action_name,
            answer=answer,
            scratch=scratch,
            draft_correct=draft.correctness,
            metrics=metrics,
            metadata=metadata,
            execution_used=1,
            execution_success=int(exec_payload["success"]),
            execution_result=str(exec_payload["result"]),
            action_failed=int(not exec_payload["success"] and not fields.get("answer")),
        )
