# UNIFY-LIVE-FULL-R2 Feature Audit

## Purpose

- This pack locks the fresh prospective manifests, feature map, and shared action geometry for `UNIFY-LIVE-FULL-R2` before final paper-facing synthesis.
- The frozen math and format primitives are unchanged from the prior branches; only integrity locking, prospective policy evaluation, and synthesis are new here.

## Shared Abstract Action Space

- `NO_INTERVENTION`
- `LOCAL_REPAIR`
- `GLOBAL_REWRITE_OR_RESTART`

## Frozen Action Mapping

- math local repair: `GRANITE_POSTPROCESS_ONLY_PATCH replay over fresh math traces`
- format local repair: `solve_then_format`

## Shared Feature Map

- `localized_failure_count`
- `repairable_local_signal`
- `final_stage_suspicion`
- `localized_enough`
- `surface_bucket`
- `shared_failure_bucket`

## Split Stability Freeze

- split seeds: `13, 29, 47`
- split ratios: `train=0.50`, `calibration=0.15`, `eval=0.35`

## Frozen Full Prospective Surfaces

- `cluster-hard full`: `1515` examples, digest `0a33c810a3ff0bb1`, manifest `/workspace/project/results/unify_live_full_r2_shared/gsm8k_train_cluster_live_full.json`
  source: `/workspace/project/data/cass_r3_manifests_20260315a/gsm8k_train_cluster_main_r3_full1515.json`
- `generic-hard full`: `483` examples, digest `72f151981d216411`, manifest `/workspace/project/results/unify_live_full_r2_shared/gsm8k_train_generic_live_full.json`
  source: `/workspace/project/data/cass_r3_manifests_20260315a/gsm8k_train_generic_main_r3_full.json`
- `screened IFEval full`: `381` examples, digest `28eda2af30e9c0c3`, manifest `/workspace/project/results/unify_live_full_r2_shared/ifeval_screened_live_full.json`
  source: `/workspace/project/data/lace_full_format_manifests_20260324a/ifeval_screened_le150_381.json`
- `IFBench full`: `300` examples, digest `5214ed9492d1d61d`, manifest `/workspace/project/results/unify_live_full_r2_shared/ifbench_live_full.json`
  source: `/workspace/project/data/lace_full_format_manifests_20260324a/ifbench_main_300.json`