# Batch 7 semantic review fragment (32 families, ranks 193–224)

This is a fragment for the supervisor to merge. `extract.py`, `semantic_reviews.json`, `inventory.jsonl`, `summary.json`, `review_history.json` and the global README are untouched. Global counts stay at **224 reviewed / 505 pending** until the merge. `release_ready` is false for every record. No constructor, factory, verifier, gate, admission or label was changed.

- **Records:** `batch07.json` holds `{baseline_commit, reviewed_on, reviewer, ids, reviews}`. `ids` equals `summary.json` `batches["7"]` exactly. No record already exists in `semantic_reviews.json`.
- **Schema:** each record uses the full batch-22 record schema with `review_batch: 7`, `review_kind: first_review` and `status: reviewed`.
- **Binding:** records bind to `96be8033a32ac47104ec737310778baffa7f5159` (integrated baseline). The worktree HEAD is `e64baab`, the batch-22 report, which changed no constructor. All 32 constructor sha256s are identical at the ordering commit `5436f3f`, at `96be803`, at HEAD and in ARC-GEN.
- **Certificates:** all 32 are current (25 `direct_factory`, 7 `direct_certificate` saved teachers).
- **Admission:** none is admitted.

## What was read

For each family:
- the whole constructor;
- every canonical train/test grid (`validate()` equals canonical for all 32);
- the factory or saved-teacher certificate and the certificate record;
- the archived verifier, where disagreements arose.

Also read:
- the gates `line_motif_evidence` and `motif_context` (98c475bf) and `tile_bar_evidence` (985ae207);
- `pool_sampling` (985ae207's compiled sampler);
- `fixture_policy` and the label review (963c33f8);
- `common.conway_sprite`.

## Probes (read-only, seeded)

- **`probes/fixture_stats_batch7.py 200 0`**
  - Output sha256 `b34dd07e…`. Two runs were byte-identical (`--timing` section excluded).
  - Evidence: `probes/fixture_stats_batch7_evidence.json`.
  - **S:** self-tests of the derived checkers.
    - The exact `conway_reachable` margin/flow test accepts 300/300 native sprites and 414/414 low-tail native sprites, and rejects both negatives.
    - The wall grammar, the 5ecac7f7 decoder, the ring inference and the hue-grammar replay each accept 200/200 native draws.
  - **A:** canonical latent parameters checked against native guards.
  - **B:** native draws checked with the production verifier, the certified program and the 98c475bf gate.
  - **C:** widened explicit-parameter scenes, with the constructor (or a self-tested lifted reference) as reference.
  - **D:** exact finite domains.
- **`probes/fixture_stats_batch7_rect.py 300 0`**
  - Output sha256 `036706f8…`. Two runs were byte-identical.
  - Evidence: `probes/fixture_stats_batch7_rect_evidence.json`.
  - Covers independent H/W rectangular scenes for 7491f3cf and 973e499e against independent reference relations. On square shapes, the builders equal the constructors (100/100 and 200/200).
- **`probes/fixture_stats_batch7_width98.py`** (follow-up)
  - Output sha256 `3161e11e…`. Two runs were byte-identical.
  - Evidence: `probes/fixture_stats_batch7_width98_evidence.json`.
  - Covers 98c475bf at module WIDTH 18/20/24/30, set temporarily and restored. Each width has 100 fixed queries, same-width 3-demo contexts and at most 64 tries, with all 8 D4 x 2 palettes on 20 queries per width and a cross-width negative check.

### Negative evidence kept

Probe errors corrected before the final runs (recorded in the evidence JSON):
- The first 817e6c09 DP over-counted (202M). Corrected to 77,999,562; the DP equals literal enumeration at widths 5–11.
- A 7d7772cc false "unreachable" came from a trailing −1 that draws nothing.
- The first 985ae207 classifier separated nothing; it was replaced by far-edge overshoot.
- The first df9fd884 widening could not be built (100/100 failed) because size is tied to 7+wide.
- In the rect probe, the square control at 3×3 was infeasible (0/300). That line is reported, not dropped.

The 762cd429 copies=2 run is kept as a negative control (0/100, expected).

## Supervisor correction (before commit)

The draft called **7491f3cf** and **973e499e** adequate unchanged. The supervisor reviewed the source and showed that both conclusions were unsupported.

- **7491f3cf:**
  - The draft claimed non-square panels could not fit. That was false: 4W+5 ≤ 30 and H+2 ≤ 30 allow, for example, H 10 and W 5.
  - Rectangular panels with every guard kept:
    - tall: 300/300 program and verifier over 30 shapes;
    - wide: 300/300 over 6 shapes;
    - up to 28×6: 60/60.
  - The wall-evidence guard is feasible on every shape tested; 3×3 is infeasible.
  - Dimensions are now `mixed` (W ≤ 6 rule-tied; square panels an implementation choice). The record is medium, `needs_constructor_work`.
- **973e499e:** a self-mask expansion like 007bbfb7 and the nativeF repairs.
  - With H and W independently 2..5, program and verifier agree on 227/227 rectangular and 73/73 square scenes against the independent relation.
  - Dimensions are now `incidental_restriction`; colour count is kept as a separate `mixed` axis. Medium, `needs_constructor_work`.

## Second supervisor correction: 98c475bf (follow-up commit)

The fixed width of 20 is incidental when demonstrations and query share a width. The canonical uniform/seen profile requires that, the factory (`_store`/`_template`) records and checks the line span, and `line_motif_evidence` refuses span mismatches.

The supervisor's probe was reproduced independently:
- At each width, 100/100 fixed queries were accepted with 0 failures (retries 24/25/23/7).
- The archived verifier, the demo-learned `motif_context`, the gate prediction and the factory were each exact on 100/100.
- Under all 8 D4 x 2 palettes, gate and factory were exact on 320/320 per width.
- Cross-width demonstrations were refused 20/20 by the gate and 20/20 by the factory.

Dimensions are now `incidental_restriction`. The record is medium and `needs_constructor_work`. The proposal is a per-scene width of 18..30 with same-width demonstrated templates. Novel-width or cross-width anchoring stays a separate, unresolved uncertainty; the fixtures do not show arbitrary anchoring.

## Results

**Patch priority:**
- **High (11):** 456873bc, 52fd389e, 5ecac7f7, 8fbca751, 981add89, 985ae207, c8b7cc0f, ef26cbf6, 17b866bd, 1e5d6875, 2e65ae53.
- **Medium (17):** 817e6c09, 458e3a53, 470c91de, 5783df64, 758abdf0, 7d7772cc, df9fd884, e9ac8c9e, 25e02866, 2601afb7, 48131b3c, 5751f35e, 963c33f8, 9968a131, 7491f3cf, 973e499e, 98c475bf.
- **Low (4):** c1990cce, 762cd429, 42a15761, 9ddd00f0.

**Adequacy:**
- `adequate_unchanged_candidate`: **none**. 98c475bf was withdrawn by the second correction.
- `finite_domain_no_change_without_new_semantics`: c1990cce (13 inputs) and 762cd429 (13,122).
- `needs_constructor_work`: the other 30.

**Canonical inputs unreachable natively (probe A):**

| Family | Unreachable pairs | Cause |
|---|---|---|
| 456873bc | test | 10-cell 4×4 sprite outside `conway_sprite` |
| 52fd389e | train[1], test | equal heights; count 5 |
| 5ecac7f7 | 4 of 6 | full piece; colour 6; width caps |
| 8fbca751 | 3 of 4 | 2 boxes; plus sprite; empty column |
| 981add89 | train[0], train[1] | marker walk |
| 985ae207 | test | 6-wide bar |
| c8b7cc0f | train[1], train[2] | rectangle caps |
| ef26cbf6 | test | sprite misses a row |
| 17b866bd | train[1] | colour 7 |
| 1e5d6875 | test | frame-gap guard; the drawn cells do not touch |
| 2e65ae53 | test | 6 boxes; 8×18 box |
| 963c33f8 | train[2] | known label quirk with a teaching copy |

**Production-verifier disagreements on native draws:** prepare would reject these pairs, so the admitted subset would be biased.

| Family | Verifier agreement | Cause |
|---|---|---|
| 5ecac7f7 | 115/200 | column-band vs k-th-object reading |
| 985ae207 | 8/11 | disagreements are exactly the far-edge overshoot scenes; no canonical pair overshoots |
| 5751f35e | 154/200 | 42 of 46 involve an inner ring of colour 0 |
| 963c33f8 | 158/200 | floor-clearing convention |
| 981add89 | 192/200 | modal-background assumption |
| 7d7772cc | 196/200 | archived verifier raises an exception |

**Feasibility:** 985ae207 had 1/12 native draws exceed 20 s. The certificate's compiled sampler needed 716M geometry proposals for 1000 accepted scenes.

## Remaining limitations

- No certificate, audit or prepare export was rerun. Probes are seeded local runs, not audits. Widened-scene passes show program support only; they do not show intended scope.
- **Not traced:** 4 of the 5751f35e disagreements, the 7d7772cc verifier exception, and individual 963c33f8 disagreements beyond one example.
- **Open semantics:**
  - 5ecac7f7's reading;
  - 985ae207's overshoot;
  - 963c33f8's floor clearing;
  - rectangular panels or inputs (7491f3cf, 973e499e);
  - 98c475bf's anchoring on a novel width (same-width episodes are supported);
  - 758abdf0's far-edge mark on other widths.
- **Pre-existing state:** `extract.py --check` reports 4 errors in this worktree, for the nativeE families `e0fb7511`, `f0df5ff0`, `f3cdc58f` and `0c786b71`, whose constructors changed before this pass. This fragment does not cause them, and they are for the global refresh owner.
- This is not release readiness and not full-1120 completion.
