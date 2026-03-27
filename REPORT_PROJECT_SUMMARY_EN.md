# UNIFY-LIVE-FULL-R2 Final Project Report

## 1. What this project was

This was a research program about late-stage repair at inference time. The core idea was that many model failures do not require a brand-new answer from scratch. Instead, the answer can often be fixed by targeting the final requirement-realization step.

By the end of the project, two problem families became the main empirical pillars:

- hard arithmetic / math repair
- validator-rich output-constraint repair

The final paper-level question was:

Can these two domains be presented as two instances of one shared late-stage intervention story, using fresh prospective online evidence rather than only frozen re-analysis?

## 2. How the project evolved

The repository went through many branches over time. Early and middle stages developed candidate mechanisms, diagnostics, validator use, and domain-specific repair operators. Those branches are historical evidence, but the final branch in this archive is `UNIFY-LIVE-FULL-R2`.

`UNIFY-LIVE-FULL-R2` did not invent a new method family. It did four narrower things:

- locked the fresh prospective `Qwen-7B` and `Mistral-7B` banks with integrity checks
- completed the missing `Qwen-14B` prospective bank
- evaluated pooled versus domain-specific policies prospectively
- produced the final cross-domain synthesis for a two-pillar paper

## 3. Final intervention geometry

The final abstraction was intentionally simple and fixed:

- `NO_INTERVENTION`
- `LOCAL_REPAIR`
- `GLOBAL_REWRITE_OR_RESTART`

This abstraction was mapped onto already-frozen domain executors:

- math:
  - direct answer
  - frozen postprocess/discretization-centered local repair
  - frozen restart path
- format:
  - direct formatted answer
  - frozen local format-side repair
  - full rewrite

The important claim is not that one universal policy wins every cell. The important claim is that both domains can be understood using the same late-stage decision geometry.

## 4. Models and evaluation surfaces

Required model families:

- `Qwen/Qwen2.5-7B-Instruct`
- `mistralai/Mistral-7B-Instruct-v0.3`
- `Qwen/Qwen2.5-14B-Instruct`

Primary surfaces:

- math:
  - `cluster-hard`
  - `generic-hard`
- format:
  - screened `IFEval`
  - `IFBench`

## 5. What was actually completed

The final `R2` run finished all required fresh prospective coverage.

Completed prospective bank:

- math raw: `1998 / 1998`
- math replay: `1998 / 1998`
- format: `681 / 681`

Surface totals:

- `cluster-hard`: `1515`
- `generic-hard`: `483`
- screened `IFEval`: `381`
- `IFBench`: `300`

The `Qwen-14B` run initially stalled under a low-utilization path. The final completed path used `8`-way sharding with `2` worker slots per GPU and later had to be resumed from an incomplete replay checkpoint. That resumed run finished cleanly and reached full `48 / 48` shard completion.

## 6. Main empirical findings

### 6.1 Fresh 7B prospective result

The two completed 7B families are the backbone of the final claim.

Fresh pooled-simple versus always-rewrite overall:

- `Qwen-7B`: `+0.2436` with range `[+0.2278, +0.2707]`
- `Mistral-7B`: `+0.2210` with range `[+0.1981, +0.2354]`

This is the main reason output-constraint can now stand beside math as a true co-main pillar. The story is no longer only retrospective.

### 6.2 Pooled versus domain-specific rules

The pooled simple rule did not need to dominate every domain-tuned rule. The important test was whether it stayed close while still beating naive rewrite.

Observed pooled-minus-domain utility gap:

- `Qwen-7B`
  - math: `-0.0010`
  - format: `-0.0121`
- `Mistral-7B`
  - math: `-0.0034`
  - format: `-0.0096`

This is close enough to support a shared-paper story without claiming full universality.

### 6.3 Qwen-14B scale check

After completion, `Qwen-14B` also supported the same geometry.

Fresh pooled-simple versus always-rewrite overall:

- `Qwen-14B`: `+0.1000` with range `[+0.0859, +0.1105]`

Pooled-minus-domain utility gap:

- math: `-0.0038`
- format: `0.0000`

Interpretation:

- scale compresses gains
- the positive geometry remains
- the format-side pooled rule can exactly match the best domain-tuned simple rule in this completed scale cell

### 6.4 Transfer asymmetry

The project also checked asymmetry across domains.

The final read is constructive, not contradictory:

- domain-specific rules remain informative
- pooled rules transfer better than a narrow domain story would suggest
- math and format are not identical tasks, but they do line up in the late-stage repair region strongly enough for one paper narrative

### 6.5 Shared failure bucket

The strongest cross-domain alignment remained:

- `final_requirement_realization`

This matters because it is exactly the region where both domains benefit from targeted local repair rather than immediate full rewrite.

## 7. What is safe to claim now

Safest high-level claim:

Across fresh prospective `Qwen-7B`, `Mistral-7B`, and a completed `Qwen-14B` scale check, hard arithmetic repair and validator-rich output-constraint repair behave like two instances of one late-stage requirement-realization problem in which targeted local repair consistently beats naive full rewrite while pooled simple policies stay close to domain-tuned rules.

In plain language:

- math is a real main pillar
- output-constraint is also a real main pillar
- the shared geometry is supported by fresh online evidence
- a pooled simple rule is good enough to support the story, even if domain-tuned rules still matter at the margin

## 8. What is not proven

This project does not prove:

- that one universal rule strictly wins every domain and every scale
- that output-constraint is as easy as math
- that `IFBench` has become a solved or parity-level surface

The honest caveat is:

- `IFBench` remains the harder boundary surface
- domain-tuned simple criteria still help at the margins
- the strongest claim is about a shared intervention geometry, not perfect policy universality

## 9. What to read next in this archive

For final conclusions:

- `reports/final/unify_live_full_r2_summary_memo.md`
- `reports/final/unify_live_full_r2_synthesis.md`
- `reports/final/unify_live_full_r2_qwen14b_report.md`

For the frozen context behind the final branch:

- `reports/frozen_context/cass_r4_main_report.md`
- `reports/frozen_context/cass_fi_portable_core_report.md`
- `reports/frozen_context/lace_full_synthesis.md`
- `reports/frozen_context/unify_full_synthesis.md`

For project history:

- `logs/research_log.md`
- `logs/decision_log.md`

## 10. Bottom line

The project reached a clear end state.

The final answer is yes:

- math and validator-rich output-constraint tasks can now be presented as two main empirical pillars of one shared late-stage requirement-realization story
- that claim is supported by fresh prospective evidence on two 7B families and a completed 14B scale check

This archive was built so a new reader can understand that conclusion without opening the full original repository.
