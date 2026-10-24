# Native batch E (2026-10-24): size, count and density expansion for four families

Base `c201cfe`. IDs: 0c786b71, e0fb7511, f0df5ff0, f3cdc58f. The native-domain review
(`native-domain-review-20261024/semantic_reviews.json`) was treated as evidence to check, not
as authority. Every claim below was re-measured here.

**Not production-ready.** `prepare` only accepts admitted, REPAIRED or REVIEWED_NATIVE IDs,
and these four are none of those. `admission.json` also pins `verified_rules.py` and
`colour_evidence.py`, which this batch changes. Root still has to rebuild admission and
register the families. **No prepare export was run.** Admission, prepare, policies and
registries were not modified or monkeypatched.

## Commits (kept separate)

| Commit | Scope |
|---|---|
| `05db160` | `verified_rules`: fixed-colour pair checkers for e0fb7511 and f3cdc58f |
| `ce8c79d` | `colour_evidence` + new `mirror_neighbourhood_evidence.py`: gates for 0c786b71, e0fb7511, f0df5ff0 |
| `b9480e9` | constructors, recertified factory records, tests, evidence, context audit, report |
| `3061857` | batch D context-audit rerun on the batch E shared sources |
| `302a830` | supervisor doc qualification (low-density limit, D rerun comparison) |
| `51e67f2` | e0fb7511 gate: component-size threshold candidates (all T ≥ 1) alongside 4/8-connectivity |
| (this) | witness evidence and context-audit refresh on the final gate bytes; report |

Shared-source hashes:
- `verified_rules.py`: 8ad9a385 → a54743d7.
- `colour_evidence.py`: 2617143c → 6789d3d8.
- `mirror_neighbourhood_evidence.py`: new, 59b0a8f1 (`ce8c79d`) → 98e1b2ea (`51e67f2`, final).

The direct factories are unchanged (871a44a1, 66678c1e, d3eb4c59, 81c2164b).

## Rules and what changed

Rules, colour roles, fixtures and factories are all unchanged. Each fixture replays
byte-for-byte: 4 canonical and 4 teaching pairs per family.

| ID | Rule (native) | Was fixed | Now (default sampling) | Explicit range |
|---|---|---|---|---|
| 0c786b71 | 2H×2W mirror tiling with the unflipped input bottom-right | 3×4 input | H, W 2..15; same 3-colour pool | H, W 1..15 (output ≤ 30) |
| e0fb7511 | 0 with a 4-adjacent 0 becomes 8; other 0s stay | 13×13, black p = 1/8 | H, W 6..30; p 0.15..0.35 per scene | H, W 1..30, any 0 < p < 1 |
| f0df5ff0 | 0s in each 1-seed's 3×3 window become 1 | 15×15, 2..8 seeds, confetti 0.5 | H, W 6..30; seeds 2..`default_max_boxes`; confetti 0.3..0.5 | H, W 1..30; seeds 1..capacity |
| f3cdc58f | colour c is a bottom-aligned bar in column c−1, height = count | 10×10, 2..8 placements | H, W 4..30; placements 2..min(H, ⌊4H/5⌋) | W 4..30, H 1..30 |

Constructor rules:
- **Explicit colours keep the legacy canvas.** Explicit `colors` with omitted dimensions use the legacy canvas: 4×3, 13×13, 15×15, 10×10.
- **Legacy RNG replay.** Explicit legacy dimensions replay the legacy RNG stream exactly for 0c786b71 and f3cdc58f (tested). e0fb7511 and f0df5ff0 now sample density, so their RNG streams intentionally differ.
- **Explicit values are never replaced.** Invalid values raise `ValueError`: non-int (including `0.0`/`1.0`/bool) colours or dimensions, out-of-range values, wrong lengths, and sampling-only arguments combined with explicit colours.
- **Minimum clarity guards are kept as sampling choices, scaled from the legacy values:**
  - e0fb7511: at least `max(2, round(13·HW/169))` azure cells, which is exactly 13 at 13×13.
  - f0df5ff0: at least 3 visible blue cells in every seed window.
  - f3cdc58f: all four colours survive overwriting.
- **Retries are bounded:** 200, 200 and 100 attempts respectively. On exhaustion the constructor raises `RuntimeError`. There is no fixed fallback, and requested counts are never relaxed.
- **e0fb7511 explicit scenes are labelled as given.** Legacy returned `None` grids when they failed the azure floor; now all-black and all-blue scenes are valid.
- **f0df5ff0 domain limits.** Edge seeds and overlapping windows are undemonstrated, so they stay excluded. Explicit scenes that contain them raise `ValueError`.
- **f0df5ff0 window placement.** Requests up to half capacity use random sequential placement. Larger requests use a randomly jittered lattice, which always succeeds for n ≤ ⌊W/3⌋·⌊H/3⌋. Full capacity on 30×30 (100 windows) finishes in ≤ 0.02 s; a test runs it under a 3 s deadline. This replaced an earlier `common.place_rectangles` draft: a buffered stress probe of 20 full-capacity draws on it ran for several minutes and was stopped by the supervisor. Those partial measurements were discarded.
- **f3cdc58f oversize counts.** Counts above H raise `ValueError`, replacing the legacy negative indexing.

## Shared checker corrections (root-authorised, two IDs only)

The archived solvers take roles from the modal colour.
- **e0fb7511:** `generate(colors=[0]*169)` labels the scene all 8, but archived returns all 0. Legacy 13×13 explicit scenes disagree 256/500 at black density 0.5.
- **f3cdc58f:** the legal 10×4 grid with ten cells of each of 1..4 gives archived rows `[2,3,4,1]` instead of `[1,2,3,4]`.

The reviewed checkers read the fixed native colours. On their own commit and the legacy
constructor bytes:
- fixtures 8/8 exact;
- 0/1000 disagreements on legacy default draws;
- 0 adversarial disagreements, against archived 10/22 (e0) and 4/9 (f3).

The adversarial set covers dense, tied, all-black and all-blue grids, diagonal-only contact,
singletons, full rows and columns, 1×1 to 30×30, and modal or tied bar colours. See
`verifier-evidence-e0fb7511-f3cdc58f.json` and the counterexample files.

## Evidence gates (`mirror_neighbourhood_evidence.py`, via `require_colour_evidence` → `make_record`)

Each gate keeps the named candidates that reproduce every demonstration. All survivors must
agree on the query input. Answers are never read, and a failure means the demos are resampled
for the same query.

| ID | Candidates | Ambiguous before the gate (strict same shape, 2000 contexts) |
|---|---|---|
| 0c786b71 | unflipped input in TL / TR / BL / BR | 2×2: 10 (TL 3, BL 5, TR 2); 3×2, 2×3, 3×4: 0 |
| e0fb7511 | 4- or 8-connectivity × every threshold T ≥ 1 (mark components of ≥ T cells) | 6×6: 127 (T ≥ 3: 66; 8-adjacency: 55; both: 6; T = 1: 0); 13×13: 0 |
| f0df5ff0 | 3×3 square vs plus cross | 6×6, 15×15: 0 (explicit legal witness in tests) |

Checked cases:
- **0c786b71:** three distinct left-right symmetric demos with an asymmetric query are rejected under all 24 D4×palette variants. The same demos with a symmetric query pass.
- **f0df5ff0:** demos whose seed diagonals all hold confetti, with a query that has a background diagonal, are rejected. These are legal constructor scenes, and tests check that the constructor reproduces them.
- **f3cdc58f:** no gate. Every pair shows all four bars.

**e0fb7511 thresholds.** The first gate (`ce8c79d`) compared 4- and 8-adjacency only. A
measured "size ≥ 3" competitor still survived in 71/2000 6×6 contexts, so `51e67f2` adds every
positive threshold, under the supervisor's reading of the earlier root authorisation of
evidenced adjacency checks.
- **Bounds from demos.** For each connectivity, a marked demo component of size s bounds T ≤ s and an unmarked one bounds T > s. A partly marked component, or a changed non-target cell, rules that connectivity out.
- **Query check.** Marked sets are nested in T, so the two extremal surviving thresholds decide agreement exactly. The upper one is capped at the largest query component + 1, where nothing is marked.
- **Cross-check.** Tests compare this against an exhaustive brute force of 34 rules on 300 random grids.
- **Measured breakdown.** The 6×6 numbers above come from the final gate on the current constructor. The pre-threshold measurement is kept in `batch-e-evidence-pre-threshold-b9480e9.json`.

The gates rule out only the listed alternatives. They are not identifiability proofs.

## Certificates (final bytes)

**Standard `recertify.check` (2 workers).** All four passed:
- 1000 fresh / 8000 D4 / 16 fixture variants;
- 0 sampler rejections;
- 1000 unique inputs.

Provenance, `draft_notes` and `limitations` were merged in, and
`previous_constructor_sha256` was recorded. Only the stale `seed`/`d4` fields were dropped.

| ID | constructor (prev → new) | factory |
|---|---|---|
| 0c786b71 | 7fc6d170 → 64010e00 | 871a44a1 |
| e0fb7511 | 3857588f → d2a9f6e3 | 66678c1e |
| f0df5ff0 | df76beda → 0c452608 | d3eb4c59 |
| f3cdc58f | 763478e5 → abd953bb | 81c2164b |

**Gate-aware context audit (`context_audit.py`, run last; `context-audit.json`).**
- 250 fixed queries per run.
- Demos are drawn at the query's input shape, which is the strict uniform/seen profile.
- At most 64 contexts per query.
- `make_record` on all 8 D4 transforms with a seeded palette, plus a check that the gate's unique prediction equals the label.
- Source hashes are pinned, including `factory_certificate`.

| ID | default: accepted / retries / query shapes | min corner (0c 2×2, e0/f0 6×6, f3 4×4): accepted / retries |
|---|---|---|
| 0c786b71 | 250/250 / 0 / 137 | 250/250 / 0 |
| e0fb7511 | 250/250 / 0 / 208 | 250/250 / 11 (10 ambiguous first contexts; 9 queries needed 1 retry, 1 needed 2) |
| f0df5ff0 | 250/250 / 0 / 201 | 250/250 / 0 |
| f3cdc58f | 250/250 / 0 / 214 | 250/250 / 0 |

Every run made 2000 `make_record` calls, and no query failed. Mixed-shape first contexts were
never ambiguous. These numbers come from the refresh on the final gate bytes (method version 2:
predictions via `candidate_predictions`). Compared with the pre-threshold audit, kept as
`context-audit-pre-threshold-b9480e9.json`, only e0fb7511@min_corner changed: 3 → 10
ambiguous first contexts, and 3 → 11 retries. The coverage sections of `batch-e-evidence.json`
reproduced exactly.

## Coverage (1000 draws, same seeds; `batch-e-evidence.json`)

Before = legacy bytes from `c201cfe` (hash-checked); after = current defaults.

| ID | input shapes | shapes with ≥ 4 pairs | family statistics, before → after |
|---|---|---|---|
| 0c786b71 | 1 → 194 | 1 → 147 | output up to 30×30; inputs with 1/2/3 colours: 0/27/973 → 1/9/990 |
| e0fb7511 | 1 → 515 | 1 → 55 | black density 0.10–0.23 → 0.11–0.41; largest component 12 → 32; azure 13–25 → 3–233 |
| f0df5ff0 | 1 → 497 | 1 → 45 | seeds 2–8 → 2–29 (27 distinct counts); confetti 0.36–0.59 → 0.20–0.56 |
| f3cdc58f | 1 → 541 | 1 → 37 | max bar 8 → 24; 591/1000 with a bar > 8; ink density 0.08–0.30 → 0.02–0.50 |

All draws give 1000/1000 unique inputs, with 0 registered-checker disagreements before and
after. These come from a bounded pool, so they are not a finite-capacity claim.

## Limits

- **e0fb7511 low densities.** Explicit densities well below 0.15 on large canvases can make the area-scaled azure floor unlikely within the attempt budget: all five measured 30×30 draws at 0.10 exhausted the budget in about 0.1 s each. This is not proof of impossibility. Pass `min_marked` to lower the floor. The random range starts at 0.15 for this reason; the review suggested 0.10.
- **f0df5ff0 dense explicit requests.** At full capacity, all windows can still fail the per-window visibility guard within 200 attempts (about 3% success per attempt at confetti 0.5 with 100 windows), which raises `RuntimeError`. Dense lattice layouts are also more regular than the scattered default.
- **Random minima are a sampling choice**, not a semantic restriction: 0c 2, e0/f0 6, f3 4. Explicit sizes go lower.
- **Production shape support.** Strict same-shape support in the production pool was estimated only from draw statistics (shapes with ≥ 4 pairs). No prepare run was done.
- **Batch D re-certification.** Batch D's `context-audit.json` pins the old shared hashes. Root authorised a real rerun, which is committed separately after this one.
- **Batch D rerun comparison.** Semantic metrics and retry counts reproduced exactly. The shared dependency hashes and measured runtimes changed; the preceding report is preserved as `context-audit-pre-batch-e-db16125.json`.
- **Batch D after the threshold gate.** None of batch D's pinned sources changed in `51e67f2`, because it does not depend on `mirror_neighbourhood_evidence.py`. A `--no-write` rerun of its `context_audit.py` on the final bytes matched the committed `context-audit.json` in every field except runtimes, so the D files were left unchanged.
- **Standard certificates were not rerun for the threshold gate.** Constructors and factories are unchanged, and `recertify.check` does not run the gates.

## Tests

| Test file | Covers |
|---|---|
| `diversity/test_native_batch_e.py` | fixture replay; legacy canvas and RNG replay; random-domain structure; partial and explicit arguments; invalid arguments, including floats; boundary shapes on both sides via checker and factory on 8 D4; dense f0 under a 3 s deadline; bounded `RuntimeError`; gate witnesses are constructor scenes; certificate and audit hash binding |
| `test_mirror_neighbourhood_evidence.py` | fixture acceptance (canonical and teaching, 24 variants); anchor, adjacency and dilation witnesses; e0 threshold witnesses (no isolated cell → T = 1, no marked pair → T = 3, only 4-cell components → T 2..4, nothing marked → T unbounded); informative contexts accept any query; no-fit demos; exhaustive brute-force cross-check; `make_record` runs the gate while `verify` passes; f3 not gated |
| `diversity/test_e0_f3_verifiers.py` | checker registration, fixtures, counterexamples, adversarial cases, raising on out-of-domain inputs |
