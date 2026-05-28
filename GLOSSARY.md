# Glossary

The closure reports and the code use a few internal terms that aren't
self-explanatory if you're coming in cold. This is the decoder ring.

## The three actions (the whole decision space)

| Action | What it means in plain English |
|---|---|
| `NO_INTERVENTION` / `do_nothing` | Keep the model's first answer. No second pass, no repair. |
| `LOCAL_REPAIR` | Patch only the last step. The rest of the model's reasoning is left intact. In math this is a `GRANITE_POSTPROCESS_ONLY_PATCH`-style targeted edit; in format it is `solve_then_format` (regenerate the content tag, then re-render under the constraints). |
| `GLOBAL_REWRITE_OR_RESTART` | Start over from scratch. `self_refine_1` in math, `full_rewrite_on_failure` in format. |

The headline result of the project is **`LOCAL_REPAIR` consistently beats
`GLOBAL_REWRITE_OR_RESTART`** in both domains and even when the same policy
is applied across both.

The three names live in `ABSTRACT_ACTION_SPACE` and `ACTION_MAPPING` in
`code/src/dart_research/unify_live_full_r2.py`.

## The two domains

| Domain | What it covers | Where it lives in code |
|---|---|---|
| **Math domain** | Hard arithmetic / word problems. Two surfaces: `cluster-hard` (a clustered slice of GSM8K-style problems) and `generic-hard` (general hard problems). | `code/src/dart_research/cass*` and `code/scripts/cass_r4_collect.py` |
| **Output-format / output-constraint domain** | Instruction-following with strict format constraints. Three surfaces: screened `IFEval`, full `IFBench`, and the in-house `planning_bridge`. | `code/src/dart_research/last_pack/` and `code/scripts/last_pack_collect_format.py` |

The interesting finding is that when both are reframed as "patch the
last-step mistake", they line up much more than their surface differences
suggest. See `REPORT_PROJECT_SUMMARY_EN.md` section 6 for the numbers.

## Naming prefixes you'll see all over the source tree

| Prefix | What it is |
|---|---|
| `cass_r4` | "Cluster-And-Schema-Steered, round 4" — the math collection used in the final pipeline. The math half of the unified frame is `cass_r4` records. Earlier rounds (`cass`, `cass_r2`, `cass_bd`) are kept as historical layers — each later round subclasses the earlier one's runner. |
| `last_pack` | "Last pack" — the last round of format-domain data before unification. The format half of the unified frame is `last_pack` records. |
| `unify_live_full_r2` | "Unified frame + live (prospective) collection + full surface coverage + round 2 of the unification effort." This is the final cross-domain entry point. The three companion scripts (`*_prepare.py`, `*_integrity.py`, `*_make_reports.py`) plus the watchdog drive it. |
| `atlas` / `atlas_rg` / `atlas_ms` | Mid-round math schemas. `_rg` = role-grounded, `_ms` = multi-signature. CASS reuses their schema helpers. |
| `eir` / `heir` / `oscar` / `tier` | Earlier math probe / repair / compile layers. Subclassed in order: EIR → HEIR → OSCAR → ATLAS → CASS → CASS_R2 → CASS_R4. |
| `lace` | The unification policy fitter — defines the three-action space and the unified `(math, format)` frame builder. |
| `vchase` / `confidence` | Bridge-layer features and the same-context-chase trace collector. Their outputs feed `lace`. |

## `DART_REPO_ROOT`

Every script and every module that reads or writes outside of the source
tree resolves its repo-root path from the `DART_REPO_ROOT` env var:

```bash
export DART_REPO_ROOT="$(pwd)"   # or any absolute path
```

The default is `/workspace/project`, which is the path the original
execution environment used; setting `DART_REPO_ROOT` redirects everything
to a fresh checkout.

## `dart_research/` package layout

```
dart_research/
├── unify_live_full_r2.py           cross-domain entry point and report writers
├── run_experiment.py               generic smoke / regression harness
├── lace/                           three-action policy + unified frame builder
├── cass/, cass_r2/, cass_r4/, cass_bd/   math-domain runners (each round)
├── atlas/, atlas_rg/, atlas_ms/    math schema layers (each round)
├── oscar/, tier/, heir/, eir/      earlier math probe / compile layers
├── last_pack/                      format-domain runner + dataset loaders
├── confidence/, vchase/            confidence traces and bridge features
├── clients/                        hf_local / vllm / openai / mock backends
├── datasets/                       benchmark loaders
├── parsing/                        JSON / tag / answer-normalization helpers
├── evaluation/                     paired-bootstrap and McNemar
├── analysis/                       small reporting helper for run_experiment
├── methods/                        generic method pipelines used by the smoke run
└── utils/                          config, cache, io, prompt-loader
```

Per-domain modules typically come in `prompts.py` + `runner.py` (+ `schema.py`
or `retrieval.py` where needed). The runner is the per-example collector;
the prompt bank wraps the `.txt` prompts under `prompts/<module>/`.

## `reports/frozen_context/` vs `reports/final/`

| Folder | What's in it |
|---|---|
| `reports/frozen_context/` | The pre-unification context, per domain. The math side's `cass_r4_main_report.md` and friends, the format side's planning reports, and the earlier `lace_full_synthesis.md` / `unify_full_synthesis.md`. These are *frozen* — they record where each domain stood before they were merged into one story. |
| `reports/final/` | The unified cross-domain reports produced by `unify_live_full_r2_make_reports.py`: per-model reports (`unify_live_full_r2_*_report.md`), the synthesis memo, the qwen14b collection report, and the one-page summary memo. |

## `tables/` and `figures/`

- `tables/` — CSVs for the writeup. The unified r2 round writes to
  `tables/unify_live_full_r2/`.
- `figures/` — PNGs for the writeup. Same r2 subfolder convention.

Both are output paths; they are not consumed by other code. The closure
report markdown files reference these by relative path.

## `manifests/`

Run manifests. Each collection writes a small `manifest.json` next to its
`per_example.jsonl` recording the dataset, surface, source model, backend,
prompt versions, etc. `unify_live_full_r2_prepare` produces the shared
manifest files (per surface, per shard) that the per-model collectors then
consume. The `manifests/` directory at repo root is where checked-in copies
of those manifests live for portability.

## `logs/research_log.md` vs `logs/decision_log.md`

| File | What it tracks |
|---|---|
| `logs/research_log.md` | Day-by-day notes — what was tried, what was observed, where each round left off. The narrative of the work. |
| `logs/decision_log.md` | The point-decisions only — "decided to drop the universal-rule claim", "switched 14B to 8-way shard", "froze the action mapping at three actions". The "what we committed to" stream. |
