# Native batch D (2026-10-24): panel-size expansion for four Boolean/priority panel families

Base `a5251a7`. IDs: 195ba7dc, 281123b4, 31d5ba1a, 34b99a2b. These were RESERVED, unreviewed
inventory batch 5 entries. The inventory audit was static, so this report rests on its own
semantic review.

**Not production-ready.** `prepare` only accepts IDs that are admitted, REPAIRED or
REVIEWED_NATIVE, and these four are none of those. `admission.json` also pins
`verified_rules.py` and `colour_evidence.py`, which this batch changes. Root still needs to
rebuild admission, register the families, and run real unmodified 200/20 exports. **No prepare
export was run.** Admission, prepare and the registries were not modified or monkeypatched.

## Commits (kept separate)

| Commit | Scope |
|---|---|
| `0e03a1a` | `verified_rules`: 34b99a2b midpoint-divider XOR checker |
| `215d063` | `colour_evidence` → new `panel_overlay_evidence.py` gates for all four IDs |
| `3b4ed54` | `verified_rules`: 195ba7dc midpoint OR and 281123b4 fixed-separator priority checkers |
| (this) | constructors, recertified factory records, batch tests, evidence, context audit, report |

Shared-source hashes:
- `verified_rules.py`: d0b43e04… (base) → 055138a0… (`0e03a1a`) → 8ad9a385… (`3b4ed54`, final).
- `colour_evidence.py`: 9547c455… → 2617143c….
- `panel_overlay_evidence.py`: new, b78b1542….

`34b99a2b-verifier-evidence.json` deliberately keeps 055138a0…, the hash at its own commit,
as provenance. The refreshed certificates and context audit pin the final bytes.

## Semantic review (kept unchanged)

| ID | Layout | Colours | Rule |
|---|---|---|---|
| 195ba7dc | 2 panels side by side, divider column | 7 on 0, divider 2, output 1 | OR |
| 281123b4 | 4 panels side by side, 3 separator columns | 8, 5, 9, 4 on 0, separator 3 | priority overlay 9 > 4 > 8 > 5 |
| 31d5ba1a | 2 panels stacked, no separator | 9 over 4 on 0, output 6 | XOR |
| 34b99a2b | 2 panels side by side, divider column | 8, 5 on 0, divider 4, output 2 | XOR |

All fixtures replay byte-for-byte: 195ba7dc 5+5, 281123b4 7+7, 31d5ba1a 7, 34b99a2b 5+5
canonical+teaching pairs. Only the incidental fixed panel size changed. The direct factories
are unchanged; they cut by the separator colour, or by halving with the axis taken from D4.

## Constructor changes

- `width` and `height` now default to `None`.
- With every mask `None`, each missing dimension is sampled.
- If any mask is given, missing dimensions fall back to the legacy default.
- Explicit values (dimensions, masks, `False`/`True`) are never replaced. Only masks left as `None` are sampled.
- With explicit dimensions, the masks consume the RNG exactly like the legacy constructor (tested). The saved `parameter-validation.json` configurations therefore still reproduce.
- Invalid arguments raise `ValueError`: non-int or bool dimensions, out-of-range dimensions, wrong mask length, non-0/1 values, and masks that don't match the dimensions. No loops were added.

| ID | Explicit range (input and output ≤ 30) | Random range w × h | Legacy |
|---|---|---|---|
| 195ba7dc | w 1..14 (2w+1 ≤ 30), h 1..30 | 3..14 × 3..30 | 6×5 |
| 281123b4 | w 1..6 (4w+3 ≤ 30), h 1..30 | 4..6 × 4..30 | 4×4 |
| 31d5ba1a | w 1..30, h 1..15 (2h ≤ 30) | 3..30 × 3..15 | 5×3 |
| 34b99a2b | w 1..14, h 1..30 | 3..14 × 3..30 | 4×5 |

The random minima are a **sampling choice, not a semantic restriction**. They keep three-demo
contexts informative. Explicit sizes down to 1×1 are accepted, and sparse layouts are never
filtered. An earlier draft justified the minima by archived-verifier failures. That was wrong:
those failures also occur at 4×4 and larger, and they are fixed by the verifiers below.

## Shared verifier corrections (root-authorised, these three IDs only)

Each archived solver takes the first full uniform column as the divider or separator. A
valid sparse scene breaks all three at native size. For example, width = height = 4, with the
top mask filling column 0 and every other mask empty: archived 195ba7dc returns 4×0, and
archived 281123b4 returns 4×18 instead of 4×4. For 34b99a2b, any left-panel column of solid 8
is enough. The reviewed checkers read the fixed geometry, which holds in every fixture and
every constructor output. They raise ValueError on any other geometry.

| ID | Fixtures (reviewed exact) | Archived disagree: legacy / expanded / adversarial (≥4×4) | Reviewed disagree |
|---|---|---|---|
| 34b99a2b | 10/10 | 106/1000, 51/1000 | 0 |
| 195ba7dc | 10/10 | 0/1000, 3/1000, 52/290 (15) | 0 |
| 281123b4 | 14/14 | 1/1000, 184/1000, 146/538 (50) | 0 |

The evidence was measured on the legacy constructor bytes, using explicit-argument draws only.
Counterexamples are in `*-archived-verifier-counterexample.json`. The adversarial tests cover:
- empty panels;
- sparse, full-row and full-column panels;
- a different full column in each panel;
- 1×1, 1×2, 2×1 and other even/odd panel shapes;
- the max-30 compound grids and max−1.

## Evidence gates (`panel_overlay_evidence.py`, via `require_colour_evidence` → `make_record`)

- **281123b4:** enumerate the 24 priority orders of the visible panel colours. Keep the orders that reproduce every demonstration output. Every survivor must give the same answer on the query input.
- **Boolean IDs:** build the ordered (a, b) occupancy truth table. Every combination in the query must appear in the demonstrations, always with the same outcome. This is equivalent to requiring that all consistent truth tables agree on the query.

The gates work in visible coordinates: separators come from the palette, and the 31d5ba1a
split axis comes from D4, like the factory. They never read query answers (tested with an
input-only dict). On failure they raise `MissingColourEvidence`, so the exporter resamples
demonstrations for the same query. Canonical fixtures pass in 16/16 D4/palette variants for
each ID. Every canonical three-demo sub-context is informative (0/20, 0/140, 0/140, 0/20).

Concrete competing rules the gates now block:
- **OR vs XOR:** demos with no overlapping cells, e.g. every demo is `(0,0),(1,0),(0,1),(0,0)`, fit both OR and XOR. A query containing a (1,1) cell is rejected; a query without one is accepted.
- **Missing (0,0):** fully covered demos, e.g. `(1,0),(0,1),(1,1),(1,0)`, also fit "always on" (or "always off" under XOR). A query containing a (0,0) cell is rejected.
- **Missing (0,1) or (1,0):** "first panel only" fits the demos alongside OR/XOR, so the same rule applies.
- **31d5ba1a square inputs (w = 2h):** the shape alone does not give the split axis; the gate reads it from D4.
- **281123b4:**
  - Disjoint demos leave all 24 orders alive, so an overlap query is rejected.
  - Showing 9>4 and 4>8 resolves 9-vs-8 cells, because the candidates are total orders.
  - 5's rank stays open, so 9&5 cells and full-overlap cells are rejected.

Probe: seed 990000+i, three demos plus a query, number of ambiguous contexts.

| ID | legacy default | strict 3×3 | new mixed |
|---|---|---|---|
| 281123b4 | 60/2000 (9/200 for the first 200) | 193/2000 | 0/2000 |
| 31d5ba1a | 1/2000 | 1/2000 | 0/2000 |
| 195ba7dc | 0/2000 | 1/2000 | 0/2000 |
| 34b99a2b | 0/2000 | 1/2000 | 0/2000 |

## Certificates (final bytes)

**Standard `recertify.check` (2 workers).** All four passed with 1000 fresh / 8000 augmented /
16 fixture variants, 0 sampler rejections and 1000 unique base inputs. The factories are
unchanged and provenance was merged. `recertify.check` only calls `verify`, which does not run
the evidence gates, so a separate audit follows.

| ID | constructor (prev → new) | factory |
|---|---|---|
| 195ba7dc | 30fee2d9 → 5424f273 | e4f61296 |
| 281123b4 | 91c64590 → e6f2fe52 | 439cca9a |
| 31d5ba1a | d33bd3dd → 5bd13763 | c3092eb8 |
| 34b99a2b | e08df2c2 → bfe8a3ab | b22e39c8 |

**Gate-aware fixed-query context audit (`context_audit.py`, run last; `context-audit.json`).**
- Each run keeps 250 queries fixed and draws same-shape demos at the query's own dimensions, which is the strict production uniform/seen profile.
- Each query gets at most 64 contexts. A context is accepted only if `make_record` succeeds on all 8 D4 transforms and the gate's unique prediction equals the constructor label.
- The audit pins source hashes, including the final shared sources and `factory_certificate`.

| ID | default queries: accepted / retries | min-corner queries (281 4×4, others 3×3): accepted / retries |
|---|---|---|
| 195ba7dc | 250/250 / 0 | 250/250 / 0 |
| 281123b4 | 250/250 / 1 | 250/250 / 10 (10 first contexts ambiguous, all resolved in 1 retry) |
| 31d5ba1a | 250/250 / 0 | 250/250 / 0 |
| 34b99a2b | 250/250 / 0 | 250/250 / 0 |

Every run made 2000 `make_record` calls. No query was dropped or failed.

## Coverage (1000 default draws, `batch-d-evidence.json`)

| ID | input shapes before → after | unique inputs | shapes with ≥ 4 pairs (1000 → 4000 draws) | three-demo witness complete before → after |
|---|---|---|---|---|
| 195ba7dc | 1 → 314 | 1000 | 126 → 335 | 250 → 250 of 250 |
| 281123b4 | 1 → 81 | 1000 | 81 → 81 | 239 → 250 of 250 |
| 31d5ba1a | 1 → 339 | 1000 | 104 → 362 | 250 → 250 of 250 |
| 34b99a2b | 1 → 318 | 1000 | 112 → 336 | 250 → 250 of 250 |

## Limits

- The gates check only cell-wise occupancy and priority evidence. They do not rule out rules outside that hypothesis class, such as spatial or colour-identity rules.
- The 31d5ba1a gate depends on the episode's D4 metadata, as the factory does.
- Re-running `validate_parameters.py` would now find no int width/height defaults for these four, so it would propose no size overrides. The saved report still reproduces.
- Production shape support (strict same-shape demos) was only estimated from pool statistics. No prepare run was done.

## Tests

| Test file | Covers |
|---|---|
| `diversity/test_native_batch_d.py` | fixtures; legacy RNG replay; random ranges and structure; partial dimensions and masks; invalid arguments; max and 1×1 boundaries under the verifier and factory on D4; sparse full columns at every size; truth-table and priority witnesses; certificate and audit hash binding |
| `test_panel_overlay_evidence.py` | gate accept/reject cases; D4/palette; input-only query reads; `make_record` invokes the gate while `verify` alone passes |
| `diversity/test_195_281_geometric_verifiers.py`, `diversity/test_34b99a2b_midpoint_verifier.py` | verifier corrections |

Run results:
- The six batch D files, including `test_colour_evidence` and `test_verified_rules`: 195 passed, plus 104 subtests.
- batch B/C, `program_targets`, `pool_signature`, `hybrid_extensions`, `coverage_export_gates`: 125 passed.
- `generator_boundaries`, `sampling_domains`, `direct_certificates`: 17 passed.
