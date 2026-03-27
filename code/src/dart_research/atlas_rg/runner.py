from __future__ import annotations

from pathlib import Path
import json

from dart_research.atlas.runner import ATLASInterfaceBankRunner
from dart_research.datasets.loaders import BenchmarkExample
from dart_research.eir.types import ActionBankRecord, BaselineOutcome, DraftRecord, ProbeRecord
from dart_research.oscar.compiler import assign_semantic_cluster, parse_schema_fields, schema_to_preview
from dart_research.parsing.tagged import extract_tagged_fields
from dart_research.utils.io import append_jsonl

from .prompts import ATLASRGPromptBank
from .retrieval import TeacherRoleSeedExample, load_teacher_seed, render_teacher_exemplars, retrieve_teacher_exemplars
from .schema import (
    compose_role_grounded_schema,
    parse_quantity_rows,
    repair_critical_role_fields,
    repair_nonrole_fields,
    repair_role_fields,
)


ATLAS_RG_METHOD_NAMES = [
    "KEEP",
    "RAW_PYTHON",
    "OPERATOR_SCHEMA_TO_CODE_BASE",
    "ATLAS_FIELDWISE_SCHEMA_TO_CODE",
    "ATLAS_RG_ROLETABLE_TO_CODE",
    "ATLAS_RG_ROLE_REPAIR_ONLY",
    "ATLAS_RG_NONROLE_REPAIR_ONLY",
    "ATLAS_RG_CRITICAL_ROLE_REPAIR",
    "TEACHER_ROLETABLE_TO_CODE",
]


class ATLASRGInterfaceBankRunner(ATLASInterfaceBankRunner):
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
        enable_critical_role_repair: bool = False,
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
            enable_critical_repair=False,
        )
        self.atlas_rg_prompts = ATLASRGPromptBank.load(repo_root)
        self.role_teacher_seed_path = teacher_seed_path
        self.teacher_seed_source = "none"
        self.teacher_seed_examples: list[TeacherRoleSeedExample] = []
        self.teacher_by_id: dict[str, TeacherRoleSeedExample] = {}
        if teacher_seed_path is not None and teacher_seed_path.exists():
            parent_name = teacher_seed_path.parent.name.strip()
            stem = teacher_seed_path.stem.strip()
            self.teacher_seed_source = parent_name or stem or "seed"
            self.teacher_seed_examples = load_teacher_seed(teacher_seed_path)
            self.teacher_by_id = {item.question_id: item for item in self.teacher_seed_examples}
        self.retrieval_mode = retrieval_mode
        self.enable_critical_role_repair = enable_critical_role_repair
        self.frozen_drafts_path = frozen_drafts_path
        self.save_drafts_path = save_drafts_path
        self.frozen_drafts: dict[str, DraftRecord] = {}
        if frozen_drafts_path is not None and frozen_drafts_path.exists():
            for line in frozen_drafts_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                raw = json.loads(line)
                draft_raw = raw.get("draft", raw)
                self.frozen_drafts[str(raw["question_id"])] = DraftRecord(
                    answer=str(draft_raw["answer"]),
                    normalized_answer=str(draft_raw["normalized_answer"]),
                    scratch=str(draft_raw["scratch"]),
                    correctness=int(draft_raw["correctness"]),
                    input_tokens=int(draft_raw.get("input_tokens", 0)),
                    output_tokens=int(draft_raw.get("output_tokens", 0)),
                    latency_s=float(draft_raw.get("latency_s", 0.0)),
                    raw_paths=list(draft_raw.get("raw_paths", [])),
                )


    def _draft_for_example(self, example: BenchmarkExample) -> tuple[DraftRecord, str]:
        frozen = self.frozen_drafts.get(example.question_id)
        if frozen is not None:
            return frozen, "frozen"
        draft = self._draft(example)
        self.frozen_drafts[example.question_id] = draft
        if self.save_drafts_path is not None:
            append_jsonl(
                self.save_drafts_path,
                {
                    "dataset": example.dataset,
                    "question_id": example.question_id,
                    "draft": draft.to_dict(),
                },
            )
        return draft, "fresh"

    def collect_record(self, example: BenchmarkExample) -> ActionBankRecord:
        draft, draft_source = self._draft_for_example(example)
        general_features = self._general_features(example, draft.answer, draft.scratch)
        state_features, _ = self._state_features(example, draft.answer, draft.scratch)
        cluster = assign_semantic_cluster(example.question)

        keep_probe = self._keep_probe(example, draft.answer, draft.scratch)
        raw_probe = self._raw_python_probe(example, draft.answer, draft.scratch)
        base_probe = self._operator_probe(example, draft.answer, draft.scratch)
        fieldwise_probe = self._fieldwise_schema_probe(example, draft.answer, draft.scratch, cluster)
        role_probe = self._role_grounded_schema_probe(example, draft.answer, draft.scratch, cluster, fieldwise_probe)
        role_repair_probe = self._role_repair_probe(example, draft.answer, draft.scratch, fieldwise_probe, cluster)
        nonrole_repair_probe = self._nonrole_repair_probe(example, draft.answer, draft.scratch, fieldwise_probe, cluster)
        probes = [keep_probe, raw_probe, base_probe, fieldwise_probe, role_probe, role_repair_probe, nonrole_repair_probe]

        actions = [
            self._keep_action(example, draft),
            self._raw_python_action(example, draft, raw_probe),
            self._base_operator_action(example, draft, base_probe),
            self._schema_action(example, draft, fieldwise_probe, action_name="ATLAS_FIELDWISE_SCHEMA_TO_CODE"),
            self._schema_action(example, draft, role_probe, action_name="ATLAS_RG_ROLETABLE_TO_CODE"),
            self._schema_action(example, draft, role_repair_probe, action_name="ATLAS_RG_ROLE_REPAIR_ONLY"),
            self._schema_action(example, draft, nonrole_repair_probe, action_name="ATLAS_RG_NONROLE_REPAIR_ONLY"),
        ]

        if self.enable_critical_role_repair:
            critical_role_probe = self._critical_role_repair_probe(example, draft.answer, draft.scratch, fieldwise_probe, cluster)
            probes.append(critical_role_probe)
            actions.append(self._schema_action(example, draft, critical_role_probe, action_name="ATLAS_RG_CRITICAL_ROLE_REPAIR"))

        teacher_probe = self._teacher_probe(example)
        if teacher_probe is not None:
            probes.append(teacher_probe)
            actions.append(self._schema_action(example, draft, teacher_probe, action_name="TEACHER_ROLETABLE_TO_CODE"))

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
        }
        prompt_bundle = self.tier_prompts.version_bundle(eir_prompts=self.prompts, heir_prompts=self.heir_prompts)
        prompt_bundle = self.atlas_rg_prompts.version_bundle(base_bundle=prompt_bundle)
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
                "enable_critical_role_repair": int(self.enable_critical_role_repair),
                "draft_source": draft_source,
            },
        )

    def _role_signature(self, quantities: str) -> str:
        pairs = sorted(f"{row.get('role', 'none')}:{row.get('entity', 'none')}" for row in parse_quantity_rows(quantities))
        return ",".join(item for item in pairs if item)

    def _role_grounded_schema_probe(
        self,
        example: BenchmarkExample,
        answer: str,
        scratch: str,
        cluster: str,
        base_probe: ProbeRecord,
    ) -> ProbeRecord:
        role_signature = self._role_signature(str(base_probe.fields.get("quantities", "")))
        exemplars = retrieve_teacher_exemplars(
            question=example.question,
            cluster=cluster,
            role_signature=role_signature,
            seed_examples=self.teacher_seed_examples,
            mode=self.retrieval_mode,
            top_k=3,
            exclude_question_id=example.question_id,
        )
        prompt = self.atlas_rg_prompts.retrieval_role_schema.render(
            cluster_hint=cluster,
            role_signature=role_signature or "none",
            retrieved_examples=render_teacher_exemplars(exemplars),
            question=example.question,
            answer=self._ctx_answer(answer),
            scratch=self._ctx_scratch(scratch),
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="atlas_rg_retrieval_role_schema",
            prompt_version=self.atlas_rg_prompts.retrieval_role_schema.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=240,
            metadata={"branch": "atlas_rg", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        return self._make_schema_probe(
            response,
            action_name="ATLAS_RG_ROLETABLE_TO_CODE",
            extra_fields={
                "retrieval_mode": self.retrieval_mode,
                "role_signature": role_signature,
                "retrieved_ids": ",".join(item.question_id for item in exemplars),
                "retrieved_clusters": ",".join(item.cluster for item in exemplars),
            },
        )

    def _role_repair_probe(
        self,
        example: BenchmarkExample,
        answer: str,
        scratch: str,
        base_probe: ProbeRecord,
        cluster: str,
    ) -> ProbeRecord:
        prompt = self.atlas_rg_prompts.role_table.render(
            cluster_hint=cluster,
            question=example.question,
            answer=self._ctx_answer(answer),
            scratch=self._ctx_scratch(scratch),
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="atlas_rg_role_table_repair",
            prompt_version=self.atlas_rg_prompts.role_table.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=180,
            metadata={"branch": "atlas_rg", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        repaired = repair_role_fields(dict(base_probe.fields), fields)
        metrics = response["metrics"]
        return ProbeRecord(
            action_name="ATLAS_RG_ROLE_REPAIR_ONLY",
            fields=repaired,
            parse_ok=int(bool(fields)),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )

    def _nonrole_repair_probe(
        self,
        example: BenchmarkExample,
        answer: str,
        scratch: str,
        base_probe: ProbeRecord,
        cluster: str,
    ) -> ProbeRecord:
        current_schema = schema_to_preview(parse_schema_fields(base_probe.fields))
        prompt = self.atlas_rg_prompts.nonrole_repair.render(
            cluster_hint=cluster,
            question=example.question,
            answer=self._ctx_answer(answer),
            scratch=self._ctx_scratch(scratch),
            current_schema=current_schema,
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="atlas_rg_nonrole_repair",
            prompt_version=self.atlas_rg_prompts.nonrole_repair.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=120,
            metadata={"branch": "atlas_rg", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        repaired = repair_nonrole_fields(dict(base_probe.fields), fields)
        metrics = response["metrics"]
        return ProbeRecord(
            action_name="ATLAS_RG_NONROLE_REPAIR_ONLY",
            fields=repaired,
            parse_ok=int(bool(fields)),
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            latency_s=metrics.latency_s,
            raw_paths=[metrics.raw_path],
        )

    def _critical_role_repair_probe(
        self,
        example: BenchmarkExample,
        answer: str,
        scratch: str,
        base_probe: ProbeRecord,
        cluster: str,
    ) -> ProbeRecord:
        current_schema = schema_to_preview(parse_schema_fields(base_probe.fields))
        prompt = self.atlas_rg_prompts.critical_role_repair.render(
            cluster_hint=cluster,
            question=example.question,
            answer=self._ctx_answer(answer),
            scratch=self._ctx_scratch(scratch),
            current_schema=current_schema,
        )
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="atlas_rg_critical_role_repair",
            prompt_version=self.atlas_rg_prompts.critical_role_repair.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=140,
            metadata={"branch": "atlas_rg", "dataset": example.dataset, "question_id": example.question_id},
            system_text="Return exactly the requested tags and nothing else.",
        )
        fields = extract_tagged_fields(response["text"])
        repaired = repair_critical_role_fields(dict(base_probe.fields), fields)
        metrics = response["metrics"]
        return ProbeRecord(
            action_name="ATLAS_RG_CRITICAL_ROLE_REPAIR",
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
            action_name="TEACHER_ROLETABLE_TO_CODE",
            fields=dict(teacher.schema_fields),
            parse_ok=int(teacher.audit_ok),
            input_tokens=0,
            output_tokens=0,
            latency_s=0.0,
            raw_paths=[],
        )
