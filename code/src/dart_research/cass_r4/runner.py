"""CASS round-4 (`cass_r4`) runner: adds the f1 high-fidelity plan/execute head.

Subclasses `CASSR2Runner` and appends a single `_f1_high_fidelity` probe /
action pair to each `ActionBankRecord`, which is what `cass_r4_collect.py`
calls into. This is the final math-side collection runner — its outputs feed
the math half of the `unify_live_full_r2` unified frame.
"""

from __future__ import annotations

from pathlib import Path

from dart_research.datasets.loaders import BenchmarkExample
from dart_research.eir.python_exec import execute_python_snippet
from dart_research.eir.types import ActionBankRecord, ActionOutcome, BaselineOutcome, ProbeRecord
from dart_research.parsing.tagged import extract_tagged_fields

from dart_research.cass_r2.runner import CASSR2Runner

from .prompts import CASSR4PromptBank


class CASSR4Runner(CASSR2Runner):
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
            frozen_drafts_path=frozen_drafts_path,
            save_drafts_path=save_drafts_path,
        )
        self.cass_r4_prompts = CASSR4PromptBank.load(repo_root)

    def collect_record(self, example: BenchmarkExample):
        record = super().collect_record(example)
        probe, action = self._f1_high_fidelity(example, record.draft)
        record.probes.append(probe)
        record.actions.append(action)
        record.prompt_bundle = self.cass_r4_prompts.version_bundle(base_bundle=record.prompt_bundle)
        return record

    def collect_record_model_light(self, example: BenchmarkExample) -> ActionBankRecord:
        ctx = self.build_patch_context(example)
        draft = ctx["draft"]
        cluster = ctx["cluster"]
        general_features = self._general_features(example, draft.answer, draft.scratch)
        state_features, _ = self._state_features(example, draft.answer, draft.scratch)

        keep_probe = self._keep_probe(example, draft.answer, draft.scratch)
        raw_probe = self._raw_python_probe(example, draft.answer, draft.scratch)
        base_probe = ctx["base_probe"]
        fieldwise_probe = ctx["fieldwise_probe"]
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
            combined_patch_probe,
        ]
        actions = [
            self._keep_action(example, draft),
            self._raw_python_action(example, draft, raw_probe),
            self._base_operator_action(example, draft, base_probe),
            self._schema_action(example, draft, fieldwise_probe, action_name="ATLAS_FIELDWISE_SCHEMA_TO_CODE"),
            self._schema_action(example, draft, combined_patch_probe, action_name="CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH"),
        ]

        f1_probe, f1_action = self._f1_high_fidelity(example, draft)
        probes.append(f1_probe)
        actions.append(f1_action)

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
        }
        prompt_bundle = self.tier_prompts.version_bundle(eir_prompts=self.prompts, heir_prompts=self.heir_prompts)
        prompt_bundle = self.atlas_rg_prompts.version_bundle(base_bundle=prompt_bundle)
        prompt_bundle = self.cass_prompts.version_bundle(base_bundle=prompt_bundle)
        prompt_bundle = self.cass_r2_prompts.version_bundle(base_bundle=prompt_bundle)
        prompt_bundle = self.cass_r4_prompts.version_bundle(base_bundle=prompt_bundle)
        prompt_bundle.update(
            {
                "atlas_field_semantics": self.atlas_prompts.field_semantics.version,
                "atlas_field_quantities": self.atlas_prompts.field_quantities.version,
                "method_pack": "model_light",
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
                "method_pack": "model_light",
            },
        )

    def _f1_high_fidelity(self, example: BenchmarkExample, draft) -> tuple[ProbeRecord, ActionOutcome]:
        plan_prompt = self.cass_r4_prompts.f1_plan.render(question=example.question)
        plan_response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="cass_r4_f1_plan",
            prompt_version=self.cass_r4_prompts.f1_plan.version,
            prompt_text=plan_prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 220),
            metadata={"branch": "cass_r4", "dataset": example.dataset, "question_id": example.question_id, "stage": "f1_plan"},
            system_text="Return exactly the requested tags and nothing else.",
        )
        plan_fields = extract_tagged_fields(plan_response["text"])
        equations = str(plan_fields.get("equations", "")).strip()
        target = str(plan_fields.get("target", "")).strip()
        solve_mode = str(plan_fields.get("solve_mode", "")).strip().lower()
        direct_expr_hint = str(plan_fields.get("direct_expr_hint", "")).strip()
        variables = str(plan_fields.get("variables", "")).strip()
        notes = str(plan_fields.get("notes", "")).strip()

        exec_prompt = self.cass_r4_prompts.f1_execute.render(
            question=example.question,
            variables=variables,
            equations=equations,
            target=target,
            solve_mode=solve_mode,
            direct_expr_hint=direct_expr_hint,
        )
        exec_response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="cass_r4_f1_execute",
            prompt_version=self.cass_r4_prompts.f1_execute.version,
            prompt_text=exec_prompt,
            temperature=0.0,
            max_output_tokens=min(self.max_output_tokens, 220),
            metadata={"branch": "cass_r4", "dataset": example.dataset, "question_id": example.question_id, "stage": "f1_execute"},
            system_text="Return exactly the requested tags and nothing else.",
        )
        exec_fields = extract_tagged_fields(exec_response["text"])
        direct_expr = str(exec_fields.get("direct_expr", "")).strip() or direct_expr_hint
        code = str(exec_fields.get("code", "")).strip()
        if solve_mode == "direct":
            code = self._direct_expr_to_code(direct_expr, target or equations)
        exec_payload = execute_python_snippet(code) if code else {"success": 0, "result": "", "error": "no_code", "latency_s": 0.0}

        plan_metrics = plan_response["metrics"]
        exec_metrics = exec_response["metrics"]
        probe = ProbeRecord(
            action_name="F1_HIGH_FIDELITY",
            fields={
                "variables": variables,
                "equations": equations,
                "target": target,
                "solve_mode": solve_mode,
                "direct_expr_hint": direct_expr_hint,
                "direct_expr": direct_expr,
                "code": code,
                "notes": notes,
            },
            parse_ok=int(bool(equations or target or direct_expr or code)),
            input_tokens=int(plan_metrics.input_tokens + exec_metrics.input_tokens),
            output_tokens=int(plan_metrics.output_tokens + exec_metrics.output_tokens),
            latency_s=float(plan_metrics.latency_s + exec_metrics.latency_s + float(exec_payload["latency_s"])),
            raw_paths=[plan_metrics.raw_path, exec_metrics.raw_path],
        )
        answer = str(exec_payload["result"]).strip() if exec_payload["success"] else self._fallback_answer(
            exec_fields.get("answer", ""),
            exec_response["text"],
            example.task_type,
            default=draft.answer,
        )
        scratch = exec_fields.get("scratch", self._fallback_scratch(exec_response["text"], default=draft.scratch))
        action = self._make_action_outcome(
            example,
            action_name="F1_HIGH_FIDELITY",
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
                "variables": variables,
                "equations": equations,
                "target": target,
                "solve_mode": solve_mode,
                "direct_expr_hint": direct_expr_hint,
                "direct_expr": direct_expr,
                "code": code,
                "notes": notes,
                "model_answer": exec_fields.get("answer", ""),
            },
            execution_used=1,
            execution_success=int(exec_payload["success"]),
            execution_result=str(exec_payload["result"]),
            action_failed=int(not exec_payload["success"] and not exec_fields.get("answer")),
        )
        return probe, action
