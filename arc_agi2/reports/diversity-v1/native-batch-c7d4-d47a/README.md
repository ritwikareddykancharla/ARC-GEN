# Native batch c7d4/d47a (2026-10-25): c7d4e6ad legend/canvas, d47aa2ff panels/counts

Base `99def42`. IDs: `c7d4e6ad` and `d47aa2ff` only. I treated the batch-3 semantic
reviews (`native-domain-review-20261024/semantic_reviews.json`) as evidence to check, not as
authority. Their "self-contained" demonstration disposition was **not** accepted: the
competitor assessment below finds a real demonstration gap in d47aa2ff that predates this
batch.

**Not production-ready.** Neither ID is admitted, in `prepare.REPAIRED`, or in any
registry. `colour_evidence.py` changed (one 4-line dispatch), so root must rebuild admission
and rerun the shared D/E/F/G audits after integration. **No prepare export was run.**
Admission, prepare, fixtures, policies, registries, vendored RE-ARC, `verified_rules.py`,
`recertify.py` and both direct factories were not changed.

## Commits

| Commit | Scope |
|---|---|
| `57bb479` | constructors; recertified factory records and native-certificate mirrors |
| `cb67c53` | shared: new `dot_motion_d47aa2ff_evidence.py` and the d47aa2ff dispatch in `colour_evidence.py` |
| `ca2e68e` | c7d4e6ad minimum canvas 4 (**withdrawn**; see below) |
| `e73297e` | undoes `ca2e68e`: constructor bytes restored exactly to `57bb479`, recertified |
| (this) | tests, competitor harness, evidence, context audit, report |

`ca2e68e` narrowed the valid pair domain because a 3x3 canvas has one input orbit. Root
corrected this: the generator's pair domain is kept separate from finite episode capacity.
`e73297e` restores H, W ≥ 3, and the shortfall is reported below. History is preserved.

## Rules and what changed

Rules, colour roles, canonical labels and factories are unchanged. Both `validate()` replays
are byte-identical to the canonical fixtures (3 and 4 pairs).

| ID | Rule (native) | Legacy | Now (default sampling) |
|---|---|---|---|
| c7d4e6ad | every non-black cell takes its row's column-0 legend colour | 10x10; legend height 7..8 with one blank row above and below; 2..4 colours, runs 1..4; grey box at column 3, width 3..5 | H, W ∈ 3..30 independently; legend height 2..H at any offset (edges included); 2..8 colours, runs ≥ 1; grey box at any column ≥ 2, any width that fits |
| d47aa2ff | output = left panel; vacated cells red (2), arrived cells blue (1) | 10x10 panels (10x21 input); 5..10 dots; 2..3 colours; 1..2 movers | panels H 3..30 x W 3..14 (input H x (2W+1) ≤ 29 wide); 1..6 colours; 2..max(2, HW//9) dots; 1..min(colours, dots − 1) movers |

Measured over 2000 default draws (`batch-evidence.json`; legacy → current):
- **c7d4e6ad:**
  - 1 → 717 input shapes;
  - legend height 7..8 → 2..30;
  - colours 2..4 → 2..8;
  - top margin 1..2 → 0..26;
  - grey left column 3..7 → 2..27;
  - grey width 1..5 → 1..27.
- **d47aa2ff:**
  - 1 → 335 shapes;
  - dots 5..10 → 2..45;
  - colours 2..3 → 1..6;
  - movers 1..2 → 1..6;
  - kept dots 3..9 → 1..44;
  - knight-type moves per scene 0..2 → 0..5.
- The archived checkers agreed on all 4 × 2000 draws.

**Kept as rule- or evidence-tied (not incidental):**
- **c7d4e6ad:**
  - The legend is column 0, one contiguous run, made of distinct non-grey colours.
  - There are ≥ 2 legend colours.
  - There is one 4-connected grey shape, and its rows are **exactly** the legend rows.
  - At least one blank column separates the legend from the shape, and black stays the
    strict modal colour (the archived checker uses the modal background).
  - The off-domain probes show what each constraint protects:
    - A grey row outside the legend has an undefined key: the native rule turns that cell
      black, while all 15 competitors answer differently.
    - Legend rows without grey let `band_aligned_bottom` differ from the native rule.
    - A single-colour demonstration cannot refute whole-shape recolouring.
- **d47aa2ff:**
  - Colours avoid 0, 1, 2 and 5, so markers and the divider never collide with dots.
  - At most one mover per colour, which keeps the correspondence unique. The probe with
    two same-colour movers separates `matched_pairs_only` and the trail readings.
  - Dots are at Chebyshev distance ≥ 2 and there are no output-space collisions.
  - Every scene keeps ≥ 1 dot in place; the no-kept-dot probe lets `markers_only` survive.
  - The two panels are equal, with a central divider.
- **Displacement window kept** (5x5 without corner jumps). No listed competitor needs it;
  the gate handles both move lengths. But fixtures show moves of at most 2, and widening
  is not needed for the rectangle and count expansion. Widening would need evidence from
  the original task.

**Explicit arguments are never replaced.** Explicit `colors` (c7d4e6ad) and explicit
`rows/cols/colors/rdiffs/cdiffs` (d47aa2ff) use the legacy 10x10 canvas unless
`height/width` are both given.
- Partial dimensions, out-of-range or non-int (incl. bool) dimensions, and wrong lengths
  raise `ValueError`.
- So do scenes outside the documented domain. For d47aa2ff these are the cases where the
  legacy code returned `None` grids, plus marker or divider colours, no mover or no kept
  dot, and window violations.
- 150 legacy draws per family, re-entered explicitly, reproduce the legacy grids exactly
  (tested against the hash-pinned base bytes).
- Retries are bounded at 200 and then raise `RuntimeError`. There is no fallback. The RNG
  streams changed intentionally.

All (H, W) combinations were generated and checker-verified: c7d4e6ad 28 × 28 shapes,
d47aa2ff 28 × 12 shapes.

## Certificates (unmodified `recertify`, auditor `1e194cb8`)

| ID | fresh | D4 checks | fixture variants | unique inputs | sampler rejections | constructor | factory (unchanged) |
|---|---|---|---|---|---|---|---|
| c7d4e6ad | 1000 | 8000 | 16 | 1000 | 0 | `6c88d33d` → `bbdf032e` | `e7d7c61c` |
| d47aa2ff | 1000 | 8000 | 16 | 1000 | 0 | `fd5d1120` → `cead94cf` | `5206d6b2` |

Each certificate was run on frozen bytes:
- The c7d4e6ad certificate is from the restored bytes, after `e73297e`. The intermediate
  `c54d430c` (min-4) certificate is superseded.
- `direct_factories/*.json` keep `provenance` and `draft_notes` verbatim. They add
  `previous_constructor_sha256` (the legacy hash) and a `recertification_note` saying that
  the draft notes describe the legacy domain. The stale `seed`/`d4` fields were dropped.
- Mirrors are in `native-certificates/`.

## Competing-hypothesis assessment (`competitors.py`, `batch_evidence.py`)

Each competitor is a finite, named, deterministic reading of one input in the native
frame:
- c7d4e6ad: 16 rules, defined in `competitors.py`.
- d47aa2ff: 15 rules, those of the shipped gate.
- None (undefined) never fits a demonstration and counts as a distinct query answer.

**Single-pair classification** (2000 draws each, legacy and current identical):

| ID | refuted by any one demonstration | identical on every sampled input | separable (can cause ambiguity) |
|---|---|---|---|
| c7d4e6ad | right-edge key, top/bottom column keys, row shift ±1, component majority/top/bottom, reversed legend, erased legend | band aligned top/bottom, proportional band, nearest key, shape-colour-only (archived reading) | **none** |
| d47aa2ff | swapped markers, markers only, arrival keeps colour, vacated only, arrived only | right-panel base, colour-sensitive diff, matched pairs only | **6 movement trails** |

**Context ambiguity, ungated** (3 demos + 1 query, d4 = 0, identity palette, 2000
contexts each):

| ID | legacy independent | current independent | current same-shape |
|---|---|---|---|
| c7d4e6ad | 0 | 0 | 0 |
| d47aa2ff | **46** | **36** | **31** |

- **d47aa2ff trails.** These readings keep the native markers and also paint the path from
  each old cell to its new cell, red or blue, along a `line` (straight or diagonal) or an
  L (`rows-first` / `cols-first`).
  - If every demonstrated move is one step, these readings cannot be refuted. A query with
    a two-cell move then separates them.
  - All 46/36/31 ambiguous contexts are trail contexts, so the gap predates the expansion.
  - Witnesses for all six readings are stored and replayed by the tests.
- **c7d4e6ad: no gate.** Every separable alternative found needs a broken invariant, and
  the probes show which invariant blocks which competitor. A gate would never reject.
  `colour_evidence` has no c7d4e6ad branch.

**Learned colour lookups: assessed, not gated.** A lookup reading would copy a
demonstrated mapping instead of a visible colour:
- c7d4e6ad: the legend colour maps to an output colour.
- d47aa2ff: the dot colour maps to the marker colours.

Some query colour lacks a demonstrated entry in a large share of contexts:
- c7d4e6ad: 1131 legacy, 724 current;
- d47aa2ff: 1116 legacy, 884 current (of 2000).

These readings are not independently motivated, and gating them would be a blanket gate:
- c7d4e6ad copies the visible key cell, and every demonstration shows output = key colour.
- d47aa2ff's markers are the same two rule colours in every demonstration (the factory
  treats them as palette constants), so there is no variation for a lookup to explain.

## Evidence gate (`dot_motion_d47aa2ff_evidence.py`, d47aa2ff only)

The gate follows the batch D/E/G pattern:
1. Undo the episode's palette and D4 using metadata only.
2. Keep the 15 rules that reproduce EVERY demonstration.
3. Require every survivor to give one defined answer on each query INPUT.
4. Otherwise raise `MissingColourEvidence`, and prepare resamples the demonstrations for
   the same query.

Query answers are never read. A test shows that adding a bogus answer to the query does not
change the verdict. The set is D4-closed (transposition swaps rows-first and cols-first),
and tests show verdicts are D4-invariant. Canonical episodes pass under all 16 variants.

Gate cost per context is at most 15 grids per input, with no search.

## Fixed-query context audit (`context_audit.py`, `context-audit.json`)

Setup:
- 250 fixed queries per domain, and the query is never dropped or replaced.
- Each query gets 8 same-shape contexts, all evaluated. The search continues up to 64.
- A context is accepted only if all of these hold:
  - the 4 inputs are orbit-distinct (`prepare.input_orbit`);
  - `make_record` passes on all 8 D4 under a seeded palette (gate plus program verify);
  - the batch competitor set leaves one answer on the query input.
- After acceptance only, the unique answer is checked against the label.
- d47aa2ff's gate verdict is cross-checked against the competitor verdict.
- Every label is checked by the archived checker.
- Failed queries stay in the report with a reason.

| Domain | accepted | failed (reason) | panel acceptance | rejected / evaluated contexts | worst first index | D4-inconsistent | gate≠competitor |
|---|---|---|---|---|---|---|---|
| c7d4e6ad default (212 shapes) | 250 | 0 | 0.988 | 24 / 2000 (orbit dup) | 1 | 0 | – |
| c7d4e6ad 10x10 | 250 | 0 | 0.9995 | 1 / 2000 | 1 | 0 | – |
| **c7d4e6ad 3x3** | **0** | **250 (`same_shape_orbit_capacity`)** | 0.0 | 16000 / 16000 (orbit dup) | – | 0 | – |
| c7d4e6ad 3x30 | 250 | 0 | 0.9785 | 43 / 2000 | 1 | 0 | – |
| c7d4e6ad 30x3 | 250 | 0 | 0.9985 | 3 / 2000 | 0 | 0 | – |
| c7d4e6ad 30x30 | 250 | 0 | 1.0 | 0 / 2000 | 0 | 0 | – |
| d47aa2ff default (174 shapes) | 250 | 0 | 0.9885 | 23 / 2000 (gate) | 1 | 0 | 0 |
| d47aa2ff 10x10 panels | 250 | 0 | 0.9855 | 29 / 2000 (gate) | 1 | 0 | 0 |
| d47aa2ff 3x3 panels | 250 | 0 | 0.9075 | 185 / 2000 (142 gate, 43 orbit dup) | 2 | 0 | 0 |
| d47aa2ff 30x14 panels | 250 | 0 | 0.99 | 20 / 2000 (gate) | 1 | 0 | 0 |

- `semantic_checks_passed` is true in all 10 domains. Strict `passed` is false only for
  c7d4e6ad 3x3.
- 141,376 `make_record` calls were made in total.
- No c7d4e6ad context showed competitor ambiguity.
- Seconds depend on machine load. Counts are seeded.

**Finite capacity (reported, not narrowed).** The c7d4e6ad 3x3 pair domain is valid. An
exact enumeration found 112 inputs, all in **one** input orbit (`capacity` in
`batch-evidence.json`). So no strict same-shape 3x3 context exists.

Sampled orbits per 3000 draws:

| Shape | c7d4e6ad | d47aa2ff |
|---|---|---|
| 3x3 | 1 | 520 |
| 3x4 | 24 | 1258 |
| 4x3 | 5 | 1297 |
| 4x4 | 103 | 2138 |
| 3x30 | 1828 | – |
| 30x3 | 2695 | – |

- 3x3 is about 0.13% of default c7d4e6ad draws; no 3x3 query appeared in the default
  audit.
- The production assembler owns the strict orbit and shape shortfall policy.

## Tests (`arc_agi2/diversity/test_native_batch_c7d4_d47a.py`, 30 passed)

The tests cover:
- fixture replay, and 16 canonical `make_record` variants;
- legacy explicit labels reproduced;
- breadth and invariants for both families;
- explicit 3x3 and edge shapes;
- `ValueError` contracts;
- that c7d4e6ad has no gate and no competitor ambiguity;
- every trail witness rejected in all 16 frames, and a witness query resolved by a
  two-cell-move demonstration;
- D4 invariance and answer-blindness;
- that the gate rule set equals the report set and the classes;
- that the probes lie outside the domain;
- the capacity record, and that MIN_DIM is 3;
- that the audit keeps every query, with honest failures;
- certificate, evidence and audit source pins.

## Source pins at the freeze (sha256 prefixes; full hashes in the JSON files)

| File | Hash |
|---|---|
| `tasks/task_c7d4e6ad.py` | `bbdf032e` |
| `tasks/task_d47aa2ff.py` | `cead94cf` |
| `dot_motion_d47aa2ff_evidence.py` | `22a6ff5f` |
| `colour_evidence.py` | `e5e26894` (base) → `9f984181` |
| `verified_rules.py` | `a54743d7` (unchanged) |
| factories | `e7d7c61c`, `5206d6b2` (unchanged) |
| `recertify.py` | `1e194cb8` (unchanged) |

## Known consequences and remaining blockers

- **Stale shared pins (hash only, recorded separately from semantics).** 12 tests fail on
  the `colour_evidence` pin and nothing else:
  - `test_native_batch_d` `test_certificates_bind_current_bytes` (4);
  - `test_native_batch_e` `test_certificates_bind_current_bytes` (4);
  - `test_native_batch_f::test_context_audit_binds_current_sources` (1);
  - `test_native_batch_g`: `test_context_audit_is_current_and_passed` (2) and
    `test_evidence_report_is_current` (1).

  Their pins (`51a6c404` for D/E/F, `56d94108` for G) already differed from base
  `e5e26894` (batch H's change), so these 12 already failed at `99def42`. My dispatch
  moves the hash again. The other 307 tests in those suites pass. Root reruns the shared
  audits after integration; their reports were not edited.
- **Review inventory.** `extract.py --check` now marks the batch-3 records for both IDs as
  stale, because the constructor hashes changed. The other stale entries existed at base.
  A re-review record is out of scope.
- **Admission** pins `colour_evidence.py` and must be rebuilt by root.
- **Same-shape production support is unmeasured.** There are about 717 (c7d4e6ad) and 335
  (d47aa2ff) default shapes. The canonical profiles are uniform/seen, and 3x3 c7d4e6ad has
  no strict context.
- **Distribution shift.** Default scenes differ strongly from the legacy 10x10 look:
  - many c7d4e6ad grey boxes are 1–2 wide (width 1: 581/2000);
  - large d47aa2ff panels are sparse.
- **Finite competitor sets only.** Unlisted readings are not excluded. The learned-lookup
  readings are deliberately not gated.
- **Not done here:** displacement widening, grey rows outside the legend, multiple grey
  shapes, a legend away from column 0, and unequal panels. These would change the rule
  or need new evidence.
