# Native-domain review inventory: 729 no-RE-ARC families (2026-10-24)

This directory is a review record only. No constructor, factory, fixture,
prepare/admission or release-readiness code was changed. `release_ready` is
`false` for every record. A source review is not enough to set it, and neither
is a smoke test.

**Progress:** 224 of 729 families have current, hand-written semantic reviews:
batches 1–6 (ranks 1–192) and batch 22 (ranks 673–704). None is stale.
Coverage is **not consecutive**. Batches 7–21 (ranks 193–672) and batch 23
(ranks 705–729) are `pending`: 505 families with no semantic review. Batch 22 was
reviewed ahead of order to assess families that already sample shapes broadly.
Nothing in this record implies that a skipped batch was reviewed. The next
pending batch is **batch 7**.

**Rereview (2026-10-24):** 11 of the 128 reviews went stale when native batches B
and C changed their constructors. They were reviewed again against the
current source, fixtures, factories, verifiers, certificates and repair
measurements; see [Rereview of 11 repaired constructors](#rereview-of-11-repaired-constructors-native-batches-b-and-c).
The superseded reviews are kept verbatim in `review_history.json`.

**Rereview (2026-10-25):** 4 more reviews (`e0fb7511` in batch 3; `0c786b71`,
`f0df5ff0` and `f3cdc58f` in batch 4) went stale when native batch E
(`a7edea3`) changed their constructors. They were reviewed again at the frozen
integrated HEAD `e64baab`; see [Rereview of 4 repaired constructors](#rereview-of-4-repaired-constructors-native-batch-e).
`review_history.json` now holds 15 superseded reviews.

## Files

| File | Content |
|---|---|
| `extract.py` | Reproducible extraction, merge and validation (`--check` validates without writing) |
| `inventory.jsonl` | One record per family (729), sorted by review rank |
| `semantic_reviews.json` | Current hand-written semantic reviews (batches 1–6 and 22, 224 families), each bound to a constructor sha256 and to the source at its `baseline_commit` |
| `review_history.json` | Superseded reviews (15 families: 11 from batches B/C, 4 from batch E), each kept verbatim with its constructor binding and the mechanical record it was written against |
| `probes/` | Small read-only, seeded measurement scripts cited by the batch-2 to batch-6 and batch-22 reviews and the rereviews (`rereview_batch_bc.py`, `rereview_batch_e.py`) |
| `summary.json` | Counts, ID lists, all batches, reviewed and pending batch numbers, the next pending batch, rereviewed and history IDs, validation errors (currently none) |

```bash
PYTHONPATH=. .venv/bin/python arc_agi2/reports/diversity-v1/native-domain-review-20261024/extract.py
```

Running the script twice gives byte-identical `inventory.jsonl` and
`summary.json`. `REVIEWED_BATCHES` in `extract.py` (currently
`(1, 2, 3, 4, 5, 6, 22)`) sets which batches must be fully and currently
reviewed. Validation fails if any other batch has a non-`pending` record.

`summary.json` lists `reviewed_batches`, `pending_batches` (currently 7–21 and
23), `next_batch_number` and `next_batch`. The next batch is the **first
unreviewed batch in the fixed batch order**, not `max(reviewed) + 1`, so it is
batch 7 after the jump to batch 22. Batch membership itself is unchanged: it is
still pinned to the ordering commit.

Validation also checks:
- the next-batch selector (`next_pending_batch`) on six fixed reviewed-set
  cases, including `(1..6, 22) -> 7`, all 23 batches reviewed `-> None`, and an
  empty set `-> 1`; and that, on the real inventory, the selected batch is
  unreviewed and every earlier batch is reviewed;
- every reviewed record's `constructor_sha256` equals the constructor at its own
  `baseline_commit`;
- every `review_history.json` entry is byte-for-byte the review at the commit
  where it was first written and at its archive commit;
- the hash it records is the constructor at its review baseline and just
  before the repair commit;
- the replacing commit is the one that changed the constructor
  (`last_commit_with_this_source` is `replaced_by_commit^`), and
  `replacement_constructor_sha256` is the source at that commit (added with the
  batch-E rereview; the 11 earlier entries pass it unchanged);
- its mechanical record equals the inventory line at the review commit;
- the current rereview's `supersedes` link points at it;
- every rereview has a complete `repair_delta` and existing `evidence` paths.

Negative tests of these checks (edited history text, dropped entry, wrong
binding or baseline, missing field or evidence path) were run in scratch, and
each one failed validation as intended. These were not repeated for batch 22,
which did not change those checks. Only the new selector check was exercised:
the seeded wrong-selector cases are listed in the batch-22 section.

## Provenance

- **Batch-E rereview (latest):** the 4 records bind to the worktree HEAD
  `e64baab92377355d6f9335ddf10a0fbda1e0e6a3` (the batch-22 report commit). It
  contains native batch E (`4909572`, `c35ae5a`, `a7edea3`, `c0effbf`,
  `4895174`, `3a08f5f`, `95ffc02`), and root's registration and admission
  refresh `96be803`. Every other record keeps its own baseline.
  - The `inventory.jsonl` and `summary.json` committed in `e64baab` were
    generated on the batch-22 lane at `4f2ec86`, before batch E was
    integrated. So at `e64baab` they still showed the pre-repair E hashes and
    "0 stale", while `extract.py --check` at that commit reported the 4 E
    records stale. Both files are now regenerated at `e64baab`.
- **Batch 22 (reviewed out of order):** records bind to `59d03df`,
  like batch 6. The worktree HEAD at extraction was the batch-6 report commit
  `4f2ec86`, which changed no constructor. All 32 constructors are identical
  from the ordering commit `5436f3f` through `59d03df` and HEAD, and equal the
  ARC-GEN files.
- **Batch 6:** records bind to `59d03df` (root integration, which
  registered native batch D and refreshed role admissions). The worktree HEAD
  at extraction was the batch-5 report commit `ce6fb52`; no constructor
  changed between the two. The rereview and batch 1–5 baselines below are kept
  as written.
- **Current baseline (worktree HEAD at the rereview):**
  `8395c38ba950e45e1e23e6b8d81c434e048d62bd`, the batch-4 review commit.
  It sits on the integrated ARC-GEN baseline
  `9c53b2c517da9b7fee67e8ecbb2e2d581a21a586`, which includes native batches B
  (`cf6f34b`) and C (`a5251a7`), their supplement admission (`c75138a`,
  `a534dfe`) and the `verified_rules.py` change of `485b4ac`.
- **Original extraction baseline:** `5436f3fe035f261cdcf7996565c108148efa37fb`.
  This commit includes the seven native repairs of `1ed7790`. Batches 1–4
  were first reviewed at `5436f3f`, `f735382`, `f1b8bb9` and `a59e28a`.
- **Ordering commit (pinned):** `5436f3f`. Batch membership uses constructor
  hashes at this commit, so later edits do not reshuffle batches.
- **Audit:** `output/generator-domain-audit-20261024`, fork `cdf50ed`,
  128 samples per sampler.
  - At the original extraction, 713 of 729 audit records matched the
    constructor, and 16 were stale: the seven `1ed7790` repairs, plus
    `aaecdb9a`, `45bbe264`, `0934a4d8`, `00dbd492`, `3a301edc`, `009d5c81`,
    `3194b014`, `09c534e7` and `ecb67b6d`.
  - Now 694 of 729 match. The 11 B/C rereviewed families are also stale, because
    the audit describes their pre-repair constructors. Their current domains
    come from the repair reports and `probes/rereview_batch_bc.py`. The four
    native batch-D families (`db16125`) are stale for the same reason; see
    batch 5. So are the four batch-E families (`a7edea3`); see the batch-E
    rereview. All 35 must be remeasured.
- **Selection:** `docs/hybrid-generator-review/family-worklist.json` with
  `rearc_overlap == false`. This gives exactly 729 IDs, and validation checks
  them against this list.

## What each mechanical record contains

- **Source:** path, sha256, and whether the file has uncommitted edits.
- **`generate()`:** line span, parameters, and numbered constraint lines,
  meaning random draws, canvas allocations, loops, guards and rejections.
  At most 28 lines are listed per family; the full count is also given.
- **Audit summary:** native and configured input/output height and width
  ranges, shape counts, colour counts, non-modal density and components, and
  unique inputs and orbits. Also `requested`/`valid`/`errors` and
  `sample_shortfall`.
- **Canonical fixture:** train/test counts, shapes and input colours.
- **Certificate records:** state is `current`, `stale` or `unavailable`.
  `current` means only that a certificate's constructor hash, and factory hash
  where one applies, equals the current file. Direct-source program hashes
  were not rebuilt.
- **Factory:** path and hash, plus a flag set when the emitted program uses
  `demonstrations`. That flag is a lead only.
- **Priority:** rank, batch and tier.

Mechanical extraction is not semantic review. All 505 families outside
batches 1–6 and 22 (that is, batches 7–21 and 23) are
`semantic_review.status = "pending"`.

Totals:
- **Tiers:** Tier A has 122 families: the audit-sampled input height and width
  are both fixed and ≥ 8. Tier B has 607.
- **Tier A split:** 114 tier-A families have a current audit and fill batches
  1–4. The 8 audit-stale ones sit at the end of batch 4.
- **Certificates:** 724 current and 5 unavailable (`00576224`, `0692e18c`,
  `9110e3c5`, `f0100645`, `f18ec8cc`).
- **Audit shortfall:** 36 families got fewer than 128 valid native audit draws
  (time budget or timeouts). For these, the "fixed dims" signal and other
  ranges may describe very few scenes (see `summary.json`).

## Batch ordering

Batches of 32, in this order:
1. **Tier A:** audit-current families sorted by ID, then audit-stale ones.
2. **Tier B:** both dims fixed (< 8) first, then one dim fixed, then
   varying; within each group, fewest sampled input shapes first, then ID.

There are 23 batches; the last has 25 families.

## Rereview of 11 repaired constructors (native batches B and C)

**Scope:** 7 batch-1 families changed by native batch B (`cf6f34b`):
`03560426`, `0becf7df`, `0f63c0b9`, `14b8e18c`, `21f83797`, `2685904e` and
`2a28add5`. 4 batch-2 families changed by native batch C (`a5251a7`):
`50c07299`, `7e2bad24`, `7e576d6e` and `94414823`. Each old review's
constructor hash equals the source just before its repair commit, and was
unchanged from first commit (`991db6c` or `6eaf441`) to `8395c38`.

**What was read, for each family:**
- the whole current constructor, and its diff against the reviewed source;
- every canonical train/test pair (`validate()` replays all of them exactly);
- the factory, or for `94414823` the direct-source program;
- the independent pair verifier;
- every certificate record, with its dependency hashes;
- `native-batch-b-domains.json` or `native-batch-c/README.md`, and
  `test_native_batch_b.py` or `test_native_batch_c.py`. Both test files pass
  at `8395c38` (63 tests).

No factory changed after the earlier reviews:
- `5f3a2b8`: `03560426`, `0becf7df`, `0f63c0b9` and `14b8e18c`;
- `f103328`: `21f83797`, `2685904e` and `2a28add5`;
- `a51474e`: `50c07299` and `7e576d6e`;
- `ad3a6a9`: `7e2bad24`.

Pair verifiers are the archived solvers, except for `7e2bad24`, which uses
`verified_rules.native_side_beam`.

**Code run:** `probes/rereview_batch_bc.py` (seed 0). It is read-only. Apart
from its timing section, two runs gave byte-identical output.

**What changed in the records:**
- Every axis disposition, proposal, priority and uncertainty was rewritten from
  the current source, with current line numbers.
- New fields: `repair_delta`, `evidence`, `certificate_note`, `admission`,
  `audit_note` and `supersedes`. `repair_delta` separates newly expanded axes,
  retained rules and unsolved restrictions.
- Nothing was refreshed by hash alone.

### Per-family result

| ID | Priority (old → new) | Newly expanded | Still restricted or open |
|---|---|---|---|
| `03560426` | high → low | Height 6..30, box-derived width ≤ 30, 3–8 boxes; exact fixed-width compositions | Height-1 boxes; box caps 5/8 do not scale, so tall canvases are mostly empty (median 29% of rows used vs 40–50% canonical) |
| `0becf7df` | medium → low | Independent 7..30 canvas, stroke count scaled | One connected figure; figure density median 0.52 vs canonical 0.27–0.48 |
| `0f63c0b9` | high → low | 9..30 × 7..30, 3–6 seeds, exact gap sampler; `size` defect fixed | 2 seeds excluded. Tie-break concern resolved: 918/1000 pairs tie, and only 9 of 18,292 simulated episodes leave it undemonstrated |
| `14b8e18c` | high → low | 6..30 canvas, box count scaled, long sides 5..side-2; bounded loops; merged-diagonal mislabel removed | Short sides 1..4; nested squares rare (9/400). Feasibility resolved: median 1.5 ms per draw |
| `21f83797` | medium → low | Independent 5..30 canvas; box sides 3..side-2 | One-cell margin and TL/BR markers only |
| `2685904e` | medium → none | Width 4..30, height 6..30, free divider/data rows, L up to 15, 2–8 colours | None beyond fixture-faithful layout order |
| `2a28add5` | medium → low | Independent 5..30 canvas; anchor and dominance guard | Two noise levels only (canonical train[1] at 0.18 is below 1000 native draws). Single-cell runs: 81/81 verifier agreement |
| `50c07299` | high → medium | Independent 5..30 canvas, L up to 14; 31,304 exact inputs (was 56) | Segment always on the corner anti-diagonal; literal colours |
| `7e2bad24` | high → medium | Per-pair flip/flop/xpose (152 h / 148 v); bounded loop; side-contact verifier | 16×16 canvas; endpoint convention learnt from demonstrations (102/300 sensitive pairs) |
| `7e576d6e` | high → medium | Per-pair transpose (260 h / 240 v); bounded loop | 30×30 canvas; start row 1 and end rows 25–28; zigzag filter rejects 79% of layouts (still `unknown`) |
| `94414823` | high → none | Canvas 5..30 × 6..30, even side 4..28, free position; 79,803,360 exact inputs (was 224) | Literal frame and background colours |

Disposition counts for the 11 current rereviews:

| Axis | incidental | mixed | intrinsic / rule-supported | broadly variable | unknown |
|---|---|---|---|---|---|
| dimensions | 2 | 0 | 0 | 9 | 0 |
| objects | 0 | 6 | 4 | 1 | 0 |
| placement | 1 | 8 | 1 | 1 | 0 |
| density / colours | 2 | 3 | 5 | 1 | 0 |
| rule parameters | 0 | 2 | 8 | 0 | 1 |
| demonstration context | 0 | 1 | 10 | 0 | 0 |

### Adequacy and admission

- **Domain-adequate now, already admitted (source and measurement
  evidence):**
  - `2685904e` and `94414823` (`none`);
  - `03560426`, `0becf7df`, `0f63c0b9`, `14b8e18c`, `21f83797` and `2a28add5`
    (`low`, optional refinements only).

  All eight are in `prepare.REPAIRED` (native batch B: `c75138a`; batch C:
  `a534dfe`). They are supplement admissions, not RE-ARC `admission.json`
  entries. None is a new admission candidate, and none is release-ready.
- **Already admitted, with further constructor work proposed (`medium`):**
  - `50c07299`: diagonal offset;
  - `7e2bad24`: canvas size;
  - `7e576d6e`: canvas size, start/end rows, zigzag review.
- **No future admission candidates arise from this rereview:** all 11 are
  already in `prepare.REPAIRED`.

### Certificate evidence

All 11 records are `current`: constructor and factory/program hashes match, and
production lookup (`certified_factory_source` / `certified_source`) returns
a source. The probe found two dependency hashes that `extract.py` does not bind,
neither of which affects these families:

- **`auditor_sha256 c7c525a7`** (10 `recertify` certificates): this is
  `recertify.py` as of `cf79bbc`. The current file `1e194cb8` (`5fdfb65`) only
  adds the `FINITE_DOMAINS` branch for families with fewer than 100 unique
  inputs. None of these 10 is such a family.
- **`7e2bad24` `pair_verifier_sha256 d0b43e04`:** this is `verified_rules.py`
  before `485b4ac`. The current file `055138a0` only adds the `34b99a2b` checker.
  `native_side_beam` is unchanged by diff, and `admission.json` pins the
  current file.

No certificate was rerun. A passed certificate is a finite audit (1000 fresh,
8000 augmented, 16 fixture checks), not a proof or release readiness.

**Other reviewed families:** two had their certificate JSON reissued after
review: `981571dc` (`a534dfe`) and `dc2aa30b` (`8f7a9db`), each as a
`recertify` 1000/8000/16 record for `prepare.REVIEWED_NATIVE`. Their
constructor and factory hashes are unchanged, and their state is still
`current`. Their reviews are byte-identical, and no metadata update was needed.
The other 115 reviews, including the `782b5218` erratum, are byte-identical to
`8395c38`.

### Remaining gaps

- **Stale audit:** the 128-sample domain audit is stale for all 11 and must be
  rerun on the current constructors.
- **No production export:** no unmodified `prepare` 200/20 export is recorded
  for the batch-B or batch-C families. The batch-C 200/20 runs waived the
  `verified_rules.py` pin.
- **Thin validation support:** the canonical episodes are uniform-shape, so
  production episodes need three demonstrations of the query's shape. The
  nine canvas-expanded families spread 1000 draws over 388–526 shapes (batch-B
  report and probe), with at most 10 draws on any one shape. Batch C measured only 23 (`50c07299`) and 24 (`94414823`)
  validation query identities against 20 requested.
- **Open semantics:**
  - `7e576d6e`: whether the zigzag is part of the rule;
  - `7e2bad24`: which endpoint reading is original;
  - `50c07299`: whether the triangular series is intended;
  - `03560426`: whether the row must reach the right edge.
- **Sample statistics:** every density, tie and timing figure above is a
  seeded sample from one local run, not an audit.

## Rereview of 4 repaired constructors (native batch E)

**Scope:** `e0fb7511` (batch 3, first reviewed at `f1b8bb9`, committed in
`25c8140`), and `0c786b71`, `f0df5ff0` and `f3cdc58f` (batch 4, first reviewed
at `a59e28a`, committed in `24493e3`). Each old review's constructor hash is
the source at its baseline and at `a7edea3^`. Each review text was
byte-identical from its first commit through `e64baab`.

Native batch E was built on a lane and integrated with new hashes:

| Lane | Integrated | Scope |
|---|---|---|
| `05db160` | `4909572` | fixed-colour pair checkers for e0fb7511 and f3cdc58f |
| `ce8c79d` | `c35ae5a` | `mirror_neighbourhood_evidence.py` gates and `colour_evidence` dispatch |
| `b9480e9` | `a7edea3` | constructors, recertified factory records, tests, evidence |
| `51e67f2` | `3a08f5f` | e0fb7511 component-size threshold candidates (final gate `98e1b2ea`) |
| `9996de4` | `95ffc02` | evidence and context-audit refresh on the final gate |

The lane tip `9996de4` and HEAD are byte-identical for every E constructor,
factory, certificate, gate and batch-E report file. Root then registered the
four families in `prepare.REPAIRED` and refreshed the `admission.json` pins
(`96be803`).

**What was read, for each family:**
- the whole current constructor, the source at the old baseline, and the exact
  `a7edea3` patch;
- every canonical train/test pair;
- the direct factory (unchanged since before the old review: `871a44a1`,
  `66678c1e`, `d3eb4c59`, `81c2164b`);
- the production pair verifier: the archived reference for `0c786b71` and
  `f0df5ff0` (colour-agnostic and fixed-colour respectively), and
  `verified_rules.native_zero_adjacency` / `fixed_colour_histogram` for
  `e0fb7511` / `f3cdc58f`;
- the final `mirror_neighbourhood_evidence.py` and its `colour_evidence.py`
  dispatch (line 209);
- both certificate records per family, including merged draft notes;
- `native-batch-e/` README, `batch-e-evidence.json`, `context-audit.json`, the
  pre-threshold snapshots and the verifier evidence;
- `prepare.py`, `sampler.admission()`, `direct_certificates.py` and
  `admission.json`.

**Code run:**
- the existing focused tests, once: `test_native_batch_e.py`,
  `test_mirror_neighbourhood_evidence.py` and `test_e0_f3_verifiers.py`, 80
  passed at `e64baab`;
- a new read-only, seeded probe, `probes/rereview_batch_e.py`. Two runs gave
  byte-identical output (sha256 `4bca2dc5…` at `e64baab`; the output records
  HEAD, so the hash differs at other commits; no timing section). It does not
  repeat the batch-E coverage or context-audit runs. It adds:
  - production lookups at HEAD;
  - canonical latent parameters checked against the **current random path**,
    not only explicit replay;
  - restrictions that remain in the default sampler;
  - plausible competitor rules that no gate enumerates.

No certificate was rerun or required: constructors and factories are unchanged
since certification, and the evidence pins equal HEAD.

### Per-family result

| ID | Priority (old → new) | Repair delta (implemented in batch E) | Still restricted or open |
|---|---|---|---|
| `0c786b71` | medium → low | Input H, W 2..15 (explicit 1..15), output up to 30×30; anchor gate | Pool fixed at 3 colours from 1..9 (black never sampled; 1-colour inputs ≈0.1%) |
| `e0fb7511` | medium → low | W, H 6..30; per-scene density 0.15..0.35; area-scaled azure floor; bounded loop; fixed-colour checker; connectivity × threshold gate | Floor removes scenes marking under ≈7.7% of the canvas (46/400 draws retried); 6×6 needs gate retries (11/250) |
| `f0df5ff0` | medium → **high** | W, H 6..30; seeds 2..area-scaled max (2..29 measured); confetti 0.3..0.5; bounded loop; square-vs-cross gate | **Canonical `train[1]` is unreachable:** it has 7 confetti colours, but line 150 `choices(range(2,10), 6)` gives ≤ 6 (legacy too; missed by the old review). Edge seeds and overlaps stay excluded |
| `f3cdc58f` | medium → medium | W, H 4..30; placements 2..min(H, 4H//5), bars to 24; bounded loop; fixed-legend checker | **No gate:** an ascending-count column legend fits all 3 demos and changes the query in 67/2000 4×4 contexts (6/2000 at default shapes). Bars above 0.8 H never sampled; ink density uncontrolled across widths |

Every old proposal (sample sizes, counts and densities) is implemented. None is
repeated. The new priorities come from findings the old reviews did not have:
- `f0df5ff0` is now `high`, because a canonical input is unreachable. This is
  the same criterion as batches 5, 6 and 22. The fix is narrow: line 150 only.
- `f3cdc58f` is `medium` for gate work, not constructor work. It follows the
  `3d31c5b3` precedent: 2.6% ungated ambiguity was `medium`.

Disposition counts for the 4 current rereviews:

| Axis | incidental | mixed | intrinsic / rule-supported | broadly variable | unknown |
|---|---|---|---|---|---|
| dimensions | 0 | 0 | 0 | 4 | 0 |
| objects | 0 | 2 | 1 | 1 | 0 |
| placement | 0 | 1 | 1 | 2 | 0 |
| density / colours | 0 | 4 | 0 | 0 | 0 |
| rule parameters | 0 | 0 | 4 | 0 | 0 |
| demonstration context | 0 | 2 | 2 | 0 | 0 |

The old reviews had all four dimensions `incidental`. Two other axes changed
from `intrinsic` to `mixed`:
- **Demonstration context** for `e0fb7511` and `f3cdc58f`: identifiability now
  depends on a gate (e0), or on a gate that is missing (f3).
- **Density/colours** for `f3cdc58f`: the legend is still intrinsic, but ink
  density across widths is uncontrolled.

### Retained constraints, sampling minima and measurable restrictions

The records keep these three kinds apart.

**Retained intrinsic or fixture-faithful constraints:**
- the mirror anchor (0c);
- 4-adjacency and the 0/1/8 roles (e0);
- the 3×3 window, confetti preservation, no blue confetti, interior seeds and
  disjoint windows (f0). Edge seeds and overlaps are undemonstrated;
- all four colours present, the colour-value legend and W ≥ 4 (f3).

**Sampling minima:** these are choices, not semantics, and explicit arguments
go below them.
- Random minimum dimensions: 2 (0c), 6 (e0, f0) and 4 (f3).
- The clarity floors:
  - e0: `max(2, round(13·HW/169))` azure cells;
  - f0: at least 3 visible blue cells per window;
  - f3: all four colours survive.
- Retry budgets: 200, 200 and 100.

**Remaining measurable restrictions** (probe, seed 0, N = 400 unless noted):
- 0c: a 3-colour pool (395/400 three-colour, 5/400 two-colour, 0/400
  one-colour).
- e0: realised azure fraction ≥ 0.075; random density 0.15..0.35.
- f0: ≤ 6 distinct confetti colours (median 4; canonical 4, 7, 6, 6). Seeds
  stay at ≤ 0.5 of window capacity, and default draws never use the lattice
  placer (0 of the 625 6..30 shapes).
- f3: max bar/H ≤ 0.8 in 400/400 (no random height allows a full-height bar);
  ink density 0.023–0.49.

### Certificates, gates and production status

These are three different things, and the records keep them apart.

1. **Repair-time snapshots (upstream lane).** The following are the batch-E
   lane's measurements:
   - certificates: 1000 fresh / 8000 D4 / 16 fixtures, 0 rejections;
   - coverage: 194/515/497/541 input shapes per 1000 draws;
   - gate-aware context audit: 250/250 queries, default and min corner.

   Every pin in `batch-e-evidence.json` and `context-audit.json` equals the HEAD
   file: constructor, factory, factory certificate,
   `mirror_neighbourhood_evidence` 98e1b2ea, `colour_evidence` 6789d3d8,
   `verified_rules` a54743d7, `program_targets` 88298f33 and harness. The
   certificates' `auditor_sha256` 1e194cb8 is the current `recertify.py`.

   Three dependency details stay explicit:
   - The certificates predate the final threshold gate (`3a08f5f`).
     `recertify.check` does not run gates, so gate coverage rests on the
     refreshed context audit only.
   - `verifier-evidence-e0fb7511-f3cdc58f.json` pins the current
     `verified_rules` but the **legacy** constructors `3857588f` and
     `763478e5`. Its 0/1000 and adversarial results are legacy-draw results.
     `batch-e-evidence.json` gives 0 disagreements on 1000 current draws.
   - The certificates' merged `draft_notes` carry an independent review bound
     to the pre-repair constructors (e0, f0 and f3). Their statements are
     historical: "1-in-8 density", "not gated", "only 10x10".
2. **Current production registration and admission (HEAD `e64baab`).**
   - All four are in `prepare.REPAIRED` (line 38, `96be803`). They are
     supplement entries, not RE-ARC `admission.json` entries.
   - All 471 `admission.json` target pins equal the HEAD files, so
     `sampler.admission()` loads.
   - `certified_factory_source` returns a program for all 8 D4 transforms.
   - The gate dispatches for 0c, e0 and f0, and canonical demos pass it. f3 is
     ungated.
3. **Unknown: full `prepare` exports.** No unmodified `prepare` 200/20 export
   for these families is recorded in this worktree, and batch E ran none. So
   these are unmeasured:
   - same-shape support (batch E estimated 147/55/45/37 shapes with ≥ 4 pairs
     per 1000 draws);
   - gate retry rates under `prepare`;
   - validation query identities.

   Registration is not an export, and no smoke test or certificate makes a
   family release-ready. `release_ready` stays false.

**Stale side records (reported, not edited):**
- `arc_agi2/reports/diversity-v1/family-status.csv` (last changed in
  `d71ead8`) still lists all four with their pre-repair constructor hashes and
  `native_repaired=False`.
- The 128-sample audit is stale for all four.

### Other stale or soon-stale constructors (not reviewed here)

At `e64baab`, `extract.py --check` reports 0 stale reviews. No F, G or H
repair is integrated in HEAD. But three lane branches change constructors of
batch-5-reviewed families:
- `hybrid-claude-native-f-20261025`: `27f8ce4f`, `48f8583b` and `5b6cbef5`;
- `hybrid-claude-native-g-20261025`: `4cd1b7b2` and `8ba14f53`;
- `hybrid-native-h-20261025`: `6d1d5c90`.

Those six reviews will go stale when root integrates the lanes. They must then
be rereviewed the same way. Their review is neither faked nor pre-empted here,
and validation is unchanged for them.

### Remaining gaps

- **`f0df5ff0`:** the confetti pool literal (line 150) excludes canonical
  `train[1]`.
- **`f3cdc58f`:** no gate for count-ordered legends. Episodes like these would
  pass `make_record` today.
- **Not measured:** no unmodified `prepare` export, so no production
  same-shape support, gate retry or validation-identity figures. The audit is
  stale.
- **Open semantics:**
  - whether 4+-colour inputs belong to `0c786b71`;
  - whether bars above 0.8 H belong to `f3cdc58f`;
  - whether edge seeds and overlaps belong to `f0df5ff0`.
- **Gate scope:** each gate rules out only its named alternatives. The probe's
  competitors are hypotheses too.
- **Sample statistics:** every probe figure is a seeded local sample, not an
  audit.

## Batch 1 semantic review (32 families)

> **Historical record.** This section describes the batch-1 reviews as first
> written at `5436f3f`, and its tables count those records. Seven of them
> (`03560426`, `0becf7df`, `0f63c0b9`, `14b8e18c`, `21f83797`, `2685904e`,
> `2a28add5`) are superseded by the rereview above; their original text is in
> `review_history.json`. Current batch-1 counts are in `summary.json`. Current
> batch-1 priorities: high 8, medium 14, low 9, none 1.

For each family, the generator body, its helpers and `validate()` were read,
alongside the canonical fixture grids and the audit record. Factory code was
read where demonstrations matter (`1b8318e3`, `4852f2fa`). Each record gives
a line-referenced disposition on six axes, plus mechanism, fixture evidence,
proposal, priority, uncertainties and certificate state. No code was run
except extraction. No fresh sampling or verifier test was done, so any claim
about verifier behaviour is listed as an uncertainty.

### Axis dispositions (count of families)

| Axis | incidental | mixed | intrinsic / rule-supported | broadly variable | unknown |
|---|---|---|---|---|---|
| dimensions | 27 | 5 | 0 | 0 | 0 |
| objects | 2 | 26 | 4 | 0 | 0 |
| placement | 5 | 13 | 13 | 1 | 0 |
| density / colours | 7 | 5 | 17 | 3 | 0 |
| rule parameters | 1 | 5 | 22 | 2 | 2 |
| demonstration context | 0 | 7 | 24 | 0 | 1 |

**Patch priority:**
- **High (11, as first written):** `03560426`, `0a1d4ef5`, `0b17323b`,
  `0f63c0b9`, `1478ab18`, `14b8e18c`, `1b8318e3`, `1c02dbbe`, `332202d5`,
  `342ae2ed`, `42f14c03`. `03560426`, `0f63c0b9` and `14b8e18c` are now `low`
  after native batch B and the rereview.
- **Medium (18, as first written).** `0becf7df`, `21f83797` and `2a28add5` are
  now `low` and `2685904e` is `none`.
- **Low (3):** `15113be4`, `319f2597`, `465b7d93`. Their configured
  parameter path already adds sizes.

The fixed canvas is the common incidental restriction. None of the 32 rules
needs its particular literal canvas size. The five `mixed` dimension cases tie
one side to a legend or cell structure (`20fb2937`, `15113be4`), or have a
square-only size parameter (`319f2597`, `342ae2ed`, `465b7d93`). Object,
placement and colour limits are more often mixed: some guards support the rule
(separation, distinct colours, unique matches), while the numeric ranges are
tied to the canvas.

### Key findings

- **Native sampler barely produces scenes:**
  - `1b8318e3`: the audit got 1 valid draw out of 3, with 2 timeouts. Its
    "fixed 10×10" is an artefact. `num_pixels ≥ size` (line 86) is above the
    canonical 5–12 pixels, and it makes unique docking rarely satisfiable.
  - `342ae2ed`: 10 valid out of 12, with 2 timeouts.
  - `14b8e18c`: 41 valid out of 43, with 2 timeouts. *Resolved by native
    batch B (bounded loops; rereview probe median 1.5 ms per draw).*
  - `20fb2937` and `22806e14` used up the 16 s budget at 76 and 104 draws.

  For `1b8318e3`, `342ae2ed`, `20fb2937` and `22806e14`, fix feasibility
  first and re-audit before judging diversity.
- **Canonical fixtures outside the native domain:**
  - `1c02dbbe`: a 10×10 grey rectangle, where the native range is 11–13.
  - `332202d5`: a line at row 14, where native rows are 1–13.
  - `42f14c03`: a 9-wide I shape, where native widths are 4–5.
  - `4852f2fa`: a sprite spanning only 2 rows. The helper never empties a row
    or column.
  - `1b8318e3`: pixel counts below the native minimum.
- **Tiny finite domains:**
  - `0b17323b`: the whole native domain is 6 inputs (3 spacings × 2 starts).
  - `1478ab18`: the whole native domain is 220 scenes.
- **Latent source defects (no patch applied by this review):**
  - `0f63c0b9`: it had a `size` parameter, but the canvas was a literal
    `grids(15, 15)` (line 38 of the reviewed source). *Fixed in `cf6f34b`:
    current lines 33–36 and 54.*
  - `0a1d4ef5`: the noise-patch check indexes the 30-wide canvas with the
    lattice width (line 68).
  - `319f2597`: the guard at line 45 counts blacked cells. It never ensures a
    preserved red cell.
  - `305b1341`: per-box fg and bg come from independent draws, so they can be
    equal.
- **Demonstration context matters:**
  - Factories that pick rules from demonstrations: `1b8318e3` (docking rule)
    and `4852f2fa` (crop/axis hypotheses).
  - Conventions that only some pairs reveal:
    - `0f63c0b9`: the odd-gap tie-break. *Measured in the rereview: 918/1000
      native pairs show it;*
    - `1d61978c`: the majority orientation versus a fixed mapping;
    - `22806e14`: both plus outcomes;
    - `332202d5`: equal-colour band merging;
    - `305b1341`: legend z-order under flips.

  Episode-level coverage of these was not measured.

## Batch 2 semantic review (32 families, ranks 33–64)

> **Historical record.** This section describes the batch-2 reviews as first
> written at `f735382`, and its tables count those records. Four of them
> (`50c07299`, `7e2bad24`, `7e576d6e`, `94414823`) are superseded by the rereview
> above; their original text is in `review_history.json`. Current batch-2
> priorities: high 3, medium 26, low 2, none 1.

**Scope:** tier A, all audit-current. Every constructor sha256 is unchanged
from the ordering commit to the review baseline `f735382`. Every family has a
`current` direct certificate:

- 29 are `direct_factory` records;
- 3 are `direct_certificate` records (`4f537728`, `522fdd07`, `94414823`).

**What was read:** for each family, the whole `generate()` body, its helpers
and `validate()`, plus every canonical train/test grid and the audit record.
Factory source was read where demonstrations or orientation matter
(`4c177718`, `4e469f39`, `73182012`, `782b5218`, `7e2bad24`).

**Unlike batch 1, some code was run:** the read-only, seeded scripts in
`probes/`. Their results are quoted in the reviews. No certificate or audit
was rerun.

### Axis dispositions (count of families)

| Axis | incidental | mixed | intrinsic / rule-supported | broadly variable | unknown |
|---|---|---|---|---|---|
| dimensions | 29 | 3 | 0 | 0 | 0 |
| objects | 6 | 20 | 5 | 1 | 0 |
| placement | 4 | 17 | 9 | 2 | 0 |
| density / colours | 9 | 16 | 7 | 0 | 0 |
| rule parameters | 0 | 4 | 27 | 0 | 1 |
| demonstration context | 0 | 6 | 26 | 0 | 0 |

**Patch priority:**
- **High (7, as first written):** `4f537728`, `50c07299`, `54db823b`,
  `7e2bad24`, `7e576d6e`, `917bccba`, `94414823`. After native batch C and the
  rereview, `50c07299`, `7e2bad24` and `7e576d6e` are `medium` and `94414823`
  is `none`.
- **Medium (23).** Includes `782b5218`, which was originally rated high; see
  the erratum below.
- **Low (2):** `5b37cb25` and `981571dc`. Both already have wide variety
  (128/128 unique audit inputs). For `981571dc`, the 30×30 crop of a 32×32
  mosaic is fixture-faithful, so no patch is justified.

As in batch 1, a fixed literal canvas is the main incidental restriction:
29 of 32 families. The three `mixed` dimension cases:
- `668eec9a`: the 5-row output equals the maximum line count.
- `7c9b52a0`: the output follows the window size, and 3×3/5×5 are excluded.
- `981571dc`: the off-centre crop is canonical.

### Discoveries

- **Audit artefact, not infeasibility.**
  - `54db823b`: the audit shows 1 valid draw out of 3, with 2 timeouts at the
    2 s per-draw limit. `probes/time_draws.py` gave 70/70 valid draws (seeds
    0 and 1, 10 s limit). The median was 2–11 ms and the maximum 3.4 s.
  - The cause is an unbounded whole-scene rejection loop (line 36) with a
    heavy tail. Pixel counts are assigned to boxes in sorted order without
    regard to box area (lines 42–47), which adds rejections.
  - Fix sampling and re-audit before judging diversity.
- **Native orientation never varies, unlike the fixtures.**
  - In `7e2bad24` and `7e576d6e`, the random branch never assigns
    `flip`/`flop`/`xpose`, so they stay `None`.
  - The canonical fixtures mix orientations within one episode.
  - `probes/orientation_blockers.py` found horizontal walls/lines in 200/200
    and 100/100 native draws.
  - For `7e2bad24`, the factory also keeps four rival mirror-end readings and
    picks between them using demonstrations.
  - *Resolved by native batch C (`a5251a7`): both now sample orientation per
    pair. The rereview probe measured 152 h / 148 v and 260 h / 240 v.*
- **Bottom exits in `782b5218` are fixture-supported (corrected; see
  erratum).** Line 52 rejects lines that leave the top edge, but lines may
  leave through the bottom. Canonical `train[2]` (identical to
  `validate()['train'][2]`) does exactly this: column 9 contains no red, and
  the output's column 9 is all zeros.

  `probes/line_span_782b5218.py` prints that counterexample. It then finds 136
  of 3000 native inputs (4.5%, seed 0) with a red-free column. In all 136,
  those output columns are blank, matching the canonical pair. The factory's
  flood fill agreed with the native output on all 3000.

  Preserve this behaviour. No bottom guard is justified.

  > **Erratum (2026-10-24, corrected after `573f0b6`).** The batch-2 text
  > called this a "latent defect", claimed that every canonical line spans all
  > 10 columns, rated the family high, and proposed a bottom-edge guard. That
  > was wrong: canonical `train[2]` demonstrates bottom clipping, so the guard
  > would narrow canonical support.
  >
  > An independent implementation worker and the orchestrator found the error.
  > The measured 136/3000 statistic is unchanged; only its interpretation
  > changed. The `782b5218` record in `semantic_reviews.json` carries an
  > `erratum` field with the original wording. Remaining proposal: canvas
  > generalisation and a bounded loop (medium).
- **Tiny or single-geometry domains.**
  - `94414823`: one geometry. The domain is 56 colour pairs × 4 orientations;
    the audit found 1 orbit. *Resolved by batch C: 79,803,360 inputs.*
  - `50c07299`: 56 inputs. Every segment lies on the main anti-diagonal.
    Every canonical example is also the L-th term of a corner-anchored series.
    *Batch C widened this to 31,304 inputs; the corner anti-diagonal remains.*
  - `4f537728`: 800 inputs (35 orbits).
  - `917bccba`: about 424 geometries (51 orbits).
  - `95755ff2`: the diamond geometry is fixed.
- **Colour-role collisions.** Both are deterministic, but they make the
  scene visually ambiguous:
  - `95755ff2`: the dust colour can equal the diamond red, with probability
    1/9 (line 55).
  - `9356391f`: a legend colour can equal the grey used as the clipped-ring
    marker.
- **Constants that are never resampled.**
  - `689c358e`: the plus colours always use the default `[2,5,8,9]`.
  - `8e301a54`: the sprite colours are always `[2,5,9]`.
- **A bound that silently does rule work.** In `689c358e`, the per-angle
  bounds alone stop two pluses from marking the same frame line.
  `probes/frame_marks_689c358e.py` found 0 such collisions in 2000 draws. A
  larger canvas would need an explicit guard.
- **Demonstration context.**
  - `73182012`: the factory reads the quadrant size from demonstration
    outputs, and the answer corner is a d4 convention.
  - `782b5218`: the factory learns which edge is cleared from demonstrations.
  - `522fdd07` and `9356391f`: a convention appears only in some pairs (the
    pixel→9×9 wrap and the clipped-swatch grey).
  - Episode-level coverage of these was not measured.

### Unknowns

- `7e576d6e`, rule parameters: whether the zigzag filter (lines 52 and 61) is
  part of the original rule. *Still open after the rereview; the filter rejects
  79% of layouts that reach `draw()`.*
- `692cd3b6`: whether the extra-bit rules for the 12 opening-direction
  combinations not in the fixtures are faithful.
- `7c9b52a0`: why 3×3 and 5×5 windows are excluded.
- Domain sizes for `4e469f39`, `917bccba` and `692cd3b6` are hand counts, not
  enumerations.
- When batch 2 was written, no proposed patch had been implemented or
  recertified. Since then, native batch C implemented and recertified patches
  for the four families above. Every other batch-2 proposal is still
  unimplemented.

## Batch 3 semantic review (32 families, ranks 65–96)

> **Historical record.** This section describes the batch-3 reviews as first
> written at `f1b8bb9`, and its tables count those records. `e0fb7511` is
> superseded by the batch-E rereview; its original text is in
> `review_history.json`. Current batch-3 priorities: high 5, medium 23, low 4.

**Scope:** tier A, all audit-current. Every constructor sha256 is unchanged
from the ordering commit to the review baseline `f1b8bb9`, and also equals
the constructor in `/Users/ritwika/projects/ARC-GEN/tasks`. Every family has
a `current` certificate:

- 29 are `direct_factory` records.
- 3 are `direct_certificate` records (`996ec1f3`, `9a4bb226`, `af24b4cc`).
  Their reference `transform(grid)` reads only the query grid.

**What was read:**
- for each family: the whole `generate()` body, its helpers and `validate()`,
  every canonical train/test grid, and the audit record;
- every factory's `solve` body. Demonstration use was judged from that code,
  not from the mechanical flag;
- certificate notes (`context_retries`, `finite_default_domain`,
  `draft_notes`) where they bear on the review.

**Code run:** new read-only, seeded probes in `probes/`:
- `stuck_scenes_bb52a14b.py`;
- `ladder_rules_a1aa0c1e.py`;
- `configured_clip_d304284e.py`;
- `fixture_stats_batch3.py`;
- the existing `time_draws.py`.

No certificate or audit was rerun.

### Axis dispositions (count of families)

| Axis | incidental | mixed | intrinsic / rule-supported | broadly variable | unknown |
|---|---|---|---|---|---|
| dimensions | 25 | 7 | 0 | 0 | 0 |
| objects | 2 | 26 | 4 | 0 | 0 |
| placement | 0 | 20 | 9 | 3 | 0 |
| density / colours | 7 | 6 | 19 | 0 | 0 |
| rule parameters | 0 | 7 | 25 | 0 | 0 |
| demonstration context | 0 | 5 | 27 | 0 | 0 |

**Patch priority:**
- **High (5):** `bb52a14b` (sampler hang), `a416fc5b`, `b7fb29bc`, `aaef0977`
  and `db7260a4` (tiny domains).
- **Medium (24).**
- **Low (3):** `996ec1f3` and `d304284e` already have approved size overrides
  on the configured path; `dc2aa30b` has wide variety (128/128 unique).

As before, a literal canvas is the main incidental restriction (25 of 32).
The 7 `mixed` dimension cases are:
- tied to structure: `a1aa0c1e` (3 levels → 3×5 output), `afe3afe9` (7×7
  lattice → 30×30), `cfb2ce5a` (2·4+2), `b2bc3ffd` (lift headroom);
- a canonical quirk: `a416fc5b` (16×16 blank output);
- size parameters that exist but are restricted: `996ec1f3` (square only, plus
  band not scaled) and `d304284e` (placement not scaled).

### Discoveries

- **`bb52a14b` audit shortfall is a hang, not a heavy tail.**
  - Draws are bimodal. `time_draws.py` (seeds 0 and 1, 5 s limit) gave 91/96
    valid, with successes at most 4 ms and every failure at the limit.
  - `stuck_scenes_bb52a14b.py` found 10/300 scenes (3.3%) that never accept,
    and all 10 are rejected even with zero noise.
  - Pattern and copy positions are drawn once (lines 59–71), outside the
    `while True` at line 72. Every stuck example has a copy touching the
    border, which fits partial border matches: line 41 skips out-of-bounds
    cells, then line 47 rejects.
  - The fixed 22×22 is a real source literal, not an artefact.
  - Fix sampling and re-audit before judging diversity.
- **Canonical conventions that native never produces.**
  - `aa300dc3`: pair 1 has a 3-way diagonal tie broken toward the centre.
    Native rejects ties (lines 52 and 75).
  - `d753a70b`: pair 0's one-column boundary translation (`extra`), and
    pair 2's radius-6 ring (native radius is 0–3). The certificate already
    uses a teaching fixture (`original_fixture_context_passed: false`).
  - `e0fb7511`: canonical black density is 0.16–0.31. Native is fixed at
    1/8, with an audit range of 0.107–0.219. *Resolved by native batch E
    (`a7edea3`): per-scene density 0.15..0.35 now covers all four canonical
    densities (batch-E rereview).*
- **Rule identity chosen from demonstrations.** These factories filter
  hypotheses against demonstrations and raise if the query is unresolved:
  - `a1aa0c1e`: length rank versus rung count. Both fit all 4 canonical
    pairs; they differ on 62% of native pairs.
  - `aa300dc3`: 10 hypotheses, 113 context retries.
  - `afe3afe9`: 3 hypotheses, 39 retries.
  - `c35c1b4c`: 8 hypotheses, 26 retries.

  `c6e1b8da` reads demonstrations only to reject contradictions. The other
  27 factories and programs do not read them.
- **Tiny or templated domains.**
  - `a416fc5b`: 16 inputs, fixed motif.
  - `b7fb29bc`: 49 inputs, fixed frame.
  - `aaef0977`: 576 inputs.
  - `db7260a4`: two fixed cup templates; 95/128 audit-unique and about
    500/1000 certificate-unique.
  - `b2bc3ffd`: about 940/1000.
- **Latent defects (no patch applied).**
  - `cf133acc`: a debug `print` at line 77 runs on every native draw.
  - `d304284e`: drawing indexes with a literal 3, ignoring `wide` (lines 52,
    53 and 58). The approved 10×12 override clips the input sprite in 95/400
    draws.
  - `c6e1b8da`: `>= 20` (line 62) stops moved boxes touching the bottom or
    right edge.
  - `bd283c4a`: tied counts (1.9% of draws) fall back on dict insertion order.
  - `cfb2ce5a`: colour 0 can make a hint pixel invisible. This is
    fixture-faithful.

### Unknowns

- `a1aa0c1e`: is the original rule length rank or rung count?
- `aa300dc3`: are diagonals counted whole or as contiguous runs, and how
  should ties break?
- `a416fc5b`: is the blank 16×16 output for solved boards meaningful?
- `d753a70b`: is the canonical translation a rule or a data error?
- Not measured: episode-level context-retry rates, acceptance rates after the
  proposed resizing, and the per-match trace for `bb52a14b`.

### Input drift since batch 2

The shared worklist was edited after `f735382`. The regenerated
`inventory.jsonl` now records `native_repaired: true` and
`remeasure_original_audit_after_constructor_change` for 14 families:

- the 7 batch-1 families `03560426`, `0becf7df`, `0f63c0b9`, `14b8e18c`,
  `21f83797`, `2685904e` and `2a28add5`;
- the 7 already audit-stale families `137f0df0`, `31adaf00`, `84db8fc4`,
  `a406ac07`, `ce039d91`, `d282b262` and `f45f5ca7`.

At the time, the 7 batch-1 families had different constructors in ARC-GEN
than in this worktree, so their reviews were `current` here but would have
been stale against ARC-GEN. They were left byte-for-byte unchanged.

By the time of the `782b5218` correction commit, the worklist also flagged 4
batch-2 families: `50c07299`, `7e2bad24`, `7e576d6e` and `94414823`. Their
ARC-GEN constructors differed from this worktree, and their reviews were
likewise left unchanged. Only their mechanical `worklist` fields were
regenerated. `782b5218` has the same constructor in both places.

*Resolved:* those constructors landed with the integrated baseline `9c53b2c`,
and all 11 were rereviewed (see the rereview section). The superseded texts are
in `review_history.json`.

## Batch 4 semantic review (32 families, ranks 97–128)

> **Historical record.** This section describes the batch-4 reviews as first
> written at `a59e28a`, and its tables count those records. `0c786b71`,
> `f0df5ff0` and `f3cdc58f` are superseded by the batch-E rereview; their
> original text is in `review_history.json`. Current batch-4 priorities: high
> 5, medium 14, low 7, none 6.

**Scope:**
- 18 tier-A families with a current audit.
- 8 tier-A families with a stale audit:
  - 7 native repairs from `1ed7790`/`5436f3f`: `137f0df0`, `31adaf00`,
    `84db8fc4`, `a406ac07`, `ce039d91`, `d282b262` and `f45f5ca7`;
  - `aaecdb9a`, hand-written in `d71ead8`.
- 6 tier-B families.

Every constructor sha256 is unchanged since the ordering commit and equals the
ARC-GEN constructor. Certificates: 30 are `current`. `00576224` and `0692e18c`
are `unavailable`: there is no certificate and no factory, only an
uncertified `direct_programs.py` candidate.

**What was read:**
- for each family: the whole `generate()` body, its helpers, every canonical
  train/test grid and the audit record;
- every factory's `solve` body (in full where demonstrations are read:
  `f3e62deb`, `17cae0c1`).

For the 8 audit-stale families the 128-sample audit describes an older
source. Their current domain was taken from
`../native-domain-expansion-20261024/measurements.json` (its source hashes
equal the current files) and from `native-certificates/`. No repair that
those files already record is proposed again.

**Code run:** a new read-only, seeded probe, `probes/fixture_stats_batch4.py`
(seed 0, N=2000). Two runs gave byte-identical output. No certificate or
audit was rerun.

### Axis dispositions (count of families)

| Axis | incidental | mixed | intrinsic / rule-supported | broadly variable | unknown |
|---|---|---|---|---|---|
| dimensions | 17 | 7 | 0 | 7 | 1 |
| objects | 2 | 20 | 4 | 6 | 0 |
| placement | 0 | 15 | 15 | 2 | 0 |
| density / colours | 5 | 19 | 8 | 0 | 0 |
| rule parameters | 0 | 0 | 32 | 0 | 0 |
| demonstration context | 0 | 4 | 28 | 0 | 0 |

**Dimensions:**
- The 7 broadly variable families are exactly the seven expansion repairs.
  `ce039d91` keeps an even width as a rule boundary.
- `fd02da9e` is `unknown`: no fixture shows how its corner templates scale.

**Patch priority:**
- **High (4):**
  - `15696249`: canonical inputs fall outside the native domain.
  - `f3e62deb` (64 inputs), `17cae0c1` (60 inputs) and `fd02da9e`
    (15 corner patterns): tiny domains.
- **Medium (16).**
- **Low (6):**
  - `e2092e0c`, `e99362f0`, `ea9794b1` and `0c9aba6e` already have size
    parameters on the configured path.
  - `00576224` and `0692e18c` are blocked on certification, not on their
    domain.
- **None (6):** `137f0df0`, `84db8fc4`, `a406ac07`, `ce039d91`, `d282b262` and
  `f45f5ca7` already have wide, certified support. They only need the stale
  audit rerun.

### Discoveries

- **Canonical inputs outside the native domain.**
  - `15696249`: line 49 forces exactly 3 cells per hue, but canonical
    `train[0]` and the test input have counts 2/3/4.
  - `31adaf00` (repaired): native grey density is median 0.59 at a requested
    10×10 (165/200 draws above 0.5). The canonical inputs are 0.35–0.41.
    Line 59's order-independence rejection pushes scenes towards high grey.
    This is a density drift, not invalidity: the certificate passed.
- **Tiny or finite domains, enumerated by the probe.**
  - `f3e62deb`: 64 inputs.
  - `17cae0c1`: 60 inputs.
  - `fd02da9e`: 5508 inputs from only 15 occupancy patterns.
  - `f1bcbc2c`: exactly 4156 inputs (2078 per flop).
  - `0692e18c`: 223 sprite masks reached.
    `common.conway_sprite` shuffles rows and columns independently, so
    every mask covers all rows and columns.
- **Legend conventions that episodes may not show.**
  - `f3e62deb`: in 42.6% of simulated 3-demo episodes the query colour is
    missing from the demos. Canonical `test[0]` (colour 3) is also missing
    from train, so elimination is canonical.
  - `17cae0c1`: 19.8% of episodes.
  - Both factories hard-code the legend. They read demonstrations only for
    unknown keys, which native scenes never produce.
- **Undemonstrated tie-break.** In `e45ef808`, the leftmost-shortest rule
  decides about 55% of native draws, but no canonical pair shows a shortest
  tie.
- **Latent defect (no patch applied).** In `ff2825db`, line 65 swaps the
  clutter-box bounds, so 42.9% of parameter draws are clipped by the
  interior. Scenes stay valid.
- **Verifier mismatch, not invalidity.** `aaecdb9a` dense scenes are covered
  by the `verified_rules.legend_object_chart` override and its counterexample
  file.

### Unknowns

- `fd02da9e`: whether corner templates are corner-anchored on larger canvases.
- `e45ef808`: the original shortest tie-break.
- `f3e62deb` and `17cae0c1`: whether elimination-only queries are intended.
- `e99362f0` and `ea9794b1`: whether priority follows colour or quadrant.
  Native data always binds the two together.
- `00576224` and `0692e18c`: whether the `direct-candidate-audit.json`
  failure applies to the current `direct_programs.py` candidates.
- Not measured: episode-level coverage under the production sampler, and
  acceptance after any proposed patch.

## Batch 5 semantic review (32 families, ranks 129–160)

**Scope:** 32 tier-B families. Every record is bound to the constructor at
baseline `724a43b` (the rereview commit on the integrated branch).
- **Four first reviews after repair:** native batch D (`db16125`) expanded
  `195ba7dc`, `281123b4`, `31d5ba1a` and `34b99a2b` before review.
  - Their records carry `review_kind = first_review_after_native_repair`,
    `repair_commit`, `repair_delta`, `evidence`, `certificate_note`,
    `admission` and `audit_note`.
  - Their pre-repair 6x5, 4x4, 5x3 and 4x5 audit sizes are stale.
- **28 first reviews:** constructors unchanged since the ordering commit; the
  128-sample audit matches them.
- **Certificates:** all 32 are `current` (31 `direct_factory`, plus
  `66e6c45b` as a `direct_certificate`). No certificate or audit was rerun.

**What was read:**
- for each family: the whole constructor, every canonical train/test pair
  (`runtime.reference(tid)["canonical"]`), the factory `build_program` body
  (or, for `66e6c45b`, the saved teacher `transform` that `program_targets`
  wraps) and the certificate records;
- the gates the families use: `colour_evidence.py` (`6ea4a07e`),
  `panel_collision_evidence.py` (`337b420f`), `panel_overlay_evidence.py`
  (batch D) and `finite_input_policy.py` (`3979b1a8`, `66e6c45b`,
  `833966f4`, `8b28cd80`);
- for batch D: `verified_rules.midpoint_or_panels`,
  `separated_priority_panels` and `midpoint_xor_panels`, the batch-D report,
  `batch-d-evidence.json` and `context-audit.json`.
  `test_native_batch_d.py` and `test_panel_overlay_evidence.py` pass at
  `724a43b` (79 tests).

**Code run:** two new read-only, seeded probes. Two runs of each gave
byte-identical output.
- `probes/fixture_stats_batch5.py`: exact finite domains, fixture-vs-guard
  checks and ungated panel-context ambiguity. Its `--timing` section is not
  reproducible.
- `probes/generalisation_batch5.py`: runs certified factory programs on
  inputs the constructors cannot produce, against independent references.

### Correction before commit (independent source review)

The first draft listed `27f8ce4f`, `48f8583b`, `5b6cbef5`, `4cd1b7b2` and
`8ba14f53` as adequate unchanged candidates. That was wrong: it treated
"every fixture has one size" as if it meant "the size is rule-derived". The
orchestrator relayed this criticism. It was then checked against the source
and the new probe, not accepted on authority.

- **Self-tiling families:** `27f8ce4f`, `48f8583b`, `5b6cbef5` and
  `8e2edd66` map H x W to H² x W², the mechanism of the certified `007bbfb7`
  repair, which samples 2..5 independently.
  - The certified factories matched an independent reference on 400/400
    inputs each, over all 16 shapes in 2..5.
  - Only H², W² ≤ 30, the unique modal/minority colour and the binary mask
    are rule-derived. The 3x3 and 4x4 literals are incidental, and the priority
    is now `medium`.
- **`4cd1b7b2`:** keeping the 4x4, four-symbol Latin geometry is defensible.
  - Exactly 5..6 blanks is not: the constructor's own strip scheme reaches
    1..7 blanks, and its solver and the factory restore the square every time.
  - Density is now `incidental_restriction`, and the priority is `medium`.
- **`8ba14f53`:** the 3x3 output capacity is rule-derived, but the 4x9 canvas
  and gaps are not.
  - Padding native scenes with margins (77 canvas shapes) left the factory
    output unchanged in 400/400.
  - Box sizes are tighter than the output-capacity bound.
  - Dimensions and placement are now incidental, and the priority is `medium`.
- **Other reassessments of this kind:**
  - `8719f442` dimensions: `mixed` → `incidental` (5n ≤ 30 is the rule bound).
  - `833966f4`: width 1 is incidental. The factory swaps rows correctly on
    400/400 5 x W inputs; height 5 stays rule-tied.
  - `66e6c45b`: the certified teacher program already defines larger even
    canvases; that path was not run.
  - These two moved from `finite_domain_no_change_without_new_semantics` to
    `needs_constructor_work`.
  - Only `3979b1a8` (fixed 5x5 motif) and `8b28cd80` (spiral origin scale 4
    has no integral analogue) still need new semantics.

**Adequate unchanged candidates: none.** No batch-5 constructor is
recommended for recertification or admission without constructor work.
Batch D is listed separately below.

### Axis dispositions (count of families)

| Axis | incidental | mixed | intrinsic / rule-supported | broadly variable | unknown |
|---|---|---|---|---|---|
| dimensions | 24 | 3 | 0 | 3 | 2 |
| objects | 1 | 11 | 12 | 8 | 0 |
| placement | 1 | 3 | 17 | 11 | 0 |
| density / colours | 2 | 15 | 15 | 0 | 0 |
| rule parameters | 0 | 1 | 31 | 0 | 0 |
| demonstration context | 0 | 2 | 30 | 0 | 0 |

The three broadly variable dimensions are batch D's `195ba7dc`, `31d5ba1a` and
`34b99a2b`. `281123b4` is `mixed`: width 4..6, capped by 4W+3 ≤ 30. The two
`unknown` are `3979b1a8` and `8b28cd80`.

**Patch priority:**
- **High (4):**
  - `6d1d5c90`: no canonical input is in the native domain (see below).
  - `8719f442`: a canonical input is unreachable.
  - `2072aba6` (420 inputs) and `5ad8a7c0` (255 inputs): tiny domains with
    fixture-compatible expansions.
- **Medium (24):** every other unrepaired family.
- **Low (4):** the batch-D families. Only an optional per-scene fill
  probability is left.

**Adequacy field (new, batch 5):**
- `repaired_domain_adequate_pending_admission` (4): batch D;
- `needs_constructor_work` (26);
- `finite_domain_no_change_without_new_semantics` (2): `3979b1a8`,
  `8b28cd80`;
- `adequate_unchanged_candidate`: 0.

### Discoveries

- **Canonical inputs outside the native domain.**
  - `6d1d5c90`: line 40 keeps scenes with exactly 7 colours, but all four
    canonical inputs have 8 (all five bar colours).
    - Native draws are 7-colour in 2000/2000, and 793/2000 unfiltered scenes
      are rejected for having 8.
    - Canonical filler share is 0.11–0.19, against a native median of 0.42.
  - `8719f442`: canonical `train[2]` is a 3-pixel diagonal, which no native
    draw can produce.
    - `conway_sprite` leaves at least 4 entries, so 3 pixels need a duplicate
      pair.
    - `diagonally_connected` never marks a duplicate (`common.py` 201–213),
      so the sprite is rejected.
  - `337b420f`: canonical `train[0]` is the collision case (`extra_color`).
    Native pieces never overlap (0/500), so the 32-mechanism factory never
    sees a collision natively.
- **Ungated panel ambiguity.**
  - `3d31c5b3` has the same 4-layer priority structure as `281123b4`, but no
    evidence gate. 52/2000 native 3-demo episodes leave the query ambiguous.
  - `506d28a5`, `5d2a5c43`, `66f2d22f` and `6a11f6da` measured 0/2000 at
    their fixed sizes. Any batch-D-style expansion needs gates first.
- **Finite domains (exact):**
  - 81 (`8b28cd80`), 255 (`5ad8a7c0`), 420 (`2072aba6`) and 504 (`3979b1a8`);
  - 1533 (`6ea4a07e`), 3024 (`66e6c45b`) and 4599 (`8e2edd66`);
  - 19683 (`59341089`), 30240 (`833966f4`) and 262140 (`5b6cbef5`);
  - 182 sprite masks reached by `8719f442`, of a 233-mask bound.
- **Demonstration context.**
  - Factories that read demonstrations:
    - `337b420f`: mechanism selection;
    - `6ea4a07e`: unknown inks only;
    - `4cd1b7b2`: non-4x4 grids only.
  - Every other program reads only the query.
  - `6ea4a07e` relies on `colour_evidence`: 588/2000 independent episodes
    lack the query ink.

### Batch D (native panel expansion) status

`195ba7dc`, `281123b4`, `31d5ba1a` and `34b99a2b` are domain-adequate as
repaired.
- **Measured:** 81–361 input shapes and 2000/2000 unique inputs in 2000 draws.
- **Checkers and gates:** geometric checkers, plus occupancy and priority
  gates with a gate-aware context audit (250/250 queries).

They are **not** admitted. They are absent from `prepare.REPAIRED` and
`REVIEWED_NATIVE`, and `admission.json` still pins `verified_rules.py`
`055138a0` and `colour_evidence.py` `9547c455`. The current files are `8ad9a385`
and `2617143c`. Root must rebuild admission, register the families and run
unmodified 200/20 exports.

> **Snapshot at `724a43b`.** The paragraph above describes the batch-5
> baseline. Root commit `59d03df` has since added all four to
> `prepare.REPAIRED` ("Native batch D") and refreshed role admissions. The
> batch-5 records are unchanged; their `admission` text is a snapshot of
> `724a43b`. Production 200/20 exports were not checked by this review.

### Remaining gaps

- **Audits:** the four batch-D audits are stale.
- **Unmeasured:**
  - production same-shape support for any expansion;
  - the factory's three-box ordering (`8ba14f53`);
  - the teacher program on larger canvases (`66e6c45b`).
- **Open semantics:**
  - which collision rule `337b420f` uses;
  - whether `6d1d5c90`'s `== 7` was meant to be `== 8`;
  - whether multi-column inputs are the same task for `833966f4`;
  - how `3979b1a8` and `8b28cd80` extend.
- **Out of scope:** the nativeE families (`0c786b71`, `e0fb7511`, `f0df5ff0`,
  `f3cdc58f`) belong to another lane. `e0fb7511` (batch 3) will need a
  rereview once that lane lands. *Done: all four were rereviewed at `e64baab`
  (batch-E rereview).*

## Batch 6 semantic review (32 families, ranks 161–192)

**Scope:** 32 tier-B families, all first reviews. Every constructor sha256 is
unchanged from the ordering commit through `59d03df`, and every record binds to
`59d03df`. The 128-sample audit matches all 32, with no sample shortfall.

- **Certificates:** 31 `current` (25 `direct_factory`, 6 `direct_certificate`
  saved-teacher programs). `9110e3c5` is `unavailable`: it has only the
  uncertified `direct_programs.py` legend candidate.
- **Admission:** none of the 32 is admitted. All are absent from every
  `prepare` registry and from `admission.json` at `59d03df`.
- **Other lane:** the nativeE families (`0c786b71`, `e0fb7511`, `f0df5ff0`,
  `f3cdc58f`) are outside batch 6 and were not touched.

**What was read, for each family:**
- the whole constructor;
- every canonical train/test pair (`runtime.reference(tid)["canonical"]`);
- the audit record;
- the factory `build_program` body, or for direct certificates the saved
  teacher `transform`;
- every certificate record.

Also read, where they bear on a family:
- `colour_evidence.py` dispatch and gates (`e133d23d`, `e345f17b`,
  `e6de6e8f`, `ed74f2f2`, `b0722778`, `ba1aa698`);
- `cursor_recolour_evidence.py` (`dd2401ed`);
- `finite_input_policy.py` and its test (`ca8de6ea`, `72207abc`);
- `fixture_policy.py` and the `ba1aa698` coverage evidence;
- `parameter-validation.json` and `build_million.py` (configured sizes);
- `direct_programs.py` (`9110e3c5`).

**Code run:** a new read-only, seeded probe, `probes/fixture_stats_batch6.py`
(N = 400, seed 0). Two runs gave byte-identical output. It covers:
- exact finite domains;
- canonical fixtures checked against native guards;
- ungated truth-table ambiguity;
- certified programs, fetched through the production lookups, run on
  out-of-domain inputs against independent references (or the constructor's
  explicit-parameter path where noted).

Two limits apply to these runs:
- Program draws keep the background modal. Scenes where the motif covers most
  of the canvas failed only because the programs read the background as the
  modal colour, so they are out of scope.
- A pass is evidence of program support. It is not certification and does not
  establish intended scope.

### Axis dispositions (count of families)

| Axis | incidental | mixed | intrinsic / rule-supported | broadly variable | unknown |
|---|---|---|---|---|---|
| dimensions | 21 | 9 | 0 | 0 | 2 |
| objects | 8 | 16 | 4 | 4 | 0 |
| placement | 1 | 9 | 21 | 1 | 0 |
| density / colours | 1 | 22 | 9 | 0 | 0 |
| rule parameters | 0 | 3 | 29 | 0 | 0 |
| demonstration context | 0 | 5 | 27 | 0 | 0 |

**Dimensions:**
- The two `unknown` are `ca8de6ea` (fixed 5x5 X) and `e6de6e8f` (8x7 output
  tied to five commands).
- The nine `mixed` keep a rule-tied part:
  - squareness: `cf5fd0ad`, `ed98d772`;
  - a fixed output: `b1fc8b8e` (5x5 motif), `e3f79277` (16x16);
  - a legend layout: `ed74f2f2`, `e87109e9` (width 24 from four panels);
  - band-derived height: `b0722778`;
  - derived widths: `42f83767`;
  - an undetermined copy count: `bc4146bd` (five copies or W+1).
- The fixed sizes were not treated as intrinsic in themselves.
  - The self-tiling analogues `a59b95c0`, `c48954c1` and `d4b1c2b1`, and
    `e633a9e5`, `a8610ef7`, `bbb1b8b6`, `9b30e358`, `72207abc` and
    `8597cfd7`, were probed with 400/400 program agreement over many shapes.
  - The fixed outputs that every fixture and program share were kept:
    `e3f79277` 16x16, `b1fc8b8e` 5x5 and `ca8de6ea` 3x3.

**Patch priority:**
- **High (9).** Canonical inputs unreachable:
  - `b4a43f3b`: train[1] needs four segments, native draws three;
  - `18447a8d`: train[1] has 2 bands, native has 3..4;
  - `d017b73f`: 4 of 5 pairs unreachable (path segment counts and lengths;
    see Discoveries);
  - `42f83767`: three hollow stencils below the conway minimum of L²−L;
  - `e87109e9`: the test pair has a 21-wide block and a 13-tall block that
    touch, while native draws cap blocks at 12 x 14 and keep them apart.

  Tiny or low-orbit domains with fixture-compatible expansions:
  - `be03b35f`: 14 inputs;
  - `e3f79277`: 160;
  - `8597cfd7`: 92;
  - `72207abc`: 1152 inputs in 4 orbits, not admitted by the finite policy.
- **Medium (20).**
- **Low (3):** `d19f7514`, `e133d23d` and `e345f17b`. Their configured
  width/height path already adds sizes, and the factory matched the
  explicit-size path on 400/400.

**Adequacy:**
- `needs_constructor_work`: 30;
- `finite_domain_no_change_without_new_semantics`: 2 (`ca8de6ea`, already in
  `finite_input_policy`; `e6de6e8f`, exhaustive 80-input certificate);
- **adequate unchanged candidates: none.**

No batch-6 constructor is recommended for admission without constructor work.
The closest is `e87109e9`: rich sampling, a four-panel legend, rejection of
ambiguous beams. It still cannot produce its canonical test input.

### Discoveries

- **Canonical inputs outside the native domain (probe, section B).**
  - `d017b73f`: the segment lengths `[3,4,4]`, `[2,5,3,1]`, `[2,4,3,2]` and
    `[2,3,4]` (lines 105–108) need fewer than three middle segments or a final
    segment of 2. Train[3] is also 9 wide, against native widths of 10–16.
    - A canonical-compatible relaxation (first 2..3, 1..4 middle segments of
      3..5, a final 1..5, 2..5 pieces) gave factory agreement on 400/400.
    - A broader sampler gave 320/400. Every mismatch (scratch triage) had a
      length-1/2 later segment or a one-column piece, where the piece tip is
      undetermined, so those exclusions support the rule.
  - `42f83767`: stencil pixels `[16,17]`, `[15,15]` (L = 5) and `[24,24,24]`
    (L = 6) are below `conway_sprite`'s minimum (20/30). Sparser stencils give
    400/400 factory agreement.
  - `b4a43f3b`: segments needed per canonical map are `[2,4,2,3,3]`.
  - `18447a8d`: band counts `[3,2,4,4]`. n in {2,5,6,7} gives 400/400.
  - `e87109e9`: the train pairs satisfy every guard; test[0] fails both the
    size caps and the separation. Touching or oversized blocks (area guard
    kept) give 400/400.
- **Canonical labels outside the native rule.** These are existing semantic
  conflicts, not new defects.
  - `dd2401ed`: train[2] is generated with `extra=1`, and the native label
    would differ in 2 cells.
    - Blue counts are 1,5,2,3,3, so 'recolour iff odd' fits every fixture.
    - Native draws contradict that reading in 147/400 cases.
    - The factory and gate keep both readings and choose by demonstration.
  - `ba1aa698`: train[1]'s extra step is covered by an approved teaching copy.
    The certificate has `original_fixture_context_passed: false`.
- **Finite domains (exact):**
  - 14 (`be03b35f`), 80 (`e6de6e8f`), 92 (`8597cfd7`) and 160 (`e3f79277`;
    colour 7 is excluded);
  - 690 (`ed74f2f2`: 230 masks x 3 keys);
  - 1152 (`72207abc`), 3145 (`b1fc8b8e`), 4590 (`ed98d772`) and 15,120
    (`ca8de6ea`).
- **Distribution drift (no invalidity).**
  - `b1fc8b8e`: 108/400 native inputs are one 4-connected blob, against 6/7
    canonical.
  - `bbb1b8b6`: canonical non-exact distractors are near misses. Only 33/183
    native non-exact draws match the hole count, and none is a coherent shape.
- **Ungated panel truth tables.** Ungated native 3-demo + query episodes leave
  the query undetermined in 2/400 (`e133d23d`, 9-cell panels) and 0/400
  (`d19f7514`, `e345f17b`). Small configured sizes would need a batch-D-style
  occupancy gate; the existing gates only check that the output colour
  appears.
- **Programs already broader than their constructors.** Factories and teacher
  programs matched independent references on out-of-domain inputs:
  - 400/400: `a59b95c0`, `a8610ef7`, `bc4146bd`, `c48954c1`, `cf5fd0ad`,
    `d4b1c2b1`, `e633a9e5`, `ed98d772`, `72207abc`, `8597cfd7`, `bbb1b8b6`
    and `9b30e358`;
  - 385/385: `be03b35f`;
  - 398/398: `e3f79277`.
- **Hard-coded factories that block expansion:**
  - `e6de6e8f`: the 8x7 output and start cell;
  - `ed74f2f2`: the 5x9 windows;
  - `0607ce86`: the tile/offset/spacing search;
  - `ca8de6ea`: the nine source cells.

### Remaining gaps

- **Not probed off-domain:**
  - `e3fe1151` (larger quadrants);
  - `b4a43f3b` (maps other than 6x6);
  - `b1fc8b8e`, `0607ce86` and `b0722778`;
  - the `9110e3c5` candidate.
- **Unmeasured:** episode-level ambiguity for `bbb1b8b6` and `b0722778`, and
  gate retry rates after any proposed expansion.
- **Open semantics:**
  - the copy count under width changes (`bc4146bd`);
  - parity or data error (`dd2401ed`);
  - the train[1] step (`ba1aa698`);
  - output sizing for other command counts (`e6de6e8f`);
  - larger X motifs (`ca8de6ea`);
  - odd heights (`a8610ef7`);
  - whether 0 counts as a colour (`a59b95c0`, `d4b1c2b1`).
- **No production checks:** no prepare 200/20 export was run, and no
  certificate or audit was rerun. The `9110e3c5` `direct-candidate-audit.json`
  failure was not traced to a specific candidate version.

## Batch 22 semantic review (32 families, ranks 673–704; reviewed out of order)

**Why this batch:** it was reviewed ahead of batches 7–21. Its families already
sample shapes broadly in the audit (110–113 input shapes and 128/128 unique
inputs each). The aim was to test whether broad sampling means an adequate
domain, and to find adequate families that need no change.

**Batches 7–21 and 23 remain unreviewed.** Their 505 records are `pending`.
Nothing in this section describes them.

**Scope:**
- 32 tier-B first reviews.
- Every constructor sha256 is identical at the ordering commit `5436f3f`, at
  `59d03df` and at HEAD `4f2ec86`, and equals ARC-GEN. Every record binds to
  `59d03df`.
- **Audit:** the 128-sample audit matches all 32, with no shortfall.
- **Certificates:** all 32 are `current`, all 1000/8000/16:
  - 20 `direct_factory`;
  - 12 `direct_certificate`: 10 saved-teacher transforms, plus
    `d6542281` (reviewed joint-fragment exact cover) and `269e22fb`
    (demonstration-conditioned shared picture).
  - `e12f9a14` is certified on its teaching fixture.
- **Admission:** none of the 32 is admitted. All are absent from
  `prepare.REPAIRED`, `prepare.REVIEWED_NATIVE` and `admission.json`, and
  `family-status.csv` has `broader_source_admitted=False`.
- **Original ARC-GEN constructors:** four are inherited unchanged from upstream
  ARC-GEN: `a2d730bd`, `2b9ef948`, `1a6449f1` and `a04b2602`.

**What was read, for each family:**
- the whole constructor;
- every canonical train/test pair (`runtime.reference(tid)["canonical"]`);
- the audit and certificate records;
- the factory draft notes or certificate basis.

Also read:
- `prepare.py`: native pairs are drawn by `module.generate` and must agree
  with `runtime.verification_solver`; episodes apply a random palette and D4
  transform;
- `episode_shape_policy.py`;
- `colour_evidence.py` dispatch: only `dfadab01` has a gate, `motif_evidence`;
- `verified_rules.VERIFIERS`: only `d6542281` has an override;
- `contextual.py` and `admit.py`, for `269e22fb`;
- the `e12f9a14` label review.

**Code run:** a new read-only, seeded probe, `probes/fixture_stats_batch22.py`
(N = 200, seed 0). Two runs gave byte-identical output (sha256 `52f19e8f…`); the
`--timing` section is excluded. It has three parts:
- **A.** Canonical latent parameters are captured by wrapping `generate()`
  during `validate()`, then checked against the random path's ranges and
  grammar. The derived checks each have a native self-test, and each passes on
  every native case:
  - the `9720b24f` outline checker accepts 616/616 native containers;
  - the `446ef5d2` accent classifier recognises 600/600 native accents;
  - `28a6681f` terrain statistics, `5b692c0f` axis statistics and `247ef758`
    legend/marker statistics are also checked against native draws.
- **B.** Native draws, checked with the production verifier
  (`verification_solver`) and the certified program.
- **C.** Certified programs past literal caps, using the constructor as
  reference.

### Axis dispositions (count of families)

| Axis | incidental | mixed | intrinsic / rule-supported | broadly variable | unknown |
|---|---|---|---|---|---|
| dimensions | 1 | 1 | 0 | 30 | 0 |
| objects | 10 | 13 | 4 | 5 | 0 |
| placement | 3 | 10 | 6 | 13 | 0 |
| density / colours | 1 | 15 | 3 | 13 | 0 |
| rule parameters | 1 | 2 | 29 | 0 | 0 |
| demonstration context | 0 | 2 | 30 | 0 | 0 |

**Shape variety did not mean adequacy.** Dimensions are broadly variable in
30 of 32 families. But in 16 families at least one canonical input is
unreachable because of an object, placement or scene-grammar bound.

**Patch priority:**
- **High (16).** At least one canonical input is unreachable:
  `4b6b68e5`, `50f325b5`, `7bb29440`, `e12f9a14`, `5dbc8537`, `e4888269`,
  `1a6449f1`, `28a6681f`, `446ef5d2`, `5545f144`, `5b692c0f`, `825aa9e9`,
  `9720b24f`, `d4c90558`, `247ef758` and `a04b2602`.
- **Medium (2):**
  - `a2d730bd`: 4/200 draws raise, and 5/196 have order-dependent colliding
    structures that the archived verifier labels differently;
  - `396d80d7`: 127/200 native figures are fragmented, against single compact
    canonical figures.
- **Low (9):** `269e22fb` (pipeline only), `79369cc6` (motif literal 3x3), and
  the seven `low` candidates below (optional refinements).
- **None (5):** the five `none` candidates below.

### Adequate unchanged candidates (12)

`c6141b15`, `d6542281`, `80a900e0`, `bf32578f` and `dfadab01` (priority none),
and `2b9ef948`, `7acdf6d3`, `c9680e90`, `cb2d8a2c`, `64efde09`, `31f7f899` and
`963f59bc` (priority low, optional refinements only).

**Evidence for each:**
- **Canonical reach:** every canonical input is inside the random path, by its
  latent parameters (probe A).
- **Broad sampling:** dimensions are broadly variable. Objects, placement and
  colours are broadly variable, or mixed only because of task roles that
  episode palette/D4 permutation covers, or because of fixture-spanning ranges.
- **Agreement:** the production verifier and the certified program each agree
  on 200/200 native draws (probe B).
- **Speed:** draws take at most 8 ms (timing, not reproducible).
- **Context:** every program is query-only. Only `dfadab01` is gated, by
  `motif_evidence`.
- **Literal caps:** wherever a fixture-spanning literal cap remains (segments,
  cup sizes, ones, chains, device length, bar count, box size), the certified
  program matched the constructor past it on 200/200 (probe C). So the cap is
  not a program limit.

**Constraints before admission (root):**
1. Fresh 1000/8000/16 native recertification of the unchanged constructor
   (`recertify`), as `REVIEWED_NATIVE` requires.
   - `d6542281` must keep the `joint_fragments` verifier override pinned.
   - `dfadab01` must keep the `motif_evidence` gate pinned, and should
     report the gate retry rate.
2. Registration in `prepare.REVIEWED_NATIVE`.
3. An unmodified `prepare` 200/20 export that reports same-shape support.
   - Canonical profiles are mixed/novel, except `c6141b15` and `dfadab01`
     (mixed/seen).
   - Native draws spread over 143–174 shapes per 200.

None is release-ready.

**Not candidates, although close:**
- `79369cc6`: the motif is always 3x3, and the factory assumes it. A single
  literal value is incidental (batch-5 lesson).
- `a2d730bd`: collisions and the sampling error.
- `396d80d7`: fragmentation.
- `269e22fb`: the domain is adequate for an episode-context family, but
  `prepare` samples pairs independently and checks them with the archived
  verifier. That verifier agrees on 0/200 native pairs, while the contextual
  verifier passes 50/50 episodes. `admit.py` line 60 excludes the family, so
  episode-level sampling is needed first.

### Discoveries

- **Canonical inputs outside the native domain (probe A).**
  - **Literal caps:**
    - `4b6b68e5`: single outline, outline over 11.
    - `5dbc8537`: pieces over 6 per side or over 24 in area; 15 pieces.
    - `1a6449f1`: frames of 12.
    - `d4c90558`: thickness 4, 10x15 interior.
    - `9720b24f`: a 3x3 grid.
    - `5b692c0f`: length 10.
  - **Scene grammar:**
    - `28a6681f`, all 4 pairs: tall pillars, several staircases, 3-wide
      steps, two water pockets.
    - `825aa9e9`: skylines outside the five styles.
    - `446ef5d2`: free-form accents. Canonical pieces are straight-cut in
      22/24 cases, against 96/1732 (5.5%) native pieces.
    - `247ef758`: legend gap 5, shared legend rows, unmatched distractor
      columns, a corner mark.
    - `9720b24f`: stepped container outlines.
    - `e4888269`: no pixels, 9 shapes up to 59 cells.
  - **Guards stricter than the fixtures:**
    - `7bb29440`: diagonal-only specials in 4 of 6 pairs; 0/820 native
      rectangles.
    - `5545f144`: walk shapes touch later dots, even at unshown positions.
    - `5b692c0f`: intact rows without the cell next to the axis, or empty.
    - `a04b2602`: rectangles one row apart.
  - **Canonical conventions removed by native filters:**
    - `50f325b5` train[1]: an overlapping mirrored placement shows the
      unmirrored-first order; the repair removes it, 0/200 native.
    - `e12f9a14` train[0] and test[0]: the tie flag.
- **Verifier disagreements.** These are not counted as invalidity, because
  `prepare` would reject such pairs. They do show where the domain is
  undetermined.
  - `a2d730bd`: 5/196, from overlapping pluses of adjacent pixels.
  - `1a6449f1`: 4/200; cause not fully traced.
- **Sampling defect.** In `a2d730bd`, 4/200 draws raise `ValueError` from
  `common.sample` (lines 91–95) instead of retrying.
- **Distribution drift.** In `396d80d7`, only 73/200 native figures are one
  8-connected component.

### Remaining gaps

- **Not run:**
  - no certificate, audit or `prepare` export was rerun;
  - the candidate list is a recommendation, not an admission.
- **Not measured:**
  - the `motif_evidence` gate retry rate for `dfadab01`;
  - same-shape support under an export;
  - search cost after the proposed cap increases (`5dbc8537`, `446ef5d2`).
- **Not inspected:** only two of the verifier disagreements per family
  (`a2d730bd`, `1a6449f1`).
- **Open semantics:**
  - tie and collision conventions not shown by the fixtures (`e12f9a14`,
    `a2d730bd`, `a04b2602`, `80a900e0` crossing rays);
  - whether multi-pocket water always pours from the global top-left
    (`28a6681f`);
  - motif sizes other than 3x3 (`79369cc6`).
- **Shared worklist drift:** the main-checkout `family-worklist.json` now
  flags the nativeE families as `native_repaired` with a remeasure pending:
  `e0fb7511` (batch 3) and `f0df5ff0`, `f3cdc58f` and `0c786b71` (batch 4).
  - Their constructors in this worktree are unchanged, so their reviews
    remain current here and were not edited. Only their mechanical `worklist`
    fields were regenerated.
  - They will become stale, and need rereview, when root's nativeE
    integration lands. *Resolved: the integration landed before `e64baab`,
    and the four were rereviewed (batch-E rereview).*
- **Selector check:** in scratch, replacing `next_pending_batch` with the old
  `max(reviewed) + 1` rule failed the focused check: it gave 23 instead of 7
  for `(1..6, 22)` and 3 instead of 1 for `(2,)`. An off-by-one variant
  failed six ways. The restored selector passed. The older validator negative
  tests were not repeated, because those checks did not change.

## Not covered

- **No changes:** constructors, factories, verifiers, fixtures, labels and
  admission/prepare code are untouched by this review record, including both
  rereviews. Gates, `verified_rules.py`, `family-status.csv` and
  `admission.json` are also untouched. No certificate or audit was rerun.
- **Dispositions are judgements:** they rest on reading the source; fixtures
  are finite examples. "Intrinsic" means the cited line serves the rule.
  It does not mean the original task forbids alternatives.
- **Proposed patches are hypotheses:** each needs recertification, and where
  noted, verifier review.
- **Probes are not audits:** the `probes/` scripts are local seeded runs.
  They are smaller than the 128-sample audit and use a different time limit.
  They do not replace re-auditing after a patch.
- **Stale reviews:** if a constructor changes after review, `extract.py` marks
  that review `stale`, and the batch fails validation until it is rereviewed.
  A rereview moves the old record into `review_history.json` verbatim; it
  does not just refresh the hash.
- **Certificate dependencies:** `extract.py` binds certificates only by
  constructor and factory hash, as production lookup does. Auditor, harness,
  gate and pair-verifier hashes are reported only for the rereviewed families:
  by `probes/rereview_batch_bc.py` for the 11 B/C families, and by
  `probes/rereview_batch_e.py` plus the batch-E evidence pins for the 4 E
  families.
- **Validator change:** the batch-E rereview strengthened one history check
  in `extract.py` (replacing-commit parent and replacement hash). No check was
  removed or relaxed. Negative tests on the new entries were run in scratch:
  18 of 18 mutations failed validation, including an edited old text, a
  dropped entry, a wrong binding, baseline, first commit or replacing commit,
  an altered mechanical record, a missing `repair_delta` field or evidence
  path, a bad line reference, and `release_ready` set.

## Coverage and next batch

| Batches | Ranks | Families | Status |
|---|---|---|---|
| 1–6 | 1–192 | 192 | reviewed (current) |
| 7–21 | 193–672 | 480 | **pending, not reviewed** |
| 22 | 673–704 | 32 | reviewed (current, out of order) |
| 23 | 705–729 | 25 | **pending, not reviewed** |

The next pending batch is the first unreviewed batch in fixed order: **batch 7
(ranks 193–224)**, which is `summary.json` `next_batch`. Batch membership is
unchanged.

`817e6c09 c1990cce 98c475bf 456873bc 458e3a53 470c91de 52fd389e 5783df64
5ecac7f7 758abdf0 762cd429 7d7772cc 8fbca751 981add89 985ae207 c8b7cc0f
df9fd884 e9ac8c9e ef26cbf6 17b866bd 1e5d6875 25e02866 2601afb7 2e65ae53
42a15761 48131b3c 5751f35e 7491f3cf 963c33f8 973e499e 9968a131 9ddd00f0`

All are tier B. Check each constructor hash against the current HEAD before
reviewing.
