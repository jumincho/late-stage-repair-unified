# LACE-R3 IFBench Cross-Family Report

## Setup

- Cross-family model: `mistralai/Mistral-7B-Instruct-v0.3`.
- Fresh IFBench rerun pattern: `/workspace/project/results/lace_r3_format/mistral7b_ifbench_crossfamily_20260318a/ifbench_shard*of04/per_example.jsonl`.
- Within-model split: `train=197`, `eval=103`.
- Primary transferred simple family: `SIMPLE_THRESHOLDED_TREE`.
- Within-tuned simple family: `SIMPLE_THRESHOLDED_TREE`.

## IFBench overall read

- `ALWAYS_DIRECT`: utility `0.117`, intervention `0.000`, false-intervene `0.000`, missed-intervene `0.136`, latency `4.436s`
- `ALWAYS_FULL_REWRITE`: utility `0.155`, intervention `1.000`, false-intervene `0.961`, missed-intervene `0.000`, latency `4.228s`
- `ALWAYS_LOCAL_FORMAT_PATCH`: utility `0.146`, intervention `1.000`, false-intervene `0.971`, missed-intervene `0.000`, latency `4.130s`
- `ALWAYS_SOLVE_THEN_FORMAT`: utility `0.184`, intervention `1.000`, false-intervene `0.903`, missed-intervene `0.000`, latency `5.655s`
- `HEURISTIC_GATE_TRANSFER`: utility `0.214`, intervention `0.883`, false-intervene `0.786`, missed-intervene `0.000`, latency `5.547s`
- `LEARNED_GATE_TRANSFER`: utility `0.204`, intervention `0.883`, false-intervene `0.796`, missed-intervene `0.000`, latency `5.429s`
- `SIMPLE_2FEATURE_GATE_TRANSFER`: utility `0.214`, intervention `0.883`, false-intervene `0.786`, missed-intervene `0.000`, latency `5.547s`
- `SIMPLE_BEST_GATE_TRANSFER`: utility `0.223`, intervention `0.883`, false-intervene `0.777`, missed-intervene `0.000`, latency `5.473s`
- `LEARNED_GATE_WITHIN`: utility `0.194`, intervention `0.777`, false-intervene `0.699`, missed-intervene `0.000`, latency `5.277s`
- `SIMPLE_WITHIN_TUNED`: utility `0.223`, intervention `0.883`, false-intervene `0.777`, missed-intervene `0.000`, latency `5.398s`
- `ORACLE_POLICY`: utility `0.252`, intervention `0.136`, false-intervene `0.000`, missed-intervene `0.000`, latency `4.299s`

## Interpretation

- The main cross-family IFBench question is whether local-repair-over-rewrite survives. Here `SIMPLE_BEST_GATE_TRANSFER = 0.223`, `LEARNED_GATE_WITHIN = 0.194`, and `ALWAYS_FULL_REWRITE = 0.155`.
- The portability question is whether a simple transferred rule stays useful without within-model tuning. Here `SIMPLE_2FEATURE_GATE_TRANSFER = 0.214` versus `LEARNED_GATE_TRANSFER = 0.204`.
- `IFBench` is materially harder than screened `IFEval`: `LEARNED_GATE_WITHIN 0.194` vs `IFEval 0.539`, and `ALWAYS_FULL_REWRITE 0.155` vs `IFEval 0.518`.
- The right read is boundary-sensitive rather than absolute: `IFBench` should be harder, but the pack still succeeds if local repair or gated local repair stays directionally above rewrite.