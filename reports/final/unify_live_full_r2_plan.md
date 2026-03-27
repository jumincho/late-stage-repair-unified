# UNIFY-LIVE-FULL-R2 Plan

## Scope

- `UNIFY-LIVE-FULL-R2` is a completion, integrity-lock, and synthesis phase over the already-collected fresh online banks.
- It is not a new methods branch.
- Prior math, format, and retrospective unification branches remain frozen evidence.
- The main paper question is whether hard math repair and validator-rich output-constraint repair can now be presented as two co-main empirical pillars of one shared late-stage requirement-realization intervention story on fresh prospective evidence.

## Frozen Starting Point

- Math is already locked as a main pillar from `CASS` through `CASS-R4`.
- The portable math-side local story is best read as postprocess/discretization-centered repair, with target-side edits more family- and scale-sensitive.
- Output-constraint tasks are already strong enough to plausibly serve as a second main pillar from `LACE-FULL`:
  - full screened `IFEval` is robustly positive
  - full `IFBench` is harder but directionally positive
  - simple portable rule families are the cleanest transfer story
- `UNIFY-FULL` already suggested that pooled simple rules can stay close to domain-specific rules, but the main evidence there was frozen-trace analysis.
- The current live progress state is:
  - `Qwen-7B` fresh prospective bank complete
  - `Mistral-7B` fresh prospective bank complete
  - `Qwen-14B` prospective bank incomplete and not claimable

## Fixed Domains And Surfaces

Math:

- cluster-hard
- generic-hard

Format:

- screened `IFEval`
- `IFBench`

## Shared Abstract Action Space

- `NO_INTERVENTION`
- `LOCAL_REPAIR`
- `GLOBAL_REWRITE_OR_RESTART`

## Frozen Action Mapping

Math:

- `NO_INTERVENTION` -> direct answer
- `LOCAL_REPAIR` -> frozen `GRANITE_POSTPROCESS_ONLY_PATCH` replay path
- `GLOBAL_REWRITE_OR_RESTART` -> frozen `self_refine_1`

Format:

- `NO_INTERVENTION` -> direct formatted answer
- `LOCAL_REPAIR` -> frozen `solve_then_format`
- `GLOBAL_REWRITE_OR_RESTART` -> frozen `full_rewrite_on_failure`

## Frozen Split And Feature Map

- split seeds: `13, 29, 47`
- split ratios: `train=0.50`, `calibration=0.15`, `eval=0.35`
- pooled shared feature columns:
  - `localized_failure_count`
  - `repairable_local_signal`
  - `final_stage_suspicion`
  - `localized_enough`
  - `surface_bucket`
  - `shared_failure_bucket`

## Required Comparisons

Baselines:

- `NO_INTERVENTION`
- `ALWAYS_LOCAL`
- `ALWAYS_REWRITE_OR_RESTART`
- `ORACLE_POLICY`

Domain-specific:

- `MATH_TUNED_SIMPLE_RULE`
- `FORMAT_TUNED_SIMPLE_RULE`
- `MATH_DOMAIN_LEARNED_GATE`
- `FORMAT_DOMAIN_LEARNED_GATE`

Unified:

- `POOLED_SIMPLE_2FEATURE`
- `POOLED_SIMPLE_3FEATURE`
- `POOLED_SIMPLE_THRESHOLDED_TREE`
- `POOLED_LEARNED_GATE`
- `POOLED_RULE_BEST`

## Registered Runtime Estimate Before Heavy Runs

- integrity audit + shard repair if needed: `1–3h`
- `Qwen-7B` policy fitting / evaluation: `2–4h`
- `Mistral-7B` policy fitting / evaluation: `2–4h`
- `Qwen-14B` full prospective completion: `14–24h`
- `Qwen-14B` policy fitting / evaluation: `2–4h`
- optional robustness reruns if needed: `2–4h`
- final synthesis / figures / memo: `2–4h`
- total expected end-to-end: `23–43h`

## Execution Policy

- local-first execution only
- `hf_local` remains first-class
- stable `Qwen-14B` path defaults to the already-validated local `4bit` route unless a clearly simpler stable local path is confirmed
- generation-heavy phases must use all `4` GPUs
- target sustained utilization during generation-heavy windows: `> 90%`
- validator-only phases may be CPU-bound
- if a generation-heavy phase remains below `80%` utilization for more than `10m`, stop and fix the runner before continuing

## Qwen-14B Completion Rule

- attempt to complete `Qwen-14B` prospectively only under a clean `R2` run root
- the current partial run is evidence only; it is not sufficient for a paper-facing conclusion
- if `Qwen-14B` remains unstable after `2` clean restart attempts:
  - stop
  - document the failure precisely
  - proceed with a 7B-centered main result

## Deliverables

- `/workspace/project/reports/unify_live_full_r2_plan.md`
- `/workspace/project/reports/unify_live_full_r2_feature_audit.md`
- `/workspace/project/reports/unify_live_full_r2_integrity_report.md`
- `/workspace/project/reports/unify_live_full_r2_qwen_report.md`
- `/workspace/project/reports/unify_live_full_r2_mistral_report.md`
- `/workspace/project/reports/unify_live_full_r2_qwen14b_collection_report.md`
- `/workspace/project/reports/unify_live_full_r2_qwen14b_report.md`
- `/workspace/project/reports/unify_live_full_r2_synthesis.md`
- `/workspace/project/reports/unify_live_full_r2_failure_notes.md`
- `/workspace/project/reports/unify_live_full_r2_summary_memo.md`
