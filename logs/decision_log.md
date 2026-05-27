# Decision Log

## 2026-03-26

### UNIFY-LIVE-FULL-R2 Qwen-14B throughput decision

- The first clean `Qwen-14B` restart under `R2` was stable but under-utilized.
- Observed behavior on the original `4`-shard path:
  - roughly `30–40%` GPU utilization in the early generation-heavy window
  - roughly `~11 GB` used per `24 GB` GPU
- That path was therefore stopped under the already-registered rule:
  - if a generation-heavy phase remains below `80%` utilization for more than `10` minutes, fix the runner before continuing

### Qwen-14B execution correction

- Keep the model family fixed.
- Keep the task surfaces, validators, local primitives, and action mapping fixed.
- Change only the serving/concurrency geometry for `Qwen-14B` collection:
  - allow `2` worker slots per GPU
  - reshard the `Qwen-14B` collection path to `8` shards per surface
  - distribute slots round-robin across all `4` GPUs before filling second slots

Why:

- A same-GPU dual-slot smoke on `Qwen/Qwen2.5-14B-Instruct` `4bit` showed that a single `RTX 3090` can sustain about `22 GB` allocation and reach `100%` utilization with two concurrent workers.
- The original `4`-shard path could not benefit from that because the per-phase worker count was capped at `4`.
- The corrected `8`-way path raises concurrency to `8` without changing any empirical surface semantics.

Effect:

- The active `Qwen-14B` collection should run from:
  - `/workspace/project/results/unify_live_full_r2_shared_qwen14_8way`
- The active serving policy should use:
  - `UNIFY_LIVE_GPU_SLOTS_PER_DEVICE=2`
- The corrected clean restart should be tracked under:
  - `/workspace/project/results/unify_live_full_r2_qwen14b/qwen14b_attempt2_20260326b`

## 2026-03-24

### UNIFY-LIVE-FULL framing

- `UNIFY-LIVE-FULL` is a main-volume prospective integration pack, not a new methods branch.
- The frozen math and format methods remain unchanged.
- The phase goal is not broader domain expansion; it is fresh online confirmation of a shared cross-domain intervention geometry.

### Cross-domain action mapping decision

- Keep one shared abstract action space:
  - `NO_INTERVENTION`
  - `LOCAL_REPAIR`
  - `GLOBAL_REWRITE_OR_RESTART`
- Freeze the math-side local executor to the safest already-supported primitive:
  - postprocess/discretization-centered local replay
- Freeze the format-side local executor to the strongest already-supported local executor from the format packs.
- Do not invent or widen the local action family in this phase.

### Prospective-evidence decision

- The main evidence in this phase must come from fresh online traces.
- Frozen-trace re-analysis from `UNIFY-FULL` is allowed only as context, not as the main result.
- To prevent accidental cache reuse from prior branches, fresh cache namespaces must be used for `UNIFY-LIVE-FULL` collection.

### Split-stability decision

- Freeze at least `3` split seeds for train / calibration / evaluation.
- The unified story should not depend on one lucky split.
- Report mean and spread over split seeds for:
  - pooled simple rules
  - domain-tuned simple rules
  - pooled learned gate

### Execution-policy decision

- Heavy collection remains local-first on `4x RTX 3090`.
- Generation-heavy phases must use all `4` GPUs strongly.
- If a generation-heavy phase stays below `80%` utilization for more than `10` minutes, stop and fix the runner before continuing.
- Validator-only phases may be CPU-bound and are not treated as utilization failures.

### Model-scope decision

- Required:
  - `Qwen/Qwen2.5-7B-Instruct`
  - `mistralai/Mistral-7B-Instruct-v0.3`
  - `Qwen/Qwen2.5-14B-Instruct`, if the local path is stable
- No additional model families will be opened in this phase.

## 2026-03-17

### LAST-PACK framing

- `LAST-PACK` is a sidecar empirical support pack, not a new methods branch.
- The frozen `CASS` abstraction remains unchanged.
- No new sparse-patch family, no new arithmetic interface family, and no new main claim surface will be introduced here.

### Math analysis decision

- Reuse existing `CASS` traces wherever possible.
- Treat:
  - `asdiv_easy_main` as the easy floor
  - `gsm8k_train_generic_main` as medium
  - `gsm8k_train_cluster_main` as hard
- If the easy floor has too few failures for conditional stage analysis, keep it as a floor and compare medium vs hard conditional failure composition.

### Planning-pack decision

- Use deterministic `gridworld` as the main beyond-math planning domain.
- Do not expand to a second planning domain unless the single-domain evidence is too weak and the extension remains low-friction.
- The registered comparison is:
  - direct plan
  - full restart after validator failure
  - suffix repair from the first failing step
- If the first suffix-repair realization is too weak because the handoff state is underspecified, allow one bounded pivot to an explicit state-snapshot suffix-repair prompt.

### Format-pack decision

- Use `IFEval` and `IFBench` as the main beyond-math output-constraint probes.
- Add a planning-format bridge slice to disentangle semantic correctness from output-format correctness.
- The registered comparison is:
  - direct formatted generation
  - full rewrite on failure
  - solve-then-format
  - format-only patch
- If format-only patch is too weak due to poor failure localization, allow one bounded pivot to validator-feedback patching while keeping tasks and validators fixed.

### Criterion-analysis decision

- The cross-module intervention criterion must stay simple and interpretable.
- Prefer validator-accessible features over opaque scores:
  - failure position ratio
  - prefix validity
  - violation type
  - math target/postprocess suspicion
  - math role suspicion
  - format-only vs semantic failure separation where available
- A lightweight pooled classifier is allowed only as a secondary comparison against the heuristic rule.

### Execution-policy decision

- Remain local-first and API-free in this phase.
- Use 4x `RTX 3090` with one generation worker per GPU.
- Keep prompts short and stable; do not broad-prompt-chase.
- If a first realization underperforms, pivot inside the registered bounded pack before concluding.

### Smoke-driven pivots before heavy collection

- The planning domain is pivoted from `gridworld` to deterministic `lineworld` with a locked-door prerequisite.
- `gridworld` is retained only as a discarded pilot.
- `FORMAT_ONLY_PATCH` is upgraded from LLM-only repair to deterministic-first local constraint patching with LLM fallback.

Why:

- The `gridworld` pilot mostly measured 2D coordinate tracking rather than localized repair quality.
- The `lineworld` pilot produced the intended localized-repair regime:
  - on the mixed smoke subset, easy direct failures were mostly early / incomplete (`failure_position_ratio` mean about `0.062`)
  - hard direct failures were late and reusable (`failure_position_ratio` mean `1.000`)
  - `suffix_repair` already outperformed `full_restart` on the hard smoke subset
- The `IFBench` pilot exposed exact keyword-count misses as the dominant failure type, which is better handled by a deterministic constraint-only patch than by another full rewrite.

Effect:

- Heavy planning collection will use `lineworld`, not `gridworld`.
- Heavy format collection will keep official `IFEval` / `IFBench` evaluators but will route `FORMAT_ONLY_PATCH` through deterministic local patching first.
- The runtime expectation is revised downward before heavy launch because the stabilized local path is substantially lighter than the conservative preregistration estimate.

## 2026-03-15

### CASS-R4 framing

- `CASS-R4` is a reviewer-proofing phase, not a new methods branch.
- The frozen `CASS` abstraction remains unchanged.
- No new patch family, no new schema family, and no new answer-normalization rule will be introduced in this phase.

### Comparator fidelity decisions

- `PRISM` remains a direct comparator.
- Official `PRISM` code exists and was audited locally, but it will not be claimed as an official reproduction here.
- The correct comparator label for this phase is:
  - `PRISM_HIGH_FIDELITY`: stronger-faithfulness local adaptation
- The required preserved ingredients are:
  - multi-strategy bank
  - offline strategy-supervision table
  - lightweight adapter training
  - thresholded adaptive routing

- `Formula-One Prompting` remains a direct comparator.
- No low-friction official code path was confirmed in this environment.
- The correct comparator label for this phase is:
  - `F1_HIGH_FIDELITY`: stronger-faithfulness local adaptation
- The required preserved ingredients are:
  - equation-first intermediate representation
  - downstream solve-mode choice

### Fairness-surface decisions

- The primary `CASS-R3` cluster-hard and generic-hard surfaces remain frozen.
- Additional fairness surfaces are allowed only as bounded support surfaces:
  - `PRISM`-aligned mixed arithmetic surface
  - `F1` bridge slice
- These surfaces are for reviewer-facing fairness and alignment checks only.
- They do not replace the primary locked `CASS` claim surface.

### Model-diversity decision

- The secondary replication model is fixed to `Qwen/Qwen2.5-Math-7B-Instruct`.
- A tertiary model will not be introduced unless it is already available at very low friction.
- The second-model check is explicitly a reduced-scale robustness audit, not a new benchmark campaign.

### Execution-policy decisions

- Heavy collection remains local-first on 4x `RTX 3090`.
- Use one generation worker per GPU and shard manifests rather than retuning prompts.
- `CASS` prompts remain frozen unless a trivial parse-only fix is required.
- `PRISM_HIGH_FIDELITY` threshold tuning is allowed only inside the comparator adapter path, not inside the frozen `CASS` method.

### CASS-R4 final submission decision

Context:

- `CASS-R3` had already locked the primary claim against `RAW_PYTHON` and `OPERATOR_SCHEMA_TO_CODE_BASE`.
- `CASS-R4` was launched only to answer reviewer-facing fairness questions:
  - whether a stronger-fidelity `PRISM` still trails `CASS`
  - whether a more benchmark-aligned `F1` comparison changes the reading
  - whether the effect direction survives a reduced second model

Decision:

- Promote the frozen `CASS` package as reviewer-robust enough for top-tier main-track submission.

Why:

- The primary preregistered lock remains intact in the `R4` analysis pack:
  - `CASS_CONSERVATIVE_GATE - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0207`, `95% CI [0.0007, 0.0422]`
- Stronger-fidelity `PRISM` still trails `CASS` on primary cluster-hard:
  - `CASS_CONSERVATIVE_GATE - PRISM_HIGH_FIDELITY = +0.0335`, `95% CI [0.0132, 0.0548]`
- Stronger-fidelity `F1` improves over `F1_LITE` but still trails `CASS`:
  - primary cluster-hard `CASS - F1_HIGH_FIDELITY = +0.0880`, `95% CI [0.0614, 0.1155]`
  - bridge slice `CASS - F1_HIGH_FIDELITY = +0.0543`, `95% CI [-0.0200, 0.1300]`
- Reduced `Qwen/Qwen2.5-Math-7B-Instruct` replication preserves the direction of the gain:
  - cluster-hard `CASS - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0629`, `95% CI [0.0333, 0.0967]`

Effect:

- Keep the paper centered on:
  - conservative target/postprocess-centered sparse schema surgery
  - cluster-hard arithmetic as the primary claim surface
- Report comparator caveats explicitly:
  - `PRISM_HIGH_FIDELITY` is a stronger-faithfulness adaptation, not an official reproduction
  - the `F1` bridge slice is a proxy alignment surface, not the original benchmark
- Report model-diversity caveats explicitly:
  - the second-model result is reduced-scale
  - it remains within the Qwen family
  - it supports robustness of direction, not absolute cross-model portability

## 2026-03-09

### Chosen framing

- DART is implemented as an inference-only workflow paper, not a training method.
- For open-ended tasks, the candidate set is treated as a hypothesis set rather than a closed answer set.
- The final answer may be outside the candidate set, which is essential for distinguishing selection from rebuttal + regeneration.

### Early design choices

- Use concise JSON schemas with Pydantic validation instead of free-form traces.
- Save raw API outputs before parsing for debugging and reproducibility.
- Keep prompts in plain text files with explicit `VERSION:` headers.
- Make OpenAI the default backend and include a deterministic `mock` backend for smoke tests.
- Keep batch/local-vLLM support as optional extensions, not the main execution path.

### Risk controls

- No benchmark gold answers inside the inference pipeline.
- No secrets written to tracked files.
- Resume logic and caching are mandatory before real runs.
- StrategyQA dataset identifier may vary by environment; loader will support fallbacks and log which source was used.

### Execution-time adjustments

- Use `google/boolq` as the first accessible yes/no fallback under the `strategyqa` config key in this environment.
- For gpt-5 Responses API calls, do not send `temperature`; some models reject it.
- For gpt-5 Responses API calls, force `reasoning.effort=minimal` and `text.verbosity=low` to reduce incomplete no-text responses.
- Accept lightweight JSON repair before schema validation because intermediate outputs are required to remain observable and concise, not perfectly tokenized.

### Pilot-based observations

- Keep `mc_select_only` as an explicit baseline; it already shows a strong contrast on the yes/no pilot slice.
- For evaluation, derive normalized predictions from the actual `answer` field rather than trusting model-supplied `normalized_answer`; this fixed a real pilot scoring bug.
- Do not overclaim from the current pilot: `dart_adv` looks promising on yes/no, but `self_refine_1` and `self_consistency_5` remain strong baselines and sometimes win outright.
- ARC-Challenge after the normalization fix no longer provides the strong negative signal seen in the earlier buggy evaluation run, so any claim about native MC now needs a larger held-out slice.

### Phase 2 scope narrowing

- The working claim for held-out execution is narrowed:
  - `dart_adv` is most promising on closed-label reasoning, especially BoolQ-style yes/no tasks.
  - On GSM8K-style arithmetic, DART should be evaluated as a potentially useful repair workflow, not presumed to beat `self_refine_1`.
  - On ARC, the key question is whether rebuttal and fresh-context finalization help beyond strict option selection when candidate coverage is guaranteed.
- The paper should now optimize for honest task-family differentiation, not for a single universal leaderboard claim.

### Metric audit finding

- The pilot field previously reported as `duplicate_rate` was actually a per-example duplicate count average.
- Follow-up reporting must use correctly named metrics:
  - `avg_duplicate_count`
  - `duplicate_fraction`
  - `avg_raw_candidates`
  - `avg_kept_candidates`

### Freeze-pass decisions

- Shared-candidate ablations must reuse the same cached artifact per example; causal ladders should differ only in downstream selection / rebuttal / finalization, not in upstream candidate generation.
- BoolQ uses a hard closed candidate set `{YES, NO}` for DART-Adv and selection baselines in phase 2.
- ARC finalization is split into:
  - same-context option-only finalization
  - fresh-context option-only finalization
  This is necessary because the dev check showed same-context can be safer than fresh-context when candidate coverage is guaranteed.
- OpenAI cache keys no longer include run metadata because metadata does not affect the request text. Keeping it in the cache key would create avoidable duplicate spend and unwanted output variance across logically identical prompts.
- Prompt/config freeze point is `results/devcheck/phase2_openai_dev_freeze`.
- Held-out main sample sizes are approved at `150 / 150 / 150` because the freeze-precheck cost projection remains comfortably under the preferred additional spend target.

### Post-heldout claim revision

- The held-out data invalidated the pilot-era expectation that closed-label reasoning would be the cleanest DART win.
- Updated supported story:
  - DART is strongest on open-ended arithmetic where candidate coverage is incomplete and regeneration can produce a correct answer outside the candidate set.
  - On BoolQ, strict closed-label selection beats DART finalization.
  - On ARC, fresh-context regeneration is not supported; same-context option finalization is the only mildly positive regeneration variant.
- Paper positioning should therefore shift away from “closed-label reasoning improvement” and toward:
  - a nuanced methods paper on selection vs rebuttal vs regeneration, or
  - a sharper open-ended/auditable-regeneration paper if a second open-ended benchmark confirms the GSM8K pattern.

### Phase 3 strategic pivot

- Positive regime is now explicitly defined as open-ended arithmetic with incomplete candidate coverage.
- BoolQ and ARC are retained as contrast / negative-control evidence, not as targets to optimize.
- Fresh-context finalization should no longer be presented as the universal mechanism:
  - on GSM8K it is competitive and useful
  - on ARC same-context option finalization can be safer
  - on BoolQ fresh finalization adds variance rather than value
- The core mechanistic claim to test in phase 3 is narrower:
  - selection-only is already strong when the answer space is closed and coverage is complete
  - on open-ended reasoning with incomplete candidate coverage, rebuttal + regeneration can matter beyond selection
- The main unresolved reviewer risk is now:
  - whether the GSM8K gain is specific to explicit auditable hypothesis sets, or whether generic adversarial critique / extra compute would explain the same improvement
- Therefore phase 3 should prioritize:
  - new open-ended confirmation data
  - direct controls against generic critique and extra compute
  - prospective candidate-diversity changes only after frozen-v1 confirmation

### Post-confirmation phase 3 conclusion

- The open-ended arithmetic result is now replicated on both GSM8K and SVAMP, so the project no longer looks GSM8K-only.
- The best-supported causal statement is:
  - selection-only is too weak when candidate coverage is incomplete
  - rebuttal + regeneration matters
  - same-context finalization is currently safer than fresh-context finalization
- The previously attractive “auditable candidate sets are the key differentiator” story is not supported by the new controls:
  - `freeform_devil_advocate_fresh` is stronger than `dart_adv_fresh` on GSM8K
  - `freeform_devil_advocate_fresh` is at least competitive with the best DART variant on SVAMP
  - `self_refine_1` and `self_refine_2_budgetmatched` remain serious baselines and are not cleanly separated by DART
- Therefore the recommended paper posture is narrower:
  - keep the auditable candidate-set framing as a design choice and analysis aid
  - do not claim that explicit candidate sets are necessary for the gain
  - center the paper on boundary conditions:
    - closed-label tasks: selection already strong
    - open-ended arithmetic: rebuttal + regeneration helps beyond selection
    - fresh-context is not universal best; same-context may be preferable
- Because candidate collapse remains severe (`~5` raw -> `~1` kept), a prospective v2 candidate-diversity improvement could still be explored later, but it is no longer required for the current paper package.

### Phase 4 objective and stopping rules

- Phase 4 exists only to test one prospectively justified idea:
  - whether repairing candidate collapse can strengthen the auditable-candidate-set story on new open-ended data
- Same-context is now the default DART finalization target:
  - fair controls must also include same-context variants
  - fresh-context is retained only as a continuity control, not as the main mechanism
- The only allowed global method change in phase 4 is upstream candidate-diversity repair:
  - persona-sharded proposal
  - hard novelty constraints
  - one repair pass if diversity remains too low
- Phase 4 should stop immediately if any of the following hold:
  - v2 does not improve diversity on new dev data
  - v2 improves diversity but not accuracy over `dart_adv_same_v1`
  - v2 remains clearly behind fair freeform same-context controls
  - cost approaches the hard cap before the minimal prospective retest is complete
- If phase 4 fails those tests, the correct action is to stop experimenting and submit the current nuanced boundary-condition paper rather than continue broad method chasing.

### Phase 4 v2 freeze decision

- The initial phase-4 v2 dev run showed that persona-sharded proposal alone was not enough:
  - raw candidate diversity rose
  - but kept-candidate diversity did not, because the existing validator was over-pruning plausible wrong alternatives
- One and only one phase-4 revision was therefore used:
  - keep v1 entirely frozen
  - keep v2 rebuttal/finalization unchanged
  - make v2 candidate validation more permissive so that non-duplicate, non-malformed, non-trivial alternatives survive into the auditable hypothesis set
- This decision follows the intended phase-4 scientific question:
  - the point is to test whether candidate-collapse repair changes the causal story
  - allowing plausible wrong alternatives to survive is part of that repair, not a new downstream reasoning method
- Freeze conclusion after the dev rerun:
  - `dart_adv_same_v2` now increases kept-candidate count substantially on both `gsm8k` and `multiarith`
  - therefore v2 is eligible for a prospective main retest on new IDs
- Fair-comparison policy for the main retest:
  - `dart_adv_same_v1` remains the frozen v1 baseline
  - `dart_adv_same_v2` is the only changed DART method
  - `freeform_devil_advocate_same` remains the key same-context critique control
  - closed-label tasks remain out of scope unless a regression check becomes absolutely necessary

### Phase 4 final decision

- Phase 4 answered the intended question cleanly enough:
  - yes, candidate collapse was a real bottleneck
  - yes, a prospective v2 repair can materially increase kept-candidate diversity
  - no, that repair does not by itself restore a strong claim that explicit auditable candidate sets matter more than fair freeform same-context critique
- Therefore the correct paper posture after phase 4 is:
  - keep the open-ended selection-vs-regeneration mechanism claim
  - keep the candidate-collapse repair as a useful negative/nuanced result
  - stop this line of method chasing and submit the nuanced boundary-condition paper

### Phase 5 objective and stop rules

- Phase 5 is justified only as a local open-model external-validity and capacity-boundary test.
- The current positive regime remains unchanged:
  - open-ended arithmetic only
  - selection-only vs rebuttal + regeneration is the real mechanistic contrast
  - same-context remains the default DART finalization
- The current unsupported claim also remains unchanged:
  - explicit auditable candidate sets are not yet established as the key ingredient beyond fair freeform critique / extra compute
- Therefore phase 5 should ask only:
  - does the supported mechanism survive outside the OpenAI model family?
  - does explicit candidate structure help weaker local models more than stronger ones?
- If the answer is “no” or “not clearly,” the correct action is to stop and submit the current nuanced paper.

### Phase 5 final decision

- The local open-model phase did not change the paper posture.
- The final local comparison used `Qwen2.5-0.5B` vs `Qwen2.5-1.5B` after larger / DeepSeek-oriented plans proved too infrastructure-heavy or too unstable for structured local execution.
- What phase 5 established:
  - a tiny `svamp` pocket where `dart_adv_same_v1` helped `Qwen2.5-1.5B`
  - but no usable local replication of the stronger API-side `gsm8k` mechanism
- What phase 5 did not establish:
  - no convincing capacity-boundary effect where explicit auditable candidate sets help weaker local models more than stronger ones
  - no fresh support for the auditable-candidate-set necessity claim
- Therefore:
  - keep the OpenAI-based open-ended arithmetic mechanism as the main paper evidence
  - treat the local phase as a negative / non-strengthening external-validity check
  - stop and submit the nuanced boundary-condition paper

### Phase 5 rerun decision

- The earlier `0.5B/1.5B` local retest was probably too weak to be very informative, so a larger-local rerun was justified.
- The rerun policy was:
  - no prompt changes
  - use all four GPUs pragmatically
  - prefer a larger same-family model if it could be brought up without turning the turn into infrastructure work
- What happened in practice:
  - `Qwen/Qwen2.5-14B-Instruct` bring-up remained download-bound during the rerun window
  - `Qwen2.5-Math-7B` and cached `DeepSeek` 7B variants were still too unstable in structured local execution
  - the clean rerun evidence therefore comes from `Qwen/Qwen2.5-7B-Instruct`, executed in parallel across both GPU pairs on `gsm8k` and `svamp`
- What the rerun established:
  - yes, the tiny-model local phase had been overly floor-limited
  - yes, on `svamp` the supported mechanism partially reappears:
    - selection-only stays at the floor when coverage=`0`
    - DART same-context recovers some coverage-miss cases
  - no, the stronger claim still is not supported:
    - `freeform_devil_advocate_same` remains stronger than DART on the rerun slices
    - `gsm8k` did not show a local DART-over-selection gain on this rerun slice
- Therefore the paper posture still should not change:
  - use the rerun as a stronger local external-validity note than the earlier tiny-model check
  - do not claim that larger local models rescue the auditable-candidate-set story
  - keep the submission recommendation as a nuanced boundary-condition paper

### V-CHASE branch decision

- All DART and CHASE artifacts are frozen evidence for this branch.
- V-CHASE exists only to answer one bounded question:
  - whether verifier-like local signals can improve hard-arithmetic control for same-context freeform devil's-advocate deliberation
- What carries over from CHASE:
  - same-context freeform critique remains the central substrate
  - raw verbal confidence is already known to be insufficient
  - challenge-conditioned dynamics remain the right frame
- What changes in V-CHASE:
  - add verifier-like features, especially PRM-style and arithmetic-consistency signals
  - explicitly model both:
    - current sufficiency
    - next-round utility / harm
- Methodological guardrails:
  - do not treat PRM scores as truth labels
  - do not let monitors become sole arbiters
  - do not broaden back into candidate-set method chasing
  - do not broadly retune prompts
- Phase gate for this branch:
  - offline rescoring and oracle headroom on existing CHASE traces first
  - only if those show meaningful headroom should new main generation proceed
- Branch stop rules:
  - stop if verifier features do not materially improve over old CHASE features on hard arithmetic
  - stop if oracle headroom over CHASE is too small
  - stop if local PRM bring-up becomes the main project
  - stop if `VCHASE_dualhead` fails to improve over `CHASE_calibrated` and does not clearly beat `robust_rule_gate`

### Phase 5 high-util long-run decision

- A second rerun was scientifically justified because the user correctly pointed out that a meaningful local read should involve:
  - sustained high GPU occupancy
  - a substantially larger sample than the earlier tiny local slices
- The chosen design was pragmatic rather than heroic:
  - run four independent `Qwen2.5-7B-Instruct fp16` jobs, one per GPU
  - cover three open-ended arithmetic datasets
  - keep methods frozen
  - collect enough local evidence to test whether the mechanism survives under a real local workload
- What this long run established:
  - yes, the supported mechanism survives locally in a weak but real form on `gsm8k` and `multiarith`
    - when coverage=`0`, selection-only stays at `0`
    - DART same-context rises slightly above `0`
  - no, the stronger claim still does not hold
    - `freeform_devil_advocate_same` stays clearly ahead of DART on all three datasets
  - therefore explicit auditable candidate structure still is not the best-supported explanation
- Net effect on the paper:
  - the local section is no longer just a tiny null sanity check
  - it now supports a narrower statement:
    - the selection-only vs rebuttal/regeneration mechanism is not purely API-specific
  - but it still does not support a stronger methods paper centered on auditable options as the uniquely valuable ingredient
- Final recommendation remains unchanged:
  - stop further experimental chasing
  - submit the nuanced boundary-condition paper

### CHASE branch launch

- The old DART branch is frozen as completed evidence.
- A new branch is justified only if it asks a different question than candidate-set-centric DART:
  - challenge-conditioned confidence for adaptive deliberation on open-ended arithmetic
- The CHASE branch therefore makes the following strategic commitments:
  - do not rewrite or overwrite old DART reports
  - do not center explicit auditable candidate sets
  - do center same-context freeform devil's-advocate as the main control baseline
  - do focus on local-open-model execution

### CHASE method decisions

- Confidence is not treated as a scalar truth oracle.
- The main control target is `P(correct_now)` / `P(sufficient_to_stop)` under adversarial challenge.
- Raw verbalized confidence is required as a baseline, but it is not trusted alone.
- The branch will benchmark a modular feature set:
  - bounded answer-conditioned verbalized confidence
  - binary self-eval margin
  - answer logprob confidence
  - small-sample disagreement
  - DiNCo-lite distractor-relative confidence
  - challenge-response deltas
- Same-context remains the default update path.
- Fresh-context is not a branch priority unless tiny dev evidence unexpectedly favors it.

### CHASE infrastructure decisions

- Keep the OpenAI backend intact in the repo, but make local execution the main path for this branch.
- Prefer `hf_local` for confidence work because token-level scoring is useful.
- Use robust tagged outputs instead of deep structured JSON whenever that improves local stability.
- Add a lightweight post-hoc calibrator only:
  - logistic regression and related simple models are allowed
  - no LLM fine-tuning, RL, or synthetic training loop

### CHASE stopping rules

- Stop the branch if local confidence prompts remain unstable after one careful dev pass.
- Stop the branch if the signal benchmark shows no usable improvement over raw verbalized confidence.
- Stop the branch if the calibrated controller does not improve the fixed-budget trade-off versus fixed one-round / two-round freeform critique.
- Stop the branch if it drifts back into method chasing for DART-style candidate prompts.

### CHASE dev and primary-model freeze decision

- `Qwen/Qwen2.5-Math-7B-Instruct` was the initially preferred primary local model.
- After the tiny dev pass, that model was demoted to a secondary-only replication role because:
  - tagged-output stability was materially worse than on `Qwen/Qwen2.5-7B-Instruct`
  - the branch risked becoming mostly an output-control problem instead of a confidence study
- Therefore the primary CHASE model is frozen as:
  - `Qwen/Qwen2.5-7B-Instruct`
- The confidence elicitation format is frozen as:
  - answer-conditioned suffix confidence
  - bounded `0-20` scale
  - same-context challenge/revision
  - no `0-100` confidence in the main runs

### CHASE final decision

- The branch produced a real but narrow result rather than a broad new methods win.
- Supported:
  - raw verbal confidence is not the best signal
  - alternative-aware / challenge-aware composite confidence is materially more informative
  - adaptive deliberation can outperform always-running fixed one-round / two-round freeform critique on easier arithmetic (`asdiv`)
- Not supported:
  - CHASE does not beat direct generation on `asdiv`
  - CHASE does not beat the best fixed freeform baselines on harder arithmetic (`gsm8k_train`)
  - weaker / more brittle local models are not rescued by confidence-control alone
- Therefore the correct recommendation is:
  - keep CHASE as a nuanced adaptive-control branch
  - do not position it as a broad replacement for fixed-K freeform critique
  - if written up, frame it as a partial result on challenge-conditioned confidence, not as a dominant new reasoning method

### V-CHASE final decision

- V-CHASE is the first follow-up branch that materially changes the hard-arithmetic controller story.
- The key design choice that held up:
  - keep same-context freeform critique frozen
  - add verifier-like features on top of CHASE rather than changing the prompt substrate
- What was learned:
  - arithmetic-consistency features already provide real signal gains over old CHASE on both old held-out traces and fresh combined traces
  - standalone PRM scores are weak and should not be treated as verdicts
  - however, PRM features are useful inside a combined controller on hard arithmetic
- Most important supported statement after V-CHASE:
  - verifier-aware challenge-conditioned control can improve hard arithmetic where CHASE alone remained too weak
- Most important unsupported statement after V-CHASE:
  - do not claim that PRM is a standalone verifier
  - do not claim that dual-head control is universally superior across all arithmetic datasets
  - do not claim clean transfer to every open arithmetic benchmark yet
- Interpretation by dataset:
  - `gsm8k_train` hard set:
    - now a real positive result
    - `VCHASE_dualhead` with PRM features cleanly beats `CHASE_calibrated`, `robust_rule_gate`, and `freeform_fixed1_same`
  - `asdiv` easy set:
    - V-CHASE preserves the over-deliberation guard and remains compute-efficient
  - `svamp` transfer:
    - mixed; `singlehead` and `verifier_rule` are mildly positive, but `dualhead` is not the clean winner
- Therefore the correct paper posture after V-CHASE is:
  - present DART as the original mechanism branch
  - present CHASE as the confidence-and-control branch that exposed the hard-arithmetic gap
  - present V-CHASE as a bounded verifier-aware follow-up that closes part of that gap on hard arithmetic
- Practical recommendation:
  - keep V-CHASE as a serious follow-up branch in the repo and paper narrative
  - avoid broadening the claim beyond verifier-aware adaptive deliberation for open-ended arithmetic

### VCHASE-R2 follow-up decision

- This phase is a bounded follow-up inside the V-CHASE line, not a new method branch.
- Frozen assumptions carried into R2:
  - same-context freeform devil's-advocate stays fixed
  - PRM must be treated as a feature, not a judge
  - closed-label tasks stay frozen
  - no prompt chasing
- The scientific goal is limited to:
  - replication
  - mechanism disentanglement
  - transfer diagnosis
- Two operating points will be frozen from calibration traces only:
  - `hard_opt`
  - `balanced_opt`
- Stop R2 quickly if any of the following happens:
  - PRM-only explains away the gain
  - single-head matches dual-head after threshold sweeps
  - fresh hard-set replication fails
  - easy-set low-round behavior disappears
  - transfer remains opaque even after a bounded diagnostic

### VCHASE-R2 final decision

- Fresh hard-set replication was not a failure, but it did not support the stronger mechanism claim.
- What held up:
  - hard arithmetic still benefits from the verifier-aware control family relative to CHASE and fixed freeform baselines
  - easy-set low-round behavior was preserved
- What weakened:
  - `PRM_only` was still weaker than the full controller family, so PRM-as-judge is not the story
  - however, `VCHASE_dualhead_PRM_hardopt` and `VCHASE_dualhead_noPRM` matched on fresh `gsm8k_train`
  - and `VCHASE_singlehead_PRM` slightly exceeded the dual-head variant on fresh `gsm8k_train`
- Therefore the right conclusion is:
  - keep the branch as a narrow positive controller family result
  - do not center PRM as the essential feature
  - do not center dual-head utility modeling as the essential mechanism
  - position the paper story around bounded verifier-aware adaptive control, with honest mechanism caveats

### EIR branch objective

- EIR is a new methods branch, not an extension of DART, CHASE, or V-CHASE controller tuning.
- The branch exists because the frozen evidence now points to a different bottleneck:
  - the unresolved issue is likely which corrective intervention the model can execute successfully on a specific draft/problem pair
  - not whether the model should merely deliberate more or trust another confidence / PRM signal
- Therefore the branch contribution target is:
  - executable intervention routing over a small heterogeneous action palette
  - with explicit comparison against relevance-only routing
  - and with action-bank counterfactual evidence

### EIR design commitments

- Same-context remains the default correction substrate.
- Candidate-set design stays frozen and is not reopened.
- PRM-like and confidence-like features may be reused only as generic state signals, not as the branch headline.
- The initial action palette is frozen at:
  - `STOP`
  - `FREEFORM_CRITIQUE`
  - `EQUATION_REDERIVE`
  - `PYTHON_RECOMPUTE`
  - `LOCALIZE_BACKTRACK`
- Only one palette replacement is allowed later:
  - `CONSTRAINT_CHECKLIST`

### EIR split policy decision

- Fresh transfer evaluation cannot honestly use `svamp` or `multiarith`:
  - prior branches have already consumed the full available pools
- Therefore a fresh arithmetic transfer dataset must be introduced for EIR if the branch is to keep a hard/easy/transfer design.
- This is a data-availability adjustment, not a method pivot.

### EIR pivot-ladder decision

- This branch must not collapse into an early negative write-up after the first underperforming router.
- The bounded ladder is approved in advance:
  - one action-palette replacement if one action is clearly dominated or unstable
  - one router-objective pivot if direct utility regression is weak
  - one bounded API preview diagnostic only if transfer weakness appears to come from preview quality
- Hard limits remain:
  - no broad prompt-chasing
  - no reopening closed-label tasks
  - no return to candidate-set methods

### EIR dev freeze decision

- The initial EIR action palette is retained without pruning after the tiny dev pass.
- Reason:
  - the palette already shows meaningful heterogeneity in realized action utility
  - on hard `gsm8k_train`, `PYTHON_RECOMPUTE` is materially stronger than `FREEFORM_CRITIQUE`
  - on easy `asdiv`, `STOP` and `PYTHON_RECOMPUTE` preserve accuracy better than freeform critique
- Therefore:
  - there is no justification yet for invoking Pivot A
  - prompts are frozen after one minimal parse-hygiene fix:
    - strip stray tags from scratch fallbacks

### EIR transfer-role fallback decision

- Fresh `svamp` and `multiarith` reuse would violate the branch's non-overlap policy.
- `mawps` is the preferred fresh transfer replacement, but its repeated action-bank bring-up is currently less stable than the already-used hard/easy sets.
- To keep the branch moving without distorting the method question:
  - keep `mawps` as the preferred transfer target if the loader stabilizes
  - reserve the remaining unseen `gsm8k` test split as the fallback secondary held-out role
- This is a dataset-plumbing fallback, not a method pivot.

### EIR calibration scheduling decision

- A single `asdiv` calibration shard that remained at `0` written examples after sustained runtime was treated as a collection issue, not as evidence about the method.
- The fix was:
  - keep the healthy `asdiv` shard running
  - replace only the stalled shard with a fresh-offset shard
- This preserves the branch's frozen prompt set and action palette while avoiding an artificial throughput bottleneck.

### EIR offline evaluation validity decision

- Offline router evidence must come from held-out calibration examples, not fit-and-evaluate-on-the-same-bank summaries.
- Therefore the offline router path is frozen to:
  - fit on a training subset of the calibration action bank
  - evaluate on a held-out validation subset
  - compare `BEST_FIXED_ACTION`, `RELEVANCE_ONLY_ROUTER`, `EXECUTABILITY_ONLY_ROUTER`, and `FULL_EIR` under the same held-out split
  - include the predeclared feature-drop ablations before invoking any pivot

### EIR partial-snapshot interpretation decision

- The rolling calibration snapshot currently suggests:
  - `PYTHON_RECOMPUTE` is the strongest single fixed action
  - `RELEVANCE_ONLY_ROUTER` is not competitive
  - learned routers are not yet clearly above `BEST_FIXED_ACTION`
- This is NOT enough to end the branch or invoke a method rewrite.
- Approved next-step order remains:
  - finish the calibration bank
  - run full held-out offline router ablations
  - if `BEST_FIXED_ACTION` still dominates, then and only then consider the single allowed router-objective pivot

### EIR hard-only checkpoint decision

- After the hard `gsm8k_train` calibration bank reached `100` examples, a hard-only offline checkpoint was treated as admissible branch-steering evidence.
- Current hard-only facts:
  - `PYTHON_RECOMPUTE` is the strongest fixed action by a wide margin
  - `RELEVANCE_ONLY_ROUTER` is clearly weaker than that best fixed action
  - the first utility-regression `FULL_EIR` router does not yet beat `BEST_FIXED_ACTION`
  - the bounded classification-style router-objective pivot also does not yet beat `BEST_FIXED_ACTION`
- Therefore:
  - the branch has now effectively exhausted the one allowed router-objective pivot in preliminary form
  - but it has NOT yet exhausted the full bounded ladder, because the palette-replacement decision still depends on the completed easy/transfer calibration evidence
  - no prompt rewrite or uncontrolled expansion is justified

### EIR Pivot A decision

- The current bounded evidence is sufficient to test the single allowed palette replacement.
- Reason:
  - `EQUATION_REDERIVE` shows near-zero oracle mass in the available hard and mixed checkpoints
  - the other actions still retain distinct oracle roles
- Approved Pivot A:
  - replace `EQUATION_REDERIVE` with `CONSTRAINT_CHECKLIST`
  - use a post-hoc replacement path from the same frozen drafts instead of re-running the entire bank
  - evaluate the replacement on the hard calibration bank before deciding whether it becomes the main-palette action

### EIR main pause decision

- Held-out main collection should not proceed at scale until the palette decision is resolved.
- Therefore the first hard-main shard was intentionally stopped early and treated as disposable warm-up output.
- Main collection will restart only after the hard-set checklist replacement result is known.

### EIR Pivot A resolution

- The single allowed palette replacement was tested and rejected.
- Evidence:
  - `CONSTRAINT_CHECKLIST` scored `0.00` accuracy on the hard replacement bank
  - harmful rate was `0.27`
  - held-out hard offline replay with the checklist palette degraded both the full router and the relevance-only baseline
- Final decision for the branch:
  - keep the original action palette:
    - `STOP`
    - `FREEFORM_CRITIQUE`
    - `EQUATION_REDERIVE`
    - `PYTHON_RECOMPUTE`
    - `LOCALIZE_BACKTRACK`
  - do not use `CONSTRAINT_CHECKLIST` in the main EIR evaluation

### EIR offline-to-main decision

- After the mixed offline router study:
  - `RELEVANCE_ONLY_ROUTER` was clearly too weak to carry the branch
  - `FULL_EIR` did not beat `BEST_FIXED_ACTION` offline
  - but the branch had not yet exhausted the required held-out fresh evaluation
- Therefore the branch continued to the full fresh main phase without adding new actions or new prompt variants.

### EIR final branch decision

- Fresh held-out evidence supports a narrower methods story than the initial north star.
- Supported:
  - corrective-action choice matters
  - executability-aware routing beats relevance-only routing on hard and easy arithmetic
  - full EIR is strongest on the easy set
- Not supported:
  - full EIR beats the strongest hard-set fixed executable action
  - full EIR restores a low-cost stop-heavy easy-set policy
  - transfer is robust on the fresh `mawps` split
- Optional follow-ups were not taken:
  - no secondary-model replication, because the primary-model hard-set result did not clear the strongest bar
  - no API micro-diagnostic, because the transfer split showed near-floor oracle headroom and would not clarify the main hard-set question enough

### HEIR branch decision

- HEIR is approved as a new methods branch rather than an EIR extension.
- Reason:
  - EIR already showed that executability matters beyond semantic relevance
  - but the strongest remaining bottleneck appears to be policy geometry, not missing actions or missing confidence features
- Branch commitments:
  - start from a pruned action palette:
    - `STOP`
    - `PYTHON_RECOMPUTE`
    - `LOCALIZE_BACKTRACK`
    - `FREEFORM_CRITIQUE`
  - exclude `EQUATION_REDERIVE` from the default HEIR phase-1 palette
  - center hierarchical gates over:
    - keep/intervene
    - tool/language
    - localize/freeform
  - reuse EIR flat-router evaluation on the same fresh HEIR banks as the primary flat baseline

### HEIR branch outcome

- The branch exhausted the bounded ladder without reopening actions or prompts:
  - baseline hierarchical gate-classification policy
  - no-keep-prior ablation
  - localize-fallback ablation
  - language-branch collapse
  - objective pivot to gate-wise utility-delta / pairwise routing
- Final strongest HEIR variants:
  - hard: `HEIR_pairwise_hardopt`
  - easy: `HEIR_KEEPPRIOR_hardopt`
  - transfer: `HEIR_pairwise_hardopt`
- Supported:
  - EIR's flat router was not the only reasonable policy class; hierarchy plus utility-aware gate scoring recovers a large fraction of the initial hard-set failure
  - hierarchy remains especially valuable for preserving low-intervention behavior on easy arithmetic
  - executability-aware routing still clearly beats relevance-only behavior
- Not supported:
  - HEIR beats the strongest fixed hard-set executable action
  - HEIR beats the best flat EIR policy on the hard set
  - language-branch preview quality is the main remaining bottleneck
- Final branch posture:
  - the strongest surviving methods story is now:
    - action geometry matters
    - flat routing underfits that geometry
    - hierarchical routing plus utility-aware gate decisions substantially improves over naive hierarchy and relevance-only routing
    - but fixed tool recomputation remains the strongest hard-set baseline under the current local model family

### GEM-HEIR branch decision

- GEM-HEIR is approved as a new methods branch rather than another HEIR ablation bundle.
- Reason:
  - HEIR already validated the hierarchy
  - but the current gate models still use the wrong target
  - the next scientifically justified target is gate-specific pairwise utility margin estimation
- Branch commitments:
  - keep the HEIR-pruned action palette unchanged
  - center Gate 1 / Gate 2 / Gate 3 margins instead of direct action identity
  - include a regime-aware extension
  - treat PRM/verifier/confidence signals only as auxiliary features
  - exhaust the bounded pivot ladder before any negative conclusion

### GEM-HEIR branch outcome

- The branch exhausted the intended bounded ladder:
  - direct margin regression
  - pairwise classification pivot
  - pairwise ranking pivot
  - regime-stratified subset-aware margin routing
  - no further preview/API pivot was taken because the main remaining gap was to fixed python, not to language-preview quality
- Supported:
  - gate-specific utility margins are a more defensible control target than direct action-class prediction
  - GEM improves over the frozen flat EIR and HEIR references on the fresh hard set:
    - `FULL_EIR_ROUTER_hardopt_ref = 0.6650`
    - `HEIR_pairwise_hardopt_ref = 0.6600`
    - best GEM = `0.6850`
  - GEM remains clearly stronger than fixed freeform critique on the hard set
  - mixed hard/easy workloads still favor adaptive routing over previous routed baselines
- Not supported:
  - GEM beats fixed `PYTHON_RECOMPUTE` / `BEST_FIXED_ACTION` on fresh `gsm8k_train`
  - the offline calibration win over fixed python robustly replicates on the held-out main set
  - regime stratification is proven necessary
- Final branch posture:
  - the strongest surviving story is a narrow methods claim about pairwise margin routing improving over prior routing families
  - the top-tier north-star claim, beating the strongest fixed executable hard-set action, remains unsupported

### TIER branch decision

- TIER is approved as a new methods branch rather than another GEM-HEIR ablation bundle.
- Reason:
  - GEM-HEIR already tested better routing targets
  - fixed `PYTHON_RECOMPUTE` still dominates the hard set
  - the next justified abstraction is executable interface quality, not another router variant
- Branch commitments:
  - keep the executable recomputation substrate central
  - compare raw python against structured semantic interfaces
  - keep routing secondary to fixed-interface evidence
  - use verifier / PRM / confidence signals only as auxiliary features
  - exhaust the bounded interface pivot ladder before any negative conclusion

### TIER branch outcome

- TIER completed with frozen dev prompts, full calibration, offline analysis, and a bounded fresh held-out local main:
  - `gsm8k_train = 103`
  - `asdiv = 109`
- Supported:
  - the remaining bottleneck after GEM-HEIR is better described as semantic-to-executable interface quality than as another action-routing failure
  - on hard held-out arithmetic, the strongest structured fixed interface was `OPERATOR_SCHEMA_TO_CODE = 0.7184`, directionally above `RAW_PYTHON = 0.6893`
  - fixed structured interfaces remain much stronger than critique-based baselines on the hard set
- Not supported:
  - `FULL_TIER_ROUTER_hardopt` beats `RAW_PYTHON` on hard held-out data
  - extra interface-routing complexity is the main source of gain
  - the branch yet supports a broad “full selector beats fixed executable recompute” claim
- Final TIER posture:
  - strongest surviving story = interface quality matters more than prior routing abstractions
  - strongest concrete method signal = operator-schema-to-code is the best structured interface candidate
  - if another phase were justified, it should focus on operator/discretization interface quality rather than additional router complexity

### OSCAR branch decision

- OSCAR is approved as a new methods branch after TIER.
- Reason:
  - TIER already showed that routing is no longer the main abstraction
  - the strongest frontier signal is fixed `OPERATOR_SCHEMA_TO_CODE`
  - the next justified target is semantic-to-executable compilation quality
- Branch commitments:
  - keep the focus on fixed executable compilation rather than another selector-heavy story
  - compare `RAW_PYTHON`, `OPERATOR_SCHEMA_TO_CODE`, `OSCAR_TEMPLATE_COMPILE`, and `OSCAR_CONSTRAINED_COMPILE`
  - use a typed operator/discretization schema as the central IR
  - separate schema quality from deterministic compilation and from freer constrained code generation
  - use PRM/verifier/confidence signals only as auxiliary features if needed
- Reserved bounded pivot:
  - replace one weak structured compiler with `NORMALIZED_QUESTION_TO_CODE` only if the predeclared ladder justifies it

### OSCAR branch outcome

- Initial OSCAR calibration did NOT support centering the branch on the new compilers:
  - `OSCAR_TEMPLATE_COMPILE` and `OSCAR_CONSTRAINED_COMPILE` were both well below `RAW_PYTHON` and `OPERATOR_SCHEMA_TO_CODE`
- Pivot A was therefore taken exactly as predeclared:
  - replace the weakest structured compiler slot with `NORMALIZED_QUESTION_TO_CODE`
- Pivot A succeeded offline:
  - `gsm8k_train`
    - `RAW_PYTHON = 0.7000`
    - `OPERATOR_SCHEMA_TO_CODE = 0.7067`
    - `NORMALIZED_QUESTION_TO_CODE = 0.7533`
  - `asdiv`
    - `RAW_PYTHON = 0.7444`
    - `OPERATOR_SCHEMA_TO_CODE = 0.7667`
    - `NORMALIZED_QUESTION_TO_CODE = 0.7778`
- Pivot B was also justified and taken:
  - compare `problem_only` vs `problem + draft` on the pivot palette
  - decision:
    - keep `problem + draft`
    - do not switch to problem-only compilation
- Fixed-compiler-first framing was retained for main:
  - no full selector was elevated to the headline
  - no keep gate was added because the hard-set claim surface was primary and offline did not justify a dedicated gate
- Final OSCAR held-out decision:
  - Supported:
    - semantic-to-executable compilation quality remains the right post-TIER abstraction
    - on the cluster-focused hard surface, fixed `OPERATOR_SCHEMA_TO_CODE` beat `RAW_PYTHON` directionally (`0.7150 > 0.6950`)
    - on easy arithmetic, fixed structured interfaces remained extremely strong (`0.9900`)
    - `problem + draft` is better than `problem only` for the serious structured interfaces
  - Not supported:
    - the new OSCAR compilers (`NORMALIZED_QUESTION_TO_CODE`, `OSCAR_TEMPLATE_COMPILE`) beat `RAW_PYTHON` on the generic hard hold-out
    - offline pivot-A wins robustly replicated on held-out hard data
    - deterministic compilation is the dominant remaining mechanism under the current local model family
- Final posture:
  - strongest surviving methods story = structured operator/discretization interface quality matters, but the main reliable hard-set frontier under the current local model family is still the simpler fixed structured interface line, not the more ambitious OSCAR compilers
  - if another phase is justified, it should focus on schema extraction quality and operator/discretization supervision, not more routing or more debate

### ATLAS branch decision

- OSCAR is treated as frozen evidence.
- The next branch should not add more routing complexity or more compiler complexity.
- The remaining plausible bottleneck is schema extraction quality for the already-promising operator/discretization interface.

### ATLAS method decision

- Keep the executable backend fixed:
  - `RAW_PYTHON`
  - `OPERATOR_SCHEMA_TO_CODE_BASE`
- Improve only the schema extraction layer via:
  - retrieval-conditioned schema extraction
  - field-wise critical-field extraction
  - optional critical-field repair as a bounded pivot
- Teacher schemas are supervision / diagnostic artifacts only.
- The branch should isolate:
  1. schema extraction quality
  2. execution / backend coverage
  3. the intrinsic advantage of the simpler operator-schema interface

### ATLAS execution policy

- Optional API teacher phase is skipped by default because no API key is present.
- Local teacher-like seed construction with `Qwen/Qwen2.5-7B-Instruct` is the fallback.
- Main held-out claim surface is cluster-focused hard arithmetic, not easy arithmetic.
- Easy-set evaluation remains secondary and only matters if a trivial keep gate becomes justified.

### ATLAS branch outcome

- Teacher/audit decision:
  - keep the teacher phase local-only
  - treat the `37`-example audited seed as retrieval memory plus field-gap supervision
  - do not present it as a stronger-model teacher upper bound
- Retrieval decision:
  - keep global retrieval
  - reject cluster-first retrieval because hard calibration fell from `0.74375` to `0.7125`
- Conditioning decision:
  - keep `problem + draft`
  - reject `problem only` because all serious schema extractors improved with draft conditioning
- Field decomposition decision:
  - keep field-wise extraction as a main ATLAS method
  - it produced the cleanest pairwise win over `RAW_PYTHON` on the cluster-focused held-out hard surface
- Repair decision:
  - include `ATLAS_CRITICAL_FIELD_REPAIR` in main as a bounded pivot artifact
  - do not center the branch on it because it tied retrieval/fieldwise offline and did not beat the base operator schema
- Keep-gate / easy-surface decision:
  - do not add a keep gate to the headline
  - easy arithmetic remains secondary and unnecessary for the main hard-cluster claim
- Final ATLAS posture:
  - the strongest surviving claim is:
    - teacher-audited, cluster-aware schema extraction improves the operator-schema interface enough to beat `RAW_PYTHON` on the targeted hard semantic clusters
  - the branch does not support:
    - universal generic-hard domination
    - cluster-first retrieval
    - repair as a standalone superior method

### ATLAS API follow-up decision

- The bounded API teacher phase was run once `OPENAI_API_KEY` became available.
- Decision:
  - keep the API role narrow:
    - teacher-schema extraction only
    - no API final-answer generation
    - no API-centered headline
- What changed:
  - the teacher seed is now available in both local-audited and API-audited forms
  - the stronger teacher confirmed that the ATLAS-local methods really are improving the critical semantic fields over the baseline operator schema extractor
- What did not change:
  - the strongest branch claim still comes from the frozen cluster-focused local main
  - the bounded local rerun with the API seed was too noisy to treat as a new headline result because non-retrieval methods also moved materially
- Final posture after the API phase:
  - keep the ATLAS headline as a local schema-quality result on the targeted hard clusters
  - cite the API phase as reinforcing evidence that schema extraction quality, especially critical semantic fields, remains the real bottleneck

### ATLAS-RG branch decision

- ATLAS is treated as frozen evidence.
- The next branch should not add more routing or broader compilation.
- The main unresolved ATLAS teacher-gap field was `quantity_role_match`.
- Decision:
  - center the branch on quantity-role grounding and target binding
  - keep the executable backend fixed
  - compare:
    - full role-grounded extraction
    - role-only repair
    - non-role-only repair
  - use replay-controlled draft matching so seed / repair gains are not confounded with rerun variance

### ATLAS-RG execution policy

- Run the API teacher role micro-phase because API access is available.
- Keep the API role narrow:
  - role-grounded schema extraction only
  - no API final-answer generation
  - budget under `$5`
- Keep local-first evaluation:
  - `Qwen/Qwen2.5-7B-Instruct`
  - 4-GPU sharded collection
  - `4bit` quantization by default for stable one-worker-per-GPU execution
- Easy arithmetic remains secondary.
- The main claim surface is:
  - cluster-focused hard arithmetic
  - plus replay-controlled generic hard as a secondary check

### ATLAS-RG infrastructure decision update

- Rejected the initial `4bit` collection path for ATLAS-RG main collection.
- Reason:
  - observed GPU utilization was materially too low for the user's explicit runtime constraint
- Adopted instead:
  - `fp16`
  - one worker per GPU
  - 4-way pre-sharded manifests
  - `nvidia-smi dmon` monitoring during long phases
- Evidence:
  - hard calibration sustained roughly `sm ~94–96%` and completed `160` examples in about `25–27 minutes`
- Consequence:
  - the rest of the branch should stay on the same `fp16` 4-worker path unless a later phase shows a new utilization bottleneck

### ATLAS-RG final decision

- Completed the bounded pivot ladder:
  - Pivot A `retrieval strategy`: exercised once and found to be effectively neutral
  - Pivot B `field-wise emphasis`: retained because it stayed competitive, but it did not become the best hard-set interface
  - Pivot C `critical-role repair`: exercised once and improved over `RAW_PYTHON` on cluster hard, but not over `OPERATOR_SCHEMA_TO_CODE_BASE`
  - Pivot D `API role phase`: exercised once; replay control showed a real seed-quality gain for the roletable path, but not a new best frontier
- Supported branch claims:
  - quantity-role grounding is a real causal bottleneck inside the operator-schema interface
  - ATLAS-RG variants beat `RAW_PYTHON` on the cluster-focused hard surface
  - replay-controlled teacher seed quality specifically improves `ATLAS_RG_ROLETABLE_TO_CODE`
- Unsupported stronger claims:
  - ATLAS-RG becomes the best fixed hard-set interface
  - the remaining gap is purely role extraction rather than a combination of role extraction and residual interface / compiler coverage
- Project posture after ATLAS-RG:
  - keep `OPERATOR_SCHEMA_TO_CODE_BASE` as the robust hard-set frontier baseline
  - cite ATLAS-RG as mechanistic evidence about field-causal bottlenecks, not as a universal replacement
  - do not center the next phase on mixed-workload or another routing layer unless a new branch can directly beat the simpler fixed operator-schema baseline

### ATLAS-MS branch decision

- ATLAS and ATLAS-RG are treated as frozen evidence.
- The next branch should not add more routing or broader compilation.
- Decision:
  - center the branch on interacting schema-field bundles
  - keep the executable backend fixed
  - compare:
    - `G1` operator/discretization only
    - `G2` target/postprocess only
    - `G3` role-only
    - pair bundles `G1+G2`, `G2+G3`, `G1+G3`
    - full bundle `G1+G2+G3`
  - keep the branch replay-controlled by freezing drafts before bundle comparison
- API policy:
  - run the bounded API teacher field phase because API access is available
  - keep it narrow:
    - full bundle extraction only
    - no API final-answer generation
    - no API-centered headline
- Runtime / infrastructure decision:
  - inherit the ATLAS-RG `fp16`, 4-worker, one-GPU-per-worker path because it achieved the best utilization and wall-clock tradeoff

### ATLAS-MS final decision

- Completed the bounded pivot ladder:
  - Pivot A `retrieval strategy`: exercised once by switching to global retrieval; improved calibration-vs-`RAW_PYTHON` robustness but did not beat the held-out operator-schema frontier
  - Pivot B `field-wise bundle composition`: exercised once; produced lower-latency composed bundles and preserved some cluster gains over `RAW_PYTHON`, but still did not beat `OPERATOR_SCHEMA_TO_CODE_BASE`
  - Pivot C `MS_MINIMAL_CLUSTER_BUNDLE`: exercised once from calibration-only selection; did not become the best held-out cluster-hard method
  - API teacher field phase: exercised once; useful for bundle audit, but replay-controlled comparison showed no teacher-seed superiority for the bundle path
- Supported branch claims:
  - multiple field-bundle methods beat `RAW_PYTHON` on the cluster-focused hard surface
  - role-only is weaker than the best interacting bundle on cluster hard
  - the recurring useful ingredient is target/postprocess handling rather than quantity-role repair alone
- Unsupported stronger claims:
  - any field-bundle method replacing `OPERATOR_SCHEMA_TO_CODE_BASE` as the robust held-out frontier
  - the claim that stronger teacher extraction alone closes the remaining gap
- Project posture after ATLAS-MS:
  - keep `OPERATOR_SCHEMA_TO_CODE_BASE` as the strongest hard-set frontier baseline
  - cite ATLAS-MS as mechanistic evidence that interacting field bundles matter more than role-only repair
  - if another phase is justified, it should target the remaining target/postprocess consistency gap directly under the same fixed executable interface

### CASS branch decision

- `ATLAS`, `ATLAS-RG`, and `ATLAS-MS` are frozen evidence.
- The next branch must not broaden schema extraction again.
- Decision:
  - freeze `OPERATOR_SCHEMA_TO_CODE_BASE` as the strong baseline interface
  - build CASS as a **baseline-preserving sparse patch** branch
  - compare:
    - `target/postprocess` patch only
    - `role` patch only
    - `target/postprocess + role` patch
    - `critical-role` patch
    - broader `nonrole` patch as a control
  - keep execution backend and code substrate unchanged
  - require replay-controlled comparison on identical drafts and identical frozen baseline schemas
- API policy:
  - run the bounded teacher patch audit if the OpenAI key is available
  - keep it narrow:
    - field patch suggestions only
    - no API final-answer generation
    - no API-centered headline
- Infrastructure policy:
  - inherit the `fp16`, one-worker-per-GPU, 4-shard path from `ATLAS-RG` / `ATLAS-MS`
  - if sustained utilization drops below the user's requested level, fix the runner before long collection continues

### CASS final decision

- Completed the branch with a positive held-out result, so no negative-conclusion pivot exhaustion was needed.
- Calibration/offline takeaways:
  - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH` was the best hard patch method
  - `CASS_TARGET_POSTPROCESS_PATCH` was the best balanced / generic-hard patch method
  - the conservative gate tied the best cluster-hard accuracy, but it is not required for the main claim
- Supported branch claims:
  - sparse patching beats `RAW_PYTHON` on fresh cluster-hard held-out data
  - sparse patching beats `OPERATOR_SCHEMA_TO_CODE_BASE` on fresh cluster-hard held-out data
  - sparse patching also beats both `RAW_PYTHON` and `OPERATOR_SCHEMA_TO_CODE_BASE` on the generic-hard held-out surface
  - `target/postprocess + role` is stronger than role-only on cluster-hard
  - `target/postprocess` is the recurring useful ingredient and remains sufficient for the best generic-hard result
  - replay-controlled comparison shows a modest but real teacher-seed benefit for the combined patch path
- Unsupported stronger claims:
  - that role-only repair is enough
  - that a broad full-schema replacement is needed once the strong baseline is available
  - that the API teacher path itself is the headline; it remains diagnostic / supportive, not the main method
- Project posture after CASS:
  - promote `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH` as the main cluster-hard method
  - promote `CASS_TARGET_POSTPROCESS_PATCH` as the simpler generic-hard method
  - treat `CASS_CONSERVATIVE_GATE` as an optional deployment variant for mixed workloads, not the central story
  - update the project frontier:
    - the strongest post-ATLAS result is now conservative sparse surgery on top of the frozen operator-schema baseline
    - the remaining gap, if another phase is justified, should be approached as narrower suspicion gating around target/postprocess-dominant clusters rather than another broad schema family

### CASS-R2 phase decision

- `CASS` is frozen as the current strongest methods result.
- The next phase should not broaden the method family.
- Decision:
  - run a confirmation / direct-comparison phase only
  - keep the sparse patch families and thresholds frozen
  - scale the cluster-hard sample enough to try to lock pairwise intervals
  - compare directly against:
    - a local faithful `PRISM_LITE`
    - a local faithful `F1_LITE`
- Comparator policy:
  - use official code only if adaptation is lightweight and surface-compatible
  - otherwise implement method-faithful local approximations and label them explicitly as such
- Evaluation policy:
  - primary surface remains cluster-hard
  - generic-hard is secondary but mandatory
  - transfer is conditional on a bounded headroom screen
## 2026-03-15 — CASS-R2 transfer-screen decision

Context:

- `CASS-R2` allows an optional cross-dataset transfer suite only if a bounded headroom screen shows aligned cluster-hard room above `KEEP` and above the strongest raw executable baseline.

Decision:

- Exclude both `mawps` and `asdiv` from the `CASS-R2` transfer suite.

Why:

- `mawps` screen:
  - almost no usable headroom (`KEEP = RAW_PYTHON = 0.0167`)
  - best schema path only reached `0.0500`
  - this is too weak to support a meaningful pooled hard confirmation surface
- `asdiv` screen:
  - `KEEP` headroom exists (`0.5278`)
  - but schema methods only tied the raw executable frontier (`0.8333`) rather than exceeding it
  - that fails the pre-registered transfer inclusion rule

Effect:

- The confirmation phase remains centered on the intended publication surface:
  - fresh GSM8K cluster-hard (`n=500`)
  - fresh GSM8K generic-hard (`n=300`)
- This keeps the phase bounded and avoids diluting the CASS story with weakly aligned transfer data.

## 2026-03-15 — CASS-R2 final confirmation decision

Context:

- `CASS-R2` was registered to answer one narrow question:
  - whether frozen `CASS` could be statistically locked on the primary cluster-hard surface
  - and whether it compared favorably to the nearest recent inference-time alternatives under the same local evaluation surface
- The preregistered primary criterion required:
  - `95% bootstrap lower bound > 0` versus `RAW_PYTHON`
  - and `95% bootstrap lower bound > 0` versus `OPERATOR_SCHEMA_TO_CODE_BASE`

Decision:

- Do not claim that `CASS` is statistically locked under the preregistered primary success criterion.
- Do claim that:
  - `CASS` remains the strongest internally motivated sparse-patching family
  - it is robustly favorable to `RAW_PYTHON` on the primary cluster-hard surface
  - it compares favorably to the direct local comparators `PRISM_LITE` and `F1_LITE`
  - but the main cluster-hard comparison against `OPERATOR_SCHEMA_TO_CODE_BASE` remains positive-directional rather than locked

Why:

- Final cluster-hard (`n=800`) head-to-head:
  - `CASS_CONSERVATIVE_GATE = 0.74875`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.73000`
  - `RAW_PYTHON = 0.69750`
  - `PRISM_LITE = 0.69750`
  - `F1_LITE = 0.61750`
- Registered pairwise result:
  - `CASS_CONSERVATIVE_GATE - RAW_PYTHON = +0.0509`, `95% CI [0.0225, 0.0800]`
  - `CASS_CONSERVATIVE_GATE - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0186`, `95% CI [-0.0075, 0.0463]`
- The interval against the frozen operator-schema baseline still touches zero after scaling to `n=800`.
- By contrast, direct-comparator results remain clearly favorable:
  - versus `PRISM_LITE`: positive direction with interval fully above zero when read as `CASS - PRISM`
  - versus `F1_LITE`: clearly favorable

Effect:

- The project can now state a stronger bounded conclusion:
  - conservative target/postprocess-centered schema surgery is externally credible and directly competitive
  - but the strongest top-tier main-track claim is still not fully locked because the primary cluster-hard comparison against the frozen operator-schema baseline remains marginal
- Another phase, if justified, should be framed as a narrow confirmation / variance-reduction continuation, not as a new methods branch.

## 2026-03-15 — CASS-R3 launch decision

Context:

- `CASS-R2` left one registered question unresolved:
  - `CASS` was locked versus `RAW_PYTHON`
  - `CASS` was directly favorable to nearby comparators
  - but `CASS` was still not locked versus `OPERATOR_SCHEMA_TO_CODE_BASE` on the primary cluster-hard surface

Decision:

- Launch `CASS-R3` as a bounded continuation of the confirmation phase.

What stays frozen:

- the full `CASS` patch family
- the operator-schema baseline
- answer normalization
- comparator family:
  - `PRISM_ADAPTED`
  - `F1_ADAPTED`

Why:

- the remaining open question is still statistical confirmation, not method invention
- fresh `gsm8k_train` still has:
  - `715` cluster-hard examples
  - `183` generic-hard examples
- this is enough to materially shrink the interval further even though it may still fall short of the extrapolated `n ~= 1755` target for locking against `OPERATOR_SCHEMA_TO_CODE_BASE`

Effect:

- `CASS-R3` will:
  - exhaust the remaining fresh GSM8K primary surface
  - rerun the same frozen comparators on the same surfaces
  - screen transfer only for bounded external-validity support
- `CASS-R3` will not create new patch families or a new broad methods claim.

## 2026-03-15 — CASS-R3 final locking decision

Context:

- `CASS-R3` was launched only to answer the remaining confirmation question:
  - can frozen `CASS` be statistically locked against `OPERATOR_SCHEMA_TO_CODE_BASE` on the preregistered primary cluster-hard surface while remaining favorable to direct inference-time comparators?
- Transfer expansion was screened and rejected:
  - `mawps` lacked aligned headroom
  - `asdiv` did not satisfy the registered inclusion rule
  - `svamp` and `multiarith` had no fresh admissible examples
- Therefore the decisive read must come from fresh-GSM exhaustion on the existing cluster-hard definition.

Decision:

- Promote `CASS-R3` as the final confirmation phase for the current paper package.

Why:

- On the combined cluster-hard surface `n = 1515`:
  - `CASS_CONSERVATIVE_GATE = 0.746535`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.726073`
  - `RAW_PYTHON = 0.704950`
  - `PRISM_LITE = 0.704950`
  - `F1_LITE = 0.603300`
- The preregistered primary pairwise reads are now positive with lower bounds above zero:
  - `CASS_CONSERVATIVE_GATE - RAW_PYTHON = +0.0416`, `95% CI [0.0205, 0.0634]`
  - `CASS_CONSERVATIVE_GATE - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0207`, `95% CI [0.0007, 0.0422]`
- The lock condition first turned on at `n = 1000` in the sequential stopping trace and remained on through `n = 1515`.
- Generic-hard also remained positive:
  - `CASS_CONSERVATIVE_GATE = 0.797101`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.751553`
  - `RAW_PYTHON = 0.734990`
- Comparator credibility improved rather than weakened:
  - `CASS_CONSERVATIVE_GATE - F1_LITE = +0.1434`, `95% CI [0.1135, 0.1716]`
  - `PRISM_LITE` collapsed to `RAW_PYTHON` routing in this local adaptation, so it should be reported as a bounded method-faithful approximation rather than as an independent reproduced frontier

Effect:

- The frozen CASS abstraction is now the strongest supported methods result in the repo.
- The submission recommendation changes from:
  - “externally credible but not yet locked”
  to:
  - “statistically locked on the preregistered primary cluster-hard surface and directly favorable to the closest feasible inference-time comparators”
- Top-tier main-track submission is now justified.

## 2026-03-17 — LAST-PACK format collection pivots

Context:

- The `LAST-PACK` format module initially targeted unscreened `IFEval` and full `IFBench` under the same local `hf_local` path used elsewhere in the repo.
- The first unscreened `IFEval` attempt showed two concrete issues:
  - a small set of ultra-long-output prompts dominated local generation time
  - `device_map=auto` reduced effective GPU utilization on the long-format collection path
- An environment-side constraint also appeared:
  - after interrupting one failed run, `GPU0` retained an orphaned allocation that could not be cleared with the available permissions

Decision:

- Keep the benchmark family and the localized-repair method set frozen, but apply bounded infrastructure and manifest pivots:
  - screen `IFEval` to `min_words <= 150`
  - score only `strict` validator success
  - force full-on-visible-GPU loading via `CUDA_VISIBLE_DEVICES=<gpu>` and `--local-device-map cuda:0`
  - reshard the format module to `3` workers over `GPU1–GPU3`

Why:

- This preserves the scientific object of the pack:
  - `IFEval` remains the easier verifiable instruction-following surface
  - `IFBench` remains the harder OOD surface
  - the planning-format bridge remains the format-vs-semantics control
- The pivots change only tractability and runner fidelity, not the underlying localized-repair comparison.
- A screened `IFEval` smoke under the stabilized path completed cleanly and restored high GPU utilization (`~96%` on the active worker GPU).

Effect:

- The format module proceeds as a benchmark-aligned local-first pack rather than being dropped.
- Heavy format collection is now expected to complete within the remaining wall-clock budget even without `GPU0`.

## 2026-03-17 — LAST-PACK optional model-diversity scope

Context:

- The mandatory `LAST-PACK` modules completed with stable math / planning / format reports.
- The environment recovered access to all four GPUs after the earlier orphan-allocation issue cleared.

Decision:

- Run the optional reduced replication under `Qwen/Qwen2.5-Math-7B-Instruct`, but keep it bounded to the most stable non-math validators:
  - planning model subset (`300`)
  - planning-format bridge (`200`)
- Do not reopen the frozen full math pipeline under a second model inside this phase.

Why:

- This keeps the optional pack within the sidecar budget while still stress-testing the broader late-stage targeted-repair story on a second local model.
- Planning and bridge validators are deterministic and low-friction, so directional model-diversity evidence here is cleaner than a rushed partial math rerun.

Effect:

- The optional replication will materially strengthen the “beyond one model” reading if the direction holds.
- The frozen CASS math claim surface remains untouched.

## 2026-03-17 — LAST-PACK second-model stable-format pivot

Context:

- The first reduced second-model read on planning + planning-format bridge was harsher than expected.
- Planning under `Qwen/Qwen2.5-Math-7B-Instruct` collapsed across direct / restart / suffix repair, so that surface alone is too brittle to carry the broader model-diversity read.

Decision:

- Do not stop at that first weak result.
- Add one bounded second-model pivot on a screened `IFEval` subset, because it is the most stable non-math validator already integrated in this repo.
- Keep the frozen localized-repair methods and answer normalization unchanged.

Why:

- This stays inside the sidecar pack rather than inventing a new branch.
- It directly answers whether the local-repair-vs-rewrite direction survives on a second model when the validator is stable and the task is not dominated by planning-search brittleness.

Effect:

- The final `LAST-PACK` model-diversity read will distinguish:
  - a brittle planning-domain failure
  - from a more stable format/constraint generalization check

## 2026-03-17 — LAST-PACK reduced-IFEval rerun after deterministic patch fix

Context:

- The first reduced `IFEval` second-model pass exposed a runner bug rather than a clean scientific outcome.
- The deterministic `FORMAT_ONLY_PATCH` branch used double-escaped regexes in the `min_words` and highlight checks, which can create an effectively unbounded extension loop on prompts with `at least N words`.

Decision:

- Fix the regex bug immediately.
- Add a regression test.
- Discard the partial reduced-`IFEval` second-model attempt and rerun all `4` shards under the same model and prompts.

Why:

- Mixing pre-fix and post-fix shards would make the model-diversity comparison untrustworthy.
- This is a narrow implementation correction inside the frozen localized-repair method, not a new method or prompt change.

Effect:

- The second-model format read remains fair and reproducible.
- The rerun directly tests whether local constraint repair still helps once the deterministic patch path behaves as intended.

## 2026-03-17 — LAST-PACK final framing decision

Context:

- All mandatory modules are complete.
- The optional second-model pack is also complete after the reduced-`IFEval` rerun that fixed the deterministic patch bug.

Decision:

- Use `LAST-PACK` as appendix / advisor-facing reinforcement for the frozen `CASS` story.
- Do not elevate it into a new main-claim branch.

Why:

- The support is real and useful:
  - hard math failures are later and more locally repairable than easy transfer failures
  - localized repair beats restart on the registered planning validator once failures are late
  - output-constraint tasks give the cleanest beyond-math support, including on a second local model for reduced `IFEval`
  - a simple pooled intervention criterion improves over always-restart and matches always-local utility at lower intervention rate
- The limits are also clear:
  - planning transfer is model-sensitive
  - the bridge control remains mostly semantic-only, so local formatting repair is not universal
  - some math pockets still prefer restart

Effect:

- The paper can now present the broader framing as a well-supported appendix / mechanism / future-work story.
- The primary frozen `CASS` methods claim remains unchanged and does not depend on overclaiming universal cross-domain dominance.

## 2026-03-18 — LACE scope and execution decision

Context:

- `LAST-PACK` already established the offline criterion story.
- The remaining advisor-facing gap is operational: when should the system leave an answer alone, patch locally, or restart?

Decision:

- Run `LACE` as a bounded online-policy sidecar rather than a new methods branch.
- Keep the frozen `CASS` mechanism unchanged.
- Reuse frozen math traces where the direct / local / restart outcomes are already fully observed.
- For non-math deployment evidence, rerun the existing local-first collectors under fresh `LACE` outputs:
  - screened `IFEval`
  - `IFBench`
  - fresh lineworld planning boundary set

Why:

- Math already has the right replay object: direct drafts, sparse local repair, and restart outcomes on identical examples.
- Output-constraint and planning tasks have strong deterministic validators, which makes online policy analysis much cleaner.
- This preserves the scientific object of the phase:
  - not a new repair method
  - not a new router
  - but a deployable criterion over frozen actions

Effect:

- `LACE` can answer the practical criterion question directly.
- Heavy local collection is concentrated where fresh deployment evidence is most informative and cheapest to validate.

## 2026-03-18 — LACE optional replication expansion decision

Context:

- The primary `LACE` modules already support the online-criterion story.
- The remaining advisor-facing gap is whether that story survives a second local model strongly enough to be worth citing in presentation and appendix material.

Decision:

- Expand the optional module beyond the originally planned tiny `IFEval` spot-check.
- Run:
  - a reduced but replay-compatible second-model math pack
  - a fresh second-model output-constraint rerun on screened `IFEval` and `IFBench`
- Keep the policy object fixed:
  - `NO_INTERVENTION`
  - `LOCAL_REPAIR`
  - `GLOBAL_RESTART`

Why:

- The broader framing is already promising enough that a fuller stress test is more useful than a tiny illustration.
- The repo already contains compatible manifests, collectors, validators, and secondary-model infrastructure, so this expansion is not an infrastructure detour.
- A fuller second-model pack is more advisor-useful than a single spot-check because it tests both math and beyond-math online policy behavior.

Effect:

- `LACE` can now close with a materially stronger model-diversity read if the direction survives.
- If the second model weakens badly, the pack will still define an honest boundary on the scope of the online-criterion claim.

## 2026-03-18 — LACE second-model execution fidelity decisions

Context:

- The optional `LACE` module expanded beyond the original tiny spot-check.
- The open question was how to keep the replication reviewer-useful without quietly changing surfaces or spending time on avoidable reruns.

Decision:

- Keep the frozen `cass_r4` reduced-math manifests as they already existed in the repo.
- This means the actual second-model fresh math replication used:
  - `400` cluster-hard examples
  - `200` generic-hard examples
  - not the smaller provisional `300 + 150` sketch from the pre-run estimate
- For output-constraint model diversity, reuse the fixed reduced screened-`IFEval` local traces from `LAST-PACK` rather than launching a fresh full `IFEval + IFBench` secondary-model rerun.

Why:

- Regenerating smaller math manifests would have introduced silent split drift into a phase whose whole point was criterion deployment, not new data curation.
- The reduced screened-`IFEval` fallback was already local, stable, validator-rich, and sufficient to answer the narrower directional model-diversity question.
- This kept the optional module bounded while still producing a real answer on math and format.

Effect:

- The model-diversity read is stronger on math than originally planned.
- The format read is narrower but still reviewer-usable because the fallback surface is explicit and stable.
- No new API path or new infrastructure branch was needed.

## 2026-03-18 — LACE final scope decision

Context:

- Primary-model `LACE` succeeded on math and output-constraint tasks.
- Optional second-model replication showed:
  - math direction survives under within-model fitting
  - reduced screened-`IFEval` direction survives narrowly
  - planning collapses

Decision:

- Present `LACE` as a real online-policy operationalization of the late-stage targeted-repair framing.
- Keep the cross-model claim explicitly bounded:
  - replicated for math
  - directionally supported on a stable format slice
  - not supported on planning

Why:

- This is the strongest numerically honest read of the collected evidence.
- It strengthens the broader framing around `CASS` without inventing a new methods branch or overclaiming universality.

Effect:

- `LACE` can support advisor-facing presentation and appendix material as a practical intervention-policy layer over the frozen `CASS` story.
- Planning remains in the paper as a control/boundary result, not as a flagship generalization claim.

## 2026-03-18 — LACE-R2 scope and fallback decision

Context:

- `LACE` already answered the main online-policy question positively on the primary model.
- The main remaining soft spots are criterion simplicity, cross-family robustness, and fresh second-model format evidence.

Decision:

- Run `LACE-R2` as a bounded reinforcement pack, not as a new methods branch.
- Keep the current online action space unchanged:
  - `NO_INTERVENTION`
  - local repair
  - global restart / rewrite
- Bring up one non-Qwen family with immediate fallback order:
  1. `Mistral`
  2. `Llama`
  3. `Gemma`

Why:

- This directly addresses the remaining reviewer-facing questions without broadening the scientific claim.
- The fallback order prevents model bring-up from becoming an infrastructure detour.
- Criterion simplification can be done entirely on frozen traces before heavy collection begins.

Effect:

- `LACE-R2` will either produce a simpler, more explainable rule plus cross-family support, or define a cleaner boundary on what robustness is and is not supported.

## 2026-03-18 — LACE-R2 completion decisions

Context:

- `LACE` had already answered the main online-policy question on the primary Qwen family.
- The remaining reviewer-facing gaps were:
  - criterion simplicity
  - genuine cross-family robustness on math
  - a fresh second-model format rerun

Decision:

- Keep `Mistral-7B-Instruct-v0.3` as the cross-family family because first-choice bring-up succeeded cleanly.
- Stop the cross-family math collection after the reduced cluster-hard rerun.
- Refresh the format evidence with a fresh screened-`IFEval` rerun only.
- Skip the optional planning sanity refresh.

Why:

- The reduced cluster-hard rerun already answered the main cross-family math question:
  - within-model gating still beats naive restart
  - and remains competitive with or slightly above always-local repair
- Fresh screened `IFEval` is the cleanest validator-rich format surface for a reviewer-facing freshness check.
- Adding generic-hard, `IFBench`, or planning at this stage would mostly increase runtime without changing the headline reinforcement read proportionally.

Effect:

- `LACE-R2` stays bounded and directly addresses the soft spots that remained after `LACE`.
- The final cross-family claim is cleaner:
  - math direction survives on `Mistral`
  - format local-repair-over-rewrite survives on a fresh second-model rerun
  - planning remains intentionally outside the headline robustness claim

## 2026-03-18 — LACE-R2 criterion simplification decision

Context:

- The learned gate worked, but reviewer-facing explanation cost was still higher than ideal.
- The pack needed a smaller rule family that preserved most of the utility.

Decision:

- Promote the smallest viable rule family, not the most complex tree, as the main interpretability read.
- Keep the stronger simple family in tables when it materially improves utility.

Why:

- On the primary math surface:
  - `SIMPLE_2FEATURE_GATE = 0.753`
  - `LEARNED_GATE = 0.759`
  - the utility gap is small enough that the two-feature rule is the cleaner story
- On the fresh cross-family math rerun:
  - `SIMPLE_BEST_GATE = 0.290`
  - `LEARNED_GATE_WITHIN = 0.282`
  - so simplification did not require paying a robustness penalty
- On the fresh cross-family format rerun:
  - `SIMPLE_BEST_GATE = 0.603`
  - `LEARNED_GATE_WITHIN = 0.539`
  - again the simple rule remained competitive or better

Effect:

- The broader `CASS` / `LACE` framing can now be explained operationally as a small rule over late-stage and localized-failure signals, not only as a learned gate.
- The paper can present the learned gate as support and the simple rule as the cleaner deployment interpretation.

## 2026-03-18 — LACE-R3 scope decision

Context:

- `LACE-R2` already closed the main simplicity question on the primary family.
- The remaining softness is now narrower:
  - portability of the simple rules vs learned transfer
  - fresh cross-family `IFBench`
  - whether one-family cross-family support is enough

Decision:

- Run `LACE-R3` as a portability-support pack, not as a new methods branch.
- Reuse the existing `Mistral` family first.
- Make fresh `IFBench` the only new mandatory collection target.
- Defer any third-family bring-up until after the `Mistral` portability and `IFBench` answers are visible.

Why:

- This keeps the pack tightly aligned to the remaining reviewer-facing questions.
- The `Mistral` reruns from `LACE-R2` already provide the right starting point for transfer-vs-within analysis.
- `IFBench` is the largest remaining format-side gap; it is more valuable than immediately broadening to another family.

Effect:

- `LACE-R3` should either show that simple rules are the cleaner portable story, or cleanly bound where portability still depends on within-model tuning.

## 2026-03-18 — LACE-R3 close-out decision

Context:

- `Mistral` portability analysis already showed:
  - math best simple transfer `0.290` vs learned transfer `0.183`
  - screened `IFEval` best simple transfer `0.624` vs learned transfer `0.574`
- The fresh cross-family `IFBench` rerun then showed:
  - `ALWAYS_FULL_REWRITE = 0.155`
  - `LEARNED_GATE_TRANSFER = 0.204`
  - `SIMPLE_BEST_GATE_TRANSFER = 0.223`
  - `LEARNED_GATE_WITHIN = 0.194`

Decision:

- Close `LACE-R3` after the completed `Mistral` portability + fresh `IFBench` pack.
- Do not bring up a third family inside this phase.
- Present the simple transferred rule family as the cleaner portability story, with learned-within gates as secondary support rather than the main explanation.

Why:

- The remaining reviewer-facing softness was specifically the missing fresh cross-family `IFBench` evidence and the simple-vs-learned portability question.
- Both are now answered on the same genuine non-Qwen family.
- A third-family bring-up would broaden the pack more than it would clarify the already-resolved portability question.

Effect:

- The advisor-facing story is now:
  - simple portable rules beat naive restart or rewrite
  - simple transfer can beat learned transfer across math and validator-rich format surfaces
  - within-model tuning still matters on math, but is not the cleanest portability story on the format surfaces

## 2026-03-19 — CASS-XF scope decision

Context:

- The main `CASS` result is already locked on the primary `Qwen` family.
- The broader late-stage criterion story is already supported by `LAST-PACK` and `LACE`.
- `LACE-R3` already addressed criterion portability on `Mistral`.
- The remaining reviewer-facing softness is now narrower:
  - the frozen `CASS` method family itself has not yet been directly replicated on a genuinely different family

Decision:

- Run `CASS-XF` as a main-method portability pack, not as a new methods branch.
- Reuse the existing stable `Mistral` family first.
- Freeze the `cass_r4` reduced replication surfaces as the exact cross-family evaluation surfaces.
- Defer any third-family bring-up until after the `Mistral` read is visible.

Why:

- This isolates the remaining main-method portability question without reopening the criterion story.
- The `cass_r4` reduced subset manifests already give a reproducible `400 / 200` cluster/generic split that matches the requested reduced replication regime.
- `Mistral` is already known to be stable on this box, so it is the right first non-Qwen family.

Effect:

- `CASS-XF` should either show that the frozen `CASS` patch family remains directionally favorable beyond `Qwen`, or cleanly bound where cross-family support for the main method is still weak.

## 2026-03-19 — CASS-XF third-family decision

Context:

- The completed `Mistral` reduced replication preserved the main direction of the frozen `CASS` family on both reduced surfaces.
- On `hard_cluster_main_r2`, the best frozen `CASS` variant beat `RAW_PYTHON` clearly and was directionally above `OPERATOR_SCHEMA_TO_CODE_BASE`.
- On `hard_generic_main_r2`, the same direction held and the ranking again favored target/postprocess-centered patching.
- The within-family `CASS` ranking changed only mildly:
  - `Qwen` preferred the conservative gate
  - `Mistral` preferred the fixed target/postprocess patch because the gate added no extra gain

Decision:

- Do not run an optional third family in `CASS-XF`.

Why:

- The bounded question for this pack was whether the frozen `CASS` method family itself survives on a genuinely different model family.
- `Mistral` already answers that question positively enough for reviewer-facing support.
- A third family would add cost but is unlikely to change the main interpretation inside this bounded phase.

Effect:

- `CASS-XF` now stands as a one-family non-`Qwen` portability replication showing:
  - strong directional support vs `RAW_PYTHON`
  - directional but reduced-sample-noisy support vs `OPERATOR_SCHEMA_TO_CODE_BASE`
  - target/postprocess patching remains the recurring useful ingredient

## 2026-03-19 — CASS-XF-R2 scope decision

Context:

- `CASS-XF` reduced the main portability softness but left one reviewer-facing gap:
  - `Mistral` was clearly above `RAW_PYTHON`, but not yet statistically locked above `OPERATOR_SCHEMA_TO_CODE_BASE`
- The remaining question is narrower than `CASS-XF`:
  - whether target/postprocess-centered sparse schema surgery is a truly portable core ingredient

Decision:

- Run `CASS-XF-R2` as a portability-lock pack for the frozen main `CASS` family.
- Expand `Mistral` first on the frozen full `cluster-hard` and `generic-hard` portability surfaces.
- Require one additional third family after `Mistral` scale-up, using the prompt’s fallback order.

Why:

- This directly targets the only remaining cross-family skepticism without reopening the method.
- The full `cass_r4` manifests already provide a larger frozen portability surface for a clean Mistral lock attempt.
- A third family is now justified because the remaining question is no longer whether `CASS` transfers at all, but whether target/postprocess patching is the stable portable core.

Effect:

- `CASS-XF-R2` should either:
  - strengthen the claim that target/postprocess patching is a portable main ingredient across families
  - or honestly bound the portability claim to “directionally portable, but not yet family-invariantly locked”

## 2026-03-19 — CASS-XF-R2 model fallback and sharding decision

Context:

- The prompt required a third family after `Mistral`, with `Llama-3.1-8B-Instruct` preferred and `Gemma-2-9B-it` as the next fallback.
- Actual frozen collector smoke attempts matter more than metadata visibility.
- The first expanded `Mistral` full-surface run also exposed a practical imbalance:
  - contiguous shard assignment put many previously cached reduced-run examples into the first shard
  - one GPU drained early even though the full manifest semantics were still frozen

Decision:

- Treat `Llama-3.1-8B-Instruct` and `Gemma-2-9B-it` as unavailable on this box for this phase because both fail at real model load with gated-repo `401`.
- Move the third-family path to the first stable open fallback family that survives the frozen collector smoke.
- Rebuild only the expanded `Mistral` shard files in deterministic round-robin order and relaunch the lock attempt.

Why:

- Real collector accessibility is the relevant criterion, not just public metadata visibility.
- Round-robin sharding preserves the frozen full-manifest order while restoring the intended 4-GPU data-parallel workload balance.
- The corrected `Mistral` run is a better scientific artifact than a lower-utilization run whose shard balance is accidentally dominated by old cache placement.

Effect:

- `CASS-XF-R2` keeps the same frozen surfaces and methods.
- The third-family choice is now constrained to open accessible fallback families only.
- The expanded `Mistral` lock attempt can be interpreted as a true 4-GPU balanced collection rather than a cache-skewed partial replay.

## 2026-03-19 — CASS-XF-R2 third-family candidate decision

Context:

- `Llama-3.1-8B-Instruct`, `Gemma-2-9B-it`, and `Aya-Expanse-8B` all fail at actual model load here because they are gated.
- `Phi-4-mini-instruct` and `Phi-3.5-mini-instruct` are open enough to load weights, but they fail under the frozen repo stack because their generation path expects newer `transformers` cache APIs.
- The remaining open accessible candidate from the fallback set is `ibm-granite/granite-3.1-8b-instruct`.

Decision:

- Use `ibm-granite/granite-3.1-8b-instruct` as the third-family candidate for `CASS-XF-R2`.

Why:

- It is a genuinely different non-`Qwen`, non-`Mistral` family.
- It is open and now fully cached locally.
- It avoids the gated-access failures that ruled out the higher-priority families and the stack-compatibility failures that ruled out the `Phi` family on this box.

Effect:

- Once the expanded `Mistral` step finishes, the third-family reduced replication can proceed on `Granite` without additional model download delay.

## 2026-03-19 — CASS-XF-R2 ended-state reporting decision

Context:

- The completed experiment window ended after the expanded `Mistral` cluster-hard run.
- That ended run already answered the highest-priority question in the pack:
  - target/postprocess-centered `CASS` patching is statistically locked above `OPERATOR_SCHEMA_TO_CODE_BASE` on expanded `Mistral` cluster-hard
- The ended run did not include:
  - expanded `Mistral` generic-hard
  - `Granite` reduced replication

Decision:

- Finalize the `CASS-XF-R2` report set against the actually completed experiment window rather than fabricating missing sections.

Why:

- The user explicitly asked to complete reporting for the ended experiment state.
- The main reviewer-facing update is already substantive:
  - `Mistral` cluster-hard moved from directional-only in `CASS-XF` to an actual lock in `CASS-XF-R2`
- Honest partial closure is better than pretending the generic and third-family modules ran when they did not.

Effect:

- `CASS-XF-R2` now records:
  - a real expanded `Mistral` cluster-hard lock
  - a stronger portability argument for target/postprocess patching
  - explicitly open follow-on work for generic-hard and `Granite`

## 2026-03-19 — CASS-XF-R3 scope decision

Context:

- `CASS-XF-R2` closed the most important portability question by locking expanded `Mistral` cluster-hard.
- The only remaining portability gaps are:
  - expanded `Mistral` generic-hard
  - one additional genuinely different family

Decision:

- Run `CASS-XF-R3` as a narrow portability-closure pack.
- Use `Granite-3.1-8B-Instruct` as the required third family because it is the first stable open candidate already cached locally.
- Reuse the frozen `CASS-XF-R2` surface semantics and methods unchanged.

Why:

- This directly addresses the remaining reviewer-facing softness without reopening the method story.
- `Granite` is the first fallback that survived the access constraints on this box.
- Reusing the existing manifes/runner stack keeps the phase bounded and reproducible.

Effect:

- `CASS-XF-R3` should either close the portability story across three families or honestly bound it as “strong across two, suggestive on a third.”

## 2026-03-20 — CASS-XF-R3 closure decision

Context:

- Expanded `Mistral` generic-hard preserved the `CASS` direction:
  - strong over `RAW_PYTHON`
  - directional but not statistically locked over `OPERATOR_SCHEMA_TO_CODE_BASE`
- Reduced `Granite` replication did not preserve the absolute direction:
  - the best frozen `CASS` patch trailed both `RAW_PYTHON` and `OPERATOR_SCHEMA_TO_CODE_BASE` on cluster-hard and generic-hard
- Even on `Granite`, however, the best frozen `CASS` ingredient remained the target/postprocess patch rather than role-only repair or the gate.

Decision:

- Close `CASS-XF-R3` with the following final reading:
  - the portable-core claim is supported across three families
  - the stronger absolute cross-family win claim is supported across two families and contradicted on `Granite`

Why:

- This separates the robust ingredient-level story from the weaker family-invariant absolute-performance story.
- It is the numerically honest way to preserve the value of the `Granite` run without overstating what it shows.

Effect:

- The repo now supports:
  - target/postprocess patching is the clearest portable core of the frozen `CASS` family
  - the conservative gate remains more family-dependent
  - additional family-based replication is less important for the core-ingredient story than it was before `CASS-XF-R3`, but still relevant for any stronger absolute portability claim

## 2026-03-20 — CASS-BD scope decision

Context:

- `Granite` is now the only clear family-level boundary case.
- The key unresolved question is not whether `CASS` works overall, but why `Granite` reverses the absolute direction while still preferring the target/postprocess patch inside the frozen `CASS` family.

Decision:

- Run `CASS-BD` as a Granite-only diagnosis pack.
- Reuse the frozen Granite reduced surfaces from `CASS-XF-R3`.
- Prefer replay-controlled partial surgery over any new full-family experiment.

Why:

- This isolates the real remaining scientific issue:
  - whether `Granite` is baseline-dominant, patch-destructive, extraction-limited, compiler-limited, or some combination
- The necessary raw traces already exist, so the right next step is mechanistic diagnosis, not another portability sweep.

Effect:

- `CASS-BD` should either yield a clean Granite boundary explanation or justify a tiny teacher diagnostic if replay evidence is still ambiguous.

## 2026-03-20 — CASS-BD boundary conclusion

Context:

- Granite field audit showed many `baseline-right / patch-wrong` cases, and those cases were dominated by code-generation-after-patch rather than by the milder quantity-role interaction pattern seen in `Qwen` and `Mistral`.
- Replay-controlled partial surgery showed a strong asymmetry:
  - postprocess-only and discretization-only edits recover much of the baseline strength
  - target-only and target+postprocess edits remain net-negative relative to Granite `RAW_PYTHON`

Decision:

- Close the Granite boundary case as:
  - primarily baseline-dominant
  - with destructive target/relation overwrite
  - plus compiler/code-generation brittleness after those target edits
- Skip the optional teacher diagnostic.

Why:

- If postprocess/discretization-only replay recovers direction on the same baseline schema, the failure is not well explained by missing extraction alone.
- The most harmful component is the target-side overwrite, not the postprocess/discretization correction itself.
- That makes a tiny teacher diagnostic lower-yield than the evidence already collected.

Effect:

- The main paper can present Granite as a clean boundary case:
  - target/postprocess patching remains the strongest ingredient inside the frozen `CASS` family
  - but on a baseline-dominant family like Granite, aggressive target-side overwrites can erase the baseline advantage and trigger code-generation brittleness

## 2026-03-21 — CASS-SR scope decision

Context:

- Family breadth has already done most of its work:
  - `Qwen` is locked
  - `Mistral` supports the portable-core read
  - `Granite` defines the boundary
- The next most valuable question is whether the frozen `CASS` core remains useful as the base model itself gets substantially stronger.

Decision:

- Run `CASS-SR` as a model-scale robustness pack.
- Use the frozen reduced `400 / 200` cluster/generic surfaces copied from the `CASS-XF` lineage.
- Require `Qwen/Qwen2.5-14B-Instruct`.
- Attempt `Mistral-Small-24B-Instruct-2501` only if smoke and serving remain low-friction.

Why:

- This is the narrowest way to test whether the `CASS` story is mainly a small/medium-model intervention or whether the target/postprocess patch remains meaningful as scale increases.
- The reduced surfaces are already frozen and comparable, so a stronger-model run can be interpreted cleanly without reopening the datasets.

Effect:

- `CASS-SR` should either show that the target/postprocess patch remains a meaningful frozen ingredient at larger scale, or honestly bound the story as strongest in small/medium open models.

## 2026-03-21 — CASS-SR closure decision

Context:

- `Qwen-14B` completed on the frozen reduced cluster-hard and generic-hard surfaces.
- On both surfaces, the best frozen `CASS` ingredient remained the target/postprocess patch.
- But on both surfaces, that patch trailed both `RAW_PYTHON` and `OPERATOR_SCHEMA_TO_CODE_BASE` by a clear margin.
- The optional `Mistral-Small-24B` path did not satisfy the low-friction requirement after bring-up attempts, so it was not run.

Decision:

- Close `CASS-SR` with the following read:
  - the target/postprocess patch remains the most stable frozen `CASS` ingredient as scale increases
  - the overall intervention is not scale-robust in absolute terms
  - the strongest paper framing is now “small/medium-model-strong portable core,” not “larger-scale absolute win”

Why:

- This preserves the ingredient-level story without pretending the absolute effect survives stronger open baselines.
- It is the numerically honest interpretation of the 14B results.

Effect:

- The repo now supports a clear scale diagnosis:
  - `CASS` is strongest as a small/medium-model intervention
  - the portable core persists at larger scale
  - but stronger open models solve enough of the target/postprocess burden themselves that the patch no longer beats the best frozen baselines

## 2026-03-22 — CASS-FI closure decision

Context:

- The `Granite` diagnosis already suggested that postprocess/discretization edits were the safe part of the patch while target-side edits were risky.
- `CASS-FI` extended the same replay-controlled field isolation to `Qwen-7B`, `Mistral-7B`, and `Qwen-14B`.
- The resulting ranking pattern is asymmetric:
  - `Granite-8B` and `Qwen-14B` promote `POSTPROCESS_ONLY_PATCH`
  - `Mistral-7B` keeps `TARGET_PLUS_POSTPROCESS_PATCH` at the top
  - `Qwen-7B` still tolerates or prefers target-side-inclusive variants on at least one surface

Decision:

- Close `CASS-FI` with the following field-aware portable-core read:
  - the safest cross-family core is `postprocess/discretization-centered patching`
  - target-side edits are family/scale-sensitive rather than universally portable

Why:

- This preserves the real signal from the replay matrix instead of forcing one monolithic patch interpretation.
- It explains why `Granite` and `Qwen-14B` behave similarly despite different family identities: both penalize target-side overwrite more than smaller/medium-scale cells do.

Effect:

- The main paper can tighten its wording from:
  - `target/postprocess patching`
  - to
  - `postprocess/discretization-centered patching, with target-side surgery being conditionally useful on smaller-model cells and risky on stronger/boundary cells`

## 2026-03-23 — Code-Last execution-path decision

Context:

- `code_last` is a bounded sidecar pack to test whether late-stage targeted repair transfers to validator-rich function-level coding.
- The required benchmark stack is `EvalPlus` over `HumanEval+` and `MBPP+`.
- Direct smoke showed that loading the local model and running EvalPlus validation inline in the same process causes fork/memory instability.

Decision:

- Run `code_last` with a split collection path:
  - GPU generation first
  - EvalPlus validation second on frozen outputs
  - then slice construction
  - then repair generation
  - then repair validation

Why:

- This preserves the frozen coding methods while avoiding the unstable pattern where EvalPlus forks from a model-loaded process.
- It also keeps the heavy phases GPU-centric, which is the only realistic way to push utilization high on the local 4-GPU box.

Effect:

- The main `code_last` run will be:
  - more stable
  - easier to resume
  - more faithful to the “local-first, validator-rich” design than an inline generation+evaluation loop

## 2026-03-23 — Code-Last left-padding correction

Context:

- The first batched `Qwen` coding pass (`20260323b`) surfaced decoder-only right-padding warnings from the local `hf_local` batch path.
- A right-padding warning on its own is not enough to throw away a run, so a targeted A/B smoke was run after forcing `tokenizer.padding_side = "left"`.
- The A/B difference was material:
  - direct `32`-task smoke changed `10 / 32` generated solutions
  - repair `4`-task smoke changed all `4 / 4` tasks on at least one repair branch

Decision:

- Treat `qwen7b_direct_20260323b` and `qwen7b_repairs_20260323b` as exploratory only.
- Restart the main `Qwen` coding pack from a clean left-padding namespace:
  - `/workspace/project/results/code_last_main/qwen7b_direct_20260323c_leftpad`
  - `/workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad`

Why:

- The direct and repair outputs are not stable enough under the padding change to support final numerics.
- The bounded coding-side pack is only useful if the collection path is trustworthy.

Effect:

- Final `code_last` reporting will use only the corrected left-padding run.
- The earlier `20260323b` artifacts remain on disk as debugging evidence but are not part of the final result set.

## 2026-03-23 — Code-Last stop-after-Qwen decision

Context:

- The corrected `Qwen/Qwen2.5-7B-Instruct` coding pack completed on frozen `EvalPlus` slices.
- The main scientific question was whether late-stage targeted local repair transfers to validator-rich function coding in a bounded and interpretable way.
- The primary read is informative, but not cleanly positive:
  - the near-correct slice exists and is late-stage-like
  - `LOCAL_TEST_GUIDED_PATCH` ties `FULL_REWRITE_FROM_FAILURE` on the pooled near-correct slice instead of beating it
  - `HumanEval+` is favorable while `MBPP+` is slightly rewrite-favoring

Decision:

- Stop after the primary `Qwen` coding pack.
- Do not run optional `Mistral-7B-Instruct-v0.3` reduced replication.
- Do not run optional `MGDebugger-lite` contextual subset.

Why:

- A second-family replication is most valuable when the primary read is clearly promising and worth locking across families.
- Here the bounded conclusion is already visible:
  - a genuine near-correct late-stage coding region exists
  - it is concentrated in boundary/postcondition failures
  - but local patch is not universally better than full rewrite
- Extra runtime would add cost without materially changing the honest conclusion.

Effect:

- `code_last` closes as a bounded support pack for the broader framing rather than a new coding-methods branch.
- The main paper can cite coding as:
  - supportive evidence that late-stage pockets exist in function coding
  - but not evidence that local patch universally dominates rewrite in code

## 2026-03-23 — Code-Last-R2 Qwen reuse decision

Context:

- `Code-Last-R2` tightens the coding-side slice definition but keeps:
  - the same frozen `Qwen` model
  - the same prompts
  - the same repair methods
- The corrected `Code-Last` run already produced complete frozen direct and repair outputs for all relevant tasks.

Decision:

- Reuse the frozen corrected `Qwen` outputs for `Code-Last-R2`.
- Do not rerun identical `Qwen` generations just to relabel the slice.

Why:

- the new information comes from deterministic slice restriction, not from a changed model or method
- duplicate `Qwen` collection would add cost without adding evidence
- this is the most numerically honest and bounded way to clarify the coding read

Effect:

- `Code-Last-R2` `Qwen` is a projection/replay clarification phase
- the only fresh GPU-heavy run, if the strict-slice read warrants it, will be optional `Mistral` reduced replication

## 2026-03-23 — Code-Last-R2 Mistral replication decision

Context:

- The frozen `Qwen-7B` strict repair-eligible slice produced a cleaner signal than the original pooled `Code-Last` read:
  - `LOCAL = 0.2308`
  - `REWRITE = 0.1538`
- The positive direction was narrow but real enough to justify checking whether the coding-side read survives a second family.

Decision:

- Run the optional reduced `Mistral-7B-Instruct-v0.3` replication.
- Do not run `MGDebugger-lite`.

Why:

- the strict `Qwen` read was promising enough to justify a second-family check
- `MGDebugger-lite` would add contextual overhead without answering the central clarification question
- second-family direction is more valuable than a lite comparator for this phase

Outcome:

- `Mistral` direct geometry produced:
  - exact public-pass / extended-fail `= 28`
  - relaxed near-correct `= 46`
  - frozen strict repair-eligible `= 4`
- That strict slice collapsed to an `MBPP`-only pocket, and the reduced replication did not preserve the `Qwen` local-patch direction:
  - strict: `REWRITE = 0.25`, `LOCAL = 0.0`
  - relaxed: `REWRITE = 0.1087`, `LOCAL = 0.0435`
- Final decision:
  - keep `Code-Last-R2` as a bounded clarification pack
  - report coding transfer as real but narrow
  - skip `MGDebugger-lite`

## 2026-03-23 — Code-Last-R3 HumanEval-only design decision

Context:

- `Code-Last-R2` showed that the only clean positive coding-side signal lives in the tiny strict repair-eligible `Qwen-7B` pocket:
  - `n = 13`
  - all `boundary_or_off_by_one`
  - `LOCAL = 0.2308`
  - `REWRITE = 0.1538`
- That signal came from `HumanEval+`, while `MBPP+` stayed flat or mixed.
- The next justified step is therefore not broader coding coverage, but a higher-power check inside the same HumanEval+ pocket.

Decision:

- Focus `Code-Last-R3` on `HumanEval+` only.
- Treat `MBPP+` as optional contrast/support only.
- Use a reproducible multi-sample completion bank rather than broadening to new coding families or tasks.

Why:

- this directly targets the underpowered part of the existing positive signal
- it preserves the bounded function-level validator-rich setting
- it avoids turning the coding pack into repo-level APR or a benchmark shootout

Effect:

- the main evidence will come from a larger HumanEval+ repair-eligible pocket
- `MBPP+` will not dominate the phase
- `Mistral` remains optional and depends on the primary `Qwen` HumanEval+ read being meaningfully positive

## 2026-03-23 — Code-Last-R3 strict rule and sampling decision

Decision:

- Freeze the HumanEval+ multi-sample bank at:
  - `8` completions per task
  - temperature `0.8`
  - top-p `0.95`
  - fixed manifest order
  - 4-way round-robin sharding
- Freeze the strict repair-eligible rule at:
  - exact public-pass / extended-fail
  - `extended_fail_count <= 8`
  - exclude `syntax_or_runtime`
  - exclude `api_or_signature_mismatch`
  - exclude `broad_algorithmic_failure`
  - require `boundary_or_off_by_one` or `return_or_postcondition`

Why:

- `K = 8` preserves continuity with the clean strict rule from `Code-Last-R2`
- the new power comes from multi-sampling inside HumanEval+, not from widening the rule after seeing results
- deterministic sampling config keeps completion-level and task-clustered analyses reproducible

## 2026-03-23 — Code-Last-R3 optional expansion decision

Context:

- `Code-Last-R3` produced a real but still small strict HumanEval+ pocket:
  - `12` completions
  - `3` tasks
  - all `boundary_or_off_by_one`
- On that strict slice the direction is positive:
  - `LOCAL_TEST_GUIDED_PATCH = 0.5000`
  - `FULL_REWRITE_FROM_FAILURE = 0.3333`
- But the task-clustered interval still touches `0` because the pocket remains task-sparse.
- The relaxed HumanEval+ slice stays mixed:
  - `LOCAL = 0.2583`
  - `REWRITE = 0.2833`

Decision:

- Do not run optional `Mistral-7B` reduced replication.
- Do not run optional `MBPP+` contrast rerun.
- Do not run `MGDebugger-lite`.

Why:

- the positive HumanEval+ read is real enough for a bounded appendix/talk signal, but not strong enough to justify a second-family coding claim
- `MBPP+` was already established as mixed in `Code-Last-R2`, and re-opening it would dilute the HumanEval-focused clarification
- `MGDebugger-lite` remains contextual overhead rather than a direct answer to the central repair-eligibility question

Outcome:

- `Code-Last-R3` closes as a HumanEval+-focused clarification pack
- the most defensible coding-side story is:
  - broader localized repair helps on a tiny boundary-heavy repair-eligible pocket
  - the effect does not generalize cleanly to relaxed or broad-fail coding slices

## 2026-03-23 — Code-Last-R4 high-power HumanEval design decision

Context:

- `Code-Last-R3` clarified the coding-side read but did not actually solve the power problem:
  - strict HumanEval+ slice = `12` completions from `3` tasks
  - all failures are `boundary_or_off_by_one`
  - `LOCAL = 0.5000`
  - `REWRITE = 0.3333`
- The positive direction is real enough to justify more power, but not broad enough to justify reopening pooled coding or repo-level repair.

Decision:

- Focus `Code-Last-R4` on high-power `HumanEval+` mining only.
- Freeze three strict tiers:
  - Tier1 `extended_fail_count <= 2`
  - Tier2 `extended_fail_count <= 4`
  - Tier3 `extended_fail_count <= 8`
- Freeze the completion-bank escalation rule:
  - start with `32` completions/task
  - expand to `64` only if Tier1 task count `< 15` or Tier2 task count `< 25`
- Keep `MBPP+` as contrast/support only.

Why:

- this directly targets the underpowered part of the existing positive signal
- it preserves the bounded HumanEval+ validator-rich setting
- it avoids turning the coding track into a broader APR benchmark branch

Effect:

- the primary read for `Code-Last-R4` will be task-clustered local-vs-rewrite comparisons on Tier1/Tier2/Tier3
- optional `Mistral` remains conditional on a meaningfully positive Tier1 or Tier2 `Qwen` result

## 2026-03-23 — Code-Last-R4 strict top-off correction decision

Context:

- The initial Qwen strict repair sweep produced the correct directional read, but a small set of strict question ids did not appear in the repair outputs.
- Relaxed and contrast surfaces were complete, but the strict tiers are the main scientific surface for `Code-Last-R4`.

Decision:

- Run a strict-only top-off rerun on the missing strict question ids before finalizing the report.

Why:

- the main claim of this phase lives on Tier1/Tier2/Tier3
- leaving avoidable strict omissions in place would make the final read less trustworthy than necessary

Effect:

- final reported strict numbers use the top-off-inclusive aggregate
- strict task coverage is restored to `5 / 8 / 11` task clusters
- the main positive Tier2 task-clustered result is read from the corrected aggregate

## 2026-03-23 — Code-Last-R4 optional Mistral reduced replication decision

Context:

- After strict top-off, Qwen Tier2 crossed the main optional threshold:
  - task-clustered `LOCAL - REWRITE = +0.1014 [0.0139, 0.2264]`
- Runtime remained comfortably manageable.

Decision:

- Run the optional Mistral reduced replication, but keep it tightly bounded:
  - Qwen Tier2 task union only
  - `8` HumanEval tasks
  - `64` completions/task
  - strict Tier1/Tier2 repair pack only

Why:

- this satisfies the pre-registered optional condition without reopening broad coding
- it gives a real second-family check at low cost

Effect:

- the reduced Mistral branch remained tiny:
  - Tier1 `12` completions / `1` task
  - Tier2 `22` completions / `2` tasks
- Mistral did not reproduce the Qwen direction:
  - Tier2 rewrite `0.1818`
  - Tier2 local patch `0.0455`
- final coding interpretation remains:
  - positive appendix-level evidence on Qwen HumanEval strict slices
  - no cross-family coding portability claim

## 2026-03-24 — LACE-FULL second-pillar expansion decision

Context:

- The main math-side `CASS` result is already strong enough for paper submission.
- Output-constraint tasks are the clearest non-math domain in the repo:
  - primary-family full pack already positive
  - fresh `Mistral` screened `IFEval` and fresh `Mistral` `IFBench` both already exist in narrower prior branches
  - simple transferred rules have repeatedly looked cleaner than learned transfer on the format surfaces
- Coding remained informative but bounded, and did not justify promotion to co-main status.

Decision:

- Launch `LACE-FULL` as a full-scale format-side lock-and-transfer expansion pack.
- Keep the method family frozen:
  - `ALWAYS_DIRECT`
  - `ALWAYS_FULL_REWRITE`
  - `ALWAYS_LOCAL_FORMAT_PATCH`
  - `ALWAYS_SOLVE_THEN_FORMAT`
  - `HEURISTIC_GATE`
  - `LEARNED_GATE`
  - `SIMPLE_2FEATURE_GATE`
  - `SIMPLE_THRESHOLDED_TREE`
  - `SIMPLE_BEST_GATE`
  - `ORACLE_POLICY`
- Freeze the main surfaces as:
  - full screened `IFEval`
  - full `IFBench`
- Require a full primary-family rerun and a full non-Qwen rerun before deciding whether `Qwen-14B` is worth adding.

Why:

- this is the cleanest path to decide whether output-constraint can move from appendix support to co-main placement
- it answers the remaining reviewer-facing questions more directly than another coding or family-breadth branch would
- it preserves the strongest existing validator-rich infrastructure in the repo without inventing a new method line

Effect:

- `LACE-FULL` will be read as a full-volume output-constraint pillar test
- `IFBench` remains the harder boundary surface and will be interpreted directionally rather than as an equal-difficulty twin of screened `IFEval`
- optional `Qwen-14B` is now strictly conditional on the completed `Qwen` + `Mistral` read being strong enough to justify a scale add-on

## 2026-03-24 — LACE-FULL optional Qwen-14B activation decision

Context:

- The completed full-volume `Qwen-7B` read is clearly positive on both frozen main surfaces:
  - screened `IFEval`: `SIMPLE_BEST_GATE - ALWAYS_FULL_REWRITE = +0.1556 [+0.0922, +0.2270]`
  - `IFBench`: `+0.1452 [+0.0680, +0.2330]`
- The completed full-volume `Mistral-7B` read keeps the same direction:
  - screened `IFEval`: `+0.1130 [+0.0426, +0.1773]`
  - `IFBench`: `+0.0686 [+0.0000, +0.1359]`
- The simple transferred rule remains cleaner than learned transfer overall on `Mistral`.

Decision:

- Activate the optional `Qwen/Qwen2.5-14B-Instruct` scale pack using the already validated local `4bit` path.

Why:

- the pre-registered condition for the optional scale pass is now satisfied
- scale is the only major remaining uncertainty in the format-side promotion argument
- the repo already contains a stable `Qwen-14B` local path, so this does not become a new infrastructure branch

Effect:

- `LACE-FULL` will close with a direct family-and-scale synthesis instead of leaving the scale question open
- if `Qwen-14B` weakens materially, the final memo will frame output-constraint as a strong second pillar with a scale-sensitive boundary rather than a universal win

## 2026-03-24 — LACE-FULL final positioning decision

Context:

- The completed full-scale format pack now contains:
  - full screened `IFEval` on `Qwen-7B`, `Mistral-7B`, and `Qwen-14B`
  - full `IFBench` on the same family/scale cells
- Full-read outcomes:
  - `Qwen-7B` and `Mistral-7B` are positive on both main surfaces
  - `Qwen-14B` remains clearly positive on screened `IFEval`
  - `Qwen-14B` `IFBench` compresses toward zero but does not reverse direction

Decision:

- Promote validator-rich output-constraint tasks to co-main empirical placement with math in the paper.

Why:

- this domain now has:
  - full-scale primary-family evidence
  - full-scale non-Qwen transfer evidence
  - an explicit larger-scale read instead of an open scale hole
- the simpler portable rule family remains the cleanest and most defensible transfer story
- coding does not currently provide comparable volume, portability, or stability

Effect:

- the main paper can present output-constraint as the second empirical pillar
- the honest caveat will be:
  - screened `IFEval` is the robust lock surface
  - `IFBench` is the harder boundary surface
  - stronger scale weakens the hard-surface gain without erasing the overall second-domain story

## 2026-03-24 — UNIFY-FULL cross-domain unification decision

Context:

- Math is already a locked main pillar.
- Output-constraint is now strong enough for co-main placement.
- The most valuable remaining paper move is no longer a new domain, but a stronger unified story across the two validated domains.

Decision:

- Launch `UNIFY-FULL` as a pooled cross-domain policy analysis over frozen math and format traces.
- Keep the core local executors frozen:
  - math local repair -> postprocess-centered frozen primitive
  - format local repair -> solve-then-format
- Use one shared abstract action space:
  - `NO_INTERVENTION`
  - `LOCAL_REPAIR`
  - `GLOBAL_REWRITE_OR_RESTART`

Why:

- this directly tests the reviewer-facing question of whether the paper can claim one late-stage repair geometry rather than two parallel stories
- the repo already contains the needed per-example traces, so this can be answered without reopening expensive collection branches
- it preserves the strongest existing evidence while improving coherence at the paper level

Effect:

- `UNIFY-FULL` will be read as a theory-plus-policy integration layer over the two strongest domains
- if pooled rules stay close to domain-specific rules, the paper can claim a genuinely shared intervention geometry
- if pooled rules weaken materially, the paper can still retain the two-pillar posture while framing unification more cautiously

## 2026-03-24 — UNIFY-FULL final paper-positioning decision

Context:

- The completed pooled analysis over frozen math and format traces shows:
  - `Qwen-7B` pooled-vs-rewrite overall `+0.2176 [+0.1799, +0.2578]`
  - `Mistral-7B` pooled-vs-rewrite overall `+0.1694 [+0.1300, +0.2115]`
  - `Qwen-14B` pooled-vs-rewrite overall `+0.1084 [+0.0694, +0.1458]`
- The pooled rule is not a disaster tax:
  - it ties the best shared-action policy on `Qwen-7B`
  - it stays very close on `Mistral-7B`
  - it ties again on `Qwen-14B`
- Transfer asymmetry is constructive rather than contradictory:
  - math-tuned rules remain above rewrite on format
  - format-tuned rules are often very strong on math

Decision:

- Present math and validator-rich output-constraint tasks as two instances of one shared late-stage targeted-repair geometry in the main paper.

Why:

- the pooled rule stays close enough to the domain-tuned rules that unification is no longer just a conceptual analogy
- the strongest shared bucket is `final_requirement_realization`, which is exactly the late-stage region where both domains benefit from local repair
- this gives the paper a cleaner narrative than two parallel case studies without requiring a new method family

Effect:

- the main paper can now use a shared intervention story as the organizing frame
- the honest caveat is that domain-tuned simple criteria still matter at the margins, especially on harder boundary surfaces
- `UNIFY-FULL` should therefore be framed as a unification lock, not as proof that one universal rule strictly dominates every domain-specific criterion

## 2026-03-26 - UNIFY-LIVE-FULL round close decision

Decision:

- Close the current round with completed fresh prospective banks on `Qwen-7B` and `Mistral-7B`, and stop the in-progress `Qwen-14B` run early.

Why:

- the required fresh online evidence on the two core `7B` families is already complete
- the `Qwen-14B` run remained optional, slower, and incomplete
- the user explicitly requested early termination of the `14B` condition

Effect:

- this round supports fresh prospective reporting on the two required `7B` families
- it does not support a completed prospective scale claim on `Qwen-14B`
- the partial `Qwen-14B` artifacts remain preserved as incomplete evidence only

## 2026-03-26 - UNIFY-LIVE-FULL-R2 execution decision

Context:

- The fresh prospective 7B banks are already complete and now need an integrity lock before paper-facing synthesis.
- The current paper question is no longer whether the domains are interesting separately, but whether fresh online evidence supports one shared intervention geometry strongly enough for a two-pillar main body.
- `Qwen-14B` remains important only as a bounded scale-compression check, not as a reason to reopen methods.

Decision:

- Launch `UNIFY-LIVE-FULL-R2` as a completion + integrity-lock + synthesis phase.
- Keep the shared abstract action space fixed:
  - `NO_INTERVENTION`
  - `LOCAL_REPAIR`
  - `GLOBAL_REWRITE_OR_RESTART`
- Keep the domain executors frozen:
  - math local repair -> `GRANITE_POSTPROCESS_ONLY_PATCH`
  - format local repair -> `solve_then_format`
- Freeze split seeds at:
  - `13`
  - `29`
  - `47`

Why:

- this directly answers the remaining main-paper question with fresh online evidence instead of another frozen re-analysis layer
- the strongest honest next move is to lock completed 7B evidence, not to invent another policy family
- the `Qwen-14B` cell should be either completed cleanly or explicitly left out; leaving it ambiguous is worse than either outcome

Effect:

- R2 will treat the existing `Qwen-7B` and `Mistral-7B` live banks as frozen fresh evidence that must pass a paper-safe integrity audit
- any `Qwen-14B` continuation will happen only under a clean `R2` run root and a bounded two-restart policy
- the final claim will center on the two-pillar math + output-constraint story even if the single pooled rule trails a domain-tuned rule on some harder boundary cells

## 2026-03-27 - Qwen-14B completion decision

Decision:

- Treat `/workspace/project/results/unify_live_full_r2_qwen14b/qwen14b_attempt2_20260326b` as the final `Qwen-14B` prospective bank for `UNIFY-LIVE-FULL-R2`.

Why:

- the corrected `8`-way + dual-slot path stayed stable through the resumed completion push
- the bank now reaches full target coverage on math raw, math replay, screened `IFEval`, and `IFBench`
- all `48` shard directories now carry `completed.txt`, so there is no longer any ambiguity about partial vs complete `14B` evidence

Effect:

- `Qwen-14B` is back in-scope for the prospective scale-compression read
- the R2 reports can now include a completed `14B` collection report and a prospective `14B` policy evaluation instead of an incomplete-attempt note
- the honest caveat remains that the recorded wall clock includes the earlier idle stall before resumption, so elapsed runtime and active high-util windows should be discussed separately
