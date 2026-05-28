"""CASS round-2 (`cass_r2`) runner: adds the F1-Lite and Prism-Lite heads.

Subclasses `CASSPatchBankRunner` and inserts two extra rows into each
`ActionBankRecord` — `F1_LITE` (lightweight first-pass schema rebuild) and
`PRISM_LITE` (multi-view consistency check). The output order is fixed by
`CASSR2_METHOD_ORDER`. This runner is what `cass_bd_collect_partial_replay`
re-uses when it lifts already-collected examples and stamps in the partial-
diagnosis methods.
"""

from __future__ import annotations

from pathlib import Path
import re

from dart_research.cass.runner import CASSPatchBankRunner
from dart_research.datasets.loaders import BenchmarkExample
from dart_research.eir.python_exec import execute_python_snippet
from dart_research.eir.types import ActionBankRecord, ActionOutcome, BaselineOutcome, ProbeRecord
from dart_research.parsing.tagged import extract_tagged_fields

from .prompts import CASSR2PromptBank


CASSR2_METHOD_ORDER = [
    "KEEP",
    "RAW_PYTHON",
    "OPERATOR_SCHEMA_TO_CODE_BASE",
    "ATLAS_FIELDWISE_SCHEMA_TO_CODE",
    "ATLAS_RG_ROLE_REPAIR_ONLY",
    "CASS_TARGET_POSTPROCESS_PATCH",
    "CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH",
    "F1_LITE",
    "PRISM_LITE",
    "TEACHER_PATCHED_BASELINE",
]


class CASSR2Runner(CASSPatchBankRunner):
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
            teacher_seed_path=teacher_seed_path,
            retrieval_mode=retrieval_mode,
            fieldwise_combined_patch=False,
            frozen_drafts_path=frozen_drafts_path,
            save_drafts_path=save_drafts_path,
        )
        self.cass_r2_prompts = CASSR2PromptBank.load(repo_root)

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
            repair_fn=self._repair_target_patch,
            target_checker=ctx["target_checker"],
            role_checker=ctx["role_checker"],
        )
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
            repair_fn=self._repair_combined_patch,
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
            combined_patch_probe,
        ]
        actions = [
            self._keep_action(example, draft),
            self._raw_python_action(example, draft, raw_probe),
            self._base_operator_action(example, draft, base_probe),
            self._schema_action(example, draft, fieldwise_probe, action_name="ATLAS_FIELDWISE_SCHEMA_TO_CODE"),
            self._schema_action(example, draft, role_reference_probe, action_name="ATLAS_RG_ROLE_REPAIR_ONLY"),
            self._schema_action(example, draft, target_patch_probe, action_name="CASS_TARGET_POSTPROCESS_PATCH"),
            self._schema_action(example, draft, combined_patch_probe, action_name="CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH"),
        ]
        action_map = {action.action_name: action for action in actions}

        f1_probe, f1_action = self._f1_lite(example, draft)
        probes.append(f1_probe)
        actions.append(f1_action)

        prism_probe, prism_action = self._prism_lite(example, draft, action_map=action_map)
        probes.append(prism_probe)
        actions.append(prism_action)

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
        prompt_bundle = self.cass_r2_prompts.version_bundle(base_bundle=prompt_bundle)
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
                "checker_target_score": int(ctx["target_checker"]["checker_target_score"]),
                "checker_role_score": int(ctx["role_checker"]["checker_role_score"]),
            },
        )

    def _repair_target_patch(self, base_fields: dict, patch_fields: dict) -> dict:
        from dart_research.cass.schema import repair_target_postprocess_patch

        return repair_target_postprocess_patch(base_fields, patch_fields)

    def _repair_combined_patch(self, base_fields: dict, patch_fields: dict) -> dict:
        from dart_research.cass.schema import repair_target_postprocess_plus_role_patch

        return repair_target_postprocess_plus_role_patch(base_fields, patch_fields)

    def _direct_expr_to_code(self, expr: str, equation: str) -> str:
        candidate = expr.strip()
        if not candidate and "=" in equation:
            candidate = equation.split("=", 1)[1].strip()
        if "=" in candidate:
            candidate = candidate.split("=", 1)[1].strip()
        candidate = candidate.replace("^", "**")
        return f"result = {candidate}" if candidate else ""

    def _f1_lite(self, example: BenchmarkExample, draft) -> tuple[ProbeRecord, ActionOutcome]:
        prompt = self.cass_r2_prompts.f1_lite.render(question=example.question)
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="cass_r2_f1_lite",
            prompt_version=self.cass_r2_prompts.f1_lite.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 180),
            metadata={"branch": "cass_r2", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        equation = str(fields.get("equation", "")).strip()
        solve_mode = str(fields.get("solve_mode", "")).strip().lower()
        direct_expr = str(fields.get("direct_expr", "")).strip()
        code = str(fields.get("code", "")).strip()
        if solve_mode == "direct":
            code = self._direct_expr_to_code(direct_expr, equation)
        exec_payload = execute_python_snippet(code) if code else {"success": 0, "result": "", "error": "no_code", "latency_s": 0.0}
        probe_metrics = response["metrics"]
        probe = ProbeRecord(
            action_name="F1_LITE",
            fields={
                "equation": equation,
                "solve_mode": solve_mode,
                "direct_expr": direct_expr,
                "code": code,
            },
            parse_ok=int(bool(equation or direct_expr or code)),
            input_tokens=probe_metrics.input_tokens,
            output_tokens=probe_metrics.output_tokens,
            latency_s=probe_metrics.latency_s + float(exec_payload["latency_s"]),
            raw_paths=[probe_metrics.raw_path],
        )
        answer = str(exec_payload["result"]).strip() if exec_payload["success"] else self._fallback_answer(
            fields.get("answer", ""),
            response["text"],
            example.task_type,
            default=draft.answer,
        )
        scratch = fields.get("scratch", self._fallback_scratch(response["text"], default=draft.scratch))
        action = self._make_action_outcome(
            example,
            action_name="F1_LITE",
            answer=answer,
            scratch=scratch,
            draft_correct=draft.correctness,
            metrics={
                "input_tokens": probe.input_tokens,
                "output_tokens": probe.output_tokens,
                "latency_s": probe.latency_s,
                "raw_paths": list(probe.raw_paths),
            },
            metadata={
                "equation": equation,
                "solve_mode": solve_mode,
                "direct_expr": direct_expr,
                "code": code,
                "model_answer": fields.get("answer", ""),
            },
            execution_used=1,
            execution_success=int(exec_payload["success"]),
            execution_result=str(exec_payload["result"]),
            action_failed=int(not exec_payload["success"] and not fields.get("answer")),
        )
        return probe, action

    def _prism_lite(
        self,
        example: BenchmarkExample,
        draft,
        *,
        action_map: dict[str, ActionOutcome],
    ) -> tuple[ProbeRecord, ActionOutcome]:
        prompt = self.cass_r2_prompts.prism_lite.render(
            question=example.question,
            answer=draft.answer,
            scratch=draft.scratch,
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="cass_r2_prism_lite",
            prompt_version=self.cass_r2_prompts.prism_lite.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=80,
            metadata={"branch": "cass_r2", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        strategy = str(fields.get("strategy", "")).strip()
        if strategy not in {"KEEP", "RAW_PYTHON", "OPERATOR_SCHEMA_TO_CODE_BASE", "ATLAS_FIELDWISE_SCHEMA_TO_CODE"}:
            strategy = "OPERATOR_SCHEMA_TO_CODE_BASE"
        chosen = action_map[strategy]
        metrics = response["metrics"]
        probe = ProbeRecord(
            action_name="PRISM_LITE",
            fields={"strategy": strategy, "reason": str(fields.get("reason", "")).strip()},
            parse_ok=int(bool(strategy)),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )
        action = ActionOutcome(
            action_name="PRISM_LITE",
            answer=chosen.answer,
            normalized_answer=chosen.normalized_answer,
            scratch=chosen.scratch,
            correctness=chosen.correctness,
            helpful=chosen.helpful,
            harmful=chosen.harmful,
            neutral=chosen.neutral,
            parse_ok=int(probe.parse_ok and chosen.parse_ok),
            action_failed=chosen.action_failed,
            execution_used=chosen.execution_used,
            execution_success=chosen.execution_success,
            execution_result=chosen.execution_result,
            input_tokens=int(chosen.input_tokens + probe.input_tokens),
            output_tokens=int(chosen.output_tokens + probe.output_tokens),
            latency_s=float(chosen.latency_s + probe.latency_s),
            raw_paths=list(chosen.raw_paths) + list(probe.raw_paths),
            metadata={
                **chosen.metadata,
                "planner_strategy": strategy,
                "planner_reason": str(fields.get("reason", "")).strip(),
            },
        )
        return probe, action
