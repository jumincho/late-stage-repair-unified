from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from dart_research.clients.hf_local import HFTransformersClient
from dart_research.datasets.loaders import BenchmarkExample
from dart_research.eir.runner import EIRActionBankRunner
from dart_research.eir.types import ActionBankRecord, BaselineOutcome, ProbeRecord
from dart_research.heir.prompts import HEIRPromptBank
from dart_research.parsing.tagged import extract_tagged_fields
from dart_research.vchase.prm import ProcessRewardModelScorer


class HEIRActionBankRunner(EIRActionBankRunner):
    """Collect a pruned HEIR action bank with an explicit keep preview."""

    def __init__(
        self,
        *,
        repo_root: Path,
        client: HFTransformersClient,
        model_name: str,
        prm_scorer: ProcessRewardModelScorer | None = None,
        max_output_tokens: int = 180,
    ) -> None:
        super().__init__(
            repo_root=repo_root,
            client=client,
            model_name=model_name,
            prm_scorer=prm_scorer,
            max_output_tokens=max_output_tokens,
            use_constraint_checklist=False,
        )
        self.heir_prompts = HEIRPromptBank.load(repo_root)

    def collect_record(self, example: BenchmarkExample) -> ActionBankRecord:
        draft = self._draft(example)
        general_features = self._general_features(example, draft.answer, draft.scratch)
        state_features, _ = self._state_features(example, draft.answer, draft.scratch)
        probes = [
            self._keep_probe(example, draft.answer, draft.scratch),
            self._freeform_probe(example, draft.answer, draft.scratch),
            self._python_probe(example, draft.answer, draft.scratch),
            self._localize_probe(example, draft.answer, draft.scratch),
        ]
        probe_map = {probe.action_name: probe for probe in probes}
        actions = [
            self._stop_action(example, draft),
            self._freeform_action(example, draft, probe_map["FREEFORM_CRITIQUE"]),
            self._python_action(example, draft, probe_map["PYTHON_RECOMPUTE"]),
            self._localize_action(example, draft, probe_map["LOCALIZE_BACKTRACK"]),
        ]
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
            prompt_bundle=self.heir_prompts.version_bundle(eir_prompts=self.prompts),
            draft=draft,
            general_features=general_features,
            state_features=state_features,
            probes=probes,
            actions=actions,
            baselines=baselines,
            metadata=example.metadata,
        )

    def _keep_probe(self, example: BenchmarkExample, answer: str, scratch: str) -> ProbeRecord:
        prompt = self.heir_prompts.keep_probe.render(question=example.question, answer=answer, scratch=scratch)
        response = self.client.generate_text(
            model_name=self.model_name,
            prompt_name="heir_keep_probe",
            prompt_version=self.heir_prompts.keep_probe.version,
            prompt_text=prompt,
            temperature=0.0,
            max_output_tokens=80,
            metadata={"branch": "heir", "dataset": example.dataset, "question_id": example.question_id},
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
            action_name="STOP",
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
