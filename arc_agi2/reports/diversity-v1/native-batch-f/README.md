# Native batch F (2026-10-25): independent H × W for three self-tilers

Base `e72190b`. IDs: 27f8ce4f, 48f8583b, 5b6cbef5. I treated the native-domain review
(`native-domain-review-20261024/semantic_reviews.json`, batch 5) as evidence to check, not
as authority. Every figure below was re-measured here.

**Not production-ready.** These IDs are not admitted, REPAIRED or REVIEWED_NATIVE.
`admission.json` pins `colour_evidence.py`, which this batch changes. Root still has to
rebuild admission and run the unmodified `prepare` export. **No prepare export was run.**

**Pre-existing admission-pin failure.** `admission.json` already pinned
`verified_rules.py` 8ad9a385 and `colour_evidence.py` 2617143c, both older than the base
versions (a54743d7 and 6789d3d8). So
`test_diversity_profile.py::test_broader_sampler_is_deterministic_and_does_not_consume_caller_rng`
fails at base and still fails here, with "Target dependency changed since diversity
admission: arc_agi2/verified_rules.py". Batch F does not touch `verified_rules.py` or
`admission.json`, and it made no admission edits.
Admission, prepare, registries, policies and colour roles were not modified or
monkeypatched. The context audit below is not an export.

## Commits (kept separate)

| Commit | Scope |
|---|---|
| `da5bf43` | constructors; recertified factory records and native certificates; recertification runner; exact small-shape orbits |
| `bd3b09f` | shared: new `self_tiler_evidence.py`, three-ID `colour_evidence` dispatch, gate tests, pre-gate witnesses |
| (this) | constructor tests, context audit, coverage, report |
| next | batch D/E context-audit reruns on the final F shared sources |

Shared-source hashes:
- `colour_evidence.py`: 6789d3d8 → 51a6c404.
- `self_tiler_evidence.py`: new, 126ce138.

Between `bd3b09f` and the D/E rerun commit, the D/E audit-binding tests fail on the stale
`colour_evidence` pin. That is expected.

## Rules and what changed

Rules, colour roles, fixtures and the direct factories are unchanged:
- Factory hashes: f49052a7, f9862775, fd5d91b9.
- Canonical fixtures replay byte-for-byte.
- All three rules map an H×W input to an (H·H)×(W·W) output. Block (r, c) is a copy of the
  input when cell (r, c) is selected; otherwise it is filled with 0.

| ID | Selector | Was | Now (default) |
|---|---|---|---|
| 27f8ce4f | unique modal colour | 3×3; 3..5 colours, all used | H, W ∈ 2..5 independently; K ∈ 3..min(5, HW−1), all used |
| 48f8583b | unique least frequent colour | 3×3; legacy nominal 2..4-colour subset | H, W ∈ 2..5; same legacy subset semantics |
| 5b6cbef5 | non-zero (single-ink mask) | 4×4; ink 1..4; fair coin; non-empty | H, W ∈ 2..5; ink 1..9; fair coin; non-empty |

**Size bound.** Each axis must fit separately: H² ≤ 30 and W² ≤ 30, so H, W ≤ 5. The
largest legal input is 5×5, giving a 25×25 output; a size of 6 would give 36. The random
minimum is 2. Explicit dimensions must also be 2..5.

**27f8ce4f feasibility.** A unique maximum among K used colours needs HW ≥ K + 1, so 2×2
supports only K = 3.
- An infeasible explicit `num_colors` raises `ValueError("infeasible: …")` at once. No
  retries run and no random numbers are drawn (tested).
- Running out of attempts raises `RuntimeError("…budget…")`.
- An explicit `num_colors` with omitted dimensions only draws canvases that can hold it.

**48f8583b: legacy subset semantics retained** (root correction).
- The legacy sampler draws a 2..4-colour subset and does *not* require every subset colour
  to appear.
- Exact enumeration over K^9 legacy draws gives this used-colour distribution:
  1: 0.14 %, 2: 37.1 %, 3: 41.4 %, 4: 21.4 %. The "2..4 used" in the review overstates
  this.
- These semantics are kept as they were, including monochrome inputs, which have a unique
  minimum and every cell selected.
- Inputs with 1..4 used colours are therefore all valid. In 1000 default draws, 14 were
  monochrome (2 before).
- The feasibility bound HW ≥ 2K−1 (for K *used* colours) holds automatically, because
  infeasible counts simply never pass the unique-minimum check. A 4-colour subset at 2×2
  stays legal.

**5b6cbef5.**
- Ink widens from 1..4 to 1..9. This is role-safe: 0 is the fixed empty role, and both the
  archived checker and the factory test `!= 0`.
- Binary masks only by default. Full masks stay allowed, matching legacy.

**Explicit arguments keep every legacy label** (root correction). This is tested against the
hash-checked base bytes on 400 random explicit inputs per family, plus named cases:
- 27f8ce4f: explicit colour 0 still works.
- 48f8583b: zeros, ties (legacy smallest-colour tie-break) and monochrome inputs keep their
  labels.
- 5b6cbef5: several inks and empty masks keep the legacy colour-on-mask construction.
  These cases are outside the certified domain. With several inks, the legacy label is not
  a copy of the input, so the factory would disagree. The docstring says so.
- The only explicit inputs that now raise `ValueError` are the ones where legacy returned
  `None` grids (27f8ce4f ties) or crashed (27f8ce4f one colour: `IndexError`).
- New validation applies only to grids that were invalid anyway: non-int, bool, outside
  0..9, or wrong length.
- With omitted dimensions, explicit colours use the legacy canvas (3×3, 3×3, 4×4). Partial
  explicit dimensions take the legacy size for the missing axis.
- `num_colors`/`color` combined with explicit `colors` raises.

**Legacy RNG replay.** At explicit `height=width=3`, the 27f8ce4f and 48f8583b default
streams replay legacy exactly (60 seeds each, tested). The 5b6cbef5 stream differs, because
the ink range changed.

**Retries** are bounded at 200 per draw. There is no fixed fallback. Requests are never
relaxed.

## Independent checking

None of the three IDs has an entry in `verified_rules`. The archived reference solvers are
already dimension-correct (h·h × w·w):
- 27f8ce4f uses the modal colour.
- 48f8583b uses `argmin` over sorted values (the same tie-break as legacy).
- 5b6cbef5 uses a literal 0, so full masks and modal-background confusion are not a problem.

Results:
- **Checker vs constructor:** 0 disagreements in 1000 draws per family, before and after.
  Also 0 on all 16 shapes, both in tests and in recertification.
- **Rule-statement reference:** tests add a separate reference written from the rule
  statement. It raises on tied selectors and on several inks.
- **No shared checker edit** was needed.

## Demonstration evidence gate (`self_tiler_evidence.py`, root-authorised)

**What `colour_evidence` gains.** The only change is a 5-line dispatch for the three IDs.

**How the gate decides.**
- It keeps every candidate from a finite family that reproduces *every* demonstration.
  A candidate is (selector, placement, content, fill):
  - selectors: modal, minority, non_modal, non_minority, all, colour:c, not_colour:c,
    corner:k;
  - placement: a D4 transform of the block grid (shape-preserving ones, plus transposing
    ones for squares);
  - content: a D4 transform of the tile, or `solid`;
  - fill: 0..9, which is left free unless some demo shows an unselected block.
- All survivors must give the same answer on the query *input*.
- Query answers are never read.
- A survivor that is undefined on the query (a tied frequency selector) counts as a separate
  answer. A sole `None` answer is a failure (review fix, with a reachable adversarial
  regression: five constructor demos plus a tied-modal query).
- A brute-force check over all candidates agrees with the gate on 120 random contexts.
- This is a bounded hypothesis set, not an identifiability proof.

**Pre-gate witnesses** (`pregate-witnesses.json`; historical, carries the pre-gate source
hashes). I measured these before wiring the dispatch. Each context is strict same-shape, and
its 4 inputs have **4 distinct `prepare.input_orbit` values**. A witness is a context where
the named competitor fits all three demos but changes the query answer, while `make_record`
accepted the episode on all 8 D4 transforms. The table gives witness contexts per 1000
contexts.

| ID @ shape | fixed colour | frequency swap | corner anchor | stamp all | mono-fill |
|---|---|---|---|---|---|
| 27f8ce4f @3×3 / @2×4 | 12 / 10 | 0 / 0 | 172 / 187 | 0 / 0 | n/a |
| 48f8583b @3×3 / @2×4 | 7 / 16 | 0 / 0 | 37 / 26 | 0 / 0 | 0 / 0 |
| 5b6cbef5 @4×4 / @3×3 | 8 / 9 | 80 / 117 | 244 / 252 | 0 / 0 | n/a |

What the measurements show:
- **Confirmed:** fixed colour (all three families) and the sparse/dense frequency swap for
  one-ink masks.
- **Not reachable under orbit identity:** stamp-all and the 48f8583b monochrome-demo fill
  ambiguity. Both need every demo to select every cell. That means all monochrome or all
  full demos, which is a single orbit. The gate still covers them, and tests check the
  monochrome-demo case.
- **Not raised in review:** the corner-anchor competitor (cells matching a corner colour),
  which batch F added, is the most frequent one.

## Certificates (final bytes)

**Standard certificate.** `recertify_batch_f.py` runs the unmodified `recertify.check` from
a real `__main__` file with `ProcessPoolExecutor(max_workers=2)`. All three passed:
- 1000 fresh / 8000 D4 / 16 fixture variants;
- 0 sampler rejections;
- auditor 1e194cb8.

Factory `provenance` and `draft_notes` (explanation and limitations) were merged back in
verbatim. `previous_constructor_sha256` was recorded, and a `recertification_note` explains
that the draft notes describe the legacy 3×3/4×4 domain. The stale draft `seed`/`d4` fields
were dropped.

| ID | constructor (prev → new) | factory | unique inputs |
|---|---|---|---|
| 27f8ce4f | 70c1d22e → dc392a5e | f49052a7 | 1000 |
| 48f8583b | e03a032e → b3443161 | f9862775 | 999 |
| 5b6cbef5 | 7037789f → 2d4fa5b4 | fd5d91b9 | 981 |

**Gate-aware context audit** (`context_audit.py`, run after the final certificate; pins
`factory_certificate` bytes; `context-audit.json`).
- 250 fixed queries per run.
- Demos are drawn at the query's shape and must be exact-input distinct from each other and
  from the query.
- At most 64 contexts per query.
- Each context runs `make_record` on all 8 D4 transforms with a seeded palette, and the gate's
  unique `candidate_predictions` answer must equal the label.
- Every label is checked by the archived checker.

| ID | default: accepted / retries / max per query / first-context rejections | 2×2 min corner: accepted / retries / max / first rejections |
|---|---|---|
| 27f8ce4f | 250/250 / 71 / 4 / 49 | 250/250 / 223 / 7 / 113 |
| 48f8583b | 250/250 / 37 / 4 / 26 | 250/250 / 145 / 15 / 75 |
| 5b6cbef5 | 250/250 / 119 / 5 / 78 | 250/250 / 206 / 8 / 102 |

Every run made 2000 `make_record` calls, and no query failed. Default queries covered all
16 shapes. Edge-case queries were all accepted after context resampling:
- monochrome 48f8583b queries: 4 in the default run, 24 in the 2×2 run;
- full 5b6cbef5 masks: 3 in the default run, 17 in the 2×2 run;
- 5b6cbef5 ink ties: 43 default, 118 at 2×2.

Mixed-shape first contexts were rejected at 43, 22 and 78 of 250. Accepted default
contexts whose 4 inputs had 4 distinct orbits: 221, 224 and 207. The 2×2 runs are explained
below.

## Finite small-shape capacity (`small-shape-orbits.json`, exhaustive)

I enumerated every default-domain input. Orbits come from `prepare.input_orbit`; the split
comes from `finite_input_policy.input_split`.

| shape | 27f8ce4f orbits (train/val) | 48f8583b | 5b6cbef5 |
|---|---|---|---|
| 2×2 | 2 (2/0) | 2 (2/0): monochrome + one odd cell | 4 (4/0): background inversion merges 1/3 occupied cells |
| 2×3 ≡ 3×2 | 34 (32/2) | 25 (24/1) | 14 (13/1) |
| 2×4 | 688 (652/36) | 431 (409/22) | 44 (40/4) |
| 3×3 | 1785 (1698/87) | 970 (919/51) | 51 (50/1) |

These match the supervisor's independent 2×2 counts.

What this means for strict same-shape episodes:
- 27f8ce4f and 48f8583b: four-distinct-orbit episodes are impossible at 2×2.
- 5b6cbef5 at 2×2 has exactly 4 orbits, all train. There is no validation support, and
  train support is limited: every such episode must use all four orbits.
- Validation strict-shape episodes are impossible at 2×3 for all three families, and at 3×3
  for 5b6cbef5.

My 2×2 audit used exact-input distinctness, so it mainly reflects gate behaviour. Of its
accepted contexts, 0, 0 and 4 (5b6cbef5) had 4 distinct orbits. Only those 4 have the orbit
structure the pipeline needs, and they were not built through `prepare`. The identity and shape policy was not weakened. I am reporting this as a limitation.

## Coverage (1000 default draws, same seeds; `batch-f-coverage.json`)

| ID | shapes | non-square | 25×25 outputs | other |
|---|---|---|---|---|
| 27f8ce4f | 1 → 16 | 0 → 734 | 0 → 71 | colours 3/4/5: 294/368/338 → 381/306/313 |
| 48f8583b | 1 → 16 | 0 → 739 | 0 → 72 | used 1/2/3/4: 2/382/418/198 → 14/427/354/205 |
| 5b6cbef5 | 1 → 16 | 0 → 738 | 0 → 57 | ink 1..4 → 1..9; density deciles 0.1–0.9 → 0.0–1.0; full masks 0 → 5 |

Unique inputs: 1000/997/1000 → 1000/993/979. Checker disagreements: 0. These come from a
bounded pool and are not a capacity claim.

## D/E context-audit reruns

Batch D and E `context-audit.json` pin the whole-file hash of `colour_evidence.py`. That
hash changes 51a6c404… ← 6789d3d8… because of the batch F dispatch. Both harnesses were
**rerun unmodified** on the final F shared sources, sequentially, with two workers each.
Previous reports are archived as `context-audit-pre-batch-f-c0effbf.json` (D) and
`context-audit-pre-batch-f-95ffc02.json` (E). No D/E constructor, gate or hash string was
hand-edited.

Comparison with the archived reports, all 16 runs (8 per batch):
- **Unchanged:** every semantic field. This covers passed, accepted (250/250 each), retries
  (D: 0, 1, 10 on 281123b4; E: 11 on e0fb7511 min corner), histograms, failure reasons,
  first-context ambiguity, `make_record` calls and query shapes.
- **Changed:** only `source_sha256.colour_evidence` and the wall-clock `seconds`. Runs took
  about 2–3× longer. I did not measure the cause.

## Tests

| Test file | Covers |
|---|---|
| `diversity/test_native_batch_f.py` | fixture replay + rule-statement reference + factory; explicit legacy output equivalence vs hash-checked base bytes; legacy RNG replay; all 16 shapes via checker and factory on 8 D4; default structure (16 shapes; 27: K 3..5; 48: 1..4 used incl. monochrome; 5b: ink 1..9); 2×2 feasibility; 5×5 → 25×25 and 6 rejected; partial/explicit args; invalid args (floats, bools, ranges); infeasible K raises without consuming RNG; `RuntimeError` on budget; timing; certificate binding |
| `test_self_tiler_evidence.py` | fixtures accepted under 8 D4 × 3 palettes; exported rule reproduces the constructor; witnesses for fixed colour, frequency swap, corner and transposed placement, monochrome support and fill evidence; query answers unused; no-fit rejection; brute-force cross-check; recorded pre-gate witnesses now rejected by `make_record` on 8 D4 while the program still verifies; sole-`None` adversarial and contract tests |

## Limits

- **Bounded hypotheses.** The gate rules out only its listed alternatives.
- **Small-shape production support** is limited by orbit identity (see above). Strict same-shape
  pool support was not measured through `prepare`.
- **Unsupported explicit domains.** These explicit inputs keep their legacy labels but are
  not certified: 5b6cbef5 several-ink or empty masks, and 27f8ce4f/48f8583b zero or tie
  inputs. Factory verification may reject them. The gate is not their semantic validator.
  - Example: the full several-ink 2×2 input `[1, 2, 3, 4]` gets the legacy colour-on-mask
    label (solid blocks). The archived checker disagrees with that label, yet the label fits
    the gate's `('all', 'id', 'solid')` candidate, among 11 survivors.
  - A partial several-ink example fit no candidate.
- **Gate retry cost** is highest at 2×2: up to 15 retries per query, and 30–45 % of first
  contexts rejected.
- **Pre-gate witnesses** record the draft `self_tiler_evidence.py` hash. Only its `predict`
  function, which is unchanged in the final bytes, evaluated the competitors.
