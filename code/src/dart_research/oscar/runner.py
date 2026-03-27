from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from dart_research.clients.hf_local import HFTransformersClient
from dart_research.datasets.loaders import BenchmarkExample
from dart_research.eir.python_exec import execute_python_snippet
from dart_research.eir.types import ActionBankRecord, ActionOutcome, BaselineOutcome, ProbeRecord
from dart_research.heir.runner import HEIRActionBankRunner
from dart_research.oscar.compiler import (
    assign_semantic_cluster,
    deterministic_compile_and_execute,
    parse_schema_fields,
    schema_to_preview,
)
from dart_research.oscar.prompts import OSCARPromptBank
from dart_research.parsing.tagged import extract_tagged_fields
from dart_research.tier.prompts import TIERPromptBank
from dart_research.vchase.prm import ProcessRewardModelScorer


OSCAR_INTERFACE_NAMES = [
    "KEEP",
    "RAW_PYTHON",
    "OPERATOR_SCHEMA_TO_CODE",
    "OSCAR_TEMPLATE_COMPILE",
    "OSCAR_CONSTRAINED_COMPILE",
    "NORMALIZED_QUESTION_TO_CODE",
]


class OSCARInterfaceBankRunner(HEIRActionBankRunner):
    def __init__(
        self,
        *,
        repo_root: Path,
        client: HFTransformersClient,
        model_name: str,
        prm_scorer: ProcessRewardModelScorer | None = None,
        max_output_tokens: int = 180,
        problem_only: bool = False,
        use_normalized_replacement: bool = False,
    ) -> None:
        super().__init__(
            repo_root=repo_root,
            client=client,
            model_name=model_name,
            prm_scorer=prm_scorer,
            max_output_tokens=max_output_tokens,
        )
        self.tier_prompts = TIERPromptBank.load(repo_root)
        self.oscar_prompts = OSCARPromptBank.load(repo_root)
        self.problem_only = problem_only
        self.use_normalized_replacement = use_normalized_replacement

    def collect_record(self, example: BenchmarkExample) -> ActionBankRecord:
        draft = self._draft(example)
        general_features = self._general_features(example, draft.answer, draft.scratch)
        state_features, _ = self._state_features(example, draft.answer, draft.scratch)
        cluster = assign_semantic_cluster(example.question)

        keep_probe = self._keep_probe(example, draft.answer, draft.scratch)
        raw_probe = self._raw_python_probe(example, draft.answer, draft.scratch)
        operator_probe = self._operator_probe(example, draft.answer, draft.scratch)
        schema_probe = self._schema_probe(example, draft.answer, draft.scratch)
        probes = [
            keep_probe,
            raw_probe,
            operator_probe,
            schema_probe,
        ]
        if self.use_normalized_replacement:
            normalized_probe = self._normalized_probe(example, draft.answer, draft.scratch)
            probes.append(normalized_probe)
        else:
            probes.append(self._clone_probe(schema_probe, "OSCAR_CONSTRAINED_COMPILE"))

        actions = [
            self._keep_action(example, draft),
            self._raw_python_action(example, draft, raw_probe),
            self._operator_action(example, draft, operator_probe),
            self._template_compile_action(example, draft, schema_probe),
        ]
        if self.use_normalized_replacement:
            actions.append(self._normalized_action(example, draft, normalized_probe))
        else:
            actions.append(self._constrained_compile_action(example, draft, schema_probe))

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
            "freeform_fixed2_same": self._baseline_freeform_fixed2(example, draft.answer, draft.scratch),
        }
        tier_bundle = self.tier_prompts.version_bundle(eir_prompts=self.prompts, heir_prompts=self.heir_prompts)
        return ActionBankRecord(
            dataset=example.dataset,
            question_id=example.question_id,
            question=example.question,
            gold_answer=example.gold_answer,
            gold_normalized=example.gold_normalized,
            task_type=example.task_type,
            model_name=self.model_name,
            backend="hf_local",
            prompt_bundle=self.oscar_prompts.version_bundle_with_tier(tier_bundle=tier_bundle),
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
                "use_normalized_replacement": int(self.use_normalized_replacement),
            },
        )

    def _ctx_answer(self, answer: str) -> str:
        return "" if self.problem_only else answer

    def _ctx_scratch(self, scratch: str) -> str:
        return "" if self.problem_only else scratch

    def _clone_probe(self, probe: ProbeRecord, action_name: str) -> ProbeRecord:
        return ProbeRecord(
            action_name=action_name,
            fields={**probe.fields, "shared_preview": 1},
            parse_ok=probe.parse_ok,
            input_tokens=0,
            output_tokens=0,
            latency_s=0.0,
            raw_paths=[],
        )

    def _keep_probe(self, example: BenchmarkExample, answer: str, scratch: str) -> ProbeRecord:
        prompt = self.heir_prompts.keep_probe.render(
            question=example.question,
            answer=self._ctx_answer(answer),
            scratch=self._ctx_scratch(scratch),
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="oscar_keep_probe",
            prompt_version=self.heir_prompts.keep_probe.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=80,
            metadata={"branch": "oscar", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        if not fields.get("keep_recommendation"):
            recovered = re.search(
                r"<keep_recommendation>(.*?)</keep_recommend(?:ation|ition)>",
                response["text"],
                flags=re.IGNORECASE | re.DOTALL,
            )
            if recovered:
                fields["keep_recommendation"] = recovered.group(1).strip()
        metrics = response["metrics"]
        return ProbeRecord(
            action_name="KEEP",
            fields={
                "keep_recommendation": fields.get("keep_recommendation", ""),
                "draft_complete": self._parse_yes_no(fields.get("draft_complete", "")),
                "risk": self._parse_int(fields.get("risk", "0")),
                "gap": fields.get("gap", ""),
            },
            parse_ok=int(bool(fields.get("keep_recommendation"))),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )

    def _keep_action(self, example: BenchmarkExample, draft) -> ActionOutcome:
        return self._make_action_outcome(
            example,
            action_name="KEEP",
            answer=draft.answer,
            scratch=draft.scratch,
            draft_correct=draft.correctness,
            metrics={"input_tokens": 0, "output_tokens": 0, "latency_s": 0.0, "raw_paths": []},
        )

    def _raw_python_probe(self, example: BenchmarkExample, answer: str, scratch: str) -> ProbeRecord:
        prompt = self.prompts.python_probe.render(
            question=example.question,
            answer=self._ctx_answer(answer),
            scratch=self._ctx_scratch(scratch),
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="oscar_raw_python_probe",
            prompt_version=self.prompts.python_probe.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=120,
            metadata={"branch": "oscar", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        exec_payload = execute_python_snippet(fields.get("code", "")) if fields.get("code") else {"success": 0, "result": "", "error": "no_code", "latency_s": 0.0}
        metrics = response["metrics"]
        return ProbeRecord(
            action_name="RAW_PYTHON",
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

    def _operator_probe(self, example: BenchmarkExample, answer: str, scratch: str) -> ProbeRecord:
        prompt = self.tier_prompts.operator_probe.render(
            question=example.question,
            answer=self._ctx_answer(answer),
            scratch=self._ctx_scratch(scratch),
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="oscar_operator_probe",
            prompt_version=self.tier_prompts.operator_probe.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=120,
            metadata={"branch": "oscar", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        metrics = response["metrics"]
        return ProbeRecord(
            action_name="OPERATOR_SCHEMA_TO_CODE",
            fields={
                "operator_family": fields.get("operator_family", ""),
                "discretization": fields.get("discretization", ""),
                "target_type": fields.get("target_type", ""),
                "formula_family": fields.get("formula_family", ""),
                "mapping": fields.get("mapping", ""),
                "complete": self._parse_yes_no(fields.get("complete", "")),
            },
            parse_ok=int(bool(fields.get("operator_family") or fields.get("mapping"))),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )

    def _schema_probe(self, example: BenchmarkExample, answer: str, scratch: str) -> ProbeRecord:
        prompt = self.oscar_prompts.schema_probe.render(
            question=example.question,
            answer=self._ctx_answer(answer),
            scratch=self._ctx_scratch(scratch),
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="oscar_schema_probe",
            prompt_version=self.oscar_prompts.schema_probe.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=220,
            metadata={"branch": "oscar", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        metrics = response["metrics"]
        quantities = str(fields.get("quantities", ""))
        relation_chain = str(fields.get("relation_chain", ""))
        return ProbeRecord(
            action_name="OSCAR_TEMPLATE_COMPILE",
            fields={
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
            },
            parse_ok=int(bool(fields.get("operator_family") or quantities or relation_chain)),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )

    def _raw_python_action(self, example: BenchmarkExample, draft, probe: ProbeRecord) -> ActionOutcome:
        preview = str(probe.fields.get("code", "")).strip() or "No executable sketch available."
        prompt = self.prompts.python_action.render(
            question=example.question,
            answer=self._ctx_answer(draft.answer),
            scratch=self._ctx_scratch(draft.scratch),
            python_preview=preview,
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="oscar_raw_python_action",
            prompt_version=self.prompts.python_action.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 160),
            metadata={"branch": "oscar", "dataset": example.dataset, "question_id": example.question_id},
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
            action_name="RAW_PYTHON",
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

    def _operator_action(self, example: BenchmarkExample, draft, probe: ProbeRecord) -> ActionOutcome:
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
            prompt_name="oscar_operator_action",
            prompt_version=self.tier_prompts.operator_action.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 180),
            metadata={"branch": "oscar", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
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
        metrics = self._add_probe_metrics(metrics, probe)
        metrics["latency_s"] += float(exec_payload["latency_s"])
        metadata = {
            "code": fields.get("code", ""),
            "schema": fields.get("schema", ""),
            "model_answer": fields.get("answer", ""),
        }
        return self._make_action_outcome(
            example,
            action_name="OPERATOR_SCHEMA_TO_CODE",
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

    def _template_compile_action(self, example: BenchmarkExample, draft, probe: ProbeRecord) -> ActionOutcome:
        schema = parse_schema_fields(probe.fields)
        try:
            payload = deterministic_compile_and_execute(schema)
            answer = str(payload["result"]).strip() if payload["success"] else draft.answer
            scratch = f"schema={schema.operator_family}; chain={payload.get('used_relation_chain', '')}"
            action_failed = int(not payload["success"])
        except Exception as error:
            payload = {"success": 0, "result": "", "latency_s": 0.0, "code": "", "used_relation_chain": "", "error": str(error)}
            answer = draft.answer
            scratch = draft.scratch
            action_failed = 1
        metrics = {
            "input_tokens": probe.input_tokens,
            "output_tokens": probe.output_tokens,
            "latency_s": probe.latency_s + float(payload.get("latency_s", 0.0)),
            "raw_paths": list(probe.raw_paths),
        }
        metadata = {
            "schema_preview": schema_to_preview(schema),
            "code": str(payload.get("code", "")),
            "used_relation_chain": str(payload.get("used_relation_chain", "")),
            "compile_mode": "deterministic_template",
            "error": str(payload.get("error", "")),
        }
        return self._make_action_outcome(
            example,
            action_name="OSCAR_TEMPLATE_COMPILE",
            answer=answer,
            scratch=scratch,
            draft_correct=draft.correctness,
            metrics=metrics,
            metadata=metadata,
            execution_used=1,
            execution_success=int(payload.get("success", 0)),
            execution_result=str(payload.get("result", "")),
            action_failed=action_failed,
        )

    def _constrained_compile_action(self, example: BenchmarkExample, draft, probe: ProbeRecord) -> ActionOutcome:
        schema = parse_schema_fields(probe.fields)
        schema_preview = schema_to_preview(schema)
        prompt = self.oscar_prompts.constrained_compile.render(
            question=example.question,
            answer=self._ctx_answer(draft.answer),
            scratch=self._ctx_scratch(draft.scratch),
            schema_preview=schema_preview,
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="oscar_constrained_compile",
            prompt_version=self.oscar_prompts.constrained_compile.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 160),
            metadata={"branch": "oscar", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        program = str(fields.get("program", "")).strip()
        try:
            payload = deterministic_compile_and_execute(schema, relation_chain=program)
            answer = str(payload["result"]).strip() if payload["success"] else self._fallback_answer(
                fields.get("answer", ""),
                response["text"],
                example.task_type,
                default=draft.answer,
            )
            action_failed = int(not payload["success"] and not fields.get("answer"))
        except Exception as error:
            payload = {"success": 0, "result": "", "latency_s": 0.0, "code": "", "used_relation_chain": program, "error": str(error)}
            answer = self._fallback_answer(fields.get("answer", ""), response["text"], example.task_type, default=draft.answer)
            action_failed = 1
        scratch = fields.get("scratch", self._fallback_scratch(response["text"], default=draft.scratch))
        metrics = self._metrics_payload(response)
        metrics = self._add_probe_metrics(metrics, probe)
        metrics["latency_s"] += float(payload.get("latency_s", 0.0))
        metadata = {
            "schema_preview": schema_preview,
            "program": program,
            "code": str(payload.get("code", "")),
            "used_relation_chain": str(payload.get("used_relation_chain", "")),
            "compile_mode": "constrained",
            "error": str(payload.get("error", "")),
        }
        return self._make_action_outcome(
            example,
            action_name="OSCAR_CONSTRAINED_COMPILE",
            answer=answer,
            scratch=scratch,
            draft_correct=draft.correctness,
            metrics=metrics,
            metadata=metadata,
            execution_used=1,
            execution_success=int(payload.get("success", 0)),
            execution_result=str(payload.get("result", "")),
            action_failed=action_failed,
        )

    def _normalized_probe(self, example: BenchmarkExample, answer: str, scratch: str) -> ProbeRecord:
        prompt = self.tier_prompts.normalized_probe.render(
            question=example.question,
            answer=self._ctx_answer(answer),
            scratch=self._ctx_scratch(scratch),
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="oscar_normalized_probe",
            prompt_version=self.tier_prompts.normalized_probe.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=100,
            metadata={"branch": "oscar", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        metrics = response["metrics"]
        return ProbeRecord(
            action_name="NORMALIZED_QUESTION_TO_CODE",
            fields={
                "normalized_problem": fields.get("normalized_problem", ""),
                "complete": self._parse_yes_no(fields.get("complete", "")),
            },
            parse_ok=int(bool(fields.get("normalized_problem"))),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )

    def _normalized_action(self, example: BenchmarkExample, draft, probe: ProbeRecord) -> ActionOutcome:
        preview = str(probe.fields.get("normalized_problem", "")).strip() or example.question
        prompt = self.tier_prompts.normalized_action.render(
            question=example.question,
            answer=self._ctx_answer(draft.answer),
            scratch=self._ctx_scratch(draft.scratch),
            normalized_preview=preview,
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="oscar_normalized_action",
            prompt_version=self.tier_prompts.normalized_action.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 180),
            metadata={"branch": "oscar", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
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
        metrics = self._add_probe_metrics(metrics, probe)
        metrics["latency_s"] += float(exec_payload["latency_s"])
        return self._make_action_outcome(
            example,
            action_name="NORMALIZED_QUESTION_TO_CODE",
            answer=answer,
            scratch=scratch,
            draft_correct=draft.correctness,
            metrics=metrics,
            metadata={"normalized_problem": fields.get("normalized_problem", ""), "code": fields.get("code", "")},
            execution_used=1,
            execution_success=int(exec_payload["success"]),
            execution_result=str(exec_payload["result"]),
            action_failed=int(not exec_payload["success"] and not fields.get("answer")),
        )

    def _add_probe_metrics(self, metrics: dict[str, Any], probe: ProbeRecord) -> dict[str, Any]:
        return {
            "input_tokens": int(metrics["input_tokens"]) + int(probe.input_tokens),
            "output_tokens": int(metrics["output_tokens"]) + int(probe.output_tokens),
            "latency_s": float(metrics["latency_s"]) + float(probe.latency_s),
            "raw_paths": list(metrics["raw_paths"]) + list(probe.raw_paths),
        }

    def _count_items(self, text: str) -> int:
        stripped = str(text).strip()
        if not stripped:
            return 0
        return len([part for part in re.split(r"[;\n]+", stripped) if part.strip()])
