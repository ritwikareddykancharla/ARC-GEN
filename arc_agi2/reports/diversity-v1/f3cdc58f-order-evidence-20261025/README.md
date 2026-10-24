# f3cdc58f bar-order demonstration evidence (2026-10-25)

This report covers one gap from the domain review
(`native-domain-review-20261024/semantic_reviews.json['reviews']['f3cdc58f']`,
probe `probes/rereview_batch_e.py`). Under the expanded histogram domain,
three demonstrations can fit a count-sorted bar order as well as the native
fixed legend, while the two orders give different answers on the query. The
fix is a narrow evidence gate.

The fix changes none of the following:
- constructor `tasks/task_f3cdc58f.py` (abd953bb…);
- factory (81c2164b…);
- pair checker `verified_rules.fixed_colour_histogram`;
- labels and the valid domain (random W and H 4..30; explicit W 4..30 and H 1..30).

The certificates stay valid as issued. No recertification, registration,
admission or prepare change was made.

## Rule and readings

**Native rule.** Count each of the colours 1..4. Draw a bottom-aligned bar of
each colour in the fixed legend order 1, 2, 3, 4 (under augmentation, the
palette images of these colours in the transformed frame).

**Readings.** The gate (`arc_agi2/histogram_order_evidence.py`) compares three
natural readings:

| reading | bar order |
|---|---|
| `fixed_legend` (native) | the legend shown by the demonstration bars |
| `ascending_count` | smallest count first |
| `descending_count` | largest count first |

**Ties.** Count ties are broken by the legend shown in the demonstration
bars. In the native frame that legend is 1,2,3,4, which is the review's
colour-order tie-break. Every demo shows all four bars, so any other fixed
order is refuted by a single demo.

**Frame.** D4 and the palette are undone using episode metadata only. The
verdict is therefore frame-invariant, without enumerating arbitrary
unobserved orders. A visible-number tie-break would be a different,
palette-dependent family, and it is not used.

**First-appearance order.** Not gated: the review measured 0/2000 contexts
for it.

**How the gate decides.**
- It keeps every reading that reproduces every demonstration output.
- All surviving readings must give the same answer on each query input.
- Query answers are never read.
- The check is query-specific. Monotone demonstrations still pass when the
  query's counts are also monotone in the same direction, or all tied.
- Production retries the demonstrations for the same query
  (`MissingColourEvidence`).

**Dispatch.** `colour_evidence.py` gains one 4-line f3-only dispatch.
Previously f3 reached the early `return`, so the new branch skips no other
check.

## Pre-gate witness

`witness.py` reimplements the competitors without importing the gate. It was
run on base 9498a90 and archived in `pregate-witness.json` (commit 8b0a9fa).
Each witness is:
- a fixed 4x4 query plus three 4x4 demonstrations;
- four distinct `prepare.input_orbit` IDs;
- demos in the query's `input_split`;
- the uniform/seen profile;
- labels that equal the checker.

| competitor | split | demo counts (legend order) | query counts |
|---|---|---|---|
| ascending | train | [2,2,2,2] [1,2,2,3] [2,2,2,3] | [2,2,3,2] |
| descending | validation | [2,2,2,2] [2,2,2,1] [2,2,2,2] | [2,1,2,2] |

**Before the gate.** The original `make_record` accepted each witness under
all 8 D4 transforms × {identity, seeded} palettes (16/16 each).

**After the gate.** Both witnesses are rejected in all 16 variants (test).

## Fixed-query context audit (`context_audit.py`, `context-audit.json`)

**Setup.**
- 250 fixed queries per domain. No query was dropped or replaced.
- Demonstrations follow the actual canonical profile (uniform/seen:
  demonstrations are drawn at the query's shape).
- Four distinct input orbits per context.
- Demonstrations are in the query's split, with at most 400 draws per slot.
- At most 64 contexts per query.

**Acceptance.** `make_record` must pass under all 8 D4 transforms with the
context's seeded palette. After that verdict, the gate's unique prediction
must equal the label. Every label is checked by
`runtime.verification_solver`.

| domain | accepted | retries (max) | make_record calls | D4-inconsistent | query split train/val | shapes / heights |
|---|---|---|---|---|---|---|
| default | 250/250 | 2 (1) | 2016 | 0 | 239/11 | 200 shapes, H 4..30, W 4..30 |
| min_4x4 | 250/250 | 12 (1) | 2096 | 0 | 237/13 | 4x4 only |

**Query count classes** (legend order; `first-context rejected` = queries
whose first context was rejected):

| domain | class | queries | first-context rejected |
|---|---|---|---|
| default | all_tied | 2 | 0 |
| default | nondecreasing | 25 | 0 |
| default | nonincreasing | 14 | 0 |
| default | non_monotone | 209 | 2 |
| min_4x4 | all_tied | 14 | 0 |
| min_4x4 | nondecreasing | 84 | 0 |
| min_4x4 | nonincreasing | 6 | 1 |
| min_4x4 | non_monotone | 146 | 11 |

**Reasons for every rejected context.** All were "demonstrations leave the
query bar order ambiguous": 2 in the default domain and 12 at 4x4.

**Survivors.**
- First contexts at 4x4: 231 kept only `fixed_legend`, and 19 also kept
  `ascending_count`.
- 7 accepted 4x4 contexts kept both readings. The query's counts agreed with
  both, which is the query-specific acceptance at work.

**Split draws.**
- default: 756 train / 627 validation draws for 723 / 33 slots.
- min_4x4: 779 / 996 draws for 744 / 42 slots.
- No slot exhausted its budget.

**Scope.** This audit is not a production export. No quota or admission is
claimed.

**Small explicit heights.** H = 1..3 are covered by tests rather than this
audit:
- H = 1: every count is 1, so all readings agree and nothing is rejected.
- H = 2 and H = 3: informative demonstrations are accepted, and monotone
  demonstrations with a non-monotone query are rejected.

## Tests

Run:

    PYTHONPATH=. python -m pytest -q arc_agi2/diversity/test_f3cdc58f_order_evidence.py

The file has 17 tests:
- unchanged constructor, factory and checker;
- domain not narrowed;
- canonical and teaching fixtures under 8 D4 × 3 palettes through
  `make_record`;
- witness rejection;
- informative, monotone, all-tied and query-specific verdicts;
- explicit H1..3 and 4x4;
- dense, full-colour and 30-high bars;
- answer-free queries;
- the independent competitor cross-check;
- out-of-domain inputs;
- audit source pins.

## Current hashes (sha256)

| file | sha256 |
|---|---|
| `arc_agi2/histogram_order_evidence.py` (new) | `f053730a6a2c66975de7de8f990512717c422c87f9b55bd4e3bf3eabc16a7562` |
| `arc_agi2/colour_evidence.py` (was 7da81112… at 9498a90) | `2abd6311d8e235c02a5d23c4532668a31c2a0e57dafe7640efc95c632a85f6ac` |
| `tasks/task_f3cdc58f.py` (unchanged) | `abd953bb8cd3a8c121ee081492f4c8e8df591b26cd03d3b13d01b875c9934d97` |
| `direct_factories/task_f3cdc58f.py` (unchanged) | `81c2164bbfb8fd3e335c16ef06186c432b50bf3c3e4ad7afb5b939673f3204d9` |
| `verified_rules.py` (unchanged) | `3a3425ae44e64be437e071b01c833eb5684a1646fe74adf5f2fbeab8df03d02f` |
| `program_targets.py` (unchanged) | `88298f336ca6a50ee91e58a08f24a4997c7c49e832eda1e68f98153dd59ed790` |
| `witness.py` | `2b896700eaa06e12c197c90329a2b56ab89e52966eb7884a352dcb7b4b1737bc` |
| `pregate-witness.json` | `825c429cb30cbd611f49b342801f9a51282f40cc574d399f55ff1abdf2d3f3a0` |
| `context_audit.py` (harness v1) | `98b3fc97fd998c357aed1fd903600f18c735b09f779e93cfa8d6a4c1cf8354d0` |
| `context-audit.json` | `4a5964ca15d39ec1f597c4067c976f71a1c35e040f037c94228d33af3b257444` |

`context-audit.json` records the full set of source pins it was run against,
and the test checks that they match the current bytes.

## Assumptions and outstanding work (root-owned)

**Assumptions.**
- The ambiguity family is the three named readings only. This is not a
  claim of universal identifiability.
- The legend tie-break equals the demonstrated legend.

**Integration refresh.** The `colour_evidence.py` hash changed. Existing
whole-file pins in other batch reports and tests (D/E/F/G/I, c7d4/d47a,
routing) were already stale at base 9498a90, and their failure sets are
identical before and after this change. Their historical audits are left
untouched, and root's merged refresh owns them.

**Admission.** `admission.json` target_source_hashes need the new
`colour_evidence.py` hash and the new dependency
`arc_agi2/histogram_order_evidence.py` (hash above). Admission already
failed at base on `verified_rules.py`.

**Production.** A prepare export for f3cdc58f under this gate has not been
run.
