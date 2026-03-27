# UNIFY-FULL Feature Audit

## Purpose

- This pack reuses frozen math and output-constraint traces to test whether both domains can share one abstract intervention geometry.
- No new local primitive was invented.
- Math local repair is frozen as the postprocess-centered replay primitive (`GRANITE_POSTPROCESS_ONLY_PATCH` in the replay traces).
- Format local repair is frozen as `solve_then_format`, the strongest already-supported format-side local executor from LACE-FULL.

## Shared Abstract Action Space

- `NO_INTERVENTION`: keep the direct answer.
- `LOCAL_REPAIR`: math -> postprocess-centered local patch; format -> solve-then-format.
- `GLOBAL_REWRITE_OR_RESTART`: math -> `self_refine_1`; format -> full rewrite.

## Shared Features

- `localized_failure_count`
- `repairable_local_signal`
- `final_stage_suspicion`
- `localized_enough`
- `surface_bucket`
- `shared_failure_bucket`

## Frozen Split Manifests

- `Qwen/Qwen2.5-7B-Instruct`: total `1579`, train `1001`, eval `578`.
- `mistralai/Mistral-7B-Instruct-v0.3`: total `1281`, train `827`, eval `454`.
- `Qwen/Qwen2.5-14B-Instruct`: total `1281`, train `849`, eval `432`.