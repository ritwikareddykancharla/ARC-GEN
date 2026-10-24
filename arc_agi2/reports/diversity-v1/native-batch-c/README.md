# Native batch C (2026-10-24): orientation sampling and finite-geometry expansion

Base `c75138a`. Audit source: native-domain-review-20261024 (`semantic_reviews.json`,
`probes/orientation_blockers.py`, `probes/line_span_782b5218.py`).

**Not production-ready.** These four families need a root admission rebuild,
and then actual unmodified `prepare` 200/20 exports. Both are still outstanding.

## Changes

| ID | Change | Kept unchanged |
|---|---|---|
| 7e2bad24 | Each random pair draws its own flip/flop/xpose. An explicit True/False is respected; sampling happens only when the argument is None. The `while True` loop is now bounded at 20000 tries. | Factory, colour-evidence and `beam_endpoint_evidence` gates; fixtures |
| 7e576d6e | Each random pair draws its own xpose (explicit values respected). The loop is bounded at 1000 tries. | Zigzag alternation; factory; fixtures |
| 94414823 | Random canvas is 5..30 by 6..30 (before transpose). The square side is even, from 4 up to the room available, and the square can sit anywhere with one-cell room for the markers. Explicit geometry arguments are honoured. With explicit colours, omitted geometry defaults to the legacy 10x10 / side 6 / (2,2). Infeasible arguments raise ValueError. | Even interior split into equal quadrants; markers at two adjacent outside corners; direct-source program (sha 617c4a43…) |
| 50c07299 | Random canvas is 5..30 by 5..30. Explicit height/width are honoured. An explicit row keeps the legacy 16x16. Infeasible arguments raise ValueError. | The segment stays on the bottom-left-corner anti-diagonal, as in every fixture. There is no free diagonal offset. Row sampling is unchanged. |
| verified_rules.py | Adds `7e2bad24: native_side_beam` and a `VERIFIER_EVIDENCE` entry (root-authorised narrow exception). It is the pair-label checker `beam_predictions(g, identity)[RULES.index('side')]`. | No other family entry changed |

## Certificates (current bytes; hashes verified)

| ID | Method | Fresh | Augmented | Fixture | Unique inputs (before→after) |
|---|---|---|---|---|---|
| 7e576d6e | `recertify.check` | 1000 | 8000 | 16 | 1000→1000 |
| 94414823 | `recertify.check` | 1000 | 8000 | 16 | 222→1000 (audit: 224-input domain, 1 orbit) |
| 50c07299 | `recertify.check` | 1000 | 8000 | 16 | 56 (check failed at HEAD)→942 |
| 7e2bad24 | `certify_7e2bad24.py` v2 (query-preserving informative context, root-approved) | 1000 | 8000 | 16 | 1000 |

The 7e2bad24 certificate records:
- **Queries:** 250 of 250 kept fixed; none dropped or failed.
- **Context:** at most 64 contexts per query; 99 context retries, all caused by `unresolved mirror-end convention`.
- **Endpoint-sensitive queries:** 91 of 250, all accepted.
- **Orientation:** 209 of 250 episodes mix wall orientations; query axes are 120 h / 130 v.
- **Pair labels:** every drawn pair is gated by the registered verifier.
- **Archived solver (reported only):** disagreed on 442 of 1000 pairs.

Generic `recertify.check` on 7e2bad24 fails with `Unresolved mirror-end interpretation`. Random three-demo contexts can be uninformative, and that is exactly the case the query-preserving method handles.

## Orientation evidence (seeded probes)

- 7e2bad24: wall axes were 1004 h / 996 v in 2000 draws. 429 of 500 four-pair episodes mix axes. Before the change, 200 of 200 were horizontal.
- 7e576d6e: 486 of 1000 draws have horizontal lines. Before the change, 100 of 100 did.

## 7e2bad24 pair verifier

The archived solver uses the diagonal-target reading. The constructor uses the side-contact reading.

| Constructor | Draws | Archived solver disagrees | Endpoint-sensitive | Side verifier disagrees |
|---|---|---|---|---|
| c75138a | 1000 (seed 11) | 400 | 390 | 0 |
| batch C | 1000 (seed 11) | 423 | 385 | 0 |

- In a separate run of 600 draws, every endpoint-sensitive pair was among the archived-solver disagreements (220/220).
- All 5 fixtures match both checkers.
- Witness: `7e2bad24-archived-verifier-counterexample.json`.

## 782b5218: deferred, constructor unchanged

The audit premise was that every canonical line spans all columns. That is false. In canonical `train[2]` the line clips at the bottom (red at row 9, cols 7–8), column 9 has no red, and the output clears column 9 to 0. Adding a bottom guard would therefore remove a configuration the fixtures exhibit, so no guard was added (confirmed by root).

Generic recertify still fails at HEAD. The archived bottom-left flood solver disagrees on about 9 in 3000 native lines that touch the bottom row and then rise again. That is a verifier-semantics question for root and is left unresolved.

## Isolated measurements (NOT production validation)

`prepare.prepare` was called directly at 200/20 with 2 workers in a scratch harness. The harness **waived the admission.json hash pin on `arc_agi2/verified_rules.py`**; every other pin was enforced, and none of these IDs is RE-ARC-admitted.

| ID | Train / val | Notes |
|---|---|---|
| 7e2bad24 | 200 / 20 | 61 of 200 train queries endpoint-sensitive (0 in a pre-verifier run, where the archived checker rejected 470 pairs); 179 of 200 episodes mix axes; 30 retried contexts; 0 retired queries |
| 7e576d6e | 200 / 20 | 177 of 200 mixed |
| 94414823 | 200 / 20 | 177 query shapes |
| 50c07299 | 200 / 20 | 172 query shapes |

Validation query support is thin under the strict uniform-shape policy: 24 identities for 94414823 and 23 for 50c07299, against 20 requested. No HEAD export baseline was completed.

Full unmodified export compatibility remains OUTSTANDING.

## Tests

- `arc_agi2/diversity/test_native_batch_c.py` covers fixtures, orientation overrides, mixing, zigzag, bounded loops, the verifier counterexample, endpoint-sensitive retention, export only with demonstrated evidence, max-30 and extreme geometry, infeasible arguments, and 782 clipping.
- Together with `test_beam_endpoint_evidence`, `test_native_batch_b`, `test_pipeline`, `test_coverage_export_gates` and `test_program_targets`, all pass.
