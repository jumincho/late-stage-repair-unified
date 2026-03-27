# CASS-XF-R3 Mistral Generic-Hard Report

## Headline

- best frozen CASS variant: `CASS_TARGET_POSTPROCESS_PATCH`
- generic-hard best-vs-RAW: `+0.2192 [+0.1739, +0.2629]`
- generic-hard best-vs-OPERATOR: `+0.0285 [-0.0124, +0.0683]`

| dataset     | surface              | method                                  |   n |   accuracy |   repair_rate |   corruption_rate |   net_gain |   avg_latency_s | model_name                         |
|:------------|:---------------------|:----------------------------------------|----:|-----------:|--------------:|------------------:|-----------:|----------------:|:-----------------------------------|
| gsm8k_train | hard_generic_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 483 |  0.178054  |      0.136646 |        0.0186335  |  0.118012  |        10.0934  | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               | 483 |  0.15942   |      0.10766  |        0.00828157 |  0.0993789 |         7.14991 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | CASS_CONSERVATIVE_GATE                  | 483 |  0.42029   |      0.380952 |        0.0207039  |  0.360248  |         9.24735 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           | 483 |  0.42029   |      0.380952 |        0.0207039  |  0.360248  |         6.97602 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 483 |  0.42029   |      0.380952 |        0.0207039  |  0.360248  |         9.24735 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | KEEP                                    | 483 |  0.0600414 |      0        |        0          |  0         |         0       | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            | 483 |  0.391304  |      0.341615 |        0.010352   |  0.331263  |         2.86292 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | RAW_PYTHON                              | 483 |  0.200828  |      0.15942  |        0.0186335  |  0.140787  |         2.45843 | mistralai/Mistral-7B-Instruct-v0.3 |

| surface              | base_method                  | alt_method                              |   n |   base_accuracy |   alt_accuracy |      delta |     ci_low |     ci_high |   mcnemar_p |   direction_favorable |
|:---------------------|:-----------------------------|:----------------------------------------|----:|----------------:|---------------:|-----------:|-----------:|------------:|------------:|----------------------:|
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 483 |        0.391304 |       0.178054 | -0.21357   | -0.258799  | -0.169772   | 2.12052e-18 |                     0 |
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | ATLAS_RG_ROLE_REPAIR_ONLY               | 483 |        0.391304 |       0.15942  | -0.232005  | -0.275362  | -0.188406   | 1.71041e-22 |                     0 |
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_CONSERVATIVE_GATE                  | 483 |        0.391304 |       0.42029  |  0.0285031 | -0.0124224 |  0.068323   | 0.184286    |                     1 |
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH           | 483 |        0.391304 |       0.42029  |  0.0285031 | -0.0124224 |  0.068323   | 0.184286    |                     1 |
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 483 |        0.391304 |       0.42029  |  0.0285031 | -0.0124224 |  0.068323   | 0.184286    |                     1 |
| hard_generic_main_r2 | RAW_PYTHON                   | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 483 |        0.200828 |       0.178054 | -0.0228685 | -0.0621118 |  0.0165631  | 0.31488     |                     0 |
| hard_generic_main_r2 | RAW_PYTHON                   | ATLAS_RG_ROLE_REPAIR_ONLY               | 483 |        0.200828 |       0.15942  | -0.0413033 | -0.0786749 | -0.00414079 | 0.0422106   |                     0 |
| hard_generic_main_r2 | RAW_PYTHON                   | CASS_CONSERVATIVE_GATE                  | 483 |        0.200828 |       0.42029  |  0.219205  |  0.173913  |  0.26294    | 1.11133e-19 |                     1 |
| hard_generic_main_r2 | RAW_PYTHON                   | CASS_TARGET_POSTPROCESS_PATCH           | 483 |        0.200828 |       0.42029  |  0.219205  |  0.173913  |  0.26294    | 1.11133e-19 |                     1 |
| hard_generic_main_r2 | RAW_PYTHON                   | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 483 |        0.200828 |       0.42029  |  0.219205  |  0.173913  |  0.26294    | 1.11133e-19 |                     1 |