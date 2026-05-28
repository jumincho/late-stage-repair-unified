"""ATLAS fieldwise schema-to-code interface bank runner (math domain).

Extends the OSCAR interface bank by collecting fieldwise schema probes:
first run an operator/quantities probe, then run the field-semantics and
field-quantities probes separately, and finally try a critical-field repair
based on retrieved teacher exemplars. Each variant is recorded as one row in
the per-example `ActionBankRecord`. Downstream rounds (`atlas_rg`, `cass`,
`cass_r4`) layer on top of this runner by adding role tables, repair-only
patches, and the f1 plan/execute heads.
"""

from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any

from dart_research.datasets.loaders import BenchmarkExample
from dart_research.eir.types import ActionBankRecord, ActionOutcome, BaselineOutcome, ProbeRecord
from dart_research.oscar.compiler import (
    assign_semantic_cluster,
    parse_schema_fields,
    schema_to_preview,
)
from dart_research.oscar.runner import OSCARInterfaceBankRunner
from dart_research.parsing.tagged import extract_tagged_fields
from dart_research.atlas.prompts import ATLASPromptBank
from dart_research.atlas.retrieval import (
    TeacherSeedExample,
    load_teacher_seed,
    render_teacher_exemplars,
    retrieve_teacher_exemplars,
)
from dart_research.atlas.schema import compose_fieldwise_schema_fields, repair_critical_schema_fields


ATLAS_METHOD_NAMES = [
    "KEEP",
    "RAW_PYTHON",
    "OPERATOR_SCHEMA_TO_CODE_BASE",
    "ATLAS_RETRIEVAL_SCHEMA_TO_CODE",
    "ATLAS_FIELDWISE_SCHEMA_TO_CODE",
    "TEACHER_SCHEMA_TO_CODE",
    "ATLAS_CRITICAL_FIELD_REPAIR",
]


class ATLASInterfaceBankRunner(OSCARInterfaceBankRunner):
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
        retrieval_mode: str = "global",
        enable_critical_repair: bool = False,
    ) -> None:
        super().__init__(
            repo_root=repo_root,
            client=client,
            model_name=model_name,
            prm_scorer=prm_scorer,
            max_output_tokens=max_output_tokens,
            problem_only=problem_only,
            use_normalized_replacement=False,
        )
        self.atlas_prompts = ATLASPromptBank.load(repo_root)
        self.teacher_seed_path = teacher_seed_path
        self.teacher_seed_examples: list[TeacherSeedExample] = []
        self.teacher_by_id: dict[str, TeacherSeedExample] = {}
        if teacher_seed_path is not None and teacher_seed_path.exists():
            self.teacher_seed_examples = load_teacher_seed(teacher_seed_path)
            self.teacher_by_id = {item.question_id: item for item in self.teacher_seed_examples}
        self.retrieval_mode = retrieval_mode
        self.enable_critical_repair = enable_critical_repair

    def collect_record(self, example: BenchmarkExample) -> ActionBankRecord:
        draft = self._draft(example)
        general_features = self._general_features(example, draft.answer, draft.scratch)
        state_features, _ = self._state_features(example, draft.answer, draft.scratch)
        cluster = assign_semantic_cluster(example.question)

        keep_probe = self._keep_probe(example, draft.answer, draft.scratch)
        raw_probe = self._raw_python_probe(example, draft.answer, draft.scratch)
        base_probe = self._operator_probe(example, draft.answer, draft.scratch)
        retrieval_probe = self._retrieval_schema_probe(example, draft.answer, draft.scratch, cluster)
        fieldwise_probe = self._fieldwise_schema_probe(example, draft.answer, draft.scratch, cluster)
        probes = [keep_probe, raw_probe, base_probe, retrieval_probe, fieldwise_probe]

        actions = [
            self._keep_action(example, draft),
            self._raw_python_action(example, draft, raw_probe),
            self._base_operator_action(example, draft, base_probe),
            self._schema_action(example, draft, retrieval_probe, action_name="ATLAS_RETRIEVAL_SCHEMA_TO_CODE"),
            self._schema_action(example, draft, fieldwise_probe, action_name="ATLAS_FIELDWISE_SCHEMA_TO_CODE"),
        ]

        if self.enable_critical_repair:
            repair_probe = self._critical_field_repair_probe(example, draft.answer, draft.scratch, retrieval_probe)
            probes.append(repair_probe)
            actions.append(self._schema_action(example, draft, repair_probe, action_name="ATLAS_CRITICAL_FIELD_REPAIR"))

        teacher_probe = self._teacher_probe(example)
        if teacher_probe is not None:
            probes.append(teacher_probe)
            actions.append(self._schema_action(example, draft, teacher_probe, action_name="TEACHER_SCHEMA_TO_CODE"))

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
        prompt_bundle.update(
            {
                "atlas_teacher_schema": self.atlas_prompts.teacher_schema.version,
                "atlas_retrieval_schema": self.atlas_prompts.retrieval_schema.version,
                "atlas_field_semantics": self.atlas_prompts.field_semantics.version,
                "atlas_field_quantities": self.atlas_prompts.field_quantities.version,
                "atlas_critical_field_repair": self.atlas_prompts.critical_field_repair.version,
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
                "enable_critical_repair": int(self.enable_critical_repair),
            },
        )

    def _make_schema_probe(self, response: dict[str, Any], *, action_name: str, extra_fields: dict[str, Any] | None = None) -> ProbeRecord:
        fields = extract_tagged_fields(response["text"])
        metrics = response["metrics"]
        quantities = str(fields.get("quantities", ""))
        relation_chain = str(fields.get("relation_chain", ""))
        payload = {
            "target_variable": fields.get("target_variable", ""),
            "final_target_type": fields.get("final_target_type", ""),
            "quantities": quantities,
            "operator_family": fields.get("operator_family", ""),
            "relation_chain": relation_chain,
            "discretization_flags": fields.get("discretization_flags", ""),
            "postprocess_flags": fields.get("postprocess_flags", ""),
            "geometry_formula_family": fields.get("geometry_formula_family", ""),
            "unresolved_items_count": self._parse_int(fields.get("unresolved_items_count", "0")),
            "complete": self._parse_yes_no(fields.get("complete", "")),
            "quantity_count": self._count_items(quantities),
            "relation_count": self._count_items(relation_chain),
        }
        if extra_fields:
            payload.update(extra_fields)
        return ProbeRecord(
            action_name=action_name,
            fields=payload,
            parse_ok=int(bool(payload["operator_family"] or quantities or relation_chain)),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )

    def _base_operator_action(self, example: BenchmarkExample, draft, probe: ProbeRecord) -> ActionOutcome:
        preview = (
            f"operator={probe.fields.get('operator_family', '')}; "
            f"discretization={probe.fields.get('discretization', '')}; "
            f"target={probe.fields.get('target_type', '')}; "
            f"formula={probe.fields.get('formula_family', '')}; "
            f"mapping={probe.fields.get('mapping', '')}"
        )
        prompt = self.tier_prompts.operator_action.render(
            question=example.question,
            answer=self._ctx_answer(draft.answer),
            scratch=self._ctx_scratch(draft.scratch),
            operator_preview=preview,
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="atlas_operator_action_base",
            prompt_version=self.tier_prompts.operator_action.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 180),
            metadata={"branch": "atlas", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        exec_payload = self._exec_payload(fields.get("code", ""))
        answer = self._exec_answer_or_fallback(exec_payload, fields, response["text"], draft.answer, example.task_type)
        scratch = fields.get("scratch", self._fallback_scratch(response["text"], default=draft.scratch))
        metrics = self._metrics_payload(response)
        metrics["latency_s"] += float(exec_payload["latency_s"])
        metadata = {
            "code": fields.get("code", ""),
            "schema": fields.get("schema", ""),
            "model_answer": fields.get("answer", ""),
            "schema_fields": json.dumps(
                {
                    "target_variable": "result",
                    "final_target_type": probe.fields.get("target_type", ""),
                    "quantities": "",
                    "operator_family": probe.fields.get("operator_family", ""),
                    "relation_chain": "",
                    "discretization_flags": probe.fields.get("discretization", ""),
                    "postprocess_flags": "none",
                    "geometry_formula_family": probe.fields.get("formula_family", ""),
                    "unresolved_items_count": 0,
                    "complete": probe.fields.get("complete", 0),
                },
                ensure_ascii=True,
            ),
        }
        return self._make_action_outcome(
            example,
            action_name="OPERATOR_SCHEMA_TO_CODE_BASE",
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

    def _retrieval_schema_probe(self, example: BenchmarkExample, answer: str, scratch: str, cluster: str) -> ProbeRecord:
        exemplars = retrieve_teacher_exemplars(
            question=example.question,
            cluster=cluster,
            seed_examples=self.teacher_seed_examples,
            mode=self.retrieval_mode,
            top_k=3,
            exclude_question_id=example.question_id,
        )
        prompt = self.atlas_prompts.retrieval_schema.render(
            cluster_hint=cluster,
            retrieved_examples=render_teacher_exemplars(exemplars),
            question=example.question,
            answer=self._ctx_answer(answer),
            scratch=self._ctx_scratch(scratch),
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="atlas_retrieval_schema",
            prompt_version=self.atlas_prompts.retrieval_schema.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=220,
            metadata={"branch": "atlas", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        return self._make_schema_probe(
            response,
            action_name="ATLAS_RETRIEVAL_SCHEMA_TO_CODE",
            extra_fields={
                "retrieval_mode": self.retrieval_mode,
                "retrieved_ids": ",".join(item.question_id for item in exemplars),
                "retrieved_clusters": ",".join(item.cluster for item in exemplars),
            },
        )

    def _fieldwise_schema_probe(self, example: BenchmarkExample, answer: str, scratch: str, cluster: str) -> ProbeRecord:
        semantic_prompt = self.atlas_prompts.field_semantics.render(
            cluster_hint=cluster,
            question=example.question,
            answer=self._ctx_answer(answer),
            scratch=self._ctx_scratch(scratch),
        )
        semantic_response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="atlas_field_semantics",
            prompt_version=self.atlas_prompts.field_semantics.version,
            prompt_text=semantic_prompt,
            temperature=0.0,
            max_output_tokens=120,
            metadata={"branch": "atlas", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        semantic_fields = extract_tagged_fields(semantic_response["text"])

        quantity_prompt = self.atlas_prompts.field_quantities.render(
            question=example.question,
            answer=self._ctx_answer(answer),
            scratch=self._ctx_scratch(scratch),
        )
        quantity_response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="atlas_field_quantities",
            prompt_version=self.atlas_prompts.field_quantities.version,
            prompt_text=quantity_prompt,
            temperature=0.0,
            max_output_tokens=180,
            metadata={"branch": "atlas", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        quantity_fields = extract_tagged_fields(quantity_response["text"])

        combined_text = "\n".join(
            [
                semantic_response["text"],
                quantity_response["text"],
            ]
        )
        combined = compose_fieldwise_schema_fields(semantic_fields, quantity_fields)
        metrics = semantic_response["metrics"]
        metrics.input_tokens += quantity_response["metrics"].input_tokens
        metrics.output_tokens += quantity_response["metrics"].output_tokens
        metrics.latency_s += quantity_response["metrics"].latency_s
        metrics.raw_path = quantity_response["metrics"].raw_path
        fake_response = {"text": combined_text, "metrics": metrics}
        return self._make_schema_probe(
            fake_response,
            action_name="ATLAS_FIELDWISE_SCHEMA_TO_CODE",
            extra_fields={"fieldwise": 1},
        )

    def _critical_field_repair_probe(self, example: BenchmarkExample, answer: str, scratch: str, base_probe: ProbeRecord) -> ProbeRecord:
        current_schema = schema_to_preview(parse_schema_fields(base_probe.fields))
        prompt = self.atlas_prompts.critical_field_repair.render(
            question=example.question,
            answer=self._ctx_answer(answer),
            scratch=self._ctx_scratch(scratch),
            current_schema=current_schema,
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="atlas_critical_field_repair",
            prompt_version=self.atlas_prompts.critical_field_repair.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=100,
            metadata={"branch": "atlas", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        repaired = repair_critical_schema_fields(dict(base_probe.fields), fields)
        metrics = response["metrics"]
        return ProbeRecord(
            action_name="ATLAS_CRITICAL_FIELD_REPAIR",
            fields=repaired,
            parse_ok=int(bool(fields)),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )

    def _teacher_probe(self, example: BenchmarkExample) -> ProbeRecord | None:
        teacher = self.teacher_by_id.get(example.question_id)
        if teacher is None:
            return None
        return ProbeRecord(
            action_name="TEACHER_SCHEMA_TO_CODE",
            fields=dict(teacher.schema_fields),
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
            prompt_name=f"atlas_{action_name.lower()}_action",
            prompt_version=self.tier_prompts.operator_action.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 180),
            metadata={"branch": "atlas", "dataset": example.dataset, "question_id": example.question_id},
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

    def _exec_payload(self, code: str) -> dict[str, Any]:
        from dart_research.eir.python_exec import execute_python_snippet

        return execute_python_snippet(code)

    def _exec_answer_or_fallback(self, exec_payload: dict[str, Any], fields: dict[str, Any], response_text: str, default_answer: str, task_type: str) -> str:
        if exec_payload["success"]:
            return str(exec_payload["result"]).strip()
        return self._fallback_answer(fields.get("answer", ""), response_text, task_type, default=default_answer)
