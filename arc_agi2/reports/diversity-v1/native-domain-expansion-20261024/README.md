# Native-domain expansion, 2026-10-24

Scope: families with no RE-ARC counterpart (`rearc_overlap: false`). Each
retained change removes a fixed canvas, or a fixed object or count range, that
was incidental to the family. The rule, the original fixtures and the factory
programs are unchanged. Exact data: `report.json`, `measurements.json`.
Reproduce with `measure.py`.

## Retained (7)

| Family | Before → after (1,000 fresh samples each) |
|---|---|
| `31adaf00` fill empty squares | 10×10 only → H,W 5–30 independent (517 shapes); filled squares per grid 1–7 → 1–14; side ≤4 → ≤5 |
| `84db8fc4` border vs enclosed holes | 10×10 → H,W 3–30 (553 shapes); enclosed regions 1–15 → 1–92; wall/empty mix varies |
| `ce039d91` mirror-pair marking | 10×10 → even W 4–30, any H 3–30 (371 shapes); grey pixels 12–49 → 3–343 |
| `137f0df0` lattice gap lines | 10×10, 2×2 blocks, 2–3 per axis → 5–30 canvas (517 shapes), 9 block shapes (1–3 × 1–3), 1–6 per axis, gaps 1–3 |
| `d282b262` slide-and-stack boxes | 15×15, squares 2–5, 5–6 boxes → 6–30 canvas (491 shapes), 24 box shapes incl. non-square, 1–9 boxes |
| `a406ac07` ruler blocks | 10×10, 4–5 colours → H,W 3–30 independent (540 shapes), 2–9 colours, run lengths 1–27 |
| `f45f5ca7` colour-offset shift | 10×10 → height 5–30 and width 5–30 (528 shapes) |

The baseline is commit `cf79bbc`: one canvas shape and a 0% rectangular rate
for every family. Current rectangular rates are 95–97%. Grids with a side over
20 are 55–64% of samples, and aspect ratio reaches 5–10. This matches the
128-sample audit in `output/generator-domain-audit-20261024`.

## Checks

- Ran `python -m arc_agi2.diversity.recertify` on all 7 families. Each passed
  1,000 fresh pairs, 8,000 D4/palette pair checks against the factory program,
  the archived verifier on every pair, and 16 original-fixture variants. There
  were no sampler rejections. Certificates are in `../native-certificates/`
  and `direct_factories/<id>.json`.
- `arc_agi2/test_native_domain_expansion_20261024.py` (21 tests) covers:
  fixture replay; broadened, rectangular canvases with large sides; verifier
  agreement and 8-D4 program agreement; a 4×4 hole on a 7×23 canvas; rectangular
  boxes and box counts in d282b262; 2–9 colours and unequal axes in a406ac07;
  1×1, 3×3, 1×3 and 3×1 blocks plus a single-row lattice in 137f0df0, plus narrow 137f0df0 canvases ending instead of hanging; and the
  even-width/free-height boundary in ce039d91.
- Six related existing test files pass (41 tests). Every allowed size was
  generated with 3 seeds each and none hung.

## Attempted and reverted: `c35c1b4c`

Even H,W 6–30 with area-scaled blob growth. The factory learns the
central-colour selector and the mirror axis from the demos, and raises an error
when they leave the query ambiguous. On standard 3-demo + 1-query episodes the
original constructor already fails 59/1000 times; the expanded one fails
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
- Episode shape: the originals have a single fixed shape. Only 36–95 of about
  370–550 shapes appear 4 or more times per 1,000 samples. A uniform-shape
  episode therefore needs large pools, or shape-matched demos requested through
  the new `width`/`height` parameters.
- Not integrated: `prepare.py` and `admission.json` were not edited, so the root
  must add these families to the supplement.
- Recertify replaced the earlier factory provenance text. A copy is kept in
  `report.json` under `previous_factory_*`.
- All numbers are sample statistics. Each exported episode still needs its own
  verification.
