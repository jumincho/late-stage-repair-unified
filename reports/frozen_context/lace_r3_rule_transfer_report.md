# LACE-R3 Rule Transfer Report

## Goal

- Separate the portability of simple rules from the portability of learned gates.
- Compare transfer and within-model tuning across math, screened IFEval, and fresh IFBench.

## Surface summary

### math_cluster

- baseline `ALWAYS_RESTART`: `0.122`
- learned transfer: `0.183`
- best simple transfer `SIMPLE_3FEATURE_GATE_TRANSFER`: `0.290`
- learned within: `0.282`
- simple within: `0.290`

### ifeval_screened

- baseline `ALWAYS_FULL_REWRITE`: `0.518`
- learned transfer: `0.574`
- best simple transfer `SIMPLE_THRESHOLDED_TREE_TRANSFER`: `0.624`
- learned within: `0.539`
- simple within: `0.603`

### ifbench

- baseline `ALWAYS_FULL_REWRITE`: `0.155`
- learned transfer: `0.204`
- best simple transfer `SIMPLE_BEST_GATE_TRANSFER`: `0.223`
- learned within: `0.194`
- simple within: `0.223`

## Read

- `math_cluster`: best simple transfer vs learned transfer = `+0.107`, learned within gain over learned transfer = `+0.099`.
- `ifeval_screened`: best simple transfer vs learned transfer = `+0.050`, learned within gain over learned transfer = `-0.035`.
- `ifbench`: best simple transfer vs learned transfer = `+0.019`, learned within gain over learned transfer = `-0.010`.
- The clean reviewer-facing question is not whether within-model tuning always helps. On math it does, but on screened `IFEval` and fresh `IFBench` the simpler transferred rule is actually more portable than the learned transfer or learned-within variants. The sharper question is whether a simple transferred rule stays useful enough to support portability and criterion clarity.