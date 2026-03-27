# CASS-R2 Main Report

## Executive Summary

- primary cluster-hard best method: `TEACHER_PATCHED_BASELINE` at `0.773333`
- best frozen CASS variant on cluster-hard: `CASS_CONSERVATIVE_GATE` at `0.748750`
- generic-hard best method: `CASS_CONSERVATIVE_GATE` at `0.783333`

## Summary

| dataset     | surface              | method                                  |   n |   accuracy |   repair_rate |   corruption_rate |   net_gain |   avg_latency_s |
|:------------|:---------------------|:----------------------------------------|----:|-----------:|--------------:|------------------:|-----------:|----------------:|
| gsm8k_train | hard_cluster_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 800 |   0.705    |      0.47125  |         0.02      |   0.45125  |         6.47856 |
| gsm8k_train | hard_cluster_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               | 800 |   0.71375  |      0.48875  |         0.02875   |   0.46     |         4.82576 |
| gsm8k_train | hard_cluster_main_r2 | CASS_CONSERVATIVE_GATE                  | 800 |   0.74875  |      0.5175   |         0.0225    |   0.495    |         6.85791 |
| gsm8k_train | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           | 800 |   0.72125  |      0.495    |         0.0275    |   0.4675   |         4.32411 |
| gsm8k_train | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 800 |   0.74875  |      0.5175   |         0.0225    |   0.495    |         6.85791 |
| gsm8k_train | hard_cluster_main_r2 | F1_LITE                                 | 800 |   0.6175   |      0.42     |         0.05625   |   0.36375  |         2.11644 |
| gsm8k_train | hard_cluster_main_r2 | KEEP                                    | 800 |   0.25375  |      0        |         0         |   0        |         0       |
| gsm8k_train | hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            | 800 |   0.73     |      0.50125  |         0.025     |   0.47625  |         1.87343 |
| gsm8k_train | hard_cluster_main_r2 | PRISM_LITE                              | 800 |   0.6975   |      0.47     |         0.02625   |   0.44375  |         1.78061 |
| gsm8k_train | hard_cluster_main_r2 | RAW_PYTHON                              | 800 |   0.6975   |      0.47     |         0.02625   |   0.44375  |         1.3522  |
| gsm8k_train | hard_cluster_main_r2 | TEACHER_PATCHED_BASELINE                |  75 |   0.773333 |      0.533333 |         0.0533333 |   0.48     |         1.76611 |
| gsm8k_train | hard_cluster_main_r2 | direct_cot                              | 800 |   0.25375  |      0        |         0         |   0        |         1.41261 |
| gsm8k_train | hard_cluster_main_r2 | freeform_fixed1_same                    | 800 |   0.425    |      0.3075   |         0.13625   |   0.17125  |         2.22909 |
| gsm8k_train | hard_cluster_main_r2 | self_refine_1                           | 800 |   0.49375  |      0.3225   |         0.0825    |   0.24     |         2.07226 |
| gsm8k_train | hard_generic_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 300 |   0.693333 |      0.423333 |         0.04      |   0.383333 |         6.56278 |
| gsm8k_train | hard_generic_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               | 300 |   0.743333 |      0.466667 |         0.0333333 |   0.433333 |         4.92826 |
| gsm8k_train | hard_generic_main_r2 | CASS_CONSERVATIVE_GATE                  | 300 |   0.783333 |      0.503333 |         0.03      |   0.473333 |         6.85818 |
| gsm8k_train | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           | 300 |   0.743333 |      0.47     |         0.0366667 |   0.433333 |         4.32374 |
| gsm8k_train | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 300 |   0.783333 |      0.503333 |         0.03      |   0.473333 |         6.85818 |
| gsm8k_train | hard_generic_main_r2 | F1_LITE                                 | 300 |   0.633333 |      0.39     |         0.0666667 |   0.323333 |         2.11902 |
| gsm8k_train | hard_generic_main_r2 | KEEP                                    | 300 |   0.31     |      0        |         0         |   0        |         0       |
| gsm8k_train | hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            | 300 |   0.736667 |      0.463333 |         0.0366667 |   0.426667 |         1.88244 |
| gsm8k_train | hard_generic_main_r2 | PRISM_LITE                              | 300 |   0.716667 |      0.44     |         0.0333333 |   0.406667 |         1.82199 |
| gsm8k_train | hard_generic_main_r2 | RAW_PYTHON                              | 300 |   0.716667 |      0.44     |         0.0333333 |   0.406667 |         1.39429 |
| gsm8k_train | hard_generic_main_r2 | direct_cot                              | 300 |   0.31     |      0        |         0         |   0        |         1.40016 |
| gsm8k_train | hard_generic_main_r2 | freeform_fixed1_same                    | 300 |   0.423333 |      0.28     |         0.166667  |   0.113333 |         2.25723 |
| gsm8k_train | hard_generic_main_r2 | self_refine_1                           | 300 |   0.456667 |      0.256667 |         0.11      |   0.146667 |         2.11628 |