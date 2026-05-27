# DART: Devil's-Advocate Reframing at Test-time

Inference-time research prototype for evaluating whether auditable hypothesis sets, adversarial defenses, structured rebuttals, and fresh-context regeneration improve reasoning accuracy over direct generation and selection-only baselines.

## Status

- Repo skeleton, configs, prompt templates, execution scripts, caching, evaluation, and reporting are implemented.
- `scripts/smoke_test.py` supports both `mock` mode and real OpenAI API mode.
- Main experiment scripts are resumable and write raw responses, parsed outputs, summaries, and figures to disk.

## Setup

```bash
cd /workspace/project
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Set environment variables in your shell:

```bash
export OPENAI_API_KEY=...
export HUGGINGFACE_HUB_TOKEN=...
export HF_TOKEN="$HUGGINGFACE_HUB_TOKEN"
```

Optional:

```bash
export DART_OPENAI_PRIMARY_MODEL=gpt-5-mini
export DART_OPENAI_CHEAP_MODEL=gpt-5-nano
```

## Execution order

1. Smoke test:

```bash
python scripts/smoke_test.py --client mock
python scripts/smoke_test.py --client openai --limit 2
```

2. Pilot run:

```bash
python scripts/pilot.py --client openai --datasets gsm8k strategyqa arc_challenge
```

3. Freeze prompts/configs by copying the pilot manifest from `results/pilot/...`.

4. Phase 2 non-pilot dev check:

```bash
python scripts/dev_check.py --client openai --limit 5 --offset 8 --output-dir results/devcheck/phase2_openai_dev_freeze
python scripts/analyze.py --input-dir results/devcheck/phase2_openai_dev_freeze
```

5. Held-out main run:

Single-process:

```bash
python scripts/heldout_main.py --client openai --limit 150 --offset 8
```

Recommended parallel-by-dataset pattern:

```bash
python -m dart_research.run_experiment --client openai --datasets strategyqa --methods direct_cot self_consistency_5 self_refine_1 mc_select_only_binary dart_adv_binary_fresh --limit 150 --offset 8 --output-dir results/main/<run_id>/strategyqa
python -m dart_research.run_experiment --client openai --datasets gsm8k --methods direct_cot self_consistency_5 self_refine_1 mc_select_only_shared_candidates dart_self dart_adv_fresh --limit 150 --offset 8 --output-dir results/main/<run_id>/gsm8k
python -m dart_research.run_experiment --client openai --datasets arc_challenge --methods direct_cot self_consistency_5 mc_select_only_human_options dart_human_defense_select dart_human_rebuttal_fresh --limit 150 --offset 8 --output-dir results/main/<run_id>/arc_challenge
python scripts/merge_run_dirs.py --parent-dir results/main/<run_id>
python scripts/analyze.py --input-dir results/main/<run_id>
```

6. Held-out ablations:

```bash
python scripts/heldout_ablations.py --client openai --limit 80 --offset 8
```

Recommended parallel-by-dataset pattern:

```bash
python -m dart_research.run_experiment --client openai --datasets strategyqa --methods direct_cot self_refine_1 adv_select_only_shared adv_rebuttal_then_select_shared adv_rebuttal_then_same_context_final adv_rebuttal_then_fresh_context_final dart_adv_binary_fresh --limit 80 --offset 8 --output-dir results/ablations/<run_id>/strategyqa
python -m dart_research.run_experiment --client openai --datasets gsm8k --methods direct_cot self_refine_1 adv_select_only_shared adv_rebuttal_then_select_shared adv_rebuttal_then_same_context_final adv_rebuttal_then_fresh_context_final dart_adv_fresh --limit 80 --offset 8 --output-dir results/ablations/<run_id>/gsm8k
python -m dart_research.run_experiment --client openai --datasets arc_challenge --methods direct_cot mc_select_only_human_options dart_human_defense_select dart_human_rebuttal_same dart_human_rebuttal_fresh --limit 80 --offset 8 --output-dir results/ablations/<run_id>/arc_challenge
python scripts/merge_run_dirs.py --parent-dir results/ablations/<run_id>
python scripts/analyze.py --input-dir results/ablations/<run_id>
```

7. Failure extraction and reports:

```bash
python scripts/extract_failure_cases.py --main-dir results/main/<run_id> --ablations-dir results/ablations/<run_id> --output-md reports/heldout_failure_notes.md
python scripts/make_heldout_report.py --main-dir results/main/<run_id> --ablations-dir results/ablations/<run_id> --output-report reports/heldout_main_report.md --positioning-report reports/submission_positioning.md --failure-notes reports/heldout_failure_notes.md
```

8. Phase 3 open-ended confirmation package:

Tiny new-data sanity:

```bash
python -m dart_research.run_experiment --client openai --datasets gsm8k --methods direct_cot self_refine_1 self_refine_2_budgetmatched adv_select_only_shared adv_rebuttal_then_select_shared dart_adv_same dart_adv_fresh freeform_devil_advocate_fresh --limit 5 --offset 158 --output-dir results/devcheck/phase3_openended_dev_freeze/gsm8k
python -m dart_research.run_experiment --client openai --datasets svamp --methods direct_cot self_refine_1 self_refine_2_budgetmatched adv_select_only_shared adv_rebuttal_then_select_shared dart_adv_same dart_adv_fresh freeform_devil_advocate_fresh --limit 5 --offset 0 --output-dir results/devcheck/phase3_openended_dev_freeze/svamp
python scripts/merge_run_dirs.py --parent-dir results/devcheck/phase3_openended_dev_freeze
python scripts/analyze_openended.py --input-dir results/devcheck/phase3_openended_dev_freeze
```

Main confirmatory run:

```bash
python -m dart_research.run_experiment --client openai --datasets gsm8k --methods direct_cot self_refine_1 self_refine_2_budgetmatched adv_select_only_shared adv_rebuttal_then_select_shared dart_adv_same dart_adv_fresh freeform_devil_advocate_fresh --limit 500 --offset 158 --output-dir results/confirm/<run_id>/gsm8k
python -m dart_research.run_experiment --client openai --datasets svamp --methods direct_cot self_refine_1 self_refine_2_budgetmatched adv_select_only_shared adv_rebuttal_then_select_shared dart_adv_same dart_adv_fresh freeform_devil_advocate_fresh --limit 300 --offset 0 --output-dir results/confirm/<run_id>/svamp
python scripts/merge_run_dirs.py --parent-dir results/confirm/<run_id>
python scripts/analyze_openended.py --input-dir results/confirm/<run_id>
python scripts/make_openended_confirmation_report.py --confirm-dir results/confirm/<run_id>
```

9. Phase 4 prospective v2 retest:

Tiny dev freeze:

```bash
python -m dart_research.run_experiment --client openai --datasets gsm8k --methods direct_cot self_refine_1 self_refine_2_budgetmatched freeform_devil_advocate_same freeform_devil_advocate_fresh dart_adv_same_v1 dart_adv_same_v2 adv_select_only_shared_v2 --limit 10 --offset 658 --output-dir results/v2_dev/gsm8k_dev_<run_id>
python -m dart_research.run_experiment --client openai --datasets multiarith --methods direct_cot self_refine_1 self_refine_2_budgetmatched freeform_devil_advocate_same freeform_devil_advocate_fresh dart_adv_same_v1 dart_adv_same_v2 adv_select_only_shared_v2 --limit 10 --offset 0 --output-dir results/v2_dev/multiarith_dev_<run_id>
python scripts/merge_run_dirs.py --parent-dir results/v2_dev/phase4_dev_<run_id> --child-dirs results/v2_dev/gsm8k_dev_<run_id> results/v2_dev/multiarith_dev_<run_id>
```

Prospective main retest, recommended sharded pattern:

```bash
python -m dart_research.run_experiment --client openai --datasets gsm8k --methods direct_cot self_refine_1 self_refine_2_budgetmatched freeform_devil_advocate_same freeform_devil_advocate_fresh dart_adv_same_v1 dart_adv_same_v2 adv_select_only_shared_v2 --limit 125 --offset 668 --output-dir results/v2_main/gsm8k_shard1_<run_id>
python -m dart_research.run_experiment --client openai --datasets gsm8k --methods direct_cot self_refine_1 self_refine_2_budgetmatched freeform_devil_advocate_same freeform_devil_advocate_fresh dart_adv_same_v1 dart_adv_same_v2 adv_select_only_shared_v2 --limit 125 --offset 793 --output-dir results/v2_main/gsm8k_shard2_<run_id>
python -m dart_research.run_experiment --client openai --datasets gsm8k --methods direct_cot self_refine_1 self_refine_2_budgetmatched freeform_devil_advocate_same freeform_devil_advocate_fresh dart_adv_same_v1 dart_adv_same_v2 adv_select_only_shared_v2 --limit 125 --offset 918 --output-dir results/v2_main/gsm8k_shard3_<run_id>
python -m dart_research.run_experiment --client openai --datasets gsm8k --methods direct_cot self_refine_1 self_refine_2_budgetmatched freeform_devil_advocate_same freeform_devil_advocate_fresh dart_adv_same_v1 dart_adv_same_v2 adv_select_only_shared_v2 --limit 125 --offset 1043 --output-dir results/v2_main/gsm8k_shard4_<run_id>
python -m dart_research.run_experiment --client openai --datasets multiarith --methods direct_cot self_refine_1 self_refine_2_budgetmatched freeform_devil_advocate_same freeform_devil_advocate_fresh dart_adv_same_v1 dart_adv_same_v2 adv_select_only_shared_v2 --limit 85 --offset 10 --output-dir results/v2_main/multiarith_shard1_<run_id>
python -m dart_research.run_experiment --client openai --datasets multiarith --methods direct_cot self_refine_1 self_refine_2_budgetmatched freeform_devil_advocate_same freeform_devil_advocate_fresh dart_adv_same_v1 dart_adv_same_v2 adv_select_only_shared_v2 --limit 85 --offset 95 --output-dir results/v2_main/multiarith_shard2_<run_id>
mkdir -p results/v2_main/gsm8k_main_<run_id>
mkdir -p results/v2_main/multiarith_main_<run_id>
python scripts/merge_run_dirs.py --parent-dir results/v2_main/gsm8k_main_<run_id> --child-dirs results/v2_main/gsm8k_shard1_<run_id> results/v2_main/gsm8k_shard2_<run_id> results/v2_main/gsm8k_shard3_<run_id> results/v2_main/gsm8k_shard4_<run_id>
python scripts/merge_run_dirs.py --parent-dir results/v2_main/multiarith_main_<run_id> --child-dirs results/v2_main/multiarith_shard1_<run_id> results/v2_main/multiarith_shard2_<run_id>
mkdir -p results/v2_main/phase4_main_<run_id>
python scripts/merge_run_dirs.py --parent-dir results/v2_main/phase4_main_<run_id> --child-dirs results/v2_main/gsm8k_main_<run_id> results/v2_main/multiarith_main_<run_id>
python scripts/make_phase4_integrated_report.py --dev-dir results/v2_dev/phase4_dev_<run_id> --main-dir results/v2_main/phase4_main_<run_id> --report-out reports/phase4_integrated_report.md --figure-dir figures
```

## Repo layout

```text
project/
  README.md
  research_log.md
  decision_log.md
  pyproject.toml
  .env.example
  prompts/
  configs/
  src/
  scripts/
  results/
  figures/
  reports/
  tests/
```

## Design highlights

- API-first, OpenAI Responses API primary backend
- Prompt templates versioned in files
- Disk cache for every request/response
- Fresh-context final generation for DART methods
- Offline evaluation only uses gold labels after inference
- Reproducible run manifests, sampled IDs, and parsed JSONL outputs

## Current recommendation

- After phase 4, the project should be positioned as a nuanced boundary-condition paper.
- The strongest support remains:
  - selection-only fails on open-ended arithmetic when coverage is incomplete
  - rebuttal + regeneration remains the key useful ingredient
- Phase 4 v2 improved candidate diversity, but it did not rescue a strong “auditable candidate sets are the key ingredient” claim.
- The detailed final narrative now lives in `reports/phase4_integrated_report.md`.

## EIR branch

EIR asks a new question:

- not whether to deliberate more
- not whether confidence or PRM should gate another round
- but which single corrective intervention is most executable on the current draft

### Tiny dev

```bash
python scripts/eir_collect_actionbank.py --dataset gsm8k_train --limit 12 --offset 800 --output-dir results/eir_dev/gsm8k_train_dev_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
python scripts/eir_collect_actionbank.py --dataset asdiv --limit 12 --offset 620 --output-dir results/eir_dev/asdiv_dev_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
```

### Calibration action bank

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/eir_collect_actionbank.py --dataset gsm8k_train --limit 50 --offset 820 --output-dir results/eir_actionbank/gsm8k_train_cal_shard1_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/eir_collect_actionbank.py --dataset gsm8k_train --limit 50 --offset 870 --output-dir results/eir_actionbank/gsm8k_train_cal_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/eir_collect_actionbank.py --dataset asdiv --limit 50 --offset 690 --output-dir results/eir_actionbank/asdiv_cal_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/eir_collect_actionbank.py --dataset asdiv --limit 50 --offset 740 --output-dir results/eir_actionbank/asdiv_cal_shard3_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/eir_collect_actionbank.py --dataset mawps --limit 40 --offset 0 --output-dir results/eir_actionbank/mawps_cal_shard1_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/eir_collect_actionbank.py --dataset mawps --limit 40 --offset 40 --output-dir results/eir_actionbank/mawps_cal_shard2_rerun_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
python scripts/eir_actionbank_report.py --input-dirs results/eir_actionbank/gsm8k_train_cal_shard1_20260312 results/eir_actionbank/gsm8k_train_cal_shard2_20260312 results/eir_actionbank/asdiv_cal_shard2_20260312 results/eir_actionbank/asdiv_cal_shard3_20260312 results/eir_actionbank/mawps_cal_shard1_20260312 results/eir_actionbank/mawps_cal_shard2_rerun_20260312 --output-dir results/eir_actionbank/mixed_calibration_20260312
python scripts/eir_offline_router.py --input-dirs results/eir_actionbank/gsm8k_train_cal_shard1_20260312 results/eir_actionbank/gsm8k_train_cal_shard2_20260312 results/eir_actionbank/asdiv_cal_shard2_20260312 results/eir_actionbank/asdiv_cal_shard3_20260312 results/eir_actionbank/mawps_cal_shard1_20260312 results/eir_actionbank/mawps_cal_shard2_rerun_20260312 --output-dir results/eir_offline/mixed_original_palette_20260312
```

### Fresh held-out main

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/eir_collect_actionbank.py --dataset gsm8k_train --limit 100 --offset 920 --output-dir results/eir_main/gsm8k_train_main_shard1_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/eir_collect_actionbank.py --dataset gsm8k_train --limit 100 --offset 1020 --output-dir results/eir_main/gsm8k_train_main_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/eir_collect_actionbank.py --dataset asdiv --limit 75 --offset 790 --output-dir results/eir_main/asdiv_main_shard1_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/eir_collect_actionbank.py --dataset asdiv --limit 75 --offset 865 --output-dir results/eir_main/asdiv_main_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/eir_collect_actionbank.py --dataset mawps --limit 60 --offset 80 --output-dir results/eir_main/mawps_main_shard1_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/eir_collect_actionbank.py --dataset mawps --limit 60 --offset 140 --output-dir results/eir_main/mawps_main_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
python scripts/eir_main.py --calibration-dirs results/eir_actionbank/gsm8k_train_cal_shard1_20260312 results/eir_actionbank/gsm8k_train_cal_shard2_20260312 results/eir_actionbank/asdiv_cal_shard2_20260312 results/eir_actionbank/asdiv_cal_shard3_20260312 results/eir_actionbank/mawps_cal_shard1_20260312 results/eir_actionbank/mawps_cal_shard2_rerun_20260312 --main-dirs results/eir_main/gsm8k_train_main_shard1_20260312 results/eir_main/gsm8k_train_main_shard2_20260312 results/eir_main/asdiv_main_shard1_20260312 results/eir_main/asdiv_main_shard2_20260312 results/eir_main/mawps_main_shard1_20260312 results/eir_main/mawps_main_shard2_20260312 --output-dir results/eir_main/eir_main_eval_20260312
python scripts/make_eir_reports.py --actionbank-dir results/eir_actionbank/mixed_calibration_20260312 --offline-dir results/eir_offline/mixed_original_palette_20260312 --main-dir results/eir_main/eir_main_eval_20260312 --main-raw-dirs results/eir_main/gsm8k_train_main_shard1_20260312 results/eir_main/gsm8k_train_main_shard2_20260312 results/eir_main/asdiv_main_shard1_20260312 results/eir_main/asdiv_main_shard2_20260312 results/eir_main/mawps_main_shard1_20260312 results/eir_main/mawps_main_shard2_20260312 --report-dir reports --table-dir tables/eir --figure-dir figures/eir
```

### EIR status

- The strongest surviving EIR result is:
  - full EIR beats relevance-only routing very clearly
  - full EIR is best on the easy arithmetic set
- The strongest unsupported EIR result is:
  - full EIR beats the strongest hard-set fixed executable action
- See:
  - `reports/eir_main_report.md`
  - `reports/eir_actionbank_report.md`
  - `reports/eir_offline_router_report.md`

## Phase 5 local open-model commands

Local backend setup:

```bash
pip install -e ".[dev,local]"
```

Tiny local dev checks used in phase 5:

```bash
python -m dart_research.run_experiment --client hf_local --datasets gsm8k --methods direct_cot self_refine_1 freeform_devil_advocate_same adv_select_only_shared dart_adv_same_v1 --limit 1 --offset 1168 --output-dir results/openmodel_dev/qwen0p5b_full_dev_gsm8k_v5 --model-name Qwen/Qwen2.5-0.5B-Instruct --primary-max-output-tokens 220 --cheap-max-output-tokens 180 --validator-max-output-tokens 180 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
python -m dart_research.run_experiment --client hf_local --datasets svamp --methods direct_cot self_refine_1 freeform_devil_advocate_same adv_select_only_shared dart_adv_same_v1 --limit 1 --offset 0 --output-dir results/openmodel_dev/qwen1p5b_full_dev_svamp_v1 --model-name Qwen/Qwen2.5-1.5B-Instruct --primary-max-output-tokens 220 --cheap-max-output-tokens 180 --validator-max-output-tokens 180 --local-quantization 4bit --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
```

Tiny clean phase-5 local main subset:

```bash
python -m dart_research.run_experiment --client hf_local --datasets gsm8k --methods direct_cot self_refine_1 freeform_devil_advocate_same adv_select_only_shared dart_adv_same_v1 --limit 3 --offset 1168 --output-dir results/openmodel_main/qwen0p5b_gsm8k3_20260310 --model-name Qwen/Qwen2.5-0.5B-Instruct --primary-max-output-tokens 220 --cheap-max-output-tokens 180 --validator-max-output-tokens 180 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
python -m dart_research.run_experiment --client hf_local --datasets svamp --methods direct_cot self_refine_1 freeform_devil_advocate_same adv_select_only_shared dart_adv_same_v1 --limit 3 --offset 0 --output-dir results/openmodel_main/qwen0p5b_svamp3_20260310 --model-name Qwen/Qwen2.5-0.5B-Instruct --primary-max-output-tokens 220 --cheap-max-output-tokens 180 --validator-max-output-tokens 180 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
python -m dart_research.run_experiment --client hf_local --datasets gsm8k --methods direct_cot self_refine_1 freeform_devil_advocate_same adv_select_only_shared dart_adv_same_v1 --limit 3 --offset 1168 --output-dir results/openmodel_main/qwen1p5b_gsm8k3_20260310 --model-name Qwen/Qwen2.5-1.5B-Instruct --primary-max-output-tokens 220 --cheap-max-output-tokens 180 --validator-max-output-tokens 180 --local-quantization 4bit --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
python -m dart_research.run_experiment --client hf_local --datasets svamp --methods direct_cot self_refine_1 freeform_devil_advocate_same adv_select_only_shared dart_adv_same_v1 --limit 3 --offset 0 --output-dir results/openmodel_main/qwen1p5b_svamp3_20260310 --model-name Qwen/Qwen2.5-1.5B-Instruct --primary-max-output-tokens 220 --cheap-max-output-tokens 180 --validator-max-output-tokens 180 --local-quantization 4bit --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
mkdir -p results/openmodel_main/phase5_openmodel_20260310
python scripts/merge_run_dirs.py --parent-dir results/openmodel_main/phase5_openmodel_20260310 --child-dirs results/openmodel_main/qwen0p5b_gsm8k3_20260310 results/openmodel_main/qwen0p5b_svamp3_20260310 results/openmodel_main/qwen1p5b_gsm8k3_20260310 results/openmodel_main/qwen1p5b_svamp3_20260310
```

Phase 5 conclusion:

- The local open-model retest did not materially strengthen the paper.
- The current recommendation remains: stop and submit the nuanced boundary-condition paper.

## CHASE confidence branch

This branch keeps the DART results frozen and asks a new question:

- can challenge-conditioned confidence control when to stop, continue, or abstain during freeform devil's-advocate deliberation on open-ended arithmetic?

Primary branch model:

- `Qwen/Qwen2.5-7B-Instruct`

Secondary small replication model:

- `Qwen/Qwen2.5-Math-7B-Instruct`

Tiny dev freeze:

```bash
source /workspace/project/.env.example
export HF_TOKEN="$HUGGINGFACE_HUB_TOKEN"

CUDA_VISIBLE_DEVICES=0 python scripts/chase_collect_traces.py \
  --dataset gsm8k_train \
  --limit 5 \
  --offset 0 \
  --output-dir results/confidence_dev/qwen7b_gsm8k_dev_20260311 \
  --model-name Qwen/Qwen2.5-7B-Instruct \
  --include-vc100 \
  --local-quantization 4bit \
  --local-device-map auto \
  --local-trust-remote-code

CUDA_VISIBLE_DEVICES=1 python scripts/chase_collect_traces.py \
  --dataset asdiv \
  --limit 5 \
  --offset 0 \
  --output-dir results/confidence_dev/qwen7b_asdiv_dev_20260311 \
  --model-name Qwen/Qwen2.5-7B-Instruct \
  --include-vc100 \
  --local-quantization 4bit \
  --local-device-map auto \
  --local-trust-remote-code
```

Primary trace collection:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/chase_collect_traces.py --dataset gsm8k_train --limit 60 --offset 20  --output-dir results/confidence_traces/qwen7b_cal_gsm8k_shard1_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-device-map auto --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/chase_collect_traces.py --dataset gsm8k_train --limit 60 --offset 80  --output-dir results/confidence_traces/qwen7b_cal_gsm8k_shard2_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-device-map auto --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/chase_collect_traces.py --dataset gsm8k_train --limit 80 --offset 140 --output-dir results/confidence_traces/qwen7b_eval_gsm8k_shard1_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-device-map auto --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/chase_collect_traces.py --dataset gsm8k_train --limit 80 --offset 220 --output-dir results/confidence_traces/qwen7b_eval_gsm8k_shard2_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-device-map auto --local-trust-remote-code

CUDA_VISIBLE_DEVICES=0 python scripts/chase_collect_traces.py --dataset asdiv --limit 50 --offset 20  --output-dir results/confidence_traces/qwen7b_cal_asdiv_shard1_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-device-map auto --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/chase_collect_traces.py --dataset asdiv --limit 50 --offset 70  --output-dir results/confidence_traces/qwen7b_cal_asdiv_shard2_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-device-map auto --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/chase_collect_traces.py --dataset asdiv --limit 50 --offset 120 --output-dir results/confidence_traces/qwen7b_eval_asdiv_shard1_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-device-map auto --local-trust-remote-code
CUDA_VISIBLE_DEVICES=0 python scripts/chase_collect_traces.py --dataset asdiv --limit 50 --offset 170 --output-dir results/confidence_traces/qwen7b_eval_asdiv_shard2_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-device-map auto --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/chase_collect_traces.py --dataset asdiv --limit 50 --offset 220 --output-dir results/confidence_traces/qwen7b_eval_asdiv_shard3_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-device-map auto --local-trust-remote-code
```

Benchmark + main evaluation:

```bash
python scripts/chase_benchmark.py \
  --calibration-traces \
    results/confidence_traces/qwen7b_cal_gsm8k_shard1_20260311 \
    results/confidence_traces/qwen7b_cal_gsm8k_shard2_20260311 \
    results/confidence_traces/qwen7b_cal_asdiv_shard1_20260311 \
    results/confidence_traces/qwen7b_cal_asdiv_shard2_20260311 \
  --eval-traces \
    results/confidence_traces/qwen7b_eval_gsm8k_shard1_20260311 \
    results/confidence_traces/qwen7b_eval_gsm8k_shard2_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard1_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard2_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard3_20260311 \
  --output-dir results/confidence_main/qwen7b_combined_benchmark_20260311

python scripts/chase_main.py \
  --trace-dirs \
    results/confidence_traces/qwen7b_eval_gsm8k_shard1_20260311 \
    results/confidence_traces/qwen7b_eval_gsm8k_shard2_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard1_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard2_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard3_20260311 \
  --calibrator-path results/confidence_main/qwen7b_combined_benchmark_20260311/calibrator.json \
  --output-dir results/confidence_main/qwen7b_combined_main_20260311

python scripts/make_chase_reports.py \
  --trace-dirs \
    results/confidence_traces/qwen7b_eval_gsm8k_shard1_20260311 \
    results/confidence_traces/qwen7b_eval_gsm8k_shard2_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard1_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard2_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard3_20260311 \
  --benchmark-dir results/confidence_main/qwen7b_combined_benchmark_20260311 \
  --main-dir results/confidence_main/qwen7b_combined_main_20260311 \
  --extra-summary-csvs results/confidence_main/math7b_gsm8k_main_20260311/summary.csv \
  --report-dir reports/chase_qwen7b_20260311 \
  --figure-dir figures/chase_qwen7b_20260311
```

Secondary small replication:

```bash
CUDA_VISIBLE_DEVICES=2 python scripts/chase_collect_traces.py --dataset gsm8k_train --limit 20 --offset 320 --output-dir results/confidence_traces/math7b_cal_gsm8k_20260311 --model-name Qwen/Qwen2.5-Math-7B-Instruct --local-quantization 4bit --local-device-map auto --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/chase_collect_traces.py --dataset gsm8k_train --limit 20 --offset 340 --output-dir results/confidence_traces/math7b_eval_gsm8k_20260311 --model-name Qwen/Qwen2.5-Math-7B-Instruct --local-quantization 4bit --local-device-map auto --local-trust-remote-code
python scripts/chase_benchmark.py --calibration-traces results/confidence_traces/math7b_cal_gsm8k_20260311 --eval-traces results/confidence_traces/math7b_eval_gsm8k_20260311 --output-dir results/confidence_main/math7b_gsm8k_benchmark_20260311
python scripts/chase_main.py --trace-dirs results/confidence_traces/math7b_eval_gsm8k_20260311 --calibrator-path results/confidence_main/math7b_gsm8k_benchmark_20260311/calibrator.json --output-dir results/confidence_main/math7b_gsm8k_main_20260311
```

4GPU larger-local rerun after the tiny-model phase 5:

```bash
CUDA_VISIBLE_DEVICES=0,1 python -m dart_research.run_experiment --client hf_local --datasets gsm8k --methods direct_cot self_refine_1 freeform_devil_advocate_same adv_select_only_shared dart_adv_same_v1 --limit 10 --offset 658 --output-dir results/openmodel_main/qwen25_7b_gsm8k10_4gpu_rerun_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --primary-max-output-tokens 220 --cheap-max-output-tokens 180 --validator-max-output-tokens 180 --local-quantization 4bit --local-device-map auto --local-max-memory 10GiB,10GiB --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2,3 python -m dart_research.run_experiment --client hf_local --datasets svamp --methods direct_cot self_refine_1 freeform_devil_advocate_same adv_select_only_shared dart_adv_same_v1 --limit 10 --offset 0 --output-dir results/openmodel_main/qwen25_7b_svamp10_4gpu_rerun_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --primary-max-output-tokens 220 --cheap-max-output-tokens 180 --validator-max-output-tokens 180 --local-quantization 4bit --local-device-map auto --local-max-memory 10GiB,10GiB --local-max-model-len 4096 --local-trust-remote-code
mkdir -p results/openmodel_main/qwen25_7b_4gpu_rerun_20260311_merged
python scripts/merge_run_dirs.py --parent-dir results/openmodel_main/qwen25_7b_4gpu_rerun_20260311_merged --child-dirs results/openmodel_main/qwen25_7b_gsm8k10_4gpu_rerun_20260311 results/openmodel_main/qwen25_7b_svamp10_4gpu_rerun_20260311
```

4GPU rerun conclusion:

- This rerun is more informative than the original `0.5B/1.5B` local phase because `Qwen2.5-7B-Instruct` is no longer entirely floor-limited.
- `svamp`: `dart_adv_same_v1 = 0.30` vs `adv_select_only_shared = 0.10`, and under coverage=`0`, DART solved `2/9` while selection-only solved `0/9`.
- `gsm8k`: `dart_adv_same_v1 = 0.30`, tied with `adv_select_only_shared = 0.30`.
- `freeform_devil_advocate_same` remained stronger than DART on both rerun slices, so the rerun still does not rescue the stronger auditable-candidate-set claim.

4GPU high-util long run:

```bash
CUDA_VISIBLE_DEVICES=0 python -m dart_research.run_experiment --client hf_local --datasets gsm8k --methods direct_cot self_refine_1 freeform_devil_advocate_same adv_select_only_shared dart_adv_same_v1 --limit 50 --offset 668 --output-dir results/openmodel_main/qwen25_7b_fp16_gsm8k50a_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --primary-max-output-tokens 220 --cheap-max-output-tokens 180 --validator-max-output-tokens 180 --local-quantization none --local-device-map auto --local-max-memory 20GiB --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python -m dart_research.run_experiment --client hf_local --datasets gsm8k --methods direct_cot self_refine_1 freeform_devil_advocate_same adv_select_only_shared dart_adv_same_v1 --limit 50 --offset 718 --output-dir results/openmodel_main/qwen25_7b_fp16_gsm8k50b_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --primary-max-output-tokens 220 --cheap-max-output-tokens 180 --validator-max-output-tokens 180 --local-quantization none --local-device-map auto --local-max-memory 20GiB --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python -m dart_research.run_experiment --client hf_local --datasets svamp --methods direct_cot self_refine_1 freeform_devil_advocate_same adv_select_only_shared dart_adv_same_v1 --limit 50 --offset 100 --output-dir results/openmodel_main/qwen25_7b_fp16_svamp50_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --primary-max-output-tokens 220 --cheap-max-output-tokens 180 --validator-max-output-tokens 180 --local-quantization none --local-device-map auto --local-max-memory 20GiB --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python -m dart_research.run_experiment --client hf_local --datasets multiarith --methods direct_cot self_refine_1 freeform_devil_advocate_same adv_select_only_shared dart_adv_same_v1 --limit 50 --offset 0 --output-dir results/openmodel_main/qwen25_7b_fp16_multiarith50_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --primary-max-output-tokens 220 --cheap-max-output-tokens 180 --validator-max-output-tokens 180 --local-quantization none --local-device-map auto --local-max-memory 20GiB --local-max-model-len 4096 --local-trust-remote-code
mkdir -p results/openmodel_main/qwen25_7b_fp16_4gpu_longrun_20260311
python scripts/merge_run_dirs.py --parent-dir results/openmodel_main/qwen25_7b_fp16_4gpu_longrun_20260311 --child-dirs results/openmodel_main/qwen25_7b_fp16_gsm8k50a_20260311 results/openmodel_main/qwen25_7b_fp16_gsm8k50b_20260311 results/openmodel_main/qwen25_7b_fp16_svamp50_20260311 results/openmodel_main/qwen25_7b_fp16_multiarith50_20260311
```

High-util long-run conclusion:

- `200` questions, `1000` records total.
- Sustained utilization snapshots during the run were roughly `72-95%` and later `84-94%` across all four GPUs.
- `gsm8k`: `dart_adv_same_v1 = 0.17` vs `adv_select_only_shared = 0.13`; under coverage=`0`, DART solved `3/70` while selection-only solved `0/70`.
- `multiarith`: `dart_adv_same_v1 = 0.54` vs `adv_select_only_shared = 0.50`; under coverage=`0`, DART solved `1/17` while selection-only solved `0/17`.
- `svamp`: `dart_adv_same_v1 = 0.64`, tied with `adv_select_only_shared = 0.64`.
- `freeform_devil_advocate_same` remained strongest on all three datasets, so even this longer 4GPU run does not rescue the stronger auditable-candidate-set claim.

## V-CHASE verifier branch

This branch keeps DART and CHASE frozen and asks a narrower question:

- can verifier-like local signals improve same-context challenge control on hard arithmetic
- especially by separating:
  - stop now
  - continue because one more round is likely helpful
  - stop because one more round is likely harmful

Primary local generator:

- `Qwen/Qwen2.5-7B-Instruct`

Primary local verifier:

- `Qwen/Qwen2.5-Math-PRM-7B`

### V-CHASE offline reuse on existing CHASE traces

Old held-out signal benchmark without PRM:

```bash
python scripts/vchase_signal_benchmark.py \
  --calibration-traces \
    results/confidence_traces/qwen7b_cal_gsm8k_shard1_20260311 \
    results/confidence_traces/qwen7b_cal_gsm8k_shard2_20260311 \
    results/confidence_traces/qwen7b_cal_asdiv_shard1_20260311 \
    results/confidence_traces/qwen7b_cal_asdiv_shard2_20260311 \
  --eval-traces \
    results/confidence_traces/qwen7b_eval_gsm8k_shard1_20260311 \
    results/confidence_traces/qwen7b_eval_gsm8k_shard2_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard1_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard2_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard3_20260311 \
  --output-dir results/vchase_signal/v0_noprm_20260311 \
  --disable-prm

python scripts/vchase_headroom.py \
  --trace-dirs \
    results/confidence_traces/qwen7b_eval_gsm8k_shard1_20260311 \
    results/confidence_traces/qwen7b_eval_gsm8k_shard2_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard1_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard2_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard3_20260311 \
  --stage-csv results/vchase_signal/v0_noprm_20260311/eval_stage_features.csv \
  --chase-calibrator-path results/confidence_main/qwen7b_combined_benchmark_20260311/calibrator.json \
  --output-dir results/vchase_headroom/v0_noprm_20260311

python scripts/vchase_main.py \
  --calibration-stage-csv results/vchase_signal/v0_noprm_20260311/calibration_stage_features.csv \
  --eval-stage-csv results/vchase_signal/v0_noprm_20260311/eval_stage_features.csv \
  --eval-trace-dirs \
    results/confidence_traces/qwen7b_eval_gsm8k_shard1_20260311 \
    results/confidence_traces/qwen7b_eval_gsm8k_shard2_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard1_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard2_20260311 \
    results/confidence_traces/qwen7b_eval_asdiv_shard3_20260311 \
  --chase-calibrator-path results/confidence_main/qwen7b_combined_benchmark_20260311/calibrator.json \
  --output-dir results/vchase_main/v0_noprm_replay_20260311
```

### V-CHASE fresh prospective trace collection

Calibration:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/chase_collect_traces.py --dataset gsm8k_train --limit 60 --offset 300 --output-dir results/vchase_main/qwen7b_cal_gsm8k_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/chase_collect_traces.py --dataset asdiv       --limit 40 --offset 270 --output-dir results/vchase_main/qwen7b_cal_asdiv_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/chase_collect_traces.py --dataset svamp       --limit 40 --offset 0   --output-dir results/vchase_main/qwen7b_cal_svamp_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
```

Held-out evaluation:

```bash
CUDA_VISIBLE_DEVICES=1 python scripts/chase_collect_traces.py --dataset gsm8k_train --limit 75 --offset 400 --output-dir results/vchase_main/qwen7b_eval_gsm8k_shard1_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/chase_collect_traces.py --dataset gsm8k_train --limit 75 --offset 475 --output-dir results/vchase_main/qwen7b_eval_gsm8k_shard2_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/chase_collect_traces.py --dataset asdiv       --limit 75 --offset 320 --output-dir results/vchase_main/qwen7b_eval_asdiv_shard1_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=0 python scripts/chase_collect_traces.py --dataset asdiv       --limit 75 --offset 395 --output-dir results/vchase_main/qwen7b_eval_asdiv_shard2_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/chase_collect_traces.py --dataset svamp       --limit 60 --offset 50  --output-dir results/vchase_main/qwen7b_eval_svamp_shard1_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/chase_collect_traces.py --dataset svamp       --limit 60 --offset 110 --output-dir results/vchase_main/qwen7b_eval_svamp_shard2_20260311 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
```

Fresh no-PRM benchmark + main replay:

```bash
python scripts/vchase_signal_benchmark.py \
  --calibration-traces \
    results/vchase_main/qwen7b_cal_gsm8k_20260311 \
    results/vchase_main/qwen7b_cal_asdiv_20260311 \
    results/vchase_main/qwen7b_cal_svamp_20260311 \
  --eval-traces \
    results/vchase_main/qwen7b_eval_gsm8k_shard1_20260311 \
    results/vchase_main/qwen7b_eval_gsm8k_shard2_20260311 \
    results/vchase_main/qwen7b_eval_asdiv_shard1_20260311 \
    results/vchase_main/qwen7b_eval_asdiv_shard2_20260311 \
    results/vchase_main/qwen7b_eval_svamp_shard1_20260311 \
    results/vchase_main/qwen7b_eval_svamp_shard2_20260311 \
  --output-dir results/vchase_signal/fresh_noprm_20260311 \
  --disable-prm

python scripts/vchase_main.py \
  --calibration-stage-csv results/vchase_signal/fresh_noprm_20260311/calibration_stage_features.csv \
  --eval-stage-csv results/vchase_signal/fresh_noprm_20260311/eval_stage_features.csv \
  --eval-trace-dirs \
    results/vchase_main/qwen7b_eval_gsm8k_shard1_20260311 \
    results/vchase_main/qwen7b_eval_gsm8k_shard2_20260311 \
    results/vchase_main/qwen7b_eval_asdiv_shard1_20260311 \
    results/vchase_main/qwen7b_eval_asdiv_shard2_20260311 \
    results/vchase_main/qwen7b_eval_svamp_shard1_20260311 \
    results/vchase_main/qwen7b_eval_svamp_shard2_20260311 \
  --chase-calibrator-path results/confidence_main/qwen7b_combined_benchmark_20260311/calibrator.json \
  --output-dir results/vchase_main/fresh_noprm_replay_20260311
```

### V-CHASE GSM8K PRM hard-set retest

```bash
CUDA_VISIBLE_DEVICES=2 python scripts/vchase_signal_benchmark.py \
  --calibration-traces results/vchase_main/qwen7b_cal_gsm8k_20260311 \
  --eval-traces results/vchase_main/qwen7b_eval_gsm8k_shard1_20260311 results/vchase_main/qwen7b_eval_gsm8k_shard2_20260311 \
  --output-dir results/vchase_signal/gsm8k_prm_20260311 \
  --prm-model Qwen/Qwen2.5-Math-PRM-7B \
  --prm-dtype float16 \
  --prm-device-map auto

python scripts/vchase_main.py \
  --calibration-stage-csv results/vchase_signal/gsm8k_prm_20260311/calibration_stage_features.csv \
  --eval-stage-csv results/vchase_signal/gsm8k_prm_20260311/eval_stage_features.csv \
  --eval-trace-dirs results/vchase_main/qwen7b_eval_gsm8k_shard1_20260311 results/vchase_main/qwen7b_eval_gsm8k_shard2_20260311 \
  --chase-calibrator-path results/confidence_main/qwen7b_combined_benchmark_20260311/calibrator.json \
  --output-dir results/vchase_main/gsm8k_prm_replay_20260311
```

Report generation:

```bash
python scripts/make_vchase_reports.py \
  --old-signal-dir results/vchase_signal/v0_noprm_20260311 \
  --headroom-dir results/vchase_headroom/v0_noprm_20260311 \
  --fresh-signal-dir results/vchase_signal/fresh_noprm_20260311 \
  --fresh-main-dir results/vchase_main/fresh_noprm_replay_20260311 \
  --gsm8k-prm-signal-dir results/vchase_signal/gsm8k_prm_20260311 \
  --gsm8k-prm-main-dir results/vchase_main/gsm8k_prm_replay_20260311 \
  --fresh-trace-dirs \
    results/vchase_main/qwen7b_eval_gsm8k_shard1_20260311 \
    results/vchase_main/qwen7b_eval_gsm8k_shard2_20260311 \
    results/vchase_main/qwen7b_eval_asdiv_shard1_20260311 \
    results/vchase_main/qwen7b_eval_asdiv_shard2_20260311 \
    results/vchase_main/qwen7b_eval_svamp_shard1_20260311 \
    results/vchase_main/qwen7b_eval_svamp_shard2_20260311 \
  --report-dir reports \
  --figure-dir figures
```

### V-CHASE conclusion

- Old-trace offline headroom justified the branch.
- Fresh no-PRM verifier features improved controller quality, but the dual-head controller was only clearly positive on `asdiv` and mixed on `gsm8k_train` / `svamp`.
- The bounded PRM add-on on fresh `gsm8k_train` changed the hard-set result materially:
  - `CHASE_calibrated = 0.3600`
  - `robust_rule_gate = 0.3800`
  - `VCHASE_dualhead = 0.4733`
- Current recommendation:
  - keep V-CHASE as a promising verifier-aware follow-up branch
  - do not claim universal transfer or PRM-as-judge

### VCHASE-R2 bounded follow-up

Offline trace-reuse ablation:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/vchase_r2_offline.py \
  --calibration-traces \
    results/vchase_main/qwen7b_cal_gsm8k_20260311 \
    results/vchase_main/qwen7b_cal_asdiv_20260311 \
    results/vchase_main/qwen7b_cal_svamp_20260311 \
  --eval-traces \
    results/vchase_main/qwen7b_eval_gsm8k_shard1_20260311 \
    results/vchase_main/qwen7b_eval_gsm8k_shard2_20260311 \
    results/vchase_main/qwen7b_eval_asdiv_shard1_20260311 \
    results/vchase_main/qwen7b_eval_asdiv_shard2_20260311 \
    results/vchase_main/qwen7b_eval_svamp_shard1_20260311 \
    results/vchase_main/qwen7b_eval_svamp_shard2_20260311 \
  --chase-calibrator-path results/confidence_main/qwen7b_combined_benchmark_20260311/calibrator.json \
  --output-dir results/vchase_r2_offline/trace_reuse_prm_hardfit_20260312
```

Fresh local replication trace collection:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/chase_collect_traces.py --dataset gsm8k_train --limit 100 --offset 550 --output-dir results/vchase_r2_main/qwen7b_eval_gsm8k_r2_shard1_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/chase_collect_traces.py --dataset gsm8k_train --limit 100 --offset 650 --output-dir results/vchase_r2_main/qwen7b_eval_gsm8k_r2_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/chase_collect_traces.py --dataset asdiv --limit 75 --offset 470 --output-dir results/vchase_r2_main/qwen7b_eval_asdiv_r2_shard1_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/chase_collect_traces.py --dataset asdiv --limit 75 --offset 545 --output-dir results/vchase_r2_main/qwen7b_eval_asdiv_r2_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/chase_collect_traces.py --dataset svamp --limit 65 --offset 170 --output-dir results/vchase_r2_main/qwen7b_eval_svamp_r2_shard1_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/chase_collect_traces.py --dataset svamp --limit 65 --offset 235 --output-dir results/vchase_r2_main/qwen7b_eval_svamp_r2_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --max-rounds 2 --dispersion-samples 2 --max-output-tokens 160 --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
```

Fresh main replay:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/vchase_r2_main.py \
  --eval-traces \
    results/vchase_r2_main/qwen7b_eval_gsm8k_r2_shard1_20260312 \
    results/vchase_r2_main/qwen7b_eval_gsm8k_r2_shard2_20260312 \
    results/vchase_r2_main/qwen7b_eval_asdiv_r2_shard1_20260312 \
    results/vchase_r2_main/qwen7b_eval_asdiv_r2_shard2_20260312 \
    results/vchase_r2_main/qwen7b_eval_svamp_r2_shard1_20260312 \
    results/vchase_r2_main/qwen7b_eval_svamp_r2_shard2_20260312 \
  --offline-dir results/vchase_r2_offline/trace_reuse_prm_hardfit_20260312 \
  --chase-calibrator-path results/confidence_main/qwen7b_combined_benchmark_20260311/calibrator.json \
  --output-dir results/vchase_r2_main/main_replay_20260312

python scripts/make_vchase_r2_reports.py \
  --offline-dir results/vchase_r2_offline/trace_reuse_prm_hardfit_20260312 \
  --main-dir results/vchase_r2_main/main_replay_20260312 \
  --trace-dirs \
    results/vchase_r2_main/qwen7b_eval_gsm8k_r2_shard1_20260312 \
    results/vchase_r2_main/qwen7b_eval_gsm8k_r2_shard2_20260312 \
    results/vchase_r2_main/qwen7b_eval_asdiv_r2_shard1_20260312 \
    results/vchase_r2_main/qwen7b_eval_asdiv_r2_shard2_20260312 \
    results/vchase_r2_main/qwen7b_eval_svamp_r2_shard1_20260312 \
    results/vchase_r2_main/qwen7b_eval_svamp_r2_shard2_20260312
```

VCHASE-R2 conclusion:

- Fresh hard-set replication stayed directionally positive:
  - `gsm8k_train`
    - `CHASE_calibrated = 0.4750`
    - `VCHASE_dualhead_PRM_hardopt = 0.4900`
- But the mechanism story weakened:
  - `VCHASE_dualhead_noPRM = 0.4900`
  - `VCHASE_singlehead_PRM = 0.5000`
  - `verifier_rule_gate = 0.5100`
- Current recommendation:
  - keep V-CHASE / VCHASE-R2 as a narrow positive controller-family result
  - do not claim PRM is the essential ingredient
  - do not claim dual-head is the essential ingredient

## HEIR commands

HEIR uses the pruned executable palette:

- `STOP`
- `PYTHON_RECOMPUTE`
- `LOCALIZE_BACKTRACK`
- `FREEFORM_CRITIQUE`

### Oracle geometry + transfer screen

```bash
python scripts/heir_oracle_geometry.py --input-dirs results/eir_actionbank/gsm8k_train_cal_shard1_20260312 results/eir_actionbank/gsm8k_train_cal_shard2_20260312 results/eir_actionbank/asdiv_cal_shard2_20260312 results/eir_actionbank/asdiv_cal_shard3_20260312 results/eir_actionbank/mawps_cal_shard1_20260312 results/eir_actionbank/mawps_cal_shard2_rerun_20260312 --output-dir results/heir_oracle_geometry/initial_20260312
python scripts/heir_transfer_screen.py --datasets multiarith mawps gsm8k --limit 20 --offsets multiarith:80 mawps:300 gsm8k:700 --model-name Qwen/Qwen2.5-7B-Instruct --output-dir results/heir_transfer_screen/screen_20260312 --disable-prm
```

### Calibration + offline

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/heir_collect_actionbank.py --dataset gsm8k_train --limit 60 --offset 1200 --output-dir results/heir_calibration/gsm8k_train_cal_shard1_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
CUDA_VISIBLE_DEVICES=1 python scripts/heir_collect_actionbank.py --dataset gsm8k_train --limit 60 --offset 1260 --output-dir results/heir_calibration/gsm8k_train_cal_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
CUDA_VISIBLE_DEVICES=2 python scripts/heir_collect_actionbank.py --dataset asdiv --limit 50 --offset 940 --output-dir results/heir_calibration/asdiv_cal_shard1_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
CUDA_VISIBLE_DEVICES=3 python scripts/heir_collect_actionbank.py --dataset asdiv --limit 50 --offset 990 --output-dir results/heir_calibration/asdiv_cal_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
python scripts/heir_offline.py --calibration-dirs results/heir_calibration/gsm8k_train_cal_shard1_20260312 results/heir_calibration/gsm8k_train_cal_shard2_20260312 results/heir_calibration/asdiv_cal_shard1_20260312 results/heir_calibration/asdiv_cal_shard2_20260312 --output-dir results/heir_offline/heir_calibration_20260312
```

### Fresh main + reports

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/heir_collect_actionbank.py --dataset gsm8k_train --limit 50 --offset 1320 --output-dir results/heir_main/gsm8k_train_main_shard1_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
CUDA_VISIBLE_DEVICES=1 python scripts/heir_collect_actionbank.py --dataset gsm8k_train --limit 50 --offset 1370 --output-dir results/heir_main/gsm8k_train_main_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
CUDA_VISIBLE_DEVICES=2 python scripts/heir_collect_actionbank.py --dataset gsm8k_train --limit 50 --offset 1420 --output-dir results/heir_main/gsm8k_train_main_shard3_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
CUDA_VISIBLE_DEVICES=3 python scripts/heir_collect_actionbank.py --dataset gsm8k_train --limit 50 --offset 1470 --output-dir results/heir_main/gsm8k_train_main_shard4_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
CUDA_VISIBLE_DEVICES=2 python scripts/heir_collect_actionbank.py --dataset asdiv --limit 50 --offset 1040 --output-dir results/heir_main/asdiv_main_shard1_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
CUDA_VISIBLE_DEVICES=3 python scripts/heir_collect_actionbank.py --dataset asdiv --limit 50 --offset 1090 --output-dir results/heir_main/asdiv_main_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
CUDA_VISIBLE_DEVICES=2 python scripts/heir_collect_actionbank.py --dataset asdiv --limit 50 --offset 1140 --output-dir results/heir_main/asdiv_main_shard3_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
CUDA_VISIBLE_DEVICES=3 python scripts/heir_collect_actionbank.py --dataset multiarith --limit 50 --offset 100 --output-dir results/heir_main/multiarith_main_shard1_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
CUDA_VISIBLE_DEVICES=0 python scripts/heir_collect_actionbank.py --dataset multiarith --limit 30 --offset 150 --output-dir results/heir_main/multiarith_main_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
CUDA_VISIBLE_DEVICES=0 python scripts/heir_collect_actionbank.py --dataset multiarith --limit 10 --offset 50 --output-dir results/heir_main/multiarith_main_shard3_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
CUDA_VISIBLE_DEVICES=1 python scripts/heir_collect_actionbank.py --dataset multiarith --limit 10 --offset 70 --output-dir results/heir_main/multiarith_main_shard4_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-dtype float16
python scripts/heir_main.py --main-dirs results/heir_main/gsm8k_train_main_shard1_20260312 results/heir_main/gsm8k_train_main_shard2_20260312 results/heir_main/gsm8k_train_main_shard3_20260312 results/heir_main/gsm8k_train_main_shard4_20260312 results/heir_main/asdiv_main_shard1_20260312 results/heir_main/asdiv_main_shard2_20260312 results/heir_main/asdiv_main_shard3_20260312 results/heir_main/multiarith_main_shard1_20260312 results/heir_main/multiarith_main_shard2_20260312 results/heir_main/multiarith_main_shard3_20260312 results/heir_main/multiarith_main_shard4_20260312 --offline-dir results/heir_offline/heir_calibration_pivotplus_20260312 --output-dir results/heir_main/heir_main_eval_pivotplus_20260312
python scripts/make_heir_reports.py --oracle-dir results/heir_oracle_geometry/initial_20260312 --calibration-dirs results/heir_calibration/gsm8k_train_cal_shard1_20260312 results/heir_calibration/gsm8k_train_cal_shard2_20260312 results/heir_calibration/asdiv_cal_shard1_20260312 results/heir_calibration/asdiv_cal_shard2_20260312 --transfer-screen-dir results/heir_transfer_screen/screen_20260312 --offline-dir results/heir_offline/heir_calibration_pivotplus_20260312 --main-dir results/heir_main/heir_main_eval_pivotplus_20260312 --main-raw-dirs results/heir_main/gsm8k_train_main_shard1_20260312 results/heir_main/gsm8k_train_main_shard2_20260312 results/heir_main/gsm8k_train_main_shard3_20260312 results/heir_main/gsm8k_train_main_shard4_20260312 results/heir_main/asdiv_main_shard1_20260312 results/heir_main/asdiv_main_shard2_20260312 results/heir_main/asdiv_main_shard3_20260312 results/heir_main/multiarith_main_shard1_20260312 results/heir_main/multiarith_main_shard2_20260312 results/heir_main/multiarith_main_shard3_20260312 results/heir_main/multiarith_main_shard4_20260312 --report-dir reports --table-dir tables/heir --figure-dir figures/heir
```

### HEIR current status

- Supported:
  - executability-aware hierarchy is justified by oracle action geometry
  - utility-delta hierarchical routing recovers most of the initial hard-set HEIR failure
  - easy-set low-intervention behavior remains strong
- Not yet supported:
  - HEIR beats fixed `PYTHON_RECOMPUTE` on `gsm8k_train`
  - HEIR beats the best flat EIR policy on the hard set

## GEM-HEIR commands

GEM-HEIR keeps the HEIR-pruned action set and changes the target from action identity to gate-specific cost-aware utility margins:

- `KEEP`
- `PYTHON_RECOMPUTE`
- `LOCALIZE_BACKTRACK`
- `FREEFORM_CRITIQUE`

### Margin audit + transfer screen

```bash
python scripts/gemheir_margin_audit.py \
  --input-dirs \
    results/eir_actionbank/gsm8k_train_cal_shard1_20260312 \
    results/eir_actionbank/gsm8k_train_cal_shard2_20260312 \
    results/eir_actionbank/asdiv_cal_shard2_20260312 \
    results/eir_actionbank/asdiv_cal_shard3_20260312 \
    results/eir_actionbank/mawps_cal_shard1_20260312 \
    results/eir_actionbank/mawps_cal_shard2_rerun_20260312 \
  --output-dir results/gemheir_offline/margin_audit_20260312

python scripts/gemheir_transfer_screen.py \
  --datasets svamp mawps \
  --offsets svamp:300 mawps:400 \
  --limit 20 \
  --model-name Qwen/Qwen2.5-7B-Instruct \
  --output-dir results/gemheir_transfer_screen/screen_20260312 \
  --client hf_local \
  --local-quantization 4bit \
  --local-dtype float16
```

### Fresh calibration bank

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/gemheir_collect_actionbank.py --client hf_local --dataset gsm8k_train --limit 70 --offset 1970 --output-dir results/gemheir_calibration/gsm8k_train_cal_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096
CUDA_VISIBLE_DEVICES=1 python scripts/gemheir_collect_actionbank.py --client hf_local --dataset gsm8k_train --limit 35 --offset 2040 --output-dir results/gemheir_calibration/gsm8k_train_cal_shard3a_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096
CUDA_VISIBLE_DEVICES=2 python scripts/gemheir_collect_actionbank.py --client hf_local --dataset gsm8k_train --limit 35 --offset 2075 --output-dir results/gemheir_calibration/gsm8k_train_cal_shard3b_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096
CUDA_VISIBLE_DEVICES=3 python scripts/gemheir_collect_actionbank.py --client hf_local --dataset gsm8k_train --limit 35 --offset 2110 --output-dir results/gemheir_calibration/gsm8k_train_cal_shard4_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096
CUDA_VISIBLE_DEVICES=2 python scripts/gemheir_collect_actionbank.py --client hf_local --dataset asdiv --limit 50 --offset 1400 --output-dir results/gemheir_calibration/asdiv_cal_shard1_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096
CUDA_VISIBLE_DEVICES=3 python scripts/gemheir_collect_actionbank.py --client hf_local --dataset asdiv --limit 50 --offset 1450 --output-dir results/gemheir_calibration/asdiv_cal_shard2_20260312 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096
```

### Offline GEM study

```bash
python scripts/gemheir_offline.py \
  --calibration-dirs \
    results/gemheir_calibration/gsm8k_train_cal_shard2_20260312 \
    results/gemheir_calibration/gsm8k_train_cal_shard3a_20260313 \
    results/gemheir_calibration/gsm8k_train_cal_shard3b_20260313 \
    results/gemheir_calibration/gsm8k_train_cal_shard4_20260313 \
    results/gemheir_calibration/asdiv_cal_shard1_20260312 \
    results/gemheir_calibration/asdiv_cal_shard2_20260312 \
  --output-dir results/gemheir_offline/gem_calibration_20260313
```

### Fresh held-out main + reports

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/gemheir_collect_actionbank.py --client hf_local --dataset gsm8k_train --limit 50 --offset 2145 --output-dir results/gemheir_main/gsm8k_train_main_shard1_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096
CUDA_VISIBLE_DEVICES=1 python scripts/gemheir_collect_actionbank.py --client hf_local --dataset gsm8k_train --limit 50 --offset 2195 --output-dir results/gemheir_main/gsm8k_train_main_shard2_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096
CUDA_VISIBLE_DEVICES=2 python scripts/gemheir_collect_actionbank.py --client hf_local --dataset gsm8k_train --limit 50 --offset 2245 --output-dir results/gemheir_main/gsm8k_train_main_shard3_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096
CUDA_VISIBLE_DEVICES=0 python scripts/gemheir_collect_actionbank.py --client hf_local --dataset gsm8k_train --limit 50 --offset 2295 --output-dir results/gemheir_main/gsm8k_train_main_shard4_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096
CUDA_VISIBLE_DEVICES=3 python scripts/gemheir_collect_actionbank.py --client hf_local --dataset asdiv --limit 50 --offset 1500 --output-dir results/gemheir_main/asdiv_main_shard1_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096
CUDA_VISIBLE_DEVICES=1 python scripts/gemheir_collect_actionbank.py --client hf_local --dataset asdiv --limit 50 --offset 1550 --output-dir results/gemheir_main/asdiv_main_shard2_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096
CUDA_VISIBLE_DEVICES=2 python scripts/gemheir_collect_actionbank.py --client hf_local --dataset asdiv --limit 50 --offset 1600 --output-dir results/gemheir_main/asdiv_main_shard3_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096

python scripts/gemheir_main.py \
  --main-dirs \
    results/gemheir_main/gsm8k_train_main_shard1_20260313 \
    results/gemheir_main/gsm8k_train_main_shard2_20260313 \
    results/gemheir_main/gsm8k_train_main_shard3_20260313 \
    results/gemheir_main/gsm8k_train_main_shard4_20260313 \
    results/gemheir_main/asdiv_main_shard1_20260313 \
    results/gemheir_main/asdiv_main_shard2_20260313 \
    results/gemheir_main/asdiv_main_shard3_20260313 \
  --offline-dir results/gemheir_offline/gem_calibration_20260313 \
  --output-dir results/gemheir_main/gem_main_20260313

python scripts/make_gemheir_reports.py \
  --margin-audit-dir results/gemheir_offline/margin_audit_20260312 \
  --transfer-screen-dir results/gemheir_transfer_screen/screen_20260312 \
  --offline-dir results/gemheir_offline/gem_calibration_20260313 \
  --main-dir results/gemheir_main/gem_main_20260313 \
  --main-raw-dirs \
    results/gemheir_main/gsm8k_train_main_shard1_20260313 \
    results/gemheir_main/gsm8k_train_main_shard2_20260313 \
    results/gemheir_main/gsm8k_train_main_shard3_20260313 \
    results/gemheir_main/gsm8k_train_main_shard4_20260313 \
    results/gemheir_main/asdiv_main_shard1_20260313 \
    results/gemheir_main/asdiv_main_shard2_20260313 \
    results/gemheir_main/asdiv_main_shard3_20260313 \
  --report-dir reports \
  --table-dir tables/gemheir \
  --figure-dir figures/gemheir
```

### GEM-HEIR current status

- Supported:
  - gate-specific executability-margin routing improves over flat EIR and over the best HEIR hard-set reference
  - adaptive routed policies remain much stronger than fixed freeform critique
  - mixed hard/easy workloads still favor adaptive routing over previous routers
- Not supported:
  - GEM-HEIR beats fixed `PYTHON_RECOMPUTE` / `BEST_FIXED_ACTION` on fresh `gsm8k_train`
  - the offline win over fixed python robustly replicates held-out
  - regime stratification is clearly the decisive ingredient

## TIER commands

TIER reframes the remaining bottleneck from action-family routing to semantic-to-executable interface quality.

Interface palette:

- `KEEP`
- `RAW_PYTHON`
- `QUANTITY_TABLE_TO_CODE`
- `OPERATOR_SCHEMA_TO_CODE`
- `EQUATION_SKETCH_TO_CODE`

### Tiny dev

```bash
python scripts/tier_collect_interfacebank.py --client hf_local --dataset gsm8k_train --limit 12 --offset 2390 --output-dir results/tier_dev/gsm8k_train_dev_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
python scripts/tier_collect_interfacebank.py --client hf_local --dataset asdiv --limit 12 --offset 1640 --output-dir results/tier_dev/asdiv_dev_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
```

### Calibration + offline

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/tier_collect_interfacebank.py --client hf_local --dataset gsm8k_train --limit 50 --offset 2360 --output-dir results/tier_calibration/gsm8k_train_cal_shard1_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/tier_collect_interfacebank.py --client hf_local --dataset gsm8k_train --limit 50 --offset 2410 --output-dir results/tier_calibration/gsm8k_train_cal_shard2_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/tier_collect_interfacebank.py --client hf_local --dataset gsm8k_train --limit 50 --offset 2460 --output-dir results/tier_calibration/gsm8k_train_cal_shard3_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/tier_collect_interfacebank.py --client hf_local --dataset asdiv --limit 50 --offset 1660 --output-dir results/tier_calibration/asdiv_cal_shard1_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=0 python scripts/tier_collect_interfacebank.py --client hf_local --dataset asdiv --limit 50 --offset 1710 --output-dir results/tier_calibration/asdiv_cal_shard2_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code

python scripts/tier_offline.py \
  --calibration-dirs \
    results/tier_calibration/gsm8k_train_cal_shard1_20260313 \
    results/tier_calibration/gsm8k_train_cal_shard2_20260313 \
    results/tier_calibration/gsm8k_train_cal_shard3_20260313 \
    results/tier_calibration/asdiv_cal_shard1_20260313 \
    results/tier_calibration/asdiv_cal_shard2_20260313 \
  --output-dir results/tier_offline/tier_calibration_20260313
```

### Fresh held-out main + reports

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/tier_collect_interfacebank.py --client hf_local --dataset gsm8k_train --limit 50 --offset 2510 --output-dir results/tier_main/gsm8k_train_main_shard1_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/tier_collect_interfacebank.py --client hf_local --dataset gsm8k_train --limit 50 --offset 2560 --output-dir results/tier_main/gsm8k_train_main_shard2_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/tier_collect_interfacebank.py --client hf_local --dataset gsm8k_train --limit 50 --offset 2610 --output-dir results/tier_main/gsm8k_train_main_shard3_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=0 python scripts/tier_collect_interfacebank.py --client hf_local --dataset gsm8k_train --limit 50 --offset 2660 --output-dir results/tier_main/gsm8k_train_main_shard4_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/tier_collect_interfacebank.py --client hf_local --dataset asdiv --limit 50 --offset 1760 --output-dir results/tier_main/asdiv_main_shard1_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/tier_collect_interfacebank.py --client hf_local --dataset asdiv --limit 50 --offset 1810 --output-dir results/tier_main/asdiv_main_shard2_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/tier_collect_interfacebank.py --client hf_local --dataset asdiv --limit 50 --offset 1860 --output-dir results/tier_main/asdiv_main_shard3_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/tier_collect_interfacebank.py --client hf_local --dataset asdiv --limit 50 --offset 1910 --output-dir results/tier_main/asdiv_main_shard4_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code

python scripts/tier_main.py \
  --main-dirs \
    results/tier_main/gsm8k_train_main_shard1_20260313 \
    results/tier_main/gsm8k_train_main_shard2_20260313 \
    results/tier_main/gsm8k_train_main_shard3_20260313 \
    results/tier_main/gsm8k_train_main_shard4_20260313 \
    results/tier_main/asdiv_main_shard1_20260313 \
    results/tier_main/asdiv_main_shard2_20260313 \
    results/tier_main/asdiv_main_shard3_20260313 \
    results/tier_main/asdiv_main_shard4_20260313 \
  --offline-dir results/tier_offline/tier_calibration_20260313 \
  --output-dir results/tier_main/tier_main_20260313

python scripts/make_tier_reports.py \
  --calibration-dirs \
    results/tier_calibration/gsm8k_train_cal_shard1_20260313 \
    results/tier_calibration/gsm8k_train_cal_shard2_20260313 \
    results/tier_calibration/gsm8k_train_cal_shard3_20260313 \
    results/tier_calibration/asdiv_cal_shard1_20260313 \
    results/tier_calibration/asdiv_cal_shard2_20260313 \
  --offline-dir results/tier_offline/tier_calibration_20260313 \
  --main-dir results/tier_main/tier_main_20260313 \
  --main-raw-dirs \
    results/tier_main/gsm8k_train_main_shard1_20260313 \
    results/tier_main/gsm8k_train_main_shard2_20260313 \
    results/tier_main/gsm8k_train_main_shard3_20260313 \
    results/tier_main/gsm8k_train_main_shard4_20260313 \
    results/tier_main/asdiv_main_shard1_20260313 \
    results/tier_main/asdiv_main_shard2_20260313 \
    results/tier_main/asdiv_main_shard3_20260313 \
    results/tier_main/asdiv_main_shard4_20260313 \
  --report-dir reports \
  --table-dir tables/tier \
  --figure-dir figures/tier
```

### TIER current status

- Supported:
  - semantic-to-executable interface quality is a stronger remaining bottleneck than additional action-routing complexity
  - on hard held-out `gsm8k_train`, the strongest structured fixed interface is `OPERATOR_SCHEMA_TO_CODE = 0.7184`, above `RAW_PYTHON = 0.6893`
  - structured executable interfaces remain much stronger than freeform critique baselines on hard arithmetic
- Not supported:
  - `FULL_TIER_ROUTER_hardopt` beats `RAW_PYTHON` on hard held-out data
  - extra interface-routing complexity is the main source of gain
- Project-wide final synthesis:
  - see `reports/final_integrated_project_report.md`

## OSCAR commands

OSCAR reframes the post-TIER problem from interface routing to semantic-to-executable compilation quality.

Compiler palette:

- `KEEP`
- `RAW_PYTHON`
- `OPERATOR_SCHEMA_TO_CODE`
- `OSCAR_TEMPLATE_COMPILE`
- bounded Pivot A replacement: `NORMALIZED_QUESTION_TO_CODE`

### Manifests

```bash
python scripts/oscar_make_manifests.py --output-dir data/oscar_manifests_20260313
```

### Initial calibration bank

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/gsm8k_train_calibration__shard01of02.json --output-dir results/oscar_calibration/oscar_calibration_20260313/gsm8k_train_calibration_s1 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/gsm8k_train_calibration__shard02of02.json --output-dir results/oscar_calibration/oscar_calibration_20260313/gsm8k_train_calibration_s2 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/asdiv_calibration__shard01of02.json --output-dir results/oscar_calibration/oscar_calibration_20260313/asdiv_calibration_s1 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/asdiv_calibration__shard02of02.json --output-dir results/oscar_calibration/oscar_calibration_20260313/asdiv_calibration_s2 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code

CUDA_VISIBLE_DEVICES=2 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/gsm8k_train_conditioning_subset__shard01of02.json --output-dir results/oscar_calibration/oscar_calibration_20260313/gsm8k_train_conditioning_problem_only_s1 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --problem-only --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/gsm8k_train_conditioning_subset__shard02of02.json --output-dir results/oscar_calibration/oscar_calibration_20260313/gsm8k_train_conditioning_problem_only_s2 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --problem-only --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/asdiv_conditioning_subset__shard01of01.json --output-dir results/oscar_calibration/oscar_calibration_20260313/asdiv_conditioning_problem_only_s1 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --problem-only --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code

python scripts/oscar_offline.py \
  --calibration-dirs \
    results/oscar_calibration/oscar_calibration_20260313/gsm8k_train_calibration_s1 \
    results/oscar_calibration/oscar_calibration_20260313/gsm8k_train_calibration_s2 \
    results/oscar_calibration/oscar_calibration_20260313/asdiv_calibration_s1 \
    results/oscar_calibration/oscar_calibration_20260313/asdiv_calibration_s2 \
  --problem-only-dirs \
    results/oscar_calibration/oscar_calibration_20260313/gsm8k_train_conditioning_problem_only_s1 \
    results/oscar_calibration/oscar_calibration_20260313/gsm8k_train_conditioning_problem_only_s2 \
    results/oscar_calibration/oscar_calibration_20260313/asdiv_conditioning_problem_only_s1 \
  --output-dir results/oscar_offline/oscar_offline_20260313 \
  --hard-lambda 0.01 \
  --balanced-lambda 0.03
```

### Pivot A + conditioning rerun

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/gsm8k_train_calibration__shard01of02.json --output-dir results/oscar_calibration/oscar_calibration_pivotA_20260313/gsm8k_train_calibration_s1 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/gsm8k_train_calibration__shard02of02.json --output-dir results/oscar_calibration/oscar_calibration_pivotA_20260313/gsm8k_train_calibration_s2 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/asdiv_calibration__shard01of02.json --output-dir results/oscar_calibration/oscar_calibration_pivotA_20260313/asdiv_calibration_s1 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/asdiv_calibration__shard02of02.json --output-dir results/oscar_calibration/oscar_calibration_pivotA_20260313/asdiv_calibration_s2 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code

CUDA_VISIBLE_DEVICES=0 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/gsm8k_train_conditioning_subset__shard01of02.json --output-dir results/oscar_calibration/oscar_calibration_pivotA_20260313/gsm8k_train_conditioning_problem_only_s1 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --problem-only --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/gsm8k_train_conditioning_subset__shard02of02.json --output-dir results/oscar_calibration/oscar_calibration_pivotA_20260313/gsm8k_train_conditioning_problem_only_s2 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --problem-only --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/asdiv_conditioning_subset__shard01of01.json --output-dir results/oscar_calibration/oscar_calibration_pivotA_20260313/asdiv_conditioning_problem_only_s1 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --problem-only --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code

python scripts/oscar_offline.py \
  --calibration-dirs \
    results/oscar_calibration/oscar_calibration_pivotA_20260313/gsm8k_train_calibration_s1 \
    results/oscar_calibration/oscar_calibration_pivotA_20260313/gsm8k_train_calibration_s2 \
    results/oscar_calibration/oscar_calibration_pivotA_20260313/asdiv_calibration_s1 \
    results/oscar_calibration/oscar_calibration_pivotA_20260313/asdiv_calibration_s2 \
  --problem-only-dirs \
    results/oscar_calibration/oscar_calibration_pivotA_20260313/gsm8k_train_conditioning_problem_only_s1 \
    results/oscar_calibration/oscar_calibration_pivotA_20260313/gsm8k_train_conditioning_problem_only_s2 \
    results/oscar_calibration/oscar_calibration_pivotA_20260313/asdiv_conditioning_problem_only_s1 \
  --output-dir results/oscar_offline/oscar_offline_pivotA_20260313 \
  --hard-lambda 0.01 \
  --balanced-lambda 0.03
```

### Held-out main + reports

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/gsm8k_train_cluster_main__shard01of04.json --output-dir results/oscar_main/oscar_main_20260313_raw/gsm8k_train_cluster_main_s1 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/gsm8k_train_cluster_main__shard02of04.json --output-dir results/oscar_main/oscar_main_20260313_raw/gsm8k_train_cluster_main_s2 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/gsm8k_train_cluster_main__shard03of04.json --output-dir results/oscar_main/oscar_main_20260313_raw/gsm8k_train_cluster_main_s3 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/gsm8k_train_cluster_main__shard04of04.json --output-dir results/oscar_main/oscar_main_20260313_raw/gsm8k_train_cluster_main_s4 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/gsm8k_train_generic_main__shard01of02.json --output-dir results/oscar_main/oscar_main_20260313_raw/gsm8k_train_generic_main_s1 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=0 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/gsm8k_train_generic_main__shard02of02.json --output-dir results/oscar_main/oscar_main_20260313_raw/gsm8k_train_generic_main_s2 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/asdiv_easy_main__shard01of02.json --output-dir results/oscar_main/oscar_main_20260313_raw/asdiv_easy_main_s1 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python scripts/oscar_collect_interfacebank.py --client hf_local --manifest data/oscar_manifests_20260313/shards/asdiv_easy_main__shard02of02.json --output-dir results/oscar_main/oscar_main_20260313_raw/asdiv_easy_main_s2 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --use-normalized-replacement --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code

python scripts/oscar_main.py \
  --main-dirs \
    results/oscar_main/oscar_main_20260313_raw/gsm8k_train_cluster_main_s1 \
    results/oscar_main/oscar_main_20260313_raw/gsm8k_train_cluster_main_s2 \
    results/oscar_main/oscar_main_20260313_raw/gsm8k_train_cluster_main_s3 \
    results/oscar_main/oscar_main_20260313_raw/gsm8k_train_cluster_main_s4 \
    results/oscar_main/oscar_main_20260313_raw/gsm8k_train_generic_main_s1 \
    results/oscar_main/oscar_main_20260313_raw/gsm8k_train_generic_main_s2 \
    results/oscar_main/oscar_main_20260313_raw/asdiv_easy_main_s1 \
    results/oscar_main/oscar_main_20260313_raw/asdiv_easy_main_s2 \
  --offline-dir results/oscar_offline/oscar_offline_pivotA_20260313 \
  --output-dir results/oscar_main/oscar_main_eval_20260313 \
  --hard-lambda 0.01 \
  --balanced-lambda 0.03

python scripts/make_oscar_reports.py \
  --calibration-dirs \
    results/oscar_calibration/oscar_calibration_pivotA_20260313/gsm8k_train_calibration_s1 \
    results/oscar_calibration/oscar_calibration_pivotA_20260313/gsm8k_train_calibration_s2 \
    results/oscar_calibration/oscar_calibration_pivotA_20260313/asdiv_calibration_s1 \
    results/oscar_calibration/oscar_calibration_pivotA_20260313/asdiv_calibration_s2 \
  --offline-dir results/oscar_offline/oscar_offline_pivotA_20260313 \
  --main-dir results/oscar_main/oscar_main_eval_20260313 \
  --main-raw-dirs \
    results/oscar_main/oscar_main_20260313_raw/gsm8k_train_cluster_main_s1 \
    results/oscar_main/oscar_main_20260313_raw/gsm8k_train_cluster_main_s2 \
    results/oscar_main/oscar_main_20260313_raw/gsm8k_train_cluster_main_s3 \
    results/oscar_main/oscar_main_20260313_raw/gsm8k_train_cluster_main_s4 \
    results/oscar_main/oscar_main_20260313_raw/gsm8k_train_generic_main_s1 \
    results/oscar_main/oscar_main_20260313_raw/gsm8k_train_generic_main_s2 \
    results/oscar_main/oscar_main_20260313_raw/asdiv_easy_main_s1 \
    results/oscar_main/oscar_main_20260313_raw/asdiv_easy_main_s2 \
  --report-dir reports \
  --table-dir tables/oscar \
  --figure-dir figures/oscar \
  --hard-lambda 0.01 \
  --balanced-lambda 0.03
```

### OSCAR current status

- Supported:
  - semantic-to-executable compilation remains the right abstraction after TIER
  - Pivot A replacement `NORMALIZED_QUESTION_TO_CODE` beat both `RAW_PYTHON` and `OPERATOR_SCHEMA_TO_CODE` offline:
    - `gsm8k_train`: `0.7533` vs `0.7000` / `0.7067`
    - `asdiv`: `0.7778` vs `0.7444` / `0.7667`
  - conditioning comparison favored `problem + draft` over `problem only` for all serious executable interfaces
  - on held-out cluster-balanced hard arithmetic, fixed structured `OPERATOR_SCHEMA_TO_CODE = 0.7150` outperformed `RAW_PYTHON = 0.6950`
  - on easy arithmetic, structured interfaces (`NORMALIZED_QUESTION_TO_CODE`, `OPERATOR_SCHEMA_TO_CODE`) reached `0.99`
- Not supported:
  - the new OSCAR compilers beat `RAW_PYTHON` on the generic hard hold-out
  - offline `NORMALIZED_QUESTION_TO_CODE` gains replicated as the strongest held-out hard result
  - deterministic template compilation is the main frontier mechanism under the current local model family
- Strongest surviving OSCAR story:
  - structured operator/discretization interfaces help because they improve semantic-to-executable compilation quality
  - the most reliable hard-set gain remained concentrated in fixed structured interfaces, especially `OPERATOR_SCHEMA_TO_CODE`, rather than in more ambitious compilers or another router
- Updated project-wide synthesis:
  - see `reports/final_integrated_project_report_oscar.md`

## ATLAS commands

ATLAS reframes the post-OSCAR problem around schema extraction quality for the already-promising operator/discretization interface.

Method palette:

- `KEEP`
- `RAW_PYTHON`
- `OPERATOR_SCHEMA_TO_CODE_BASE`
- `ATLAS_RETRIEVAL_SCHEMA_TO_CODE`
- `ATLAS_FIELDWISE_SCHEMA_TO_CODE`
- bounded Pivot C artifact: `ATLAS_CRITICAL_FIELD_REPAIR`

### Manifests

```bash
python /workspace/project/scripts/atlas_make_manifests.py --output-dir /workspace/project/data/atlas_manifests_20260313
```

### Teacher seed

API teacher extraction was skipped because `OPENAI_API_KEY` was unset. The frozen seed was built locally with `Qwen/Qwen2.5-7B-Instruct` and audited into a small retrieval memory.

```bash
CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/atlas_build_teacher_seed.py --client hf_local --manifest /workspace/project/data/atlas_manifests_20260313/shards/gsm8k_train_teacher_seed_hard__shard01of04.json --output-dir /workspace/project/results/atlas_calibration/teacher_seed_shard1_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python /workspace/project/scripts/atlas_build_teacher_seed.py --client hf_local --manifest /workspace/project/data/atlas_manifests_20260313/shards/gsm8k_train_teacher_seed_hard__shard02of04.json --output-dir /workspace/project/results/atlas_calibration/teacher_seed_shard2_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python /workspace/project/scripts/atlas_build_teacher_seed.py --client hf_local --manifest /workspace/project/data/atlas_manifests_20260313/shards/gsm8k_train_teacher_seed_hard__shard03of04.json --output-dir /workspace/project/results/atlas_calibration/teacher_seed_shard3_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python /workspace/project/scripts/atlas_build_teacher_seed.py --client hf_local --manifest /workspace/project/data/atlas_manifests_20260313/shards/gsm8k_train_teacher_seed_hard__shard04of04.json --output-dir /workspace/project/results/atlas_calibration/teacher_seed_shard4_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
```

Merged audited seed:

- `/workspace/project/results/atlas_calibration/teacher_seed_merged_20260313/teacher_seed.jsonl`

### Optional API teacher phase

Once `OPENAI_API_KEY` became available, the skipped bounded teacher phase was run with `gpt-5-mini`:

```bash
cd /workspace/project
set -a && source /workspace/project/.env.example && set +a
python /workspace/project/scripts/atlas_build_teacher_seed.py \
  --client openai \
  --manifest /workspace/project/data/atlas_manifests_20260313/gsm8k_train_teacher_seed.json \
  --output-dir /workspace/project/results/atlas_api_diag/teacher_seed_gpt5mini_20260314 \
  --model-name gpt-5-mini
```

Key result:

- candidates `72`
- kept `32`
- total API cost about `$0.038`
- report: `/workspace/project/reports/atlas_teacher_audit.md`

### Calibration collection

```bash
CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/atlas_collect_interfacebank.py --client hf_local --manifest /workspace/project/data/atlas_manifests_20260313/shards/gsm8k_train_hard_calibration__shard01of04.json --output-dir /workspace/project/results/atlas_calibration/hard_cal_shard1_global_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --teacher-seed /workspace/project/results/atlas_calibration/teacher_seed_merged_20260313/teacher_seed.jsonl --retrieval-mode global --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python /workspace/project/scripts/atlas_collect_interfacebank.py --client hf_local --manifest /workspace/project/data/atlas_manifests_20260313/shards/gsm8k_train_hard_calibration__shard02of04.json --output-dir /workspace/project/results/atlas_calibration/hard_cal_shard2_global_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --teacher-seed /workspace/project/results/atlas_calibration/teacher_seed_merged_20260313/teacher_seed.jsonl --retrieval-mode global --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=2 python /workspace/project/scripts/atlas_collect_interfacebank.py --client hf_local --manifest /workspace/project/data/atlas_manifests_20260313/shards/gsm8k_train_hard_calibration__shard03of04.json --output-dir /workspace/project/results/atlas_calibration/hard_cal_shard3_global_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --teacher-seed /workspace/project/results/atlas_calibration/teacher_seed_merged_20260313/teacher_seed.jsonl --retrieval-mode global --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python /workspace/project/scripts/atlas_collect_interfacebank.py --client hf_local --manifest /workspace/project/data/atlas_manifests_20260313/shards/gsm8k_train_hard_calibration__shard04of04.json --output-dir /workspace/project/results/atlas_calibration/hard_cal_shard4_global_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --teacher-seed /workspace/project/results/atlas_calibration/teacher_seed_merged_20260313/teacher_seed.jsonl --retrieval-mode global --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/atlas_collect_interfacebank.py --client hf_local --manifest /workspace/project/data/atlas_manifests_20260313/shards/asdiv_easy_calibration__shard01of02.json --output-dir /workspace/project/results/atlas_calibration/easy_cal_shard1_global_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --teacher-seed /workspace/project/results/atlas_calibration/teacher_seed_merged_20260313/teacher_seed.jsonl --retrieval-mode global --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=1 python /workspace/project/scripts/atlas_collect_interfacebank.py --client hf_local --manifest /workspace/project/data/atlas_manifests_20260313/shards/asdiv_easy_calibration__shard02of02.json --output-dir /workspace/project/results/atlas_calibration/easy_cal_shard2_global_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --teacher-seed /workspace/project/results/atlas_calibration/teacher_seed_merged_20260313/teacher_seed.jsonl --retrieval-mode global --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code

CUDA_VISIBLE_DEVICES=2 python /workspace/project/scripts/atlas_collect_interfacebank.py --client hf_local --manifest /workspace/project/data/atlas_manifests_20260313/shards/gsm8k_train_hard_conditioning_subset__shard01of02.json --output-dir /workspace/project/results/atlas_calibration/hard_conditioning_problem_only_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --teacher-seed /workspace/project/results/atlas_calibration/teacher_seed_merged_20260313/teacher_seed.jsonl --retrieval-mode global --problem-only --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
CUDA_VISIBLE_DEVICES=3 python /workspace/project/scripts/atlas_collect_interfacebank.py --client hf_local --manifest /workspace/project/data/atlas_manifests_20260313/shards/asdiv_easy_conditioning_subset__shard01of01.json --output-dir /workspace/project/results/atlas_calibration/easy_conditioning_problem_only_20260313 --model-name Qwen/Qwen2.5-7B-Instruct --teacher-seed /workspace/project/results/atlas_calibration/teacher_seed_merged_20260313/teacher_seed.jsonl --retrieval-mode global --problem-only --disable-prm --local-quantization 4bit --local-dtype float16 --local-device-map auto --local-max-model-len 4096 --local-trust-remote-code
```

### Offline study + pivots

```bash
python /workspace/project/scripts/atlas_offline.py \
  --calibration-dirs \
    /workspace/project/results/atlas_calibration/hard_cal_shard1_global_20260313 \
    /workspace/project/results/atlas_calibration/hard_cal_shard2_global_20260313 \
    /workspace/project/results/atlas_calibration/hard_cal_shard3_global_20260313 \
    /workspace/project/results/atlas_calibration/hard_cal_shard4_global_20260313 \
    /workspace/project/results/atlas_calibration/easy_cal_shard1_global_20260313 \
    /workspace/project/results/atlas_calibration/easy_cal_shard2_global_20260313 \
  --problem-only-dirs \
    /workspace/project/results/atlas_calibration/hard_conditioning_problem_only_20260313 \
    /workspace/project/results/atlas_calibration/easy_conditioning_problem_only_20260313 \
  --teacher-eval-dirs \
    /workspace/project/results/atlas_calibration/teacher_eval_shard1_global_20260313 \
    /workspace/project/results/atlas_calibration/teacher_eval_shard2_global_20260313 \
  --output-dir /workspace/project/results/atlas_offline/global_full_20260313

python /workspace/project/scripts/atlas_offline.py \
  --calibration-dirs \
    /workspace/project/results/atlas_calibration/hard_cal_shard1_clusterfirst_20260313 \
    /workspace/project/results/atlas_calibration/hard_cal_shard2_clusterfirst_20260313 \
    /workspace/project/results/atlas_calibration/hard_cal_shard3_clusterfirst_20260313 \
    /workspace/project/results/atlas_calibration/hard_cal_shard4_clusterfirst_20260313 \
    /workspace/project/results/atlas_calibration/easy_cal_shard1_global_20260313 \
    /workspace/project/results/atlas_calibration/easy_cal_shard2_global_20260313 \
  --output-dir /workspace/project/results/atlas_offline/clusterfirst_20260313

python /workspace/project/scripts/atlas_offline.py \
  --calibration-dirs \
    /workspace/project/results/atlas_calibration/hard_cal_shard1_repair_20260313 \
    /workspace/project/results/atlas_calibration/hard_cal_shard2_repair_20260313 \
    /workspace/project/results/atlas_calibration/hard_cal_shard3_repair_20260313 \
    /workspace/project/results/atlas_calibration/hard_cal_shard4_repair_20260313 \
    /workspace/project/results/atlas_calibration/easy_cal_shard1_global_20260313 \
    /workspace/project/results/atlas_calibration/easy_cal_shard2_global_20260313 \
  --output-dir /workspace/project/results/atlas_offline/repair_20260313
```

### Held-out main

```bash
python /workspace/project/scripts/atlas_main.py \
  --main-dirs \
    /workspace/project/results/atlas_main/cluster_main_shard1_globalrepair_20260313 \
    /workspace/project/results/atlas_main/cluster_main_shard2_globalrepair_20260313 \
    /workspace/project/results/atlas_main/cluster_main_shard3_globalrepair_20260313 \
    /workspace/project/results/atlas_main/cluster_main_shard4_globalrepair_20260313 \
    /workspace/project/results/atlas_main/generic_main_shard1_globalrepair_20260313 \
    /workspace/project/results/atlas_main/generic_main_shard2_globalrepair_20260313 \
  --offline-dir /workspace/project/results/atlas_offline/global_full_20260313 \
  --output-dir /workspace/project/results/atlas_main/atlas_main_eval_20260313 \
  --hard-lambda 0.01 \
  --balanced-lambda 0.03
```

### ATLAS current status

- Supported:
  - `problem + draft` beats `problem only` for the serious schema methods
  - on the cluster-focused hard main surface, ATLAS methods beat `RAW_PYTHON`
  - `ATLAS_RETRIEVAL_SCHEMA_TO_CODE = 0.815`, `ATLAS_FIELDWISE_SCHEMA_TO_CODE = 0.810`, `ATLAS_CRITICAL_FIELD_REPAIR = 0.810`
  - the cleanest pairwise win over `RAW_PYTHON` on cluster-focused hard came from field-wise extraction
  - ATLAS gains are concentrated in the targeted semantic clusters, not broad generic hard dominance
- Not supported:
  - universal hard-set win over generic `gsm8k_train`
  - cluster-first retrieval
  - critical-field repair as a standalone hard-set winner
- Strongest surviving ATLAS story:
  - cluster-aware schema extraction improves the operator-schema interface enough to beat `RAW_PYTHON` on the targeted hard operator/discretization subset
- API follow-up:
  - `gpt-5-mini` teacher auditing reinforced that schema extraction quality is still the core bottleneck
  - but the bounded local rerun with the API seed was too noisy to replace the frozen ATLAS main claim surface

## ATLAS-RG role-grounding branch

ATLAS-RG keeps the operator-schema execution backend fixed and asks a narrower question:

- can quantity-role grounding repair beat `RAW_PYTHON` on the targeted hard operator/discretization clusters?
- is any gain specifically attributable to role grounding rather than generic non-role schema repair?

Environment used for the branch:

```bash
cd /workspace/project
source /workspace/project/.env.example
export HF_TOKEN="$HUGGINGFACE_HUB_TOKEN"
```

Manifest generation:

```bash
python /workspace/project/scripts/atlas_rg_make_manifests.py \
  --output-dir /workspace/project/data/atlas_rg_manifests_20260314c \
  --teacher-target-per-cluster 10 \
  --hard-cal-limit 160 \
  --easy-cal-limit 70 \
  --cluster-main-target-per-cluster 34 \
  --cluster-main-limit 204 \
  --generic-hard-limit 140 \
  --conditioning-hard-limit 80 \
  --conditioning-easy-limit 40
```

API teacher role seed and held-out teacher subset:

```bash
python /workspace/project/scripts/atlas_rg_build_teacher_seed.py \
  --client openai \
  --manifest /workspace/project/data/atlas_rg_manifests_20260314c/gsm8k_train_teacher_seed.json \
  --output-dir /workspace/project/results/atlas_rg_api_diag/teacher_seed_gpt5mini_20260314 \
  --model-name gpt-5-mini

python /workspace/project/scripts/atlas_rg_build_teacher_seed.py \
  --client openai \
  --manifest /workspace/project/data/atlas_rg_manifests_20260314c/gsm8k_train_cluster_teacher_subset59.json \
  --output-dir /workspace/project/results/atlas_rg_api_diag/heldout_teacher_subset59_gpt5mini_20260314 \
  --model-name gpt-5-mini
```

Main local collection path used in the branch:

```bash
MODEL=Qwen/Qwen2.5-7B-Instruct
SEED=/workspace/project/results/atlas_rg_api_diag/teacher_seed_gpt5mini_20260314_merged/teacher_seed.jsonl
MAN=/workspace/project/data/atlas_rg_manifests_20260314c/shards

CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/atlas_rg_collect_interfacebank.py \
  --client hf_local \
  --manifest ${MAN}/gsm8k_train_calibration__shard01of04.json \
  --output-dir /workspace/project/results/atlas_rg_calibration/hard_cal_fp16_20260314_orch/shard01 \
  --model-name ${MODEL} \
  --teacher-seed ${SEED} \
  --retrieval-mode global \
  --disable-prm \
  --local-dtype float16 \
  --local-device-map auto \
  --local-max-model-len 4096 \
  --local-trust-remote-code

CUDA_VISIBLE_DEVICES=1 python /workspace/project/scripts/atlas_rg_collect_interfacebank.py \
  --client hf_local \
  --manifest ${MAN}/gsm8k_train_calibration__shard02of04.json \
  --output-dir /workspace/project/results/atlas_rg_calibration/hard_cal_fp16_20260314_orch/shard02 \
  --model-name ${MODEL} \
  --teacher-seed ${SEED} \
  --retrieval-mode global \
  --disable-prm \
  --local-dtype float16 \
  --local-device-map auto \
  --local-max-model-len 4096 \
  --local-trust-remote-code

CUDA_VISIBLE_DEVICES=2 python /workspace/project/scripts/atlas_rg_collect_interfacebank.py \
  --client hf_local \
  --manifest ${MAN}/gsm8k_train_calibration__shard03of04.json \
  --output-dir /workspace/project/results/atlas_rg_calibration/hard_cal_fp16_20260314_orch/shard03 \
  --model-name ${MODEL} \
  --teacher-seed ${SEED} \
  --retrieval-mode global \
  --disable-prm \
  --local-dtype float16 \
  --local-device-map auto \
  --local-max-model-len 4096 \
  --local-trust-remote-code

CUDA_VISIBLE_DEVICES=3 python /workspace/project/scripts/atlas_rg_collect_interfacebank.py \
  --client hf_local \
  --manifest ${MAN}/gsm8k_train_calibration__shard04of04.json \
  --output-dir /workspace/project/results/atlas_rg_calibration/hard_cal_fp16_20260314_orch/shard04 \
  --model-name ${MODEL} \
  --teacher-seed ${SEED} \
  --retrieval-mode global \
  --disable-prm \
  --local-dtype float16 \
  --local-device-map auto \
  --local-max-model-len 4096 \
  --local-trust-remote-code
```

Offline summary:

```bash
python /workspace/project/scripts/atlas_rg_offline.py \
  --calibration-dirs \
    /workspace/project/results/atlas_rg_calibration/hard_criticalrole_20260314/shard01 \
    /workspace/project/results/atlas_rg_calibration/hard_criticalrole_20260314/shard02 \
    /workspace/project/results/atlas_rg_calibration/hard_criticalrole_20260314/shard03 \
    /workspace/project/results/atlas_rg_calibration/hard_criticalrole_20260314/shard04 \
    /workspace/project/results/atlas_rg_calibration/easy_cal_fp16_20260314/shard01 \
    /workspace/project/results/atlas_rg_calibration/easy_cal_fp16_20260314/shard02 \
    /workspace/project/results/atlas_rg_calibration/easy_cal_fp16_20260314/shard03 \
    /workspace/project/results/atlas_rg_calibration/easy_cal_fp16_20260314/shard04 \
  --teacher-eval-dirs /workspace/project/results/atlas_rg_calibration/teacher_eval_api_20260314/shard01 /workspace/project/results/atlas_rg_calibration/teacher_eval_api_20260314/shard02 /workspace/project/results/atlas_rg_calibration/teacher_eval_api_20260314/shard03 /workspace/project/results/atlas_rg_calibration/teacher_eval_api_20260314/shard04 \
  --problem-only-dirs /workspace/project/results/atlas_rg_calibration/hard_conditioning_problemonly_20260314/shard01 /workspace/project/results/atlas_rg_calibration/hard_conditioning_problemonly_20260314/shard02 /workspace/project/results/atlas_rg_calibration/hard_conditioning_problemonly_20260314/shard03 /workspace/project/results/atlas_rg_calibration/hard_conditioning_problemonly_20260314/shard04 \
  --output-dir /workspace/project/results/atlas_rg_offline/full_pivotC_20260314
```

Held-out main, replay-controlled seed comparison, and report generation:

```bash
FROZEN_DRAFTS=/workspace/project/results/atlas_rg_main/main_api_seed_20260314/drafts_merged.jsonl

python /workspace/project/scripts/atlas_rg_replay_seed_compare.py \
  --client hf_local \
  --manifest /workspace/project/data/atlas_rg_manifests_20260314c/gsm8k_train_cluster_main.json \
  --output-dir /workspace/project/results/atlas_rg_main/replay_local_seed_20260314 \
  --model-name Qwen/Qwen2.5-7B-Instruct \
  --teacher-seed /workspace/project/results/atlas_calibration/teacher_seed_merged_20260313/teacher_seed.jsonl \
  --frozen-drafts ${FROZEN_DRAFTS} \
  --retrieval-mode global \
  --local-dtype float16 \
  --local-device-map auto \
  --local-max-model-len 4096 \
  --local-trust-remote-code

python /workspace/project/scripts/atlas_rg_replay_seed_compare.py \
  --client hf_local \
  --manifest /workspace/project/data/atlas_rg_manifests_20260314c/gsm8k_train_cluster_main.json \
  --output-dir /workspace/project/results/atlas_rg_main/replay_api_seed_20260314 \
  --model-name Qwen/Qwen2.5-7B-Instruct \
  --teacher-seed /workspace/project/results/atlas_rg_api_diag/teacher_seed_gpt5mini_20260314_merged/teacher_seed.jsonl \
  --frozen-drafts ${FROZEN_DRAFTS} \
  --retrieval-mode global \
  --local-dtype float16 \
  --local-device-map auto \
  --local-max-model-len 4096 \
  --local-trust-remote-code

python /workspace/project/scripts/atlas_rg_collect_interfacebank.py \
  --client hf_local \
  --manifest /workspace/project/data/atlas_rg_manifests_20260314c/gsm8k_train_cluster_teacher_covered27.json \
  --output-dir /workspace/project/results/atlas_rg_main/teacher_covered_api_20260314 \
  --model-name Qwen/Qwen2.5-7B-Instruct \
  --teacher-seed /workspace/project/results/atlas_rg_api_diag/heldout_teacher_subset59_gpt5mini_20260314/teacher_seed.jsonl \
  --frozen-drafts ${FROZEN_DRAFTS} \
  --retrieval-mode global \
  --enable-critical-role-repair \
  --disable-prm \
  --local-dtype float16 \
  --local-device-map auto \
  --local-max-model-len 4096 \
  --local-trust-remote-code

python /workspace/project/scripts/atlas_rg_main.py \
  --main-dirs \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/cluster_shard01 \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/cluster_shard02 \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/cluster_shard03 \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/cluster_shard04 \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/generic_shard01 \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/generic_shard02 \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/generic_shard03 \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/generic_shard04 \
  --offline-dir /workspace/project/results/atlas_rg_offline/full_pivotC_20260314 \
  --replay-dirs \
    /workspace/project/results/atlas_rg_main/replay_local_seed_20260314/shard01 \
    /workspace/project/results/atlas_rg_main/replay_local_seed_20260314/shard02 \
    /workspace/project/results/atlas_rg_main/replay_local_seed_20260314/shard03 \
    /workspace/project/results/atlas_rg_main/replay_local_seed_20260314/shard04 \
    /workspace/project/results/atlas_rg_main/replay_api_seed_20260314/shard01 \
    /workspace/project/results/atlas_rg_main/replay_api_seed_20260314/shard02 \
    /workspace/project/results/atlas_rg_main/replay_api_seed_20260314/shard03 \
    /workspace/project/results/atlas_rg_main/replay_api_seed_20260314/shard04 \
  --output-dir /workspace/project/results/atlas_rg_main/main_final_replayboth_20260314 \
  --hard-lambda 0.01 \
  --balanced-lambda 0.03

python /workspace/project/scripts/make_atlas_rg_reports.py \
  --calibration-dirs \
    /workspace/project/results/atlas_rg_calibration/hard_criticalrole_20260314/shard01 \
    /workspace/project/results/atlas_rg_calibration/hard_criticalrole_20260314/shard02 \
    /workspace/project/results/atlas_rg_calibration/hard_criticalrole_20260314/shard03 \
    /workspace/project/results/atlas_rg_calibration/hard_criticalrole_20260314/shard04 \
    /workspace/project/results/atlas_rg_calibration/easy_cal_fp16_20260314/shard01 \
    /workspace/project/results/atlas_rg_calibration/easy_cal_fp16_20260314/shard02 \
    /workspace/project/results/atlas_rg_calibration/easy_cal_fp16_20260314/shard03 \
    /workspace/project/results/atlas_rg_calibration/easy_cal_fp16_20260314/shard04 \
  --offline-dir /workspace/project/results/atlas_rg_offline/full_pivotC_20260314 \
  --main-dir /workspace/project/results/atlas_rg_main/main_final_replayboth_20260314 \
  --main-raw-dirs \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/cluster_shard01 \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/cluster_shard02 \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/cluster_shard03 \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/cluster_shard04 \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/generic_shard01 \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/generic_shard02 \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/generic_shard03 \
    /workspace/project/results/atlas_rg_main/main_api_seed_20260314/generic_shard04 \
  --initial-teacher-seed-dir /workspace/project/results/atlas_rg_api_diag/teacher_seed_gpt5mini_20260314_merged \
  --heldout-teacher-seed-dir /workspace/project/results/atlas_rg_api_diag/heldout_teacher_subset59_gpt5mini_20260314 \
  --heldout-teacher-eval-dir /workspace/project/results/atlas_rg_main/teacher_covered_api_20260314 \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/atlas_rg \
  --figure-dir /workspace/project/figures/atlas_rg
```

ATLAS-RG runtime / utilization notes:

- initial conservative estimate: `6–9h`
- observed heavy-run experimental window: about `3h05m` from first merged teacher seed to final replay summary
- hard calibration: about `25–27m`, active `sm` average about `84.7`
- easy calibration: about `11–12m`, active `sm` average about `91.1`
- held-out main: about `69m`, active `sm` average about `91.7`
- replay / teacher-covered diagnostics: active `sm` average about `93.4`
- dmon logs:
  - `/workspace/project/results/atlas_rg_calibration/logs/calibration_fp16_orch_dmon_20260314.log`
  - `/workspace/project/results/atlas_rg_calibration/logs/easy_cal_dmon_20260314.log`
  - `/workspace/project/results/atlas_rg_main/logs/main_api_seed_dmon_20260314.log`
  - `/workspace/project/results/atlas_rg_main/logs/replay_teacher_dmon_20260314.log`

ATLAS-RG current status:

- Supported:
  - on cluster-focused hard, multiple ATLAS-RG variants beat `RAW_PYTHON`
  - replay-controlled API seed quality specifically helps the role-grounded roletable path
  - quantity-role grounding is a real field-causal bottleneck
- Not supported:
  - ATLAS-RG beating `OPERATOR_SCHEMA_TO_CODE_BASE` as the new robust hard-set frontier
  - a claim that the remaining gap is purely role extraction

## ATLAS-MS minimal-sufficient-bundle branch

ATLAS-MS keeps the operator-schema execution backend fixed and asks a narrower replay-controlled question:

- which schema-field bundle is minimally sufficient?
- can an interacting bundle beat `RAW_PYTHON` and displace `OPERATOR_SCHEMA_TO_CODE_BASE` on the targeted hard clusters?

Environment used for the branch:

```bash
cd /workspace/project
source /workspace/project/.env.example
export HF_TOKEN="$HUGGINGFACE_HUB_TOKEN"
export PYTHONPATH=/workspace/project/src:${PYTHONPATH:-}
```

Manifest generation:

```bash
python /workspace/project/scripts/atlas_ms_make_manifests.py \
  --output-dir /workspace/project/data/atlas_ms_manifests_20260314a \
  --teacher-target-per-cluster 15 \
  --hard-cal-limit 180 \
  --easy-cal-limit 70 \
  --conditioning-hard-limit 90 \
  --cluster-main-target-per-cluster 34 \
  --cluster-main-limit 204 \
  --generic-hard-limit 140 \
  --heldout-teacher-limit 40 \
  --teacher-overlap-limit 75
```

API teacher full-bundle seed and held-out teacher subset:

```bash
python /workspace/project/scripts/atlas_ms_build_teacher_seed.py \
  --client openai \
  --manifest /workspace/project/data/atlas_ms_manifests_20260314a/gsm8k_train_teacher_seed.json \
  --output-dir /workspace/project/results/atlas_ms_api_diag/teacher_seed_gpt5mini_20260314 \
  --model-name gpt-5-mini

python /workspace/project/scripts/atlas_ms_build_teacher_seed.py \
  --client openai \
  --manifest /workspace/project/data/atlas_ms_manifests_20260314a/gsm8k_train_heldout_teacher_subset40.json \
  --output-dir /workspace/project/results/atlas_ms_api_diag/heldout_teacher_subset_gpt5mini_20260314 \
  --model-name gpt-5-mini
```

Primary local collection path:

```bash
MODEL=Qwen/Qwen2.5-7B-Instruct
SEED=/workspace/project/results/atlas_ms_api_diag/teacher_seed_gpt5mini_20260314_merged/teacher_seed.jsonl
MAN=/workspace/project/data/atlas_ms_manifests_20260314a/shards

CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/atlas_ms_collect_bundlebank.py \
  --client hf_local \
  --manifest ${MAN}/gsm8k_train_hard_calibration__shard01of04.json \
  --output-dir /workspace/project/results/atlas_ms_calibration/hard_cal_fp16_20260314/shard01 \
  --model-name ${MODEL} \
  --teacher-seed ${SEED} \
  --retrieval-mode cluster_first \
  --disable-prm \
  --local-dtype float16 \
  --local-device-map auto \
  --local-max-model-len 4096 \
  --local-trust-remote-code
```

Repeat the same command for shards `02/03/04`, then analogously for:

- `asdiv_easy_calibration`
- `gsm8k_train_hard_conditioning_problem_only`
- `gsm8k_train_cluster_main`
- `gsm8k_train_generic_main`
- replay-controlled `gsm8k_train_cluster_main` local-seed and API-seed reruns with `--frozen-drafts`

Offline aggregation:

```bash
python /workspace/project/scripts/atlas_ms_offline.py \
  --calibration-dirs \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fp16_20260314/shard01 \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fp16_20260314/shard02 \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fp16_20260314/shard03 \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fp16_20260314/shard04 \
    /workspace/project/results/atlas_ms_calibration/easy_cal_fp16_20260314/shard01 \
    /workspace/project/results/atlas_ms_calibration/easy_cal_fp16_20260314/shard02 \
    /workspace/project/results/atlas_ms_calibration/easy_cal_fp16_20260314/shard03 \
    /workspace/project/results/atlas_ms_calibration/easy_cal_fp16_20260314/shard04 \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fieldwise_compose_20260314/shard01 \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fieldwise_compose_20260314/shard02 \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fieldwise_compose_20260314/shard03 \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fieldwise_compose_20260314/shard04 \
  --teacher-eval-dirs \
    /workspace/project/results/atlas_ms_main/heldout_teacher_eval_20260314/shard01 \
    /workspace/project/results/atlas_ms_main/heldout_teacher_eval_20260314/shard02 \
    /workspace/project/results/atlas_ms_main/heldout_teacher_eval_20260314/shard03 \
    /workspace/project/results/atlas_ms_main/heldout_teacher_eval_20260314/shard04 \
  --problem-only-dirs \
    /workspace/project/results/atlas_ms_calibration/hard_conditioning_problemonly_20260314/shard01 \
    /workspace/project/results/atlas_ms_calibration/hard_conditioning_problemonly_20260314/shard02 \
    /workspace/project/results/atlas_ms_calibration/hard_conditioning_problemonly_20260314/shard03 \
    /workspace/project/results/atlas_ms_calibration/hard_conditioning_problemonly_20260314/shard04 \
  --output-dir /workspace/project/results/atlas_ms_offline/pivotB_fieldwise_20260314
```

Field-wise compose pivot and replay-controlled held-out aggregation:

```bash
set -euo pipefail
source /workspace/project/.env.example
export PYTHONPATH=/workspace/project/src:${PYTHONPATH:-}
export TOKENIZERS_PARALLELISM=false
SCRIPT=/workspace/project/scripts/atlas_ms_compose_fieldwise.py
MODEL=Qwen/Qwen2.5-7B-Instruct

run_phase() {
  phase_name="$1"
  input_base="$2"
  output_base="$3"
  for shard in 01 02 03 04; do
    gpu=$((10#$shard - 1))
    CUDA_VISIBLE_DEVICES="$gpu" python "$SCRIPT" \
      --input-dirs "$input_base/shard$shard" \
      --output-dir "$output_base/shard$shard" \
      --client hf_local \
      --model-name "$MODEL" \
      --local-quantization none \
      --local-dtype float16 \
      --local-device-map auto &
  done
  wait
}

run_phase main_fieldwise_compose \
  /workspace/project/results/atlas_ms_main/main_api_seed_20260314 \
  /workspace/project/results/atlas_ms_main/main_fieldwise_compose_20260314

run_phase replay_api_fieldwise_compose \
  /workspace/project/results/atlas_ms_main/replay_api_seed_20260314 \
  /workspace/project/results/atlas_ms_main/replay_api_fieldwise_compose_20260314

run_phase replay_local_fieldwise_compose \
  /workspace/project/results/atlas_ms_main/replay_local_seed_20260314 \
  /workspace/project/results/atlas_ms_main/replay_local_fieldwise_compose_20260314

python /workspace/project/scripts/atlas_ms_main.py \
  --main-dirs \
    /workspace/project/results/atlas_ms_main/main_api_seed_20260314/shard01 \
    /workspace/project/results/atlas_ms_main/main_api_seed_20260314/shard02 \
    /workspace/project/results/atlas_ms_main/main_api_seed_20260314/shard03 \
    /workspace/project/results/atlas_ms_main/main_api_seed_20260314/shard04 \
    /workspace/project/results/atlas_ms_main/main_fieldwise_compose_20260314/shard01 \
    /workspace/project/results/atlas_ms_main/main_fieldwise_compose_20260314/shard02 \
    /workspace/project/results/atlas_ms_main/main_fieldwise_compose_20260314/shard03 \
    /workspace/project/results/atlas_ms_main/main_fieldwise_compose_20260314/shard04 \
  --offline-dir /workspace/project/results/atlas_ms_offline/pivotB_fieldwise_20260314 \
  --teacher-eval-dirs \
    /workspace/project/results/atlas_ms_main/heldout_teacher_eval_20260314/shard01 \
    /workspace/project/results/atlas_ms_main/heldout_teacher_eval_20260314/shard02 \
    /workspace/project/results/atlas_ms_main/heldout_teacher_eval_20260314/shard03 \
    /workspace/project/results/atlas_ms_main/heldout_teacher_eval_20260314/shard04 \
  --replay-dirs \
    /workspace/project/results/atlas_ms_main/replay_api_seed_20260314/shard01 \
    /workspace/project/results/atlas_ms_main/replay_api_seed_20260314/shard02 \
    /workspace/project/results/atlas_ms_main/replay_api_seed_20260314/shard03 \
    /workspace/project/results/atlas_ms_main/replay_api_seed_20260314/shard04 \
    /workspace/project/results/atlas_ms_main/replay_local_seed_20260314/shard01 \
    /workspace/project/results/atlas_ms_main/replay_local_seed_20260314/shard02 \
    /workspace/project/results/atlas_ms_main/replay_local_seed_20260314/shard03 \
    /workspace/project/results/atlas_ms_main/replay_local_seed_20260314/shard04 \
    /workspace/project/results/atlas_ms_main/replay_api_fieldwise_compose_20260314/shard01 \
    /workspace/project/results/atlas_ms_main/replay_api_fieldwise_compose_20260314/shard02 \
    /workspace/project/results/atlas_ms_main/replay_api_fieldwise_compose_20260314/shard03 \
    /workspace/project/results/atlas_ms_main/replay_api_fieldwise_compose_20260314/shard04 \
    /workspace/project/results/atlas_ms_main/replay_local_fieldwise_compose_20260314/shard01 \
    /workspace/project/results/atlas_ms_main/replay_local_fieldwise_compose_20260314/shard02 \
    /workspace/project/results/atlas_ms_main/replay_local_fieldwise_compose_20260314/shard03 \
    /workspace/project/results/atlas_ms_main/replay_local_fieldwise_compose_20260314/shard04 \
  --output-dir /workspace/project/results/atlas_ms_main/main_pivotB_fieldwise_20260314
```

Report generation:

```bash
python /workspace/project/scripts/make_atlas_ms_reports.py \
  --calibration-dirs \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fp16_20260314/shard01 \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fp16_20260314/shard02 \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fp16_20260314/shard03 \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fp16_20260314/shard04 \
    /workspace/project/results/atlas_ms_calibration/easy_cal_fp16_20260314/shard01 \
    /workspace/project/results/atlas_ms_calibration/easy_cal_fp16_20260314/shard02 \
    /workspace/project/results/atlas_ms_calibration/easy_cal_fp16_20260314/shard03 \
    /workspace/project/results/atlas_ms_calibration/easy_cal_fp16_20260314/shard04 \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fieldwise_compose_20260314/shard01 \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fieldwise_compose_20260314/shard02 \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fieldwise_compose_20260314/shard03 \
    /workspace/project/results/atlas_ms_calibration/hard_cal_fieldwise_compose_20260314/shard04 \
  --offline-dir /workspace/project/results/atlas_ms_offline/pivotB_fieldwise_20260314 \
  --main-dir /workspace/project/results/atlas_ms_main/main_pivotB_fieldwise_20260314 \
  --main-raw-dirs \
    /workspace/project/results/atlas_ms_main/main_api_seed_20260314/shard01 \
    /workspace/project/results/atlas_ms_main/main_api_seed_20260314/shard02 \
    /workspace/project/results/atlas_ms_main/main_api_seed_20260314/shard03 \
    /workspace/project/results/atlas_ms_main/main_api_seed_20260314/shard04 \
    /workspace/project/results/atlas_ms_main/main_fieldwise_compose_20260314/shard01 \
    /workspace/project/results/atlas_ms_main/main_fieldwise_compose_20260314/shard02 \
    /workspace/project/results/atlas_ms_main/main_fieldwise_compose_20260314/shard03 \
    /workspace/project/results/atlas_ms_main/main_fieldwise_compose_20260314/shard04 \
  --teacher-seed-dir /workspace/project/results/atlas_ms_api_diag/teacher_seed_gpt5mini_20260314_merged \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/atlas_ms \
  --figure-dir /workspace/project/figures/atlas_ms
```

ATLAS-MS runtime / utilization notes:

- measured compose-phase wall-clock:
  - hard calibration field-wise compose: `270s`
  - held-out main field-wise compose: `462s`
  - replay API field-wise compose: `245s`
  - replay local field-wise compose: `196s`
- earlier long phases:
  - main API-seed collection: `5292s`
  - replay local-seed collection: `1370s`
  - held-out teacher eval: `357s`
  - conditioning problem-only subset: `428s`
- active-window `sm` averages from the new compose dmon logs:
  - main field-wise compose: about `92.7`
  - replay API field-wise compose: about `88.7`
  - replay local field-wise compose: about `86.5`

ATLAS-MS current status:

- Supported:
  - bundle methods beat `RAW_PYTHON` on the cluster-focused hard surface
  - role-only is not the full answer
  - target/postprocess-bearing bundles recur among the strongest methods
- Not supported:
  - any bundle displacing `OPERATOR_SCHEMA_TO_CODE_BASE` as the robust held-out hard frontier
  - the claim that stronger API teacher extraction alone fixes the remaining gap
- Strongest surviving ATLAS-MS story:
  - minimal bundle interactions matter, but the robust hard-set frontier still belongs to the simpler frozen operator-schema baseline

## CASS

CASS (`Conservative Arithmetic Schema Surgery`) freezes `OPERATOR_SCHEMA_TO_CODE_BASE` and patches only suspicious target/postprocess and role fields. The completed branch lives in:

- reports:
  - `/workspace/project/reports/cass_plan.md`
  - `/workspace/project/reports/cass_patch_audit.md`
  - `/workspace/project/reports/cass_teacher_audit.md`
  - `/workspace/project/reports/cass_patchbank_report.md`
  - `/workspace/project/reports/cass_offline_report.md`
  - `/workspace/project/reports/cass_main_report.md`
  - `/workspace/project/reports/cass_failure_notes.md`
  - `/workspace/project/reports/cass_next_step_memo.md`
- results:
  - `/workspace/project/results/cass_api_diag/teacher_seed_gpt5mini_20260315_merged`
  - `/workspace/project/results/cass_offline/offline_full_clusterfirst_20260315`
  - `/workspace/project/results/cass_main/main_clusterfirst_20260315`

Environment setup:

```bash
set -euo pipefail
source /workspace/project/.env.example
export HF_TOKEN="${HUGGINGFACE_HUB_TOKEN:-}"
export PYTHONPATH=/workspace/project/src:${PYTHONPATH:-}
export TOKENIZERS_PARALLELISM=false
MODEL=Qwen/Qwen2.5-7B-Instruct
MAN=/workspace/project/data/cass_manifests_20260315b/shards
SEED=/workspace/project/results/cass_api_diag/teacher_seed_gpt5mini_20260315_merged/teacher_seed.jsonl
```

Build fresh manifests:

```bash
python /workspace/project/scripts/cass_make_manifests.py \
  --output-dir /workspace/project/data/cass_manifests_20260315b
```

API teacher seed and held-out teacher subset:

```bash
run_teacher_phase() {
  phase_name="$1"
  prefix="$2"
  out_base="$3"
  for shard in 01 02 03 04; do
    gpu=$((10#$shard - 1))
    CUDA_VISIBLE_DEVICES="$gpu" python /workspace/project/scripts/cass_build_teacher_seed.py \
      --manifest "${MAN}/${prefix}__shard${shard}of04.json" \
      --output-dir "${out_base}_shard${shard}of04" \
      --local-client hf_local \
      --local-model-name "$MODEL" \
      --api-model-name gpt-5-mini \
      --local-quantization none \
      --local-dtype float16 \
      --local-device-map auto \
      --local-max-model-len 4096 \
      --local-trust-remote-code &
  done
  wait
}

run_teacher_phase teacher_seed \
  gsm8k_train_teacher_seed \
  /workspace/project/results/cass_api_diag/teacher_seed_gpt5mini_20260315

run_teacher_phase heldout_teacher_subset \
  gsm8k_train_cluster_teacher_subset \
  /workspace/project/results/cass_api_diag/heldout_teacher_subset_gpt5mini_20260315
```

Primary local collection:

```bash
run_cass_collect() {
  prefix="$1"
  out_base="$2"
  extra_args="${3:-}"
  for shard in 01 02 03 04; do
    gpu=$((10#$shard - 1))
    CUDA_VISIBLE_DEVICES="$gpu" python /workspace/project/scripts/cass_collect_patchbank.py \
      --client hf_local \
      --manifest "${MAN}/${prefix}__shard${shard}of04.json" \
      --output-dir "${out_base}_shard${shard}of04" \
      --model-name "$MODEL" \
      --teacher-seed "$SEED" \
      --retrieval-mode cluster_first \
      --disable-prm \
      --local-quantization none \
      --local-dtype float16 \
      --local-device-map auto \
      --local-max-model-len 4096 \
      --local-trust-remote-code \
      ${extra_args} &
  done
  wait
}

run_cass_collect gsm8k_train_calibration \
  /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_hard

run_cass_collect asdiv_calibration \
  /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_easy

run_cass_collect gsm8k_train_cluster_main \
  /workspace/project/results/cass_main/cluster_main_teacher_20260315

run_cass_collect gsm8k_train_generic_main \
  /workspace/project/results/cass_main/generic_main_teacher_20260315

run_cass_collect asdiv_easy_main \
  /workspace/project/results/cass_main/easy_main_teacher_20260315

for shard in 01 02 03 04; do
  gpu=$((10#$shard - 1))
  CUDA_VISIBLE_DEVICES="$gpu" python /workspace/project/scripts/cass_collect_patchbank.py \
    --client hf_local \
    --manifest "${MAN}/gsm8k_train_cluster_main__shard${shard}of04.json" \
    --output-dir "/workspace/project/results/cass_main/replay_local_cluster_20260315_shard${shard}of04" \
    --model-name "$MODEL" \
    --teacher-seed "$SEED" \
    --retrieval-mode cluster_first \
    --disable-prm \
    --local-quantization none \
    --local-dtype float16 \
    --local-device-map auto \
    --local-max-model-len 4096 \
    --local-trust-remote-code \
    --frozen-drafts "/workspace/project/results/cass_main/cluster_main_teacher_drafts_shard${shard}of04.jsonl" &
done
wait
```

Offline aggregation:

```bash
python /workspace/project/scripts/cass_offline.py \
  --calibration-dirs \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_hard_shard01of04 \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_hard_shard02of04 \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_hard_shard03of04 \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_hard_shard04of04 \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_easy_shard01of04 \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_easy_shard02of04 \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_easy_shard03of04 \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_easy_shard04of04 \
  --teacher-eval-dirs \
    /workspace/project/results/cass_api_diag/heldout_teacher_eval_20260315_merged \
  --output-dir /workspace/project/results/cass_offline/offline_full_clusterfirst_20260315
```

Held-out main aggregation:

```bash
python /workspace/project/scripts/cass_main.py \
  --main-dirs \
    /workspace/project/results/cass_main/cluster_main_teacher_20260315_shard01of04 \
    /workspace/project/results/cass_main/cluster_main_teacher_20260315_shard02of04 \
    /workspace/project/results/cass_main/cluster_main_teacher_20260315_shard03of04 \
    /workspace/project/results/cass_main/cluster_main_teacher_20260315_shard04of04 \
    /workspace/project/results/cass_main/generic_main_teacher_20260315_shard01of04 \
    /workspace/project/results/cass_main/generic_main_teacher_20260315_shard02of04 \
    /workspace/project/results/cass_main/generic_main_teacher_20260315_shard03of04 \
    /workspace/project/results/cass_main/generic_main_teacher_20260315_shard04of04 \
    /workspace/project/results/cass_main/easy_main_teacher_20260315_shard01of04 \
    /workspace/project/results/cass_main/easy_main_teacher_20260315_shard02of04 \
    /workspace/project/results/cass_main/easy_main_teacher_20260315_shard03of04 \
    /workspace/project/results/cass_main/easy_main_teacher_20260315_shard04of04 \
  --offline-dir /workspace/project/results/cass_offline/offline_full_clusterfirst_20260315 \
  --teacher-eval-dirs /workspace/project/results/cass_api_diag/heldout_teacher_eval_20260315_merged \
  --replay-dirs \
    /workspace/project/results/cass_main/replay_local_cluster_20260315_shard01of04 \
    /workspace/project/results/cass_main/replay_local_cluster_20260315_shard02of04 \
    /workspace/project/results/cass_main/replay_local_cluster_20260315_shard03of04 \
    /workspace/project/results/cass_main/replay_local_cluster_20260315_shard04of04 \
  --output-dir /workspace/project/results/cass_main/main_clusterfirst_20260315
```

Report generation:

```bash
python /workspace/project/scripts/make_cass_reports.py \
  --calibration-dirs \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_hard_shard01of04 \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_hard_shard02of04 \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_hard_shard03of04 \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_hard_shard04of04 \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_easy_shard01of04 \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_easy_shard02of04 \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_easy_shard03of04 \
    /workspace/project/results/cass_calibration/calibration_clusterfirst_20260315_easy_shard04of04 \
  --offline-dir /workspace/project/results/cass_offline/offline_full_clusterfirst_20260315 \
  --main-dir /workspace/project/results/cass_main/main_clusterfirst_20260315 \
  --main-raw-dirs \
    /workspace/project/results/cass_main/cluster_main_teacher_20260315_shard01of04 \
    /workspace/project/results/cass_main/cluster_main_teacher_20260315_shard02of04 \
    /workspace/project/results/cass_main/cluster_main_teacher_20260315_shard03of04 \
    /workspace/project/results/cass_main/cluster_main_teacher_20260315_shard04of04 \
    /workspace/project/results/cass_main/generic_main_teacher_20260315_shard01of04 \
    /workspace/project/results/cass_main/generic_main_teacher_20260315_shard02of04 \
    /workspace/project/results/cass_main/generic_main_teacher_20260315_shard03of04 \
    /workspace/project/results/cass_main/generic_main_teacher_20260315_shard04of04 \
    /workspace/project/results/cass_main/easy_main_teacher_20260315_shard01of04 \
    /workspace/project/results/cass_main/easy_main_teacher_20260315_shard02of04 \
    /workspace/project/results/cass_main/easy_main_teacher_20260315_shard03of04 \
    /workspace/project/results/cass_main/easy_main_teacher_20260315_shard04of04 \
  --teacher-seed-dir /workspace/project/results/cass_api_diag/teacher_seed_gpt5mini_20260315_merged \
  --heldout-teacher-eval-dir /workspace/project/results/cass_api_diag/heldout_teacher_eval_20260315_merged \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/cass \
  --figure-dir /workspace/project/figures/cass
```

CASS final headline:

- cluster-hard:
  - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH = 0.771429`
  - `RAW_PYTHON = 0.738095`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.728571`
- generic-hard:
  - `CASS_TARGET_POSTPROCESS_PATCH = 0.842857`
  - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH = 0.842857`
  - `RAW_PYTHON = 0.814286`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.778571`
- teacher-covered subset:
  - `TEACHER_PATCHED_BASELINE = 0.825`
- runtime:
  - teacher seed -> final main: about `3h08m`
  - active cluster-hard main GPU `sm`: roughly `90–96%` on all `4` GPUs

## CASS-R2

CASS-R2 is the bounded confirmation and direct-comparison phase for CASS. It keeps the CASS patch family frozen and asks only whether the CASS effect can be statistically locked against the closest inference-time comparators on the same hard arithmetic surfaces.

Final outcome:

- primary cluster-hard (`n=800`):
  - `CASS_CONSERVATIVE_GATE = 0.74875`
  - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH = 0.74875`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.73000`
  - `RAW_PYTHON = 0.69750`
  - `PRISM_LITE = 0.69750`
  - `F1_LITE = 0.61750`
- generic-hard (`n=300`):
  - `CASS_CONSERVATIVE_GATE = 0.78333`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.73667`
  - `RAW_PYTHON = 0.71667`
- registered cluster-hard pairwise read:
  - `CASS_CONSERVATIVE_GATE - RAW_PYTHON = +0.0509`, `95% CI [0.0225, 0.0800]`
  - `CASS_CONSERVATIVE_GATE - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0186`, `95% CI [-0.0075, 0.0463]`
- interpretation:
  - the CASS confirmation story is robust versus `RAW_PYTHON`, `PRISM_LITE`, and `F1_LITE`
  - but it is not yet statistically locked versus the frozen operator-schema baseline on the preregistered primary surface

Key artifacts:

- reports:
  - `/workspace/project/reports/cass_r2_plan.md`
  - `/workspace/project/reports/cass_r2_comparator_audit.md`
  - `/workspace/project/reports/cass_r2_power_plan.md`
  - `/workspace/project/reports/cass_r2_headroom_screen.md`
  - `/workspace/project/reports/cass_r2_main_report.md`
  - `/workspace/project/reports/cass_r2_comparator_report.md`
  - `/workspace/project/reports/cass_r2_failure_notes.md`
  - `/workspace/project/reports/cass_r2_final_lock_memo.md`
- results:
  - `/workspace/project/results/cass_r2_main/power_plan_20260315`
  - `/workspace/project/results/cass_r2_main/headroom_screen_20260315`
  - `/workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard01of04`
  - `/workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard02of04`
  - `/workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard03of04`
  - `/workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard04of04`
  - `/workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard01of04`
  - `/workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard02of04`
  - `/workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard03of04`
  - `/workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard04of04`
  - `/workspace/project/results/cass_r2_main/main_20260315a`
  - `/workspace/project/results/cass_r2_comparators/comparator_pack_20260315a`

Environment setup:

```bash
set -euo pipefail
source /workspace/project/.env.example
export HF_TOKEN="${HUGGINGFACE_HUB_TOKEN:-}"
export PYTHONPATH=/workspace/project/src:${PYTHONPATH:-}
export TOKENIZERS_PARALLELISM=false
MODEL=Qwen/Qwen2.5-7B-Instruct
SEED=/workspace/project/results/cass_api_diag/teacher_seed_gpt5mini_20260315_merged/teacher_seed.jsonl
```

Build the confirmation manifests:

```bash
python /workspace/project/scripts/cass_r2_make_manifests.py \
  --output-dir /workspace/project/data/cass_r2_manifests_20260315a

python /workspace/project/scripts/cass_r2_compose_manifests.py \
  --manifests \
    /workspace/project/data/cass_r2_manifests_20260315a/gsm8k_train_cluster_main_r2.json \
    /workspace/project/data/cass_r2_manifests_20260315a/gsm8k_train_generic_main_r2.json \
  --output-dir /workspace/project/data/cass_r2_main_compose_20260315a \
  --stem gsm8k_train_cluster_generic_main_r2 \
  --nshards 4
```

Power analysis from the frozen CASS result:

```bash
python /workspace/project/scripts/cass_r2_power.py \
  --cass-main-dir /workspace/project/results/cass_main/main_clusterfirst_20260315 \
  --output-dir /workspace/project/results/cass_r2_main/power_plan_20260315 \
  --report-path /workspace/project/reports/cass_r2_power_plan.md
```

Bounded transfer headroom screen:

```bash
MAN=/workspace/project/data/cass_r2_manifests_20260315a/shards

run_cass_r2_screen() {
  prefix="$1"
  out_base="$2"
  for shard in 01 02 03 04; do
    gpu=$((10#$shard - 1))
    CUDA_VISIBLE_DEVICES="$gpu" python /workspace/project/scripts/cass_r2_collect.py \
      --client hf_local \
      --manifest "${MAN}/${prefix}__shard${shard}of04.json" \
      --output-dir "${out_base}_shard${shard}of04" \
      --model-name "$MODEL" \
      --teacher-seed "$SEED" \
      --retrieval-mode cluster_first \
      --disable-prm \
      --local-quantization none \
      --local-dtype float16 \
      --local-device-map auto \
      --local-max-model-len 4096 \
      --local-trust-remote-code &
  done
  wait
}

run_cass_r2_screen mawps_cluster_headroom_screen \
  /workspace/project/results/cass_r2_main/mawps_headroom_20260315

run_cass_r2_screen asdiv_cluster_headroom_screen \
  /workspace/project/results/cass_r2_main/asdiv_headroom_20260315

python /workspace/project/scripts/cass_r2_headroom.py \
  --screen-dirs \
    /workspace/project/results/cass_r2_main/mawps_headroom_20260315_shard01of04 \
    /workspace/project/results/cass_r2_main/mawps_headroom_20260315_shard02of04 \
    /workspace/project/results/cass_r2_main/mawps_headroom_20260315_shard03of04 \
    /workspace/project/results/cass_r2_main/mawps_headroom_20260315_shard04of04 \
    /workspace/project/results/cass_r2_main/asdiv_headroom_20260315_shard01of04 \
    /workspace/project/results/cass_r2_main/asdiv_headroom_20260315_shard02of04 \
    /workspace/project/results/cass_r2_main/asdiv_headroom_20260315_shard03of04 \
    /workspace/project/results/cass_r2_main/asdiv_headroom_20260315_shard04of04 \
  --output-dir /workspace/project/results/cass_r2_main/headroom_screen_20260315 \
  --report-path /workspace/project/reports/cass_r2_headroom_screen.md
```

Large-scale local confirmation run with the direct comparators in the same replay-controlled records:

```bash
MAN=/workspace/project/data/cass_r2_main_compose_20260315a/shards
OUT_BASE=/workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a
mkdir -p /workspace/project/results/cass_r2_main/dmon_20260315a

(timeout 900 nvidia-smi dmon -s um -d 5 -o TD > /workspace/project/results/cass_r2_main/dmon_20260315a/gsm8k_cluster_generic_early.txt 2>&1) &
(sleep 2700; timeout 900 nvidia-smi dmon -s um -d 5 -o TD > /workspace/project/results/cass_r2_main/dmon_20260315a/gsm8k_cluster_generic_mid.txt 2>&1) &

for shard in 01 02 03 04; do
  gpu=$((10#$shard - 1))
  CUDA_VISIBLE_DEVICES="$gpu" python /workspace/project/scripts/cass_r2_collect.py \
    --client hf_local \
    --manifest "${MAN}/gsm8k_train_cluster_generic_main_r2__shard${shard}of04.json" \
    --output-dir "${OUT_BASE}_shard${shard}of04" \
    --model-name "$MODEL" \
    --teacher-seed "$SEED" \
    --retrieval-mode cluster_first \
    --disable-prm \
    --local-quantization none \
    --local-dtype float16 \
    --local-device-map auto \
    --local-max-model-len 4096 \
    --local-trust-remote-code &
done
wait
```

If the preregistered cluster-hard stopping rule is still not locked after the first `500` examples, extend the cluster manifest to the full `800` target and rerun only the fresh cluster remainder:

```bash
python /workspace/project/scripts/cass_r2_extend_cluster_manifest.py \
  --base-cluster-manifest /workspace/project/data/cass_r2_manifests_20260315a/gsm8k_train_cluster_main_r2.json \
  --generic-manifest /workspace/project/data/cass_r2_manifests_20260315a/gsm8k_train_generic_main_r2.json \
  --target-total 800 \
  --output-dir /workspace/project/data/cass_r2_cluster_ext_20260315a

MAN=/workspace/project/data/cass_r2_cluster_ext_20260315a/shards
OUT_BASE=/workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a
mkdir -p /workspace/project/results/cass_r2_main/dmon_ext_20260315a

(timeout 900 nvidia-smi dmon -s um -d 5 -o TD > /workspace/project/results/cass_r2_main/dmon_ext_20260315a/gsm8k_cluster_ext300_early.txt 2>&1) &
(sleep 1800; timeout 900 nvidia-smi dmon -s um -d 5 -o TD > /workspace/project/results/cass_r2_main/dmon_ext_20260315a/gsm8k_cluster_ext300_mid.txt 2>&1) &

for shard in 01 02 03 04; do
  gpu=$((10#$shard - 1))
  CUDA_VISIBLE_DEVICES="$gpu" python /workspace/project/scripts/cass_r2_collect.py \
    --client hf_local \
    --manifest "${MAN}/gsm8k_train_cluster_main_r2_ext300__shard${shard}of04.json" \
    --output-dir "${OUT_BASE}_shard${shard}of04" \
    --model-name "$MODEL" \
    --teacher-seed "$SEED" \
    --retrieval-mode cluster_first \
    --disable-prm \
    --local-quantization none \
    --local-dtype float16 \
    --local-device-map auto \
    --local-max-model-len 4096 \
    --local-trust-remote-code &
done
wait
```

Aggregation and report generation:

```bash
python /workspace/project/scripts/cass_r2_main.py \
  --main-dirs \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard01of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard02of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard03of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard04of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard01of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard02of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard03of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard04of04 \
  --cluster-manifest /workspace/project/data/cass_r2_cluster_ext_20260315a/gsm8k_train_cluster_main_r2_full800.json \
  --generic-manifest /workspace/project/data/cass_r2_manifests_20260315a/gsm8k_train_generic_main_r2.json \
  --output-dir /workspace/project/results/cass_r2_main/main_20260315a

python /workspace/project/scripts/make_cass_r2_reports.py \
  --main-dir /workspace/project/results/cass_r2_main/main_20260315a \
  --power-dir /workspace/project/results/cass_r2_main/power_plan_20260315 \
  --headroom-dir /workspace/project/results/cass_r2_main/headroom_screen_20260315 \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/cass_r2 \
  --figure-dir /workspace/project/figures/cass_r2

mkdir -p /workspace/project/results/cass_r2_comparators/comparator_pack_20260315a
cp -f \
  /workspace/project/results/cass_r2_main/main_20260315a/comparator_summary.csv \
  /workspace/project/results/cass_r2_main/main_20260315a/pairwise.csv \
  /workspace/project/results/cass_r2_main/main_20260315a/summary.csv \
  /workspace/project/results/cass_r2_main/main_20260315a/summary.md \
  /workspace/project/results/cass_r2_main/main_20260315a/manifest.json \
  /workspace/project/results/cass_r2_comparators/comparator_pack_20260315a/
cp -f \
  /workspace/project/reports/cass_r2_comparator_report.md \
  /workspace/project/results/cass_r2_comparators/comparator_pack_20260315a/summary.md
```

## CASS-R3 lock-and-compare continuation

Build the fresh-GSM manifests and the fresh-vs-feasible power plan:

```bash
python /workspace/project/scripts/cass_r3_make_manifests.py \
  --output-dir /workspace/project/data/cass_r3_manifests_20260315a

python /workspace/project/scripts/cass_r3_power.py \
  --cass-r2-main-dir /workspace/project/results/cass_r2_main/main_20260315a \
  --fresh-cluster-manifest /workspace/project/data/cass_r3_manifests_20260315a/gsm8k_train_cluster_main_r3_fresh715.json \
  --output-dir /workspace/project/results/cass_r3_main/power_plan_20260315a \
  --report-path /workspace/project/reports/cass_r3_power_plan.md
```

Run the bounded transfer headroom screen:

```bash
source /workspace/project/.env.example
export HF_TOKEN="$HUGGINGFACE_HUB_TOKEN"
export PYTHONPATH=/workspace/project/src:${PYTHONPATH:-}

run_cass_r3_screen() {
  local manifest="$1"
  local out_base="$2"
  local model="Qwen/Qwen2.5-7B-Instruct"
  for shard in 01 02 03 04; do
    local gpu=$((10#$shard - 1))
    CUDA_VISIBLE_DEVICES="$gpu" python /workspace/project/scripts/cass_r2_collect.py \
      --client hf_local \
      --manifest "/workspace/project/data/cass_r3_manifests_20260315a/shards/${manifest}__shard${shard}of04.json" \
      --output-dir "${out_base}_shard${shard}of04" \
      --model-name "$model" \
      --teacher-seed /workspace/project/results/cass_api_diag/teacher_seed_gpt5mini_20260315_merged/teacher_seed.jsonl \
      --retrieval-mode cluster_first \
      --disable-prm \
      --local-quantization none \
      --local-dtype float16 \
      --local-device-map auto \
      --local-max-model-len 4096 \
      --local-trust-remote-code &
  done
  wait
}

run_cass_r3_screen mawps_cluster_headroom_screen \
  /workspace/project/results/cass_r3_main/mawps_headroom_20260315a
run_cass_r3_screen asdiv_cluster_headroom_screen \
  /workspace/project/results/cass_r3_main/asdiv_headroom_20260315a

python /workspace/project/scripts/cass_r3_headroom.py \
  --screen-dirs \
    /workspace/project/results/cass_r3_main/mawps_headroom_20260315a_shard01of04 \
    /workspace/project/results/cass_r3_main/mawps_headroom_20260315a_shard02of04 \
    /workspace/project/results/cass_r3_main/mawps_headroom_20260315a_shard03of04 \
    /workspace/project/results/cass_r3_main/mawps_headroom_20260315a_shard04of04 \
    /workspace/project/results/cass_r3_main/asdiv_headroom_20260315a_shard01of04 \
    /workspace/project/results/cass_r3_main/asdiv_headroom_20260315a_shard02of04 \
    /workspace/project/results/cass_r3_main/asdiv_headroom_20260315a_shard03of04 \
    /workspace/project/results/cass_r3_main/asdiv_headroom_20260315a_shard04of04 \
  --datasets mawps asdiv svamp multiarith \
  --output-dir /workspace/project/results/cass_r3_main/headroom_screen_20260315a \
  --report-path /workspace/project/reports/cass_r3_headroom_screen.md
```

Compose the fresh main manifests and run the frozen CASS family plus frozen comparators:

```bash
python /workspace/project/scripts/cass_r2_compose_manifests.py \
  --manifests \
    /workspace/project/data/cass_r3_manifests_20260315a/gsm8k_train_cluster_main_r3_fresh715.json \
    /workspace/project/data/cass_r3_manifests_20260315a/gsm8k_train_generic_main_r3_fresh.json \
  --output-dir /workspace/project/data/cass_r3_main_compose_20260315a \
  --stem gsm8k_train_cluster_generic_main_r3_fresh \
  --nshards 4

source /workspace/project/.env.example
export HF_TOKEN="$HUGGINGFACE_HUB_TOKEN"
export PYTHONPATH=/workspace/project/src:${PYTHONPATH:-}
export TOKENIZERS_PARALLELISM=false
MODEL=Qwen/Qwen2.5-7B-Instruct
SEED=/workspace/project/results/cass_api_diag/teacher_seed_gpt5mini_20260315_merged/teacher_seed.jsonl
MAN=/workspace/project/data/cass_r3_main_compose_20260315a/shards
OUT_BASE=/workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a
mkdir -p /workspace/project/results/cass_r3_main/dmon_20260315r3a

(timeout 900 nvidia-smi dmon -s um -d 5 -o TD > /workspace/project/results/cass_r3_main/dmon_20260315r3a/gsm8k_cluster_generic_early.txt 2>&1) &
(sleep 5400; timeout 900 nvidia-smi dmon -s um -d 5 -o TD > /workspace/project/results/cass_r3_main/dmon_20260315r3a/gsm8k_cluster_generic_mid.txt 2>&1) &

for shard in 01 02 03 04; do
  gpu=$((10#$shard - 1))
  CUDA_VISIBLE_DEVICES="$gpu" python /workspace/project/scripts/cass_r2_collect.py \
    --client hf_local \
    --manifest "${MAN}/gsm8k_train_cluster_generic_main_r3_fresh__shard${shard}of04.json" \
    --output-dir "${OUT_BASE}_shard${shard}of04" \
    --model-name "$MODEL" \
    --teacher-seed "$SEED" \
    --retrieval-mode cluster_first \
    --disable-prm \
    --local-quantization none \
    --local-dtype float16 \
    --local-device-map auto \
    --local-max-model-len 4096 \
    --local-trust-remote-code &
done
wait
```

Aggregate the combined R2+R3 surfaces and generate reports, tables, figures, and comparator pack:

```bash
python /workspace/project/scripts/cass_r3_main.py \
  --main-dirs \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard01of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard02of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard03of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard04of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard01of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard02of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard03of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard04of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard01of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard02of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard03of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard04of04 \
  --cluster-manifest /workspace/project/data/cass_r3_manifests_20260315a/gsm8k_train_cluster_main_r3_full1515.json \
  --generic-manifest /workspace/project/data/cass_r3_manifests_20260315a/gsm8k_train_generic_main_r3_full.json \
  --output-dir /workspace/project/results/cass_r3_main/main_20260315a

python /workspace/project/scripts/make_cass_r3_reports.py \
  --main-dir /workspace/project/results/cass_r3_main/main_20260315a \
  --power-dir /workspace/project/results/cass_r3_main/power_plan_20260315a \
  --headroom-dir /workspace/project/results/cass_r3_main/headroom_screen_20260315a \
  --raw-dirs \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard01of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard02of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard03of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard04of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard01of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard02of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard03of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard04of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard01of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard02of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard03of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard04of04 \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/cass_r3 \
  --figure-dir /workspace/project/figures/cass_r3

mkdir -p /workspace/project/results/cass_r3_comparators/comparator_pack_20260315a
cp -f \
  /workspace/project/results/cass_r3_main/main_20260315a/comparator_summary.csv \
  /workspace/project/results/cass_r3_main/main_20260315a/pairwise.csv \
  /workspace/project/results/cass_r3_main/main_20260315a/summary.csv \
  /workspace/project/results/cass_r3_main/main_20260315a/summary.md \
  /workspace/project/results/cass_r3_main/main_20260315a/manifest.json \
  /workspace/project/results/cass_r3_comparators/comparator_pack_20260315a/
cp -f \
  /workspace/project/reports/cass_r3_comparator_report.md \
  /workspace/project/results/cass_r3_comparators/comparator_pack_20260315a/summary.md
```

## CASS-R4 fairness-and-generalization pack

Environment:

```bash
source /workspace/project/.env.example
export HF_TOKEN="${HUGGINGFACE_HUB_TOKEN:-}"
export PYTHONPATH=/workspace/project/src:${PYTHONPATH:-}
export TOKENIZERS_PARALLELISM=false
```

Build the `CASS-R4` manifest pack:

```bash
python /workspace/project/scripts/cass_r4_make_manifests.py \
  --output-dir /workspace/project/data/cass_r4_manifests_20260315a \
  --gsm8k-prism-limit 500 \
  --svamp-prism-limit 150 \
  --asdiv-prism-limit 150 \
  --gsm8k-f1-bridge-limit 120 \
  --asdiv-f1-bridge-limit 80 \
  --model-cluster-limit 300 \
  --model-generic-limit 150
```

Augment the frozen primary `CASS-R3` surface with `F1_HIGH_FIDELITY`:

```bash
python /workspace/project/scripts/cass_r4_augment_f1.py \
  --client hf_local \
  --model-name Qwen/Qwen2.5-7B-Instruct \
  --input-dirs \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard01of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard02of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard03of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_ext300_20260315a_shard04of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard01of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard02of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard03of04 \
    /workspace/project/results/cass_r2_main/gsm8k_cluster_generic_20260315a_shard04of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard01of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard02of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard03of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard04of04 \
  --output-root /workspace/project/results/cass_r4_main/qwen7b_primary_f1aug_20260315a
```

Collect the PRISM fairness surface and F1 bridge slice under the primary local model:

```bash
MODEL=Qwen/Qwen2.5-7B-Instruct
TEACHER=/workspace/project/results/cass_api_diag/teacher_seed_gpt5mini_20260315_merged/teacher_seed.jsonl
MROOT=/workspace/project/data/cass_r4_manifests_20260315a/shards

CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --manifest "$MROOT/gsm8k_prism_mixed_eval__shard01of04.json" \
  --output-dir /workspace/project/results/cass_r4_prism/qwen7b_mixed_20260315a/gsm8k_prism_mixed_eval_part01of02 \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
CUDA_VISIBLE_DEVICES=1 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --manifest "$MROOT/gsm8k_prism_mixed_eval__shard02of04.json" \
  --output-dir /workspace/project/results/cass_r4_prism/qwen7b_mixed_20260315a/gsm8k_prism_mixed_eval_part02of02 \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
CUDA_VISIBLE_DEVICES=2 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --manifest "$MROOT/svamp_prism_mixed_eval__shard01of04.json" \
  --output-dir /workspace/project/results/cass_r4_prism/qwen7b_mixed_20260315a/svamp_prism_mixed_eval \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
CUDA_VISIBLE_DEVICES=3 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --manifest "$MROOT/asdiv_prism_mixed_eval__shard01of04.json" \
  --output-dir /workspace/project/results/cass_r4_prism/qwen7b_mixed_20260315a/asdiv_prism_mixed_eval \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
wait

CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --manifest "$MROOT/gsm8k_f1_bridge_eval__shard01of04.json" \
  --output-dir /workspace/project/results/cass_r4_f1/qwen7b_bridge_20260315a/gsm8k_f1_bridge_eval_part01of02 \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
CUDA_VISIBLE_DEVICES=1 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --manifest "$MROOT/gsm8k_f1_bridge_eval__shard02of04.json" \
  --output-dir /workspace/project/results/cass_r4_f1/qwen7b_bridge_20260315a/gsm8k_f1_bridge_eval_part02of02 \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
CUDA_VISIBLE_DEVICES=2 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --manifest "$MROOT/asdiv_f1_bridge_eval__shard01of04.json" \
  --output-dir /workspace/project/results/cass_r4_f1/qwen7b_bridge_20260315a/asdiv_f1_bridge_eval_part01of02 \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
CUDA_VISIBLE_DEVICES=3 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --manifest "$MROOT/asdiv_f1_bridge_eval__shard02of04.json" \
  --output-dir /workspace/project/results/cass_r4_f1/qwen7b_bridge_20260315a/asdiv_f1_bridge_eval_part02of02 \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
wait
```

Run the reduced model-diversity pack under `Qwen/Qwen2.5-Math-7B-Instruct`:

```bash
MODEL=Qwen/Qwen2.5-Math-7B-Instruct
TEACHER=/workspace/project/results/cass_api_diag/teacher_seed_gpt5mini_20260315_merged/teacher_seed.jsonl
MROOT=/workspace/project/data/cass_r4_manifests_20260315a/shards

CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --method-pack model_light \
  --manifest "$MROOT/gsm8k_train_cluster_model_subset__shard01of04.json" \
  --output-dir /workspace/project/results/cass_r4_model_diversity/qwenmath7b_reducedlight_20260315a/gsm8k_train_cluster_model_subset_reduced__shard01of04 \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
CUDA_VISIBLE_DEVICES=1 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --method-pack model_light \
  --manifest "$MROOT/gsm8k_train_cluster_model_subset__shard02of04.json" \
  --output-dir /workspace/project/results/cass_r4_model_diversity/qwenmath7b_reducedlight_20260315a/gsm8k_train_cluster_model_subset_reduced__shard02of04 \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
CUDA_VISIBLE_DEVICES=2 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --method-pack model_light \
  --manifest "$MROOT/gsm8k_train_cluster_model_subset__shard03of04.json" \
  --output-dir /workspace/project/results/cass_r4_model_diversity/qwenmath7b_reducedlight_20260315a/gsm8k_train_cluster_model_subset_reduced__shard03of04 \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
CUDA_VISIBLE_DEVICES=3 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --method-pack model_light \
  --manifest "$MROOT/gsm8k_train_cluster_model_subset__shard04of04.json" \
  --output-dir /workspace/project/results/cass_r4_model_diversity/qwenmath7b_reducedlight_20260315a/gsm8k_train_cluster_model_subset_reduced__shard04of04 \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
wait

CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --method-pack model_light \
  --manifest "$MROOT/gsm8k_train_generic_model_subset__shard01of04.json" \
  --output-dir /workspace/project/results/cass_r4_model_diversity/qwenmath7b_reducedlight_20260315a/gsm8k_train_generic_model_subset_reduced__shard01of04 \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
CUDA_VISIBLE_DEVICES=1 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --method-pack model_light \
  --manifest "$MROOT/gsm8k_train_generic_model_subset__shard02of04.json" \
  --output-dir /workspace/project/results/cass_r4_model_diversity/qwenmath7b_reducedlight_20260315a/gsm8k_train_generic_model_subset_reduced__shard02of04 \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
CUDA_VISIBLE_DEVICES=2 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --method-pack model_light \
  --manifest "$MROOT/gsm8k_train_generic_model_subset__shard03of04.json" \
  --output-dir /workspace/project/results/cass_r4_model_diversity/qwenmath7b_reducedlight_20260315a/gsm8k_train_generic_model_subset_reduced__shard03of04 \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
CUDA_VISIBLE_DEVICES=3 python /workspace/project/scripts/cass_r4_collect.py \
  --client hf_local \
  --method-pack model_light \
  --manifest "$MROOT/gsm8k_train_generic_model_subset__shard04of04.json" \
  --output-dir /workspace/project/results/cass_r4_model_diversity/qwenmath7b_reducedlight_20260315a/gsm8k_train_generic_model_subset_reduced__shard04of04 \
  --model-name "$MODEL" \
  --disable-prm \
  --teacher-seed "$TEACHER" &
wait
```

Train/apply `PRISM_HIGH_FIDELITY`, aggregate the final `CASS-R4` pack, and render reports:

```bash
find /workspace/project/results/cass_r4_main/qwen7b_primary_f1aug_20260315a -mindepth 1 -maxdepth 1 -type d | sort \
  > /workspace/project/results/cass_r4_main/primary_aug_dirs_20260315a.txt
find /workspace/project/results/cass_r4_prism/qwen7b_mixed_20260315a -mindepth 1 -maxdepth 1 -type d | sort \
  > /workspace/project/results/cass_r4_prism/mixed_raw_dirs_20260315a.txt
find /workspace/project/results/cass_r4_f1/qwen7b_bridge_20260315a -mindepth 1 -maxdepth 1 -type d | sort \
  > /workspace/project/results/cass_r4_f1/bridge_raw_dirs_20260315a.txt
find /workspace/project/results/cass_r4_model_diversity/qwenmath7b_reducedlight_20260315a -mindepth 1 -maxdepth 1 -type d | sort \
  > /workspace/project/results/cass_r4_model_diversity/model_raw_dirs_20260315a.txt

mapfile -t TRAIN_DIRS < /workspace/project/results/cass_r4_prism/train_dirs_20260315a.txt
mapfile -t PRIMARY_DIRS < /workspace/project/results/cass_r4_main/primary_aug_dirs_20260315a.txt
mapfile -t MIXED_DIRS < /workspace/project/results/cass_r4_prism/mixed_raw_dirs_20260315a.txt
mapfile -t BRIDGE_DIRS < /workspace/project/results/cass_r4_f1/bridge_raw_dirs_20260315a.txt
mapfile -t MODEL_DIRS < /workspace/project/results/cass_r4_model_diversity/model_raw_dirs_20260315a.txt

python /workspace/project/scripts/cass_r4_prism.py \
  --train-raw-dirs "${TRAIN_DIRS[@]}" \
  --primary-raw-dirs "${PRIMARY_DIRS[@]}" \
  --mixed-raw-dirs "${MIXED_DIRS[@]}" \
  --model-raw-dirs "${MODEL_DIRS[@]}" \
  --output-dir /workspace/project/results/cass_r4_prism/prism_highfid_20260315a

python /workspace/project/scripts/cass_r4_main.py \
  --primary-raw-dirs "${PRIMARY_DIRS[@]}" \
  --mixed-raw-dirs "${MIXED_DIRS[@]}" \
  --bridge-raw-dirs "${BRIDGE_DIRS[@]}" \
  --model-raw-dirs "${MODEL_DIRS[@]}" \
  --prism-dir /workspace/project/results/cass_r4_prism/prism_highfid_20260315a \
  --output-dir /workspace/project/results/cass_r4_main/main_20260315a

python /workspace/project/scripts/make_cass_r4_reports.py \
  --main-dir /workspace/project/results/cass_r4_main/main_20260315a \
  --prism-dir /workspace/project/results/cass_r4_prism/prism_highfid_20260315a \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/cass_r4 \
  --figure-dir /workspace/project/figures/cass_r4
```

## LAST-PACK empirical support pack

Generate the planning manifests used by the main math/planning pack and the reduced model-diversity subset:

```bash
python /workspace/project/scripts/last_pack_make_manifests.py \
  --output-dir /workspace/project/data/last_pack_manifests_20260317a \
  --planning-domain lineworld \
  --planning-easy-count 400 \
  --planning-hard-count 400 \
  --bridge-limit 200 \
  --model-subset-limit 400 \
  --nshards 4 \
  --seed 13

python /workspace/project/scripts/last_pack_make_manifests.py \
  --output-dir /workspace/project/data/last_pack_manifests_20260317f \
  --planning-domain lineworld \
  --planning-easy-count 400 \
  --planning-hard-count 400 \
  --bridge-limit 200 \
  --model-subset-limit 300 \
  --nshards 4 \
  --seed 13
```

Collect the primary-model planning pack on all four GPUs:

```bash
MODEL="Qwen/Qwen2.5-7B-Instruct"
MROOT="/workspace/project/data/last_pack_manifests_20260317a/shards"

timeout 21600 bash -lc 'nvidia-smi dmon -s pucm -d 5 -o TD > /workspace/project/results/last_pack_planning/dmon_lineworld_main_20260317a.log' &

CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/last_pack_collect_planning.py \
  --manifest "$MROOT/planning_lineworld_full__shard01of04.json" \
  --output-dir /workspace/project/results/last_pack_planning/main_lineworld_20260317a_shard01of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
CUDA_VISIBLE_DEVICES=1 python /workspace/project/scripts/last_pack_collect_planning.py \
  --manifest "$MROOT/planning_lineworld_full__shard02of04.json" \
  --output-dir /workspace/project/results/last_pack_planning/main_lineworld_20260317a_shard02of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
CUDA_VISIBLE_DEVICES=2 python /workspace/project/scripts/last_pack_collect_planning.py \
  --manifest "$MROOT/planning_lineworld_full__shard03of04.json" \
  --output-dir /workspace/project/results/last_pack_planning/main_lineworld_20260317a_shard03of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
CUDA_VISIBLE_DEVICES=3 python /workspace/project/scripts/last_pack_collect_planning.py \
  --manifest "$MROOT/planning_lineworld_full__shard04of04.json" \
  --output-dir /workspace/project/results/last_pack_planning/main_lineworld_20260317a_shard04of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
wait
```

Generate the screened verifiable-format manifests and collect `IFEval`, `IFBench`, and the planning-format bridge:

```bash
python /workspace/project/scripts/last_pack_make_format_manifests.py \
  --output-dir /workspace/project/data/last_pack_format_manifests_20260317d \
  --ifeval-limit 400 \
  --ifbench-limit 300 \
  --ifeval-max-min-words 150 \
  --nshards 3 \
  --seed 13

MODEL="Qwen/Qwen2.5-7B-Instruct"
FROOT="/workspace/project/data/last_pack_format_manifests_20260317d/shards"

timeout 21600 bash -lc 'nvidia-smi dmon -s pucm -d 5 -o TD > /workspace/project/results/last_pack_format/dmon_ifeval_screened3way_20260317a.log' &
CUDA_VISIBLE_DEVICES=1 python /workspace/project/scripts/last_pack_collect_format.py \
  --surface ifeval \
  --manifest "$FROOT/ifeval_screened_le150_381__shard01of03.json" \
  --output-dir /workspace/project/results/last_pack_format/ifeval_screened3way_20260317a_shard01of03 \
  --model-name "$MODEL" \
  --client hf_local \
  --ifeval-repo /workspace/project/external/google-research \
  --ifbench-repo /workspace/project/external/IFBench \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
CUDA_VISIBLE_DEVICES=2 python /workspace/project/scripts/last_pack_collect_format.py \
  --surface ifeval \
  --manifest "$FROOT/ifeval_screened_le150_381__shard02of03.json" \
  --output-dir /workspace/project/results/last_pack_format/ifeval_screened3way_20260317a_shard02of03 \
  --model-name "$MODEL" \
  --client hf_local \
  --ifeval-repo /workspace/project/external/google-research \
  --ifbench-repo /workspace/project/external/IFBench \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
CUDA_VISIBLE_DEVICES=3 python /workspace/project/scripts/last_pack_collect_format.py \
  --surface ifeval \
  --manifest "$FROOT/ifeval_screened_le150_381__shard03of03.json" \
  --output-dir /workspace/project/results/last_pack_format/ifeval_screened3way_20260317a_shard03of03 \
  --model-name "$MODEL" \
  --client hf_local \
  --ifeval-repo /workspace/project/external/google-research \
  --ifbench-repo /workspace/project/external/IFBench \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
wait

bash /workspace/project/scripts/last_pack_run_followon.sh
```

Render the math/planning/format/criterion reports from the collected traces:

```bash
python /workspace/project/scripts/last_pack_analyze_math.py
python /workspace/project/scripts/last_pack_analyze_planning.py
python /workspace/project/scripts/last_pack_analyze_format.py
python /workspace/project/scripts/last_pack_analyze_criterion.py
```

Run the optional second-model reduced replication on the stable planning and bridge validators:

```bash
MODEL="Qwen/Qwen2.5-Math-7B-Instruct"
MROOT="/workspace/project/data/last_pack_manifests_20260317f/shards"

timeout 3600 bash -lc 'nvidia-smi dmon -s pucm -d 5 -o TD > /workspace/project/results/last_pack_model_diversity/dmon_qwenmath7b_planning_20260317a.log' &

CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/last_pack_collect_planning.py \
  --manifest "$MROOT/planning_model_subset__shard01of04.json" \
  --output-dir /workspace/project/results/last_pack_model_diversity/qwenmath7b_planning_20260317a_shard01of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
CUDA_VISIBLE_DEVICES=1 python /workspace/project/scripts/last_pack_collect_planning.py \
  --manifest "$MROOT/planning_model_subset__shard02of04.json" \
  --output-dir /workspace/project/results/last_pack_model_diversity/qwenmath7b_planning_20260317a_shard02of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
CUDA_VISIBLE_DEVICES=2 python /workspace/project/scripts/last_pack_collect_planning.py \
  --manifest "$MROOT/planning_model_subset__shard03of04.json" \
  --output-dir /workspace/project/results/last_pack_model_diversity/qwenmath7b_planning_20260317a_shard03of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
CUDA_VISIBLE_DEVICES=3 python /workspace/project/scripts/last_pack_collect_planning.py \
  --manifest "$MROOT/planning_model_subset__shard04of04.json" \
  --output-dir /workspace/project/results/last_pack_model_diversity/qwenmath7b_planning_20260317a_shard04of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
wait

timeout 3600 bash -lc 'nvidia-smi dmon -s pucm -d 5 -o TD > /workspace/project/results/last_pack_model_diversity/dmon_qwenmath7b_bridge_20260317a.log' &

CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/last_pack_collect_format.py \
  --surface planning_bridge \
  --manifest "$MROOT/planning_format_bridge__shard01of04.json" \
  --output-dir /workspace/project/results/last_pack_model_diversity/qwenmath7b_bridge_20260317a_shard01of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --ifeval-repo /workspace/project/external/google-research \
  --ifbench-repo /workspace/project/external/IFBench \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
CUDA_VISIBLE_DEVICES=1 python /workspace/project/scripts/last_pack_collect_format.py \
  --surface planning_bridge \
  --manifest "$MROOT/planning_format_bridge__shard02of04.json" \
  --output-dir /workspace/project/results/last_pack_model_diversity/qwenmath7b_bridge_20260317a_shard02of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --ifeval-repo /workspace/project/external/google-research \
  --ifbench-repo /workspace/project/external/IFBench \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
CUDA_VISIBLE_DEVICES=2 python /workspace/project/scripts/last_pack_collect_format.py \
  --surface planning_bridge \
  --manifest "$MROOT/planning_format_bridge__shard03of04.json" \
  --output-dir /workspace/project/results/last_pack_model_diversity/qwenmath7b_bridge_20260317a_shard03of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --ifeval-repo /workspace/project/external/google-research \
  --ifbench-repo /workspace/project/external/IFBench \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
CUDA_VISIBLE_DEVICES=3 python /workspace/project/scripts/last_pack_collect_format.py \
  --surface planning_bridge \
  --manifest "$MROOT/planning_format_bridge__shard04of04.json" \
  --output-dir /workspace/project/results/last_pack_model_diversity/qwenmath7b_bridge_20260317a_shard04of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --ifeval-repo /workspace/project/external/google-research \
  --ifbench-repo /workspace/project/external/IFBench \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
wait

python /workspace/project/scripts/last_pack_analyze_model_diversity.py
```

## LACE online intervention policy pack

Math online policy analysis reuses frozen `CASS` / `CASS-R4` traces and does not require fresh generation:

```bash
python /workspace/project/scripts/lace_analyze_math_online.py
```

Collect the fresh `LACE` output-constraint surfaces on the existing frozen screened manifests:

```bash
MODEL="Qwen/Qwen2.5-7B-Instruct"
FROOT="/workspace/project/data/lace_format_manifests_20260318a/shards"

timeout 21600 bash -lc 'nvidia-smi dmon -s pucm -d 5 -o TD > /workspace/project/results/lace_format/dmon_ifeval_20260318a.log' &
for shard in 01 02 03 04; do
  CUDA_VISIBLE_DEVICES=$((10#$shard - 1)) python /workspace/project/scripts/last_pack_collect_format.py \
    --client hf_local \
    --surface ifeval \
    --manifest "$FROOT/ifeval_screened_le150_381__shard${shard}of04.json" \
    --output-dir "/workspace/project/results/lace_format/qwen7b_policypack_20260318a/ifeval_screened_shard${shard}of04" \
    --model-name "$MODEL" \
    --ifeval-repo /workspace/project/external/google-research \
    --ifbench-repo /workspace/project/external/IFBench \
    --local-quantization none \
    --local-dtype float16 \
    --local-device-map cuda:0 \
    --local-max-model-len 4096 \
    --local-trust-remote-code &
done
wait

timeout 21600 bash -lc 'nvidia-smi dmon -s pucm -d 5 -o TD > /workspace/project/results/lace_format/dmon_ifbench_20260318a.log' &
for shard in 01 02 03 04; do
  CUDA_VISIBLE_DEVICES=$((10#$shard - 1)) python /workspace/project/scripts/last_pack_collect_format.py \
    --client hf_local \
    --surface ifbench \
    --manifest "$FROOT/ifbench_main_300__shard${shard}of04.json" \
    --output-dir "/workspace/project/results/lace_format/qwen7b_policypack_20260318a/ifbench_shard${shard}of04" \
    --model-name "$MODEL" \
    --ifeval-repo /workspace/project/external/google-research \
    --ifbench-repo /workspace/project/external/IFBench \
    --local-quantization none \
    --local-dtype float16 \
    --local-device-map cuda:0 \
    --local-max-model-len 4096 \
    --local-trust-remote-code &
done
wait
```

Collect the `LACE` planning boundary pack on the frozen lineworld manifests:

```bash
MODEL="Qwen/Qwen2.5-7B-Instruct"
MROOT="/workspace/project/data/lace_manifests_20260318a/shards"

timeout 21600 bash -lc 'nvidia-smi dmon -s pucm -d 5 -o TD > /workspace/project/results/lace_planning/dmon_lineworld_20260318a.log' &
for shard in 01 02 03 04; do
  CUDA_VISIBLE_DEVICES=$((10#$shard - 1)) python /workspace/project/scripts/last_pack_collect_planning.py \
    --client hf_local \
    --manifest "$MROOT/planning_lineworld_full__shard${shard}of04.json" \
    --output-dir "/workspace/project/results/lace_planning/fresh_lineworld_20260318a_shard${shard}of04" \
    --model-name "$MODEL" \
    --local-quantization none \
    --local-dtype float16 \
    --local-device-map cuda:0 \
    --local-max-model-len 4096 \
    --local-trust-remote-code &
done
wait
```

Render the primary-model `LACE` reports:

```bash
python /workspace/project/scripts/lace_analyze_math_online.py
python /workspace/project/scripts/lace_analyze_format_online.py
python /workspace/project/scripts/lace_analyze_planning_boundary.py
python /workspace/project/scripts/lace_analyze_intervention_policy.py
```

Optional second-model reduced replication for `LACE`:

```bash
MODEL="Qwen/Qwen2.5-Math-7B-Instruct"
TEACHER="/workspace/project/results/cass_api_diag/teacher_seed_gpt5mini_20260315_merged/teacher_seed.jsonl"
MROOT="/workspace/project/data/cass_r4_manifests_20260315a/shards"
OUTROOT="/workspace/project/results/lace_model_diversity/qwenmath7b_math_online_20260318a"

timeout 43200 bash -lc 'nvidia-smi dmon -s mu -d 5 > /workspace/project/results/lace_model_diversity/qwenmath7b_math_online_20260318a/dmon_cluster_20260318a.log' &
for shard in 01 02 03 04; do
  CUDA_VISIBLE_DEVICES=$((10#$shard - 1)) python /workspace/project/scripts/cass_collect_patchbank.py \
    --client hf_local \
    --manifest "$MROOT/gsm8k_train_cluster_model_subset__shard${shard}of04.json" \
    --output-dir "$OUTROOT/gsm8k_train_cluster_model_subset_reduced__shard${shard}of04" \
    --model-name "$MODEL" \
    --disable-prm \
    --teacher-seed "$TEACHER" \
    --local-quantization none \
    --local-dtype float16 \
    --local-device-map cuda:0 \
    --local-max-model-len 4096 \
    --local-trust-remote-code &
done
wait

timeout 21600 bash -lc 'nvidia-smi dmon -s mu -d 5 > /workspace/project/results/lace_model_diversity/qwenmath7b_math_online_20260318a/dmon_generic_20260318a.log' &
for shard in 01 02 03 04; do
  CUDA_VISIBLE_DEVICES=$((10#$shard - 1)) python /workspace/project/scripts/cass_collect_patchbank.py \
    --client hf_local \
    --manifest "$MROOT/gsm8k_train_generic_model_subset__shard${shard}of04.json" \
    --output-dir "$OUTROOT/gsm8k_train_generic_model_subset_reduced__shard${shard}of04" \
    --model-name "$MODEL" \
    --disable-prm \
    --teacher-seed "$TEACHER" \
    --local-quantization none \
    --local-dtype float16 \
    --local-device-map cuda:0 \
    --local-max-model-len 4096 \
    --local-trust-remote-code &
done
wait

python /workspace/project/scripts/lace_analyze_model_diversity.py
```

No OpenAI API path was used for `LACE`.

If the reduced second-model `IFEval` run exposes a deterministic patch-loop bottleneck on `at least N words` prompts, apply the fixed rerun used in the final pack:

```bash
MODEL="Qwen/Qwen2.5-Math-7B-Instruct"

timeout 3600 bash -lc 'nvidia-smi dmon -s pucm -d 5 -o TD > /workspace/project/results/last_pack_model_diversity/dmon_qwenmath7b_ifevalfix_20260317b.log' &

CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/last_pack_collect_format.py \
  --surface ifeval \
  --manifest /workspace/project/data/last_pack_format_manifests_20260317e/shards/ifeval_screened_le150_200__shard01of04.json \
  --output-dir /workspace/project/results/last_pack_model_diversity/qwenmath7b_ifevalfix_20260317b_shard01of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --ifeval-repo /workspace/project/external/google-research \
  --ifbench-repo /workspace/project/external/IFBench \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
CUDA_VISIBLE_DEVICES=1 python /workspace/project/scripts/last_pack_collect_format.py \
  --surface ifeval \
  --manifest /workspace/project/data/last_pack_format_manifests_20260317e/shards/ifeval_screened_le150_200__shard02of04.json \
  --output-dir /workspace/project/results/last_pack_model_diversity/qwenmath7b_ifevalfix_20260317b_shard02of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --ifeval-repo /workspace/project/external/google-research \
  --ifbench-repo /workspace/project/external/IFBench \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
CUDA_VISIBLE_DEVICES=2 python /workspace/project/scripts/last_pack_collect_format.py \
  --surface ifeval \
  --manifest /workspace/project/data/last_pack_format_manifests_20260317e/shards/ifeval_screened_le150_200__shard03of04.json \
  --output-dir /workspace/project/results/last_pack_model_diversity/qwenmath7b_ifevalfix_20260317b_shard03of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --ifeval-repo /workspace/project/external/google-research \
  --ifbench-repo /workspace/project/external/IFBench \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
CUDA_VISIBLE_DEVICES=3 python /workspace/project/scripts/last_pack_collect_format.py \
  --surface ifeval \
  --manifest /workspace/project/data/last_pack_format_manifests_20260317e/shards/ifeval_screened_le150_200__shard04of04.json \
  --output-dir /workspace/project/results/last_pack_model_diversity/qwenmath7b_ifevalfix_20260317b_shard04of04 \
  --model-name "$MODEL" \
  --client hf_local \
  --ifeval-repo /workspace/project/external/google-research \
  --ifbench-repo /workspace/project/external/IFBench \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code &
wait

python /workspace/project/scripts/last_pack_analyze_model_diversity.py
```

## LACE-R2 simplicity and cross-family robustness pack

`LACE-R2` keeps the frozen `CASS` and `LACE` methods fixed and asks three narrower questions:

- can the learned online criterion be simplified into a small interpretable rule
- does the online local-repair preference survive on a genuinely different model family
- does the format-side support survive a fresh second-model rerun

The completed pack used:

- primary model family:
  - `Qwen/Qwen2.5-7B-Instruct`
- genuinely different cross-family model:
  - `mistralai/Mistral-7B-Instruct-v0.3`

Criterion simplification on frozen primary-model traces:

```bash
python /workspace/project/scripts/lace_r2_criterion_simplification.py
```

Optional one-example cross-family smoke test before the heavy runs:

```bash
CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/last_pack_collect_format.py \
  --surface ifeval \
  --manifest /workspace/project/data/lace_format_manifests_20260318a/shards/ifeval_screened_le150_381__shard01of04.json \
  --output-dir /workspace/project/results/lace_r2_model_diversity/mistral_smoke_20260318a \
  --model-name mistralai/Mistral-7B-Instruct-v0.3 \
  --client hf_local \
  --ifeval-repo /workspace/project/external/google-research \
  --ifbench-repo /workspace/project/external/IFBench \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code \
  --limit 1
```

Fresh cross-family math reduced replication on `4` GPUs:

```bash
/workspace/project/scripts/lace_r2_run_math_crossfamily.sh \
  'mistralai/Mistral-7B-Instruct-v0.3' \
  /workspace/project/results/lace_r2_math/mistral7b_math_online_20260318a \
  cluster_only

python /workspace/project/scripts/lace_r2_analyze_math_crossfamily.py \
  --model-name 'mistralai/Mistral-7B-Instruct-v0.3' \
  --result-tag mistral7b_crossfamily_20260318a \
  --cluster-pattern '/workspace/project/results/lace_r2_math/mistral7b_math_online_20260318a/gsm8k_train_cluster_model_subset_reduced__shard*of04/per_example.jsonl'
```

Fresh cross-family screened-`IFEval` rerun on `4` GPUs:

```bash
/workspace/project/scripts/lace_r2_run_format_crossfamily.sh \
  'mistralai/Mistral-7B-Instruct-v0.3' \
  /workspace/project/results/lace_r2_format/mistral7b_format_online_20260318a \
  ifeval_only

python /workspace/project/scripts/lace_r2_analyze_format_crossfamily.py \
  --model-name 'mistralai/Mistral-7B-Instruct-v0.3' \
  --result-tag mistral7b_crossfamily_20260318a \
  --ifeval-pattern '/workspace/project/results/lace_r2_format/mistral7b_format_online_20260318a/ifeval_screened_shard*of04/per_example.jsonl'
```

Render the final memo and cross-family summary:

```bash
python /workspace/project/scripts/lace_r2_finalize.py
```

Final `LACE-R2` read:

- primary-family simplicity:
  - math `LEARNED_GATE = 0.759`
  - math `SIMPLE_2FEATURE_GATE = 0.753`
- cross-family math:
  - `ALWAYS_RESTART = 0.122`
  - `ALWAYS_CASS = 0.275`
  - `LEARNED_GATE_WITHIN = 0.282`
  - `SIMPLE_BEST_GATE = 0.290`
- cross-family format on fresh screened `IFEval`:
  - `ALWAYS_FULL_REWRITE = 0.518`
  - `HEURISTIC_GATE = 0.610`
  - `LEARNED_GATE_WITHIN = 0.539`
  - `SIMPLE_BEST_GATE = 0.603`

No OpenAI API path was used for `LACE-R2`.

## LACE-R3

`LACE-R3` is the bounded portability-support pack after `LACE-R2`. It answers:

- do simplified intervention criteria transfer cleanly across model families
- does the format-side support survive a fresh cross-family `IFBench` rerun
- is the simple rule family actually more portable than the learned gate family

The completed pack reused the existing non-Qwen family:

- `mistralai/Mistral-7B-Instruct-v0.3`

Portability analysis on the existing `Mistral` math + screened-`IFEval` reruns:

```bash
python /workspace/project/scripts/lace_r3_analyze_portability.py \
  --model-name 'mistralai/Mistral-7B-Instruct-v0.3' \
  --result-tag mistral7b_portability_20260318a
```

Fresh cross-family `IFBench` rerun on `4` GPUs:

```bash
bash /workspace/project/scripts/lace_r3_run_ifbench_crossfamily.sh \
  'mistralai/Mistral-7B-Instruct-v0.3' \
  /workspace/project/results/lace_r3_format/mistral7b_ifbench_crossfamily_20260318a

python /workspace/project/scripts/lace_r3_analyze_ifbench_crossfamily.py \
  --model-name 'mistralai/Mistral-7B-Instruct-v0.3' \
  --result-tag mistral7b_ifbench_crossfamily_20260318a \
  --ifbench-pattern '/workspace/project/results/lace_r3_format/mistral7b_ifbench_crossfamily_20260318a/ifbench_shard*of04/per_example.jsonl'
```

Rule-transfer synthesis and final memo:

```bash
python /workspace/project/scripts/lace_r3_analyze_rule_transfer.py \
  --result-tag mistral7b_portability_20260318a

python /workspace/project/scripts/lace_r3_finalize.py
```

Final `LACE-R3` read:

- `Mistral` math portability:
  - `ALWAYS_RESTART = 0.122`
  - `LEARNED_GATE_TRANSFER = 0.183`
  - `LEARNED_GATE_WITHIN = 0.282`
  - best simple transfer `= 0.290`
- `Mistral` screened-`IFEval` portability:
  - `ALWAYS_FULL_REWRITE = 0.518`
  - `LEARNED_GATE_TRANSFER = 0.574`
  - `LEARNED_GATE_WITHIN = 0.539`
  - best simple transfer `= 0.624`
- fresh cross-family `IFBench`:
  - `ALWAYS_FULL_REWRITE = 0.155`
  - `LEARNED_GATE_TRANSFER = 0.204`
  - `LEARNED_GATE_WITHIN = 0.194`
  - best simple transfer `= 0.223`
- portability summary:
  - simple transferred rules beat learned transfer on math, screened `IFEval`, and fresh `IFBench`
  - within-model tuning helps on math
  - format portability is cleaner for the simple transferred rules than for the learned gates

No OpenAI API path was used for `LACE-R3`.

## CASS-XF

`CASS-XF` is the bounded cross-family replication pack for the frozen main `CASS` method family. It asks one narrower question:

- does the main `CASS` patch family itself survive on a genuinely different model family

The completed pack reused the existing stable non-`Qwen` family:

- `mistralai/Mistral-7B-Instruct-v0.3`

Freeze the reduced replication manifests:

```bash
python /workspace/project/scripts/cass_xf_prepare_manifests.py \
  --output-dir /workspace/project/data/cass_xf_manifests_20260319a \
  --report-path /workspace/project/reports/cass_xf_surface_manifest.md
```

Run the frozen main-method replication on `4` GPUs:

```bash
bash /workspace/project/scripts/cass_xf_run_mistral.sh \
  'mistralai/Mistral-7B-Instruct-v0.3' \
  /workspace/project/data/cass_xf_manifests_20260319a \
  /workspace/project/results/cass_xf_mistral/mistral7b_main_20260319a \
  with_generic
```

Aggregate the frozen `CASS` methods and render the `CASS-XF` reports:

```bash
python /workspace/project/scripts/cass_xf_main.py \
  --main-dirs \
    /workspace/project/results/cass_xf_mistral/mistral7b_main_20260319a/gsm8k_train_cluster_model_subset__shard01of04 \
    /workspace/project/results/cass_xf_mistral/mistral7b_main_20260319a/gsm8k_train_cluster_model_subset__shard02of04 \
    /workspace/project/results/cass_xf_mistral/mistral7b_main_20260319a/gsm8k_train_cluster_model_subset__shard03of04 \
    /workspace/project/results/cass_xf_mistral/mistral7b_main_20260319a/gsm8k_train_cluster_model_subset__shard04of04 \
    /workspace/project/results/cass_xf_mistral/mistral7b_main_20260319a/gsm8k_train_generic_model_subset__shard01of04 \
    /workspace/project/results/cass_xf_mistral/mistral7b_main_20260319a/gsm8k_train_generic_model_subset__shard02of04 \
    /workspace/project/results/cass_xf_mistral/mistral7b_main_20260319a/gsm8k_train_generic_model_subset__shard03of04 \
    /workspace/project/results/cass_xf_mistral/mistral7b_main_20260319a/gsm8k_train_generic_model_subset__shard04of04 \
  --cluster-manifest /workspace/project/data/cass_xf_manifests_20260319a/gsm8k_train_cluster_model_subset.json \
  --generic-manifest /workspace/project/data/cass_xf_manifests_20260319a/gsm8k_train_generic_model_subset.json \
  --output-dir /workspace/project/results/cass_xf_mistral/main_20260319a

python /workspace/project/scripts/make_cass_xf_reports.py \
  --main-dir /workspace/project/results/cass_xf_mistral/main_20260319a \
  --surface-report /workspace/project/reports/cass_xf_surface_manifest.md \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/cass_xf \
  --figure-dir /workspace/project/figures/cass_xf
```

Final `CASS-XF` read:

- collection runtime:
  - `runtime_s = 4615` (`76.9m`)
  - cluster `sm` mean `= 91.10`
  - generic `sm` mean `= 87.02`
- `Mistral` cluster-hard:
  - `RAW_PYTHON = 0.2075`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.3175`
  - `CASS_TARGET_POSTPROCESS_PATCH = 0.3325`
  - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH = 0.3325`
  - `CASS_CONSERVATIVE_GATE = 0.3325`
- `Mistral` generic-hard:
  - `RAW_PYTHON = 0.1800`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.3850`
  - `CASS_TARGET_POSTPROCESS_PATCH = 0.4150`
  - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH = 0.4150`
  - `CASS_CONSERVATIVE_GATE = 0.4150`
- key pairwise read:
  - cluster-hard `CASS_TARGET_POSTPROCESS_PATCH - RAW_PYTHON = +0.1244 [0.0800, 0.1675]`
  - cluster-hard `CASS_TARGET_POSTPROCESS_PATCH - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0145 [-0.0225, 0.0525]`
  - generic-hard `CASS_TARGET_POSTPROCESS_PATCH - RAW_PYTHON = +0.2348 [0.1600, 0.3100]`
  - generic-hard `CASS_TARGET_POSTPROCESS_PATCH - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0299 [-0.0300, 0.0900]`
- interpretation:
  - the frozen `CASS` family clearly survives against `RAW_PYTHON` on `Mistral`
  - it is directionally favorable to `OPERATOR_SCHEMA_TO_CODE_BASE` on both reduced surfaces
  - target/postprocess patching remains the recurring useful ingredient
  - the conservative gate does not add extra value over the best fixed target/postprocess patch on this reduced `Mistral` replication

No OpenAI API path was used for `CASS-XF`.

## CASS-XF-R2

`CASS-XF-R2` is the portability-lock reinforcement step after `CASS-XF`. In the ended experiment window reflected here, the completed run was the expanded `Mistral` cluster-hard lock attempt.

Freeze the expanded and reduced manifests:

```bash
python /workspace/project/scripts/cass_xf_r2_prepare_manifests.py \
  --output-dir /workspace/project/data/cass_xf_r2_manifests_20260319a \
  --report-path /workspace/project/reports/cass_xf_r2_surface_manifest.md
```

Expanded `Mistral` cluster-hard / generic-hard runner:

```bash
bash /workspace/project/scripts/cass_xf_r2_run_family.sh \
  'mistralai/Mistral-7B-Instruct-v0.3' \
  /workspace/project/data/cass_xf_r2_manifests_20260319a \
  gsm8k_train_cluster_portability_full \
  gsm8k_train_generic_portability_full \
  /workspace/project/results/cass_xf_r2_mistral/mistral7b_full_20260319b
```

Aggregate the completed ended-state `Mistral` cluster run and render the `CASS-XF-R2` reports:

```bash
python /workspace/project/scripts/cass_xf_main.py \
  --main-dirs \
    /workspace/project/results/cass_xf_r2_mistral/mistral7b_full_20260319b/gsm8k_train_cluster_portability_full__shard01of04 \
    /workspace/project/results/cass_xf_r2_mistral/mistral7b_full_20260319b/gsm8k_train_cluster_portability_full__shard02of04 \
    /workspace/project/results/cass_xf_r2_mistral/mistral7b_full_20260319b/gsm8k_train_cluster_portability_full__shard03of04 \
    /workspace/project/results/cass_xf_r2_mistral/mistral7b_full_20260319b/gsm8k_train_cluster_portability_full__shard04of04 \
  --cluster-manifest /workspace/project/data/cass_xf_r2_manifests_20260319a/gsm8k_train_cluster_portability_full.json \
  --generic-manifest /workspace/project/data/cass_xf_r2_manifests_20260319a/gsm8k_train_generic_portability_full.json \
  --family-label Mistral \
  --output-dir /workspace/project/results/cass_xf_r2_mistral/main_cluster_20260319b

python /workspace/project/scripts/make_cass_xf_r2_reports.py \
  --mistral-main-dir /workspace/project/results/cass_xf_r2_mistral/main_cluster_20260319b \
  --mistral-cluster-manifest /workspace/project/data/cass_xf_r2_manifests_20260319a/gsm8k_train_cluster_portability_full.json \
  --surface-report /workspace/project/reports/cass_xf_r2_surface_manifest.md \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/cass_xf_r2 \
  --figure-dir /workspace/project/figures/cass_xf_r2 \
  --third-family-label Granite
```

Ended-state `CASS-XF-R2` read:

- expanded `Mistral` cluster-hard:
  - `RAW_PYTHON = 0.209901`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.331353`
  - `CASS_TARGET_POSTPROCESS_PATCH = 0.358416`
  - `CASS_CONSERVATIVE_GATE = 0.358416`
- key pairwise results:
  - `CASS_TARGET_POSTPROCESS_PATCH - RAW_PYTHON = +0.1486 [0.1234, 0.1716]`
  - `CASS_TARGET_POSTPROCESS_PATCH - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0273 [0.0079, 0.0482]`
- sequential lock:
  - first positive lower CI bound vs operator at `n=1350`
  - still positive at `n=1500` and `n=1515`
- portable-core interpretation:
  - on `Mistral`, the best frozen CASS ingredient is the fixed `CASS_TARGET_POSTPROCESS_PATCH`
  - `role-only` remains much weaker
  - the conservative gate adds no extra gain over the fixed target/postprocess patch on this family

Not run in this ended experiment window:

- expanded `Mistral` generic-hard
- `Granite` reduced replication

No OpenAI API path was used for `CASS-XF-R2`.

## CASS-XF-R3

`CASS-XF-R3` is the portability-closure step after `CASS-XF-R2`. It closes the two remaining holes:

- expanded `Mistral` generic-hard
- one third-family reduced replication

Freeze the `R3` manifest namespace:

```bash
python /workspace/project/scripts/cass_xf_r3_prepare_manifests.py \
  --output-dir /workspace/project/data/cass_xf_r3_manifests_20260319a \
  --report-path /workspace/project/reports/cass_xf_r3_surface_manifest.md
```

Run expanded `Mistral` generic-hard:

```bash
bash /workspace/project/scripts/cass_xf_r2_run_family.sh \
  'mistralai/Mistral-7B-Instruct-v0.3' \
  /workspace/project/data/cass_xf_r3_manifests_20260319a \
  gsm8k_train_generic_portability_full \
  gsm8k_train_generic_portability_full \
  /workspace/project/results/cass_xf_r3_mistral/mistral7b_generic_20260319a \
  generic_only
```

Run reduced `Granite` cluster-hard + generic-hard:

```bash
bash /workspace/project/scripts/cass_xf_r2_run_family.sh \
  'ibm-granite/granite-3.1-8b-instruct' \
  /workspace/project/data/cass_xf_r3_manifests_20260319a \
  gsm8k_train_cluster_third_family_reduced \
  gsm8k_train_generic_third_family_reduced \
  /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a
```

Aggregate and render the final `R3` report set:

```bash
python /workspace/project/scripts/cass_xf_main.py \
  --main-dirs \
    /workspace/project/results/cass_xf_r3_mistral/mistral7b_generic_20260319a/gsm8k_train_generic_portability_full__shard01of04 \
    /workspace/project/results/cass_xf_r3_mistral/mistral7b_generic_20260319a/gsm8k_train_generic_portability_full__shard02of04 \
    /workspace/project/results/cass_xf_r3_mistral/mistral7b_generic_20260319a/gsm8k_train_generic_portability_full__shard03of04 \
    /workspace/project/results/cass_xf_r3_mistral/mistral7b_generic_20260319a/gsm8k_train_generic_portability_full__shard04of04 \
  --cluster-manifest /workspace/project/data/cass_xf_r3_manifests_20260319a/gsm8k_train_cluster_third_family_reduced.json \
  --generic-manifest /workspace/project/data/cass_xf_r3_manifests_20260319a/gsm8k_train_generic_portability_full.json \
  --family-label Mistral \
  --output-dir /workspace/project/results/cass_xf_r3_mistral/main_generic_20260319a

python /workspace/project/scripts/cass_xf_main.py \
  --main-dirs \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_cluster_third_family_reduced__shard01of04 \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_cluster_third_family_reduced__shard02of04 \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_cluster_third_family_reduced__shard03of04 \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_cluster_third_family_reduced__shard04of04 \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_generic_third_family_reduced__shard01of04 \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_generic_third_family_reduced__shard02of04 \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_generic_third_family_reduced__shard03of04 \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_generic_third_family_reduced__shard04of04 \
  --cluster-manifest /workspace/project/data/cass_xf_r3_manifests_20260319a/gsm8k_train_cluster_third_family_reduced.json \
  --generic-manifest /workspace/project/data/cass_xf_r3_manifests_20260319a/gsm8k_train_generic_third_family_reduced.json \
  --family-label Granite \
  --output-dir /workspace/project/results/cass_xf_r3_third_family/main_20260320a

python /workspace/project/scripts/make_cass_xf_r3_reports.py \
  --mistral-cluster-main-dir /workspace/project/results/cass_xf_r2_mistral/main_cluster_20260319b \
  --mistral-generic-main-dir /workspace/project/results/cass_xf_r3_mistral/main_generic_20260319a \
  --third-main-dir /workspace/project/results/cass_xf_r3_third_family/main_20260320a \
  --third-family-label Granite \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/cass_xf_r3 \
  --figure-dir /workspace/project/figures/cass_xf_r3
```

Final `CASS-XF-R3` read:

- `Mistral` generic-hard:
  - `RAW_PYTHON = 0.200828`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.391304`
  - `CASS_TARGET_POSTPROCESS_PATCH = 0.420290`
  - `CASS_TARGET_POSTPROCESS_PATCH - RAW_PYTHON = +0.2192 [0.1739, 0.2629]`
  - `CASS_TARGET_POSTPROCESS_PATCH - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0285 [-0.0124, 0.0683]`
- `Granite` reduced replication:
  - cluster-hard:
    - `RAW_PYTHON = 0.6075`
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.7325`
    - `CASS_TARGET_POSTPROCESS_PATCH = 0.5075`
  - generic-hard:
    - `RAW_PYTHON = 0.655`
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.765`
    - `CASS_TARGET_POSTPROCESS_PATCH = 0.64`
- closure interpretation:
  - target/postprocess patching remains the strongest ingredient inside the frozen `CASS` family across `Qwen`, `Mistral`, and `Granite`
  - role-only remains weaker
  - the conservative gate remains more family-dependent
  - but the stronger claim that the frozen `CASS` patch family stays absolutely favorable to `RAW_PYTHON` / `OPERATOR` across three families is not supported because `Granite` reverses that direction

No OpenAI API path was used for `CASS-XF-R3`.

## CASS-BD

`CASS-BD` is the Granite-only boundary-diagnosis pack after `CASS-XF-R3`. It asks:

- why Granite breaks the absolute direction
- whether the damage comes from baseline dominance, destructive patching, extraction weakness, compiler brittleness, or some combination

Freeze the Granite diagnosis manifests:

```bash
python /workspace/project/scripts/cass_bd_prepare_manifests.py \
  --output-dir /workspace/project/data/cass_bd_manifests_20260320a \
  --report-path /workspace/project/reports/cass_bd_surface_manifest.md
```

Run the field audit from existing raw outputs:

```bash
python /workspace/project/scripts/cass_bd_analyze.py \
  --granite-dirs \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_cluster_third_family_reduced__shard01of04 \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_cluster_third_family_reduced__shard02of04 \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_cluster_third_family_reduced__shard03of04 \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_cluster_third_family_reduced__shard04of04 \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_generic_third_family_reduced__shard01of04 \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_generic_third_family_reduced__shard02of04 \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_generic_third_family_reduced__shard03of04 \
    /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a/gsm8k_train_generic_third_family_reduced__shard04of04 \
  --mistral-dirs \
    /workspace/project/results/cass_xf_r2_mistral/mistral7b_full_20260319b/gsm8k_train_cluster_portability_full__shard01of04 \
    /workspace/project/results/cass_xf_r2_mistral/mistral7b_full_20260319b/gsm8k_train_cluster_portability_full__shard02of04 \
    /workspace/project/results/cass_xf_r2_mistral/mistral7b_full_20260319b/gsm8k_train_cluster_portability_full__shard03of04 \
    /workspace/project/results/cass_xf_r2_mistral/mistral7b_full_20260319b/gsm8k_train_cluster_portability_full__shard04of04 \
  --qwen-dirs \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard01of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard02of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard03of04 \
    /workspace/project/results/cass_r3_main/gsm8k_cluster_generic_20260315r3a_shard04of04 \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/cass_bd \
  --figure-dir /workspace/project/figures/cass_bd
```

Run the replay-controlled partial surgery pack:

```bash
bash /workspace/project/scripts/cass_bd_run_partial_replay.sh \
  'ibm-granite/granite-3.1-8b-instruct' \
  /workspace/project/data/cass_bd_manifests_20260320a \
  /workspace/project/results/cass_xf_r3_third_family/granite31_8b_reduced_20260319a \
  /workspace/project/results/cass_bd_granite/partial_replay_20260320a

python /workspace/project/scripts/cass_bd_analyze_partial_replay.py \
  --input-dirs \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_cluster_third_family_reduced__shard01of04 \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_cluster_third_family_reduced__shard02of04 \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_cluster_third_family_reduced__shard03of04 \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_cluster_third_family_reduced__shard04of04 \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_generic_third_family_reduced__shard01of04 \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_generic_third_family_reduced__shard02of04 \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_generic_third_family_reduced__shard03of04 \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_generic_third_family_reduced__shard04of04 \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/cass_bd \
  --figure-dir /workspace/project/figures/cass_bd
```

Final `CASS-BD` read:

- Granite field audit:
  - cluster `baseline-right / patch-wrong = 115`
  - generic `baseline-right / patch-wrong = 42`
  - dominant category on both surfaces: `code_generation_after_correct_patch`
- partial surgery:
  - cluster-hard:
    - `GRANITE_POSTPROCESS_ONLY_PATCH = 0.7075`
    - `GRANITE_DISCRETIZATION_ONLY_PATCH = 0.7025`
    - `GRANITE_TARGET_ONLY_PATCH = 0.515`
    - `CASS_TARGET_POSTPROCESS_PATCH = 0.5075`
  - generic-hard:
    - `GRANITE_POSTPROCESS_ONLY_PATCH = 0.715`
    - `GRANITE_DISCRETIZATION_ONLY_PATCH = 0.710`
    - `GRANITE_TARGET_ONLY_PATCH = 0.625`
    - `CASS_TARGET_POSTPROCESS_PATCH = 0.64`
- interpretation:
  - Granite is best explained as a combination of:
    - strong baseline dominance
    - destructive target/relation overwrite
    - compiler/code-generation brittleness after those target edits
  - postprocess/discretization edits are relatively safe on Granite
  - the harmful part is the target-side overwrite, not the full idea of sparse patching itself

No OpenAI API path was used for `CASS-BD`.

## CASS-SR

`CASS-SR` is the scale-robustness pack after the cross-family work. It asks whether the frozen `CASS` portable core still matters when the base open model becomes substantially stronger.

Freeze the stronger-model reduced surfaces:

```bash
python /workspace/project/scripts/cass_sr_prepare_manifests.py \
  --output-dir /workspace/project/data/cass_sr_manifests_20260321a \
  --report-path /workspace/project/reports/cass_sr_surface_manifest.md
```

Bring up and run the required `Qwen-14B` path:

```bash
HF_HUB_DISABLE_XET=1 CUDA_VISIBLE_DEVICES=0 python /workspace/project/scripts/cass_r2_collect.py \
  --client hf_local \
  --manifest /workspace/project/data/cass_r4_manifests_20260315a/gsm8k_train_cluster_smoke1.json \
  --output-dir /workspace/project/results/cass_sr_smoke/qwen14b_smoke1_20260321b \
  --model-name Qwen/Qwen2.5-14B-Instruct \
  --disable-prm \
  --teacher-seed /workspace/project/results/cass_api_diag/teacher_seed_gpt5mini_20260315_merged/teacher_seed.jsonl \
  --local-quantization 4bit \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code

bash /workspace/project/scripts/cass_sr_run_family.sh \
  'Qwen/Qwen2.5-14B-Instruct' \
  /workspace/project/data/cass_sr_manifests_20260321a \
  gsm8k_train_cluster_scale_reduced \
  gsm8k_train_generic_scale_reduced \
  /workspace/project/results/cass_sr_qwen14b/qwen14b_reduced_20260321b \
  both \
  4bit \
  float16

bash /workspace/project/scripts/cass_sr_run_family.sh \
  'Qwen/Qwen2.5-14B-Instruct' \
  /workspace/project/data/cass_sr_manifests_20260321a \
  gsm8k_train_cluster_scale_reduced \
  gsm8k_train_generic_scale_reduced \
  /workspace/project/results/cass_sr_qwen14b/qwen14b_generic_20260321b \
  generic_only \
  4bit \
  float16
```

Aggregate the finished 14B set and render the scale report:

```bash
python /workspace/project/scripts/cass_xf_main.py \
  --main-dirs \
    /workspace/project/results/cass_sr_qwen14b/qwen14b_reduced_20260321b/gsm8k_train_cluster_scale_reduced__shard01of04 \
    /workspace/project/results/cass_sr_qwen14b/qwen14b_reduced_20260321b/gsm8k_train_cluster_scale_reduced__shard02of04 \
    /workspace/project/results/cass_sr_qwen14b/qwen14b_reduced_20260321b/gsm8k_train_cluster_scale_reduced__shard03of04 \
    /workspace/project/results/cass_sr_qwen14b/qwen14b_reduced_20260321b/gsm8k_train_cluster_scale_reduced__shard04of04 \
    /workspace/project/results/cass_sr_qwen14b/qwen14b_generic_20260321b/gsm8k_train_generic_scale_reduced__shard01of04 \
    /workspace/project/results/cass_sr_qwen14b/qwen14b_generic_20260321b/gsm8k_train_generic_scale_reduced__shard02of04 \
    /workspace/project/results/cass_sr_qwen14b/qwen14b_generic_20260321b/gsm8k_train_generic_scale_reduced__shard03of04 \
    /workspace/project/results/cass_sr_qwen14b/qwen14b_generic_20260321b/gsm8k_train_generic_scale_reduced__shard04of04 \
  --cluster-manifest /workspace/project/data/cass_sr_manifests_20260321a/gsm8k_train_cluster_scale_reduced.json \
  --generic-manifest /workspace/project/data/cass_sr_manifests_20260321a/gsm8k_train_generic_scale_reduced.json \
  --family-label Qwen-14B \
  --output-dir /workspace/project/results/cass_sr_qwen14b/main_20260321a

python /workspace/project/scripts/make_cass_sr_reports.py \
  --qwen14b-main-dir /workspace/project/results/cass_sr_qwen14b/main_20260321a \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/cass_sr \
  --figure-dir /workspace/project/figures/cass_sr
```

Final `CASS-SR` read:

- `Qwen-14B` cluster-hard:
  - `RAW_PYTHON = 0.8650`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.8625`
  - `CASS_TARGET_POSTPROCESS_PATCH = 0.7050`
  - `CASS_TARGET_POSTPROCESS_PATCH - RAW_PYTHON = -0.1594 [-0.2100, -0.1125]`
  - `CASS_TARGET_POSTPROCESS_PATCH - OPERATOR_SCHEMA_TO_CODE_BASE = -0.1568 [-0.2025, -0.1125]`
- `Qwen-14B` generic-hard:
  - `RAW_PYTHON = 0.8800`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.8750`
  - `CASS_TARGET_POSTPROCESS_PATCH = 0.7200`
  - `CASS_TARGET_POSTPROCESS_PATCH - RAW_PYTHON = -0.1599 [-0.2250, -0.0950]`
  - `CASS_TARGET_POSTPROCESS_PATCH - OPERATOR_SCHEMA_TO_CODE_BASE = -0.1549 [-0.2200, -0.0850]`
- interpretation:
  - at larger scale, the target/postprocess patch remains the strongest frozen `CASS` ingredient inside the `Qwen` family
  - but its absolute value collapses against much stronger `RAW_PYTHON` / `OPERATOR` baselines
  - the strongest honest framing is now: `CASS` is most compelling as a small/medium-model intervention, while the portable core survives as an ingredient-level story at larger scale

No OpenAI API path was used for `CASS-SR`.

## CASS-FI

`CASS-FI` is the field-isolation clarification pack after `CASS-BD` and `CASS-SR`. It asks which sub-field inside the current target/postprocess story is actually portable:

- `TARGET_ONLY_PATCH`
- `POSTPROCESS_ONLY_PATCH`
- `DISCRETIZATION_ONLY_PATCH`
- `TARGET_PLUS_POSTPROCESS_PATCH`
- `ROLE_ONLY_REPLAY`

Freeze the `CASS-FI` manifest namespace:

```bash
python /workspace/project/scripts/cass_fi_prepare_manifests.py \
  --output-dir /workspace/project/data/cass_fi_manifests_20260321a \
  --report-path /workspace/project/reports/cass_fi_surface_manifest.md
```

Run the missing family/scale replays and reuse the already finished Granite replay:

```bash
bash /workspace/project/scripts/cass_fi_run_family_replay.sh \
  'Qwen/Qwen2.5-7B-Instruct' \
  /workspace/project/data/cass_fi_manifests_20260321a \
  qwen7b_cluster_field_replay \
  qwen7b_generic_field_replay \
  /workspace/project/data/cass_fi_manifests_20260321a/source_aliases \
  qwen7b_cluster_field_replay \
  qwen7b_generic_field_replay \
  /workspace/project/results/cass_fi_replay/qwen7b_20260322a \
  both \
  none \
  float16
```

Render the full `CASS-FI` synthesis across the four family/scale cells:

```bash
python /workspace/project/scripts/cass_fi_reports.py \
  --qwen7b-dirs \
    /workspace/project/results/cass_fi_replay/qwen7b_20260322a/qwen7b_cluster_field_replay__shard01of04 \
    /workspace/project/results/cass_fi_replay/qwen7b_20260322a/qwen7b_cluster_field_replay__shard02of04 \
    /workspace/project/results/cass_fi_replay/qwen7b_20260322a/qwen7b_cluster_field_replay__shard03of04 \
    /workspace/project/results/cass_fi_replay/qwen7b_20260322a/qwen7b_cluster_field_replay__shard04of04 \
    /workspace/project/results/cass_fi_replay/qwen7b_20260322a/qwen7b_generic_field_replay__shard01of04 \
    /workspace/project/results/cass_fi_replay/qwen7b_20260322a/qwen7b_generic_field_replay__shard02of04 \
    /workspace/project/results/cass_fi_replay/qwen7b_20260322a/qwen7b_generic_field_replay__shard03of04 \
    /workspace/project/results/cass_fi_replay/qwen7b_20260322a/qwen7b_generic_field_replay__shard04of04 \
  --mistral7b-dirs \
    /workspace/project/results/cass_fi_replay/mistral7b_20260321b/mistral7b_cluster_field_replay__shard01of04 \
    /workspace/project/results/cass_fi_replay/mistral7b_20260321b/mistral7b_cluster_field_replay__shard02of04 \
    /workspace/project/results/cass_fi_replay/mistral7b_20260321b/mistral7b_cluster_field_replay__shard03of04 \
    /workspace/project/results/cass_fi_replay/mistral7b_20260321b/mistral7b_cluster_field_replay__shard04of04 \
    /workspace/project/results/cass_fi_replay/mistral7b_cluster_remainder_tail9_20260321a \
    /workspace/project/results/cass_fi_replay/mistral7b_generic_20260321a/mistral7b_generic_field_replay__shard01of04 \
    /workspace/project/results/cass_fi_replay/mistral7b_generic_20260321a/mistral7b_generic_field_replay__shard02of04 \
    /workspace/project/results/cass_fi_replay/mistral7b_generic_20260321a/mistral7b_generic_field_replay__shard03of04 \
    /workspace/project/results/cass_fi_replay/mistral7b_generic_20260321a/mistral7b_generic_field_replay__shard04of04 \
  --granite-dirs \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_cluster_third_family_reduced__shard01of04 \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_cluster_third_family_reduced__shard02of04 \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_cluster_third_family_reduced__shard03of04 \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_cluster_third_family_reduced__shard04of04 \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_generic_third_family_reduced__shard01of04 \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_generic_third_family_reduced__shard02of04 \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_generic_third_family_reduced__shard03of04 \
    /workspace/project/results/cass_bd_granite/partial_replay_20260320a/gsm8k_train_generic_third_family_reduced__shard04of04 \
  --qwen14b-dirs \
    /workspace/project/results/cass_fi_replay/qwen14b_20260321a/qwen14b_cluster_field_replay__shard01of04 \
    /workspace/project/results/cass_fi_replay/qwen14b_20260321a/qwen14b_cluster_field_replay__shard02of04 \
    /workspace/project/results/cass_fi_replay/qwen14b_20260321a/qwen14b_cluster_field_replay__shard03of04 \
    /workspace/project/results/cass_fi_replay/qwen14b_20260321a/qwen14b_cluster_field_replay__shard04of04 \
    /workspace/project/results/cass_fi_replay/qwen14b_20260321a/qwen14b_generic_field_replay__shard01of04 \
    /workspace/project/results/cass_fi_replay/qwen14b_20260321a/qwen14b_generic_field_replay__shard02of04 \
    /workspace/project/results/cass_fi_replay/qwen14b_20260321a/qwen14b_generic_field_replay__shard03of04 \
    /workspace/project/results/cass_fi_replay/qwen14b_20260321a/qwen14b_generic_field_replay__shard04of04 \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/cass_fi \
  --figure-dir /workspace/project/figures/cass_fi
```

Final `CASS-FI` read:

- portable-core win counts:
  - `POSTPROCESS_ONLY_PATCH = 4`
  - `TARGET_PLUS_POSTPROCESS_PATCH = 2`
  - `CASS_TARGET_POSTPROCESS_PATCH = 1`
  - `TARGET_ONLY_PATCH = 1`
- family pattern:
  - `Granite-8B` and `Qwen-14B` both promote `POSTPROCESS_ONLY_PATCH` / `DISCRETIZATION_ONLY_PATCH`
  - `Mistral-7B` keeps `TARGET_PLUS_POSTPROCESS_PATCH` on top
  - `Qwen-7B` still tolerates or prefers target-side-inclusive variants on at least one surface
- interpretation:
  - the safest cross-family core is now best described as `postprocess/discretization-centered patching`
  - `target-side surgery` is useful on smaller-model cells but becomes risky on stronger or boundary cells

No OpenAI API path was used for `CASS-FI`.

## Code-Last

`Code-Last` is the bounded coding-side generalization pack after `CASS-FI`. It asks whether the broader late-stage targeted repair framing transfers to validator-rich function-level coding with deterministic unit-test validation.

Scope:

- benchmark stack:
  - `EvalPlus`
  - `HumanEval+`
  - `MBPP+`
- primary model:
  - `Qwen/Qwen2.5-7B-Instruct`
- frozen coding methods:
  - `DIRECT_CODE`
  - `FULL_REWRITE_FROM_FAILURE`
  - `LOCAL_TEST_GUIDED_PATCH`
  - `RETURN_POSTCOND_PATCH`
  - `BOUNDARY_PATCH`
  - `SIMPLE_CODE_GATE`
  - `LEARNED_CODE_GATE`
  - `ORACLE_POLICY`
- this is not repo-level APR, vulnerability repair, or a new coding methods branch

Freeze benchmark manifests:

```bash
python /workspace/project/scripts/code_last_prepare_benchmarks.py \
  --output-dir /workspace/project/data/code_last_manifests_20260323a \
  --report-path /workspace/project/reports/code_last_benchmark_audit.md
```

Run the corrected left-padding `Qwen` coding pack:

```bash
bash /workspace/project/scripts/code_last_run_qwen.sh \
  /workspace/project/data/code_last_manifests_20260323a \
  /workspace/project/results/code_last_main/qwen7b_direct_20260323c_leftpad \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad
```

Resume from the corrected direct outputs if needed:

```bash
bash /workspace/project/scripts/code_last_resume_qwen.sh \
  /workspace/project/data/code_last_manifests_20260323a \
  /workspace/project/results/code_last_main/qwen7b_direct_20260323c_leftpad \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad
```

Render the final tables/figures/reports from completed repair shards:

```bash
python /workspace/project/scripts/code_last_finalize.py \
  --repair-dirs \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_near_correct__shard01of04 \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_near_correct__shard02of04 \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_near_correct__shard03of04 \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_near_correct__shard04of04 \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_general_fail__shard01of04 \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_general_fail__shard02of04 \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_general_fail__shard03of04 \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_general_fail__shard04of04 \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/code_last \
  --figure-dir /workspace/project/figures/code_last
```

Outputs:

- reports:
  - `/workspace/project/reports/code_last_benchmark_audit.md`
  - `/workspace/project/reports/code_last_slice_report.md`
  - `/workspace/project/reports/code_last_main_report.md`
  - `/workspace/project/reports/code_last_failure_notes.md`
  - `/workspace/project/reports/code_last_summary_memo.md`
- results:
  - `/workspace/project/results/code_last_main/qwen7b_direct_20260323c_leftpad`
  - `/workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad`
- tables:
  - `/workspace/project/tables/code_last/code_last_summary.csv`
  - `/workspace/project/tables/code_last/code_last_pairwise.csv`
  - `/workspace/project/tables/code_last/code_last_failure_summary.csv`
- figures:
  - `/workspace/project/figures/code_last/near_correct_failure_type_chart.png`
  - `/workspace/project/figures/code_last/local_patch_vs_full_rewrite_on_coding.png`
  - `/workspace/project/figures/code_last/return_postcondition_vs_boundary_patch.png`
  - `/workspace/project/figures/code_last/coding_side_summary_figure.png`

Final `Code-Last` read:

- the public-pass / extended-fail coding region exists:
  - exact size `48`
  - relaxed main slice `56`
- that near-correct region is genuinely late-stage-like:
  - `boundary_or_off_by_one = 38 / 56`
  - `return_or_postcondition = 4 / 56`
  - combined late/boundary share `= 75.0%`
- pooled near-correct head-to-head is mixed:
  - `LOCAL_TEST_GUIDED_PATCH = 9 / 56 = 0.1607`
  - `FULL_REWRITE_FROM_FAILURE = 9 / 56 = 0.1607`
  - so local patch does not beat rewrite overall
- `HumanEval+` is the more favorable coding analogue, while `MBPP+` is noisier and slightly rewrite-favoring
- `BOUNDARY_PATCH` is the strongest narrow coding-side repair family in this bounded pack
- the broader late-stage framing transfers to coding only partially:
  - strong enough for appendix / future-work / talk support
  - not strong enough to claim universal local-patch superiority in code

Optional follow-ups:

- `Mistral-7B-Instruct-v0.3` reduced replication: not run
- `MGDebugger-lite` contextual subset: not run
- reason: the primary `Qwen` coding read is mixed and already sufficient to support the bounded conclusion

No OpenAI API path was used for `Code-Last`.

## Code-Last-R2

`Code-Last-R2` is the bounded coding clarification pack after `Code-Last`. It asks whether the mixed coding result becomes cleaner once we restrict to a genuinely repair-eligible strict slice, and whether that stricter read survives a reduced second-family replication.

Scope:

- validator-rich function-level coding only
- `EvalPlus` / `HumanEval+` / `MBPP+`
- not repo-level APR
- not vulnerability repair

Primary `Qwen` strict-slice replay and reporting:

```bash
python /workspace/project/scripts/code_last_r2_construct_slices.py \
  --direct-input-dirs \
  /workspace/project/results/code_last_main/qwen7b_direct_20260323c_leftpad/evalplus_direct_all__shard01of04 \
  /workspace/project/results/code_last_main/qwen7b_direct_20260323c_leftpad/evalplus_direct_all__shard02of04 \
  /workspace/project/results/code_last_main/qwen7b_direct_20260323c_leftpad/evalplus_direct_all__shard03of04 \
  /workspace/project/results/code_last_main/qwen7b_direct_20260323c_leftpad/evalplus_direct_all__shard04of04 \
  --repair-input-dirs \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_near_correct__shard01of04 \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_near_correct__shard02of04 \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_near_correct__shard03of04 \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_near_correct__shard04of04 \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_general_fail__shard01of04 \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_general_fail__shard02of04 \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_general_fail__shard03of04 \
  /workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad/evalplus_general_fail__shard04of04 \
  --manifest-root /workspace/project/data/code_last_r2_manifests_20260323a \
  --project-output-root /workspace/project/results/code_last_r2_main/qwen7b_projected_20260323a \
  --report-path /workspace/project/reports/code_last_r2_slice_report.md \
  --table-dir /workspace/project/tables/code_last_r2 \
  --strict-k 8
```

```bash
python /workspace/project/scripts/code_last_r2_finalize.py \
  --repair-dirs \
  /workspace/project/results/code_last_r2_main/qwen7b_projected_20260323a/strict_repair_eligible \
  /workspace/project/results/code_last_r2_main/qwen7b_projected_20260323a/relaxed_near_correct \
  /workspace/project/results/code_last_r2_main/qwen7b_projected_20260323a/contrast_broad_fail \
  /workspace/project/results/code_last_r2_main/qwen7b_projected_20260323a/boundary_heavy \
  /workspace/project/results/code_last_r2_main/qwen7b_projected_20260323a/return_only \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/code_last_r2 \
  --figure-dir /workspace/project/figures/code_last_r2 \
  --report-prefix code_last_r2
```

Optional reduced `Mistral` replication actually used in this branch:

```bash
bash /workspace/project/scripts/code_last_r2_run_mistral.sh \
  /workspace/project/data/code_last_manifests_20260323a \
  /workspace/project/data/code_last_r2_mistral_manifests_20260323a \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_direct_20260323a \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a
```

```bash
python /workspace/project/scripts/code_last_r2_finalize.py \
  --repair-dirs \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/strict_repair_eligible__shard01of04 \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/strict_repair_eligible__shard02of04 \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/strict_repair_eligible__shard03of04 \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/strict_repair_eligible__shard04of04 \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/relaxed_near_correct__shard01of04 \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/relaxed_near_correct__shard02of04 \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/relaxed_near_correct__shard03of04 \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/relaxed_near_correct__shard04of04 \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/code_last_r2 \
  --figure-dir /workspace/project/figures/code_last_r2 \
  --report-prefix code_last_r2_mistral
```

```bash
python /workspace/project/scripts/code_last_r2_model_diversity.py \
  --qwen-repair-dirs \
  /workspace/project/results/code_last_r2_main/qwen7b_projected_20260323a/strict_repair_eligible \
  /workspace/project/results/code_last_r2_main/qwen7b_projected_20260323a/relaxed_near_correct \
  /workspace/project/results/code_last_r2_main/qwen7b_projected_20260323a/contrast_broad_fail \
  /workspace/project/results/code_last_r2_main/qwen7b_projected_20260323a/boundary_heavy \
  /workspace/project/results/code_last_r2_main/qwen7b_projected_20260323a/return_only \
  --mistral-repair-dirs \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/strict_repair_eligible__shard01of04 \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/strict_repair_eligible__shard02of04 \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/strict_repair_eligible__shard03of04 \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/strict_repair_eligible__shard04of04 \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/relaxed_near_correct__shard01of04 \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/relaxed_near_correct__shard02of04 \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/relaxed_near_correct__shard03of04 \
  /workspace/project/results/code_last_r2_model_diversity/mistral7b_repairs_20260323a/relaxed_near_correct__shard04of04 \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/code_last_r2 \
  --figure-dir /workspace/project/figures/code_last_r2
```

Final `Code-Last-R2` read:

- the strict repair-eligible slice becomes much cleaner on `Qwen-7B`:
  - `n = 13`
  - all failures are `boundary_or_off_by_one`
  - `LOCAL = 0.2308`
  - `REWRITE = 0.1538`
- the positive strict direction is carried by `HumanEval+`; `MBPP+` strict remains flat
- the relaxed `Qwen` slice remains mixed:
  - `LOCAL = REWRITE = 0.1607`
- reduced `Mistral-7B` does not preserve the `Qwen` local-patch direction:
  - strict slice collapses to `4` `MBPP` tasks
  - strict: `REWRITE = 0.25`, `LOCAL = 0.0`
  - relaxed: `REWRITE = 0.1087`, `LOCAL = 0.0435`
- the most defensible coding-side analogue is therefore:
  - boundary-heavy, validator-rich, repair-eligible failure pockets
  - not universal local-patch superiority

No OpenAI API path was used for `Code-Last-R2`.

## Code-Last-R3

`Code-Last-R3` is the bounded HumanEval+-focused clarification pack after `Code-Last-R2`. It asks whether the positive coding-side signal becomes cleaner once we stay inside a larger multi-sampled HumanEval+ repair-eligible boundary-heavy pocket.

Scope:

- `HumanEval+` only as the primary signal surface
- `MBPP+` kept as prior contrast/support rather than the main surface
- validator-rich function-level coding only
- not repo-level APR
- not vulnerability repair

Prepare the frozen HumanEval+ multi-sample bank manifests:

```bash
python /workspace/project/scripts/code_last_r3_prepare_humaneval.py \
  --output-dir /workspace/project/data/code_last_r3_manifests_20260323a \
  --report-path /workspace/project/reports/code_last_r3_benchmark_audit.md \
  --samples-per-task 8 \
  --base-seed 13 \
  --shard-count 4
```

Primary `Qwen-7B` HumanEval+ run:

```bash
bash /workspace/project/scripts/code_last_r3_run_qwen.sh \
  /workspace/project/data/code_last_r3_manifests_20260323a \
  /workspace/project/results/code_last_r3_main/qwen7b_direct_20260323a \
  /workspace/project/results/code_last_r3_main/qwen7b_repairs_20260323a
```

If the main repair root closes before the contrast surface is fully evaluated, recover only the missing HumanEval+ broad-fail contrast surface in a fresh root:

```bash
ROOT=/workspace/project
MANIFEST_ROOT=/workspace/project/data/code_last_r3_manifests_20260323a
DIRECT_OUT=/workspace/project/results/code_last_r3_main/qwen7b_direct_20260323a
OUT=/workspace/project/results/code_last_r3_main/qwen7b_contrast_retry_20260323b
mkdir -p "$OUT" "$OUT/logs"
for shard in 01 02 03 04; do
  HF_HUB_DISABLE_XET=1 CUDA_VISIBLE_DEVICES=$((10#$shard - 1)) python "$ROOT/scripts/code_last_r3_collect_repairs.py" \
    --client hf_local \
    --input-dirs \
    "$DIRECT_OUT/humaneval_direct_multisample__shard01of04" \
    "$DIRECT_OUT/humaneval_direct_multisample__shard02of04" \
    "$DIRECT_OUT/humaneval_direct_multisample__shard03of04" \
    "$DIRECT_OUT/humaneval_direct_multisample__shard04of04" \
    --manifest "$MANIFEST_ROOT/shards/humaneval_contrast_broad_fail__shard${shard}of04.json" \
    --output-dir "$OUT/humaneval_contrast_broad_fail__shard${shard}of04" \
    --model-name Qwen/Qwen2.5-7B-Instruct \
    --local-quantization 4bit \
    --local-dtype float16 \
    --local-device-map cuda:0 \
    --local-max-model-len 4096 \
    --local-trust-remote-code \
    --batch-size 12 &
done
wait
for shard in 01 02 03 04; do
  python "$ROOT/scripts/code_last_r3_evaluate_repairs.py" \
    --input-dir "$OUT/humaneval_contrast_broad_fail__shard${shard}of04" \
    --output-dir "$OUT/humaneval_contrast_broad_fail__shard${shard}of04" \
    --eval-workers 12 &
done
wait
```

Finalize reporting from strict, relaxed, and contrast repair roots:

```bash
python /workspace/project/scripts/code_last_r3_finalize.py \
  --repair-dirs \
  /workspace/project/results/code_last_r3_main/qwen7b_repairs_20260323a/humaneval_strict_repair_eligible__shard01of04 \
  /workspace/project/results/code_last_r3_main/qwen7b_repairs_20260323a/humaneval_strict_repair_eligible__shard02of04 \
  /workspace/project/results/code_last_r3_main/qwen7b_repairs_20260323a/humaneval_strict_repair_eligible__shard03of04 \
  /workspace/project/results/code_last_r3_main/qwen7b_repairs_20260323a/humaneval_strict_repair_eligible__shard04of04 \
  /workspace/project/results/code_last_r3_main/qwen7b_repairs_20260323a/humaneval_relaxed_near_correct__shard01of04 \
  /workspace/project/results/code_last_r3_main/qwen7b_repairs_20260323a/humaneval_relaxed_near_correct__shard02of04 \
  /workspace/project/results/code_last_r3_main/qwen7b_repairs_20260323a/humaneval_relaxed_near_correct__shard03of04 \
  /workspace/project/results/code_last_r3_main/qwen7b_repairs_20260323a/humaneval_relaxed_near_correct__shard04of04 \
  /workspace/project/results/code_last_r3_main/qwen7b_contrast_retry_20260323b/humaneval_contrast_broad_fail__shard01of04 \
  /workspace/project/results/code_last_r3_main/qwen7b_contrast_retry_20260323b/humaneval_contrast_broad_fail__shard02of04 \
  /workspace/project/results/code_last_r3_main/qwen7b_contrast_retry_20260323b/humaneval_contrast_broad_fail__shard03of04 \
  /workspace/project/results/code_last_r3_main/qwen7b_contrast_retry_20260323b/humaneval_contrast_broad_fail__shard04of04 \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/code_last_r3 \
  --figure-dir /workspace/project/figures/code_last_r3 \
  --report-prefix code_last_r3
```

Final `Code-Last-R3` read:

- strict HumanEval+ repair-eligible pocket:
  - `12` completions from `3` tasks
  - all `boundary_or_off_by_one`
  - `LOCAL_TEST_GUIDED_PATCH = 0.5000`
  - `FULL_REWRITE_FROM_FAILURE = 0.3333`
- task-clustered strict local-minus-rewrite remains positive but underpowered:
  - `+0.1111 [0.0000, 0.3333]`
- relaxed HumanEval+ remains mixed:
  - `LOCAL = 0.2583`
  - `REWRITE = 0.2833`
- broad-fail contrast remains a boundary/control surface:
  - `LOCAL = 0.3100`
  - `REWRITE = 0.4300`
- the strongest coding-side analog is:
  - broader localized repair on boundary-heavy near-correct code
  - not return-only repair
  - not universal local-patch superiority

Optional follow-ups:

- `MBPP+` contrast rerun: not run
- `Mistral-7B-Instruct-v0.3` reduced replication: not run
- `MGDebugger-lite` contextual subset: not run
- reason: the HumanEval+ strict signal stayed positive but still covered only `3` tasks, so the expected information gain from expansion remained low

No OpenAI API path was used for `Code-Last-R3`.

## Code-Last-R4

`Code-Last-R4` is the high-power HumanEval+-focused coding lock attempt after `Code-Last-R3`. It asks whether the coding-side transfer becomes cleaner once we expand the HumanEval+ completion bank, keep only strict repair-eligible boundary-heavy slices, and judge the result at the task-clustered level.

### Exact Local Commands

Prepare the frozen HumanEval+ manifests:

```bash
python /workspace/project/scripts/code_last_r4_prepare_humaneval.py \
  --output-dir /workspace/project/data/code_last_r4_manifests_20260323a \
  --report-path /workspace/project/reports/code_last_r4_benchmark_audit.md \
  --initial-samples-per-task 32 \
  --extra-samples-per-task 32 \
  --base-seed 13 \
  --shard-count 4
```

Run the Qwen 32-sample bank on 4 GPUs:

```bash
ROOT=/workspace/project
MAN_ROOT=/workspace/project/data/code_last_r4_manifests_20260323a/bank32/shards
OUT=/workspace/project/results/code_last_r4_main/qwen7b_bank32_20260323a
for shard in 01 02 03 04; do
  CUDA_VISIBLE_DEVICES=$((10#$shard - 1)) HF_HUB_DISABLE_XET=1 \
  python "$ROOT/scripts/code_last_r4_collect_direct.py" \
    --client hf_local \
    --manifest "$MAN_ROOT/humaneval_direct_bank32__shard${shard}of04.json" \
    --output-dir "$OUT/humaneval_direct_bank32__shard${shard}of04" \
    --model-name Qwen/Qwen2.5-7B-Instruct \
    --local-quantization 4bit \
    --local-dtype float16 \
    --local-device-map cuda:0 \
    --local-max-model-len 4096 \
    --local-trust-remote-code \
    --temperature 0.8 \
    --top-p 0.95 \
    --batch-size 16 &
done
wait
```

Run public-only evaluation on the direct bank:

```bash
IN_ROOT=/workspace/project/results/code_last_r4_main/qwen7b_bank32_20260323a
OUT_ROOT=/workspace/project/results/code_last_r4_main/qwen7b_public_bank32_20260323a
find "$IN_ROOT" -mindepth 1 -maxdepth 1 -type d -name 'humaneval_*' | sort > "$OUT_ROOT/input_dirs.txt"
cat "$OUT_ROOT/input_dirs.txt" | xargs -I{} -P 4 bash -lc \
  'python /workspace/project/scripts/code_last_r4_evaluate_public.py --input-dir "$1" --output-dir "$2/$(basename "$1")" --diagnostic-limit 3 --eval-workers 12' \
  _ {} "$OUT_ROOT"
```

Build exact/relaxed candidate manifests, run exact extended evaluation, and construct slices:

```bash
python /workspace/project/scripts/code_last_r4_build_candidate_manifests.py \
  --public-input-dirs \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank32_20260323a/humaneval_direct_bank32__shard01of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank32_20260323a/humaneval_direct_bank32__shard02of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank32_20260323a/humaneval_direct_bank32__shard03of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank32_20260323a/humaneval_direct_bank32__shard04of04 \
  --output-dir /workspace/project/results/code_last_r4_main/qwen7b_candidates_bank32_20260323a \
  --report-path /workspace/project/reports/code_last_r4_candidate_manifest_report_bank32.md

python /workspace/project/scripts/code_last_r4_evaluate_extended.py \
  --raw-input-dirs \
    /workspace/project/results/code_last_r4_main/qwen7b_bank32_20260323a/humaneval_direct_bank32__shard01of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_bank32_20260323a/humaneval_direct_bank32__shard02of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_bank32_20260323a/humaneval_direct_bank32__shard03of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_bank32_20260323a/humaneval_direct_bank32__shard04of04 \
  --manifest /workspace/project/results/code_last_r4_main/qwen7b_candidates_bank32_20260323a/humaneval_exact_public_pass_candidates.json \
  --output-dir /workspace/project/results/code_last_r4_main/qwen7b_extended_exact_bank32_20260323a \
  --diagnostic-limit 3 \
  --eval-workers 12

python /workspace/project/scripts/code_last_r4_construct_slices.py \
  --public-input-dirs \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank32_20260323a/humaneval_direct_bank32__shard01of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank32_20260323a/humaneval_direct_bank32__shard02of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank32_20260323a/humaneval_direct_bank32__shard03of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank32_20260323a/humaneval_direct_bank32__shard04of04 \
  --extended-input-dirs /workspace/project/results/code_last_r4_main/qwen7b_extended_exact_bank32_20260323a \
  --manifest-root /workspace/project/results/code_last_r4_main/qwen7b_bank32_slices_20260323a \
  --report-path /workspace/project/reports/code_last_r4_slice_report_bank32_checkpoint.md \
  --completion-bank-report-path /workspace/project/reports/code_last_r4_completion_bank_report_bank32_checkpoint.md \
  --table-dir /workspace/project/tables/code_last_r4/bank32_final \
  --project-output-root /workspace/project/results/code_last_r4_main/qwen7b_merged64_20260323a/projected_direct_records_bank32_final \
  --samples-per-task-total 32 \
  --status-json /workspace/project/results/code_last_r4_main/qwen7b_bank32_20260323a/bank32_status_final.json
```

After the pre-registered escalation trigger fired, repeat the same direct/public path for the extra 32 samples/task bank and then construct the merged 64-sample frozen slices. The final frozen slice construction command was:

```bash
python /workspace/project/scripts/code_last_r4_construct_slices.py \
  --public-input-dirs \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank32_20260323a/humaneval_direct_bank32__shard01of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank32_20260323a/humaneval_direct_bank32__shard02of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank32_20260323a/humaneval_direct_bank32__shard03of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank32_20260323a/humaneval_direct_bank32__shard04of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank64extra_20260323a/humaneval_direct_bank64_extra__shard01of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank64extra_20260323a/humaneval_direct_bank64_extra__shard02of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank64extra_20260323a/humaneval_direct_bank64_extra__shard03of04 \
    /workspace/project/results/code_last_r4_main/qwen7b_public_bank64extra_20260323a/humaneval_direct_bank64_extra__shard04of04 \
  --extended-input-dirs \
    /workspace/project/results/code_last_r4_main/qwen7b_extended_exact_bank32_20260323a \
    /workspace/project/results/code_last_r4_main/qwen7b_bank64extra_20260323a/humaneval_extended_exact_candidates_bank64extra_final_rerun \
    /workspace/project/results/code_last_r4_main/qwen7b_merged64_20260323a/humaneval_extended_relaxed_candidates_merged64_final \
  --manifest-root /workspace/project/results/code_last_r4_main/qwen7b_merged64_20260323a/frozen_manifests_all_final \
  --report-path /workspace/project/reports/code_last_r4_slice_report.md \
  --completion-bank-report-path /workspace/project/reports/code_last_r4_completion_bank_report.md \
  --table-dir /workspace/project/tables/code_last_r4/final_all_bank64 \
  --project-output-root /workspace/project/results/code_last_r4_main/qwen7b_merged64_20260323a/projected_direct_records_all_final \
  --samples-per-task-total 64 \
  --status-json /workspace/project/results/code_last_r4_main/qwen7b_merged64_20260323a/final_all_status.json
```

Run the Qwen repair pack, evaluate it, apply the strict top-off, and finalize:

```bash
python /workspace/project/scripts/code_last_r4_finalize.py \
  --repair-dirs $(find /workspace/project/results/code_last_r4_main/qwen7b_repairs_eval_strict_contrast_20260323a /workspace/project/results/code_last_r4_main/qwen7b_repairs_eval_relaxed_20260323a /workspace/project/results/code_last_r4_main/qwen7b_repairs_eval_strict_topoff_20260323a -mindepth 1 -maxdepth 1 -type d \( -name 'humaneval_*' -o -name 'strict_topoff_bundle*' \) | sort) \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/code_last_r4 \
  --figure-dir /workspace/project/figures/code_last_r4 \
  --report-prefix code_last_r4
```

Optional reduced Mistral replication on the Qwen Tier2 task union:

```bash
python /workspace/project/scripts/code_last_r4_collect_direct.py \
  --client hf_local \
  --manifest /workspace/project/results/code_last_r4_model_diversity/mistral7b_tier2_subset_20260323a/manifests/shards/humaneval_mistral_tier2_union_bank64__shard01of04.json \
  --output-dir /workspace/project/results/code_last_r4_model_diversity/mistral7b_direct_20260323a/humaneval_mistral_tier2_union_bank64__shard01of04 \
  --model-name mistralai/Mistral-7B-Instruct-v0.3 \
  --local-quantization 4bit \
  --local-dtype float16 \
  --local-device-map cuda:0 \
  --local-max-model-len 4096 \
  --local-trust-remote-code \
  --temperature 0.8 \
  --top-p 0.95 \
  --batch-size 16
```

Then repeat the same public-manifest-extended-slice-repair path under:

- `/workspace/project/results/code_last_r4_model_diversity/mistral7b_public_20260323a`
- `/workspace/project/results/code_last_r4_model_diversity/mistral7b_candidates_20260323a`
- `/workspace/project/results/code_last_r4_model_diversity/mistral7b_extended_exact_20260323a`
- `/workspace/project/results/code_last_r4_model_diversity/mistral7b_slices_20260323a`
- `/workspace/project/results/code_last_r4_model_diversity/mistral7b_repairs_20260323a`
- `/workspace/project/results/code_last_r4_model_diversity/mistral7b_repairs_eval_20260323a`

### Final `Code-Last-R4` Read

- Qwen strict HumanEval+ pocket became meaningfully larger:
  - Tier1 `46` completions / `5` tasks
  - Tier2 `203` completions / `8` tasks
  - Tier3 `215` completions / `11` tasks
- strict tiers remained overwhelmingly `boundary_or_off_by_one`
- Qwen local patch vs rewrite:
  - Tier1 task-clustered `+0.2000 [0.0000, 0.4000]`
  - Tier2 task-clustered `+0.1014 [0.0139, 0.2264]`
  - Tier3 task-clustered `+0.0737 [0.0000, 0.1728]`
- the cleanest coding-side analog is:
  - broader localized patching on boundary-heavy near-correct code
  - not `BOUNDARY_PATCH` alone
  - not `RETURN_POSTCOND_PATCH` alone
- relaxed near-correct remains mixed and broad-fail remains negative for local patch
- optional reduced `Mistral` replication stayed tiny and unfavorable:
  - Tier1 `12` completions / `1` task, all methods `0`
  - Tier2 `22` completions / `2` tasks
  - `REWRITE = 0.1818`, `LOCAL = 0.0455`
- final coding interpretation:
  - appendix-level support for late-stage targeted repair on a narrow HumanEval+ strict pocket
  - no cross-family coding portability claim

No OpenAI API path was used for `Code-Last-R4`.

## `LACE-FULL` Full-Scale Format Lock-And-Transfer Pack

Freeze the full screened `IFEval` and full `IFBench` manifests:

```bash
python /workspace/project/scripts/lace_full_prepare_manifests.py \
  --output-dir /workspace/project/data/lace_full_format_manifests_20260324a \
  --ifeval-limit 400 \
  --ifbench-limit 300 \
  --ifeval-max-min-words 150 \
  --nshards 4 \
  --seed 13
```

Run the full `Qwen-7B` and `Mistral-7B` packs with four shard-parallel workers:

```bash
bash /workspace/project/scripts/lace_full_run_family.sh \
  'Qwen/Qwen2.5-7B-Instruct' \
  /workspace/project/results/lace_full_qwen/qwen7b_full_20260324a \
  /workspace/project/data/lace_full_format_manifests_20260324a/shards \
  none \
  float16 \
  4096 \
  1

bash /workspace/project/scripts/lace_full_run_family.sh \
  'mistralai/Mistral-7B-Instruct-v0.3' \
  /workspace/project/results/lace_full_mistral/mistral7b_full_20260324a \
  /workspace/project/data/lace_full_format_manifests_20260324a/shards \
  none \
  float16 \
  4096 \
  1
```

Run the optional `Qwen-14B` scale pack on the same frozen surfaces using the stable local `4bit` path:

```bash
HF_HUB_DISABLE_XET=1 bash /workspace/project/scripts/lace_full_run_family.sh \
  'Qwen/Qwen2.5-14B-Instruct' \
  /workspace/project/results/lace_full_qwen14b/qwen14b_full_20260324a \
  /workspace/project/data/lace_full_format_manifests_20260324a/shards \
  4bit \
  float16 \
  4096 \
  1
```

Finalize the full reports, tables, and figures:

```bash
python /workspace/project/scripts/lace_full_make_reports.py \
  --qwen-ifeval-pattern '/workspace/project/results/lace_full_qwen/qwen7b_full_20260324a/ifeval_shard*of04/per_example.jsonl' \
  --qwen-ifbench-pattern '/workspace/project/results/lace_full_qwen/qwen7b_full_20260324a/ifbench_shard*of04/per_example.jsonl' \
  --mistral-ifeval-pattern '/workspace/project/results/lace_full_mistral/mistral7b_full_20260324a/ifeval_shard*of04/per_example.jsonl' \
  --mistral-ifbench-pattern '/workspace/project/results/lace_full_mistral/mistral7b_full_20260324a/ifbench_shard*of04/per_example.jsonl' \
  --qwen14-ifeval-pattern '/workspace/project/results/lace_full_qwen14b/qwen14b_full_20260324a/ifeval_shard*of04/per_example.jsonl' \
  --qwen14-ifbench-pattern '/workspace/project/results/lace_full_qwen14b/qwen14b_full_20260324a/ifbench_shard*of04/per_example.jsonl' \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/lace_full \
  --figure-dir /workspace/project/figures/lace_full
```

### Final `LACE-FULL` Read

- full screened `IFEval` is now the strongest non-math validator-rich domain in the repo:
  - `Qwen-7B`: `SIMPLE_BEST_GATE - ALWAYS_FULL_REWRITE = +0.1556 [+0.0922, +0.2270]`
  - `Mistral-7B`: `SIMPLE_BEST_GATE_TRANSFER - ALWAYS_FULL_REWRITE = +0.1130 [+0.0426, +0.1773]`
  - `Qwen-14B`: `SIMPLE_BEST_GATE - ALWAYS_FULL_REWRITE = +0.1561 [+0.0922, +0.2199]`
- full `IFBench` remains the harder boundary surface:
  - `Qwen-7B`: `+0.1452 [+0.0680, +0.2330]`
  - `Mistral-7B`: `+0.0686 [+0.0000, +0.1359]`
  - `Qwen-14B`: `+0.0472 [-0.0291, +0.1262]`
- the simplest portable rule family remains the cleanest main-paper story:
  - it stays above naive rewrite on the full primary-family and non-Qwen reruns
  - it remains competitive with or above learned transfer
- final paper positioning:
  - output-constraint tasks now deserve co-main placement with math
  - `IFBench` and `Qwen-14B` define the honest harder-scale boundary

## `UNIFY-FULL` Cross-Domain Unification Pack

`UNIFY-FULL` is a frozen-trace analysis pack. It does not launch a new generation-heavy run. Instead it reuses the completed math-side `CASS-FI/CASS-SR` traces and the completed format-side `LACE-FULL` traces to test whether both domains can share one abstract intervention geometry:

- `NO_INTERVENTION`
- `LOCAL_REPAIR`
- `GLOBAL_REWRITE_OR_RESTART`

with the frozen domain mapping:

- math local repair -> postprocess-centered replay primitive
- format local repair -> `solve_then_format`

Run the unification analysis:

```bash
python /workspace/project/scripts/unify_full_make_reports.py
```

This produces:

- reports:
  - `/workspace/project/reports/unify_full_feature_audit.md`
  - `/workspace/project/reports/unify_full_qwen_report.md`
  - `/workspace/project/reports/unify_full_mistral_report.md`
  - `/workspace/project/reports/unify_full_qwen14b_report.md`
  - `/workspace/project/reports/unify_full_synthesis.md`
  - `/workspace/project/reports/unify_full_failure_notes.md`
  - `/workspace/project/reports/unify_full_summary_memo.md`
- tables:
  - `/workspace/project/tables/unify_full/unify_full_summary.csv`
  - `/workspace/project/tables/unify_full/unify_full_pairwise.csv`
  - `/workspace/project/tables/unify_full/unify_full_transfer.csv`
  - `/workspace/project/tables/unify_full/unify_full_domain_gap.csv`
  - `/workspace/project/tables/unify_full/unify_full_alignment.csv`
- figures:
  - `/workspace/project/figures/unify_full/unify_full_domain_vs_pooled.png`
  - `/workspace/project/figures/unify_full/unify_full_transfer_plot.png`
  - `/workspace/project/figures/unify_full/unify_full_family_plot.png`
  - `/workspace/project/figures/unify_full/unify_full_alignment_heatmap.png`
  - `/workspace/project/figures/unify_full/unify_full_qwen14b_scale_plot.png`
  - `/workspace/project/figures/unify_full/unify_full_positioning_summary.png`

Minimal verification:

```bash
pytest -q /workspace/project/tests/test_unify_full_core.py /workspace/project/tests/test_lace_full_core.py
```

### Final `UNIFY-FULL` Read

- pooled-vs-rewrite overall:
  - `Qwen-7B`: `+0.2176 [+0.1799, +0.2578]`
  - `Mistral-7B`: `+0.1694 [+0.1300, +0.2115]`
  - `Qwen-14B`: `+0.1084 [+0.0694, +0.1458]`
- the shared abstraction is strongest in `final_requirement_realization`:
  - math late target/postprocess failures
  - format constraint-realization failures
- the pooled simple rule stays close to the best domain-tuned shared-action rules:
  - exact tie on `Qwen-7B`
  - small gap on `Mistral-7B`
  - exact tie on `Qwen-14B`
- paper-level interpretation:
  - math and validator-rich output-constraint tasks can now be presented as two manifestations of one shared late-stage targeted-repair problem
  - the honest caveat is that domain-tuned simple criteria still matter at the margins on harder boundary surfaces

## `UNIFY-LIVE-FULL-R2` Completion / Integrity-Lock Pack

`UNIFY-LIVE-FULL-R2` starts from the already collected live banks and does three things:

- freezes the shared manifests / feature map / split seeds
- audits and locks the completed `Qwen-7B` and `Mistral-7B` banks
- evaluates pooled-vs-domain-specific policies prospectively, then attempts bounded `Qwen-14B` completion if stable

Prepare the frozen R2 manifest bundle:

```bash
python /workspace/project/scripts/unify_live_full_r2_prepare.py \
  --output-dir /workspace/project/results/unify_live_full_r2_shared \
  --report-path /workspace/project/reports/unify_live_full_r2_feature_audit.md
```

Run the mandatory integrity audit on the current live banks:

```bash
python /workspace/project/scripts/unify_live_full_r2_integrity.py \
  --qwen-root /workspace/project/results/unify_live_full_qwen/qwen7b_live_20260324a \
  --mistral-root /workspace/project/results/unify_live_full_mistral/mistral7b_live_20260324a \
  --qwen14-root /workspace/project/results/unify_live_full_qwen14b/qwen14b_live_20260324a \
  --qwen-out /workspace/project/results/unify_live_full_r2_qwen \
  --mistral-out /workspace/project/results/unify_live_full_r2_mistral \
  --qwen14-out /workspace/project/results/unify_live_full_r2_qwen14b
```

Generate the R2 reports, tables, and figures:

```bash
python /workspace/project/scripts/unify_live_full_r2_make_reports.py \
  --manifest-root /workspace/project/results/unify_live_full_r2_shared \
  --qwen-root /workspace/project/results/unify_live_full_qwen/qwen7b_live_20260324a \
  --mistral-root /workspace/project/results/unify_live_full_mistral/mistral7b_live_20260324a \
  --qwen14-root /workspace/project/results/unify_live_full_r2_qwen14b/qwen14b_attempt2_20260326b \
  --qwen-results /workspace/project/results/unify_live_full_r2_qwen \
  --mistral-results /workspace/project/results/unify_live_full_r2_mistral \
  --qwen14-results /workspace/project/results/unify_live_full_r2_qwen14b \
  --report-dir /workspace/project/reports \
  --table-dir /workspace/project/tables/unify_live_full_r2 \
  --figure-dir /workspace/project/figures/unify_live_full_r2 \
  --qwen14-attempts-json /workspace/project/results/unify_live_full_r2_qwen14b/qwen14_attempts.json
```

If `Qwen-14B` needs a clean restart under `R2`, use the already-validated local `4bit` path:

```bash
python /workspace/project/scripts/unify_live_full_r2_prepare.py \
  --output-dir /workspace/project/results/unify_live_full_r2_shared_qwen14_8way \
  --report-path /workspace/project/reports/unify_live_full_r2_feature_audit_qwen14_8way.md \
  --nshards 8
```

Then launch the corrected high-util `Qwen-14B` restart with `8`-way sharding and `2` worker slots per GPU:

```bash
UNIFY_LIVE_GPU_SLOTS_PER_DEVICE=2 HF_HUB_DISABLE_XET=1 \
  bash /workspace/project/scripts/unify_live_full_run_family.sh \
  'Qwen/Qwen2.5-14B-Instruct' \
  qwen14b_r2 \
  /workspace/project/results/unify_live_full_r2_shared_qwen14_8way \
  /workspace/project/results/unify_live_full_r2_qwen14b/qwen14b_attempt2_20260326b \
  4bit \
  float16 \
  4096 \
  1
```

Restart / recovery note:

- the first clean `Qwen-14B` restart on the original `4`-shard root was halted because it stayed around `30–40%` GPU utilization while using only about `11 GB` per GPU
- the corrected `8`-way + dual-slot path reached about `22 GB` per GPU and `100%` utilization in the early cluster-raw window
- the same corrected path was resumed on `2026-03-27` after a stalled replay checkpoint and then completed the full `Qwen-14B` bank at `/workspace/project/results/unify_live_full_r2_qwen14b/qwen14b_attempt2_20260326b`
- if a `Qwen-14B` worker drops, preserve the failed attempt root, capture the log filenames in the collection report, and restart cleanly under a new sibling run root such as `qwen14b_attempt3`
- do not overwrite the earlier partial `UNIFY-LIVE-FULL` root; treat it as frozen incomplete evidence

Quick watch command:

```bash
python /workspace/project/scripts/unify_live_full_r2_watch_qwen14.py --run-root /workspace/project/results/unify_live_full_r2_qwen14b/qwen14b_attempt2_20260326b
```

Minimal verification:

```bash
pytest -q \
  /workspace/project/tests/test_unify_live_full_r2_core.py \
  /workspace/project/tests/test_unify_live_full_r2_reporting.py
```
