# e1d2900e: nearest square before alignment

The independent [atlas explanation](https://github.com/yhay81/arc-agi-2-solution-atlas/blob/main/notes/e1d2900e.json) and [solver](https://github.com/yhay81/arc-agi-2-solution-atlas/blob/main/solutions/e1d2900e.py) use one geometric rule: choose the closest red square by Chebyshev distance, then slide only if aligned with that square. Diagonal nearest squares keep a blue point stationary. Exact-distance ties use a consistent reading order.

In original train[1], point `(23,13)` is equally distant (7) from square C at rows 15–16, columns 10–11 and square D at rows 22–23, columns 20–21. The visible demonstrations require C to win this tie. It is diagonal to C, so it stays. This explains the original label uniformly; changing the original fixture is unnecessary.

The old constructor considers only aligned squares and adds hidden `extra_idxs=[12]` to reproduce this example. The proposed constructor replaces returned labels with the independently documented rule. Its historical input sampler and rejection decisions are preserved, so supported hard cases are not removed. Exact seeded input comparisons and independent atlas checks are in `audit_nearest.py`.

The direct program retains all eight reading orders consistent with the demonstrations. It never selects an order using D4 metadata and never prefers the old aligned-only mechanism. If the surviving orders disagree on the query, both the program and an independently implemented evidence gate reject the context. The audit keeps each query fixed and resamples its demonstrations.

The target uses bounding-box distances and move lists; the independent gate uses minimum Chebyshev distance over red-cell sets and paints all resulting point destinations. Six tests cover original fixtures, an unresolved tie, a newly resolved query, counterfactual tie behavior, rotations/reflections/color mappings, and missing or contradictory demonstrations.

No fixture labels, policy, admission certificates, or shared dispatch are changed by this worker. The live constructor remains untouched until parent review. This is an independently supported interpretation, not a claim of official upstream endorsement.

Final proposed audit: **1,000 unique accepted pairs, 8,000 transformed checks, 16 original-fixture variants, all passed.** Across 2,146 old/new seeded draws including context retries, all inputs matched exactly; 1,881 outputs changed under the corrected rule. Of 250 fixed queries, 96 depended on tie order; 382 context retries resolved them. No sampling failure occurred. Each generated output also matched the independent atlas solver. `native-label-counterexamples.json` and `unresolved-context-examples.json` retain witnesses.
