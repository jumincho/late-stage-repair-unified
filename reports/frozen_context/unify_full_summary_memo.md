# UNIFY-FULL Summary Memo

## Advisor-Facing Read

- The strongest honest question here is not whether one universal rule wins everywhere, but whether a pooled interpretable rule stays close enough to domain-tuned rules that the paper can present one shared intervention geometry.
- In this pack, `POOLED_RULE_BEST` is the main unification candidate. `MATH_TUNED_RULE` and `FORMAT_TUNED_RULE` are the shared-feature rules tuned on one domain only and transferred to the other.
- The common abstraction is best read as `late-stage final-requirement realization`: math late target/postprocess failures and format constraint-realization failures both create pockets where local repair can be preferable to global restart/rewrite.

## What Is Supported

- Qwen-7B: best overall shared-action policy `FORMAT_TUNED_RULE (0.706)`, with `POOLED_RULE_BEST` exactly tied.
- Mistral-7B: best overall shared-action policy `FORMAT_TUNED_RULE (0.432)`, with `POOLED_RULE_BEST` remaining very close.
- Qwen-7B pooled-vs-rewrite overall `+0.2176 [+0.1799, +0.2578]`.
- Mistral-7B pooled-vs-rewrite overall `+0.1694 [+0.1300, +0.2115]`.
- Qwen-14B pooled-vs-rewrite overall `+0.1084 [+0.0694, +0.1458]`.
- The failure-bucket alignment remains strongest in `final_requirement_realization`, which is exactly where both math postprocess/discretization repair and format local repair operate.

## What Is Not Supported

- The pooled rule should not be oversold as a free replacement for every domain-tuned criterion if the domain-gap table remains materially negative on one module.
- The unified story still does not imply that all late failures are equal. Math target-side edits remain more sensitive than math postprocess-only repair, and IFBench remains a harder boundary surface than screened IFEval.

## Paper Positioning

- If the pooled rule remains reasonably close to the domain-tuned rules on both Qwen and Mistral, the paper can present math and output-constraint tasks as two manifestations of one shared late-stage targeted-repair geometry.
- If the pooled gap is too large, the safe claim is narrower: one common geometry exists, but the paper still needs domain-specific simple criteria on top of that shared analysis layer.