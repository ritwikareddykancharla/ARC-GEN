# Native batch a04b (2026-10-25): a04b2602 rectangle spacing, red rate, checker and gate

Base `9498a90`. ID: `a04b2602` only. The batch-22 semantic review
(`native-domain-review-20261024/semantic_reviews.json`) was treated as evidence to
check, not as authority. Its placement finding was confirmed. Its
"demonstration context: intrinsic" disposition was **not** confirmed: the competitor
assessment below finds a demonstration gap that predates this batch.

**Not production-ready.** a04b2602 is not admitted, not in `prepare.REPAIRED` or
`prepare.REVIEWED_NATIVE`, and not in any registry. Two shared files changed:
`verified_rules.py` (one checker for this ID) and `colour_evidence.py` (one 4-line
dispatch). Root must therefore rebuild admission and rerun the shared audits that pin
those hashes. **No prepare export was run.** Admission, prepare, fixtures, policies,
registries, vendored RE-ARC, `recertify.py` and the direct factory were not changed.

## Commits

| Commit | Scope |
|---|---|
| `b64ed3c` | constructor; recertified factory record and native-certificate mirror; reviewed checker `verified_rules.rectangle_red_rings` with its counterexample (`counterexample.py`, `a04b2602-archived-verifier-counterexample.json`) |
| `198f1cd` | shared: new `rect_ring_a04b2602_evidence.py` and the a04b2602 dispatch in `colour_evidence.py` |
| (this) | tests, competitor harness, batch evidence, context audit, report |

## Rule and what changed

The rule, colour roles, canonical labels and factory are unchanged. Every red (2)
inside a green (3) rectangle gets a 3x3 blue (1) ring. Rings overwrite green, black and
other reds, and the framed reds stay red. `validate()` replays all 4 canonical pairs
byte-identically.

| Axis | Legacy | Now (default sampling) | Why |
|---|---|---|---|
| spacing (line 61) | `overlaps(..., 2)`: min gap 2 | `SPACING = 1`: min gap 1 | canonical train[0] has rectangles one row apart (gaps 1, 2, 4), which was unreachable. Gap 0 would merge rectangles. |
| red rate (line 68) | 1/20 | 1/k, k ∈ 12..30 per scene | the rule acts on each red cell; canonical densities 0.055..0.067 |
| retries | unbounded `while True` | 10 000 attempts, then `RuntimeError`, with no fallback | worst observed: 776 attempts in exploratory probes and 635 in `batch-evidence` (3-box placement), at about 5 ms |
| explicit `width/height` without `colors` | crashed | samples at that size (10..30) | same-shape demonstration contexts |
| canvas, box count, box sides | 10..30, 2..3, 4..side−6 | unchanged | count and size were judged "mixed" rather than clearly incidental; canonical values fit |

**Kept: the `outlined == expected` guard (line 75).** A scene is accepted only if the
reds with ≥ 2 orthogonal green neighbours are exactly the reds inside rectangles, and at
least one red is inside a rectangle. With spacing 1, this guard also rejects a red in a
one-cell gap that touches both rectangles. Without it, the neighbour rule frames that red
and the inside-rectangle rule does not (`probes.gap1_red_touching_two_rectangles`; the
reviewed checker raises there). The batch-22 review flagged this as uncertain, so it
stays outside the domain rather than being given a label.

**Explicit arguments are never replaced.** Explicit `colors` are drawn exactly as given,
without the guard, as before. 150 legacy draws re-entered explicitly reproduce the
legacy grids, tested against sha-pinned base bytes. `ValueError` is raised for:
- partial explicit arguments;
- non-int or bool dimensions, or dimensions out of range;
- `colors` of the wrong length.

The RNG stream changed intentionally.

### Before / after (2000 per-draw-seeded default draws each, `batch-evidence.json`)

| Measure | Legacy | Current |
|---|---|---|
| scenes whose min gap is 1 | **0** | **819** |
| min-gap histogram 1/2/3/4/5/≥6 | 0/1011/454/201/117/217 | 819/512/268/146/87/168 |
| pairwise gaps = 1 | 0 | 990 |
| red period k | 20 only | all 19 values 12..30 (87..120 each) |
| red density min/mean/max | 0.009 / 0.050 / 0.117 | 0.007 / 0.0515 / 0.129 |
| framed reds per scene, mean/max | 6.0 / 23 | 6.4 / 42 |
| box count 2/3 | 973/1027 | 973/1027 (same seeds) |
| box side min/median/max | 4/6/24 | 4/6/24 |
| distinct box sizes | 255 | 259 |
| distinct input shapes / unique inputs | 436 / 2000 | 436 / 2000 |
| placement rejections, total (mean, max per scene) | 260 495 (130, 2246) | 97 134 (49, 635) |
| guard rejections (`outlined != expected`), total (mean, max) | 178 (0.09, 3) | 526 (0.26, 5) |
| `RuntimeError` | 0 | 0 |
| archived checker / reviewed checker / factory program | **1998** / 2000 / 2000 | 2000 / 2000 / 2000 |

All rejections are counted. Guard rejections roughly tripled because of gap-1 facing
spans and denser red noise. This is a selection effect: in gap-1 scenes, the facing
gap span never holds a red. The constructor counts these rejections and does not hide
them.

## Pair checker: archived solver defect (pre-existing)

The archived reference solver frames the reds inside the bounding box of each
4-connected green component. Reds can cut one rectangle into several components: a full
red row or column, or a staircase that cuts off a corner. The cut reds then lie outside
every component box, so the archived solver leaves them unframed. The constructor frames
them, because they are inside the rectangle it drew and each has ≥ 2 orthogonal green
neighbours.

This defect **predates the batch**. With per-draw seeds (`counterexample.py`, 20 000
draws each):
- the legacy bytes give 7 archived disagreements (seeds 7157, 13561, …);
- the current bytes also give 7;
- `batch_evidence` legacy gives 2/2000.

The old certificate passed only because its 1000 seeded draws missed every such case.
At k = 12 the rate rises to about 0.2%, so recertify would have failed without a fix.

`verified_rules.rectangle_red_rings`, registered for this ID only, works as follows:
1. It merges green components while their joint box still holds only green and red.
   The merged boxes are the rectangles.
2. It requires the reds inside them to equal the reds with ≥ 2 orthogonal greens.
3. It raises instead of guessing when they differ. It also raises on colours outside
   0/2/3, on a green shape whose box holds black, and when no red is inside a
   rectangle.
4. Otherwise it draws rings in the constructor's order.

It is exact on the 4 canonical and 4 teaching pairs, and on all 40 000 legacy+current
draws. Its `VERIFIER_EVIDENCE` entry cites the counterexample file. The archived
reference packet and the factory are unchanged. The factory already unions the
component-box reading with the neighbour test, which is why it was exact on both
domains.

## Certificate (unmodified `recertify`, auditor `1e194cb8`)

| fresh | D4 checks | fixture variants | unique inputs | sampler rejections | constructor | factory (unchanged) |
|---|---|---|---|---|---|---|
| 1000 | 8000 | 16 | 1000 | 0 | `bdc12773` → `a141eb4b` | `d9e8477a` |

The certificate was run on frozen final bytes. It was rerun after the
`VERIFIER_EVIDENCE` entry was added, and the result is identical apart from the timing.
- `direct_factories/a04b2602.json` keeps `provenance` and `draft_notes` verbatim.
- It adds `previous_constructor_sha256` (`bdc12773`) and a `recertification_note`
  saying that the draft notes describe the legacy domain.
- The mirror is `native-certificates/a04b2602.json`. It had no mirror before.

## Competing-hypothesis assessment (`competitors.py`, `batch_evidence.py`)

There are 22 named, deterministic readings of one input, in the native frame:
- `native`;
- 8 alternative red selections, each with native painting: thresholds ≥1, ≥3, ==4 and
  8-way ≥2; all reds; the largest rectangle only (undefined on a tie); merged
  rectangles; and the archived component boxes;
- 13 alternative paintings, each with native selection: rings that spare other reds,
  spare green, or are clipped to the rectangle; a plus shape; a filled 3x3; and
  sequential stamping in each of the 8 D4 scan orders, where a later ring covers an
  adjacent framed red.

None (undefined) never fits a demonstration.

**Single-pair classification** (24 000 sampled pairs):
- **Identical on every sampled pair:** `select:inside_rectangle`, which is guaranteed
  by the guard.
- **Refuted by every pair:** `paint:filled`, `paint:plus`, `paint:spare_green`.
- **Separable:** the other 16.
- Fit rates: spare_reds 0.68, sequential 0.51, touch_ge3 0.50,
  component_bbox 0.999, largest 0.11, touch_ge1 0.09, touch8_ge2 0.09, clip 0.09,
  touch_4 0.05.

**Context ambiguity, ungated** (3 demos + 1 query, d4 = 0, identity palette, 2000
contexts each):

| Context | ambiguous | spare_reds | touch_ge3 | sequential (each order) | other |
|---|---|---|---|---|---|
| legacy independent | **393** | 179 | 137 | 132 | clip 3, touch_ge1 3, component_bbox 2, touch8 2, touch_4 2, largest 1 |
| current independent | **415** | 222 | 129 | 139 | touch_ge1 3, largest 2, component_bbox 1, touch8 1 |
| current same-shape | **386** | 206 | 109 | 132 | touch_ge1 6, touch8 5, clip 3, largest 3, component_bbox 1 |

These three readings are plausible ways to read the task:
- "the ring leaves other red pixels alone";
- "only reds surrounded on three sides";
- "stamp each ring in turn".

They survive whenever no demonstration shows, respectively:
- an unframed red under a ring;
- a framed corner red;
- two adjacent framed reds.

The canonical train pairs refute all three: train[0] refutes spare_reds, and
train[1..2] refute touch_ge3 and sequential. The canonical train context therefore
leaves only native, inside_rectangle and component_bbox, and has one answer on the
canonical test. The gap is about 20% in both legacy and current contexts, so it
**predates the expansion**. The gap-1 change does not add a separable reading, because
every reading that separates gap-1 reds is excluded by the guard.

## Evidence gate (`rect_ring_a04b2602_evidence.py`)

The gate follows the d47aa2ff pattern:
1. Undo the episode's palette and D4 using metadata only.
2. Keep the 22 rules that reproduce EVERY demonstration.
3. Require every survivor to give one defined answer on each query INPUT.
4. Otherwise raise `MissingColourEvidence`, and prepare resamples the demonstrations
   for the same query.

Query answers are never read. A test adds a bogus query answer and checks that the
verdict does not change.

The set is D4-closed: scan orders map to scan orders, and the other rules are
equivariant. Verdicts were D4-invariant in tests and in the audit. The gate is a
separate implementation from `competitors.py`, but uses the same rule names, and its
per-rule answers matched on 1500 exploratory draws (150 in the tests). All 9 stored minimal witnesses, covering all 16
separable readings, are rejected in all 16 frames. Canonical episodes pass all 16
`make_record` variants. The cost per context is 22 grids per input, with no search.

`select:component_bbox` is gated because it is the archived teacher program's reading.
A query whose rectangle is cut by reds therefore needs a demonstration with a cut. This
is rare: 1–2 per 2000 contexts.

## Fixed-query context audit (`context_audit.py`, `context-audit.json`)

Setup:
- 250 fixed queries per domain, and a query is never dropped or replaced.
- `default`: the default sampler.
- `gap1`: default draws whose query **input** has two rectangles exactly one cell
  apart, which is the newly admitted geometry. The condition reads only the input.
  364 draws that failed it are counted, and the first draw that meets it is the fixed
  query.
- Each query gets 8 same-shape contexts, all evaluated. The search continues up to 64
  if none is accepted.
- A context is accepted only if all of these hold:
  - the 4 inputs are orbit-distinct (`prepare.input_orbit`);
  - `make_record` passes on all 8 D4 under a seeded palette (gate plus program verify);
  - the independent harness leaves one answer on the query input.
- After acceptance only, the gate's unique answer must equal the label in every frame.
  Every pair label is checked by `verification_solver`.
- Run with 2 worker processes. Each domain was persisted as it finished.

| Domain | accepted | failed | panel acceptance | rejected / evaluated contexts | worst first index | D4-inconsistent | gate≠harness | mixed-context ambiguous (ungated) |
|---|---|---|---|---|---|---|---|---|
| default (193 shapes; 99 gap-1 queries) | **250** | 0 | 0.816 | 368 / 2000 (all gate) | 5 | 0 | 0 | 40 / 250 |
| gap1 (188 shapes; 250 gap-1 queries) | **250** | 0 | 0.8215 | 357 / 2000 (all gate) | 5 | 0 | 0 | 49 / 250 |

Both domains have `passed`, `semantic_checks_passed` and `all_queries_accepted` all
true.
- **Calls.** 26 200 `make_record` calls and 14 364 pair draws were made.
- **Rejections.** No context failed orbit distinctness. Every rejection was the gate,
  with 8 frames × 368 = 2944 and 8 × 357 = 2856 `MissingColourEvidence` messages. The
  harness flagged exactly the same contexts.
- **Panels.** Panels accepted at least 1 of 8 contexts for every query. The minimum
  was 1/8, for 2 default queries; no query needed the search.
- **Capacity.** Sampled orbit capacity is 3000/3000 distinct orbits at 10x10, 10x30,
  30x10 and 30x30, so no finite-capacity shortfall exists at these shapes. None was
  hidden by narrowing.

Seconds depend on machine load; counts are seeded.

## Tests (`arc_agi2/diversity/test_native_batch_a04b.py`)

All 35 tests pass. They cover:
- fixture replay, 16 canonical `make_record` variants with a unique gate answer, and
  canonical train[0] gap 1 now reachable;
- legacy explicit labels reproduced from sha-pinned base bytes;
- default-domain breadth and invariants: gap-1 scenes present, min gap ≥ 1, ≥ 15 red
  periods, and neighbour reading = inside reading;
- explicit extreme shapes; `ValueError` contracts; bounded retries without fallback
  (`RuntimeError`);
- the guard probes;
- the reviewed checker:
  - its registration and evidence entry;
  - exact on fixtures;
  - archived counterexamples replayed, including the legacy seed redrawn from base
    bytes;
  - off-domain inputs raise;
- the gate:
  - its rules equal the harness rules, with per-rule answers matching;
  - the dispatch routes to it;
  - every witness is rejected in all 16 frames;
  - verdicts are D4-invariant and answer-blind;
  - canonical refutation of the separable readings;
- before/after domain evidence, capacity, the audit's query accounting, the certificate
  and mirror pins, and the evidence and audit source pins.

## Source pins at the freeze (sha256 prefixes; full hashes in the JSON files)

| File | Hash |
|---|---|
| `tasks/task_a04b2602.py` | `bdc12773` (base) → `a141eb4b` |
| `direct_factories/task_a04b2602.py` | `d9e8477a` (unchanged) |
| `direct_factories/a04b2602.json` | `2dca0a23` (base) → `3a24802c` |
| `verified_rules.py` | `3a3425ae` (base) → `17519b6d` |
| `colour_evidence.py` | `7da81112` (base) → `10880dcd` |
| `rect_ring_a04b2602_evidence.py` | `ca28f724` (new) |
| `recertify.py` | `1e194cb8` (unchanged) |
| `program_targets.py` / `prepare.py` | `88298f33` / `52df35f6` (unchanged) |
| `references/a04b2602.json` | `6d9dd41d` (unchanged) |

## Known consequences and remaining blockers

- **Shared pins (hash only, kept separate from semantics).** I ran the 12 suites that
  touch `verified_rules.py` or `colour_evidence.py`: 17 failed and 338 passed. I reran
  the 17 with both shared files restored to base bytes, then restored and
  hash-verified them afterwards.
  - **16 fail at base too, so they predate this batch:**
    - `test_native_batch_d` and `test_native_batch_e`
      `test_certificates_bind_current_bytes` (4 + 4);
    - `test_native_batch_f::test_context_audit_binds_current_sources`;
    - `test_native_batch_g`: `test_context_audit_is_current_and_passed` (2) and
      `test_evidence_report_is_current`;
    - `test_native_batch_i::test_context_audit_bound_to_current_sources`;
    - `test_native_batch_c7d4_d47a::test_evidence_and_audit_pin_current_sources`. Its
      `colour_evidence` pin `9f984181` already differed from base `7da81112`.
    - `test_34b99a2b_midpoint_verifier::test_registered_and_documented` and
      `test_195_281_geometric_verifiers::test_only_authorised_ids_added`. These exact
      `VERIFIERS` key-set assertions were already broken by `b4a43f3b`, and they now
      also list `a04b2602`.
  - **1 is new and hash-only:**
    `test_b4_verifier::test_evidence_report_bound_to_current_sources` pins
    `verified_rules.py` `3a3425ae` (now `17519b6d`).
  - No semantic failure was found. Older reports were not edited or rehashed, and root
    reruns the shared audits after integration.
- **Review inventory.** The batch-22 record pins constructor `bdc12773`, so
  `extract.py --check` will mark it stale. A re-review record is out of scope.
- **Admission** pins `colour_evidence.py` and `verified_rules.py`. Root must rebuild it.
- **Production context cost.** The gate rejects about 20% of random contexts, and about
  18% of same-shape panel contexts in the audit (368 and 357 of 2000). Prepare resamples demonstrations
  for the same query. Production quota support at prepare's budgets is unmeasured.
- **Finite competitor set only.** Readings not on the list are not excluded. Learned
  colour lookups were not assessed separately, because ring and red colours are fixed
  rule colours in every demonstration (the factory treats them as palette constants).
- **Distribution shift.** Red noise now ranges from sparse (k = 30) to dense (k = 12).
  Gap-1 scenes are about 41% of draws, against one of the four canonical pairs. The
  facing span of a gap-1 pair never holds a red (guard selection).
- **Not done here:**
  - box counts 1 or ≥ 4;
  - box sides < 4 or > side − 6;
  - touching rectangles (gap 0);
  - labelling reds that touch two rectangles across a gap.

  These would change the rule's evidence or need a semantic decision the fixtures do
  not show.
