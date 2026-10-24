# Native-domain expansion, 2026-10-24

Scope: families with no RE-ARC counterpart (`rearc_overlap: false`). Each
retained change removes a fixed canvas, or a fixed object or count range, that
was incidental to the family. The rule, the original fixtures and the factory
programs are unchanged. Exact data: `report.json`, `measurements.json`.
Reproduce with `measure.py`; it records each source's sha256.

## Retained (7)

| Family | Before → after (1,000 fresh samples each) |
|---|---|
| `31adaf00` fill empty squares | 10×10 only → H,W 5–30 independent (517 shapes); filled squares per grid 1–7 → 1–14; side ≤4 → ≤5 |
| `84db8fc4` border vs enclosed holes | 10×10 → H,W 3–30 (553 shapes); enclosed regions 1–15 → 1–92; wall/empty mix varies |
| `ce039d91` mirror-pair marking | 10×10 → even W 4–30, any H 3–30 (371 shapes); grey pixels 12–49 → 3–343 |
| `137f0df0` lattice gap lines | 10×10, 2×2 blocks, 2–3 per axis → 5–30 canvas (517 shapes), 9 block shapes (1–3 × 1–3), 1–6 per axis, gaps 1–3 |
| `d282b262` slide-and-stack boxes | 15×15, squares 2–5, 5–6 boxes → 6–30 canvas (491 shapes), 24 box shapes incl. non-square, 1–9 boxes |
| `a406ac07` ruler blocks | 10×10, 4–5 colours → H,W 3–30 independent (514 shapes), 2–9 colours, run lengths 1–28 |
| `f45f5ca7` colour-offset shift | 10×10 → height 5–30 and width 5–30 (528 shapes) |

The baseline is commit `cf79bbc`: one canvas shape and a 0% rectangular rate
for every family, consistent with the 128-sample audit in
`output/generator-domain-audit-20261024`. Current rectangular rates are 95–97%.
Grids with a side over 20 are 55–67% of samples, and the aspect ratio reaches
5–10.

## Bounded proposal loops

Every whole-scene rejection loop has a fixed proposal budget. When the budget
runs out, the constructor raises `RuntimeError`. It never returns a simplified
scene. Budgets were set from the worst measured acceptance per proposal,
using the hardest valid canvas, with 100–2,000 samples per size:

| Family | Hardest canvas | Acceptance | Budget | Exhaustion bound |
|---|---|---|---|---|
| `31adaf00` | 30×30 | ~18% | 1,000 | < 1e-80 |
| `84db8fc4` | 3×3 | ~4.5% | 10,000 | < 1e-190 |
| `ce039d91` | 4 wide × 3 high | ~29% | 1,000 | < 1e-140 |
| `d282b262` | 6×6 | ~63% | 1,000 | < 1e-400 |
| `f45f5ca7` | height 5 | 5!/5⁵ ≈ 3.8% | 10,000 | < 1e-160 |

- `137f0df0` was already bounded at 1,000 proposals and raises `ValueError`
  when a canvas is infeasible.
- `a406ac07` has no rejection loop.
- The following inner loops are unchanged:
  - placement retries: 50 per proposal in 31adaf00, 100 in d282b262;
  - deterministic flood fills and gap decrements, which provably make progress.
- The random draws for unbounded loops are unchanged, so the valid domain is
  the same as before.

## Checks

- Standard `python -m arc_agi2.diversity.recertify` was run on the final
  sources. All 7 passed. Each has:
  - 1,000 fresh pairs, every one checked by the archived verifier;
  - 8,000 D4/palette pair checks against the factory program;
  - 16 original-fixture variants;
  - no sampler rejections.

  Certificates are in `../native-certificates/` and
  `direct_factories/<id>.json`, and their constructor hashes match the
  committed sources. 137f0df0's source is unchanged since its first
  certificate.
- `arc_agi2/test_native_domain_expansion_20261024.py` has 32 tests. They cover:
  - fixture replay;
  - broadened rectangular canvases with large sides;
  - verifier agreement and agreement with the 8-D4 programs;
  - a 4×4 hole on a 7×23 canvas;
  - box shapes and counts in d282b262;
  - 2–9 colours in a406ac07;
  - block shapes and single-axis lattices in 137f0df0;
  - the even-width boundary in ce039d91;
  - narrow 137f0df0 canvases ending instead of hanging;
  - shape requests honoured by every family;
  - the hardest valid canvases still succeeding;
  - budget exhaustion for all five bounded families. A degenerate random
    source (always the top of the range, or a single choice) must raise
    `RuntimeError` within 20 s; observed time is under 0.1 s.
- Six related existing test files pass (41 tests). Every allowed width × height
  was generated with 3 seeds and returned the requested shape. The slowest call
  took 0.033 s.

## Attempted and reverted: `c35c1b4c`

Even H,W 6–30 with area-scaled blob growth. The factory learns the
central-colour selector and the mirror axis from the demos, and raises an error
when they leave the query ambiguous. On standard 3-demo + 1-query episodes the
original constructor already fails 59/1000 times; the expanded one failed
73/1000. The existing certificate relies on context retries, which recertify
does not do. Reverted, and the source is unchanged. Fixing it needs an
episode-context policy, not a generator change.

## Remaining restrictions and uncertainty

- These are kept as rule boundaries:
  - `ce039d91` keeps an even width; an odd width would add an undemonstrated self-mirror column.
  - `f45f5ca7` keeps its fixed colour→offset legend.
  - `a406ac07` keeps its ruler edges and a final run of at least 2.
  - `137f0df0` keeps a full lattice of one block shape per scene.
- Kept for the archived verifier:
  - `137f0df0` and `d282b262` reject scenes where black would not be the modal colour.
  - `31adaf00` still rejects overlapping equal-size empty windows, which keeps the fill independent of order.
- **Strict shape contract.** Every original task has the same input shape for
  all demos and the query. Under a strict contract, each episode needs three
  distinct demos with the query's exact shape.
  - In 1,000 independent samples only 36–95 of about 370–550 shapes appeared
    4 or more times. Pools drawn independently will therefore leave many
    queries without enough same-shape demos. These are strict-sampling
    shortfalls; the requirement must not be relaxed to cover them.
  - Meeting the contract needs shape-conditioned context sampling: draw the
    query, then generate demos at its shape. Every family accepts the
    requested shape: `width`/`height` for six of them, and `height` for
    f45f5ca7, whose width is already a parameter. A test covers this.
  - I have not inspected how the root sampler reports shortfalls or what
    rate they reach, and I make no claim about either.
- Not integrated: `prepare.py` and `admission.json` were not edited, so the root
  must add these families to the supplement.
- Recertify replaced the earlier factory provenance text. A copy is kept in
  `report.json` under `previous_factory_*`.
- All numbers are sample statistics. Each exported episode still needs its own
  verification.
