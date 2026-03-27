# CASS-XF-R2 Mistral Lock Report

## Headline

- expanded cluster-hard best frozen CASS variant: `CASS_TARGET_POSTPROCESS_PATCH`
- expanded generic-hard best frozen CASS variant: `none`
- cluster-hard `CASS_TARGET_POSTPROCESS_PATCH - RAW_PYTHON`: `+0.1486 [+0.1234, +0.1716]`
- cluster-hard `CASS_TARGET_POSTPROCESS_PATCH - OPERATOR_SCHEMA_TO_CODE_BASE`: `+0.0273 [+0.0079, +0.0482]`
- stable sequential lock vs operator reached at prefix: `1350`

## Expanded Mistral summary

| dataset     | surface              | method                                  |    n |   accuracy |   repair_rate |   corruption_rate |   net_gain |   avg_latency_s | model_name                         |
|:------------|:---------------------|:----------------------------------------|-----:|-----------:|--------------:|------------------:|-----------:|----------------:|:-----------------------------------|
| gsm8k_train | hard_cluster_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 1515 |  0.173597  |      0.126733 |        0.0151815  |  0.111551  |         9.72576 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_cluster_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               | 1515 |  0.153795  |      0.10297  |        0.0112211  |  0.0917492 |         6.91266 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_cluster_main_r2 | CASS_CONSERVATIVE_GATE                  | 1515 |  0.358416  |      0.316832 |        0.020462   |  0.29637   |         8.9478  | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           | 1515 |  0.358416  |      0.316832 |        0.020462   |  0.29637   |         6.70991 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 1515 |  0.358416  |      0.316832 |        0.020462   |  0.29637   |         8.9478  | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_cluster_main_r2 | KEEP                                    | 1515 |  0.0620462 |      0        |        0          |  0         |         0       | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            | 1515 |  0.331353  |      0.286469 |        0.0171617  |  0.269307  |         2.80575 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_cluster_main_r2 | RAW_PYTHON                              | 1515 |  0.209901  |      0.157756 |        0.00990099 |  0.147855  |         2.42918 | mistralai/Mistral-7B-Instruct-v0.3 |

## Pairwise focus

| surface              | base_method                  | alt_method                              |    n |   base_accuracy |   alt_accuracy |      delta |      ci_low |    ci_high |   mcnemar_p |   direction_favorable |
|:---------------------|:-----------------------------|:----------------------------------------|-----:|----------------:|---------------:|-----------:|------------:|-----------:|------------:|----------------------:|
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 1515 |        0.331353 |       0.173597 | -0.157668  | -0.181518   | -0.133333  | 1.52715e-38 |                     0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | ATLAS_RG_ROLE_REPAIR_ONLY               | 1515 |        0.331353 |       0.153795 | -0.177557  | -0.20132    | -0.154455  | 8.28211e-48 |                     0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_CONSERVATIVE_GATE                  | 1515 |        0.331353 |       0.358416 |  0.0273343 |  0.00792079 |  0.0481848 | 0.0110998   |                     1 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH           | 1515 |        0.331353 |       0.358416 |  0.0273343 |  0.00792079 |  0.0481848 | 0.0110998   |                     1 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 1515 |        0.331353 |       0.358416 |  0.0273343 |  0.00792079 |  0.0481848 | 0.0110998   |                     1 |
| hard_cluster_main_r2 | RAW_PYTHON                   | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 1515 |        0.209901 |       0.173597 | -0.0364287 | -0.0567657  | -0.0158416 | 0.00104536  |                     0 |
| hard_cluster_main_r2 | RAW_PYTHON                   | ATLAS_RG_ROLE_REPAIR_ONLY               | 1515 |        0.209901 |       0.153795 | -0.0563182 | -0.0765677  | -0.0356436 | 6.78741e-08 |                     0 |
| hard_cluster_main_r2 | RAW_PYTHON                   | CASS_CONSERVATIVE_GATE                  | 1515 |        0.209901 |       0.358416 |  0.148574  |  0.123432   |  0.171617  | 1.33677e-32 |                     1 |
| hard_cluster_main_r2 | RAW_PYTHON                   | CASS_TARGET_POSTPROCESS_PATCH           | 1515 |        0.209901 |       0.358416 |  0.148574  |  0.123432   |  0.171617  | 1.33677e-32 |                     1 |
| hard_cluster_main_r2 | RAW_PYTHON                   | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 1515 |        0.209901 |       0.358416 |  0.148574  |  0.123432   |  0.171617  | 1.33677e-32 |                     1 |

## Interval shrinkage vs RAW_PYTHON

| surface              | base_method   | alt_method                    |    n |   base_accuracy |   alt_accuracy |    delta |    ci_low |   ci_high |   mcnemar_p |   locked |
|:---------------------|:--------------|:------------------------------|-----:|----------------:|---------------:|---------:|----------:|----------:|------------:|---------:|
| hard_cluster_main_r2 | RAW_PYTHON    | CASS_TARGET_POSTPROCESS_PATCH |  150 |        0.24     |       0.353333 | 0.113643 | 0.0333333 |  0.186667 | 0.00763208  |        1 |
| hard_cluster_main_r2 | RAW_PYTHON    | CASS_TARGET_POSTPROCESS_PATCH |  300 |        0.203333 |       0.313333 | 0.11008  | 0.06      |  0.16     | 3.76061e-05 |        1 |
| hard_cluster_main_r2 | RAW_PYTHON    | CASS_TARGET_POSTPROCESS_PATCH |  450 |        0.211111 |       0.34     | 0.129607 | 0.0888889 |  0.173333 | 1.88293e-08 |        1 |
| hard_cluster_main_r2 | RAW_PYTHON    | CASS_TARGET_POSTPROCESS_PATCH |  600 |        0.213333 |       0.345    | 0.131656 | 0.095     |  0.17     | 2.95451e-11 |        1 |
| hard_cluster_main_r2 | RAW_PYTHON    | CASS_TARGET_POSTPROCESS_PATCH |  750 |        0.204    |       0.344    | 0.139921 | 0.106667  |  0.173333 | 5.13507e-15 |        1 |
| hard_cluster_main_r2 | RAW_PYTHON    | CASS_TARGET_POSTPROCESS_PATCH |  900 |        0.208889 |       0.356667 | 0.147449 | 0.117778  |  0.18     | 6.61965e-20 |        1 |
| hard_cluster_main_r2 | RAW_PYTHON    | CASS_TARGET_POSTPROCESS_PATCH | 1050 |        0.222857 |       0.369524 | 0.146674 | 0.117143  |  0.17619  | 1.70774e-22 |        1 |
| hard_cluster_main_r2 | RAW_PYTHON    | CASS_TARGET_POSTPROCESS_PATCH | 1200 |        0.223333 |       0.375    | 0.151634 | 0.124167  |  0.18     | 7.14935e-27 |        1 |
| hard_cluster_main_r2 | RAW_PYTHON    | CASS_TARGET_POSTPROCESS_PATCH | 1350 |        0.216296 |       0.366667 | 0.150285 | 0.122222  |  0.176296 | 2.90966e-29 |        1 |
| hard_cluster_main_r2 | RAW_PYTHON    | CASS_TARGET_POSTPROCESS_PATCH | 1500 |        0.21     |       0.359333 | 0.149372 | 0.123333  |  0.174    | 8.91527e-33 |        1 |
| hard_cluster_main_r2 | RAW_PYTHON    | CASS_TARGET_POSTPROCESS_PATCH | 1515 |        0.209901 |       0.358416 | 0.148491 | 0.122772  |  0.172937 | 1.33677e-32 |        1 |

## Interval shrinkage vs OPERATOR_SCHEMA_TO_CODE_BASE

| surface              | base_method                  | alt_method                    |    n |   base_accuracy |   alt_accuracy |      delta |       ci_low |   ci_high |   mcnemar_p |   locked |
|:---------------------|:-----------------------------|:------------------------------|-----:|----------------:|---------------:|-----------:|-------------:|----------:|------------:|---------:|
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH |  150 |        0.366667 |       0.353333 | -0.0136067 | -0.0866667   | 0.06      |   0.850554  |        0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH |  300 |        0.313333 |       0.313333 |  0.00029   | -0.04        | 0.0433333 |   1         |        0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH |  450 |        0.324444 |       0.34     |  0.0160867 | -0.0222222   | 0.0533333 |   0.488683  |        0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH |  600 |        0.333333 |       0.345    |  0.0116808 | -0.0216667   | 0.045     |   0.54261   |        0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH |  750 |        0.329333 |       0.344    |  0.0146107 | -0.016       | 0.044     |   0.359358  |        0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH |  900 |        0.342222 |       0.356667 |  0.0141894 | -0.0133333   | 0.0422222 |   0.331993  |        0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH | 1050 |        0.348571 |       0.369524 |  0.0209619 | -0.0047619   | 0.0466667 |   0.121353  |        0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH | 1200 |        0.350833 |       0.375    |  0.0240825 | -0.000833333 | 0.0475    |   0.0536469 |        0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH | 1350 |        0.342963 |       0.366667 |  0.0234441 |  0.000740741 | 0.0451852 |   0.0433701 |        1 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH | 1500 |        0.332    |       0.359333 |  0.027203  |  0.006       | 0.0486667 |   0.0107758 |        1 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH | 1515 |        0.331353 |       0.358416 |  0.0269287 |  0.00660066  | 0.0481848 |   0.0110998 |        1 |