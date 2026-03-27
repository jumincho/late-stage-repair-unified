# LACE-R2 Format Cross-Family Report

## Setup

- Cross-family model: `mistralai/Mistral-7B-Instruct-v0.3`.
- Within-model split: stable hash split with `35%` eval (`train=240`, `eval=141`).
- Simple family chosen from Module A: `SIMPLE_THRESHOLDED_TREE`.
- Smallest viable simple family from Module A: `SIMPLE_2FEATURE_GATE`.
- Human-readable simple rule: if direct validator passes: NO_INTERVENTION; elif failed_instruction_count > 1: GLOBAL_REWRITE; elif keyword-or-no-comma constraint is active: LOCAL_FORMAT_PATCH; else: SOLVE_THEN_FORMAT
- IFBench included: `0`.

## Overall policy read

- `ALWAYS_FULL_REWRITE`: utility `0.518`, intervention `1.000`, false-intervene `0.872`, missed-intervene `0.000`, latency `4.325s`
- `ALWAYS_LOCAL_FORMAT_PATCH`: utility `0.546`, intervention `1.000`, false-intervene `0.844`, missed-intervene `0.000`, latency `4.104s`
- `ALWAYS_SOLVE_THEN_FORMAT`: utility `0.475`, intervention `1.000`, false-intervene `0.780`, missed-intervene `0.000`, latency `6.343s`
- `HEURISTIC_GATE`: utility `0.610`, intervention `0.610`, false-intervene `0.390`, missed-intervene `0.000`, latency `5.850s`
- `LEARNED_GATE_WITHIN`: utility `0.539`, intervention `0.567`, false-intervene `0.418`, missed-intervene `0.021`, latency `4.936s`
- `SIMPLE_BEST_GATE`: utility `0.603`, intervention `0.610`, false-intervene `0.397`, missed-intervene `0.000`, latency `5.384s`
- `ORACLE_POLICY`: utility `0.674`, intervention `0.284`, false-intervene `0.000`, missed-intervene `0.000`, latency `4.537s`

## Surface breakdown

### ifeval_screened

- `ALWAYS_FULL_REWRITE`: utility `0.518`, intervention `1.000`, false-intervene `0.872`, missed-intervene `0.000`
- `ALWAYS_SOLVE_THEN_FORMAT`: utility `0.475`, intervention `1.000`, false-intervene `0.780`, missed-intervene `0.000`
- `HEURISTIC_GATE`: utility `0.610`, intervention `0.610`, false-intervene `0.390`, missed-intervene `0.000`
- `LEARNED_GATE_WITHIN`: utility `0.539`, intervention `0.567`, false-intervene `0.418`, missed-intervene `0.021`
- `SIMPLE_BEST_GATE`: utility `0.603`, intervention `0.610`, false-intervene `0.397`, missed-intervene `0.000`

## Interpretation

- The main cross-family question is whether local repair or gated local repair stays above full rewrite. Here `LEARNED_GATE_WITHIN = 0.539` and `SIMPLE_BEST_GATE = 0.603` versus `ALWAYS_FULL_REWRITE = 0.518`.
- The direct simplicity question is whether the chosen simple rule stays close to the within-model learned gate: `SIMPLE_BEST_GATE = 0.603` vs `LEARNED_GATE_WITHIN = 0.539`.
- The strongest reviewer-facing read here is on validator-rich output-constraint tasks, especially screened `IFEval`; `IFBench` is included when runtime permits because it is harder and more distribution-shifted.