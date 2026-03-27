# CASS Main Report

## Executive Summary

- Best sparse patch method on cluster-hard: `CASS_CONSERVATIVE_GATE`

## Cluster-hard Summary

| dataset     | surface           | method                                  |   n |   accuracy |   repair_rate |   corruption_rate |   net_gain |   avg_latency_s |
|:------------|:------------------|:----------------------------------------|----:|-----------:|--------------:|------------------:|-----------:|----------------:|
| gsm8k_train | hard_cluster_main | CASS_CONSERVATIVE_GATE                  | 210 |   0.771429 |      0.542857 |         0.0428571 |   0.5      |         6.65377 |
| gsm8k_train | hard_cluster_main | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 210 |   0.771429 |      0.542857 |         0.0428571 |   0.5      |         6.65377 |
| gsm8k_train | hard_cluster_main | CASS_NONROLE_PATCH                      | 210 |   0.761905 |      0.514286 |         0.0238095 |   0.490476 |         3.50094 |
| gsm8k_train | hard_cluster_main | ATLAS_RG_ROLE_REPAIR_ONLY               | 210 |   0.761905 |      0.538095 |         0.047619  |   0.490476 |         4.65351 |
| gsm8k_train | hard_cluster_main | CASS_TARGET_POSTPROCESS_PATCH           | 210 |   0.752381 |      0.52381  |         0.0428571 |   0.480952 |         4.13712 |
| gsm8k_train | hard_cluster_main | RAW_PYTHON                              | 210 |   0.738095 |      0.495238 |         0.0285714 |   0.466667 |         1.30111 |
| gsm8k_train | hard_cluster_main | CASS_CRITICAL_ROLE_PATCH                | 210 |   0.733333 |      0.519048 |         0.0571429 |   0.461905 |         5.19126 |
| gsm8k_train | hard_cluster_main | OPERATOR_SCHEMA_TO_CODE_BASE            | 210 |   0.728571 |      0.504762 |         0.047619  |   0.457143 |         1.79722 |
| gsm8k_train | hard_cluster_main | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 210 |   0.728571 |      0.490476 |         0.0333333 |   0.457143 |         6.28522 |
| gsm8k_train | hard_cluster_main | CASS_ROLE_PATCH                         | 210 |   0.719048 |      0.519048 |         0.0714286 |   0.447619 |         5.83161 |

## Generic-hard Summary

| dataset     | surface           | method                                  |   n |   accuracy |   repair_rate |   corruption_rate |   net_gain |   avg_latency_s |
|:------------|:------------------|:----------------------------------------|----:|-----------:|--------------:|------------------:|-----------:|----------------:|
| gsm8k_train | hard_generic_main | CASS_TARGET_POSTPROCESS_PATCH           | 140 |   0.842857 |      0.464286 |        0.00714286 |   0.457143 |         4.10631 |
| gsm8k_train | hard_generic_main | CASS_CONSERVATIVE_GATE                  | 140 |   0.842857 |      0.492857 |        0.0357143  |   0.457143 |         6.66785 |
| gsm8k_train | hard_generic_main | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 140 |   0.842857 |      0.492857 |        0.0357143  |   0.457143 |         6.66785 |
| gsm8k_train | hard_generic_main | CASS_NONROLE_PATCH                      | 140 |   0.835714 |      0.471429 |        0.0214286  |   0.45     |         3.42604 |
| gsm8k_train | hard_generic_main | CASS_ROLE_PATCH                         | 140 |   0.821429 |      0.464286 |        0.0285714  |   0.435714 |         5.96082 |
| gsm8k_train | hard_generic_main | RAW_PYTHON                              | 140 |   0.814286 |      0.442857 |        0.0142857  |   0.428571 |         1.29968 |
| gsm8k_train | hard_generic_main | ATLAS_RG_ROLE_REPAIR_ONLY               | 140 |   0.814286 |      0.457143 |        0.0285714  |   0.428571 |         4.78825 |
| gsm8k_train | hard_generic_main | CASS_CRITICAL_ROLE_PATCH                | 140 |   0.814286 |      0.457143 |        0.0285714  |   0.428571 |         5.34435 |
| gsm8k_train | hard_generic_main | OPERATOR_SCHEMA_TO_CODE_BASE            | 140 |   0.778571 |      0.428571 |        0.0357143  |   0.392857 |         1.75703 |
| gsm8k_train | hard_generic_main | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 140 |   0.778571 |      0.414286 |        0.0214286  |   0.392857 |         6.47349 |

## Pairwise Comparisons

| surface           | base_method                   | alt_method                              |   base_accuracy |   alt_accuracy |       delta |      ci_low |   ci_high |   mcnemar_p |   n |
|:------------------|:------------------------------|:----------------------------------------|----------------:|---------------:|------------:|------------:|----------:|------------:|----:|
| hard_cluster_main | RAW_PYTHON                    | OPERATOR_SCHEMA_TO_CODE_BASE            |        0.738095 |       0.728571 | -0.00940238 | -0.0619048  | 0.047619  |   0.867939  | 210 |
| hard_cluster_main | RAW_PYTHON                    | ATLAS_FIELDWISE_SCHEMA_TO_CODE          |        0.738095 |       0.728571 | -0.00921905 | -0.0619048  | 0.0428571 |   0.86005   | 210 |
| hard_cluster_main | RAW_PYTHON                    | ATLAS_RG_ROLE_REPAIR_ONLY               |        0.738095 |       0.761905 |  0.0235643  | -0.0380952  | 0.0809524 |   0.511376  | 210 |
| hard_cluster_main | RAW_PYTHON                    | CASS_TARGET_POSTPROCESS_PATCH           |        0.738095 |       0.752381 |  0.0147667  | -0.0428571  | 0.0714286 |   0.735879  | 210 |
| hard_cluster_main | RAW_PYTHON                    | CASS_ROLE_PATCH                         |        0.738095 |       0.719048 | -0.0189619  | -0.0809524  | 0.0380952 |   0.627103  | 210 |
| hard_cluster_main | RAW_PYTHON                    | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |        0.738095 |       0.771429 |  0.0330857  | -0.0190476  | 0.0857143 |   0.296206  | 210 |
| hard_cluster_main | RAW_PYTHON                    | CASS_CRITICAL_ROLE_PATCH                |        0.738095 |       0.733333 | -0.00452381 | -0.0619048  | 0.047619  |   1         | 210 |
| hard_cluster_main | RAW_PYTHON                    | CASS_NONROLE_PATCH                      |        0.738095 |       0.761905 |  0.0239952  | -0.0285714  | 0.0761905 |   0.48685   | 210 |
| hard_cluster_main | OPERATOR_SCHEMA_TO_CODE_BASE  | CASS_TARGET_POSTPROCESS_PATCH           |        0.728571 |       0.752381 |  0.024169   | -0.0285714  | 0.0809524 |   0.49956   | 210 |
| hard_cluster_main | OPERATOR_SCHEMA_TO_CODE_BASE  | CASS_ROLE_PATCH                         |        0.728571 |       0.719048 | -0.00955952 | -0.0619048  | 0.0428571 |   0.864166  | 210 |
| hard_cluster_main | OPERATOR_SCHEMA_TO_CODE_BASE  | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |        0.728571 |       0.771429 |  0.0424881  | -0.00952381 | 0.0952381 |   0.136046  | 210 |
| hard_cluster_main | OPERATOR_SCHEMA_TO_CODE_BASE  | CASS_CRITICAL_ROLE_PATCH                |        0.728571 |       0.733333 |  0.00487857 | -0.052381   | 0.0571429 |   1         | 210 |
| hard_cluster_main | OPERATOR_SCHEMA_TO_CODE_BASE  | CASS_NONROLE_PATCH                      |        0.728571 |       0.761905 |  0.0333976  | -0.0142857  | 0.0857143 |   0.264931  | 210 |
| hard_cluster_main | CASS_ROLE_PATCH               | CASS_TARGET_POSTPROCESS_PATCH           |        0.719048 |       0.752381 |  0.0337286  | -0.0190476  | 0.0857143 |   0.310505  | 210 |
| hard_cluster_main | CASS_ROLE_PATCH               | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |        0.719048 |       0.771429 |  0.0520476  |  0          | 0.104762  |   0.0707555 | 210 |
| hard_cluster_main | CASS_TARGET_POSTPROCESS_PATCH | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |        0.752381 |       0.771429 |  0.018319   | -0.0333333  | 0.0714286 |   0.596615  | 210 |
| hard_generic_main | RAW_PYTHON                    | CASS_TARGET_POSTPROCESS_PATCH           |        0.814286 |       0.842857 |  0.0279964  | -0.0285714  | 0.0857143 |   0.480682  | 140 |
| hard_generic_main | RAW_PYTHON                    | CASS_ROLE_PATCH                         |        0.814286 |       0.821429 |  0.00668571 | -0.0571429  | 0.0714286 |   1         | 140 |
| hard_generic_main | RAW_PYTHON                    | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |        0.814286 |       0.842857 |  0.0287536  | -0.0357143  | 0.0928571 |   0.503445  | 140 |
| hard_generic_main | OPERATOR_SCHEMA_TO_CODE_BASE  | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |        0.778571 |       0.842857 |  0.0650821  |  0          | 0.135714  |   0.0931396 | 140 |

## Replay-controlled Seed Comparison

| surface           | draft_source   | teacher_seed_source                   | action_name                             |   n |   accuracy |   utility_costaware |
|:------------------|:---------------|:--------------------------------------|:----------------------------------------|----:|-----------:|--------------------:|
| hard_cluster_main | fresh          | teacher_seed_gpt5mini_20260315_merged | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 210 |   0.728571 |            0.448138 |
| hard_cluster_main | fresh          | teacher_seed_gpt5mini_20260315_merged | ATLAS_RG_ROLE_REPAIR_ONLY               | 210 |   0.761905 |            0.483764 |
| hard_cluster_main | fresh          | teacher_seed_gpt5mini_20260315_merged | CASS_CRITICAL_ROLE_PATCH                | 210 |   0.733333 |            0.454407 |
| hard_cluster_main | fresh          | teacher_seed_gpt5mini_20260315_merged | CASS_NONROLE_PATCH                      | 210 |   0.761905 |            0.485401 |
| hard_cluster_main | fresh          | teacher_seed_gpt5mini_20260315_merged | CASS_ROLE_PATCH                         | 210 |   0.719048 |            0.439235 |
| hard_cluster_main | fresh          | teacher_seed_gpt5mini_20260315_merged | CASS_TARGET_POSTPROCESS_PATCH           | 210 |   0.752381 |            0.474983 |
| hard_cluster_main | fresh          | teacher_seed_gpt5mini_20260315_merged | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 210 |   0.771429 |            0.490483 |
| hard_cluster_main | frozen         | none                                  | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 210 |   0.728571 |            0.448066 |
| hard_cluster_main | frozen         | none                                  | ATLAS_RG_ROLE_REPAIR_ONLY               | 210 |   0.761905 |            0.48372  |
| hard_cluster_main | frozen         | none                                  | CASS_CRITICAL_ROLE_PATCH                | 210 |   0.757143 |            0.479354 |
| hard_cluster_main | frozen         | none                                  | CASS_NONROLE_PATCH                      | 210 |   0.752381 |            0.476197 |
| hard_cluster_main | frozen         | none                                  | CASS_ROLE_PATCH                         | 210 |   0.742857 |            0.463281 |
| hard_cluster_main | frozen         | none                                  | CASS_TARGET_POSTPROCESS_PATCH           | 210 |   0.733333 |            0.456684 |
| hard_cluster_main | frozen         | none                                  | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 210 |   0.742857 |            0.462188 |

## Held-out Teacher-covered Subset

| dataset     | surface                     | method                                  |   n |   accuracy |   repair_rate |   corruption_rate |   net_gain |   avg_latency_s |
|:------------|:----------------------------|:----------------------------------------|----:|-----------:|--------------:|------------------:|-----------:|----------------:|
| gsm8k_train | hard_cluster_teacher_subset | ATLAS_FIELDWISE_SCHEMA_TO_CODE          |  40 |      0.7   |         0.5   |             0.025 |      0.475 |         6.38139 |
| gsm8k_train | hard_cluster_teacher_subset | ATLAS_RG_ROLE_REPAIR_ONLY               |  40 |      0.775 |         0.575 |             0.025 |      0.55  |         4.69202 |
| gsm8k_train | hard_cluster_teacher_subset | CASS_CRITICAL_ROLE_PATCH                |  40 |      0.675 |         0.5   |             0.05  |      0.45  |         5.36853 |
| gsm8k_train | hard_cluster_teacher_subset | CASS_NONROLE_PATCH                      |  40 |      0.625 |         0.45  |             0.05  |      0.4   |         3.71643 |
| gsm8k_train | hard_cluster_teacher_subset | CASS_ROLE_PATCH                         |  40 |      0.775 |         0.6   |             0.05  |      0.55  |         5.94042 |
| gsm8k_train | hard_cluster_teacher_subset | CASS_TARGET_POSTPROCESS_PATCH           |  40 |      0.7   |         0.525 |             0.05  |      0.475 |         4.19677 |
| gsm8k_train | hard_cluster_teacher_subset | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |  40 |      0.725 |         0.55  |             0.05  |      0.5   |         6.70964 |
| gsm8k_train | hard_cluster_teacher_subset | KEEP                                    |  40 |      0.225 |         0     |             0     |      0     |         0       |
| gsm8k_train | hard_cluster_teacher_subset | OPERATOR_SCHEMA_TO_CODE_BASE            |  40 |      0.675 |         0.5   |             0.05  |      0.45  |         1.86901 |
| gsm8k_train | hard_cluster_teacher_subset | RAW_PYTHON                              |  40 |      0.775 |         0.575 |             0.025 |      0.55  |         1.41691 |
| gsm8k_train | hard_cluster_teacher_subset | TEACHER_PATCHED_BASELINE                |  40 |      0.825 |         0.65  |             0.05  |      0.6   |         1.73732 |
| gsm8k_train | hard_cluster_teacher_subset | direct_cot                              |  40 |      0.225 |         0     |             0     |      0     |         1.34289 |
| gsm8k_train | hard_cluster_teacher_subset | freeform_fixed1_same                    |  40 |      0.45  |         0.4   |             0.175 |      0.225 |         2.25513 |
| gsm8k_train | hard_cluster_teacher_subset | self_refine_1                           |  40 |      0.45  |         0.325 |             0.1   |      0.225 |         1.94103 |
