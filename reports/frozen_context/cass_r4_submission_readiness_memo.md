# CASS-R4 Submission Readiness Memo

## Verdict

Top-tier main-track submission is now justified.

Why:

- the frozen `CASS` lock against `OPERATOR_SCHEMA_TO_CODE_BASE` on the preregistered primary cluster-hard surface remains intact in this reinforcement phase
- the stronger-fidelity `PRISM` comparator still trails `CASS` on the primary surface
- the stronger-fidelity `F1` comparator improves but still trails `CASS` on the primary surface and does not reverse the bridge-slice reading
- the reduced second-model check preserves the directional `CASS` advantage

Scope:

- the paper should still be framed around **cluster-hard arithmetic** and **conservative target/postprocess-centered sparse schema surgery**
- the bridge slice should be presented as a boundary check, not as a new primary claim surface

- primary cluster-hard `CASS - OPERATOR_SCHEMA`: `+0.0207 [0.0007, 0.0422]`
- primary cluster-hard `CASS - PRISM_HIGH_FIDELITY`: `+0.0335 [0.0132, 0.0548]`
- primary cluster-hard `CASS - F1_HIGH_FIDELITY`: `+0.0880 [0.0614, 0.1155]`
- bridge-slice `CASS - F1_HIGH_FIDELITY`: `+0.0543 [-0.0200, 0.1300]`
- secondary-model cluster-hard `CASS - OPERATOR_SCHEMA`: `+0.0629 [0.0333, 0.0967]`

- Comparator caveat:
  - `PRISM_HIGH_FIDELITY` is a stronger-faithfulness adaptation over the official PRISM design axes, not an official reproduction.
- External-validity caveat:
  - the second-model check is reduced-scale, Qwen-family-only, and its absolute accuracy level is much lower than the primary model.
- Benchmark-alignment caveat:
  - the F1 bridge slice is a proxy alignment surface rather than the exact original benchmark family.

## Reviewer-facing reading

- `PRISM` fairness concern:
  - addressed well enough for submission
  - stronger fidelity did not rescue the comparator on the primary claim surface
- `F1` fairness concern:
  - addressed well enough for submission
  - a more equation-faithful path improved `F1` but did not overturn the main result
- model-diversity concern:
  - addressed narrowly but honestly
  - use it as a reduced robustness check, not as a broad multi-family generalization claim

## Primary summary

| surface              | model_name               | method                       |    n |   accuracy |   repair_rate |   corruption_rate |   net_gain |   avg_latency_s |
|:---------------------|:-------------------------|:-----------------------------|-----:|-----------:|--------------:|------------------:|-----------:|----------------:|
| hard_cluster_main_r2 | Qwen/Qwen2.5-7B-Instruct | RAW_PYTHON                   | 1515 |   0.70495  |      0.462046 |        0.0224422  |   0.439604 |         1.36086 |
| hard_cluster_main_r2 | Qwen/Qwen2.5-7B-Instruct | OPERATOR_SCHEMA_TO_CODE_BASE | 1515 |   0.726073 |      0.489769 |        0.0290429  |   0.460726 |         1.88746 |
| hard_cluster_main_r2 | Qwen/Qwen2.5-7B-Instruct | CASS_CONSERVATIVE_GATE       | 1515 |   0.746535 |      0.50297  |        0.0217822  |   0.481188 |         6.83312 |
| hard_cluster_main_r2 | Qwen/Qwen2.5-7B-Instruct | PRISM_HIGH_FIDELITY          | 1515 |   0.712871 |      0.456106 |        0.00858086 |   0.447525 |        11.1207  |
| hard_cluster_main_r2 | Qwen/Qwen2.5-7B-Instruct | F1_HIGH_FIDELITY             | 1515 |   0.658746 |      0.453465 |        0.060066   |   0.393399 |         3.87368 |
