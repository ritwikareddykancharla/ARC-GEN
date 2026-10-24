# Native batch G (2026-10-25): 8ba14f53 placement/canvas, 4cd1b7b2 blank counts

Base `e72190b`. IDs: `8ba14f53`, `4cd1b7b2` only. The batch-5 semantic review
(`native-domain-review-20261024/semantic_reviews.json`) was used as evidence to
check, not as authority. Every claim below was re-measured here.

**Not production-ready.** Neither ID is admitted, in `prepare.REPAIRED`, or in
`REVIEWED_NATIVE`. `colour_evidence.py` changed (minimal dispatch only), so
root must rebuild admission and refresh the shared D/E audit pins after
integration. **No prepare export was run.** Admission, prepare, fixtures,
policies, registries, vendored RE-ARC and the direct factories were not changed.

## Rules and what changed

Rules, colour roles, canonical labels and factories are all unchanged. Both
`validate()` replays match the canonical fixtures exactly (7 and 4 pairs).

| ID | Rule (native) | Legacy | Now (default sampling) |
|---|---|---|---|
| 8ba14f53 | Holes of two boxes, left box first. Each box writes its colour once per hole cell in a row-major 3x3 grid, starting a new row | 4x9 canvas; box widths 3..5, heights 3..4; gaps 0..1 | H 3..30 x W 6..30 independently; random left margin, gap and vertical offsets; hole rectangles of area ≤ 6 (1x1..6x1, 1x6, 2x3, 3x2) with the legacy notch |
| 4cd1b7b2 | 4x4 Latin square over 1..4; holes (0) filled by single-line propagation | exactly 5 or 6 blanks | 1..7 blanks, roughly uniform |

Constructor rules:
- **Kept as rule-tied.**
  - 8ba14f53: two boxes in disjoint column ranges, the 3x3 output, and
    capacity overflow rejection. That is `draw()`, unchanged:
    ceil(a/3) + ceil(b/3) ≤ 3.
  - 4cd1b7b2: the 4x4 geometry and the four symbols.
- **Why 1..7 blanks.** Each blank is carved from a then-complete line, so
  reverse-order line propagation restores it and the completion is unique.
  Each carve permanently breaks the perpendicular line through the cell, so
  at most 7 of the 8 lines can be used. 1..7 is therefore the full range of
  the constructor's own scheme. The legacy full-visit scheme can only reach
  4..7.
- **Excluded: more than 7 blanks.** These are not line-propagation solvable.
  The constructor's own labeller (`solve`) would leave zeros. They would need
  a different deduction (cell candidates or search), which is a rule change
  and not attempted.
- **Explicit arguments are never replaced.**
  - 8ba14f53: explicit `rows/cols/groups/colors` keep the legacy 4x9 canvas
    unless `height/width` are given.
  - Invalid values raise `ValueError`:
    - dimensions out of range or non-int, including bool;
    - partial explicit arguments;
    - out-of-canvas borders;
    - overlapping or right-of-left box ranges;
    - overflow, where the legacy code returned `None` grids;
    - 4cd1b7b2: `blanks` outside 1..7 or given with `colors`, malformed
      `colors`, and explicit scenes propagation cannot finish.
- **Retries are bounded** at 1000 attempts, after which the constructor
  raises `RuntimeError`. There is no fixed fallback.
- **RNG streams changed intentionally.** Legacy seeds do not replay.

## Demonstration-sufficiency gap (measured on the UNCHANGED legacy samplers)

The certified factories read only the query (4x4 / palette constants). A
passed certificate shows that the program agrees with the labels. It does not
show that three demonstrations establish the rule. `batch_g_evidence.py`
enumerates finite named competitor sets: the same sets as the gates. It counts
independent 3-demo + 1-query contexts (identity palette, d4 = 0, 2000 per row)
in which some competitor fits every demonstration but answers the query
differently.

| Sampler | 8ba14f53 ambiguous | 4cd1b7b2 ambiguous |
|---|---|---|
| legacy (base `e72190b`) | **1032 / 2000** | **182 / 2000** |
| current, independent contexts | 986 / 2000 | 291 / 2000 |
| current, same-shape contexts | 981 / 2000 | (always 4x4) |

Single-factor competitors, legacy → current contexts. One context can count
under several factors:
- **8ba14f53:**
  - order competitors:
    - top-first edge: 220 → 205;
    - bottom-first edge: 212 → 181;
    - more holes first: 231 → 189;
    - fewer holes first: 234 → 173;
    - colour index ascending: 117 → 140;
    - colour index descending: 137 → 137;
  - notch-blind bounding-box count: 221 → 182;
  - continuous fill (no new row per box): 17 → 50;
  - slot-order D4 image: 0 → 2.
- **4cd1b7b2:**
  - single-pass cell-candidate fill: 173 → 209;
  - single-pass line fill: 23 → 150;
  - rows-only and columns-only: 0 → 85 each. Rows-only is identical to its
    single pass, because filling a row never changes another row's blank
    count.

The gap therefore predates the expansion. For 8ba14f53 it is the dominant
effect: two boxes give one bit of order per demonstration. Even the 6
canonical demonstrations do not refute "top edge first, ties left"; the
canonical query happens to agree.

**2x2-box (Sudoku) rule (4cd1b7b2): assessed, not gated.** Box-valid squares
are a subset of the Latin squares, and the native completion is unique. So
when every demonstration output is box-valid, the box rule either reproduces
the native answer or has no completion on the query input. It never predicts
a different grid:
- current: 86 same, 87 none, 0 different;
- legacy: 80 same, 89 none.

In the "none" case the query input itself refutes the box rule. A witness is
stored (`sudoku_no_completion`).

## Evidence gates (`via require_colour_evidence → make_record`)

The gates follow the batch D/E pattern:
1. Keep the named rules that reproduce EVERY demonstration.
2. Require all survivors to give one answer on each query INPUT.
3. On failure, raise `MissingColourEvidence`, and prepare resamples the
   demonstrations for the same query.

Query answers are never read, and no context is chosen against the answer. A
pass only rules out the listed alternatives.

- **`hole_tally_8ba14f53_evidence.py`** (`f57fa7df`): 832 rules, the product of:
  - order (26):
    - left/right/top/bottom edge, ties broken by either perpendicular
      direction;
    - hole count descending or ascending, with a two-level spatial
      tie-break;
    - colour index ascending or descending;
  - slot order (8 D4 images of row-major);
  - layout (new row / continuous);
  - measure (hole cells / bounding-box area).

  The set is D4-closed and needs no episode metadata beyond `palette[0]`.
  A rule whose key ties completely is undefined: it cannot fit a
  demonstration, and if undefined on the query it counts as a distinct
  answer. A hole bordered by two colours, or by none, is rejected outright.
  Outputs are cached by (sequence, slot order, layout, measure), so at most
  64 grids are rendered per input.
- **`latin_fill_4cd1b7b2_evidence.py`** (`11c461a8`): 8 rules:
  - lines / cells / rows / columns iterated;
  - lines / rows / columns / cells single pass.

  The set is D4-closed (rows ↔ columns). The fill colours are the
  non-hole colours shown in the demonstrations. There must be exactly 4,
  and a query colour not among them is rejected.
- **`colour_evidence.py`** (`6789d3d8` → `56d94108`): two early-return
  dispatch branches, nothing else. Neither ID was in the generic colour list
  before, so they previously passed with no check. The change only adds
  strictness.

The colour-index orders make the 8ba14f53 verdict palette-dependent. That is
correct: whether the demonstrations refute "sort by colour" depends on the
visible colours. The verdict is D4-invariant within a palette; this is tested,
and the audit found 0 D4-inconsistent contexts.

**Not enumerated:** three or more boxes (never generated); box or border
counts (these always overflow); centre order (equal to edge order for disjoint
columns); hypotheses outside these factors. This is a finite assessment, not
an identifiability proof.

## Certificates (unmodified `recertify`, auditor `1e194cb8`)

| ID | fresh | D4 checks | fixture variants | unique base inputs | sampler rejections | constructor | factory (unchanged) |
|---|---|---|---|---|---|---|---|
| 8ba14f53 | 1000 | 8000 | 16 | 1000 | 0 | `4f1cca95` → `c468bb7e` | `82f82e9e` |
| 4cd1b7b2 | 1000 | 8000 | 16 | 998 | 0 | `30bf33e5` → `64151e8e` | `cf5a9135` |

The archived reference checkers agreed with every certificate label. They
also agreed on all 2000 + 2000 draws per family in `batch-g-evidence.json`,
legacy and current. No checker defect was found, and `verified_rules.py` is
unchanged (`a54743d7`).

The `direct_factories/*.json` records keep the old `provenance` and
`draft_notes` and add `previous_constructor_sha256`, as batch E did.
Mirrors are in `native-certificates/`.

## Fixed-query context audit (`context_audit.py`, `context-audit.json`)

Setup:
- 250 fixed queries per query domain. Each query gets a panel of 8
  independent same-shape contexts, ALL evaluated.
- A context is accepted only if `make_record` passes on all 8 D4 under a
  seeded palette (gate plus program verify). The gate's unique prediction
  must also equal the label; this is checked after acceptance, as a
  soundness check.
- If no panel context is accepted, the search continues up to 64 contexts.
- No query is dropped. Every label is checked by `verification_solver`.
- The query input is asserted unchanged across all of its contexts.

| Query domain | accepted | panel acceptance | panel contexts rejected / 2000 | worst first-accept index | queries needing > 8 | mixed first-context ambiguous | D4 inconsistent |
|---|---|---|---|---|---|---|---|
| 8ba14f53 default (210 shapes) | 250/250 | 0.497 | 1035 of 2034 evaluated | 25 | 5 | 136 | 0 |
| 8ba14f53 legacy 4x9 | 250/250 | 0.479 | 1066 of 2028 | 19 | 5 | 126 | 0 |
| 8ba14f53 min 3x6 | 250/250 | 0.887 | 227 of 2000 | 3 | 0 | 124 | 0 |
| 4cd1b7b2 default | 250/250 | 0.833 | 335 of 2000 | 4 | 0 | 42 | 0 |
| 4cd1b7b2 1 blank | 250/250 | 1.000 | 0 of 2000 | 0 | 0 | 0 | 0 |
| 4cd1b7b2 7 blanks | 250/250 | 0.646 | 711 of 2003 | 10 | 1 | 93 | 0 |

**Context variability for the same query.** The panel histograms show that
acceptance depends on the context, not on the query alone. For 8ba14f53
default:
- per-query accepted panel counts span 0..8;
- 5 queries had 0/8 and were then certified by search;
- 2..8 distinct surviving-rule sets per query (6..8 for 218 of 250);
- up to 24 distinct candidate answers in one panel.

Every accepted context gave the label, and no context was accepted on some
D4 and rejected on others. Rejection reasons are recorded per D4 call: 8 per
rejected context. Timings (`seconds`) are machine-load dependent and not
reproducible; all counts are seeded.

## Tests (`arc_agi2/diversity/test_native_batch_g.py`, 50)

The tests cover:
- fixture replay;
- 16 canonical gate+program variants with a unique correct prediction;
- each blank count 1..7 line-solvable, Latin and checker-agreed;
- default coverage of 1..7;
- 8ba14f53 breadth, disjoint columns, explicit canvas, legacy explicit
  canvas;
- `ValueError` contracts;
- every stored witness ambiguous and rejected, and witness queries resolved
  by resampled contexts;
- D4 invariance, with a bogus query answer not changing the verdict;
- the ambiguous hole-owner rejection;
- demonstrated-colour requirements;
- Sudoku non-competition;
- certificate, audit and evidence source pins.

## Source pins (sha256 prefixes at the freeze)

| File | Hash |
|---|---|
| `tasks/task_8ba14f53.py` | `c468bb7e` |
| `tasks/task_4cd1b7b2.py` | `64151e8e` |
| `hole_tally_8ba14f53_evidence.py` | `f57fa7df` |
| `latin_fill_4cd1b7b2_evidence.py` | `11c461a8` |
| `colour_evidence.py` | `56d94108` |
| `verified_rules.py` | `a54743d7` (unchanged) |
| factories | `82f82e9e`, `cf5a9135` (unchanged) |
| `recertify.py` | `1e194cb8` (unchanged) |

Full hashes are in `batch-g-evidence.json` and `context-audit.json`.

## Known consequences and residual limitations

- **Stale shared pins (hash only).** `test_native_batch_d.py` and
  `test_native_batch_e.py` `test_certificates_bind_current_bytes` fail: 8
  cases, all `colour_evidence` `6789d3d8…` ≠ `56d94108…`. No semantic
  failure. Root refreshes the D/E audits after integration; batch G did not
  edit their reports.
- **Review inventory.** `native-domain-review-20261024/extract.py --check`
  now reports the batch-5 records for both IDs as stale, because their
  constructor hashes changed. The four batch-E staleness errors already
  existed at base. A rereview record is out of scope here.
- **Production same-shape support is unmeasured.**
  - 8ba14f53 has about 670 canvas shapes (667 in 2000 draws), and prepare's
    uniform/seen policy needs at least 4 pool rows per shape.
  - In a fixed-shape pool, about half of first contexts are rejected by the
    gate.
- **Two boxes only.** A third box is admitted by output capacity but never
  demonstrated; the factory's ordering of three groups is unmeasured.
  Hole shapes are rectangles with the legacy notch only.
- **Distribution shift.** The default distributions differ from legacy:
  - 4cd1b7b2: 1–3-blank scenes are near-trivial as queries; the gate
    accepts all of them, since all rules agree.
  - 8ba14f53: larger canvases are mostly empty.
- **Finite competitor sets only.** Unlisted hypotheses are not excluded.
