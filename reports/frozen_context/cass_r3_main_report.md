# CASS-R3 Main Report

## Executive Summary

- best frozen CASS variant on the combined cluster-hard surface: `CASS_CONSERVATIVE_GATE`
- statistically locked vs `RAW_PYTHON` and `OPERATOR_SCHEMA_TO_CODE_BASE`: `1`
- directly favorable to at least one registered comparator: `1`
- cluster-hard accuracy: `0.746535`
- generic-hard best method: `CASS_CONSERVATIVE_GATE` at `0.797101`

## Summary

| dataset     | surface              | method                                  |    n |   accuracy |   repair_rate |   corruption_rate |   net_gain |   avg_latency_s |
|:------------|:---------------------|:----------------------------------------|-----:|-----------:|--------------:|------------------:|-----------:|----------------:|
| gsm8k_train | hard_cluster_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 1515 |   0.716172 |      0.469967 |         0.0191419 |  0.450825  |         6.466   |
| gsm8k_train | hard_cluster_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               | 1515 |   0.731353 |      0.493069 |         0.0270627 |  0.466007  |         4.85073 |
| gsm8k_train | hard_cluster_main_r2 | CASS_CONSERVATIVE_GATE                  | 1515 |   0.746535 |      0.50297  |         0.0217822 |  0.481188  |         6.83312 |
| gsm8k_train | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           | 1515 |   0.735314 |      0.49571  |         0.0257426 |  0.469967  |         4.31073 |
| gsm8k_train | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 1515 |   0.746535 |      0.50297  |         0.0217822 |  0.481188  |         6.83312 |
| gsm8k_train | hard_cluster_main_r2 | F1_LITE                                 | 1515 |   0.6033   |      0.407261 |         0.0693069 |  0.337954  |         2.1126  |
| gsm8k_train | hard_cluster_main_r2 | KEEP                                    | 1515 |   0.265347 |      0        |         0         |  0         |         0       |
| gsm8k_train | hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            | 1515 |   0.726073 |      0.489769 |         0.0290429 |  0.460726  |         1.88746 |
| gsm8k_train | hard_cluster_main_r2 | PRISM_LITE                              | 1515 |   0.70495  |      0.462046 |         0.0224422 |  0.439604  |         1.78818 |
| gsm8k_train | hard_cluster_main_r2 | RAW_PYTHON                              | 1515 |   0.70495  |      0.462046 |         0.0224422 |  0.439604  |         1.36086 |
| gsm8k_train | hard_cluster_main_r2 | TEACHER_PATCHED_BASELINE                |   75 |   0.773333 |      0.533333 |         0.0533333 |  0.48      |         1.76611 |
| gsm8k_train | hard_cluster_main_r2 | direct_cot                              | 1515 |   0.265347 |      0        |         0         |  0         |         1.40641 |
| gsm8k_train | hard_cluster_main_r2 | freeform_fixed1_same                    | 1515 |   0.431023 |      0.29769  |         0.132013  |  0.165677  |         2.24094 |
| gsm8k_train | hard_cluster_main_r2 | self_refine_1                           | 1515 |   0.481188 |      0.30363  |         0.0877888 |  0.215842  |         2.08124 |
| gsm8k_train | hard_generic_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          |  483 |   0.718427 |      0.436853 |         0.0331263 |  0.403727  |         6.49582 |
| gsm8k_train | hard_generic_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |  483 |   0.755694 |      0.469979 |         0.0289855 |  0.440994  |         4.90076 |
| gsm8k_train | hard_generic_main_r2 | CASS_CONSERVATIVE_GATE                  |  483 |   0.797101 |      0.507246 |         0.0248447 |  0.482402  |         6.79276 |
| gsm8k_train | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |  483 |   0.755694 |      0.469979 |         0.0289855 |  0.440994  |         4.24169 |
| gsm8k_train | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |  483 |   0.797101 |      0.507246 |         0.0248447 |  0.482402  |         6.79276 |
| gsm8k_train | hard_generic_main_r2 | F1_LITE                                 |  483 |   0.654244 |      0.391304 |         0.0517598 |  0.339545  |         2.0826  |
| gsm8k_train | hard_generic_main_r2 | KEEP                                    |  483 |   0.3147   |      0        |         0         |  0         |         0       |
| gsm8k_train | hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            |  483 |   0.751553 |      0.467909 |         0.0310559 |  0.436853  |         1.86257 |
| gsm8k_train | hard_generic_main_r2 | PRISM_LITE                              |  483 |   0.73499  |      0.449275 |         0.0289855 |  0.42029   |         1.79189 |
| gsm8k_train | hard_generic_main_r2 | RAW_PYTHON                              |  483 |   0.73499  |      0.449275 |         0.0289855 |  0.42029   |         1.36022 |
| gsm8k_train | hard_generic_main_r2 | direct_cot                              |  483 |   0.3147   |      0        |         0         |  0         |         1.36492 |
| gsm8k_train | hard_generic_main_r2 | freeform_fixed1_same                    |  483 |   0.397516 |      0.256729 |         0.173913  |  0.0828157 |         2.24836 |
| gsm8k_train | hard_generic_main_r2 | self_refine_1                           |  483 |   0.465839 |      0.250518 |         0.0993789 |  0.151139  |         2.11337 |