# Research Log

## 2026-03-26

### UNIFY-LIVE-FULL-R2 launch and Qwen-14B throughput correction

- `UNIFY-LIVE-FULL-R2` artifacts were created under:
  - `reports/unify_live_full_r2_*.md`
  - `results/unify_live_full_r2_*`
  - `tables/unify_live_full_r2/`
  - `figures/unify_live_full_r2/`
- The frozen shared action space was locked as:
  - `NO_INTERVENTION`
  - `LOCAL_REPAIR`
  - `GLOBAL_REWRITE_OR_RESTART`
- The shared split seeds were locked as:
  - `13`
  - `29`
  - `47`
- The completed fresh `Qwen-7B` and `Mistral-7B` banks were integrity-audited and marked paper-safe.
- Prospective pooled-vs-domain-specific evaluation was completed on both 7B families before resuming 14B collection work.

### Qwen-14B runtime correction after direct observation

- Clean restart `attempt1_20260326a` was launched against the original `4`-shard `R2` manifest root.
- The run was stable and produced first rows, but the generation-heavy window remained materially under target:
  - observed early GPU utilization stayed roughly in the `30–40%` range
  - observed memory use stayed around `~11 GB` per `24 GB` GPU
- Per the registered execution rule, that under-utilized path was halted instead of being allowed to continue.

### Throughput fix applied before continuing

- `scripts/unify_live_full_run_family.sh` was upgraded to support `UNIFY_LIVE_GPU_SLOTS_PER_DEVICE`, allowing multiple workers on one GPU when memory allows.
- A same-GPU dual-slot smoke on `Qwen/Qwen2.5-14B-Instruct` `4bit` succeeded:
  - one `RTX 3090` reached about `22.1 GB` allocated
  - the same smoke hit `100%` GPU utilization
- The actual concurrency bottleneck was then identified:
  - the original `Qwen-14B` path still had only `4` shards per phase, so dual-slot scheduling alone could not raise worker count above `4`
- A `Qwen-14B`-specific `8`-way manifest root was prepared at:
  - `/workspace/project/results/unify_live_full_r2_shared_qwen14_8way`
- A corrected clean restart `attempt2_20260326b` was launched against the `8`-way root with:
  - `UNIFY_LIVE_GPU_SLOTS_PER_DEVICE=2`
  - `hf_local`
  - `4bit`
  - `float16`
  - `max_model_len=4096`
- Early corrected-attempt observation:
  - all `4` GPUs reached roughly `22.2–22.6 GB` allocated
  - all `4` GPUs hit `100%` SM in the early cluster-raw window
  - first `per_example.jsonl` rows began to accumulate under the corrected attempt root

## 2026-03-24

### UNIFY-LIVE-FULL objective

Run a bounded prospective cross-domain deployment pack after `UNIFY-FULL`.

This phase is not a new methods branch. It asks only:

1. whether math and validator-rich output-constraint tasks still support one shared late-stage requirement-realization geometry on fresh online runs
2. whether a pooled simple rule remains close to the best domain-tuned simple rules prospectively
3. whether that pooled rule remains above naive rewrite/restart on `Qwen-7B` and `Mistral-7B`
4. whether `Qwen-14B` preserves the same geometry or compresses the gains

### Registered runtime estimate before heavy runs

- `Qwen-7B` full prospective bank: `6–10 hours`
- `Mistral-7B` full prospective bank: `6–10 hours`
- `Qwen-14B` full prospective bank: `6–10 hours`
- policy fitting / repeated split evaluation / synthesis: `2–4 hours`
- total expected end-to-end: `20–34 hours`
- if a model is unstable and skipped: `14–24 hours`

### Practical local estimate before launch

Frozen surface sizes in the current workspace:

- math cluster-hard: `1515`
- math generic-hard: `483`
- screened `IFEval`: `381`
- `IFBench`: `300`

Working local estimate from prior full-pack throughput plus the new fresh three-action bank requirement:

- `Qwen-7B` prospective bank: `3.5–6.0 hours`
- `Mistral-7B` prospective bank: `4.2–7.0 hours`
- `Qwen-14B` prospective bank: `5.5–9.0 hours`
- policy fitting / figures / summary / tests: `1.5–3.0 hours`
- practical end-to-end expectation with all three models stable: `14.5–25.0 hours`

Runtime policy entering launch:

- generation-heavy phases must use all `4` GPUs
- target sustained utilization during generation-heavy windows: `> 90%`
- validator-only phases may be CPU-bound
- if the first hour deviates by more than `25%` from the working estimate, update this runtime estimate before continuing

### Frozen execution plan before launch

- keep the shared abstract action space fixed:
  - `NO_INTERVENTION`
  - `LOCAL_REPAIR`
  - `GLOBAL_REWRITE_OR_RESTART`
- keep the domain-specific local executors frozen:
  - math local repair: postprocess/discretization-centered replay primitive
  - format local repair: strongest frozen local format executor from `LACE-FULL`
- use at least `3` split seeds for prospective train / calibration / eval stability
- collect fresh online traces for all three abstract actions on all four surfaces before policy fitting
- do not reuse frozen trace re-analysis as the main evidence

### Runtime update after early Qwen-7B live throughput

- During the first hour of the `Qwen-7B` prospective bank, `cluster-hard raw` completed `332` examples in `3659s`.
- That implies `~4.64h` for the full `cluster-hard raw` phase alone if throughput remains stable.
- Generation-heavy utilization remained healthy through the first hour:
  - early `sm` mean: `93.44`
  - mid-window `sm` mean: `94.64`
- The deviation from the preregistered working local estimate is well above `25%`, so the wall-clock estimate is updated here before continuing.

Revised practical estimate:

- `Qwen-7B` prospective bank: `9–12 hours`
- `Mistral-7B` prospective bank: `10–13 hours`
- `Qwen-14B` prospective bank: `12–16 hours`
- policy fitting / synthesis / figures / tests: `2–3 hours`
- revised practical end-to-end expectation with all three models stable: `33–44 hours`
- if one model is unstable and skipped: `21–29 hours`

## 2026-03-17

### LAST-PACK objective

Run a bounded empirical generalization and criterion-clarification support pack for the frozen `CASS` result after `CASS-R4`.

This phase is not a new methods branch. It asks only:

1. whether harder math failures concentrate later than easier math failures
2. whether localized repair beats full restart when the failure is late and localized
3. whether that philosophy transfers beyond math
4. whether a simple intervention criterion can decide between local repair and restart

### Registered runtime estimate before heavy runs

- math late-stage existing-trace analysis: `1–2 hours`
- planning pack:
  - setup + pilot hardness check: `45–75 minutes`
  - main collection: `3–5 hours`
- format / instruction-following pack:
  - `IFEval` + `IFBench`: `2–4 hours`
  - planning-format bridge slice: `1–2 hours`
- cross-module analysis / figures / memos: `1–2 hours`
- optional second-model reduced replication: `+3–4 hours`
- total expected end-to-end: `9–15 hours`
- with second-model support: `12–18 hours`

Practical expectation before launch:

- math should mostly reuse frozen `CASS` traces
- the heavy runtime should come from:
  - planning direct / restart / suffix-repair collection
  - `IFEval` / `IFBench` direct-vs-repair collection
  - optional `Qwen/Qwen2.5-Math-7B-Instruct` reduced replication

### Runtime update after smoke stabilization

- The initial estimate was materially conservative.
- Main reasons:
  - math Module A can mostly reuse frozen `CASS` / `CASS-R3` traces
  - the planning pack was pivoted from `gridworld` to a lower-entropy `lineworld` validator domain after the pilot showed that 2D coordinate tracking, not localized repair, was the dominant failure source
  - the format pack now uses official `IFEval` / `IFBench` validators plus deterministic constraint-only patching for exact-count failures, which reduces repeated LLM repair passes

Revised pre-heavy-run estimate:

- math late-stage trace analysis: `20–35 minutes`
- planning lineworld main (`800` tasks, 4 GPUs): `25–35 minutes`
- `IFEval` main (`400` examples, 4 GPUs): `35–50 minutes`
- `IFBench` main (`300` examples, 4 GPUs): `25–40 minutes`
- planning-format bridge (`200` examples, 4 GPUs): `15–25 minutes`
- synthesis / criterion / figures / memo: `90–150 minutes`
- optional second-model reduced replication: `+90–150 minutes`
- practical end-to-end expectation under the stabilized local path: `3.5–5.5 hours`

### Comparator / conceptual-anchor audit outcome before execution

- `Localizing and Correcting Errors for LLM-based Planners` supports using validator-localized repair in planning, but does not justify importing a heavy new planning stack.
- `Decoupling Task-Solving and Output Formatting in LLM Generation` supports solve-then-format separation on output-constrained tasks.
- `LLMs Are Biased Towards Output Formats!` supports explicit format-vs-semantics disentangling.
- `IFEval` is directly usable as a verifiable constraint-following surface from Hugging Face in this environment.
- `IFBench` is usable from Hugging Face for data and from the official repo for evaluation logic; this phase will treat it as a true beyond-math probe.

### Surface plan before execution

Module A math surfaces:

- easy floor: existing `asdiv_easy_main`
- medium: existing `gsm8k_train_generic_main`
- hard: existing `gsm8k_train_cluster_main`

Module B planning surface:

- deterministic lineworld with easy/hard splits defined by horizon length and prerequisite-detour burden
- gridworld is retained only as a discarded pilot because it over-measured 2D coordinate tracking capacity rather than localized repair quality

Module C format surfaces:

- `IFEval`
- `IFBench`
- planning-format bridge slice for semantics-vs-format disentangling

### Engineering status before heavy runs

- `last_pack` plan registered in `reports/last_pack_plan.md`
- no API path will be used in this phase
- `Qwen/Qwen2.5-7B-Instruct` on 4x `RTX 3090` remains the primary execution path

## 2026-03-15

### CASS-R4 objective

Run a bounded fairness-and-generalization reinforcement phase for the frozen `CASS` result after `CASS-R3`.

This phase is not a new methods branch. It asks only:

1. whether the comparison to `PRISM` can survive reviewer scrutiny under a stronger-fidelity implementation
2. whether the comparison to `F1` can survive reviewer scrutiny under a more benchmark-aligned bridge slice
3. whether the `CASS` directional story survives a reduced second-model replication

### Registered runtime estimate before heavy runs

- comparator fidelity audit + setup: `45–75 minutes`
- PRISM official-style data generation / adapter run / inference: `5–8 hours`
- F1 bridge-slice run: `2–4 hours`
- secondary-model reduced replication: `4–6 hours`
- offline statistics / figures / memos: `1–2 hours`
- optional API micro-diagnostic: `30–60 minutes`
- total expected end-to-end: `12–20 hours`
- if the PRISM official path is heavier than expected: `15–24 hours`

Practical expectation before launch:

- the frozen primary surfaces can partially reuse existing structure from `CASS-R3`
- the dominant new runtime cost should come from:
  - `PRISM_HIGH_FIDELITY` adapter training + evaluation
  - `F1_HIGH_FIDELITY` bridge pack
  - `Qwen/Qwen2.5-Math-7B-Instruct` reduced replication

### Comparator fidelity audit outcome before execution

- `PRISM` is a direct comparator and official code exists.
- The official repo was inspected locally under `/workspace/PRISM_official`.
- End-to-end direct reuse is not appropriate for this repo's frozen arithmetic surfaces.
- Therefore `CASS-R4` uses `PRISM_HIGH_FIDELITY` as a stronger-faithfulness local adaptation that preserves:
  - multi-strategy routing
  - offline strategy-supervision data
  - lightweight adapter training
  - thresholded adaptive routing
- `Formula-One Prompting` is also a direct comparator, but no low-friction official code path was confirmed here.
- Therefore `CASS-R4` uses `F1_HIGH_FIDELITY` as a stronger-faithfulness equation-first adaptation on:
  - the frozen primary surface
  - a new bridge slice for benchmark alignment

### Surface plan before execution

Frozen reference surfaces:

- primary cluster-hard surface from `CASS-R3`
- generic-hard reference surface from `CASS-R3`

New bounded fairness surfaces:

- `PRISM`-aligned mixed arithmetic surface:
  - `gsm8k` test
  - bounded `svamp`
  - bounded `asdiv`
- `F1` bridge slice:
  - geometry / ratio / average / percent-heavy slice built from existing tagged data

### Engineering status before heavy runs

- `src/dart_research/cass_r4/` package created
- `scripts/cass_r4_*.py` created
- `make_cass_r4_reports.py` created
- `tests/test_cass_r4_core.py` added
- targeted regression suite result:
  - `17 passed, 2 warnings`

### Immediate next steps

1. generate `CASS-R4` manifests
2. run same-model collection on frozen primary + fairness surfaces
3. train/apply `PRISM_HIGH_FIDELITY`
4. run reduced secondary-model replication
5. aggregate reports, figures, and submission-readiness memo

### CASS-R4 execution update and final outcome

- No API diagnostic was needed in the final path.
- Additional API spend for `CASS-R4`: `$0`.

Actual completed collection/runtime accounting:

- primary frozen-surface `F1_HIGH_FIDELITY` augmentation:
  - `2395s` (`39.9m`)
- PRISM-aligned mixed surface:
  - clean remainder pass: `4638s` (`77.3m`)
  - note: the first mixed pass was intentionally interrupted after a load-balance failure, so the clean deterministic runtime excludes that partial aborted attempt
- F1 bridge slice:
  - `1569s` (`26.2m`)
- secondary-model reduced replication:
  - main pass: `5636s` (`93.9m`)
  - parse-fix retry on failed shards: `2160s` (`36.0m`)
  - total completed model-diversity collection: `7796s` (`129.9m`)
- completed collection time excluding the intentionally aborted mixed partial:
  - `16398s` (`4h33m`)

Observed utilization:

- primary augmentation `nvidia-smi dmon` nonzero-window `sm` mean:
  - early: `94.31`
  - mid-active: `95.86`
- mixed remainder `sm` nonzero-window mean:
  - `90.85`
- secondary-model reduced replication `sm` nonzero-window mean:
  - `95.01`

Engineering note:

- a parse-only robustness fix was required during the secondary-model pack:
  - `parse_schema_fields(...)` now defaults descriptive `unresolved_items_count` strings such as `integer or empty` to `0`
  - this did not change the frozen `CASS` method; it only prevented a free-form field from crashing the collector

PRISM fidelity outcome:

- `PRISM_HIGH_FIDELITY` adapter summary:
  - `train_n = 457`
  - `val_n = 119`
  - `tau_c = 0.35`
  - `tau_a = 0.05`
- primary cluster-hard:
  - `PRISM_HIGH_FIDELITY = 0.712871`
  - `CASS_CONSERVATIVE_GATE = 0.746535`
  - pairwise `CASS - PRISM_HIGH_FIDELITY = +0.0335`, `95% CI [0.0132, 0.0548]`
- PRISM-aligned mixed surface:
  - `PRISM_HIGH_FIDELITY = 0.782500`
  - `CASS_CONSERVATIVE_GATE = 0.805000`
  - pairwise `CASS - PRISM_HIGH_FIDELITY = +0.0220`, `95% CI [-0.0012, 0.0450]`
- collapse remained structural:
  - `route_mode = explore` for `100%` of primary, mixed, and reduced-model examples
  - top strategy remained mostly `RAW_PYTHON`

F1 bridge outcome:

- primary cluster-hard:
  - `F1_LITE = 0.603300`
  - `F1_HIGH_FIDELITY = 0.658746`
  - `CASS_CONSERVATIVE_GATE = 0.746535`
- pooled bridge slice:
  - `RAW_PYTHON = 0.740000`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.710000`
  - `CASS_CONSERVATIVE_GATE = 0.720000`
  - `F1_HIGH_FIDELITY = 0.665000`
- reading:
  - stronger-fidelity `F1` helped on the main surface
  - but it did not overturn `CASS`
  - the bridge slice clarified a narrower domain boundary rather than reversing the paper story

Model-diversity outcome:

- reduced `Qwen/Qwen2.5-Math-7B-Instruct` cluster-hard:
  - `RAW_PYTHON = 0.043333`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.060000`
  - `CASS_CONSERVATIVE_GATE = 0.123333`
  - `CASS - OPERATOR = +0.0629`, `95% CI [0.0333, 0.0967]`
- reduced generic-hard:
  - `RAW_PYTHON = 0.066667`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.113333`
  - `CASS_CONSERVATIVE_GATE = 0.160000`
  - `CASS - OPERATOR = +0.0465`, `95% CI [0.0000, 0.0933]`
- absolute levels collapsed on the second model, but the directional sparse-surgery advantage survived

Final reviewer-proofing read:

- the primary cluster-hard lock from `CASS-R3` remains intact
- a stronger-fidelity `PRISM` still trails `CASS` on the primary surface
- a stronger-fidelity `F1` remains below `CASS` on both the primary surface and the bridge slice
- the second-model reduced replication preserves the direction of the `CASS` gain
- therefore the current `CASS` package is now reviewer-robust enough for a top-tier main-track submission, with explicit caveats about:
  - PRISM adaptation vs official reproduction
  - bridge-slice proxy alignment
  - reduced-scale Qwen-family-only model diversity

## 2026-03-09

### Objective

Build an end-to-end, reproducible inference-time research prototype for DART (Devil's-Advocate Reframing at Test-time) using OpenAI API models as the primary execution backend.

### Phase plan

1. Reference scan
   - Inspect the cited papers and public repos quickly for reusable design ideas only.
   - Avoid reproducing any RL or training pipeline.
2. Repo bootstrap
   - Create clean repo skeleton, configs, prompt files, model abstractions, caching, and evaluation code.
3. Smoke test
   - Run a tiny end-to-end path on GSM8K, StrategyQA, and ARC-Challenge with 1-2 examples each.
   - First use `mock` mode to validate parsing/caching; then run a real OpenAI smoke path if secrets are available via env.
4. Pilot
   - Freeze small held-out pilot subsets for prompt reliability checks and cost estimation.
   - Metrics: parse success, malformed/duplicate/trivial rates, latency, approximate cost.
5. Main comparison
   - Run `direct_cot`, `self_consistency_5`, `self_refine_1`, `mc_select_only`, `dart_self`, `dart_adv`, and `dart_human_options` where native choices exist.
6. Ablations
   - `mini/mini` vs `mini/nano`
   - selection-only vs rebuttal+regeneration
   - same-context vs fresh-context finalization
   - self-generated vs adversarial candidate construction
7. Analysis/report
   - Produce csv/markdown tables, plots, failure analysis, and final report.

### Dataset choices

- `gsm8k`
  - Task: numeric reasoning
  - Metric: normalized numeric exact match
  - Split policy: pilot from labeled validation/test subset; main on disjoint labeled subset
- `strategyqa`
  - Task: yes/no reasoning
  - Metric: normalized yes/no exact match
  - Split policy: accessible labeled validation split preferred; otherwise documented alternative labeled split
- `arc_challenge`
  - Task: native multiple choice
  - Metric: exact option match
  - Special use: required for `dart_human_options`

### Default methods

- `direct_cot`
- `self_consistency_5`
- `self_refine_1`
- `mc_select_only`
- `dart_self`
- `dart_adv`
- `dart_human_options` on native MC only

### Default model assignments

- Primary solver / final regeneration: `gpt-5-mini`
- Cheap adversary / distractor / defense: `gpt-5-nano`
- Validator / rebuttal: `gpt-5-mini`

### Prompting defaults

- Observable concise JSON only
- No long chain-of-thought requests
- All intermediate prompts versioned and stored in `prompts/`
- Fresh-context final generation for DART methods

### Reproducibility defaults

- Fixed run seed in config
- Frozen sample ID files
- Request/response caching on disk
- Raw output saved before parsing
- Prompt version recorded in every result record

### Immediate implementation priorities

1. Build reliable schemas and normalization
2. Build disk cache + OpenAI client wrapper
3. Implement dataset loaders and smoke runner
4. Add pilot/main/analysis scripts

### Reference scan notes

- `Language Self-Play for Data-Free Training`
  - Useful design signal: challenger/solver asymmetry is valuable, but the project should stay inference-only.
  - Action taken: adopted targeted adversary roles without any training loop.
- `Auditable-choice reframing / VMR`
  - Useful design signal: open-ended tasks benefit from observable, auditable intermediate choices.
  - Action taken: all intermediate stages emit concise JSON artifacts rather than hidden traces.
- `Critic Discernment Game`
  - Useful design signal: criticism quality matters more than merely adding more samples.
  - Action taken: DART includes defense + rebuttal stages instead of selection-only candidate voting.
- `Distractor generator repo`
  - Useful design signal: distractors should be plausible and targeted, not random.
  - Action taken: adversary personas target concrete failure modes such as arithmetic slips and ignored constraints.
  - Not reused directly: the public repo appears oriented toward distractor generation research, not this inference-only API pipeline.

### Implementation progress

- Repo skeleton created under `/workspace/project`.
- Prompt templates versioned in files under `prompts/`.
- Structured schemas implemented with Pydantic.
- OpenAI Responses API client implemented with disk caching and token/cost logging.
- Deterministic `mock` backend implemented for offline smoke tests.
- Dataset loaders implemented for GSM8K, ARC-Challenge, and a yes/no benchmark path using StrategyQA key with BoolQ fallback.
- Analysis scripts now emit CSV, Markdown, PNG, and PDF outputs.

### Smoke test outcomes

- `mock` smoke completed on GSM8K, yes/no fallback, and ARC-Challenge.
- Real OpenAI smoke completed on:
  - GSM8K: all implemented methods executed successfully on 1 example.
  - ARC-Challenge: all implemented methods, including `dart_human_options`, executed successfully on 1 example.
  - yes/no fallback under `strategyqa` key: all open-ended methods executed successfully on 1 example.

### Pilot outcomes

- Pilot scope executed with real OpenAI API:
  - GSM8K: 8 examples
  - yes/no fallback (`strategyqa` config key, `google/boolq` source): 8 examples
  - ARC-Challenge: 8 examples
- Final pilot records written: 152
- Final pilot directory: `results/pilot/20260309_071406`
- Final pilot cost/time:
  - modeled API-equivalent cost from usage logs: about `$0.1655`
  - sum of per-record stage latencies: about `1553.6s`
  - cached rerun wall-clock for finalized evaluation: about `420.8s`
- Important note:
  - an intermediate pilot run exposed a normalization bug where some models put explanations in `normalized_answer`; after fixing evaluation normalization to derive from the actual answer text, the pilot was rerun from cache and this rerun is the authoritative pilot result.
- Final pilot headline patterns:
  - GSM8K: `self_refine_1` is best on this slice (`1.00`), while `dart_self` and `mc_select_only` tie at `0.75`.
  - yes/no fallback: `dart_adv` and `self_consistency_5` reach `1.00`; `direct_cot` and `mc_select_only` reach `0.875`; `dart_self` reaches `0.75`.
  - ARC-Challenge: after the normalization fix, nearly all methods reach `1.00`; only `self_refine_1` lags slightly at `0.875`.
- Immediate interpretation:
  - The earlier ARC failure pattern was largely an evaluation/normalization artifact, not a core method failure.
  - The clearest pilot win for DART is currently `dart_adv` on the yes/no slice, but it does not dominate `self_consistency_5`.
  - On GSM8K, critique/revision is unexpectedly strong and may be a harder baseline than DART in this prompt family.

### Issues discovered and resolved during smoke

- `gpt-5-mini` rejected the `temperature` parameter.
  - Fix: omit `temperature` on gpt-5 models and keep requested temperature only in metadata/config.
- Some Responses API calls spent output budget on reasoning tokens and returned incomplete responses.
  - Fix: request `reasoning.effort=minimal`, `text.verbosity=low`, and raise output token ceilings modestly.
- Some model outputs had small JSON syntax errors.
  - Fix: added lightweight pre-repair plus `json_repair` fallback before Pydantic validation.
- StrategyQA source availability was inconsistent in this environment.
  - Fix: configured `google/boolq` as the first fallback for the yes/no benchmark path and recorded the chosen HF source in metadata.

### Phase 2 continuation plan

- Purpose:
  - convert the completed pilot into a held-out main run plus decisive ablations with frozen prompts/configs after one final structural pass
  - keep claims narrow and honest: strongest current target is BoolQ / closed-label reasoning, not broad reasoning dominance
- Pre-freeze fixes to make before any held-out run:
  - metric audit and rename/fix any misnamed rate fields
  - honest dataset labeling so final reporting says BoolQ, not StrategyQA
  - normalization regression protection in tests
  - one structural pass for shared candidate artifacts, binary yes/no closed hypothesis handling, and ARC option-fidelity flow
- Planned held-out datasets and default target sizes:
  - BoolQ in this environment, under the existing `strategyqa` config key but honestly labeled as BoolQ in reports: 150 examples, fallback 100
  - GSM8K: 150 examples, fallback 100
  - ARC-Challenge: 150 examples, fallback 100
  - all held-out runs must exclude pilot examples by using non-overlapping offsets beyond the pilot's first 8 examples
- Planned held-out methods:
  - BoolQ:
    - `direct_cot`
    - `self_consistency_5`
    - `self_refine_1`
    - `mc_select_only_binary`
    - `dart_adv_binary_fresh`
    - optional `dart_self_binary` only if cheap
  - GSM8K:
    - `direct_cot`
    - `self_consistency_5`
    - `self_refine_1`
    - `mc_select_only_shared_candidates`
    - `dart_self`
    - `dart_adv_fresh`
  - ARC-Challenge:
    - direct baseline
    - `self_consistency_5` if clean
    - `mc_select_only_human_options`
    - `dart_human_defense_select`
    - `dart_human_rebuttal_fresh`
- Planned decisive ablations:
  - shared candidate ladder on BoolQ and GSM8K:
    - select-only
    - rebuttal-then-select
    - rebuttal-then-same-context-final
    - rebuttal-then-fresh-context-final
  - honest GSM8K comparison: `self_refine_1` vs DART-Adv
  - ARC human-options selection vs regeneration
  - same-model mini/mini vs split-role mini/nano on a subset if budget allows
- Cost/runtime projection starting point from pilot:
  - pilot modeled cost was about `$0.1655` for 24 questions
  - naive linear scaling to 150 / 150 / 150 with the current full method set would exceed the preferred budget and likely approach or exceed the hard cap
  - before main execution, use pilot usage logs plus the narrowed method matrix to estimate final cost precisely and downscale symmetrically to 100 / 100 / 100 if needed
- Stopping rules:
  - stop before main if projected additional spend exceeds `$20`
  - stop before main if non-pilot dev check shows broken parsing, broken option fidelity, broken shared-candidate reuse, or invalid metric semantics
  - otherwise freeze and proceed without further prompt churn

### Metric-audit checklist

- Verify every field ending in `_rate` is mathematically constrained to `[0, 1]`
- Investigate `duplicate_rate > 1.0` in pilot summaries
  - likely cause from initial audit: `duplicates` is stored as a per-example count, so `duplicate_rate` is misnamed
  - required fix: rename to a count-per-example metric or normalize to a true fraction
- Recompute and regenerate pilot summary tables after the metric fix
- Audit dataset labeling:
  - final reporting must say BoolQ or “yes/no benchmark (BoolQ in this environment)”
  - do not imply StrategyQA was used
- Audit normalization regression protection:
  - ensure normalized prediction is derived from the final `answer`
  - add/strengthen regression tests
- Audit candidate-quality semantics:

## 2026-03-11

### V-CHASE branch kickoff

### Objective

Start a new bounded branch, `V-CHASE`, after freezing all DART and CHASE evidence.

Research question:

- Can verifier-like local signals improve CHASE specifically on harder arithmetic by distinguishing:
  - stop now because the current answer is sufficient,
  - continue because one more devil's-advocate round is likely to help,
  - stop because one more round is likely to destabilize a currently good answer?

### Branch framing

- This is not a DART continuation and not a prompt-chasing phase.
- Same-context freeform devil's-advocate remains the central critique substrate.
- Explicit candidate sets remain out of scope unless they are reused only as frozen historical comparison.
- The branch is local-first and controller-first:
  - primary generator: `Qwen/Qwen2.5-7B-Instruct`
  - primary verifier/monitor target: `Qwen/Qwen2.5-Math-PRM-7B`

### Literature guardrails for V-CHASE

- `CoRefine`
  - Justifies adaptive test-time compute as a control problem rather than a single fixed critique budget.
  - Does not justify generic confidence thresholding without utility-aware targets.
- `interwhen`
  - Justifies verifier-like monitors as partial-state control signals.
  - Does not justify using a monitor as a sole oracle for correctness.
- `Uncertainty-Aware Step-wise Verification with Generative Reward Models`
  - Justifies using verifier uncertainty / step-wise verifier outputs as features.
  - Does not justify treating PRM scores as ground truth labels.
- `EDIS`
  - Justifies instability / delta-style signals rather than only static scalar confidence.
  - Suggests trajectory dynamics may carry more information than one-shot confidence.
- `On Verbalized Confidence Scores for LLMs`
  - Supports the prior CHASE finding that raw verbal confidence alone is not enough.
- `Are LLM Decisions Faithful to Verbal Confidence?`
  - Adds a faithfulness caveat: elicited confidence can drift from correctness.
- `Confidence Estimation for LLMs in Multi-turn Interactions`
  - Supports using stage-conditioned confidence and round-to-round deltas.
- `The Lessons of Developing Process Reward Models in Mathematical Reasoning`
  - Requires explicit caution:
    - do not use PRM scores as labels,
    - do not assume PRMs transfer cleanly across prompts / trajectories,
    - log when PRM features conflict with outcome.

### Immediate audit outcome

- Existing CHASE traces are reusable.
- The trace records already contain enough stage-wise information for offline rescoring and replay:
  - stage-0 / stage-1 / stage-2 answers
  - correctness labels
  - old CHASE confidence features
  - answer-change indicators
  - raw generation paths for stage text rescoring
- Therefore V-CHASE can and should begin with:
  - offline verifier-like feature extraction,
  - offline signal benchmark extension,
  - offline oracle headroom analysis,
  before any new large generation run.

### Preferred execution order

1. Create `reports/vchase_plan.md` and freeze branch scope.
2. Add verifier-like signal layer:
   - PRM-based features if `Qwen/Qwen2.5-Math-PRM-7B` is stable,
   - arithmetic-consistency checks,
   - optional entropy / instability summaries where cheap.
3. Re-score reusable CHASE traces and run an offline headroom study.
4. Proceed to new main generation only if:
   - verifier features materially improve hard-arithmetic signal quality over old CHASE features,
   - oracle headroom over CHASE is non-trivial.

### Planned datasets and split policy

- Offline signal/headroom stage:
  - reuse CHASE calibration/evaluation traces for `gsm8k_train` and `asdiv`
  - use `svamp` only later if main prospective evaluation is justified
- Prospective main evaluation only if justified:
  - hard set: fresh unseen `gsm8k` / `gsm8k_train` slice, target `>= 150`
  - easy / over-deliberation set: fresh unseen `asdiv`, target `>= 150` if available
  - transfer set: fresh unseen `svamp`, target `100-150` if stable

### Planned methods

- Replayed / benchmarked from existing CHASE traces:
  - `direct_cot`
  - `self_refine_1`
  - `freeform_fixed1_same`
  - `freeform_fixed2_same`
  - `robust_rule_gate`
  - `CHASE_calibrated`
- New verifier-augmented controllers:
  - `verifier_rule_gate`
  - `VCHASE_singlehead`
  - `VCHASE_dualhead`
  - optional `VCHASE_selective`

### Runtime expectations

- Offline rescoring and headroom analysis should be cheap relative to full trace recollection.
- Main infrastructure risk is the local PRM bring-up, not OpenAI cost.
- Four GPUs should be used pragmatically only if the offline analysis justifies a fresh main run.

### Stop rules for the new branch

- Stop if reusable CHASE traces are insufficient and rebuilding them becomes the main work.
- Stop if verifier-like features do not materially improve over old CHASE features on hard-arithmetic signal benchmarks.
- Stop if oracle headroom over CHASE is too small to justify controller work.
- Stop if the branch starts drifting into prompt-chasing or candidate-set redesign.

### V-CHASE execution outcome

- Existing CHASE traces were sufficient for offline rescoring and replay.
- Old held-out verifier benchmark without PRM:
  - current-correctness discrimination:
    - `old_current_score AUROC = 0.8474`
    - `vchase_current_score AUROC = 0.8819`
  - helpful-next prediction:
    - `old_helpful_score AUROC = 0.7899`
    - `vchase_helpful_score AUROC = 0.7919`
  - harmful-next prediction:
    - `old_harmful_score AUROC = 0.6475`
    - `vchase_harmful_score AUROC = 0.7158`
- Offline headroom on reusable CHASE traces justified continued work:
  - `gsm8k_train`: `CHASE_calibrated = 0.3250`, `oracle_stop_current = 0.5938`
  - `asdiv`: `CHASE_calibrated = 0.8333`, `oracle_stop_current = 0.8933`

### Fresh prospective V-CHASE run

- Fresh trace collection completed on `Qwen/Qwen2.5-7B-Instruct`:
  - calibration:
    - `gsm8k_train`: `60` at offset `300`
    - `asdiv`: `40` at offset `270`
    - `svamp`: `40` at offset `0`
  - held-out evaluation:
    - `gsm8k_train`: `150` at offsets `400` and `475`
    - `asdiv`: `150` at offsets `320` and `395`
    - `svamp`: `120` at offsets `50` and `110`
- Fresh no-PRM signal benchmark:
  - current-correctness:
    - `old_current_score AUROC = 0.8876`
    - `vchase_current_score AUROC = 0.9203`
  - helpful-next:
    - `old_helpful_score AUROC = 0.8098`
    - `vchase_helpful_score AUROC = 0.8448`
- Fresh no-PRM main replay:
  - `asdiv`:
    - `CHASE_calibrated = 0.9133`
    - `VCHASE_dualhead = 0.9267`
    - `verifier_rule_gate = 0.9267`
  - `gsm8k_train`:
    - `CHASE_calibrated = 0.3600`
    - `VCHASE_dualhead = 0.3867`
    - `VCHASE_singlehead = 0.4000`
    - `verifier_rule_gate = 0.4267`
  - `svamp`:
    - `CHASE_calibrated = 0.6917`
    - `VCHASE_dualhead = 0.6750`
    - `VCHASE_singlehead = 0.7083`
    - `verifier_rule_gate = 0.7000`
- Immediate interpretation after the no-PRM fresh run:
  - verifier-like arithmetic / consistency features already help
  - but the dual-head controller is not yet the clean best method on hard arithmetic without PRM
  - transfer is mixed, so a bounded PRM add-on on the hard set is justified

### PRM bring-up and hard-set retest

- `Qwen/Qwen2.5-Math-PRM-7B` initially failed due two compatibility issues:
  - missing `pad_token_id`
  - cache API mismatch with the current `transformers` build
- Both were resolved with bounded wrapper changes:
  - set `pad_token_id` from the config fallback path
  - force `use_cache=False`
- PRM standalone caveat:
  - standalone `prm_score_current` remained weak on fresh `gsm8k_train` (`AUROC = 0.4182`)
  - this matches the design guardrail that PRM should be treated as a feature, not as ground truth
- Fresh `gsm8k_train` PRM verifier benchmark:
  - `old_current_score AUROC = 0.7343`
  - `vchase_current_score AUROC = 0.8350`
  - `old_helpful_score AUROC = 0.5810`
  - `vchase_helpful_score AUROC = 0.6813`
- Fresh `gsm8k_train` PRM main replay:
  - `CHASE_calibrated = 0.3600`
  - `robust_rule_gate = 0.3800`
  - `freeform_fixed1_same = 0.3333`
  - `VCHASE_dualhead = 0.4733`
  - `VCHASE_singlehead = 0.4267`
  - `verifier_rule_gate = 0.4267`
  - paired comparisons for `VCHASE_dualhead`:
    - vs `CHASE_calibrated`: delta `+0.1140`, McNemar `p = 0.0009`
    - vs `robust_rule_gate`: delta `+0.0938`, McNemar `p = 0.0094`
    - vs `freeform_fixed1_same`: delta `+0.1393`, McNemar `p = 0.0031`

### Final V-CHASE interpretation

- The branch is stronger than the first CHASE branch.
- Supported:
  - verifier-like local signals improve controller quality beyond old CHASE features
  - arithmetic-consistency features are already useful without PRM
  - on hard arithmetic, PRM-like features help when used as controller features rather than as standalone verdicts
  - fresh `gsm8k_train` now shows a clear hard-set gain for `VCHASE_dualhead`
  - easy-set compute savings remain intact on `asdiv`
- Still limited:
  - `svamp` transfer is mixed
  - PRM as a standalone scalar is weak
  - dual-head control is not yet universally best across all arithmetic datasets
- Branch posture:
  - promising follow-up, but still a bounded verifier-aware control result rather than a universal reasoning method claim
  - distinguish raw candidate count, kept candidate count, duplicate count-per-example, duplicate fraction, trivial fraction, malformed fraction
  - ensure names match what is actually computed

### Pilot case inspection notes before final structural pass

- Available authoritative pilot categories after the normalization fix were smaller than the ideal 4-per-bucket target for some buckets, so all available cases were inspected and the shortfall is noted explicitly.
- `direct wrong -> dart_adv repaired`
  - Available cases: 2
  - `gsm8k_4`: direct answer collapsed to `10`; `dart_adv` recovered `20` once an explicit alternative hypothesis was surfaced.
  - `strategyqa_2`: direct answer drifted into a concept label instead of a yes/no output; `dart_adv` forced a clean binary answer and succeeded.
- `direct correct -> DART corrupted`
  - Available cases: 2, both under `dart_self` on BoolQ
  - `strategyqa_0`: self-generated candidate set mixed `yes`, `no`, and “it depends” style hypotheses; final answer drifted to ambiguity even though direct was already correct.
  - `strategyqa_1`: self-generated alternatives overemphasized taxonomy distinctions (“house tax” vs “property tax”) and overturned a correct direct answer.
- `self_refine_1` wins over DART on GSM8K
  - Available cases: 3
  - `gsm8k_2`: DART candidates clustered around duplicated wrong numeric hypotheses (`195000`, `120000`) while self-refine corrected to `70000`.
  - `gsm8k_5`: DART adversary set retained several weak numeric distractors and final answer stayed at the wrong draft value.
  - `gsm8k_7`: `dart_self` repaired but `dart_adv` failed due poor alternative quality; self-refine still solved it cleanly.
- ARC option-fidelity inspection
  - Inspected 4 representative cases: `MDSA_2007_4_52`, `Mercury_7027230`, `Mercury_7205135`, `Mercury_SC_405487`
  - After the normalization fix, DART outputs were usually valid option letters and no longer showed the earlier evaluation collapse.
  - The deeper issue for ARC is now not option fidelity collapse but lack of separation: current slice is too easy and regeneration seldom changes the outcome.
- Structural implications from the inspection
  - BoolQ needs a strict closed hypothesis set `{YES, NO}` instead of four self-generated verbal variants.
  - Shared candidate artifacts are necessary so selection vs rebuttal vs regeneration comparisons use identical inputs.
  - GSM8K adversaries need stronger diversity and duplicate suppression by normalized answer and failure mode.
  - ARC should preserve letters/text exactly and use dedicated selection-vs-regeneration ablations rather than relying on the generic open-ended path.

### Final structural pass and freeze-precheck dev run

- Structural pass implemented before freeze:
  - shared candidate artifacts are now materialized once per example and reused across:
    - `adv_select_only_shared`
    - `adv_rebuttal_then_select_shared`
    - `adv_rebuttal_then_same_context_final`
    - `adv_rebuttal_then_fresh_context_final`
  - BoolQ / yes-no examples now use a closed hypothesis set `{YES, NO}` instead of model-generated verbal variants.
  - ARC now has dedicated human-option methods:
    - `mc_select_only_human_options`
    - `dart_human_defense_select`
    - `dart_human_rebuttal_same`
    - `dart_human_rebuttal_fresh`
  - GSM8K/open-ended candidate generation now deduplicates by normalized answer and repeated failure mode before validator filtering.
  - cache keys were changed to ignore `metadata` so identical prompt texts reuse cached responses across methods; this matters for shared-ablation fairness and avoids paying multiple times for the same request text.
  - runtime monitoring was updated to use `manifest.json` method counts instead of assuming the pilot method matrix.
- Non-pilot freeze-precheck dev run:
  - run dir: `results/devcheck/phase2_openai_dev_freeze`
  - scope: 5 held-out items per dataset, offset `8`, total `15` questions / `125` records
  - monitored runtime estimate after the cache-key fix: about `238s` / `$0.025`
  - realized record count: `125`
  - realized average record cost during the run stabilized around `$0.00118`
- Freeze-precheck headline results:
  - BoolQ:
    - all tested methods tied at `0.80` on this tiny slice
    - binary special handling is stable and duplicate pressure is gone (`duplicate_fraction = 0`)
    - this slice is too small / easy to decide whether rebuttal or fresh-context helps beyond selection
  - GSM8K:
    - `direct_cot = 0.00`
    - `self_refine_1 = 0.40`
    - `mc_select_only_shared_candidates = 0.20`
    - `adv_select_only_shared = 0.20`
    - `adv_rebuttal_then_select_shared = 0.20`
    - `adv_rebuttal_then_same_context_final = 0.80`
    - `adv_rebuttal_then_fresh_context_final = 0.80`
    - `dart_adv_fresh = 0.80`
    - `dart_self = 0.80`
    - coverage-conditioned note: adversarial shared candidates only covered the gold answer on `20%` of this slice, yet fresh/same-context finalization still reached `0.80`; this is exactly the kind of regeneration-beyond-selection signal the paper needs to test at scale.
  - ARC-Challenge:
    - `direct_cot = 1.00`
    - `mc_select_only_human_options = 1.00`
    - `dart_human_defense_select = 0.80`
    - `dart_human_rebuttal_same = 1.00`
    - `dart_human_rebuttal_fresh = 0.80`
    - interpretation: same-context final option selection looks safer than fresh-context finalization on this small slice, so the ARC ablation should explicitly compare same vs fresh rather than assuming fresh is better.
- Freeze decision:
  - prompts/configs are now frozen for held-out main and ablations.
  - no further prompt edits should be made before the main run unless a hard execution bug appears.
- Main-run scope lock after cost check:
  - projected main comparison cost using freeze-precheck realized averages is comfortably below the `$10` preferred budget even at:
    - BoolQ `150`
    - GSM8K `150`
    - ARC-Challenge `150`
  - projected decisive ablations on top are also still below budget.
  - therefore the held-out main comparison is locked to `150 / 150 / 150` with offset `8`.
  - recommended ablation subset sizes:
    - BoolQ `80`
    - GSM8K `80`
    - ARC-Challenge `80`

### Held-out main run completed

- Main run dir: `results/main/20260309_085512`
- Main scope:
  - BoolQ (`strategyqa` config key in this environment): `150` questions
  - GSM8K: `150` questions
  - ARC-Challenge: `150` questions
  - total main records: `2400`
- Main modeled cost from usage logs: about `$2.1827`
- Sum of recorded stage latencies: about `20170.3s`
- Main headline results:
  - BoolQ:
    - `mc_select_only_binary = 0.9133`
    - `direct_cot = 0.8800`
    - `dart_adv_binary_fresh = 0.8667`
    - interpretation: strict closed-label selection is stronger than fresh-context DART here.
  - GSM8K:
    - `dart_adv_fresh = 0.8733`
    - `dart_self = 0.8600`
    - `self_refine_1 = 0.8267`
    - `mc_select_only_shared_candidates = 0.4867`
    - `direct_cot = 0.4467`
    - interpretation: this is the strongest positive regime for DART in the held-out run.
  - ARC-Challenge:
    - `mc_select_only_human_options = 0.9600`
    - `dart_human_rebuttal_fresh = 0.9467`
    - `direct_cot = 0.9400`
    - interpretation: fresh-context regeneration is not a win when candidate coverage is guaranteed.

### Held-out ablations completed

- Ablation run dir: `results/ablations/20260309_095442`
- Ablation scope:
  - BoolQ `80`
  - GSM8K `80`
  - ARC-Challenge `80`
  - total ablation records: `1520`
- Ablation modeled cost from usage logs: about `$1.7078`
- Sum of recorded stage latencies: about `14595.5s`
- Decisive ablation takeaways:
  - BoolQ:
    - `adv_select_only_shared = 0.9125`
    - `adv_rebuttal_then_select_shared = 0.8875`
    - `adv_rebuttal_then_same_context_final = 0.8625`
    - `adv_rebuttal_then_fresh_context_final = 0.8250`
    - interpretation: each extra stage hurts rather than helps.
  - GSM8K:
    - `adv_select_only_shared = 0.4750`
    - `adv_rebuttal_then_select_shared = 0.5125`
    - `adv_rebuttal_then_same_context_final = 0.9000`
    - `adv_rebuttal_then_fresh_context_final = 0.8875`
    - interpretation: rebuttal alone helps a little; regeneration is the main useful ingredient.
  - ARC-Challenge:
    - `mc_select_only_human_options = 0.9625`
    - `dart_human_defense_select = 0.9500`
    - `dart_human_rebuttal_same = 0.9750`
    - `dart_human_rebuttal_fresh = 0.9500`
    - interpretation: if regeneration is used at all on ARC, same-context option finalization is better than fresh-context finalization on this slice.

### Final empirical read

- The pilot-era “BoolQ / closed-label is the best DART regime” hypothesis did not survive the held-out run.
- The strongest supported claim shifted toward open-ended arithmetic:
  - DART clearly beats direct generation and selection-only on GSM8K.
  - DART is competitive with or slightly above `self_refine_1` on the held-out GSM8K slice, though the main pairwise delta over `self_refine_1` is modest and its CI still overlaps zero.
- Closed-label results are mostly negative or mixed:
  - BoolQ favors strict selection.
  - ARC favors strict selection or, at most, same-context option finalization rather than fresh-context regeneration.
- Net-net:
  - the project now looks more like a nuanced “where regeneration helps and where it hurts” paper than a broad DART-dominates claim.

### Phase 3 continuation plan

- Objective:
  - treat existing held-out results as frozen evidence and build a paper-ready open-ended confirmation package
  - do not try to rescue BoolQ or ARC
  - first confirm or falsify the open-ended story on new arithmetic data before considering any method change
- Audit status before new runs:
  - held-out main and ablation summaries regenerate cleanly from cached `per_example.jsonl` files via the current analysis stack
  - current figures / tables already reproduce coverage-conditioned summaries and candidate-quality metrics without rerunning old API calls
  - no concrete bug was found that invalidates the reported phase 2 results
- New dataset plan:
  - GSM8K confirmatory: `500` new test examples, offset `158`
    - rationale: pilot used `0:8`, held-out main used `8:158`, so offset `158` is the first clearly unused region
  - SVAMP: full accessible labeled test set, `300` examples, offset `0`
    - accessible cleanly from `ChilleD/SVAMP`
    - numeric exact evaluation is straightforward through the existing normalization path
  - Optional only if budget remains after the main confirmation package:
    - MultiArith full test set, `180` examples, offset `0`
    - this is a low-friction third numeric benchmark, but it is not required for phase-3 success
- Frozen-v1 method matrix for new open-ended confirmation:
  - `direct_cot`
  - `self_refine_1`
  - `adv_select_only_shared`
  - `adv_rebuttal_then_select_shared`
  - `dart_adv_same` (implemented as the same-context shared-candidate regeneration variant)
  - `dart_adv_fresh`
- Mechanism-control methods to add and run prospectively on new data:
  - `freeform_devil_advocate_fresh`
    - adversarial critique + rebuttal + fresh regeneration without an explicit auditable candidate set
  - `self_refine_2_budgetmatched`
    - two critique/revision rounds, calibrated only to be in the same rough cost band as `dart_adv_fresh`
- Planned execution order:
  - patch the repo minimally to support the new datasets and the two mechanism controls
  - run a tiny sanity check on new data only:
    - GSM8K `5` at offset `158`
    - SVAMP `5` at offset `0`
  - if parsing, evaluation, and cost are stable, freeze v1 and launch the confirmatory package
  - main confirmatory run:
    - GSM8K `500`
    - SVAMP `300`
    - methods: the 6 frozen-v1 methods plus the 2 mechanism controls
  - optional only if cost/runtime remain comfortable:
    - MultiArith `180` with the 6 frozen-v1 methods
- Cost estimate before new API spend:
  - extrapolating from observed GSM8K phase-2 per-example costs:
    - GSM8K `500` with 8 methods: about `$5.45`
    - SVAMP `300` with 8 methods: about `$3.27`
    - combined primary package: about `$8.72`
    - optional MultiArith `180` with the 6 frozen-v1 methods: about `$1.46`
  - target additional spend remains below `$12`; even with the optional third benchmark the package stays around `$10.18` before small sanity checks
- Runtime estimate:
  - observed GSM8K ablation latency suggests roughly `16-17s` stage-sum per candidate-based record and `~2s` for `direct_cot`
  - with concurrency and caching, the expected wall-clock for the primary package is on the order of `3-5` hours rather than the raw stage-sum
  - a monitoring script should be kept running during the long API phase
- Success criteria:
  - replicate the selection -> rebuttal -> regeneration ladder on new GSM8K examples
  - show the same or a similar ladder on at least one additional open-ended arithmetic benchmark
  - keep the coverage-conditioned story central:
    - when `candidate_coverage = 0`, selection-only should remain near floor while DART remains materially above floor
  - determine whether `dart_adv_fresh` is actually better than:
    - `self_refine_1`
    - `self_refine_2_budgetmatched`
    - `freeform_devil_advocate_fresh`
- Stopping rules:
  - if frozen v1 does not replicate on SVAMP, do not expand further; treat the positive regime as potentially GSM8K-specific
  - if `dart_adv_fresh` does not separate from the freeform control or the budget-matched self-refine control, do not claim auditable hypothesis sets are the key ingredient
  - do not introduce any prompt redesign before the frozen-v1 confirmation is complete

### Phase 3 tiny new-data dev sanity

- Dev freeze run dir: `results/devcheck/phase3_openended_dev_freeze`
- Scope:
  - GSM8K `5` new examples at offset `158`
  - SVAMP `5` examples at offset `0`
  - methods:
    - `direct_cot`
    - `self_refine_1`
    - `self_refine_2_budgetmatched`
    - `adv_select_only_shared`
    - `adv_rebuttal_then_select_shared`
    - `dart_adv_same`
    - `dart_adv_fresh`
    - `freeform_devil_advocate_fresh`
- Realized dev cost:
  - GSM8K child run: about `$0.0512`
  - SVAMP child run: about `$0.0466`
  - merged total: about `$0.0978`
- Sanity outcomes:
  - parsing and JSON repair remained stable; no structural crash appeared in the new mechanism-control paths
  - `self_refine_2_budgetmatched` landed close enough to DART cost for the planned control:
    - GSM8K cost ratio vs `dart_adv_fresh`: `0.872`
    - SVAMP cost ratio vs `dart_adv_fresh`: `0.929`
  - GSM8K tiny slice:
    - `adv_select_only_shared = 0.00`
    - `adv_rebuttal_then_select_shared = 0.00`
    - `dart_adv_same = 0.60`
    - `dart_adv_fresh = 1.00`
    - `freeform_devil_advocate_fresh = 1.00`
    - `self_refine_1 = 0.80`
    - `self_refine_2_budgetmatched = 1.00`
    - note: tiny-slice variance is high, but the selection-vs-regeneration separation is in the expected direction
  - SVAMP tiny slice:
    - all shared-candidate methods were correct on this easy slice
    - `freeform_devil_advocate_fresh = 0.80`
    - `self_refine_1 = 0.60`
    - coverage was `1.0` throughout this tiny sample, so SVAMP needs the larger run to test the incomplete-coverage mechanism seriously
- Freeze decision:
  - prompts/configs remain frozen for phase 3 main confirmation
  - no prompt redesign is justified before the larger new-data run

### Phase 3 main confirmation completed

- Confirmatory run dir: `results/confirm/20260309_120134`
- Final scope:
  - GSM8K unseen continuation: `500` examples at offset `158`
  - SVAMP full labeled test set: `300` examples at offset `0`
  - methods:
    - `direct_cot`
    - `self_refine_1`
    - `self_refine_2_budgetmatched`
    - `adv_select_only_shared`
    - `adv_rebuttal_then_select_shared`
    - `dart_adv_same`
    - `dart_adv_fresh`
    - `freeform_devil_advocate_fresh`
- Operational note:
  - the initial sequential confirmatory run was stable but too slow
  - after `92` completed GSM8K examples and `109` completed SVAMP examples were safely materialized, the remaining ranges were resumed as non-overlapping shards
  - this changed wall-clock only; it did not change prompts, methods, or evaluation IDs
- Realized run size:
  - `500` GSM8K questions / `4000` records
  - `300` SVAMP questions / `2400` records
  - total: `800` questions / `6400` records
- Realized resource usage:
  - modeled cost from usage logs: about `$7.9148`
  - summed stage latencies: about `79199.3s`
  - approximate wall-clock from earliest child manifest to final child completion: about `132.4` minutes
  - total spend stayed below the phase-3 target budget
- Headline results:
  - GSM8K:
    - `direct_cot = 0.400`
    - `adv_select_only_shared = 0.424`
    - `adv_rebuttal_then_select_shared = 0.458`
    - `dart_adv_fresh = 0.842`
    - `dart_adv_same = 0.884`
    - `self_refine_1 = 0.844`
    - `self_refine_2_budgetmatched = 0.848`
    - `freeform_devil_advocate_fresh = 0.914`
  - SVAMP:
    - `direct_cot = 0.823`
    - `adv_select_only_shared = 0.820`
    - `adv_rebuttal_then_select_shared = 0.823`
    - `dart_adv_fresh = 0.903`
    - `dart_adv_same = 0.917`
    - `self_refine_1 = 0.903`
    - `self_refine_2_budgetmatched = 0.907`
    - `freeform_devil_advocate_fresh = 0.927`
- Mechanistic takeaways:
  - the selection -> rebuttal -> regeneration ladder replicated clearly:
    - GSM8K: `0.424 -> 0.458 -> 0.884`
    - SVAMP: `0.820 -> 0.823 -> 0.917`
  - coverage-conditioned evidence remained strong:
    - GSM8K coverage `0`: `adv_select_only_shared = 0.000`, `dart_adv_same = 0.767`, `dart_adv_fresh = 0.683`
    - SVAMP coverage `0`: `adv_select_only_shared = 0.000`, `dart_adv_same = 0.581`, `dart_adv_fresh = 0.535`
  - same-context finalization outperformed fresh-context finalization on GSM8K and slightly on SVAMP:
    - GSM8K delta (`fresh -> same`) = `+0.0417`, bootstrap CI `[+0.0160, +0.0680]`, McNemar `p=0.0046`
    - SVAMP delta (`fresh -> same`) = `+0.0130`, CI touches `0`
- Negative or narrowing findings:
  - explicit auditable candidate sets are not supported as the main differentiator in phase 3
  - `freeform_devil_advocate_fresh` beat `dart_adv_fresh` on GSM8K by `+0.0721` absolute and remained slightly above the best DART variant on SVAMP
  - `dart_adv_fresh` and `self_refine_1` were effectively tied on both datasets
  - `self_refine_2_budgetmatched` was also tied with `dart_adv_fresh`
- Candidate-collapse bottleneck persisted:
  - GSM8K:
    - `avg_raw_candidates = 4.978`
    - `avg_kept_candidates = 1.07`
    - `avg_duplicate_count = 2.042`
    - `duplicate_fraction = 0.4099`
    - `malformed_fraction = 0.095`
  - SVAMP:
    - `avg_raw_candidates = 4.993`
    - `avg_kept_candidates = 1.02`
    - `avg_duplicate_count = 2.40`
    - `duplicate_fraction = 0.4808`
    - `malformed_fraction = 0.0813`
- Final phase-3 read:
  - the open-ended positive regime is real and now replicated on two arithmetic datasets
  - the supported mechanism is rebuttal + regeneration beyond selection-only, not the superiority of explicit auditable candidate sets over generic adversarial critique
  - fresh-context finalization should not be centered as the main claimed mechanism; same-context is the stronger current DART variant

### Phase 4 continuation plan

- Objective:
  - run exactly one prospective v2 candidate-diversity repair
  - test whether fixing candidate collapse can recover a stronger auditable-hypothesis-set story on new open-ended data
  - stop immediately if v2 does not materially improve candidate diversity or if it still fails against fair freeform same-context controls
- Audit status before v2:
  - phase-3 summaries still regenerate cleanly from cached `per_example.jsonl`
  - current analysis stack already reports coverage-conditioned accuracy and candidate-collapse metrics
  - missing for phase 4 and to be added before the main retest:
    - distinct error-type count
    - explicit v1 -> v2 collapse deltas
    - fair same-context freeform comparison tables
- Batch API decision:
  - official OpenAI Batch docs currently advertise a 50% discount with a `24h` completion window for `/v1/responses`
  - however, this pipeline is multi-stage and stateful:
    - persona-sharded proposal
    - dedupe / validation
    - optional repair pass
    - rebuttal
    - same-context finalization
  - making all of that batch-native would require a new stage orchestrator and delayed artifact reassembly, which is too much new infrastructure for this phase
  - since the projected synchronous spend is still within the phase-4 target budget, phase 4 will remain on the existing cached synchronous path
- Exact phase-4 v2 design target:
  - working method name: `dart_adv_same_v2`
  - one global change only:
    - contrastive persona-sharded candidate generation
    - hard novelty constraints over forbidden answers and error types
    - one repair pass if unique kept candidates remain below target
  - same-context finalization remains the default DART endpoint
- New-data plan:
  - tiny v2 dev sanity:
    - GSM8K `10` new examples at offset `658`
    - MultiArith `10` examples at offset `0`
  - prospective main retest:
    - GSM8K `500` new examples at offset `658`
      - rationale: previous phases consumed through index `657`; this starts at the first unused region
    - MultiArith full test set: `180` examples at offset `0`
      - rationale: new objective arithmetic benchmark, low friction, cheap enough for a fair control-heavy retest
- Main methods for phase 4:
  - `self_refine_1`
  - `self_refine_2_budgetmatched`
  - `freeform_devil_advocate_same`
  - `freeform_devil_advocate_fresh`
  - `dart_adv_same_v1`
  - `dart_adv_same_v2`
  - `adv_select_only_shared_v2`
  - `direct_cot` for reference if cost remains in line during the dev sanity
  - optional only if still comfortably under budget:
    - `adv_rebuttal_then_select_shared_v2`
- Rough cost estimate:
  - using phase-3 observed method costs plus a conservative uplift for v2:
    - GSM8K `500` with the primary phase-4 method set: about `$6.4-$7.2`
    - MultiArith `180` with the same set: about `$2.2-$2.6`
    - tiny dev sanity: about `$0.20-$0.30`
  - total planned spend stays roughly in the `$8.8-$10.1` range before optional extras
  - therefore the plan is acceptable under the phase-4 target budget, but optional ablations should remain off unless v2 is clearly promising
- Runtime estimate:
  - synchronous wall-clock should be kept manageable with non-overlapping sharded runs if needed, as in phase 3
  - expected wall-clock is on the order of `2-3` hours, depending on v2 artifact cost
- Success criteria:
  - v2 materially increases diversity on new dev data:
    - higher `avg_kept_candidates`
    - lower `duplicate_fraction`
    - no large malformed-output blow-up
  - on the prospective main retest:
    - `dart_adv_same_v2 > dart_adv_same_v1`
    - v2 coverage and kept-candidate count improve
    - the gap to `freeform_devil_advocate_same` narrows materially, ideally closing on at least one dataset
- Stopping rules:
  - if v2 does not improve diversity on the tiny dev sanity, stop phase 4
  - if v2 improves diversity but not accuracy, stop phase 4
  - if v2 improves over v1 but still clearly trails fair freeform same-context with no convincing mechanistic upside, stop phase 4
  - if spend approaches the hard cap before obtaining:
    - one GSM8K retest
    - one new-benchmark retest
    - one fair freeform same-context comparison
    then stop and finalize the current nuanced paper package

### Phase 4 dev sanity and freeze

- Ran the initial tiny new-data v2 dev sanity on:
  - `gsm8k` offset `658`, limit `10`
  - `multiarith` offset `0`, limit `10`
- Initial result:
  - v2 improved raw candidate count and sometimes coverage, but `avg_kept_candidates` stayed flat at about `1`
  - artifact inspection showed the main bottleneck was not proposer collapse alone
  - the validator was aggressively rejecting plausible wrong alternatives as simply “incorrect,” which prevented the auditable hypothesis set from staying diverse
- One allowed revision was used:
  - keep v1 frozen
  - for v2 only, reinterpret validator outputs permissively:
    - still drop duplicates, malformed outputs, and trivial/silly options
    - keep plausible non-duplicate wrong alternatives instead of collapsing back to a single “correct” option
  - this is still a candidate-diversity repair rather than a rebuttal/finalization redesign
- Re-ran the same tiny dev slice using cached API outputs and the v2-only permissive validator interpretation.
- Final dev result used for freeze:
  - `gsm8k`
    - `dart_adv_same_v1`: accuracy `0.90`, avg kept `1.1`, coverage `0.8`
    - `dart_adv_same_v2`: accuracy `1.00`, avg kept `3.6`, coverage `0.8`
  - `multiarith`
    - `dart_adv_same_v1`: accuracy `1.00`, avg kept `1.0`, coverage `1.0`
    - `dart_adv_same_v2`: accuracy `1.00`, avg kept `3.1`, coverage `1.0`
- Freeze decision:
  - v2 now materially improves kept-candidate diversity on both dev datasets
  - no malformed-output explosion was observed
  - therefore freeze the v2 design here and proceed to the prospective main retest only on non-overlapping IDs
- Main run will therefore use:
  - `gsm8k` offset `668`, limit `500`
  - `multiarith` offset `10`, limit `170`
  - methods:
    - `direct_cot`
    - `self_refine_1`
    - `self_refine_2_budgetmatched`
    - `freeform_devil_advocate_same`
    - `freeform_devil_advocate_fresh`
    - `dart_adv_same_v1`
    - `dart_adv_same_v2`
    - `adv_select_only_shared_v2`

### Phase 4 main result and stop decision

- Main prospective run completed on:
  - `gsm8k` offset `668`, limit `500`
  - `multiarith` offset `10`, limit `170`
- Because sequential execution was too slow, the final main run was restarted as non-overlapping shards:
  - GSM8K: 4 shards x 125 examples
  - MultiArith: 2 shards x 85 examples
  - partial sequential outputs were preserved on disk but excluded from the merged final run
- Final merged phase-4 main run:
  - `670` questions
  - `5360` method records
  - modeled cost about `$8.8210`
- Headline outcome:
  - v2 clearly improved candidate diversity:
    - GSM8K kept candidates `1.114 -> 3.54`
    - MultiArith kept candidates `1.012 -> 2.653`
  - but it did not strengthen the main methods claim enough:
    - GSM8K `dart_adv_same_v1 = 0.870`, `dart_adv_same_v2 = 0.866`
    - MultiArith `dart_adv_same_v1 = 0.976`, `dart_adv_same_v2 = 0.988`
    - `freeform_devil_advocate_same` remained tied on GSM8K and competitive overall
- Final phase-4 decision:
  - candidate-collapse repair is real
  - the stronger auditable-candidate-set story is still not restored
  - stop experimentation in this branch and package phase 4 as a final stop result inside the nuanced paper

### Phase 5 continuation plan

- Objective:
  - test whether the currently supported mechanism survives outside the API model family
  - check whether explicit auditable candidate structure helps weaker local models more than stronger local models
  - stop immediately if the story does not strengthen materially
- Preferred local model pair:
  - `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B`
  - `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B`
- Fallback pair if 32B is unstable on this node:
  - `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`
  - `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B`
- Serving stack plan:
  - keep OpenAI backend untouched
  - add `vllm` backend first
  - add `hf_local` fallback backend using `transformers` + `accelerate` + `bitsandbytes`
  - preserve the same disk-caching and raw-output logging semantics as the API path
- Datasets for phase 5:
  - prospective subset:
    - remaining unseen GSM8K examples not used in phases 1-4
    - expected remaining pool after earlier frozen runs is about `161`
  - frozen replication set:
    - phase-3 GSM8K 500-example confirmatory slice
  - optional only if runtime is stable and the story is still ambiguous:
    - phase-3 SVAMP 300-example slice
- Default methods for local phase:
  - `direct_cot`
  - `self_refine_1`
  - `freeform_devil_advocate_same`
  - `adv_select_only_shared`
  - `dart_adv_same_v1`
  - optional only if runtime allows:
    - `self_refine_2_budgetmatched`
    - `dart_adv_same_v2` only if local dev candidate-quality checks justify it
- Tiny local dev sanity policy:
  - `10-20` examples per dataset/model combination maximum
  - use only for parser stability and candidate-quality metrics
  - do not use dev accuracy to decide prompts
- Runtime / feasibility estimate before bring-up:
  - `14B` on a single `3090` should be feasible in BF16 or 4-bit fallback
  - `32B` likely needs multi-GPU serving and may require quantization or reduced context length
  - if `vllm` is stable, the target is to run:
    - one smaller model
    - one larger model
    - one prospective subset + one replication set
    within a single working day on this node
  - if infrastructure work starts dominating, phase 5 should stop early
- Success criteria:
  - local models replicate the selection-only vs DART mechanism, especially on GSM8K coverage=`0`
  - there is at least suggestive evidence that weaker local models benefit more from explicit auditable options than stronger ones
  - otherwise, phase 5 should be written up as a decisive external-validity null / mixed result
- Stop rules:
  - if local mechanistic replication fails, stop
  - if DART and freeform same-context remain tied or freeform wins at all local scales, stop
  - if local infrastructure becomes the main bottleneck, stop
  - after one prospective subset + one replication set + one fair freeform same-context comparison, if the story is unchanged, stop

### Phase 5 execution outcome

- Local backend work completed:
  - added `hf_local` as the practical local path
  - added import-guarded `vllm` backend without making it a hard dependency
  - kept the OpenAI path unchanged
- Preferred `DeepSeek-R1-Distill-Qwen-{14B,32B}` plan was not used for the final retest:
  - `32B` was not practical under current disk/runtime constraints
  - `DeepSeek` local structured-output stability was weak enough that infrastructure started dominating the science
- Final local comparison used the same-family fallback:
  - `Qwen/Qwen2.5-0.5B-Instruct`
  - `Qwen/Qwen2.5-1.5B-Instruct`
- Local parser hardening was required before the phase could run:
  - stricter schema hints in the local backend
  - one repair pass for non-JSON or wrong-schema outputs
  - more permissive defaults for non-essential structured fields
  - lightweight coercion for list-shaped payloads returned where single-field wrapper objects were expected
- Clean phase-5 local subsets completed:
  - prospective `gsm8k` unseen subset: offset `1168`, limit `3`
  - frozen replication `svamp` subset: offset `0`, limit `3`
- Main local findings:
  - `gsm8k`:
    - both local models scored `0/3` on every method
    - no local mechanistic replication signal was observed
  - `svamp`:
    - `Qwen2.5-0.5B` tied at `1/3` across all methods
    - `Qwen2.5-1.5B` showed `dart_adv_same_v1 = 1/3` while the other methods stayed at `0/3`
    - this was too small to support a real capacity-boundary claim
- Coverage-conditioned local readout:
  - in the tiny local main subset, no coverage=`0` case was solved by `dart_adv_same_v1`
  - therefore the strongest API-side mechanistic evidence did not reappear locally
- Final phase-5 decision:
  - local open-model evidence did not materially strengthen the story
  - explicit auditable candidate structure still was not rescued as the key ingredient
  - stop experimentation and keep the nuanced boundary-condition paper posture

### Phase 5 rerun: 4GPU larger-local retest

- User requested a more meaningful local rerun using the full GPU box rather than the earlier `0.5B/1.5B` tiny-model check.
- Practical rerun plan:
  - keep prompts frozen
  - keep the same local `hf_local` backend
  - add explicit `max_memory` support so HF local loads can be sharded intentionally
  - use all `4 x RTX 3090` concurrently via two parallel local runs
- Model bring-up audit:
  - attempted `Qwen/Qwen2.5-14B-Instruct` authenticated download for a larger same-family retest
  - download throughput remained too slow for a clean same-turn 14B retest and started to become an infrastructure bottleneck
  - attempted alternative second local model paths (`Qwen2.5-Math-7B`, cached DeepSeek 7B distill), but structured-output reliability remained too weak for a clean end-to-end comparison
  - therefore the final clean rerun evidence uses the largest fully stable cached local path on this node:
    - `Qwen/Qwen2.5-7B-Instruct`
- Exact rerun execution:
  - `GSM8K` prospective subset: offset `658`, limit `10`, GPUs `0,1`
  - `SVAMP` replication subset: offset `0`, limit `10`, GPUs `2,3`
  - methods:
    - `direct_cot`
    - `self_refine_1`
    - `freeform_devil_advocate_same`
    - `adv_select_only_shared`
    - `dart_adv_same_v1`
- Backend robustness changes required for the rerun:
  - added `max_memory` passthrough for local multi-GPU sharding
  - added one more object-only JSON repair step for local models
  - kept tests green after the change (`7 passed`)
- Rerun results:
  - `gsm8k`, `n=10`
    - `direct_cot = 0.30`
    - `self_refine_1 = 0.20`
    - `freeform_devil_advocate_same = 0.40`
    - `adv_select_only_shared = 0.30`
    - `dart_adv_same_v1 = 0.30`
  - `svamp`, `n=10`
    - `direct_cot = 0.10`
    - `self_refine_1 = 0.10`
    - `freeform_devil_advocate_same = 0.50`
    - `adv_select_only_shared = 0.10`
    - `dart_adv_same_v1 = 0.30`
- Coverage-conditioned rerun readout:
  - `gsm8k`
    - coverage=`0`: `adv_select_only_shared = 0/6`, `dart_adv_same_v1 = 0/6`
    - coverage=`1`: both `3/4`
  - `svamp`
    - coverage=`0`: `adv_select_only_shared = 0/9`, `dart_adv_same_v1 = 2/9`
    - coverage=`1`: both `1/1`
- Interpretation:
  - the larger-local rerun is more meaningful than the tiny-model phase-5 slice because the models are no longer completely floor-limited
  - the core mechanism partially reappears on `SVAMP`: selection-only stays near floor under missing coverage while DART same-context recovers some cases
  - that same mechanism does not reappear on this `GSM8K` rerun slice
  - the stronger auditable-candidate-set claim still is not rescued because `freeform_devil_advocate_same` remains better than DART on both rerun datasets
- Final rerun decision:
  - this rerun strengthens confidence that the earlier tiny-model phase-5 readout was underpowered
  - but it still does not justify changing the paper posture away from the nuanced boundary-condition story

### Phase 5 rerun: 4GPU high-util long run

- User requested a longer rerun that keeps all four GPUs busy for a sustained period rather than relying on tiny local slices.
- Execution change:
  - instead of 2-GPU sharding, switch to `1 x Qwen2.5-7B-Instruct fp16` process per GPU
  - run four shards in parallel so the box stays busy for a long continuous interval
- Practical reason for this design:
  - it gives higher sustained cluster utilization than a single multi-GPU local model
  - it avoids the still-unfinished `14B` download path becoming the bottleneck
  - it uses the largest local model that was already fully stable end-to-end on this machine during this turn
- Exact long-run shard layout:
  - GPU `0`: `gsm8k`, offset `668`, limit `50`
  - GPU `1`: `gsm8k`, offset `718`, limit `50`
  - GPU `2`: `svamp`, offset `100`, limit `50`
  - GPU `3`: `multiarith`, offset `0`, limit `50`
  - methods:
    - `direct_cot`
    - `self_refine_1`
    - `freeform_devil_advocate_same`
    - `adv_select_only_shared`
    - `dart_adv_same_v1`
- Runtime / utilization snapshots during the run:
  - early sustained snapshot: GPU utilization approximately `72% / 92% / 95% / 94%`
  - later sustained snapshot: GPU utilization approximately `85% / 84% / 94% / 93%`
  - later sustained snapshot: GPU utilization approximately `90% / 85% / 94% / 94%`
  - memory stayed around `15-16 GiB` per GPU during active generation
- Scale:
  - `200` questions total
  - `1000` per-method records total
- Long-run results:
  - `gsm8k`, `n=100`
    - `direct_cot = 0.13`
    - `self_refine_1 = 0.14`
    - `freeform_devil_advocate_same = 0.45`
    - `adv_select_only_shared = 0.13`
    - `dart_adv_same_v1 = 0.17`
  - `svamp`, `n=50`
    - `direct_cot = 0.64`
    - `self_refine_1 = 0.64`
    - `freeform_devil_advocate_same = 0.70`
    - `adv_select_only_shared = 0.64`
    - `dart_adv_same_v1 = 0.64`
  - `multiarith`, `n=50`
    - `direct_cot = 0.50`
    - `self_refine_1 = 0.52`
    - `freeform_devil_advocate_same = 0.74`
    - `adv_select_only_shared = 0.50`
    - `dart_adv_same_v1 = 0.54`
- Coverage-conditioned readout:
  - `gsm8k`
    - coverage=`0`: selection-only `0/70`, DART `3/70`
    - coverage=`1`: selection-only `13/30`, DART `14/30`
  - `multiarith`
    - coverage=`0`: selection-only `0/17`, DART `1/17`
    - coverage=`1`: selection-only `25/33`, DART `26/33`
  - `svamp`
    - coverage=`0`: selection-only `0/13`, DART `0/13`
    - coverage=`1`: both `32/37`
- Interpretation:
  - this long run is the strongest local evidence collected so far because it avoids the tiny-model / tiny-slice failure mode
  - the supported mechanism now partially replicates locally on `gsm8k` and `multiarith`:
    - selection-only stays at the floor in coverage-miss cases
    - DART same-context recovers a small non-zero fraction of those cases
  - `svamp` does not show a DART-over-selection gain in this larger local slice
  - most importantly, the stronger auditable-candidate-set claim still does not recover:
    - `freeform_devil_advocate_same` remains much stronger than DART on all three long-run datasets
- Final long-run decision:
  - this run materially strengthens the local external-validity story for the narrow mechanism
  - it still does not justify claiming that explicit auditable candidate sets are the key ingredient
  - the correct paper posture remains the nuanced boundary-condition paper

## 2026-03-11

### Confidence branch kickoff

- A new branch is started after freezing all DART-phase results.
- This is explicitly **not** another DART prompt-tuning phase.
- New branch name:
  - `CHASE` = `CHallenge-Aware Sufficiency Estimation`
- New branch question:
  - can challenge-conditioned confidence control whether open-ended arithmetic reasoning should stop, continue with another devil's-advocate round, or abstain?

### Frozen old-branch context carried into CHASE

- Keep all old DART artifacts intact.
- Use old-branch conclusions as design constraints:
  - open-ended arithmetic remains the only clearly positive regime
  - same-context freeform devil's-advocate is a central baseline
  - explicit candidate sets are not to be assumed necessary
  - closed-label tasks remain frozen contrast evidence and are out of scope

### Literature scan notes for CHASE

- `Generating with Confidence` and related verbalized-UQ work:
  - verbalized confidence can discriminate correctness somewhat, but it is unstable and prompt-sensitive.
- `On Verbalized Confidence Scores for LLMs` / `Rescaling Confidence`:
  - scale choice matters; large `0-100` scales can create fake granularity.
  - branch default should therefore start with a small bounded scale such as `0-20`.
- `Confidence Estimation for LLMs in Multi-turn Interactions`:
  - confidence should be measured over trajectories, not only on the first answer.
  - this supports collecting stage-wise draft -> challenge -> revision traces.
- `Are LLM Decisions Faithful to Verbal Confidence?`:
  - verbalized confidence should not be treated as a direct truth estimate.
  - branch implication: raw VC is a baseline feature, not the final controller.
- `ADVICE` and distractor-conditioned confidence work:
  - answer-conditioned and alternative-aware confidence are more defensible than generic self-confidence.
  - branch implication: include DiNCo-lite alternative features.
- `CoRefine` and other confidence-guided refinement papers:
  - adaptive test-time compute is plausible, but must be compared against fixed-budget strong baselines.
- debate-confidence papers:
  - adversarial interaction can inflate confidence rather than calibrate it.
  - branch implication: post-challenge deltas and stability matter more than raw post-hoc confidence alone.

### Branch design implications frozen before implementation

- Confidence is treated as a **control signal**, not a correctness guarantee.
- The branch will center:
  - answer-conditioned verbalized confidence
  - binary self-eval margins
  - answer logprob features
  - small-sample disagreement / semantic dispersion
  - DiNCo-lite distractor-relative confidence
  - challenge-response deltas after critique
- The branch will **not** center explicit candidate sets.
- Output format should prefer robust tagged text over brittle nested JSON for local models.

### Local model and dataset plan

- Preferred local model pair:
  - primary: `Qwen/Qwen2.5-Math-7B-Instruct`
  - secondary replication: `Qwen/Qwen2.5-7B-Instruct`
- Feasibility check:
  - both model snapshots are already cached locally, so bring-up cost is low.
- Dataset plan:
  - `gsm8k_train` for clean new calibration/eval splits, because prior DART phases mostly consumed GSM8K test examples
  - `EleutherAI/asdiv` as a fully new arithmetic benchmark
  - `svamp` only as optional continuity evidence if later needed

### Runtime expectations and stop rules

- Main cost should be local wall-clock only; API is not the main path.
- Execution order:
  1. branch plan + backend hardening
  2. tiny dev for confidence elicitation stability
  3. fixed-budget trace collection
  4. signal benchmark
  5. lightweight calibrator
  6. adaptive main evaluation
- Stop early if:
  - confidence extraction remains too unstable after one careful dev pass
  - no signal materially improves on raw verbalized confidence
  - CHASE does not improve the accuracy/compute or risk/coverage trade-off over fixed freeform baselines

### CHASE dev freeze outcome

- Tiny dev was run first on:
  - `gsm8k_train`
  - `asdiv`
- Initial preferred model `Qwen/Qwen2.5-Math-7B-Instruct` proved brittle for this branch:
  - tagged confidence outputs were unstable
  - answer extraction frequently fell back to raw prose
  - the branch risked becoming an output-control project rather than a confidence study
- Fallback decision:
  - make `Qwen/Qwen2.5-7B-Instruct` the primary model for the branch
  - retain `Qwen/Qwen2.5-Math-7B-Instruct` only as a smaller secondary replication
- Prompt-format freeze after dev:
  - keep bounded answer-conditioned verbalized confidence on `0-20`
  - keep same-context freeform devil's-advocate
  - keep tagged outputs
  - drop `0-100` from the main trace runs after confirming it offered little extra useful dispersion over `0-20`

### CHASE fixed-budget traces and main result

- Primary trace collection completed on `Qwen/Qwen2.5-7B-Instruct`:
  - calibration:
    - `gsm8k_train`: `120`
    - `asdiv`: `100`
  - held-out evaluation:
    - `gsm8k_train`: `160`
    - `asdiv`: `150`
- Secondary replication completed on `Qwen/Qwen2.5-Math-7B-Instruct`:
  - `gsm8k_train` calibration: `20`
  - `gsm8k_train` evaluation: `20` completed before stopping; the planned `40`-example eval was cut because throughput became the dominant issue and the model was already near floor

### CHASE signal benchmark findings

- On the primary combined held-out traces (`n=930` stage rows):
  - `dinco_gap` was the best correctness signal:
    - `AUROC ≈ 0.796`
  - `self_eval_yes_prob` was second:
    - `AUROC ≈ 0.702`
  - bounded raw verbal confidence was weaker:
    - `AUROC ≈ 0.646`
  - answer logprob was weakest among the retained main signals:
    - `AUROC ≈ 0.566`
- This supports the branch thesis that raw verbal confidence alone is not enough, and that alternative-aware / challenge-aware signals are more useful.

### CHASE main method findings

- On `gsm8k_train` with `Qwen/Qwen2.5-7B-Instruct`:
  - `direct_cot = 0.2375`
  - `freeform_fixed1_same = 0.3500`
  - `freeform_fixed2_same = 0.3563`
  - `raw_vc_gate = 0.3563`
  - `robust_rule_gate = 0.3563`
  - `CHASE_calibrated = 0.3250`
  - interpretation:
    - CHASE improves over `direct_cot`
    - but it does not beat fixed freeform or simple rule-based gating on this harder arithmetic slice
- On `asdiv` with `Qwen/Qwen2.5-7B-Instruct`:
  - `direct_cot = 0.8600`
  - `freeform_fixed1_same = 0.5267`
  - `freeform_fixed2_same = 0.7133`
  - `raw_vc_gate = 0.7267`
  - `robust_rule_gate = 0.8000`
  - `CHASE_calibrated = 0.8333`
  - interpretation:
    - CHASE is clearly better than always doing 1 or 2 critique rounds
    - but it still does not beat direct generation on this easier dataset
- Secondary `Qwen/Qwen2.5-Math-7B-Instruct` result:
  - near-floor behavior on the small GSM8K replication
  - no usable adaptive-control advantage emerged
  - practical conclusion: below a certain model-stability / base-quality threshold, confidence-control does not rescue the model

### CHASE branch conclusion

- The branch is not a strong new methods win.
- Supported statement:
  - challenge-conditioned composite confidence is more useful than raw verbalized confidence
  - adaptive control can beat naive fixed-K freeform critique on easier arithmetic (`asdiv`)
  - adaptive control is not strong enough to beat the best fixed freeform baselines on harder arithmetic (`gsm8k_train`)
- Final branch posture:
  - nuanced partial result
  - not a broad replacement for fixed-K critique

### VCHASE-R2 kickoff

- Starting bounded R2 follow-up after the frozen V-CHASE result.
- Scope is explicitly narrower than a new method branch:
  - replicate the hard-set PRM-feature gain
  - disentangle PRM-as-feature vs PRM-as-judge
  - test whether dual-head still matters beyond simpler alternatives
  - diagnose mixed transfer without reopening prompt design
- Audit status at kickoff:
  - frozen V-CHASE reports re-read first
  - existing V-CHASE traces are reusable
  - existing tests still pass:
    - `pytest -q` -> `15 passed`
- Dataset audit at kickoff:
  - `gsm8k_train = 7473`
  - `asdiv = 2305`
  - `svamp = 300`
- Fresh local replication windows reserved beyond earlier CHASE/V-CHASE use:
  - `gsm8k_train`: start `550`, target `200`
  - `asdiv`: start `470`, target `150`
  - `svamp`: start `170`, target `130`
- Fixed phase order:
  1. offline frontier and mechanism ablation on reusable traces
  2. fresh local replication
  3. optional small API challenger diagnostic only if transfer remains unresolved

### VCHASE-R2 outcome

- Offline trace-reuse ablation was completed first on reused V-CHASE traces with fresh PRM rescoring.
- Key offline findings:
  - PRM-only scalar signals remained weak.
  - Hard-fit replay on `gsm8k_train` still supported moving beyond CHASE:
    - `CHASE_calibrated = 0.3600`
    - `VCHASE_dualhead_PRM_hardopt = 0.4667`
  - But the mechanism already started to simplify:
    - `VCHASE_dualhead_noPRM = 0.4667`
    - i.e. the hard-fit gain did not require PRM features on the reused traces.
- Fresh local replication was then run on new held-out IDs only:
  - `gsm8k_train`: `200` examples from offset `550`
  - `asdiv`: `150` examples from offset `470`
  - `svamp`: `130` examples from offset `170`
- Fresh local replication result:
  - `gsm8k_train`
    - `CHASE_calibrated = 0.4750`
    - `VCHASE_dualhead_PRM_hardopt = 0.4900`
    - `VCHASE_dualhead_noPRM = 0.4900`
    - `VCHASE_singlehead_PRM = 0.5000`
    - `verifier_rule_gate = 0.5100`
  - `asdiv`
    - `VCHASE_dualhead_PRM_balanced = 0.8933`
    - low-round easy-set behavior was preserved
  - `svamp`
    - `VCHASE_dualhead_PRM_hardopt = 0.6846`
    - `VCHASE_dualhead_noPRM = 0.6846`
    - directionally better than CHASE and fixed freeform, but still not a decisive mechanism win
- Final R2 interpretation:
  - the hard-set improvement over CHASE remains directionally positive on fresh data
  - but the mechanism story weakens materially:
    - PRM features are not clearly necessary
    - dual-head is not clearly stronger than single-head
    - verifier-rule remains highly competitive
- Because the unresolved issue after Phase 2 was no longer challenger quality but mechanism collapse, the optional API challenger diagnostic was skipped.

## 2026-03-12

### EIR kickoff

- Starting a new methods branch:
  - `EIR = Executable Intervention Routing`
- This branch keeps DART, CHASE, V-CHASE, and VCHASE-R2 frozen.
- The branch question is explicitly different from prior controller branches:
  - not whether to deliberate more
  - not whether confidence is high enough
  - not whether PRM is sufficient
  - but which corrective intervention is actually executable for the current draft on the current instance

### Frozen-context audit

- Re-read before implementation:
  - `reports/phase4_integrated_report.md`
  - `reports/phase5_integrated_report.md`
  - `reports/confidence_signal_benchmark.md`
  - `reports/chase_main_report.md`
  - `reports/chase_stop_or_pivot.md`
  - `reports/verifier_signal_benchmark.md`
  - `reports/vchase_main_report.md`
  - `reports/vchase_stop_or_pivot.md`
  - `reports/vchase_r2_plan.md`
  - `reports/vchase_r2_main_report.md`
  - `reports/vchase_r2_failure_notes.md`
  - `reports/vchase_r2_stop_or_submit.md`
  - `reports/final_claim_matrix.md`
  - `reports/reviewer_risk_audit.md`
  - `reports/final_submission_memo.md`
  - `research_log.md`
  - `decision_log.md`
  - `README.md`
- Main carry-over conclusion:
  - the unresolved bottleneck is likely not “more confidence” or “more PRM”
  - it is which corrective intervention the model can actually execute successfully on a given draft/problem instance

### Literature scan notes for EIR

- `Strategy Executability in Mathematical Reasoning`
  - supports the branch thesis that strategy usage / relevance and executability are distinct
  - directly motivates action-specific executability probes
- `Formula-One Prompting`
  - supports equation formalization as a distinct corrective action
  - does not justify collapsing the branch into equations-only routing
- `Structure Enables Effective Self-Localization of Errors in LLMs`
  - supports structured localization / backtracking as a distinct action family
  - does not justify long iterative correction loops here
- `interwhen`
  - supports cheap monitors on partial state
  - does not justify using monitors as final judges
- `ODAR`
  - supports cost-aware routing
  - does not justify difficulty-only routing; EIR must remain action-specific
- `DenoiseFlow`
  - supports uncertainty-aware regulation
  - does not justify another generic uncertainty-controller branch
- `InT`
  - supports intervention-level credit assignment analysis
  - does not justify any training step in this repo
- `Are Reasoning LLMs Robust to Interventions on Their Chain-of-Thought?`
  - supports the caution that relevant interventions can still be harmful
  - strengthens the need for action-level regret analysis

### Fresh split audit for the new branch

- Existing result manifests were scanned to count already-consumed IDs:
  - `gsm8k`: `1188`
  - `gsm8k_train`: `715`
  - `asdiv`: `595`
  - `svamp`: `300`
  - `multiarith`: `180`
- Implication:
  - `svamp` and `multiarith` are fully exhausted for genuinely fresh transfer evaluation
  - EIR cannot honestly reuse them as the fresh transfer role
  - a fresh arithmetic transfer set must be introduced if the branch is to preserve the hard/easy/transfer design

### EIR initial plan

- Action palette at kickoff:
  - `STOP`
  - `FREEFORM_CRITIQUE`
  - `EQUATION_REDERIVE`
  - `PYTHON_RECOMPUTE`
  - `LOCALIZE_BACKTRACK`
  - replacement-only action if needed later: `CONSTRAINT_CHECKLIST`
- Required preview probes:
  - critique specificity
  - equation completeness
  - python parse/execution status
  - localization concreteness
- Router family:
  - best fixed action
  - relevance-only
  - executability-only
  - full EIR
- Calibration action bank plan:
  - `gsm8k_train = 100`
  - `asdiv = 100`
  - fresh transfer set = `80`
- Fresh held-out main target:
  - `gsm8k_train = 200`
  - `asdiv = 150`
  - fresh transfer set = `130`

### Runtime and stop policy

- Expected local runtime on 4 GPUs:
  - tiny dev: under `1h`
  - calibration action bank: about `4-6h`
  - offline router fitting: under `30m`
  - fresh held-out main: about `5-7h`
- This branch should not stop just because the first router underperforms.
- The bounded pivot ladder will be used if needed:
  - one action replacement
  - one router-objective pivot
  - one optional bounded API micro-diagnostic

### EIR implementation and tiny-dev status

- Added new EIR-specific components:
  - prompt bank under `prompts/eir/`
  - `dart_research.eir` package with:
    - action-bank runner
    - safe python execution wrapper
    - action-utility router
  - scripts:
    - `scripts/eir_collect_actionbank.py`
    - `scripts/eir_offline_router.py`
    - `scripts/eir_main.py`
    - `scripts/eir_actionbank_report.py`
- Added initial EIR tests:
  - python execution safety
  - action-bank serialization
  - router build / fit smoke
- New tests pass:
  - `pytest -q tests/test_eir_core.py` -> `4 passed`

### Disk and cache intervention

- Local experimentation initially hit a real infrastructure blocker:
  - `/workspace` and `/root` were both at `100%` usage
- Root cause was not result artifacts but a large Hugging Face model cache under `/root/.cache/huggingface`
- To unblock new local runs without touching prior branch results:
  - removed large, reproducible cached checkpoints not needed for EIR
  - retained:
    - `Qwen/Qwen2.5-7B-Instruct`
    - `Qwen/Qwen2.5-Math-7B-Instruct`
    - `Qwen/Qwen2.5-Math-PRM-7B`
- After cleanup:
  - free space recovered to about `94G`

### EIR tiny-dev findings

- `gsm8k_train` tiny dev:
  - all four probes parsed cleanly
  - `PYTHON_RECOMPUTE` was already the strongest action on the 12-example hard slice:
    - accuracy `0.8333`
  - `STOP`, `FREEFORM_CRITIQUE`, and `LOCALIZE_BACKTRACK` all sat near `0.50`
  - interpretation:
    - the initial palette is genuinely heterogeneous
    - executability is already visible because the best action is not the same as the most semantically generic one
- `asdiv` tiny dev:
  - all probes parsed cleanly
  - `STOP` and `EQUATION_REDERIVE` stayed high at `0.9167`
  - `PYTHON_RECOMPUTE` reached `1.0000`
  - `FREEFORM_CRITIQUE` dropped to `0.8333`
  - interpretation:
    - easy-set over-deliberation remains a real risk
    - a router that can keep or cheaply recompute should outperform fixed freeform critique here
- Minimal global parse fix after dev:
  - scratch fallback now strips stray tags before truncation
  - this is a parse-hygiene change, not a method change

### Transfer-role dataset status during dev

- `svamp` and `multiarith` are fully exhausted from earlier branches, so they cannot serve as a fresh transfer role.
- `mawps` loader bring-up is partially working:
  - direct one-shot loading of examples succeeds
  - but repeated action-bank collection processes intermittently stall before generation
- Branch decision for forward progress:
  - keep `mawps` as the preferred fresh transfer candidate if it stabilizes
  - in parallel, reserve the remaining unseen `gsm8k` test region as a fallback secondary held-out role so the branch does not stall on transfer-data plumbing

### EIR calibration launch

- Began main calibration action-bank collection on fresh hard/easy IDs:
  - `gsm8k_train`: `100` examples from offset `820`
  - `asdiv`: `100` examples from offset `640`
- Overlap audit on the first written records showed `0` overlap with prior-branch sample IDs.
- Goal of this phase:
  - one frozen draft per instance
  - all probes executed from that draft
  - all full actions executed from that same draft
  - offline router development only after the counterfactual bank exists

### EIR calibration execution update

- The first `asdiv` shard launched at offset `640` never emitted a record despite sustained GPU activity.
- Rather than blocking the whole branch on that shard:
  - stopped only the stalled process
  - relaunched an equivalent fresh `asdiv` shard at offset `740`
  - retained the already-progressing `asdiv` shard at offset `690`
- Interpretation:
  - this is a collection-scheduling fix, not a method or split-policy change
  - the branch still targets `100` easy-set calibration examples through fresh non-overlapping IDs

### EIR offline ablation hardening

- The first offline router script version evaluated on the same action-bank examples it fit on.
- Before treating any router result as evidence, the script was upgraded to:
  - split calibration question IDs into train / held-out validation subsets
  - choose `BEST_FIXED_ACTION` on train only
  - fit executability/full routers on train only
  - evaluate all routers and rules on held-out validation only
  - include predeclared feature-drop ablations:
    - no PRM-derived generic features
    - no action probes
    - no python execution-success feature
    - no equation-completeness feature
    - no localization-concreteness feature
- This is a validity fix for the offline phase, not a method pivot.

### EIR partial calibration snapshot

- A rolling snapshot on the currently written calibration bank was used only for branch steering, not as a final result.
- Current direction from the partial action summary:
  - `PYTHON_RECOMPUTE` is the strongest fixed action on both the hard and easy slices seen so far
  - `RELEVANCE_ONLY_ROUTER` is clearly weaker than the best fixed action
  - full learned routers are not yet beating `BEST_FIXED_ACTION` on the partial held-out split
- Current interpretation:
  - executability evidence is already visible in the gap between relevance-only and the stronger fixed actions
  - but the stronger routing claim still depends on the full calibration bank and may require the predeclared router-objective pivot if best-fixed python remains dominant

### EIR hard-only calibration checkpoint

- The hard `gsm8k_train` calibration bank reached its planned `100` examples first, so a hard-only checkpoint was run in parallel with continuing easy/transfer collection.
- Hard action-bank summary at `100` examples:
  - `STOP`: accuracy `0.27`
  - `FREEFORM_CRITIQUE`: accuracy `0.49`
  - `EQUATION_REDERIVE`: accuracy `0.45`
  - `LOCALIZE_BACKTRACK`: accuracy `0.57`
  - `PYTHON_RECOMPUTE`: accuracy `0.75`
- Interpretation:
  - `PYTHON_RECOMPUTE` is currently the strongest hard-set fixed action by a large margin
  - the action palette is still heterogeneous, but the branch must now explain why routing can beat a very strong executable recomputation baseline

### EIR hard-only offline routing checkpoint

- Held-out hard-only offline replay with the initial cost-aware utility-regression router gave:
  - `BEST_FIXED_ACTION_hardopt = 0.70`
  - `FULL_EIR_ROUTER_hardopt = 0.65`
  - `RELEVANCE_ONLY_ROUTER_hardopt = 0.40`
  - `EXECUTABILITY_ONLY_ROUTER_hardopt = 0.30`
- Important nuance:
  - the regression router did not collapse into always choosing one action
  - but it still failed to learn that `PYTHON_RECOMPUTE` should dominate more often on this hard slice
- Bounded Pivot B was therefore prepared and tested:
  - add a multiclass classifier router that predicts the cost-aware oracle action directly from state + probe features
- Hard-only classifier checkpoint:
  - `FULL_EIR_ROUTER_cls_hardopt = 0.55`
  - `EXECUTABILITY_ONLY_ROUTER_cls_hardopt = 0.45`
- Interpretation:
  - the first utility-regression formulation is weak
  - the first direct-classification pivot is also not yet enough
  - the branch should not conclude anything until easy/transfer calibration is complete and the single allowed palette pivot is judged against the fuller bank

### EIR Pivot A initiation

- The hard-only and mixed partial action-bank evidence was strong enough to justify preparing the single allowed palette replacement:
  - `EQUATION_REDERIVE` had effectively zero oracle selection in the available checkpoint views
  - `FREEFORM_CRITIQUE`, `STOP`, and `PYTHON_RECOMPUTE` all retained non-zero oracle mass
- Therefore Pivot A was activated in bounded form:
  - add `CONSTRAINT_CHECKLIST` as the replacement-only action
  - implement checklist probe + checklist action prompts
  - add a post-hoc replacement path that swaps `EQUATION_REDERIVE` for `CONSTRAINT_CHECKLIST` from the same frozen drafts, without re-running all other actions

### EIR main-collection pause for palette decision

- A fresh hard-main shard was briefly started after the hard calibration closed.
- It was then intentionally interrupted at low count so the branch would not accumulate a large held-out main bank under a palette that might immediately be replaced by Pivot A.
- This pause is a method-selection safeguard, not a failure of the main path.
- Main collection will resume after the hard-set checklist replacement check resolves whether Pivot A is worth keeping.

### EIR Pivot A outcome

- The bounded hard-set checklist replacement completed on the same frozen `gsm8k_train` calibration drafts.
- Replacement-only action summary:
  - `CONSTRAINT_CHECKLIST`: accuracy `0.00`
  - harmful rate `0.27`
  - average cost-aware utility strongly negative
- Held-out hard-only offline replay with the checklist palette gave:
  - `BEST_FIXED_ACTION_hardopt = 0.70`
  - `FULL_EIR_ROUTER_hardopt = 0.60`
  - `FULL_EIR_ROUTER_cls_hardopt = 0.55`
  - `RELEVANCE_ONLY_ROUTER_hardopt = 0.20`
- Interpretation:
  - Pivot A failed decisively on the hard set
  - the replacement action does not rescue the palette
  - the branch should revert to the original five-action palette for mixed offline fitting and held-out main evaluation

### EIR mixed offline router study

- The mixed original-palette held-out offline replay completed on:
  - `gsm8k_train 100`
  - `asdiv 100`
  - `mawps 80`
- Main offline takeaways:
  - `RELEVANCE_ONLY_ROUTER` was clearly weak on both `gsm8k_train` and `asdiv`
  - `BEST_FIXED_ACTION` remained strongest on the hard set
  - `FULL_EIR` did not beat `BEST_FIXED_ACTION` offline
  - `FULL_EIR` still beat `RELEVANCE_ONLY_ROUTER` by a wide margin
  - the classifier-style router-objective pivot improved oracle-action matching but not realized accuracy enough to change the branch direction
- Important nuance from the calibration bank:
  - `gsm8k_train` oracle action mass remained genuinely heterogeneous:
    - `STOP 43`
    - `PYTHON_RECOMPUTE 42`
    - `FREEFORM_CRITIQUE 13`
    - `LOCALIZE_BACKTRACK 2`
  - `asdiv` also retained a real `STOP` / `PYTHON_RECOMPUTE` split
  - `mawps` showed almost no recoverable action headroom for the current local model

### EIR held-out main evaluation

- Fresh held-out main bank collected with the original palette:
  - hard: `gsm8k_train 200`
  - easy: `asdiv 150`
  - transfer: `mawps 120`
- Fresh main headline results:
  - `gsm8k_train`:
    - `BEST_FIXED_ACTION = 0.8250`
    - `FULL_EIR_ROUTER_hardopt = 0.7800`
    - `EXECUTABILITY_ONLY_ROUTER = 0.7700`
    - `RELEVANCE_ONLY_ROUTER = 0.6000`
  - `asdiv`:
    - `FULL_EIR_ROUTER_balanced = 0.6667`
    - `BEST_FIXED_ACTION = 0.6067`
    - `EXECUTABILITY_ONLY_ROUTER = 0.6133`
    - `RELEVANCE_ONLY_ROUTER = 0.5133`
  - `mawps`:
    - `STOP = 0.0333`
    - `FULL_EIR_ROUTER_hardopt = 0.0250`
- Pairwise interpretation:
  - `FULL_EIR` beats `RELEVANCE_ONLY_ROUTER` very clearly on both hard and easy sets
  - `FULL_EIR` beats `BEST_FIXED_ACTION` directionally on `asdiv`
  - `BEST_FIXED_ACTION` still beats `FULL_EIR` on `gsm8k_train`
  - `FULL_EIR` and `EXECUTABILITY_ONLY_ROUTER` are effectively tied on the hard set
- Branch-level interpretation:
  - executability matters beyond semantic relevance
  - but the current full router does not yet beat the strongest fixed executable hard-set action
  - the cleanest surviving positive result is on the easy set, not the hard set

### HEIR branch launch

- HEIR is launched as a new methods branch on top of the frozen EIR diagnosis.
- The core motivation is not “more confidence” or “more actions”.
- The diagnosis to test is:
  - the flat router class is mismatched to the empirical action geometry
  - the real decision structure is hierarchical:
    - `KEEP` vs `INTERVENE`
    - `PYTHON_RECOMPUTE` vs language repair
    - `LOCALIZE_BACKTRACK` vs `FREEFORM_CRITIQUE`
- Literature guardrails recorded for the branch:
  - relevant action is not the same as executable action
  - a flat action router can be statistically misaligned with oracle action geometry
  - tool recomputation and keep/stop decisions are first-class policy decisions
  - structured localization occupies a different niche from freeform critique
  - verifiers and PRMs remain auxiliary signals only
- Planned execution order:
  - oracle geometry audit from EIR
  - tiny pruned-palette dev
  - fresh HEIR calibration bank
  - transfer headroom screen
  - offline hierarchy study
  - fresh held-out main

### HEIR oracle geometry and transfer screen

- Oracle geometry audit from the frozen EIR action bank confirms the intended hierarchy:
  - `asdiv`: oracle mass is dominated by `STOP 0.65`, then `PYTHON_RECOMPUTE 0.24`, then `FREEFORM_CRITIQUE 0.11`
  - `gsm8k_train`: oracle mass is split between `STOP 0.43` and `PYTHON_RECOMPUTE 0.42`, with a smaller language branch
  - flat-router regret is concentrated mostly in Gate 1 and Gate 2, not Gate 3
- Transfer headroom screen rejected `mawps` as a main transfer claim set and selected `multiarith`:
  - `multiarith`: `oracle_minus_keep = 0.25`, `best_fixed_minus_direct = 0.25`
  - `mawps`: essentially no action headroom
- This means HEIR should be evaluated on:
  - hard: `gsm8k_train`
  - easy: `asdiv`
  - transfer/stress: `multiarith`

### HEIR dev and calibration

- Tiny dev with the pruned palette was stable after the single global keep-tag parse fix.
- Fresh HEIR calibration bank collected:
  - `gsm8k_train 120`
  - `asdiv 100`
- Fresh HEIR held-out bank collected:
  - `gsm8k_train 200`
  - `asdiv 150`
  - `multiarith 100`

### HEIR initial offline and fresh-main result

- Initial HEIR gate-classification policy underperformed badly on the hard set:
  - offline `gsm8k_train`: `HEIR_KEEPPRIOR_hardopt = 0.6250`
  - fresh main `gsm8k_train`: `HEIR_KEEPPRIOR_hardopt = 0.5300`
- But the easy-set story remained real:
  - fresh main `asdiv`: `HEIR_KEEPPRIOR_hardopt = 0.8267`, `HEIR_KEEPPRIOR_balanced = 0.8200`
- Main failure pattern from regret decomposition:
  - hard-set regret is dominated by `gate1_missed_intervene` and `gate2_tool_miss`
  - gate-3 localize-vs-freeform noise is secondary

### HEIR pivot ladder execution

- Pivot A (`KEEP` prior / stop regularization):
  - tested implicitly through `HEIR_KEEPPRIOR_*` vs `HEIR_no_keep_prior`
  - result: no meaningful difference on the hard set
  - interpretation: the problem was not insufficient keep bias; the initial hard failure was actually missed intervention structure
- Pivot B (language-branch simplification):
  - implemented as `HEIR_flattened_tool_language`
  - offline val:
    - `gsm8k_train = 0.6667`
    - `asdiv = 0.7000`
  - fresh main:
    - `gsm8k_train = 0.7500`
    - `asdiv = 0.7933`
    - `multiarith = 0.8800`
- Pivot C (objective pivot from oracle-gate classification to gate-wise utility-delta routing):
  - implemented as `HEIR_pairwise_hardopt` and `HEIR_pairwise_balanced`
  - offline val:
    - `HEIR_pairwise_hardopt`: `gsm8k_train = 0.6667`
    - `HEIR_pairwise_balanced`: `asdiv = 0.8000`
  - fresh main:
    - `HEIR_pairwise_hardopt`: `gsm8k_train = 0.7500`, `asdiv = 0.7933`, `multiarith = 0.8900`
    - `HEIR_pairwise_balanced`: `gsm8k_train = 0.7350`, `asdiv = 0.8000`, `multiarith = 0.8600`
- Pivot D (API preview micro-diagnostic) was not run:
  - regret stayed concentrated in keep/intervene and tool/language decisions
  - language-preview quality was not the dominant remaining bottleneck

### HEIR final branch interpretation

- Strongest surviving positives:
  - hierarchical routing is empirically justified by oracle action geometry
  - on easy arithmetic, HEIR recovers strong low-action behavior and outperforms fixed freeform critique
  - after the objective pivot, HEIR closes most of the initial hard-set gap:
    - initial hard HEIR: `0.5300`
    - final `HEIR_pairwise_hardopt`: `0.7500`
- Strongest unsupported claims:
  - HEIR does not beat fixed `PYTHON_RECOMPUTE` on `gsm8k_train` (`0.7700`)
  - HEIR does not beat flat `FULL_EIR_ROUTER_balanced` / `hardopt` on the hard set (`0.7650` / `0.7550`)
  - the main hard bottleneck remains Gate 2: missing executable tool wins

### GEM-HEIR branch launch

- GEM-HEIR is launched as a new methods branch on top of the frozen EIR and HEIR diagnosis.
- The branch does NOT reopen actions, candidate sets, or confidence control.
- Central diagnosis carried forward from HEIR:
  - the action geometry is hierarchical
  - Gate 1 and Gate 2 dominate regret
  - the remaining bottleneck is gate-specific margin estimation, not action identity prediction
- Literature guardrails recorded:
  - relevant action is not the same as executable action
  - flat action-class prediction is likely misaligned with the true decision structure
  - tool recomputation vs keep is a first-order boundary
  - localization only matters after the higher-level gate is correct
  - verifier / PRM signals remain auxiliary only
- Planned branch structure:
  - margin audit on frozen EIR/HEIR banks
  - skip broad dev unless preview stability actually breaks
  - fresh calibration bank
  - offline margin study with pivot ladder
  - fresh held-out main plus mixed-workload frontier

### GEM-HEIR execution summary

- Margin audit on frozen EIR/HEIR action banks confirmed the gate-specific geometry:
  - `gsm8k_train`
    - Gate 1 intervene-positive rate: `0.5227`
    - Gate 2 tool-positive rate: `0.7045`
    - Gate 3 localize-positive rate: `0.1909`
  - `asdiv`
    - Gate 1 intervene-positive rate: `0.3000`
    - Gate 2 tool-positive rate: `0.6133`
    - Gate 3 localize-positive rate: `0.1800`
- Transfer headroom screen rejected a main transfer claim set:
  - `svamp` fresh offset had no unused examples left
  - `mawps` fresh slice stayed at floor for direct, keep, best-fixed, and oracle-best
  - transfer is therefore secondary only for this branch
- A fresh GEM calibration bank was collected:
  - `gsm8k_train = 140`
  - `asdiv = 100`
- Offline margin study completed with the full bounded ladder:
  - direct margin regression
  - pairwise classification pivot
  - pairwise ranking pivot
  - regime-stratified subset-aware margin model
  - ablations removing cross-action features, auxiliary CHASE/V-CHASE features, and PRM-derived auxiliaries
- Offline result on the fresh calibration split was genuinely encouraging on the hard set:
  - `gsm8k_train`
    - `PYTHON_RECOMPUTE = 0.8000`
    - `GEM_margin_regression_hardopt = 0.8333`
    - `GEM_global_margin_hardopt = 0.8333`
    - `GEM_subsetaware_margin_hardopt = 0.8333`
  - but easy-set calibration already hinted that aggressive hard-opt GEM variants could over-intervene on `asdiv`

### GEM-HEIR fresh held-out main

- Fresh held-out bank collected:
  - `gsm8k_train = 200`
  - `asdiv = 150`
- Fresh main result did not replicate the offline hard-set win over fixed python:
  - `gsm8k_train`
    - `PYTHON_RECOMPUTE = 0.7250`
    - `BEST_FIXED_ACTION = 0.7250`
    - `HEIR_KEEPPRIOR_balanced_ref = 0.7050`
    - `GEM_subsetaware_margin_hardopt = 0.6850`
    - `GEM_pairwise_ranking_hardopt = 0.6850`
    - `GEM_margin_regression_hardopt = 0.6600`
  - pairwise:
    - `PYTHON_RECOMPUTE` vs `GEM_subsetaware_margin_hardopt`: delta `-0.0398`, CI includes `0`, McNemar `p = 0.1153`
- GEM still improved on prior routers on the hard set, but only modestly:
  - `FULL_EIR_ROUTER_hardopt_ref = 0.6650`
  - `HEIR_pairwise_hardopt_ref = 0.6600`
  - best GEM = `0.6850`
- Easy-set behavior remained strong but GEM was not the best policy:
  - `asdiv`
    - `HEIR_KEEPPRIOR_balanced_ref = 0.8600`
    - `GEM_flat_action_same_features_balanced = 0.8533`
    - `GEM_subsetaware_margin_balanced = 0.8333`
    - `KEEP = 0.6933`
- Mixed-workload frontier still showed value from adaptive routing relative to flat HEIR:
  - `25/75 hard/easy`
    - `PYTHON_RECOMPUTE = 0.8163`
    - `GEM_subsetaware_margin_hardopt = 0.8013`
    - `HEIR_pairwise_hardopt_ref = 0.7750`
  - `75/25 hard/easy`
    - `PYTHON_RECOMPUTE = 0.7554`
    - `GEM_subsetaware_margin_hardopt = 0.7238`
    - `HEIR_pairwise_hardopt_ref = 0.6983`

### GEM-HEIR final interpretation

- Supported:
  - gate-specific margin modeling is a better target than relevance-only routing
  - GEM improves over flat EIR and over the best HEIR references on the hard set
  - GEM preserves useful heterogeneous-workload behavior and remains much better than fixed freeform critique
- Not supported:
  - GEM closes or beats the fixed `PYTHON_RECOMPUTE` hard-set baseline on fresh held-out data
  - regime stratification is the decisive ingredient
  - PRM-derived auxiliary features are necessary
- Strongest surviving methods story:
  - pairwise executability-margin routing is a better fit than flat/hard hierarchical class routing
  - but the hard-set north-star claim still fails because fixed executable recomputation remains stronger than routed mixtures under the current local model family

### TIER branch launch

- TIER is launched as a new methods branch after GEM-HEIR.
- Branch motivation:
  - GEM-HEIR improved over prior routed baselines but still could not beat fixed `PYTHON_RECOMPUTE` on fresh `gsm8k_train`
  - the remaining bottleneck is therefore treated as semantic-to-executable interface quality, not action-family routing
- Literature guardrails recorded:
  - strategy routing is not the same as executable interface selection
  - equation formalization matters insofar as it improves formulation-to-execution quality
  - math word-problem performance conflates formulation and computation
  - verifier / PRM signals remain auxiliary only
- Initial TIER interface palette:
  - `KEEP`
  - `RAW_PYTHON`
  - `QUANTITY_TABLE_TO_CODE`
  - `OPERATOR_SCHEMA_TO_CODE`
  - `EQUATION_SKETCH_TO_CODE`
- Optional bounded pivot interface:
  - `NORMALIZED_QUESTION_TO_CODE`
- Planned branch phases:
  - python/interface failure audit from GEM and HEIR notes
  - tiny dev for parse and execution stability
  - fresh interface-bank calibration
  - offline fixed-interface and selector study
  - fresh held-out main on hard/easy arithmetic

### TIER branch completion

- Tiny dev completed and prompts were frozen without broad prompt changes:
  - `results/tier_dev/gsm8k_train_dev_20260313`
  - `results/tier_dev/asdiv_dev_20260313`
- Fresh calibration bank completed:
  - `gsm8k_train = 150`
  - `asdiv = 100`
- Offline TIER study completed:
  - calibration summary path: `results/tier_offline/tier_calibration_20260313/summary.csv`
  - main offline signal:
    - `gsm8k_train`
      - `RAW_PYTHON_hardopt = 0.7333`
      - `OPERATOR_SCHEMA_TO_CODE_hardopt = 0.8667`
      - `FULL_TIER_ROUTER_hardopt = 0.7000`
  - interpretation:
    - the fixed structured operator-schema interface looked stronger than raw python on the hard calibration split
    - this made TIER a genuine interface-quality test rather than another routing-only branch
- Fresh held-out main collection was run locally and then bounded at a practical stopping point once both held-out roles had enough data for stable comparison:
  - `gsm8k_train = 103`
  - `asdiv = 109`
  - raw shard dirs:
    - `results/tier_main/gsm8k_train_main_shard1_20260313`
    - `results/tier_main/gsm8k_train_main_shard2_20260313`
    - `results/tier_main/gsm8k_train_main_shard3_20260313`
    - `results/tier_main/gsm8k_train_main_shard4_20260313`
    - `results/tier_main/asdiv_main_shard1_20260313`
    - `results/tier_main/asdiv_main_shard2_20260313`
    - `results/tier_main/asdiv_main_shard3_20260313`
    - `results/tier_main/asdiv_main_shard4_20260313`
- Final held-out TIER result:
  - `gsm8k_train`
    - `RAW_PYTHON = 0.6893`
    - `BEST_FIXED_INTERFACE = 0.6893`
    - `OPERATOR_SCHEMA_TO_CODE = 0.7184`
    - `COMPILABILITY_ONLY_INTERFACE_ROUTER_hardopt = 0.7087`
    - `FULL_TIER_ROUTER_hardopt = 0.6311`
  - `asdiv`
    - `KEEP = 1.0000`
    - `RAW_PYTHON = 1.0000`
    - `BEST_FIXED_INTERFACE = 1.0000`
    - `FULL_TIER_ROUTER_balanced = 0.9908`
- Pairwise interpretation:
  - `OPERATOR_SCHEMA_TO_CODE` was directionally above `RAW_PYTHON` on hard held-out, but the CI still crossed zero
  - `FULL_TIER_ROUTER_hardopt` did not beat `RAW_PYTHON` and underperformed the strongest fixed interfaces
- Strongest surviving TIER story:
  - executable interface quality is a more plausible remaining bottleneck than action-family routing
  - structured interfaces can match or slightly exceed raw python on hard arithmetic
  - but the full TIER router is not the main win under the current local model family
- Final TIER artifacts:
  - report bundle in `reports/tier_*`
  - tables in `tables/tier`
  - figures in `figures/tier`
  - project-wide synthesis in `reports/final_integrated_project_report.md`

### OSCAR branch launch

- OSCAR is launched as a new methods branch after TIER.
- Branch motivation:
  - TIER showed that the strongest remaining signal is fixed `OPERATOR_SCHEMA_TO_CODE`, not another router
  - the unresolved bottleneck is therefore treated as semantic-to-executable compilation quality
  - the target failure surface is operator/discretization semantics on hard arithmetic
- Confirmed locally cached models are available without fresh downloads:
  - `Qwen/Qwen2.5-7B-Instruct`
  - `Qwen/Qwen2.5-Math-7B-Instruct`
  - `Qwen/Qwen2.5-Math-PRM-7B`
- Confirmed all four RTX 3090 GPUs were idle at OSCAR branch start.
- Literature pass completed for:
  - Strategy Executability in Mathematical Reasoning
  - Plan before Solving
  - Formula-One Prompting
  - Disentangling Abstract Formulation From Arithmetic Computation
  - NeuroProlog
  - Solving Math Word Problems by Combining Language Models With Symbolic Solvers
  - Mapping to Declarative Knowledge for Word Problem Solving
- Literature-derived guardrails recorded:
  - routing among action families is no longer the main abstraction
  - operator/equation formalization helps because it improves executable interface quality
  - MWP accuracy conflates semantic formulation and arithmetic computation; OSCAR targets formulation-to-execution quality
  - deterministic compilation must be separated from freer code generation
  - PRM/verifier signals remain auxiliary only
- Fresh-capacity check at branch launch:
  - `gsm8k_train`: 7,473 total, prior usage through roughly offset/end `2710`
  - `asdiv`: 2,305 total, prior usage through roughly offset/end `1960`
- Planned branch emphasis:
  - fresh hard calibration and held-out slices from unused `gsm8k_train`
  - secondary `asdiv` sanity only where needed
  - no closed-label reruns
  - no new routing-centric headline

### OSCAR execution

- Implemented OSCAR branch code:
  - `src/dart_research/oscar/compiler.py`
  - `src/dart_research/oscar/runner.py`
  - `src/dart_research/oscar/analysis.py`
  - `scripts/oscar_make_manifests.py`
  - `scripts/oscar_collect_interfacebank.py`
  - `scripts/oscar_offline.py`
  - `scripts/oscar_main.py`
  - `scripts/make_oscar_reports.py`
  - `tests/test_oscar_core.py`
- Generated fresh OSCAR manifests under `data/oscar_manifests_20260313`:
  - hard calibration `gsm8k_train = 150`
  - easy calibration `asdiv = 90`
  - conditioning subsets `gsm8k_train = 60`, `asdiv = 40`
  - hard cluster main `gsm8k_train = 200`
  - hard generic main `gsm8k_train = 140`
  - easy main `asdiv = 100`
- Tiny dev results with the initial palette:
  - `gsm8k_train`: `RAW_PYTHON = 0.75`, `OPERATOR_SCHEMA_TO_CODE = 0.6667`, `OSCAR_TEMPLATE_COMPILE = 0.6667`, `OSCAR_CONSTRAINED_COMPILE = 0.6667`
  - `asdiv`: `RAW_PYTHON = 1.0`, `OPERATOR_SCHEMA_TO_CODE = 1.0`, `OSCAR_TEMPLATE_COMPILE = 1.0`, `OSCAR_CONSTRAINED_COMPILE = 0.9167`
  - parse stability was clean enough to freeze prompts
- Initial calibration + offline:
  - hard `gsm8k_train`:
    - `RAW_PYTHON = 0.7000`
    - `OPERATOR_SCHEMA_TO_CODE = 0.7067`
    - `OSCAR_TEMPLATE_COMPILE = 0.4933`
    - `OSCAR_CONSTRAINED_COMPILE = 0.5867`
  - easy `asdiv`:
    - `RAW_PYTHON = 0.7444`
    - `OPERATOR_SCHEMA_TO_CODE = 0.7667`
    - `OSCAR_TEMPLATE_COMPILE = 0.5667`
    - `OSCAR_CONSTRAINED_COMPILE = 0.5889`
  - interpretation:
    - `OSCAR_CONSTRAINED_COMPILE` was clearly the weakest serious structured alternative
    - this triggered the predeclared Pivot A
- Pivot A:
  - replaced `OSCAR_CONSTRAINED_COMPILE` with `NORMALIZED_QUESTION_TO_CODE`
  - reran full calibration on the same fresh IDs
- Pivot A offline result:
  - hard `gsm8k_train`:
    - `NORMALIZED_QUESTION_TO_CODE = 0.7533`
    - `OPERATOR_SCHEMA_TO_CODE = 0.7067`
    - `RAW_PYTHON = 0.7000`
  - easy `asdiv`:
    - `NORMALIZED_QUESTION_TO_CODE = 0.7778`
    - `OPERATOR_SCHEMA_TO_CODE = 0.7667`
    - `RAW_PYTHON = 0.7444`
  - `best_fixed_hard = NORMALIZED_QUESTION_TO_CODE`
  - `best_fixed_balanced = NORMALIZED_QUESTION_TO_CODE`
- Pivot B:
  - reran the conditioning subset with `problem_only + use_normalized_replacement`
  - result:
    - `problem + draft` helped all serious interfaces, including `NORMALIZED_QUESTION_TO_CODE`
    - `gsm8k_train`: normalized `0.6667 -> 0.7500`
    - `asdiv`: normalized `0.6250 -> 0.8000`
  - main was therefore frozen to `problem + draft`
- Fresh held-out main with the pivot palette:
  - hard cluster surface `gsm8k_train = 200`
  - hard generic surface `gsm8k_train = 140`
  - easy surface `asdiv = 100`
- Final OSCAR held-out result:
  - hard cluster:
    - `OPERATOR_SCHEMA_TO_CODE = 0.7150`
    - `RAW_PYTHON = 0.6950`
    - `NORMALIZED_QUESTION_TO_CODE = 0.6600`
    - `OSCAR_TEMPLATE_COMPILE = 0.4600`
  - hard generic:
    - `RAW_PYTHON = 0.7429`
    - `OPERATOR_SCHEMA_TO_CODE = 0.7143`
    - `NORMALIZED_QUESTION_TO_CODE = 0.6429`
    - `OSCAR_TEMPLATE_COMPILE = 0.4429`
  - easy:
    - `KEEP = 0.8600`
    - `RAW_PYTHON = 0.9700`
    - `OPERATOR_SCHEMA_TO_CODE = 0.9900`
    - `NORMALIZED_QUESTION_TO_CODE = 0.9900`
- Mixed-workload frontier:
  - `25/75` hard/easy: `OPERATOR_SCHEMA_TO_CODE = 0.9211` vs `RAW_PYTHON = 0.9132`
  - `50/50` and `75/25`: `RAW_PYTHON` remained strongest
- Final OSCAR artifact bundle:
  - reports: `reports/oscar_*`
  - tables: `tables/oscar`
  - figures: `figures/oscar`
  - updated project synthesis: `reports/final_integrated_project_report_oscar.md`

### ATLAS branch kickoff

### Objective

Start `ATLAS` (`Audited Typed Layout for Arithmetic Schemas`) as a schema-quality branch after freezing all prior branches through OSCAR.

The motivating diagnosis after TIER and OSCAR is:

- the remaining hard-arithmetic bottleneck is semantic-to-executable interface quality
- the strongest frontier signal is still the simple fixed structured interface, especially `OPERATOR_SCHEMA_TO_CODE`
- richer routers and richer compiler families did not survive held-out evaluation robustly
- therefore the next justified target is schema extraction quality itself

### Branch framing

- This is not a routing branch.
- This is not another confidence or verifier branch.
- This is not another ambitious compiler-family branch.
- The main question is whether a small audited schema seed plus cluster-aware local extraction can improve the fixed operator-schema interface enough to beat `RAW_PYTHON` on the hard operator/discretization clusters.

### Literature guardrails for ATLAS

- `Strategy Executability in Mathematical Reasoning`
  - relevant strategy does not imply executable strategy
- `Plan before Solving`
  - decomposition is useful, but routing is no longer the main abstraction here
- `Formula-One Prompting`
  - operator/equation formalization helps because it improves executable interface quality
- `Can LLMs Reason Abstractly Over Math Word Problems Without CoT?`
  - formulation and arithmetic execution should be disentangled
- `NeuroProlog`
  - typed intermediate representations are useful, but this branch should stay lightweight and local-first
- `Solving Math Word Problems by Combining Language Models With Symbolic Solvers`
  - executable backends help only when the semantic interface is correct
- `Mapping to Declarative Knowledge for Word Problem Solving`
  - quantity roles / entities and typed relations matter for hard MWPs

### Runtime estimate

- API teacher schema phase: `20–40 minutes` if used
- local calibration bank: `2–3 hours`
- offline study + ablations: `30–60 minutes`
- fresh held-out main: `2–3 hours`
- total expected end-to-end: `5–8 hours`
- if one pivot is exercised: `7–10 hours`

Current environment note:

- `OPENAI_API_KEY` is unset, so the optional API teacher phase is skipped by default.
- The teacher-seed fallback is:
  - local `Qwen/Qwen2.5-7B-Instruct` schema extraction
  - deterministic audit / filtering
  - frozen retrieval memory used only for supervision / upper-bound diagnosis

### Immediate implementation priorities

1. Build ATLAS manifests with fresh hard/easy splits and a teacher-seed split
2. Implement retrieval-conditioned and field-wise schema extraction on top of the existing `tier_operator_action` backend
3. Measure local-vs-teacher field gaps before large held-out collection
4. Compare `RAW_PYTHON` vs baseline operator schema vs ATLAS methods on a calibration bank

### ATLAS execution

- Generated fresh ATLAS manifests under `data/atlas_manifests_20260313`:
  - teacher seed hard `72`
  - hard calibration `gsm8k_train = 160`
  - easy calibration `asdiv = 80`
  - conditioning subsets `gsm8k_train = 60`, `asdiv = 40`
  - hard cluster main `gsm8k_train = 200`
  - hard generic main `gsm8k_train = 140`
  - easy main `asdiv = 80`
- Teacher seed construction:
  - optional API teacher phase remained skipped
  - local audited seed was built from `Qwen/Qwen2.5-7B-Instruct`
  - merged kept seed size: `37`
  - all pre-registered hard clusters remained represented, though unevenly
- Offline calibration, global retrieval mode:
  - hard `gsm8k_train`
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.78125`
    - `ATLAS_RETRIEVAL_SCHEMA_TO_CODE = 0.74375`
    - `ATLAS_FIELDWISE_SCHEMA_TO_CODE = 0.74375`
    - `RAW_PYTHON = 0.72500`
  - easy `asdiv`
    - `ATLAS_RETRIEVAL_SCHEMA_TO_CODE = 0.9500`
    - `ATLAS_FIELDWISE_SCHEMA_TO_CODE = 0.9250`
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.9125`
    - `RAW_PYTHON = 0.9000`
- Conditioning comparison:
  - `problem + draft` beat `problem only` for every serious schema method
  - hard retrieval `0.6500 -> 0.8000`
  - hard fieldwise `0.6333 -> 0.7500`
  - hard baseline operator schema `0.6667 -> 0.8167`
- Pivot A, cluster-first retrieval:
  - exercised exactly as predeclared
  - negative on hard calibration: retrieval dropped to `0.7125`
  - rejected in favor of global retrieval
- Pivot B:
  - field-wise decomposition was already part of the initial ATLAS palette
  - no extra branch rerun was needed
- Pivot C, critical-field repair:
  - hard calibration `0.74375`
  - matched retrieval / fieldwise accuracy
  - reduced latency materially
  - still did not beat `OPERATOR_SCHEMA_TO_CODE_BASE`
- Teacher-gap analysis:
  - local ATLAS extractors improved `operator_family`, `target_type`, and `discretization_flags` relative to the baseline extractor
  - `quantity_role_match` remained the main weak field
  - because the teacher seed was a small local audited memory, this analysis should be read as a schema-gap diagnostic, not a clean stronger-teacher upper bound
- Fresh held-out ATLAS main:
  - cluster-focused hard `gsm8k_train = 200`
    - `ATLAS_RETRIEVAL_SCHEMA_TO_CODE = 0.815`
    - `ATLAS_FIELDWISE_SCHEMA_TO_CODE = 0.810`
    - `ATLAS_CRITICAL_FIELD_REPAIR = 0.810`
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.800`
    - `RAW_PYTHON = 0.770`
  - generic hard `gsm8k_train = 140`
    - `ATLAS_FIELDWISE_SCHEMA_TO_CODE = 0.792857`
    - `RAW_PYTHON = 0.785714`
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.778571`
    - `ATLAS_RETRIEVAL_SCHEMA_TO_CODE = 0.771429`
    - `ATLAS_CRITICAL_FIELD_REPAIR = 0.771429`
- Pairwise held-out note:
  - cluster-focused hard:
    - `RAW_PYTHON -> ATLAS_FIELDWISE_SCHEMA_TO_CODE` delta `+0.0401`, CI `[0.005, 0.08]`
    - retrieval had the best point estimate, but the cleanest pairwise interval over raw came from fieldwise
- Cluster-conditioned held-out interpretation:
  - retrieval / repair improved over the baseline operator schema on:
    - `average_repeated_times`
    - `geometry_formula_family`
    - `percent_fraction_complement`
    - `comparison_leftover_more`
  - the baseline operator schema remained stronger on:
    - `direct_exact_arithmetic`
  - and remained at least as strong on:
    - `ratio_proportion_rate`
    - `remainder_packaging_divisibility`
- Final ATLAS posture:
  - targeted cluster-aware schema extraction improves the operator-schema interface enough to beat `RAW_PYTHON` on the pre-registered hard operator/discretization subset
  - it does not support a universal hard-set dominance claim over generic arithmetic

### ATLAS API teacher follow-up

- Date: `2026-03-14`
- The previously skipped bounded API teacher phase was run after `OPENAI_API_KEY` became available via `.env.example`.
- Code changes required before the run:
  - added `generate_text(...)` to `OpenAIResponsesClient`
  - updated `scripts/atlas_build_teacher_seed.py` to accept `--client openai`
  - switched the teacher build script to the ATLAS teacher prompt instead of the OSCAR probe prompt
  - recorded token/cost/latency metadata in teacher-seed outputs
- API teacher seed run:
  - manifest: `data/atlas_manifests_20260313/gsm8k_train_teacher_seed.json`
  - model: `gpt-5-mini`
  - candidates: `72`
  - kept: `32`
  - total cost: `$0.03797075`
- Relative to the frozen local audited seed:
  - local kept: `37`
  - overlap: `25`
  - local-only: `12`
  - API-only: `7`
- API teacher-gap diagnosis against the existing local teacher-eval raw records:
  - `OPERATOR_SCHEMA_TO_CODE_BASE`
    - operator `0.000`
    - target `0.300`
    - discretization `0.062`
    - quantity-role `0.000`
  - `ATLAS_RETRIEVAL_SCHEMA_TO_CODE`
    - operator `0.498`
    - target `0.635`
    - discretization `0.269`
    - quantity-role `0.000`
  - `ATLAS_FIELDWISE_SCHEMA_TO_CODE`
    - operator `0.544`
    - target `0.531`
    - discretization `0.362`
    - quantity-role `0.000`
- Interpretation:
  - the stronger teacher phase reinforced the same diagnosis as the local seed:
    - ATLAS improves critical semantic fields relative to the baseline operator-schema extractor
    - `quantity_role_match` remains the weakest field
- Bounded local follow-up:
  - selected the `46` cluster-main examples where frozen `RAW_PYTHON` had been wrong
  - reran local ATLAS with the API teacher seed as retrieval memory
  - results:
    - `RAW_PYTHON`: `0.0000 -> 0.4130`
    - `OPERATOR_SCHEMA_TO_CODE_BASE`: `0.4130 -> 0.5435`
    - `ATLAS_RETRIEVAL_SCHEMA_TO_CODE`: `0.3696 -> 0.4565`
    - `ATLAS_FIELDWISE_SCHEMA_TO_CODE`: `0.2609 -> 0.3043`
    - `ATLAS_CRITICAL_FIELD_REPAIR`: `0.3478 -> 0.4565`
  - because non-retrieval methods also moved strongly, this bounded rerun is diagnostic rather than a clean causal estimate of API-seed benefit alone
- Final API-phase reading:
  - API teacher supervision strengthened the schema-quality bottleneck diagnosis
  - it did not justify rewriting the frozen ATLAS main claim around an API-seed-driven accuracy jump

### ATLAS-RG kickoff

- Date: `2026-03-14`
- Branch framing:
  - not another router
  - not another confidence or verifier branch
  - not another broad compiler branch
  - the current target is quantity-role grounding quality inside the fixed operator-schema interface
- Frozen diagnosis from ATLAS:
  - cluster-aware schema extraction beat `RAW_PYTHON` on the targeted hard subset
  - generic-hard was near-tie
  - API teacher follow-up reinforced that `quantity_role_match` remained the weakest field
- Pre-registered ATLAS-RG hypothesis:
  - quantity-role / target-binding errors are the main remaining bottleneck
  - role-only repair should explain more of the teacher gap than non-role-only repair on the target hard clusters
- Literature guardrails for ATLAS-RG:
  - `Strategy Executability in Mathematical Reasoning`
    - executable strategy is the relevant object, not just semantic relevance
  - `Plan before Solving`
    - decomposition is useful, but routing is no longer the main abstraction here
  - `Formula-One Prompting`
    - structured intermediate representations help because they improve executable interfaces
  - `Can LLMs Reason Abstractly Over Math Word Problems Without CoT?`
    - formulation and arithmetic execution should stay disentangled
  - `NeuroProlog`
    - typed executable intermediates help, but this branch stays lightweight and local-first
  - `Solving Math Word Problems by Combining Language Models With Symbolic Solvers`
    - symbolic execution only helps if the formulation fields are right
  - `Mapping to Declarative Knowledge for Word Problem Solving`
    - quantity roles and typed relations matter for hard MWPs
  - `SBI-RAG`
    - bounded retrieval can help schema extraction, but this branch should stay narrow and field-causal
- Initial runtime estimate before heavy runs:
  - API teacher role phase: `30–60 minutes`
  - local dev/stability: `20–40 minutes`
  - calibration bank: `2.5–3.5 hours`
  - offline field-causal study: `45–75 minutes`
  - fresh held-out main: `2.5–4 hours`
  - total expected end-to-end: `6–9 hours`
  - with one pivot: `8–11 hours`
- GPU plan:
  - use all `4` GPUs
  - one generator worker per GPU
  - `4bit` local inference by default
  - log `nvidia-smi dmon` snapshots early and mid-run
  - stop and fix the runner if utilization stays below `75%` for too long

### ATLAS-RG runtime / utilization update

- The initial `4bit` hard-calibration launch underused the GPUs and was stopped.
- The active path switched to:
  - `fp16`
  - one visible GPU per worker
  - 4 shard manifests
  - asynchronous CPU-side execution / file writes overlapped with sharded generation
- Hard calibration result:
  - `160` fresh hard examples
  - completed in roughly `25–27 minutes`
  - sustained `nvidia-smi dmon` utilization was mostly `sm ~94–96%`
- Runtime estimate revised from the initial conservative plan:
  - teacher-covered eval: `40–50 minutes`
  - hard conditioning pair: `25–35 minutes`
  - easy calibration + easy conditioning: `20–30 minutes`
  - fresh held-out main: `60–90 minutes`
  - replay-controlled seed comparison: `20–30 minutes`
  - remaining branch wall-clock after hard calibration: `~4–5 hours`

### ATLAS-RG completion

- API teacher role phases:
  - initial teacher seed: `78` candidates, `34` kept, `gpt-5-mini`, cost `$0.046593`
  - held-out teacher subset: `59` candidates, `27` kept, `gpt-5-mini`, cost `$0.035326`
  - total API spend for ATLAS-RG: `$0.081919`
- Actual experimental wall-clock:
  - first merged API teacher manifest at `2026-03-14T03:06:00+00:00`
  - final replay summary manifest at `2026-03-14T06:11:42+00:00`
  - heavy-run experimental window was about `3h05m`, materially below the initial `6–9h` estimate after switching to the `fp16` 4-worker path
- Utilization logs:
  - hard calibration: `/workspace/project/results/atlas_rg_calibration/logs/calibration_fp16_orch_dmon_20260314.log`
  - easy calibration: `/workspace/project/results/atlas_rg_calibration/logs/easy_cal_dmon_20260314.log`
  - held-out main: `/workspace/project/results/atlas_rg_main/logs/main_api_seed_dmon_20260314.log`
  - replay / teacher-covered: `/workspace/project/results/atlas_rg_main/logs/replay_teacher_dmon_20260314.log`
- Active-window GPU utilization from `nvidia-smi dmon`:
  - hard calibration active `sm` average: about `84.7`
  - easy calibration active `sm` average: about `91.1`
  - held-out main active `sm` average: about `91.7`
  - replay / teacher-covered active `sm` average: about `93.4`
- Final held-out results:
  - cluster-focused hard `gsm8k_train`:
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.779412`
    - `ATLAS_RG_CRITICAL_ROLE_REPAIR = 0.759804`
    - `ATLAS_RG_ROLETABLE_TO_CODE = 0.750000`
    - `ATLAS_FIELDWISE_SCHEMA_TO_CODE = 0.740196`
    - `RAW_PYTHON = 0.730392`
    - `ATLAS_RG_ROLE_REPAIR_ONLY = 0.730392`
    - `ATLAS_RG_NONROLE_REPAIR_ONLY = 0.720588`
  - generic hard `gsm8k_train`:
    - `RAW_PYTHON = 0.821429`
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.821429`
    - best ATLAS-RG variants reached `0.814286`
- Replay-controlled seed comparison on identical frozen drafts:
  - `ATLAS_RG_ROLETABLE_TO_CODE`: local seed `0.715686` -> API seed `0.750000`
  - `ATLAS_FIELDWISE_SCHEMA_TO_CODE`: local seed `0.740196` -> API seed `0.740196`
- Held-out teacher-covered diagnostic:
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.925926`
  - `TEACHER_ROLETABLE_TO_CODE = 0.777778`
  - the teacher upper bound did not exceed the simpler operator-schema baseline
- Final reading:
  - quantity-role grounding is a real field-causal bottleneck
  - teacher-audited seed quality specifically helps the role-grounded roletable path under replay control
  - but the robust hard-set frontier still belongs to `OPERATOR_SCHEMA_TO_CODE_BASE`, not the full ATLAS-RG family

### ATLAS-MS kickoff

- New branch: `ATLAS-MS` (`ATLAS for Minimal Sufficient Schemas`)
- Frozen diagnosis carried forward:
  - ATLAS cluster-aware schema extraction beat `RAW_PYTHON` on targeted hard clusters
  - ATLAS-RG showed role grounding is causal, but role-only repair did not displace `OPERATOR_SCHEMA_TO_CODE_BASE`
  - the remaining bottleneck is likely an interacting field bundle rather than a single field
- Branch hypothesis:
  - `G1` operator/discretization + `G2` target/postprocess + `G3` quantity-role grounding should be analyzed as interacting bundles
  - the main question is whether a minimal sufficient bundle can beat the fixed baseline operator schema interface on the targeted hard clusters
- Literature guardrails checked for plan registration:
  - `Strategy Executability in Mathematical Reasoning`
  - `Plan before Solving`
  - `Formula-One Prompting`
  - `Can LLMs Reason Abstractly Over Math Word Problems Without CoT?`
  - `NeuroProlog`
  - `Solving Math Word Problems by Combining Language Models With Symbolic Solvers`
- Initial runtime estimate before heavy runs:
  - API teacher seed / field audit: `30–60 minutes`
  - local dev/stability: `20–40 minutes`
  - calibration bank: `3–4 hours`
  - offline bundle study: `45–75 minutes`
  - fresh held-out main: `3–4 hours`
  - total expected end-to-end: `7–10 hours`
  - with one pivot: `9–12 hours`
- Operational plan for minimizing runtime:
  - use all `4` GPUs
  - `fp16`
  - one generator worker per GPU
  - pre-sharded manifests
  - overlap CPU parse / execution / writes with generation
  - log `nvidia-smi dmon` early and mid-run

### ATLAS-MS completion

- API teacher full-bundle phases:
  - initial teacher seed: `75` candidates, `41` kept, `gpt-5-mini`, cost `$0.044565`
  - held-out teacher subset: `40` candidates, `23` kept, `gpt-5-mini`, cost `$0.023503`
  - total API spend for ATLAS-MS: `$0.068068`
- Main measured collection / aggregation windows:
  - main API-seed held-out collection: `5292s` (`88.2m`)
  - replay local-seed collection: `1370s` (`22.8m`)
  - held-out teacher eval: `357s` (`6.0m`)
  - conditioning problem-only subset: `428s` (`7.1m`)
  - Pivot A hard calibration global retrieval: `896s` (`14.9m`)
  - Pivot A cluster-main global retrieval: `1635s` (`27.3m`)
  - Pivot B hard calibration field-wise compose: `270s` (`4.5m`)
  - Pivot B held-out main field-wise compose: `462s` (`7.7m`)
  - Pivot B replay API field-wise compose: `245s` (`4.1m`)
  - Pivot B replay local field-wise compose: `196s` (`3.3m`)
- GPU utilization evidence:
  - the major ATLAS-MS collection phases stayed on the `fp16`, one-worker-per-GPU path
  - active-window compose-phase `sm` averages from `nvidia-smi dmon` were about:
    - main field-wise compose: `92.7`
    - replay API field-wise compose: `88.7`
    - replay local field-wise compose: `86.5`
  - during live snapshots, all four GPUs repeatedly stayed in the `90%+` band during generation windows
- Final ATLAS-MS held-out results:
  - cluster-focused hard `gsm8k_train`:
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.794118`
    - best bundle method `MS_FULL_BUNDLE = 0.759804`
    - next-best bundle methods `MS_OPERATOR_PLUS_TARGET_FIELDWISE = 0.754902`, `MS_TARGET_POSTPROCESS_ONLY = 0.754902`
    - `RAW_PYTHON = 0.730392`
  - generic hard `gsm8k_train`:
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.864286`
    - best bundle methods `MS_ROLE_ONLY = 0.850000`, `MS_MINIMAL_CLUSTER_BUNDLE = 0.850000`
    - `RAW_PYTHON = 0.792857`
- Replay-controlled seed comparison on identical frozen cluster-hard drafts:
  - API teacher seed did not improve the bundle path over the local seed
  - `MS_OPERATOR_PLUS_TARGET`: local `0.784314` vs API `0.750000`
  - `MS_FULL_BUNDLE`: local `0.779412` vs API `0.759804`
  - `MS_FULL_BUNDLE_FIELDWISE`: local `0.759804` vs API `0.710784`
- Final reading:
  - bundle interaction matters more than role-only repair
  - the recurring useful ingredient is target/postprocess handling
  - but the robust hard-set frontier still belongs to `OPERATOR_SCHEMA_TO_CODE_BASE`, not the ATLAS-MS bundle family

## 2026-03-15

### CASS kickoff

- New branch: `CASS` (`Conservative Arithmetic Schema Surgery`)
- Frozen diagnosis carried forward:
  - `ATLAS-MS` showed interacting fields matter, especially `G2` target/postprocess information
  - but no broad bundle displaced `OPERATOR_SCHEMA_TO_CODE_BASE`
  - stronger teacher seed alone did not close the gap
- New branch hypothesis:
  - broad replacement is now too destructive
  - the next test should preserve the frozen operator-schema baseline and patch only suspicious fields
  - the main repair surface is `target/postprocess + role`, not role-only
- Literature / guardrail scan for the plan:
  - `Strategy Executability in Mathematical Reasoning`
  - `Plan before Solving`
  - `Formula-One Prompting`
  - `Can LLMs Reason Abstractly Over Math Word Problems Without CoT?`
  - `NeuroProlog`
  - `ToolMATH`
  - `Solving Math Word Problems by Combining Language Models With Symbolic Solvers`
- Runtime estimate before heavy runs:
  - API teacher / field audit: `20–40 minutes`
  - local dev / stability: `20–30 minutes`
  - calibration bank: `2–3 hours`
  - offline patch study: `40–70 minutes`
  - fresh held-out main: `2–3 hours`
  - total expected end-to-end: `5–8 hours`
  - with one pivot: `7–10 hours`
- Runtime minimization plan:
  - use all `4` GPUs
  - `fp16`
  - one generator worker per GPU
  - shard manifests ahead of time
  - overlap CPU parse / execution / writes with generation
  - log `nvidia-smi dmon` during the first `15` minutes and near the midpoint of long phases

### CASS runtime smoke update

- Added `tests/test_cass_core.py`; `pytest -q tests/test_cass_core.py` passed: `5 passed, 2 warnings`
- Built fresh sharded manifests at `data/cass_manifests_20260315b`
  - teacher seed and teacher-heldout subsets are now also split into `4` shards so the API teacher phase can use all `4` GPUs
- Ran a local smoke at `results/cass_dev/smoke_runtime_20260315`
  - manifest: `gsm8k_train_calibration_smoke2.json`
  - model: `Qwen/Qwen2.5-7B-Instruct`
  - backend: `hf_local`, `fp16`, `CUDA_VISIBLE_DEVICES=0`
  - records: `2`
- Observed runtime from the smoke:
  - per-example summed local action latency: about `55.75s`, `42.43s`
  - mean: about `49s / example / GPU`
  - spot `nvidia-smi` during generation reached about `95–96%` utilization on the active GPU
- Revised wall-clock estimate from the smoke:
  - API teacher seed `75` examples with `4` shards: about `22–25 minutes`
  - hard calibration `180` examples with `4` shards: about `42–47 minutes`
  - easy calibration `70` examples with `4` shards: about `18–22 minutes`
  - cluster-hard main `210` examples with `4` shards: about `48–55 minutes`
  - generic-hard main `140` examples with `4` shards: about `34–40 minutes`
  - replay / teacher-covered follow-up: about `30–45 minutes`
  - revised end-to-end expectation without a pivot: about `4.5–5.5 hours`

### CASS API teacher seed build

- Used the re-sharded manifest set at `data/cass_manifests_20260315b`
- Parallelized the teacher seed over `4` GPUs / `4` shards
- Merged seed directory:
  - `results/cass_api_diag/teacher_seed_gpt5mini_20260315_merged`
- Final teacher-seed manifest:
  - candidate count: `75`
  - kept count: `75`
  - API model: `gpt-5-mini`
  - local model: `Qwen/Qwen2.5-7B-Instruct`
  - total input tokens: `46835`
  - total output tokens: `15532`
  - total cost: `$0.042773`
- Cluster coverage after merge:
  - `average_repeated_times`: `15`
  - `ceil_floor_partial_group`: `15`
  - `comparison_leftover_more`: `15`
  - `percent_fraction_complement`: `15`
  - `remainder_packaging_divisibility`: `15`
- Immediate operational note:
  - the `4`-shard teacher phase avoided the single-GPU bottleneck from the original conservative estimate
  - this keeps the branch on track for the revised `4.5–5.5h` end-to-end window

### CASS hard calibration start

- Started `gsm8k_train` hard calibration on `4` GPUs with:
  - `Qwen/Qwen2.5-7B-Instruct`
  - `hf_local`
  - `fp16`
  - `cluster_first` retrieval
  - merged API teacher seed retrieval memory
- Early utilization snapshots during steady-state generation reached roughly:
  - `gpu0=78%`
  - `gpu1=96%`
  - `gpu2=96%`
  - `gpu3=97%`
- Logged `nvidia-smi dmon` early and mid calibration windows at:
  - `results/cass_calibration/calibration_clusterfirst_20260315_hard_dmon_early.txt`
  - `results/cass_calibration/calibration_clusterfirst_20260315_hard_dmon_mid.txt`

### CASS frozen patch audit registration

- Pre-registered hard clusters:
  - `percent_fraction_complement`
  - `average_repeated_times`
  - `geometry_formula_family`
  - `comparison_leftover_more`
  - `ceil_floor_partial_group`
  - `remainder_packaging_divisibility`
- Key frozen evidence:
  - `ATLAS-MS` cluster-hard by cluster showed `G2` target/postprocess information repeatedly helping in `comparison_leftover_more`, `remainder_packaging_divisibility`, and `ceil_floor_partial_group`
  - `ATLAS-RG` and `ATLAS-MS` failure notes repeatedly highlighted:
    - wrong target binding
    - wrong postprocess handling
    - wrong discretization flag
    - wrong quantity role
    - wrong base/delta
    - wrong per-item vs total assignment
- Working interpretation:
  - the remaining bottleneck looks like conservative field surgery on top of a strong sparse baseline, not another full schema branch

### CASS completion

- Completed the bounded API teacher field-audit phase with `gpt-5-mini`.
- Teacher-seed outputs:
  - merged seed dir: `results/cass_api_diag/teacher_seed_gpt5mini_20260315_merged`
  - candidate count: `75`
  - kept count: `75`
  - total API cost: `$0.042773`
- Held-out teacher-covered API subset:
  - merged seed dir: `results/cass_api_diag/heldout_teacher_subset_gpt5mini_20260315_merged`
  - candidate count: `40`
  - kept count: `40`
  - incremental API cost: `$0.022554`
- Total CASS API spend:
  - `$0.065327`
- Completed collection dirs:
  - hard calibration: `results/cass_calibration/calibration_clusterfirst_20260315_hard_shard01of04` ... `shard04of04`
  - easy calibration: `results/cass_calibration/calibration_clusterfirst_20260315_easy_shard01of04` ... `shard04of04`
  - offline aggregation: `results/cass_offline/offline_full_clusterfirst_20260315`
  - cluster-hard main: `results/cass_main/cluster_main_teacher_20260315_shard01of04` ... `shard04of04`
  - generic-hard main: `results/cass_main/generic_main_teacher_20260315_shard01of04` ... `shard04of04`
  - replay local cluster: `results/cass_main/replay_local_cluster_20260315_shard01of04` ... `shard04of04`
  - easy main: `results/cass_main/easy_main_teacher_20260315_shard01of04` ... `shard04of04`
  - final main aggregation: `results/cass_main/main_clusterfirst_20260315`
- Offline operating-point freeze:
  - best hard patch method: `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH`
  - best balanced patch method: `CASS_TARGET_POSTPROCESS_PATCH`
  - conservative gate enabled with:
    - `gate_patch_action = CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH`
    - `gate_threshold = 1`
- Fresh held-out cluster-hard main (`n=210`):
  - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH = 0.771429`
  - `CASS_CONSERVATIVE_GATE = 0.771429`
  - `CASS_TARGET_POSTPROCESS_PATCH = 0.752381`
  - `RAW_PYTHON = 0.738095`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.728571`
  - key deltas:
    - combined patch vs `RAW_PYTHON`: `+0.033086`
    - combined patch vs frozen baseline: `+0.042488`
- Fresh held-out generic-hard main (`n=140`):
  - `CASS_TARGET_POSTPROCESS_PATCH = 0.842857`
  - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH = 0.842857`
  - `CASS_CONSERVATIVE_GATE = 0.842857`
  - `RAW_PYTHON = 0.814286`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.778571`
  - key deltas:
    - target/postprocess patch vs `RAW_PYTHON`: `+0.027996`
    - combined patch vs frozen baseline: `+0.065082`
- Easy main (`asdiv`, `n=70`) stayed saturated:
  - `KEEP = 1.0`
  - all CASS patch methods = `1.0`
  - `RAW_PYTHON = 1.0`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 1.0`
- Replay-controlled seed comparison on identical cluster-hard drafts:
  - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH`:
    - fresh teacher-seeded = `0.771429`
    - frozen local no-seed replay = `0.742857`
  - `CASS_TARGET_POSTPROCESS_PATCH`:
    - fresh teacher-seeded = `0.752381`
    - frozen local no-seed replay = `0.733333`
- Held-out teacher-covered subset (`n=40`):
  - `TEACHER_PATCHED_BASELINE = 0.825`
  - `RAW_PYTHON = 0.775`
  - `CASS_ROLE_PATCH = 0.775`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.675`
- Runtime summary:
  - teacher-seed merged manifest timestamp: `2026-03-15T01:30:39Z`
  - offline full manifest timestamp: `2026-03-15T02:38:24Z`
  - final main manifest timestamp: `2026-03-15T04:38:29Z`
  - teacher seed -> final main wall-clock: about `3h08m`
  - offline -> final main wall-clock: about `2h00m`
- GPU utilization summary:
  - hard calibration steady-state `sm`:
    - `gpu0 ~76–77`
    - `gpu1 ~96–98`
    - `gpu2 ~95–96`
    - `gpu3 ~96`
  - cluster-hard main steady-state `sm`:
    - `gpu0 ~90–96`
    - `gpu1 ~89–97`
    - `gpu2 ~95–100`
    - `gpu3 ~92–96`
- Strongest surviving CASS story:
  - conservative, baseline-preserving sparse patching finally turns the post-ATLAS signal into a held-out win over both `RAW_PYTHON` and `OPERATOR_SCHEMA_TO_CODE_BASE`
  - the recurring useful ingredient is `target/postprocess`; role-only patching remains weaker than the combined patch on cluster-hard

### CASS-R2 kickoff

- New phase: `CASS-R2`
- Scope:
  - bounded confirmation and direct-comparison phase only
  - not a new methods branch
- Frozen core story carried forward:
  - `CASS` is the strongest positive post-ATLAS result so far
  - but the current cluster-hard pairwise intervals are not yet statistically locked
- New questions:
  - can the CASS cluster-hard effect be locked at larger sample size?
  - can it compare favorably to the closest recent inference-time comparators on the same surfaces?
- Frozen methods to confirm:
  - `CASS_TARGET_POSTPROCESS_PATCH`
  - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH`
  - `CASS_CONSERVATIVE_GATE`
- Direct comparator targets:
  - `PRISM_LITE`
  - `F1_LITE`
  - `SSR_LITE` only if low-friction enough to stay faithful and bounded
- Initial runtime estimate before heavy runs:
  - dataset screening and setup: `30–60 minutes`
  - large-scale local main collection: `8–12 hours`
  - direct-baseline collection: `3–5 hours`
  - offline statistics and figures: `1–2 hours`
  - optional API micro-diagnostic: `30–60 minutes`
  - end-to-end total: `12–18 hours`
  - with stable throughput and an early sequential stop: `10–14 hours`
- Planned hardware policy:
  - `Qwen/Qwen2.5-7B-Instruct`
  - `hf_local`
  - `fp16`
  - `4` GPUs
  - one worker per GPU
  - `nvidia-smi dmon` early and mid logs during heavy phases

### CASS-R2 runtime revision after smoke

- The initial CASS-R2 runtime plan was materially too conservative.
- Local smoke used:
  - `Qwen/Qwen2.5-7B-Instruct`
  - `hf_local`
  - `fp16`
  - frozen CASS-R2 internal method matrix
- Observed action-latency totals on the `2`-example smoke:
  - example `gsm8k_train_2955`: `29.292s`
  - example `gsm8k_train_2956`: `26.387s`
  - mean: about `27.8s/example/GPU`
- Derived wall-clock implications at `4` GPUs:
  - `500` cluster-hard examples: about `58 minutes` before modest overhead
  - `300` generic-hard examples: about `35 minutes` before modest overhead
- Runtime estimate revised because the first-hour projection deviated from the kickoff estimate by well over `25%`:
  - setup + headroom screen: `20–30 minutes`
  - main local collection: `1.5–2.0 hours`
  - direct comparator collection: `1.0–1.5 hours`
  - statistics + figures + report assembly: `30–45 minutes`
  - optional screened transfer: `15–25 minutes`
  - end-to-end total under the observed path: `3–5 hours`

### CASS-R2 headroom screen outcome

- Completed the bounded transfer headroom screen on:
  - `mawps` cluster-hard screen (`n=60`)
  - `asdiv` cluster-hard screen (`n=36`)
- Registered inclusion rule:
  - include only if `KEEP <= 0.55`
  - and best schema path exceeds `KEEP` by at least `0.10`
  - and best schema path exceeds `RAW_PYTHON` by at least `0.02`
- Outcome:
  - `mawps`: excluded
    - `KEEP = 0.0167`
    - `RAW_PYTHON = 0.0167`
    - best schema path `OPERATOR_SCHEMA_TO_CODE_BASE = 0.0500`
    - too little aligned headroom and too little useful transfer room
  - `asdiv`: excluded
    - `KEEP = 0.5278`
    - `RAW_PYTHON = 0.8333`
    - best schema path `0.8333`
    - meaningful headroom over `KEEP`, but no schema edge over `RAW_PYTHON`
- Decision:
  - do not add a transfer suite
  - keep the primary confirmation surfaces exactly on fresh GSM8K:
    - `500` cluster-hard
    - `300` generic-hard

### CASS-R2 final confirmation outcome

- Completed the full registered confirmation path:
  - base replay-controlled main sweep:
    - `500` cluster-hard
    - `300` generic-hard
  - sequential extension because the cluster-hard `vs OPERATOR_SCHEMA_TO_CODE_BASE` lower bound still touched zero at `n=500`
  - final primary surfaces:
    - `800` cluster-hard
    - `300` generic-hard
- Final aggregate outputs:
  - `results/cass_r2_main/main_20260315a`
  - `results/cass_r2_comparators/comparator_pack_20260315a`
  - reports:
    - `reports/cass_r2_main_report.md`
    - `reports/cass_r2_comparator_report.md`
    - `reports/cass_r2_failure_notes.md`
    - `reports/cass_r2_final_lock_memo.md`
- Final cluster-hard (`n=800`) summary:
  - `CASS_CONSERVATIVE_GATE = 0.74875`
  - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH = 0.74875`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.73000`
  - `RAW_PYTHON = 0.69750`
  - `PRISM_LITE = 0.69750`
  - `F1_LITE = 0.61750`
- Final generic-hard (`n=300`) summary:
  - `CASS_CONSERVATIVE_GATE = 0.78333`
  - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH = 0.78333`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.73667`
  - `RAW_PYTHON = 0.71667`
  - `PRISM_LITE = 0.71667`
  - `F1_LITE = 0.63333`
- Final registered pairwise reads:
  - cluster-hard:
    - `CASS_CONSERVATIVE_GATE - RAW_PYTHON = +0.0509`, `95% CI [0.0225, 0.0800]`
    - `CASS_CONSERVATIVE_GATE - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0186`, `95% CI [-0.0075, 0.0463]`
    - `CASS_CONSERVATIVE_GATE - PRISM_LITE = +0.0509`, `95% CI [0.0213, 0.0800]`
    - `CASS_CONSERVATIVE_GATE - F1_LITE = +0.1313`, `95% CI [0.0938, 0.1713]`
  - generic-hard:
    - `CASS_CONSERVATIVE_GATE - RAW_PYTHON = +0.0668`, `95% CI [0.0233, 0.1167]`
    - `CASS_CONSERVATIVE_GATE - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0469`, `95% CI [0.0033, 0.0900]`
- Sequential stopping outcome:
  - the cluster-hard lower bound versus `RAW_PYTHON` became positive early and stayed positive
  - the cluster-hard lower bound versus `OPERATOR_SCHEMA_TO_CODE_BASE` remained slightly below zero through `n=800`
  - therefore the primary preregistered success criterion did not lock
- Interpretation:
  - the CASS effect is real and stable versus `RAW_PYTHON`
  - it also compares favorably to the closest direct inference-time comparators collected here (`PRISM_LITE`, `F1_LITE`)
  - but it is still not statistically locked against the frozen operator-schema baseline on the primary cluster-hard surface
- Compute / runtime notes:
  - no new API phase was needed in `CASS-R2`
  - observed `nvidia-smi dmon` nonzero-window `sm` mean:
    - base `500+300` phase: `91.06`
    - cluster extension phase: `93.00`
  - per-GPU nonzero-window `sm` means:
    - base phase: `gpu0 95.26`, `gpu1 95.24`, `gpu2 79.28`, `gpu3 94.47`
    - extension phase: `gpu0 94.93`, `gpu1 95.00`, `gpu2 87.59`, `gpu3 94.52`
  - the kickoff estimate (`12–18h`) remained conservative; the executed local collection path stayed much closer to the revised `3–5h` regime

### CASS-R3 kickoff

- New phase: `CASS-R3`
- Scope:
  - bounded lock-and-compare continuation for frozen `CASS`
  - not a new methods branch
- Registered initial runtime estimate before heavy runs:
  - comparator audit + power plan: `30–60 minutes`
  - dataset headroom / expansion screen: `30–60 minutes`
  - large-scale local confirmation run: `8–12 hours`
  - direct comparator runs: `3–5 hours`
  - offline statistics / figures / memo: `1–2 hours`
  - optional API diagnostic: `30–60 minutes`
  - end-to-end total: `12–18 hours`
  - with sequential stopping and stable throughput: `10–14 hours`
- Practical feasibility read before collection:
  - fresh `gsm8k_train` cluster-hard remainder: `715`
  - fresh `gsm8k_train` generic-hard remainder: `183`
  - combined totals with `CASS-R2`:
    - cluster-hard: `1515`
    - generic-hard: `483`
- Immediate implication:
  - the requested `1600–1800` cluster-hard target is not reachable with fresh GSM8K alone
  - `CASS-R3` must therefore run to fresh GSM8K exhaustion unless a screened transfer suite proves both aligned and useful
- Comparator audit update:
  - direct comparators remain `PRISM` and `Formula-One Prompting`
  - both will remain explicitly labeled as `method-faithful local approximations`
  - updated official PRISM repo reference observed during this audit:
    - `https://github.com/reml-group/PRISM`
- Power update from `CASS-R2`:
  - `CASS_CONSERVATIVE_GATE` vs `RAW_PYTHON`
    - already comfortably feasible to lock
    - required total `n ~= 262`
  - `CASS_CONSERVATIVE_GATE` vs `OPERATOR_SCHEMA_TO_CODE_BASE`
    - estimated required total `n ~= 1755`
    - this exceeds the fresh-GSM-only feasible total `1515`
  - therefore `CASS-R3` is genuinely a lock attempt under bounded data exhaustion, not a guaranteed lock phase

### CASS-R3 runtime revision after first-hour trajectory

- The registered `12–18h` bound is again materially too conservative for the observed local path.
- Headroom screen actual path:
  - `mawps` target-cluster screen: `216` examples
  - `asdiv` target-cluster screen: `14` examples
  - outcome:
    - `mawps`: excluded
    - `asdiv`: excluded
    - `svamp`: no fresh examples
    - `multiarith`: no fresh examples
- Main fresh confirmation sweep:
  - combined fresh manifest size: `898`
    - cluster-hard remainder: `715`
    - generic-hard remainder: `183`
  - first-hour trajectory stabilized around:
    - about `346 / 898` examples completed
    - extrapolated wall-clock about `2.2–2.5 hours`
  - early `nvidia-smi dmon` nonzero-window `sm` mean: about `94.17`
- Runtime note revised after the first-hour deviation clearly exceeded `25%`:
  - comparator audit + power + manifest setup: `20–35 minutes`
  - bounded headroom screen: `25–35 minutes`
  - fresh main sweep: `2.2–2.5 hours`
  - aggregation + reports + figures + memo: `45–75 minutes`
  - total expected end-to-end under the observed path: about `4–5.5 hours`

### CASS-R3 final lock outcome

- Final frozen-result directories:
  - `results/cass_r3_main/main_20260315a`
  - `results/cass_r3_comparators/comparator_pack_20260315a`
- Final reports:
  - `reports/cass_r3_main_report.md`
  - `reports/cass_r3_comparator_report.md`
  - `reports/cass_r3_failure_notes.md`
  - `reports/cass_r3_final_lock_memo.md`
- Final surface sizes:
  - cluster-hard primary: `n = 1515`
  - generic-hard secondary: `n = 483`
- Final cluster-hard accuracies:
  - `CASS_CONSERVATIVE_GATE = 0.746535`
  - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH = 0.746535`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.726073`
  - `RAW_PYTHON = 0.704950`
  - `PRISM_LITE = 0.704950`
  - `F1_LITE = 0.603300`
- Final generic-hard accuracies:
  - `CASS_CONSERVATIVE_GATE = 0.797101`
  - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH = 0.797101`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.751553`
  - `RAW_PYTHON = 0.734990`
  - `PRISM_LITE = 0.734990`
  - `F1_LITE = 0.654244`
- Final registered pairwise reads:
  - cluster-hard:
    - `CASS_CONSERVATIVE_GATE - RAW_PYTHON = +0.0416`, `95% CI [0.0205, 0.0634]`
    - `CASS_CONSERVATIVE_GATE - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0207`, `95% CI [0.0007, 0.0422]`
    - `CASS_CONSERVATIVE_GATE - PRISM_LITE = +0.0416`, `95% CI [0.0205, 0.0634]`
    - `CASS_CONSERVATIVE_GATE - F1_LITE = +0.1434`, `95% CI [0.1135, 0.1716]`
  - generic-hard:
    - `CASS_CONSERVATIVE_GATE - RAW_PYTHON = +0.0622`, `95% CI [0.0269, 0.0994]`
    - `CASS_CONSERVATIVE_GATE - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0459`, `95% CI [0.0124, 0.0807]`
- Sequential stopping outcome:
  - the preregistered cluster-hard lock condition first turned on at `n = 1000`
  - it remained locked through the full `n = 1515` exhaustion point
- Comparator-fidelity read:
  - `PRISM_LITE` again collapsed to `RAW_PYTHON` routing on the combined surfaces and must be interpreted as a bounded local planning adaptation rather than an independent strong frontier
  - `F1_LITE` remained nontrivial on cluster-hard:
    - `solve_mode = direct` for `1276 / 1515`
    - `solve_mode = python` for `236 / 1515`
    - blank / parse-missing for `3 / 1515`
- Runtime / utilization notes:
  - fresh R3 main sweep wall-clock, from first `dmon` sample to final shard completion: about `2h48m`
  - observed `nvidia-smi dmon` nonzero-window `sm` mean:
    - early window: `94.17`
    - mid window: `92.56`
  - per-GPU nonzero-window `sm` means:
    - early: `gpu0 93.55`, `gpu1 94.24`, `gpu2 94.55`, `gpu3 94.35`
    - mid: `gpu0 95.39`, `gpu1 95.76`, `gpu2 95.92`, `gpu3 83.16`
- Final interpretation:
  - `CASS` is now statistically locked against both `RAW_PYTHON` and `OPERATOR_SCHEMA_TO_CODE_BASE` on the preregistered primary cluster-hard surface
  - `CASS` remains directly favorable to the closest recent inference-time comparator family collected here, with the cleanest external head-to-head coming from `F1_LITE`
  - the strongest supported paper posture is now a top-tier main-track submission centered on conservative target/postprocess-centered sparse schema surgery

## 2026-03-17 — LAST-PACK format-runner stabilization

- The first local `IFEval` main path exposed a real collection bottleneck:
  - the unscreened slice includes a small number of ultra-long-output prompts that dominate generation time under local 7B decoding
  - `hf_local` with `device_map=auto` also depressed format-pack GPU utilization because long-format runs were partially offloaded
- Bounded pivots applied:
  - keep `IFEval`, but screen out prompts with `min_words > 150`
  - cache the evaluator module and drop unused `loose` scoring
  - force per-worker full-on-visible-GPU loading via `CUDA_VISIBLE_DEVICES=<gpu>` and `--local-device-map cuda:0`
- Verified smoke on the stabilized path:
  - `IFEval` screened smoke on `GPU1` completed with:
    - `direct_success = 0`
    - `full_rewrite_success = 1`
    - `format_only_patch_success = 1`
    - `solve_then_format_success = 0`
  - per-method latencies on that smoke example:
    - direct `3.02s`
    - full rewrite `2.56s`
    - solve-then-format `6.29s`
- GPU availability issue:
  - `GPU0` retained an orphaned `14.8 GiB` allocation after an interrupted run
  - `nvidia-smi --gpu-reset -i 0` is not permitted in the current environment
  - therefore the stabilized heavy format path currently uses `GPU1–GPU3`
- Revised remaining runtime from the stabilized point:
  - screened `IFEval` (`381`, `3` GPUs): `35–55 minutes`
  - `IFBench` (`300`, `3` GPUs): `25–45 minutes`
  - planning-format bridge (`200`, `3` GPUs): `15–30 minutes`
  - criterion/report synthesis: `90–150 minutes`
  - optional second-model reduced replication: `+90–150 minutes`

## 2026-03-17 — LAST-PACK optional model-diversity registration

- Modules A-C completed with the core support-pack reports in place, so the optional reduced replication moved in-scope.
- Environment update:
  - the earlier orphan-allocation problem on `GPU0` / `GPU1` no longer appears in `nvidia-smi`
  - all four GPUs are again available for bounded heavy collection
- Registered optional reduced replication before launch:
  - model: `Qwen/Qwen2.5-Math-7B-Instruct`
  - surfaces:
    - planning model-diversity subset (`300`)
    - planning-format bridge subset (`200`)
  - sharding: `4` shards over `4` GPUs
  - expected incremental wall-clock: `1.5–2.5 hours`
- Scope decision:
  - keep the optional replication focused on the most stable non-math validators
  - do not reopen the frozen full math pipeline under a second model inside this sidecar phase

## 2026-03-17 — LAST-PACK model-diversity pivot to stable format subset

- First optional read after completing the secondary-model planning + bridge pack:
  - planning subset under `Qwen/Qwen2.5-Math-7B-Instruct` collapsed across methods (`PLAN_DIRECT = PLAN_FULL_RESTART = PLAN_SUFFIX_REPAIR = 0` on both easy and hard splits)
  - bridge subset stayed valid enough to score, but the local-repair edge did not strengthen on the second model
- Because the user explicitly asked not to stop after the first weak read, a bounded pivot is now registered before any conclusion:
  - keep the same frozen methods
  - add one reduced screened `IFEval` subset on the second model as the stable non-math validator
  - use `4` GPUs again with one shard per GPU
- Expected incremental wall-clock for this pivot:
  - reduced screened `IFEval` subset (`200`, `4` GPUs): `25–40 minutes`
  - refreshed model-diversity analysis and memo updates: `30–45 minutes`
- Mid-run bottleneck discovered during the first reduced `IFEval` attempt:
  - deterministic `FORMAT_ONLY_PATCH` used double-escaped regexes for highlight and word-count checks
  - this can trap a worker on prompts that contain `at least N words`
- Correction:
  - fix the regexes
  - add a regression test for `min_words`
  - rerun the full reduced `IFEval` second-model subset from scratch rather than mixing pre-fix and post-fix shards

## 2026-03-17 — LAST-PACK final support-pack outcome

- Core support-pack outcome:
  - math late-stage concentration is supported:
    - late-stage failure share rises from `0.652` on the easy transfer bucket to `0.802` on the hard cluster bucket
    - combined local patch beats restart in every registered bucket:
      - easy `0.609 vs 0.435`
      - medium `0.802 vs 0.512`
      - hard `0.691 vs 0.384`
  - planning generalization is supported in the narrower validator-conditioned sense:
    - hard lineworld failures are much later (`late share = 0.973`, mean failure-position ratio `0.978`)
    - suffix repair beats restart on both splits and never loses head-to-head in the main primary-model run
  - format generalization is the cleanest beyond-math support:
    - screened `IFEval`: `SOLVE_THEN_FORMAT = 0.695`, `FULL_REWRITE = 0.668`, `FORMAT_ONLY_PATCH = 0.659`, `DIRECT = 0.610`
    - `IFBench`: `SOLVE_THEN_FORMAT = 0.387`, `FORMAT_ONLY_PATCH = 0.320`, `FULL_REWRITE = 0.303`, `DIRECT = 0.267`
  - intervention criterion is supported:
    - pooled classifier matches `always_local` utility (`0.349`) while reducing intervention rate from `1.000` to `0.706`
- Optional model-diversity pack:
  - planning subset (`Qwen/Qwen2.5-Math-7B-Instruct`) collapses across direct / restart / suffix repair, so planning is not a stable cross-model support surface here
  - reduced screened `IFEval` does preserve the local-repair direction on the second model:
    - `DIRECT = 0.160`
    - `FULL_REWRITE = 0.215`
    - `LOCAL_BEST = 0.255`
- Runtime notes for the optional reduced replication:
  - planning subset wall-clock from first `dmon` sample to last shard completion: `11m27s`
  - planning-format bridge wall-clock: `16m48s`
  - reduced screened `IFEval` fixed rerun wall-clock: `14m15s`
  - active-window nonzero `sm` means:
    - planning `89.57`
    - bridge `90.61`
    - reduced `IFEval` rerun `88.29`
- Final read:
  - the broader “late-stage targeted repair” framing is materially stronger after this pack, especially for math and validator-rich format tasks
  - the most honest scope is still bounded rather than universal:
    - strong for late math failures
    - strong for non-math output-constraint repair
    - weaker and model-sensitive for planning

## 2026-03-18 — LACE registration and runtime estimate

- New sidecar phase registered:
  - `LACE = Localized Action Criterion Evaluation`
  - purpose: operationalize the `LAST-PACK` late-stage targeted-repair framing as a real online intervention policy
- Frozen method posture:
  - do not alter `CASS`
  - use `LACE` only to decide among:
    - `NO_INTERVENTION`
    - `LOCAL_REPAIR`
    - `GLOBAL_RESTART`
- Execution plan:
  - math online criterion deployment from frozen `CASS` traces
  - fresh output-constraint online rerun on screened `IFEval` + `IFBench`
  - fresh planning boundary rerun on a new lineworld seed
  - optional reduced second-model online check only if the first three modules finish cleanly
- Local-only execution rule:
  - no OpenAI API usage in this phase
  - heavy collection uses `Qwen/Qwen2.5-7B-Instruct`
  - `4` GPUs, one worker per visible GPU, `CUDA_VISIBLE_DEVICES=<gpu>` plus `--local-device-map cuda:0`
- Prompt-registered initial runtime estimate:
  - math online pack: `3–5h`
  - format online pack: `3–5h`
  - planning boundary: `2–3h`
  - analysis / figures / memos: `1–2h`
  - optional second-model reduced replication: `+3–4h`
  - total: `9–15h`
- Operational estimate before heavy collection given current repo reuse:
  - math analysis from frozen traces: `45–90m`
  - fresh format rerun: `90–150m`
  - fresh planning rerun: `75–120m`
  - analysis / memo synthesis: `60–120m`
  - optional reduced second-model `IFEval`: `25–45m`
  - likely total without optional module: `5–8h`
  - likely total with optional module: `6–9h`

## 2026-03-18 — LACE second-model expansion estimate before launch

- After Modules A–C completed cleanly, I expanded the optional replication beyond a tiny `IFEval` spot-check because the current `LACE` story is already positive and the repo has a clean reuse path.
- New second-model scope:
  - reduced math online-criterion replication on registered hard subsets (`300` cluster-hard + `150` generic-hard)
  - fresh output-constraint rerun on the same `LACE` screened `IFEval` (`381`) and `IFBench` (`300`) surfaces
  - follow-on model-diversity analysis and memo integration
- Revised pre-run wall-clock estimate:
  - second-model math collection: `3.0–4.0h`
  - second-model output-constraint collection: `1.0–1.5h`
  - second-model analysis / figures / memo integration: `45–75m`
  - incremental optional-module total: `4.75–6.75h`
  - revised end-to-end realized total if the expansion completes: `10–14h`
- Execution policy remains unchanged:
  - local-only
  - `4` GPUs
  - one worker per visible GPU
  - no new OpenAI API use

## 2026-03-18 — LACE final read

- Primary `LACE` answer:
  - the late-stage targeted-repair framing can be turned into a real online intervention policy
- Math online policy on the frozen primary-model traces:
  - `ALWAYS_DIRECT = 0.257`
  - `ALWAYS_RESTART = 0.466`
  - `ALWAYS_CASS = 0.753`
  - `LEARNED_GATE = 0.759`
  - intervention drops from `1.000` to `0.735`
- Output-constraint online policy:
  - `ALWAYS_FULL_REWRITE = 0.505`
  - `LOCAL_BEST = 0.653`
  - `HEURISTIC_GATE = 0.634`
  - `LEARNED_GATE = 0.620`
  - strongest surface remains screened `IFEval`
- Planning boundary check:
  - `FULL_RESTART = 0.000`
  - `SUFFIX_REPAIR = 0.055`
  - `LEARNED_GATE = 0.050`
  - planning remains usable only as bounded/control evidence
- Primary-model interpretation:
  - math is the cleanest online operationalization of the frozen `CASS` mechanism
  - output-constraint tasks are the strongest beyond-math deployment support
  - planning remains a useful but fragile boundary domain

## 2026-03-18 — LACE optional model-diversity completion

- The optional module was completed locally with `Qwen/Qwen2.5-Math-7B-Instruct`.
- Actual fresh math replication size used the frozen `cass_r4` model-subset manifests rather than regenerating smaller ones:
  - cluster-hard subset: `400`
  - generic-hard subset: `200`
  - reason: keep frozen split semantics and avoid hidden manifest drift
- Second-model math eval (`n = 214` after stable-hash holdout):
  - `ALWAYS_RESTART = 0.023`
  - `ALWAYS_CASS = 0.131`
  - `LEARNED_GATE_TRANSFER = 0.047`
  - `LEARNED_GATE_WITHIN = 0.140`
  - read: within-model fitting preserves the local-repair direction; raw transfer from the primary-model gate does not
- Second-model format eval (`n = 67`):
  - uses the fixed reduced screened-`IFEval` local fallback from `LAST-PACK`
  - `ALWAYS_FULL_REWRITE = 0.209`
  - `LEARNED_GATE_TRANSFER = 0.224`
  - `LOCAL_BEST = 0.254`
  - read: narrower but still directionally supportive
- Second-model planning eval (`n = 107`):
  - direct / suffix / restart / both gates all collapse to `0.000`
  - read: planning should remain a boundary/control surface only
- Runtime / utilization notes for the fresh second-model math collection:
  - cluster-hard pack wall-clock approximated from `nvidia-smi dmon`: `274.33m`
  - generic-hard pack wall-clock approximated from `nvidia-smi dmon`: `83.92m`
  - combined fresh second-model math collection: about `5.97h`
  - active-window nonzero `sm` means:
    - cluster `92.20`
    - generic `94.65`
  - cluster GPU-level `sm` means:
    - `gpu0 = 94.73`
    - `gpu1 = 84.42`
    - `gpu2 = 95.86`
    - `gpu3 = 94.84`
  - generic GPU-level `sm` means:
    - `gpu0 = 93.04`
    - `gpu1 = 95.24`
    - `gpu2 = 95.82`
    - `gpu3 = 94.54`
- Runtime-estimate update:
  - the expanded optional module exceeded the pre-run `4.75–6.75h` estimate only narrowly once the full frozen `400 + 200` math pack was honored
  - this was accepted because utilization stayed high and the run answered a reviewer-relevant model-diversity question cleanly
- API usage:
  - no OpenAI API usage in `LACE`

## 2026-03-18 — LACE-R2 registration and runtime estimate

- New reinforcement phase registered:
  - `LACE-R2`
  - purpose: simplify the online criterion and strengthen cross-family robustness
- Frozen posture:
  - do not alter `CASS`
  - do not alter the completed `LACE` main result
  - use `LACE-R2` only to reinforce explainability and robustness
- Registered module order:
  - criterion simplification on frozen primary-model traces
  - non-Qwen cross-family math reduced replication
  - fresh non-Qwen format rerun
  - optional tiny planning sanity only if cheap
- Cross-family model bring-up order:
  1. `mistralai/Mistral-7B-Instruct-v0.3`
  2. `meta-llama/Llama-3.1-8B-Instruct`
  3. `google/gemma-2-9b-it`
- Hardware check before heavy collection:
  - `4 x RTX 3090 24GB`
  - enough for one-worker-per-GPU 7B-ish local runs, likely in `float16` or fallback quantization if needed
- Prompt-registered initial estimate:
  - criterion simplification pack: `2–3h`
  - cross-family math reduced replication: `4–6h`
  - cross-family format fresh rerun: `2–4h`
  - analysis / figures / memos: `1–2h`
  - total: `9–15h`
  - with model bring-up issues: `12–18h`
- Operational pre-run estimate:
  - criterion simplification implementation + report: `60–120m`
  - cross-family model smoke test / bring-up: `20–45m`
  - cross-family math reduced collection over `4` GPUs: `180–300m`
  - cross-family screened `IFEval` rerun: `60–120m`
  - `IFBench` add-on if stable: `45–90m`
  - cross-family analysis / figures / memos: `60–120m`
  - likely total without `IFBench` and planning: `7–11h`
  - likely total with `IFBench` and a cheap planning sanity: `9–14h`
- API usage rule:
  - no OpenAI API usage planned in `LACE-R2`

## 2026-03-18 — LACE-R2 completion

- `LACE-R2` closed as a bounded simplicity-and-robustness reinforcement pack over the frozen `LACE` result.
- Cross-family model chosen:
  - `mistralai/Mistral-7B-Instruct-v0.3`
  - bring-up succeeded on the first-choice family, so no fallback to `Llama` or `Gemma` was needed
- Criterion simplification result on the primary Qwen family:
  - math:
    - `LEARNED_GATE = 0.759`
    - `SIMPLE_3FEATURE_GATE = 0.759`
    - `SIMPLE_2FEATURE_GATE = 0.753`
    - smallest viable rule:
      - `if max(target_score, role_score) < 3: NO_INTERVENTION; elif checker_target_score >= 1: LOCAL_PATCH; else: GLOBAL_RESTART`
  - format:
    - `LEARNED_GATE = 0.620`
    - `SIMPLE_THRESHOLDED_TREE = 0.640`
    - `SIMPLE_2FEATURE_GATE = 0.634`
    - simplest strong rule:
      - `if direct validator passes: NO_INTERVENTION; elif failed_instruction_count <= 2: SOLVE_THEN_FORMAT; else: GLOBAL_REWRITE`
- Cross-family math rerun on fresh reduced cluster-hard only:
  - eval split:
    - `train = 269`
    - `eval = 131`
  - `ALWAYS_RESTART = 0.122`
  - `ALWAYS_CASS = 0.275`
  - `LEARNED_GATE_TRANSFER = 0.183`
  - `LEARNED_GATE_WITHIN = 0.282`
  - `SIMPLE_BEST_GATE = 0.290`
  - `ORACLE_POLICY = 0.321`
  - read:
    - the directional online-policy result survives on a genuinely different family
    - within-model fitting beats naive restart clearly
    - the best simple rule slightly exceeds the within-model learned gate on this eval slice
    - transfer gating is materially weaker than within-model fitting
  - late-stage failure concentration among failed drafts:
    - `hard_cluster_main = 0.664`
- Cross-family format rerun on fresh screened `IFEval`:
  - eval split:
    - `train = 240`
    - `eval = 141`
  - `ALWAYS_FULL_REWRITE = 0.518`
  - `ALWAYS_LOCAL_FORMAT_PATCH = 0.546`
  - `ALWAYS_SOLVE_THEN_FORMAT = 0.475`
  - `HEURISTIC_GATE = 0.610`
  - `LEARNED_GATE_WITHIN = 0.539`
  - `SIMPLE_BEST_GATE = 0.603`
  - `ORACLE_POLICY = 0.674`
  - read:
    - local repair or gated local repair remains above full rewrite on the new family
    - the simple rule stays competitive and is easier to explain than the learned gate
- Scope decisions:
  - generic-hard was not rerun on the cross-family model because the reduced cluster-hard rerun already answered the main math robustness question
  - `IFBench` was not rerun in `LACE-R2` because the fresh screened `IFEval` rerun already answered the reviewer-facing freshness concern and kept the pack bounded
  - optional planning sanity refresh was not run because planning remains a control/boundary domain and would not materially change the headline reinforcement read
- Runtime / utilization notes:
  - fresh cross-family math cluster run proxy wall-clock:
    - about `78.53m`
    - measured from output-root start proxy to last shard completion
  - fresh cross-family format `IFEval` rerun wall-clock:
    - about `26.57m`
    - measured from first `dmon` timestamp to last shard completion
  - combined heavy-collection proxy:
    - about `105.10m`
  - nonzero-window `sm` means:
    - math cluster `93.77`
    - format `IFEval` `90.90`
  - read:
    - the 4-GPU saturation target was met during the actual generation windows
- Final `LACE-R2` interpretation:
  - the online intervention story is now simpler and more explainable
  - the strongest reinforcement survives on a genuinely different model family for math
  - the format-side support is refreshed with a fresh second-model rerun rather than only the earlier reduced fallback slice
- API usage:
  - no OpenAI API usage in `LACE-R2`

## 2026-03-18 — LACE-R3 registration and runtime estimate

- New bounded reinforcement phase registered:
  - `LACE-R3`
  - purpose: criterion portability, fresh cross-family `IFBench`, and simple-vs-learned transfer clarity
- Frozen posture remains unchanged:
  - do not alter `CASS`
  - do not alter `LACE`
  - do not alter `LACE-R2`
- Registered module order:
  - portability analysis on existing `Mistral` math + screened `IFEval`
  - fresh `Mistral` `IFBench` rerun
  - combined rule-transfer analysis
  - optional third family only if ambiguity remains and bring-up is cheap
- Cross-family family order:
  1. existing `Mistral`
  2. optional `Llama`
  3. optional `Gemma`
- Prompt-registered estimate:
  - criterion portability on current `Mistral` family: `2–3h`
  - fresh cross-family `IFBench` run: `2–4h`
  - optional third-family reduced replication: `4–6h`
  - analysis / figures / memo: `1–2h`
  - total expected end-to-end: `8–14h`
  - with third-family support: `12–18h`
- Operational pre-run estimate:
  - portability analysis implementation + report: `60–120m`
  - fresh `Mistral` `IFBench` collection over `4` GPUs: `60–150m`
  - `IFBench` analysis + rule-transfer synthesis: `60–120m`
  - optional third-family bring-up + reduced replication: `240–360m`
  - likely total without third family: `4–7h`
  - likely total with third family: `8–13h`
- API usage rule:
  - no OpenAI API usage planned in `LACE-R3`

## 2026-03-18 — LACE-R3 completion

- `LACE-R3` closed without reopening the frozen `CASS` / `LACE` methods story.
- Main portability read on the existing `Mistral` family:
  - math cluster:
    - `ALWAYS_RESTART = 0.122`
    - `LEARNED_GATE_TRANSFER = 0.183`
    - best simple transfer `= 0.290`
    - `LEARNED_GATE_WITHIN = 0.282`
  - screened `IFEval`:
    - `ALWAYS_FULL_REWRITE = 0.518`
    - `LEARNED_GATE_TRANSFER = 0.574`
    - best simple transfer `= 0.624`
    - `LEARNED_GATE_WITHIN = 0.539`
  - read:
    - simple transferred rules beat learned transfer on math and screened `IFEval`
    - within-model tuning helps on math
    - within-model tuning is not uniformly helpful on the format surfaces
- Fresh cross-family `IFBench` rerun on `Mistral`:
  - split:
    - `train=197`
    - `eval=103`
  - overall:
    - `ALWAYS_DIRECT = 0.117`
    - `ALWAYS_FULL_REWRITE = 0.155`
    - `ALWAYS_LOCAL_FORMAT_PATCH = 0.146`
    - `ALWAYS_SOLVE_THEN_FORMAT = 0.184`
    - `HEURISTIC_GATE_TRANSFER = 0.214`
    - `LEARNED_GATE_TRANSFER = 0.204`
    - `SIMPLE_BEST_GATE_TRANSFER = 0.223`
    - `LEARNED_GATE_WITHIN = 0.194`
    - `SIMPLE_WITHIN_TUNED = 0.223`
  - read:
    - local-repair-over-rewrite survives on fresh cross-family `IFBench`
    - the simple transferred rule remains above the learned transfer gate and above learned-within on this surface
- Combined rule-transfer read:
  - math portability gap:
    - best simple transfer minus learned transfer `= +0.107`
  - screened `IFEval` portability gap:
    - best simple transfer minus learned transfer `= +0.050`
  - fresh `IFBench` portability gap:
    - best simple transfer minus learned transfer `= +0.019`
  - practical conclusion:
    - the small-rule family is the cleaner portable criterion story
- Runtime and utilization:
  - registration-to-summary wall clock:
    - about `45.3m`
    - from `2026-03-18T14:22:22Z` to `2026-03-18T15:07:38Z`
  - fresh `IFBench` `dmon` window:
    - `2026-03-18T14:38:53Z` to `2026-03-18T15:08:26Z`
  - fresh `IFBench` shard-completion span:
    - about `5.45m`
    - from first to last shard `completed.txt`
  - fresh `IFBench` collection span from first `dmon` sample to last shard completion:
    - about `24.58m`
  - fresh `IFBench` nonzero-window `sm` mean:
    - `88.91`
  - read:
    - the `>85%` active-window utilization target was met
    - the prompt estimate overshot because `LACE-R3` reused the cached `Mistral` math and screened `IFEval` reruns and the optional third family never became necessary
- Final `LACE-R3` interpretation:
  - the criterion story is now cleaner because the simple rule family is not just interpretable, but portable
  - fresh cross-family `IFBench` fills the main remaining format-side gap
  - optional third-family bring-up was not needed once `Mistral` answered the portability question cleanly
- API usage:
  - no OpenAI API usage in `LACE-R3`

## 2026-03-19 — CASS-XF registration and runtime estimate

- New bounded reinforcement phase registered:
  - `CASS-XF`
  - purpose: cross-family replication of the frozen main `CASS` method family itself
- Frozen posture remains unchanged:
  - do not alter `CASS`
  - do not alter `CASS-R2`
  - do not alter `CASS-R3`
  - do not alter `CASS-R4`
  - do not alter `LAST-PACK` / `LACE`
- Registered module order:
  - freeze exact reduced `cluster-hard` and `generic-hard` manifests
  - run frozen `CASS` family on `Mistral`
  - decompose fixed-patch vs gate vs operator portability
  - consider a third family only if the `Mistral` read remains materially ambiguous
- Cross-family family order:
  1. existing `Mistral`
  2. optional `Llama`
  3. optional `Gemma`
- Frozen reduced surfaces chosen from the `cass_r4` manifest lineage:
  - `gsm8k_train_cluster_model_subset`
  - `n=400`
  - `hard_cluster_main_r2`
  - `gsm8k_train_generic_model_subset`
  - `n=200`
  - `hard_generic_main_r2`
- Prompt-registered estimate:
  - `Mistral` cluster-hard reduced replication: `3–5h`
  - `Mistral` generic-hard reduced replication: `2–3h`
  - analysis / figures / memo: `1–2h`
  - optional third-family reduced replication: `+5–8h`
  - total expected end-to-end: `6–10h`
  - with optional third family: `11–18h`
- Operational pre-run estimate:
  - manifest freeze + surface report: `30–60m`
  - `Mistral` cluster-hard collection over `4` GPUs: `120–240m`
  - `Mistral` generic-hard collection over `4` GPUs: `60–120m`
  - portability decomposition + report generation: `60–120m`
  - likely total without third family: `4.5–8h`
  - likely total with third family: `9.5–15h`
- First-hour runtime revision after live `Mistral` monitoring:
  - `cluster-hard` completed in roughly `35–45m` active collection time
  - `generic-hard` is slower per example but sustained `sm` utilization is still in the high `80s`
  - revised likely total without third family: `2.5–4.5h`
  - revised likely total with third family: `7.5–11h`
- API usage rule:
  - no OpenAI API usage planned in `CASS-XF`

## 2026-03-19 — CASS-XF Mistral completion

- Completed the frozen `CASS` main-method cross-family replication on:
  - `mistralai/Mistral-7B-Instruct-v0.3`
- Frozen reduced surfaces completed exactly as registered:
  - `hard_cluster_main_r2`: `n=400`
  - `hard_generic_main_r2`: `n=200`
- Collection runtime:
  - `runtime_s = 4615` (`76.9m`)
  - cluster active-window `sm` mean from `dmon_cluster_early.log`: `91.10`
  - cluster recent active-window mean: `94.04`
  - generic active-window `sm` mean from `dmon_generic_early.log`: `87.02`
  - generic recent mean is lower at the end because three GPUs go idle while the final shard drains
- Main portability read on `Mistral`:
  - cluster-hard:
    - `RAW_PYTHON = 0.2075`
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.3175`
    - `CASS_TARGET_POSTPROCESS_PATCH = 0.3325`
    - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH = 0.3325`
    - `CASS_CONSERVATIVE_GATE = 0.3325`
  - generic-hard:
    - `RAW_PYTHON = 0.1800`
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.3850`
    - `CASS_TARGET_POSTPROCESS_PATCH = 0.4150`
    - `CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH = 0.4150`
    - `CASS_CONSERVATIVE_GATE = 0.4150`
- Pairwise reduced-replication read:
  - cluster-hard `CASS_TARGET_POSTPROCESS_PATCH - RAW_PYTHON = +0.1244 [0.0800, 0.1675]`
  - cluster-hard `CASS_TARGET_POSTPROCESS_PATCH - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0145 [-0.0225, 0.0525]`
  - generic-hard `CASS_TARGET_POSTPROCESS_PATCH - RAW_PYTHON = +0.2348 [0.1600, 0.3100]`
  - generic-hard `CASS_TARGET_POSTPROCESS_PATCH - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0299 [-0.0300, 0.0900]`
- Portability interpretation:
  - the frozen `CASS` family clearly survives against `RAW_PYTHON` on a genuine non-`Qwen` family
  - it is directionally favorable to `OPERATOR_SCHEMA_TO_CODE_BASE` on both reduced surfaces, but the reduced-sample interval still overlaps zero
  - the main useful ingredient still looks like target/postprocess-centered patching
  - `Mistral` does not gain anything further from the conservative gate over the best fixed target/postprocess patch on this reduced replication
- Third-family decision:
  - not run
  - the `Mistral` read is already directional enough that a third-family escalation would be low-yield inside this bounded pack

## 2026-03-19 — CASS-XF-R2 registration and runtime estimate

- New bounded reinforcement phase registered:
  - `CASS-XF-R2`
  - purpose: portability-lock reinforcement for the frozen main `CASS` family
- Frozen posture remains unchanged:
  - keep `CASS`, `CASS-R2`, `CASS-R3`, `CASS-R4`, `CASS-XF` fixed as evidence
- Planned module order:
  - expand `Mistral` to the full portability surfaces
  - add one required third-family reduced replication
  - synthesize whether target/postprocess patching, rather than role-only repair or the conservative gate, is the portable core
- Prompt-registered estimate:
  - `Mistral` scale-up on cluster-hard + generic-hard: `4–6h`
  - third-family reduced replication: `4–6h`
  - analysis / figures / memo: `1–2h`
  - total expected end-to-end: `9–14h`
  - with model bring-up issues: `12–18h`
- Operational pre-run estimate:
  - manifest freeze + surface report: `30–45m`
  - expanded `Mistral` cluster-hard collection: `180–300m`
  - expanded `Mistral` generic-hard collection: `75–135m`
  - third-family reduced replication: `75–150m`
  - synthesis + figure/report pass: `60–120m`
  - likely total without infra friction: `7–12.5h`
- Third-family bring-up order:
  1. `meta-llama/Llama-3.1-8B-Instruct`
  2. `google/gemma-2-9b-it`
  3. first stable non-`Qwen`, non-`Mistral` fallback
- API usage rule:
  - no OpenAI API usage planned in `CASS-XF-R2`

## 2026-03-19 — CASS-XF-R2 bring-up notes

- Third-family access audit:
  - `meta-llama/Llama-3.1-8B-Instruct` metadata resolved, but frozen collector smoke failed at actual model load with gated-repo `401`
  - `google/gemma-2-9b-it` behaved the same way: metadata visible, model load gated at runtime
  - therefore the required third-family path moved to the allowed open fallback set
- Expanded `Mistral` sharding correction:
  - first expanded `Mistral` attempt used contiguous full-manifest shards
  - because the earlier reduced `Mistral` run had cached many prefix examples, contiguous sharding concentrated cache hits on shard `01`
  - that made one GPU finish almost immediately and dropped the active-window `sm` mean far below the intended heavy-collection regime
  - fix applied:
    - preserve the frozen full manifest order
    - repartition only the expanded `Mistral` shard files in deterministic round-robin order
    - relaunch collection into a fresh output root
- Post-fix `Mistral` collection health:
  - balanced shard counts
  - recent cluster active-window `sm` mean returned to about `94`
- First-hour runtime revision:
  - after the round-robin relaunch, expanded `Mistral` cluster collection settled into sustained `~89–95` recent-window `sm`
  - realized throughput is slower than the cache-heavy opening minutes but still points to a full `Mistral` run that is materially faster than the conservative `7–12.5h` pre-run estimate
  - revised likely total for `CASS-XF-R2` without additional infra issues: `4.5–8.5h`
- Third-family fallback resolution:
  - `Phi-4-mini-instruct` is accessible but fails under the frozen local stack because its dynamic model code expects a newer `transformers` cache API
  - `Phi-3.5-mini-instruct` fails for the same family of cache-API mismatch during generation
  - `CohereForAI/aya-expanse-8b` is gated at actual model load on this box
  - `ibm-granite/granite-3.1-8b-instruct` successfully snapshot-downloaded into the local Hugging Face cache and is the active third-family candidate for the reduced replication step

## 2026-03-19 — CASS-XF-R2 ended experiment window

- The completed raw experiment window reflected in the current `CASS-XF-R2` reports is:
  - expanded `Mistral` cluster-hard only
  - `n=1515`
  - `hard_cluster_main_r2`
- Actual ended-state main read:
  - `RAW_PYTHON = 0.209901`
  - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.331353`
  - `CASS_TARGET_POSTPROCESS_PATCH = 0.358416`
  - `CASS_CONSERVATIVE_GATE = 0.358416`
- Pairwise ended-state read:
  - `CASS_TARGET_POSTPROCESS_PATCH - RAW_PYTHON = +0.1486 [0.1234, 0.1716]`
  - `CASS_TARGET_POSTPROCESS_PATCH - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0273 [0.0079, 0.0482]`
- Sequential interval-shrinkage read:
  - first positive lower CI bound vs operator appears at `n=1350`
  - remains positive again at `n=1500` and `n=1515`
  - therefore the expanded `Mistral` cluster-hard lock attempt succeeded on the ended run
- Portable-core read from ended-state evidence:
  - `Mistral` best frozen CASS method is `CASS_TARGET_POSTPROCESS_PATCH`
  - `Mistral` gate-over-patch wins: `0`
  - `role-only` remains much weaker than target/postprocess patching
- Not run in this ended experiment window:
  - expanded `Mistral` generic-hard
  - `Granite` reduced replication
  - therefore `CASS-XF-R2` reporting is honest about a strong `Mistral` cluster-hard lock plus still-open follow-on portability work

## 2026-03-19 — CASS-XF-R3 registration and runtime estimate

- New bounded reinforcement phase registered:
  - `CASS-XF-R3`
  - purpose: portability closure for the remaining `Mistral` generic-hard and third-family gaps
- Frozen posture remains unchanged:
  - keep `CASS`, `CASS-XF`, and `CASS-XF-R2` fixed as evidence
- Third-family choice order is now resolved in practice:
  - use `ibm-granite/granite-3.1-8b-instruct` first because it is the first stable open candidate already accessible on this box
- Prompt-registered estimate:
  - `Mistral` generic-hard completion: `2–3h`
  - third-family cluster-hard reduced replication: `4–6h`
  - third-family generic-hard reduced replication: `2–3h`
  - analysis / figures / memo: `1–2h`
  - total expected end-to-end: `9–14h`
  - with model bring-up issues: `12–18h`
- Operational pre-run estimate:
  - manifest freeze + report: `20–30m`
  - expanded `Mistral` generic-hard: `45–90m`
  - reduced `Granite` cluster-hard: `75–150m`
  - reduced `Granite` generic-hard: `35–75m`
  - synthesis + reports: `60–120m`
  - likely total without infra surprises: `3.9–7.6h`
- API usage rule:
  - no OpenAI API usage planned in `CASS-XF-R3`

## 2026-03-20 — CASS-XF-R3 completion

- Completed `CASS-XF-R3` on:
  - expanded `Mistral` generic-hard
  - reduced `Granite` cluster-hard
  - reduced `Granite` generic-hard
- Runtime:
  - `Mistral` generic-hard `runtime_s = 5673` (`94.6m`)
  - `Granite` reduced replication `runtime_s = 14587` (`243.1m`)
- GPU traces:
  - `Mistral` generic `dmon_generic_early.log` mean `88.27`
  - `Granite` cluster `dmon_cluster_early.log` mean `81.89`
  - `Granite` generic `dmon_generic_early.log` mean `86.96`
- Main ended-state read:
  - `Mistral` generic-hard:
    - `RAW_PYTHON = 0.200828`
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.391304`
    - `CASS_TARGET_POSTPROCESS_PATCH = 0.420290`
    - `CASS_TARGET_POSTPROCESS_PATCH - RAW_PYTHON = +0.2192 [0.1739, 0.2629]`
    - `CASS_TARGET_POSTPROCESS_PATCH - OPERATOR_SCHEMA_TO_CODE_BASE = +0.0285 [-0.0124, 0.0683]`
  - `Granite` cluster-hard:
    - `RAW_PYTHON = 0.6075`
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.7325`
    - `CASS_TARGET_POSTPROCESS_PATCH = 0.5075`
  - `Granite` generic-hard:
    - `RAW_PYTHON = 0.655`
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.765`
    - `CASS_TARGET_POSTPROCESS_PATCH = 0.64`
- Portable-core read:
  - across `Qwen`, `Mistral`, and `Granite`, target/postprocess patching is still the strongest ingredient inside the frozen `CASS` family more often than the gate
  - `role-only` remains weaker than the target/postprocess patch on all tested families/surfaces
  - but absolute direction vs `RAW_PYTHON` / `OPERATOR_SCHEMA_TO_CODE_BASE` does not survive on `Granite`
- Interpretation:
  - the portability closure is strong across two families (`Qwen`, `Mistral`)
  - the within-family portable-core story generalizes to `Granite`
  - the stronger claim that the full frozen `CASS` patch family stays favorable to `RAW_PYTHON` / `OPERATOR` across three families is not supported

## 2026-03-20 — CASS-BD registration and runtime estimate

- New bounded diagnosis phase registered:
  - `CASS-BD`
  - purpose: explain the `Granite` boundary case after `CASS-XF-R3`
- Frozen posture remains unchanged:
  - keep `CASS`, `CASS-XF`, `CASS-XF-R2`, and `CASS-XF-R3` fixed as evidence
- Prompt-registered estimate:
  - Granite replay-controlled field audit: `1–2h`
  - Granite partial patch replay pack: `2–3h`
  - optional tiny API teacher diagnostic: `30–60m`
  - analysis / figures / memo: `1–2h`
  - total expected end-to-end: `4–6h`
  - with optional API diagnostic: `5–7h`
- Operational pre-run estimate:
  - manifest freeze + report: `15–25m`
  - Granite field audit: `30–60m`
  - partial replay over the Granite reduced surfaces on `4` GPUs: `90–180m`
  - synthesis + figures + memo: `60–120m`
  - likely total without API diagnostic: `3.3–6.4h`
- API usage rule:
  - no OpenAI API usage planned unless the diagnosis remains ambiguous after the replay pack

## 2026-03-20 — CASS-BD completion

- Completed `CASS-BD` on the frozen Granite reduced surfaces:
  - field audit from existing `Granite` raw outputs
  - replay-controlled partial surgery over the same frozen drafts and baseline schemas
- Runtime:
  - Granite partial replay `runtime_s = 3754` (`62.6m`)
- Granite field-audit read:
  - cluster baseline-right / patch-wrong count: `115`
  - generic baseline-right / patch-wrong count: `42`
  - dominant category on both surfaces: `code_generation_after_correct_patch`
- Partial surgery read:
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
- Diagnosis conclusion:
  - Granite is not well described as simple extraction weakness
  - the cleaner explanation is a combination of:
    - strong baseline dominance
    - destructive target/relation overwrite
    - compiler/code-generation brittleness once those target fields are changed
  - postprocess/discretization edits are comparatively safe on Granite; target-side surgery is the dangerous part
- Optional teacher diagnostic decision:
  - skipped
  - field audit plus partial replay already distinguished the failure mode well enough

## 2026-03-21 — CASS-SR registration and runtime estimate

- New bounded reinforcement phase registered:
  - `CASS-SR`
  - purpose: scale robustness for the frozen main `CASS` family
- Frozen posture remains unchanged:
  - keep `CASS`, `CASS-XF`, `CASS-XF-R2`, `CASS-XF-R3`, and `CASS-BD` fixed as evidence
- Prompt-registered estimate:
  - `Qwen-14B` cluster-hard reduced replication: `4–6h`
  - `Qwen-14B` generic-hard reduced replication: `2–3h`
  - optional `Mistral-Small-24B` cluster-hard reduced replication: `5–8h`
  - optional `Mistral-Small-24B` generic-hard reduced replication: `3–5h`
  - analysis / figures / memo: `1–2h`
  - total expected end-to-end: `7–11h` (`Qwen-14B` only)
  - total expected end-to-end: `12–20h` (`Qwen-14B + 24B Mistral`)
- Operational pre-run estimate:
  - manifest freeze + report: `15–25m`
  - `Qwen-14B` reduced cluster + generic over `4` GPUs with `4bit`: `2.5–4.5h`
  - optional `Mistral-Small-24B` reduced cluster + generic over `4` GPUs with `4bit`: `4–7h`
  - synthesis + figure/report pass: `60–120m`
- Bring-up policy:
  - `Qwen-14B` is the required first stronger model
  - `Mistral-Small-24B-Instruct-2501` is optional and only runs if the smoke path is low-friction
- API usage rule:
  - no OpenAI API usage planned in `CASS-SR`

## 2026-03-21 — CASS-SR Qwen-14B completion

- Completed the required stronger-scale run on:
  - `Qwen/Qwen2.5-14B-Instruct`
- Reduced surfaces used exactly as frozen:
  - cluster-hard `n=400`
  - generic-hard `n=200`
- Ended-state runtime notes:
  - cluster pass was launched in `/workspace/project/results/cass_sr_qwen14b/qwen14b_reduced_20260321b`
  - generic required a clean follow-on tail rerun in `/workspace/project/results/cass_sr_qwen14b/qwen14b_generic_20260321b`
  - `dmon_cluster_early.log` span: `2026-03-21 04:32:25 UTC` to `2026-03-21 07:54:37 UTC`
  - `dmon_generic_early.log` span: `2026-03-21 09:31:53 UTC` to `2026-03-21 09:58:42 UTC`
  - cluster `sm` mean: `41.65`
  - generic `sm` mean: `40.95`
  - this run was throughput-limited under the only stable local 14B path found (`hf_local`, `4bit`)
- Main result:
  - cluster-hard:
    - `RAW_PYTHON = 0.8650`
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.8625`
    - `CASS_TARGET_POSTPROCESS_PATCH = 0.7050`
    - `CASS_TARGET_POSTPROCESS_PATCH - RAW_PYTHON = -0.1594 [-0.2100, -0.1125]`
    - `CASS_TARGET_POSTPROCESS_PATCH - OPERATOR_SCHEMA_TO_CODE_BASE = -0.1568 [-0.2025, -0.1125]`
  - generic-hard:
    - `RAW_PYTHON = 0.8800`
    - `OPERATOR_SCHEMA_TO_CODE_BASE = 0.8750`
    - `CASS_TARGET_POSTPROCESS_PATCH = 0.7200`
    - `CASS_TARGET_POSTPROCESS_PATCH - RAW_PYTHON = -0.1599 [-0.2250, -0.0950]`
    - `CASS_TARGET_POSTPROCESS_PATCH - OPERATOR_SCHEMA_TO_CODE_BASE = -0.1549 [-0.2200, -0.0850]`
- Interpretation:
  - at 14B, the target/postprocess patch remains the strongest frozen `CASS` ingredient inside the `Qwen` family
  - but the absolute intervention value collapses against very strong `RAW_PYTHON` / `OPERATOR` baselines
  - the scale story is therefore much stronger for small/medium open models than for stronger open models
- Optional `Mistral-Small-24B` decision:
  - not run
  - the low-friction requirement was not met during bring-up

## 2026-03-22 — CASS-FI completion

- Completed `CASS-FI` across the four established family/scale cells:
  - `Qwen-7B`
  - `Mistral-7B`
  - `Granite-8B` (reused the completed `CASS-BD` replay)
  - `Qwen-14B`
- Runtime notes:
  - `Qwen-7B` replay `runtime_s = 2141` (`35.7m`)
  - `Mistral-7B` generic replay `runtime_s = 746` (`12.4m`)
  - `Granite-8B` replay `runtime_s = 3754` (`62.6m`)
  - `Qwen-14B` replay was completed via a cluster pass plus a generic tail rerun under the only stable local path found
- Portable-core win counts:
  - `POSTPROCESS_ONLY_PATCH = 4`
  - `TARGET_PLUS_POSTPROCESS_PATCH = 2`
  - `CASS_TARGET_POSTPROCESS_PATCH = 1`
  - `TARGET_ONLY_PATCH = 1`
- Family-by-family read:
  - `Granite-8B`:
    - `POSTPROCESS_ONLY_PATCH` and `DISCRETIZATION_ONLY_PATCH` dominate both surfaces
  - `Qwen-14B`:
    - `POSTPROCESS_ONLY_PATCH` dominates both surfaces
    - `DISCRETIZATION_ONLY_PATCH` is second on both surfaces
  - `Mistral-7B`:
    - `TARGET_PLUS_POSTPROCESS_PATCH` stays strongest on both surfaces
    - `TARGET_ONLY_PATCH` remains close behind
  - `Qwen-7B`:
    - cluster-hard still prefers the frozen full `CASS_TARGET_POSTPROCESS_PATCH`
    - generic-hard still prefers a target-side-inclusive variant
- Final interpretation:
  - the most defensible cross-family wording is now:
    - `postprocess/discretization-centered patching is the safer portable core`
    - `target-side surgery is conditionally useful on smaller-model cells and risky on stronger/boundary cells`
- Optional teacher diagnostic decision:
  - skipped
  - the replay evidence already separates the safe sub-field from the family/scale-sensitive one

## 2026-03-23 — Code-Last registration and smoke-calibrated estimate

- Started `code_last`, the bounded coding-side generalization pack after `CASS-FI`.
- Scope frozen before heavy runs:
  - validator-rich function-level coding only
  - `EvalPlus` with `HumanEval+` and `MBPP+`
  - primary model `Qwen/Qwen2.5-7B-Instruct`
  - optional second-family support only via `Mistral-7B-Instruct-v0.3` if runtime remains comfortable
  - `MGDebugger` only as a contextual debugging comparator, not a main benchmark target
- Why this scope:
  - function-level coding with deterministic tests is the cleanest coding analogue of late-stage repair
  - this is not a repo-level APR or vulnerability-repair study
- Benchmark setup:
  - cloned and inspected:
    - `external/evalplus`
    - `external/MGDebugger`
  - materialized frozen direct benchmark manifest:
    - `542` tasks total
    - `164` HumanEval+
    - `378` MBPP+
  - manifest root:
    - `/workspace/project/data/code_last_manifests_20260323a`
- Execution-path decision:
  - split generation and EvalPlus validation into separate phases
  - reason:
    - inline validation from the model-loaded process triggered EvalPlus fork/memory instability during smoke
    - generation-only phases keep GPU collection moving while validation runs afterward on frozen outputs
- Smoke measurements used for wall-clock calibration:
  - direct generation:
    - `8` tasks on `1` GPU in `20.01s`
  - direct validation:
    - `8` tasks serial in `95.47s`
  - repair generation:
    - `4` failed tasks on `1` GPU in `130.08s`
  - repair validation:
    - `4` failed tasks serial in `20.03s`
- Preregistered runtime estimate written to `reports/code_last_plan.md`:
  - EvalPlus integration + slice construction: `1–2h`
  - primary Qwen coding pack: `4–6h`
  - optional Mistral reduced replication: `3–5h`
  - analysis / figures / memo: `1–2h`
  - total expected end-to-end: `6–10h`
  - with Mistral support: `9–14h`
- Smoke-scaled working expectation:
  - Qwen-only path likely lands near the lower half of the preregistered window, roughly `4–6h`
- First heavy-pass correction:
  - the initial `qwen7b_*_20260323b` collection exposed two issues:
    - direct diagnostic replay needed a safer parent/child handoff than the first `Queue.empty()` path
    - batched `hf_local` generation was running decoder-only prompts with right-padding
  - direct left-padding A/B smoke on `32` tasks changed `10 / 32` direct solutions
  - repair left-padding A/B smoke on `4` tasks changed `4 / 4` task-level repair outputs on at least one branch
  - because those differences are too large to ignore, the `20260323b` collection is treated as exploratory only and not used for final numerics
  - the clean main rerun is restarted in:
    - `/workspace/project/results/code_last_main/qwen7b_direct_20260323c_leftpad`
    - `/workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad`
- Revised expectation after the correction:
  - remaining Qwen collection + validation: `5–7h`
  - synthesis / figures / memo: `1–2h`
  - working Qwen-only expectation from the corrected restart: `7–9h`

## 2026-03-23 — Code-Last final read

- Completed corrected left-padding main run:
  - direct namespace:
    - `/workspace/project/results/code_last_main/qwen7b_direct_20260323c_leftpad`
  - repair namespace:
    - `/workspace/project/results/code_last_main/qwen7b_repairs_20260323c_leftpad`
- Final wall-clock:
  - direct collection + validation: `509s`
  - repair collection + validation: `1336s`
  - total after corrected restart: `1845s` (`30.8m`)
- Generation utilization snapshots:
  - direct active-window `sm` mean: `83.35`
  - near-correct repair active-window `sm` mean: `84.38`
  - general-fail repair active-window `sm` mean: `91.70`
  - deterministic EvalPlus validation remained CPU-bound as expected
- Slice construction:
  - exact public-pass / extended-fail: `48`
  - relaxed main near-correct slice: `56`
  - general-fail contrast slice: `184`
  - syntax/runtime control slice: `13`
- Near-correct failure concentration:
  - `boundary_or_off_by_one = 38 / 56`
  - `return_or_postcondition = 4 / 56`
  - combined late/boundary share: `42 / 56 = 0.750`
- Main near-correct head-to-head:
  - `LOCAL_TEST_GUIDED_PATCH = 9 / 56 = 0.1607`
  - `FULL_REWRITE_FROM_FAILURE = 9 / 56 = 0.1607`
  - pairwise delta `LOCAL - REWRITE = +0.0018 [-0.0893, +0.0893]`
  - result: overall tie, not a local-patch win
- Dataset split:
  - `HumanEval+` near-correct:
    - `LOCAL = 5 / 16`
    - `REWRITE = 3 / 16`
  - `MBPP+` near-correct:
    - `LOCAL = 4 / 40`
    - `REWRITE = 6 / 40`
- General-fail contrast:
  - `FULL_REWRITE_FROM_FAILURE = 52 / 184 = 0.2826`
  - `BOUNDARY_PATCH = 50 / 184 = 0.2717`
  - `LOCAL_TEST_GUIDED_PATCH = 25 / 184 = 0.1359`
  - `RETURN_POSTCOND_PATCH = 32 / 184 = 0.1739`
  - contrast slice remains dominated by `broad_algorithmic_failure = 167 / 184`
- Gate read:
  - `SIMPLE_CODE_GATE` does not recover local-patch value while intervening less
  - `LEARNED_CODE_GATE` collapses:
    - near-correct `0 / 56`
    - general-fail `1 / 184`
- Optional follow-ups:
  - `Mistral-7B-Instruct-v0.3` reduced replication: skipped
  - `MGDebugger-lite` subset: skipped
  - reason: the primary coding read is mixed and already sufficient to support a bounded conclusion
- Final interpretation:
  - coding supports the broader late-stage targeted repair framing only partially
  - the validator-rich near-correct pocket is real and is concentrated in boundary/postcondition failures
  - but local patch does not beat full rewrite overall, so this pack should be positioned as appendix / future-work / talk support rather than a new central claim

## 2026-03-23 — Code-Last-R2 registration and estimate

- Started `Code-Last-R2`, the bounded coding-side repair-eligibility clarification pack after `Code-Last`.
- Frozen goal:
  - determine whether the coding read becomes cleaner once the slice is restricted to genuinely repair-eligible near-correct failures
- Scope remains:
  - validator-rich function-level coding only
  - `EvalPlus` / `HumanEval+` / `MBPP+`
  - not repo-level APR or vulnerability repair
- Execution-path decision before heavy runs:
  - reuse the frozen corrected `Qwen` `Code-Last` direct and repair outputs for strict-slice projection
  - do not rerun identical `Qwen` generations
  - only launch a fresh GPU-heavy run if the strict-slice `Qwen` read is promising enough to justify optional `Mistral`
- Strict slice calibration from frozen direct outputs:
  - `K=1` and `K=2` exact public-pass / extended-fail slices were too small
  - `K=8` is the smallest threshold yielding a double-digit exact slice while remaining entirely boundary-dominated
- Pre-registered `Code-Last-R2` estimate written to `reports/code_last_r2_plan.md`:
  - stricter slice construction: `1–2h`
  - primary Qwen rerun on repair-eligible slices: `3–5h`
  - optional Mistral reduced replication: `2–4h`
  - analysis / figures / memo: `1–2h`
  - total expected end-to-end: `5–9h`
  - with Mistral support: `7–12h`
- Execution-adjusted working estimate from the reuse decision:
  - `Qwen` projection + strict-slice reporting: `0.5–1.0h`
  - optional fresh `Mistral` reduced replication: `2–4h`
  - synthesis / figures / memo: `1–2h`
- practical total from this point:
    - without Mistral: `2–4h`
    - with Mistral: `4–7h`

## 2026-03-23 — Code-Last-R2 final read

- `Code-Last-R2` completed with:
  - frozen `Qwen-7B` projection/replay
  - fresh reduced `Mistral-7B` replication
- Final frozen strict rule:
  - exact public-pass / extended-fail
  - `extended_fail_count <= 8`
  - exclude `syntax_or_runtime`
  - exclude `api_or_signature_mismatch`
  - exclude `broad_algorithmic_failure`
- `Qwen-7B` strict read:
  - strict slice `n = 13`
  - all failures are `boundary_or_off_by_one`
  - `LOCAL_TEST_GUIDED_PATCH = 3 / 13 = 0.2308`
  - `FULL_REWRITE_FROM_FAILURE = 2 / 13 = 0.1538`
  - `HumanEval+` carries the strict positive direction:
    - `LOCAL = 0.6`
    - `REWRITE = 0.4`
  - `MBPP+` strict remains flat at `0`
- `Qwen-7B` relaxed near-correct remains mixed:
  - `LOCAL = 9 / 56 = 0.1607`
  - `REWRITE = 9 / 56 = 0.1607`
- `Mistral-7B` direct slice geometry:
  - exact public-pass / extended-fail `= 28`
  - relaxed near-correct `= 46`
  - frozen strict slice after exclusions `= 4`
  - strict slice composition:
    - all `MBPP`
    - `3` `boundary_or_off_by_one`
    - `1` `return_or_postcondition`
- `Mistral-7B` reduced repair outcomes:
  - strict:
    - `LOCAL = 0 / 4 = 0.0`
    - `REWRITE = 1 / 4 = 0.25`
  - relaxed:
    - `LOCAL = 2 / 46 = 0.0435`
    - `REWRITE = 5 / 46 = 0.1087`
- Runtime:
  - `Mistral` direct generation + evaluation wall-clock: `853s` (`14.2m`)
  - `Mistral` repair generation + evaluation wall-clock: `336s` (`5.6m`)
- GPU monitoring:
  - `Mistral` direct `dmon` `sm` active mean: `82.46`
  - strict repair `sm` active mean is low (`47.12`) because the slice is only `4` tasks, but the active generation burst reached `84–87%`
  - relaxed repair `sm` active mean: `86.13`
- Final read:
  - coding support becomes cleaner on the strict repair-eligible `Qwen` slice
  - the broader transfer remains bounded and family/slice-sensitive
  - the most defensible coding-side analogue is boundary-heavy localizable failure pockets rather than return/postcondition-only repair or universal local-patch superiority

## 2026-03-23 — Code-Last-R3 registration and estimate

- Started `Code-Last-R3`, the bounded HumanEval+-focused coding clarification pack after `Code-Last-R2`.
- Frozen goal:
  - determine whether the positive coding-side signal from `Code-Last-R2` was real but underpowered because the strict slice was too small
  - enlarge the HumanEval+ repair-eligible pocket without broadening the task family
  - test whether broader localized patching on boundary-heavy near-correct code is the cleanest coding analog of late-stage targeted repair
- Scope remains:
  - validator-rich function-level coding only
  - `HumanEval+` as the primary surface
  - `MBPP+` only as optional contrast/support
  - not repo-level APR or vulnerability repair
- Pre-registered `Code-Last-R3` design written to `reports/code_last_r3_plan.md`:
  - `8` completions per HumanEval+ task
  - temperature `0.8`
  - top-p `0.95`
  - fixed 4-way sharding
  - strict rule uses exact public-pass / extended-fail, `extended_fail_count <= 8`, excludes runtime/API/broad failures, and requires boundary or return failure type
- Prompt-level initial estimate written before heavy runs:
  - HumanEval+ multi-sample completion bank: `3–5h`
  - strict slice construction + repair runs: `2–4h`
  - optional Mistral reduced replication: `2–4h`
  - analysis / figures / memo: `1–2h`
  - total expected end-to-end: `6–10h`
  - with Mistral support: `8–13h`
- Execution-adjusted working estimate from prior throughput:
  - Qwen HumanEval+ completion bank generation + evaluation: `0.5–1.5h`
  - strict / relaxed / contrast repair pack: `1.0–2.5h`
  - reporting / synthesis: `1.0–2.0h`
  - practical Qwen-only total from this point: `2.5–6.0h`
- First-hour runtime update:
  - actual `Qwen` HumanEval+ direct generation + evaluation wall-clock: `529s` (`8.8m`)
  - the pre-run direct estimate was too conservative by well over `25%`
  - updated remaining estimate after direct completion:
    - relaxed/contrast repair pack remainder: `20–45m`
    - analysis / figures / memo: `45–90m`
    - practical remaining total from that checkpoint: `1.0–2.25h`
- Contrast recovery update:
  - the original `qwen7b_repairs_20260323a` run completed strict and relaxed surfaces but exited before contrast evaluation and final reporting were closed
  - strict and relaxed outputs remain usable and frozen; only the missing HumanEval+ broad-fail contrast surface needs to be re-collected/evaluated in a fresh result root
  - execution estimate before the recovery run:
    - contrast generation rerun: `8–15m`
    - contrast evaluation: `10–20m`
    - final aggregation / figures / memo / README closeout: `20–40m`
    - practical remaining total from this checkpoint: `38–75m`
- Final `Code-Last-R3` read:
  - direct HumanEval+ multi-sample bank:
    - `1312` completions over `164` tasks
    - exact public-pass / extended-fail completions: `48`
    - relaxed near-correct completions: `120`
    - strict repair-eligible completions: `12`
    - strict repair-eligible task count: `3`
  - strict slice composition:
    - `boundary_or_off_by_one = 12 / 12`
  - strict HumanEval+ outcomes:
    - `LOCAL_TEST_GUIDED_PATCH = 0.5000`
    - `FULL_REWRITE_FROM_FAILURE = 0.3333`
    - completion-level local-minus-rewrite: `+0.1647 [0.0000, 0.4167]`
    - task-clustered local-minus-rewrite: `+0.1111 [0.0000, 0.3333]`
  - relaxed HumanEval+ outcomes:
    - `LOCAL_TEST_GUIDED_PATCH = 0.2583`
    - `FULL_REWRITE_FROM_FAILURE = 0.2833`
  - broad-fail contrast outcomes:
    - `LOCAL_TEST_GUIDED_PATCH = 0.3100`
    - `FULL_REWRITE_FROM_FAILURE = 0.4300`
    - `BOUNDARY_PATCH = 0.4600`
  - interpretation:
    - coding support is cleaner inside the strict HumanEval+ repair-eligible boundary pocket
    - the best coding analog is broader localized repair on boundary-heavy near-correct code
    - this does not support universal local-patch superiority across coding failures
- Actual runtime notes:
  - `Qwen` HumanEval+ direct generation + evaluation: `529s` (`8.8m`)
  - contrast recovery generation + evaluation: `341s` (`5.7m`)
- Optional follow-up decision:
  - skip `Mistral-7B` reduced replication, `MBPP+` contrast rerun, and `MGDebugger-lite`
  - reason: the strict HumanEval+ signal remains positive but underpowered at only `3` tasks, so the expected information gain from expansion is low relative to execution cost

## 2026-03-23 — Code-Last-R4 registration and estimate

- Started `Code-Last-R4`, the bounded high-power HumanEval+-focused coding lock attempt after `Code-Last-R3`.
- Frozen goal:
  - enlarge the HumanEval+ repair-eligible boundary-heavy pocket enough to test task-level local-over-rewrite evidence
  - determine whether broader localized patching remains the cleanest coding analog of late-stage targeted repair
  - determine whether prior mixed coding reads were mainly underpowered strict slices plus MBPP contamination
- Scope remains:
  - `HumanEval+` primary only
  - `MBPP+` contrast/support only
  - function-level validator-rich coding only
  - not repo-level APR or vulnerability repair
- Pre-registered `Code-Last-R4` design written to `reports/code_last_r4_plan.md`:
  - initial bank: `32` completions/task over `164` HumanEval+ tasks (`5248` completions)
  - frozen escalation rule:
    - escalate by the pre-registered extra `32` completions/task if Tier1 task count `< 15` or Tier2 task count `< 25`
    - stop expansion after `64` completions/task and report intrinsic smallness if Tier1 task count remains `< 15`
  - strict tiers:
    - Tier1 `extended_fail_count <= 2`
    - Tier2 `extended_fail_count <= 4`
    - Tier3 `extended_fail_count <= 8`
- Prompt-level runtime estimate written before heavy runs:
  - large HumanEval+ completion bank: `4–6h`
  - strict / relaxed / contrast slice construction: `2–4h`
  - primary Qwen repair runs: `3–5h`
  - optional Mistral reduced rerun: `2–4h`
  - analysis / figures / memo: `1–2h`
  - total expected end-to-end: `10–17h`
  - with Mistral support: `12–20h`
- Working local estimate from prior throughput:
  - 32-sample direct bank generation + public screen: `25–45m`
  - exact-pass / relaxed extended evaluation and tier construction: `20–50m`
  - Qwen repair runs on Tier1/Tier2/Tier3/relaxed/contrast: `30–75m`
  - reporting / figures / memo: `30–60m`
  - practical Qwen-only total if no 64-sample escalation is needed: `1.75–3.8h`
  - practical total with 64-sample escalation: `3.5–6.5h`

## 2026-03-23 — Code-Last-R4 Qwen completion-bank and strict-tier result

- Completed the pre-registered 32-sample HumanEval+ bank and the mandated 64-sample escalation:
  - bank32 generation runtime: `1019s`
  - bank64extra generation runtime: `1050s`
- Final Qwen bank geometry:
  - total completions: `10496`
  - exact public-pass: `7096` completions / `140` tasks
  - Tier1 / Tier2 / Tier3 from the frozen 64-sample bank:
    - `43 / 5`
    - `193 / 8`
    - `205 / 11`
- Initial strict multi-surface repair sweep left a small set of strict question ids uncovered.
- Ran a strict top-off repair rerun before finalization:
  - strict+contrast repair generation runtime: `789s`
  - relaxed repair generation runtime: `633s`
  - strict top-off repair generation runtime: `31s`
- Final top-off-inclusive Qwen strict evaluation:
  - Tier1: `46` completions / `5` task clusters
  - Tier2: `203` completions / `8` task clusters
  - Tier3: `215` completions / `11` task clusters
- Final Qwen read:
  - Tier1 local vs rewrite:
    - completion-level `0.2174` vs `0.1087`
    - task-clustered delta `+0.2000 [0.0000, 0.4000]`
  - Tier2 local vs rewrite:
    - completion-level `0.4828` vs `0.4236`
    - task-clustered delta `+0.1014 [0.0139, 0.2264]`
  - Tier3 local vs rewrite:
    - completion-level `0.4651` vs `0.4093`
    - task-clustered delta `+0.0737 [0.0000, 0.1728]`
  - relaxed near-correct remains mixed:
    - task-clustered delta `-0.0548 [-0.1733, 0.0595]`
  - broad-fail contrast remains negative for local patch:
    - task-clustered delta `-0.2293 [-0.3310, -0.1311]`
- Mechanism read sharpened:
  - strict tiers remain overwhelmingly boundary-dominated
  - broader localized patching is much stronger than `BOUNDARY_PATCH` or `RETURN_POSTCOND_PATCH`
  - coding-side transfer is now cleaner on HumanEval+ strict slices, but still bounded

## 2026-03-23 — Code-Last-R4 optional Mistral reduced replication

- Because Qwen Tier2 produced a task-clustered positive result, ran the optional reduced Mistral branch on the Qwen Tier2 task union only.
- Reduced Mistral setup:
  - `8` HumanEval tasks
  - `64` completions/task
  - total direct bank size: `512`
- Measured generation runtimes:
  - Mistral reduced direct bank: `156s`
  - Mistral reduced strict repair generation: `112s`
- Reduced Mistral geometry:
  - exact public-pass: `151` completions / `6` tasks
  - Tier1: `12` completions / `1` task
  - Tier2: `22` completions / `2` tasks
  - Tier3: `31` completions / `3` tasks
- Reduced Mistral outcome:
  - Tier1 all methods `0.0000`
  - Tier2:
    - `FULL_REWRITE_FROM_FAILURE = 0.1818`
    - `LOCAL_TEST_GUIDED_PATCH = 0.0455`
    - task-clustered delta `LOCAL - REWRITE = -0.2143 [-0.4286, 0.0000]`
- Final `Code-Last-R4` reading:
  - coding transfer is now cleaner on Qwen HumanEval strict slices
  - the cleanest coding analog is broader localized patching on boundary-heavy near-correct code
  - this does not extend to a robust cross-family coding claim

## 2026-03-24 — LACE-FULL launch estimate and scope freeze

- Starting `LACE-FULL` as a bounded full-scale output-constraint expansion pack.
- Frozen target surfaces:
  - full screened `IFEval`
  - full `IFBench`
- Required families:
  - `Qwen/Qwen2.5-7B-Instruct`
  - `mistralai/Mistral-7B-Instruct-v0.3`
- Optional stronger-scale path:
  - `Qwen/Qwen2.5-14B-Instruct`
  - only if the full `Qwen` + `Mistral` read is already strong and runtime remains comfortable
- Prompt-registered wall-clock estimate:
  - full `Qwen` format pack: `5–8h`
  - full `Mistral` format pack: `5–8h`
  - optional `Qwen-14B` scale pack: `4–6h`
  - analysis / figures / memo: `1–2h`
  - total expected end-to-end: `10–16h`
  - with `Qwen-14B` support: `14–22h`
- Working local estimate from prior format throughput:
  - full `Qwen` screened `IFEval`: `35–55m`
  - full `Qwen` `IFBench`: `25–45m`
  - full `Mistral` screened `IFEval`: `45–90m`
  - full `Mistral` `IFBench`: `45–90m`
  - analysis / synthesis / plots: `45–120m`
  - practical Qwen + Mistral total if runner stability matches earlier branches: `4–7.5h`
- Reference positioning for this phase:
  - `IFEval` and `IFBench` are direct benchmark anchors
  - `Decoupling Task-Solving and Output Formatting in LLM Generation` is contextual only
  - `LLMs Are Biased Towards Output Formats!` is contextual only
- Why this pack is the highest-value next step:
  - math is already locked
  - coding stayed appendix-level and underpowered cross-family
  - validator-rich output-constraint tasks are already the cleanest non-math support and now justify full-volume reinforcement

## 2026-03-24 — LACE-FULL full Qwen + Mistral completion and Qwen-14B launch decision

- Full `Qwen-7B` run completed on the frozen full surfaces:
  - screened `IFEval` shards: `96 / 95 / 95 / 95`
  - `IFBench` shards: `75 / 75 / 75 / 75`
- Full `Mistral-7B` run completed on the same frozen surfaces:
  - screened `IFEval` shards: `96 / 95 / 95 / 95`
  - `IFBench` shards: `75 / 75 / 75 / 75`
- Measured wall-clock observed so far:
  - `Qwen-7B` IFBench completion after restart/skip path: `14m46.615s`
  - `Mistral-7B` full run: `53m35.596s`
- Full-scale read before scale add-on:
  - `Qwen` screened `IFEval`: `SIMPLE_BEST_GATE - ALWAYS_FULL_REWRITE = +0.1556 [+0.0922, +0.2270]`
  - `Qwen` `IFBench`: `+0.1452 [+0.0680, +0.2330]`
  - `Mistral` screened `IFEval`: `SIMPLE_BEST_GATE_TRANSFER - ALWAYS_FULL_REWRITE = +0.1130 [+0.0426, +0.1773]`
  - `Mistral` `IFBench`: `+0.0686 [+0.0000, +0.1359]`
- Revised practical estimate after the completed 7B runs:
  - full `Qwen-14B` scale pack in `4bit` over `4` GPUs should be treated as roughly `60–120m` generation time plus `30–90m` analysis / memo closure
  - practical remaining end-to-end estimate before final closeout: `1.5–3.5h`
- Decision:
  - the optional `Qwen-14B` phase is now justified and launched because:
    - the `Qwen + Mistral` read is already strong enough
    - scale is the last unresolved reviewer-facing uncertainty inside the pre-registered ladder

## 2026-03-24 — LACE-FULL final full-scale read

- Full `Qwen-14B` scale pack completed on the same frozen surfaces.
- Captured wall-clock for the optional scale run:
  - `Qwen-14B` full pack: `82m11.658s`
- Full-scale headline numbers:
  - `Qwen-7B`
    - screened `IFEval`: `SIMPLE_BEST_GATE - ALWAYS_FULL_REWRITE = +0.1556 [+0.0922, +0.2270]`
    - `IFBench`: `+0.1452 [+0.0680, +0.2330]`
  - `Mistral-7B`
    - screened `IFEval`: `SIMPLE_BEST_GATE_TRANSFER - ALWAYS_FULL_REWRITE = +0.1130 [+0.0426, +0.1773]`
    - `IFBench`: `+0.0686 [+0.0000, +0.1359]`
  - `Qwen-14B`
    - screened `IFEval`: `SIMPLE_BEST_GATE - ALWAYS_FULL_REWRITE = +0.1561 [+0.0922, +0.2199]`
    - `IFBench`: `+0.0472 [-0.0291, +0.1262]`
- Overall utility summary:
  - `Qwen-7B`: `SIMPLE_BEST_GATE = 0.623`, `LEARNED_GATE = 0.549`, `REWRITE = 0.471`
  - `Mistral-7B`: `SIMPLE_BEST_GATE_TRANSFER = 0.459`, `LEARNED_GATE_TRANSFER = 0.402`, `REWRITE = 0.365`
  - `Qwen-14B`: `SIMPLE_BEST_GATE = 0.664`, `LEARNED_GATE = 0.635`, `REWRITE = 0.553`
- Constraint-type read:
  - local repair remains strongest on structural / keyword / multi-part buckets
  - `ordering_or_position` is the main category where `ALWAYS_SOLVE_THEN_FORMAT` can still dominate
  - `IFBench` punctuation/count micro-buckets remain brittle and sparse
- Runtime read versus the pre-registered estimate:
  - practical local runtime was much shorter than the prompt-registered `10–16h` envelope
  - observed full-run wall clocks were on the order of tens of minutes to low hours rather than half-day scale
- Final research conclusion:
  - output-constraint is now the strongest non-math empirical pillar in the repo
  - full screened `IFEval` is robust across family and scale
  - full `IFBench` stays positive on `Qwen-7B` and `Mistral-7B`, then compresses at `Qwen-14B`

## 2026-03-24 — UNIFY-FULL launch estimate and scope freeze

- Starting `UNIFY-FULL` as a bounded cross-domain unification pack over frozen math and format traces.
- Required families:
  - `Qwen/Qwen2.5-7B-Instruct`
  - `mistralai/Mistral-7B-Instruct-v0.3`
- Optional scale family:
  - `Qwen/Qwen2.5-14B-Instruct`
  - run only if the `Qwen-7B + Mistral-7B` unified read is already strong and runtime remains comfortable
- Prompt-registered wall-clock estimate:
  - pooled split construction and feature alignment: `1–2h`
  - `Qwen-7B` unified policy run: `3–4h`
  - `Mistral-7B` unified policy run: `3–4h`
  - optional `Qwen-14B` scale run: `2–4h`
  - analysis / figures / memo: `1–2h`
  - total expected end-to-end: `8–12h`
  - with `Qwen-14B`: `10–16h`
- Practical local estimate for the current repo state:
  - this pack reuses frozen per-example traces and does not need fresh generation collection
  - expected practical wall-clock:
    - `Qwen-7B` pooled analysis: `10–20m`
    - `Mistral-7B` pooled analysis: `10–20m`
    - optional `Qwen-14B` pooled analysis: `10–20m`
    - synthesis / plots / memo / tests: `20–40m`
    - practical end-to-end with `Qwen-14B`: `50–100m`
- Frozen action mapping entered into this phase:
  - math local repair will be the postprocess-centered frozen primitive
  - format local repair will be the frozen solve-then-format executor
  - the action abstraction is `NO_INTERVENTION / LOCAL_REPAIR / GLOBAL_REWRITE_OR_RESTART`

## 2026-03-24 — UNIFY-FULL final cross-domain read

- `UNIFY-FULL` completed as a pooled policy analysis over frozen math and output-constraint traces.
- No fresh generation collection was needed, so there was no honest GPU-heavy phase to saturate; this pack was CPU-side analysis only.
- Observed local wall-clock for the end-to-end `unify_full_make_reports.py` run was about `97s`, well below the prompt-registered `8–12h` envelope because all per-example traces were already frozen.
- Main overall pooled-vs-rewrite results:
  - `Qwen-7B`: `POOLED_RULE_BEST - ALWAYS_REWRITE_OR_RESTART = +0.2176 [+0.1799, +0.2578]`
  - `Mistral-7B`: `+0.1694 [+0.1300, +0.2115]`
  - `Qwen-14B`: `+0.1084 [+0.0694, +0.1458]`
- Module-level read:
  - `Qwen-7B`:
    - math overall `+0.2943 [+0.2351, +0.3512]`
    - format overall `+0.1120 [+0.0661, +0.1612]`
  - `Mistral-7B`:
    - math overall `+0.2676 [+0.2160, +0.3208]`
    - format overall `+0.0833 [+0.0420, +0.1245]`
  - `Qwen-14B`:
    - math overall `+0.1306 [+0.0933, +0.1697]`
    - format overall `+0.0911 [+0.0468, +0.1379]`
- Best shared-action policy by family:
  - `Qwen-7B`: `FORMAT_TUNED_RULE = 0.706`, with `POOLED_RULE_BEST` exactly tied
  - `Mistral-7B`: `FORMAT_TUNED_RULE = 0.432`, with `POOLED_RULE_BEST = 0.427`
  - `Qwen-14B`: `FORMAT_TUNED_RULE = 0.773`, with `POOLED_RULE_BEST` exactly tied
- Transfer asymmetry remained informative rather than fatal:
  - math-tuned rule on format stayed above rewrite on every family
  - format-tuned rule on math was often very strong, which supports a genuinely shared late-stage geometry rather than two disconnected stories
- Failure alignment remained strongest in `final_requirement_realization`, which links:
  - math late target/postprocess errors
  - format constraint-realization failures
- Final interpretation:
  - the paper can now present math and validator-rich output-constraint tasks as two manifestations of a shared late-stage targeted-repair problem
  - the safest wording is still that pooled simple rules stay close to domain-tuned rules, not that one universal rule strictly dominates everywhere

## 2026-03-26 - UNIFY-LIVE-FULL round progress checkpoint

- Wrote `/workspace/project/reports/unify_live_full_round_progress_report.md` to record the current round status.
- Fresh prospective full-bank collection is complete on:
  - `Qwen-7B`
  - `Mistral-7B`
- `Qwen-14B` prospective collection was started on the stable `4bit` path but stopped early by user instruction before any shard completed.
- The current round therefore locks fresh online evidence on the two required `7B` families, but does not justify a prospective `14B` scale conclusion yet.

## 2026-03-26 - UNIFY-LIVE-FULL-R2 launch registration

- Starting `UNIFY-LIVE-FULL-R2` as the main-volume completion and integrity-lock phase after the live progress checkpoint.
- R2 keeps all prior math / format / unification branches frozen and adds only:
  - fresh-bank integrity auditing
  - pooled-vs-domain-specific prospective policy evaluation
  - bounded `Qwen-14B` completion attempts if stable
  - paper-facing synthesis across math + output-constraint
- Registered wall-clock estimate before heavy R2 work:
  - integrity audit + shard repair if needed: `1–3h`
  - `Qwen-7B` policy fitting / evaluation: `2–4h`
  - `Mistral-7B` policy fitting / evaluation: `2–4h`
  - `Qwen-14B` full prospective completion: `14–24h`
  - `Qwen-14B` policy fitting / evaluation: `2–4h`
  - optional robustness reruns if needed: `2–4h`
  - final synthesis / figures / memo: `2–4h`
  - total expected end-to-end: `23–43h`
- Frozen R2 action mapping:
  - math local repair -> `GRANITE_POSTPROCESS_ONLY_PATCH`
  - format local repair -> `solve_then_format`
  - shared action abstraction -> `NO_INTERVENTION / LOCAL_REPAIR / GLOBAL_REWRITE_OR_RESTART`
- Frozen R2 split seeds:
  - `13`
  - `29`
  - `47`
- R2 workspace namespaces are created under:
  - `/workspace/project/results/unify_live_full_r2_*`
  - `/workspace/project/tables/unify_live_full_r2`
  - `/workspace/project/figures/unify_live_full_r2`
  - `/workspace/project/reports/unify_live_full_r2_*.md`

## 2026-03-27 - Qwen-14B prospective completion lock

- Resumed the stalled `Qwen-14B` R2 run at `/workspace/project/results/unify_live_full_r2_qwen14b/qwen14b_attempt2_20260326b` after confirming the bank had stopped at incomplete replay coverage with all GPUs idle.
- Restarted only the missing shards by relaunching the same `8`-way / dual-slot runner against the existing run root; the collectors safely rewrote incomplete shard `per_example.jsonl` files instead of appending duplicates.
- The resumed run completed all remaining phases and now reaches full prospective coverage:
  - `math_raw`: `1998/1998`
  - `math_replay`: `1998/1998`
  - `format`: `681/681`
  - surfaces:
    - `cluster-hard`: `1515/1515`
    - `generic-hard`: `483/483`
    - screened `IFEval`: `381/381`
    - `IFBench`: `300/300`
- Final completion markers on the active root are now present for all `48/48` shard directories, and `runtime_end_s.txt` was written at `2026-03-27T08:40:46Z`.
- The end-to-end elapsed wall clock recorded in `runtime_s.txt` is `109964s`; this includes the earlier stalled interval before the resumed completion push on `2026-03-27`.
- During the resumed heavy generation windows the corrected `8`-way + dual-slot path again sustained near-`100%` GPU utilization with roughly `22-22.7 GB` used per `24 GB` GPU.
