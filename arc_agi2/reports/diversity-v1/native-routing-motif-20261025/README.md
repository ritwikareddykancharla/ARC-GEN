# Native routing/motif expansions (2026-10-25): 7491f3cf panels, 98c475bf width

Base `99def42`, in an isolated worktree. Only `7491f3cf` and `98c475bf` were
changed. **This is not production-ready.** Neither family was registered or
admitted. `admission.json`, `prepare.py`, `recertify.py`, `verified_rules.py`,
`colour_evidence.py`, the motif gates, the factories, the fixtures and the
labels are all unchanged. Root must integrate the work and rerun what is
listed under [Integration](#integration-root).

The batch-7 review (`df43372`, `59125f4`) was used as evidence to check, not
as authority. Every claim below was re-measured here.

## What changed

| ID | Legacy | Now |
|---|---|---|
| `7491f3cf` | Square N×N panels, N 4..6 (weights 1:3:1) | Independent panel H 3..28 × W 3..6, so the canvas is (H+2)×(4W+5) ≤ 30. 3×3 is excluded (see below). One default draw in four keeps the legacy squares; otherwise W is uniform and H is uniform for that W. The shape is drawn once per call and kept for every retry. |
| `98c475bf` | Width fixed at 20, height 12..30 | Per-scene width 18..30 (18 = the rightmost table decoration x=16, plus the interior and the border). Unconstrained calls draw it once, before any retry. An explicit `height` without `width` keeps the legacy width 20. |

**`7491f3cf` (constructor `tasks/task_7491f3cf.py`):**
- New arguments `panel_height` and `panel_width`. `panel_size` keeps its legacy 4..6 square semantics. Patterns may now be rectangular.
- The wall kinds are restated for rectangles:
  - straight row or column;
  - a corner-to-corner staircase diagonal;
  - an ell;
  - a monotone path along either axis.
- The pattern kinds are restated too: staircase X, plus, checker, blocks, ells, row or column stripes, ring, an inscribed diamond, four-fold symmetric, and random.
- Every guard is kept:
  - the wall splits the panel into exactly two 4-connected regions, each with at least 2 cells;
  - the dot is not 8-adjacent to the wall;
  - the fill colour is strictly dominant;
  - both regions contribute;
  - the patterns differ;
  - routing is not an overlay;
  - wall evidence is required on half of the draws.
- Square panels use the exact legacy random-draw order.
- The 400-try loop raises `RuntimeError` naming the shape. The shape is never changed to recover.

**`98c475bf` (constructor `tasks/task_98c475bf.py`):**
- The following are unchanged: the fixed five-colour table, absolute x from the left border, border distinctness, packing, clipping and collision checks, and the 500-try bound.
- Bounded stochastic exhaustion now raises `RuntimeError` naming the width, any requested height and the try budget.
- Invalid or incompatible explicit arguments still raise `ValueError`. That includes a fully explicit markers / line colour / height request with no free line row. The legacy code raised the same `ValueError`, but only after 500 identical retries.

### Correction to the 3×3 claim

The 3×3 exclusion follows from the retained **two-cells-per-region guard**.
It is not a geometric impossibility of the task. Exhaustive enumeration of
all 512 wall subsets of a 3×3 panel (8-connected, at least 2 cells) found:

- 192 walls that leave exactly two 4-connected regions;
- 16 of those 192 leave room for a dot, but every one of the 16 has a one-cell region;
- 40 walls pass the guard, and none of them leaves room for a dot.

Counterexample to removing the guard: wall (0,2),(1,2),(2,1),(2,0) with the
dot at (0,0) gives regions of 4 and 1 cells.

For comparison, 3×4 and 4×3 each have 425 walls that pass the guard, and 90
of them leave room for a dot. These numbers are in `domain-measurements.json`
and are tested.

The supervisor's independent count matched. The docstring, comment and error
message were corrected in `967c6b4`; this did not change behaviour. Allowing
one-cell regions is a separate future hypothesis, not adopted here.

## Final hashes (sha256)

| File | sha256 |
|---|---|
| `tasks/task_7491f3cf.py` | `7e63ecacb08572182b4784a718ad6063e2161482fcb06fc1895a347648d1650b` (legacy `43812195…`) |
| `tasks/task_98c475bf.py` | `8aa790e85569ce903d172a1c4cb5e4c6829ed5117125a3aba3554bf5e17f244e` (legacy `c7bac10a…`) |
| `direct_factories/task_7491f3cf.py` (unchanged) | `20e054e846172a50a7a52c168f5b7b347ea4b0eeabc61ebf90678fac796e515b` |
| `direct_factories/task_98c475bf.py` (unchanged) | `4ccb80b0d8523a3189b65009ebca2bd128def68d02f710911a7cddf95a29e87a` |
| `direct_factories/7491f3cf.json` (= native-certificates mirror) | `9c38aa6cb9f680e370c8ca8d641cabffd9accbdb2e1f37c8f9bb06984151ac1b` |
| `direct_factories/98c475bf.json` (= native-certificates mirror) | `b8bad388818bb89ed51a1397483856b060482190425a8165edf2842ed22e2e22` |
| `certify_98c475bf.py` (adapter) | `f1f6ed31da74a0879ab54e9ff86f5931014974e15927ef6f7b007c2d3158ca84` |
| `history.py` | `936ad4fc22575a1b0769098e9e8629cccfe172147e238a774bc778890ed03d26` |
| `context_audit.py` / `context-audit.json` | `a4f5ba75…` / `db0a981a2791c27a49dd689b14403f5fa1d7cfb4f1e432ba5d803bdb2776d50d` |
| `domain_probe.py` / `domain-measurements.json` | `2b37c327…` / `1629ce0cdb34b55aad88c14e7028f2d3861ca7dd939fef2661ecd93030beb1c6` |
| `certificate-98c475bf.json` | `8ce46e195bd982358da2f09d0bfa5e9e0d7e61f55820eaaf96c8765f1c686588` |
| `line_motif_evidence.py` / `colour_evidence.py` / `motif_context.py` (pinned, unchanged) | `f99a8a9b…` / `e5e26894…` / `9e0c64c5…` |
| `diversity/test_native_routing_motif.py` | `ff4fe8f4490d3c2a075726a714f31e917d035ce224d33092d2964884e0384f20` |

## Certificates

**`7491f3cf`: the standard harness passed.** The command was the unmodified
`python -m arc_agi2.diversity.recertify 7491f3cf`, run on the final
constructor bytes. Results:
- 1,000 fresh pairs, 8,000 D4 checks and 16 fixture variants;
- 1,000 unique inputs and no sampler rejections.

The raw harness output is kept byte for byte as `standard-recertify-7491f3cf.json`.

**`98c475bf`: the standard harness fails, and its failure is kept.** The
report is in `standard-recertify-98c475bf.json`. The run checked all 16
fixture variants and then stopped on the first fresh episode with
`ValueError('Conflicting demonstrated motifs for one colour')`: among four
independent draws, the same colour was demonstrated at two widths.

`context-audit.json` replays the harness's own 300 seeds for both versions:

| Version | Gate accepted | Undemonstrated marker colour | Mixed widths |
|---|---|---|---|
| Legacy | 246 | 54 | none |
| Now | none | none | 300 |

So the standard harness could not certify this family before the change either.

**`98c475bf`: the root-authorized dedicated adapter passed.** The adapter is
`certify_98c475bf.py`. It holds 1,000 fresh default queries fixed and
resamples only the three demonstrations, at the query's own canvas shape (at
most 64 contexts per query). A context is accepted only by the production
gate (`require_colour_evidence` → `line_motif_evidence`). The gate sees the
demonstrations and the query input, under all 8 D4 transforms with a seeded
palette, and its verdicts must agree across D4. Labels never select a context.

After acceptance, these must all hold, or the certificate fails:
- the gate's prediction is exact under 8 D4;
- the factory program (`verify`, every demonstration and the query) is exact under 8 D4;
- `motif_context` is exact at d4 0.

The archived verifier checks every drawn label. Results:

| Measure | Value |
|---|---|
| Queries accepted | 1,000/1,000; 0 failed, replaced or dropped |
| Distinct episode identities | 1,000 |
| Unique raw query inputs | 1,000 (997 D4/palette orbits; 3 duplicate orbits reported, not replaced) |
| Query shapes | 237; all 13 widths, 69..93 queries each |
| Query D4 checks | 8,000 |
| Demonstration D4 checks | 24,000 (3,000 accepted demonstrations) |
| Fixture variants | 16 |
| Rejected contexts | 244: 238 by the gate (missing motif evidence), 6 for duplicate orbits; no sampler exhaustion |
| Retry histogram | 0: 814, 1: 146, 2: 27, 3: 9, 4: 3, 5: 1 |
| Labels checked by the archived verifier | 4,792 = 1,000 queries + 3,732 demonstrations drawn + 60 cross-width demonstrations |
| Cross-width control (20 queries) | refused 20/20 by the gate; the factory raised 20/20 (a raise is required, not just a wrong answer) |

The adapter pins its own hash and those of the constructor, factory, gate,
dispatch, native target, checker dispatch, archived reference, program
targets, augmentation, runtime, helpers, prepare, `direct_certificates` and
`common`. Only this family's records were updated.

**Records (`history.py`).** Measured fields come only from the runs. Each record also keeps:
- `provenance` and `draft_notes`, verbatim from `99def42`;
- `draft_notes_status`, marking the square and width-20 statements as historical;
- `previous_certificate`, holding the superseded values;
- `certificate_scope` and `certification_provenance`.

Each `native-certificates/<id>.json` mirror is identical to the admitted
record, as `test_pipeline.native_recertification` requires for `NEW_TASK_IDS`.

**What this does not establish.** The 98c475bf certificate covers only
same-shape demonstrated contexts. 7491f3cf has no demonstration-evidence gate
(`require_colour_evidence` falls through), and its factory reads panel order
from demonstrations or the D4 constant. A passing finite 7491f3cf certificate
shows only that the program is exact on the sampled scenes. It does not
establish exhaustive identifiability of the rule from three demonstrations
(for example against competing routing hypotheses), and it does not prove
correctness on every rectangle.

## Context audits (`context_audit.py`)

Each domain used 250 fixed queries, with demonstrations resampled at the
query's shape. Every domain passed.

**7491f3cf**, through the production `make_record` path: 2,000 calls and
8,000 pair checks per domain.

| Domain | Queries accepted | Rejected contexts |
|---|---|---|
| default (90+ shapes) | 250/250 | none |
| 5×5 | 250/250 | none |
| 3×4 | 250/250 | 5, all duplicate orbits |
| 4×3 | 250/250 | none |
| 28×6 | 250/250 | none |

**98c475bf**, through the adapter: 2,000 query and 6,000 demonstration D4 checks per domain.

| Domain | Rejected contexts | Unique raw queries | Distinct orbits |
|---|---|---|---|
| 12×18 | 97 | 242 | 89 |
| 20×20 | 42 | 248 | 225 |
| width 30 | 57 | 250 | 250 |

The 12×18 minimum canvas is close to finite.

## Measurements (`domain_probe.py`)

Each version was sampled with 2,000 default draws under the same seeds. The
legacy source is loaded from the `99def42` blobs, and the output was
byte-identical on two runs. There were no errors in any version.

**7491f3cf (before → after):**
- **Shapes:**
  - panel shapes 3 → 103;
  - aspect ratios, before all 2,000 square, after 578 square, 1,328 tall and 94 wide;
  - largest single shape 58% → 16%.
- **Uniqueness:** unique orbits 1,987 → 1,999.
- **Walls:**
  - kinds, after: straight 461, diagonal 331, ell 718, path 490;
  - straight walls cover both axes (223 rows, 252 columns);
  - wall length, mean 5.2 → 9.0, maximum 9 → 28.
- **Patterns:** all ten kinds are reached; pattern cells, mean 11.2 → 21.1.
- **Dots:** distinct dot placements 72 → 1,237.
- **Wall evidence:** both-branch share 0.656 → 0.669.
- **Ink density:** mean 0.374 → 0.337, minimum 0.176 → 0.056. Tall panels are sparser; this is the density tradeoff.
- **Retry budget:**
  - the worst shape with wall evidence required is 4×3, at an acceptance rate of 0.063;
  - the chance of exhausting the 400 tries there is about 10^-11;
  - 60 calls on each of the 103 shapes raised no `RuntimeError`.

**98c475bf (before → after):**
- **Shapes:** canvas shapes 19 → 247, with all 13 widths at about 8% each.
- **Uniqueness:** unique orbits 1,868 → 1,989.
- **Placement:** distinct marker layouts 1,692 → 1,965.
- **Unchanged:** the marker-count, line-colour and marker-colour distributions.
- **Ink density:** interior ink, mean 0.110 → 0.104.

**Same-shape pool support (export risk).** This is measured with
`prepare.query_support` (imported read-only) on a 560-row pool, the
`--train 200 --validation 20` target.

| Family | Shape bins (before → after) | Feasible query rows (before → after) |
|---|---|---|
| 7491f3cf | 3 → 102 | 100% → 84.3% |
| 98c475bf | 19 → 219 | 100% → 41.1% |

For 98c475bf, only 34.6% of rows also have the motif coverage the gate needs.
At 2,000 rows, support is 100% (7491f3cf), and 98.6% and 97.2% (98c475bf).
Prepare extends pools while support is short, but **no prepare export was run**.

## Tests (results already obtained; nothing was rerun for this README)

- **Focused tests:** `arc_agi2/diversity/test_native_routing_motif.py` passed 36/36. They cover:
  - canonical replay, and legacy replay against the `99def42` blobs;
  - argument validation and shape boundaries;
  - the preserved guards, and wall and pattern kind coverage;
  - the scoped 3×3 enumeration;
  - bounded `RuntimeError` with the shape unchanged;
  - `ValueError` versus `RuntimeError` for 98c475bf;
  - absolute decorations at other widths;
  - gate acceptance and refusal;
  - hash binding, history and count reconciliation, and a fixed-query adapter run.
- **Shared tests** (`test_pipeline`, `test_line_motif_evidence`, `test_contextual`, `test_program_targets`): 199 passed and 1 failed, after certification. The failure is `test_contextual.py::SharedPictureTests::test_builder_preserves_context_and_split_through_d4`, a pyarrow `ArrowTypeError`. It already fails at `99def42`, before any change here. Between the constructor change and recertification, two line-motif tests failed because the old certificate was hash-stale. Both pass now.
- **Broad suite `arc_agi2/diversity` with `-x`:** 215 passed, then it stopped at its first failure, `test_native_batch_d.py::test_certificates_bind_current_bytes[195ba7dc]`. Batch D's audit pins `colour_evidence.py` as `51a6c404…`, but the file is `e5e26894…`. That file was last changed in `35aa0fb` (batch G, before this base) and is untouched here, so the stale pin predates this work. A later run without `-x` was **interrupted by the supervisor and is recorded as interrupted, not passed**. The rest of the broad suite has not been run here.

## Limitations

- **7491f3cf:**
  - Rectangular panels are a hypothesis supported by the rule, not shown by any fixture: all five are 5×5.
  - The staircase X and diagonal, and the inscribed diamond, are this batch's restatements.
  - The ≥2-cells-per-region guard stays, so 3×3 is excluded.
  - The layout (four panels in a row) and the colour roles are fixed.
- **98c475bf:**
  - The five-colour motif table and the absolute left anchoring are fixed.
  - Novel-width and cross-width anchoring are undetermined and refused.
  - Same-width demonstrations are required.
  - Demonstrations for an explicit-height query come from `generate(height=, width=)`. That is not exactly the default sampler conditioned on the shape.
- **Both:** same-shape support is thinner (see the table above). This needs a real export measurement.

## Integration (root)

- Root `main` has moved (`3f491aa`), and its shared dependency files differ from `99def42`. Before export, root must:
  - rerun `recertify 7491f3cf`, then `history.py 7491f3cf`;
  - rerun `certify_98c475bf.py --write`;
  - rerun `context_audit.py`.

  The adapter and audit pin `colour_evidence`, `program_targets`, `verified_rules`, `prepare`, `runtime` and the other shared files. There must be no hash-only refresh.
- Register both families in `prepare.REPAIRED` (or equivalent) and rebuild admission.
- Run an unmodified prepare 200/20 export that reports same-shape and motif-evidence support.
- The batch D stale `colour_evidence` pin and the pyarrow failure belong to root and predate this work.

## Commits

```
bc5dd77 7491f3cf: independent rectangular panel heights and widths
9c7747e 98c475bf: per-scene canvas width 18..30 with same-width motif anchoring
967c6b4 Scope the 3x3 exclusion and separate stochastic exhaustion errors
542d32b Certify 7491f3cf (standard) and 98c475bf (dedicated adapter) on final bytes
0d54ebd Focused tests, gate-aware context audits and before/after domain probe
```
