"""DART research prototype package.

`dart_research` is the source package for the late-stage repair decision-space
experiments. It is organised as a small set of per-domain runner modules
(`cass*`, `last_pack`, `eir`, `heir`, `oscar`, `atlas*`) plus shared
infrastructure (`clients`, `parsing`, `evaluation`, `datasets`, `utils`,
`analysis`, `methods`).

The two domain-side narrative pieces are:

- `cass_r4` / `cass_bd` / `cass_r2` / `cass` — the math domain, organised
  around schema-and-cluster-steered patch banks at successive rounds.
- `last_pack` — the output-format / output-constraint domain
  (IFEval, IFBench, in-house planning bridge).

`unify_live_full_r2` is the cross-domain entry point that maps both into the
shared three-action space (`NO_INTERVENTION`, `LOCAL_REPAIR`,
`GLOBAL_REWRITE_OR_RESTART`). `lace` holds the policy fitter and the unified
frame builder used by that module.
"""

