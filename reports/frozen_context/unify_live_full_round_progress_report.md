# UNIFY-LIVE-FULL Round Progress Report

## Status

- This note records the current round status after completing the required fresh prospective banks on `Qwen-7B` and `Mistral-7B`.
- `Qwen-14B` was stopped early by user instruction before completing the full prospective bank.
- This is a progress report, not the final `UNIFY-LIVE-FULL` synthesis.

## Completed Runs

### Qwen-7B

Run root:
- `/workspace/project/results/unify_live_full_qwen/qwen7b_live_20260324a`

Collected coverage:
- `math_raw`: `1998 / 1998`
- `math_replay`: `1998 / 1998`
- `format`: `681 / 681`

Surface coverage:
- cluster-hard raw: `1515`
- generic-hard raw: `483`
- cluster-hard replay: `1515`
- generic-hard replay: `483`
- screened `IFEval`: `381`
- `IFBench`: `300`

Recorded runtimes:
- `math_cluster_raw_runtime_s.txt`: `19069`
- `math_generic_raw_runtime_s.txt`: `6105`
- `math_cluster_replay_runtime_s.txt`: `3281`
- `math_generic_replay_runtime_s.txt`: `1024`
- `format_ifeval_runtime_s.txt`: `1355`
- `format_ifbench_runtime_s.txt`: `1016`
- `runtime_s.txt`: `31850`

### Mistral-7B

Run root:
- `/workspace/project/results/unify_live_full_mistral/mistral7b_live_20260324a`

Collected coverage:
- `math_raw`: `1998 / 1998`
- `math_replay`: `1998 / 1998`
- `format`: `681 / 681`

Surface coverage:
- cluster-hard raw: `1515`
- generic-hard raw: `483`
- cluster-hard replay: `1515`
- generic-hard replay: `483`
- screened `IFEval`: `381`
- `IFBench`: `300`

Recorded runtimes:
- `math_cluster_raw_runtime_s.txt`: `30237`
- `math_generic_replay_runtime_s.txt`: `1882`
- `format_ifeval_runtime_s.txt`: `1596`
- `format_ifbench_runtime_s.txt`: `1591`
- `runtime_s.txt`: `54725`

## Early-Stopped Run

### Qwen-14B

Run root:
- `/workspace/project/results/unify_live_full_qwen14b/qwen14b_live_20260324a`

State at stop:
- active phase at stop: `math_cluster_raw`
- partial `math_raw`: `47` rows total across `4` shards
- no shard completed

Operational observations:
- the stable local path was the frozen `4bit` configuration
- the run required manual relaunch after an early worker drop without an explicit traceback in the shard logs
- after relaunch, collection resumed but remained much slower than the completed `7B` runs

Reason for stop:
- user-directed early termination
- not enough evidence collected to support a `Qwen-14B` prospective conclusion

## What This Round Already Supports

- Fresh prospective collection is complete on the two required online families:
  - `Qwen-7B`
  - `Mistral-7B`
- Both domains were fully collected on those families:
  - math
  - validator-rich output-constraint tasks
- Therefore this round already secures the main fresh-online evidence on the required `7B` cross-family cells.

## What This Round Does Not Yet Support

- No final prospective policy-fitting result has been written yet.
- No final pooled-vs-domain-specific online evaluation result has been written yet.
- No `Qwen-14B` prospective scale conclusion should be claimed from this round.

## Safest Current Read

- The round successfully locked the fresh prospective data bank for `Qwen-7B` and `Mistral-7B`.
- The scale cell on `Qwen-14B` remains incomplete and should be treated as out of scope for the current round close-out.
- Any final paper-facing claim from this round should therefore be framed as:
  - fresh prospective confirmation on the two required `7B` families is complete
  - the optional `14B` scale check was started but intentionally stopped early
