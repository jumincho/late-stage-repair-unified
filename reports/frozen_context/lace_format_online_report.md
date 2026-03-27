# LACE Format Online Report

## Setup

- Train split: frozen `LAST-PACK` format traces.
- Eval split: fresh local rerun under the same screened `IFEval` and `IFBench` surfaces collected for `LACE`.
- Actions:
  - `NO_INTERVENTION`
  - `LOCAL_FORMAT_PATCH`
  - `GLOBAL_REWRITE`
  - `SOLVE_THEN_FORMAT`

## Main read

- `ALWAYS_DIRECT`: utility `0.458`, intervention rate `0.000`, false-intervene `0.000`, missed-intervene `0.204`, mean latency `3.132s`
- `ALWAYS_FULL_REWRITE`: utility `0.505`, intervention rate `1.000`, false-intervene `0.953`, missed-intervene `0.000`, mean latency `3.112s`
- `ALWAYS_LOCAL_FORMAT_PATCH`: utility `0.511`, intervention rate `1.000`, false-intervene `0.947`, missed-intervene `0.000`, mean latency `3.067s`
- `ALWAYS_SOLVE_THEN_FORMAT`: utility `0.557`, intervention rate `1.000`, false-intervene `0.824`, missed-intervene `0.000`, mean latency `3.796s`
- `LOCAL_BEST`: utility `0.653`, intervention rate `1.000`, false-intervene `0.805`, missed-intervene `0.000`, mean latency `3.656s`
- `HEURISTIC_GATE`: utility `0.634`, intervention rate `0.542`, false-intervene `0.366`, missed-intervene `0.000`, mean latency `3.566s`
- `LEARNED_GATE`: utility `0.620`, intervention rate `0.539`, false-intervene `0.377`, missed-intervene `0.000`, mean latency `3.388s`
- `ORACLE_POLICY`: utility `0.662`, intervention rate `0.204`, false-intervene `0.000`, missed-intervene `0.000`, mean latency `3.133s`

## Surface breakdown

### ifeval_screened

- `ALWAYS_FULL_REWRITE`: utility `0.664`, intervention rate `1.000`, false-intervene `0.945`, missed-intervene `0.000`
- `ALWAYS_SOLVE_THEN_FORMAT`: utility `0.690`, intervention rate `1.000`, false-intervene `0.832`, missed-intervene `0.000`
- `LOCAL_BEST`: utility `0.793`, intervention rate `1.000`, false-intervene `0.816`, missed-intervene `0.000`
- `HEURISTIC_GATE`: utility `0.777`, intervention rate `0.391`, false-intervene `0.223`, missed-intervene `0.000`
- `LEARNED_GATE`: utility `0.753`, intervention rate `0.386`, false-intervene `0.241`, missed-intervene `0.000`

### ifbench

- `ALWAYS_FULL_REWRITE`: utility `0.303`, intervention rate `1.000`, false-intervene `0.963`, missed-intervene `0.000`
- `ALWAYS_SOLVE_THEN_FORMAT`: utility `0.387`, intervention rate `1.000`, false-intervene `0.813`, missed-intervene `0.000`
- `LOCAL_BEST`: utility `0.477`, intervention rate `1.000`, false-intervene `0.790`, missed-intervene `0.000`
- `HEURISTIC_GATE`: utility `0.453`, intervention rate `0.733`, false-intervene `0.547`, missed-intervene `0.000`
- `LEARNED_GATE`: utility `0.450`, intervention rate `0.733`, false-intervene `0.550`, missed-intervene `0.000`

## Interpretation

- `LEARNED_GATE` reaches utility `0.620` at intervention rate `0.539`.
- The naive global-rewrite baseline sits at `0.505`; this is the main online comparator for the output-constraint story.
- The local upper frontier on this eval pack is `LOCAL_BEST = 0.653` at intervention rate `1.000`.
- The clearest beyond-math reading remains the same as in `LAST-PACK`: validator-rich output-constraint tasks are the cleanest place where a deployable local-repair gate can be both useful and simple.