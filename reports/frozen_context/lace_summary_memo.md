# LACE Summary Memo

## Advisor-facing read

`LACE` turns the broader `LAST-PACK` framing into an actual online policy question:

- when should we do nothing
- when should we repair locally
- when should we restart globally

The strongest supported statement from the main `Qwen/Qwen2.5-7B-Instruct` runs is:

- on hard math, a learned online gate approaches or slightly exceeds `ALWAYS_CASS` while intervening materially less
- on validator-rich output-constraint tasks, an online gate is much better than naive full rewrite and recovers most of the local-repair frontier
- on planning, the criterion remains useful as a boundary check, but planning should not carry the headline claim

## What is supported

### 1. The late-stage targeted-repair story is deployable online in math

- Overall math read:
  - `ALWAYS_DIRECT = 0.257`
  - `ALWAYS_RESTART = 0.466`
  - `ALWAYS_CASS = 0.753`
  - `LEARNED_GATE = 0.759`
- Intervention efficiency:
  - `ALWAYS_CASS` intervenes on `100%` of examples
  - `LEARNED_GATE` intervenes on `73.5%`
- Operational read:
  - the current math gate is already good enough to beat naive restart cleanly
  - and it recovers essentially all of the local-repair value without paying the full always-patch cost

### 2. The math story is strongest exactly where the frozen CASS mechanism predicts

- Late-stage failure share rises sharply from easy transfer to hard registered buckets:
  - easy transfer `1 / 4 = 0.250`
  - hard cluster `205 / 339 = 0.605`
  - hard generic `145 / 241 = 0.602`
- Dominant hard failure bucket:
  - `late_target_role_interaction`
- Best cluster pockets for the learned online policy:
  - `remainder_packaging_divisibility = 0.920`
  - `ratio_proportion_rate = 0.910`
  - `percent_fraction_complement = 0.737`
  - `average_repeated_times = 0.722`
- This is the cleanest sign that the online criterion is not arbitrary:
  - it is inheriting the same late-stage repair geometry that made `CASS` work offline

### 3. The strongest non-math support is output-constraint deployment

- Overall format read:
  - `ALWAYS_DIRECT = 0.458`
  - `ALWAYS_FULL_REWRITE = 0.505`
  - `ALWAYS_LOCAL_FORMAT_PATCH = 0.511`
  - `ALWAYS_SOLVE_THEN_FORMAT = 0.557`
  - `LOCAL_BEST = 0.653`
  - `HEURISTIC_GATE = 0.634`
  - `LEARNED_GATE = 0.620`
- This is exactly the operational pattern we wanted:
  - the gate beats naive rewrite by a large margin
  - it approaches the best local policy while intervening on only about half of cases
- Surface read:
  - screened `IFEval` is the clearest success surface:
    - `ALWAYS_FULL_REWRITE = 0.664`
    - `LOCAL_BEST = 0.793`
    - `HEURISTIC_GATE = 0.777`
    - `LEARNED_GATE = 0.753`
  - `IFBench` is harder but still directionally consistent:
    - `ALWAYS_FULL_REWRITE = 0.303`
    - `LOCAL_BEST = 0.477`
    - `HEURISTIC_GATE = 0.453`
    - `LEARNED_GATE = 0.450`

### 4. Planning remains boundary evidence, not headline evidence

- Planning overall:
  - `FULL_RESTART = 0.000`
  - `SUFFIX_REPAIR = 0.055`
  - `HEURISTIC_GATE = 0.033`
  - `LEARNED_GATE = 0.050`
- Planning still matters scientifically because:
  - hard failures are very late
  - there are real suffix-localized wins
  - the criterion can reduce waste relative to always-local
- But the honest paper posture stays bounded:
  - planning is a control domain showing where the idea can help
  - not the main proof surface for the online-policy claim

## What is not supported

- `LACE` does not support a universal rule that local repair should always replace restart.
- `LACE` does not support planning as a headline cross-domain deployment story.
- `LACE` does not claim that every failure exposed by a validator is late and locally repairable.
- `LACE` does not modify the frozen `CASS` mechanism; it only operationalizes when to use that mechanism.

## Practical paper posture

Use `LACE` as:

- advisor-facing support that the repair criterion can be deployed online
- appendix evidence that the broader framing is operational rather than purely retrospective
- future-work scaffolding for more explicit intervention policies

Do not use `LACE` as:

- a replacement for the frozen `CASS` main result
- a new broad methods branch
- a universal statement about all validator-rich tasks

## Optional model-diversity addendum

The optional second-model reduced replication is now integrated in `reports/lace_model_diversity_report.md`.

### What survived

- Math direction survives on `Qwen/Qwen2.5-Math-7B-Instruct`:
  - `ALWAYS_RESTART = 0.023`
  - `ALWAYS_CASS = 0.131`
  - `LEARNED_GATE_WITHIN = 0.140`
  - intervention drops from `1.000` to `0.280`
- Reduced stable-format direction also survives on the fallback screened-`IFEval` slice:
  - `ALWAYS_FULL_REWRITE = 0.209`
  - `LEARNED_GATE_TRANSFER = 0.224`
  - `LOCAL_BEST = 0.254`

### What did not survive

- Planning collapses on the secondary model:
  - direct, suffix repair, restart, and both gates all land at `0.000`

### Honest read

- The online-policy story now has real, but bounded, model-diversity support.
- The strongest replicated piece is math.
- The format result is supportive but narrower because it comes from the stable reduced screened-`IFEval` fallback slice rather than a fresh full secondary-model rerun.
- Planning should remain a boundary/control example rather than a cross-model claim anchor.

## Bottom line

`LACE` materially strengthens the broader framing around `CASS`.

The most honest final statement is:

- there is a real online criterion question here
- on hard math, that criterion can already beat naive restart and nearly match or slightly exceed always-local repair while intervening less
- on validator-rich output-constraint tasks, the same idea also works cleanly enough to matter
- on planning, the criterion is still better treated as bounded control evidence than as a headline deployment success
