# Native-domain review inventory: 729 no-RE-ARC families (2026-10-24)

This directory is a review record only. No constructor, factory, fixture,
prepare/admission or release-readiness code was changed. `release_ready` is
`false` for every record. A source review is not enough to set it, and neither
is a smoke test.

**Progress:** 64 of 729 families have hand-written semantic reviews (batches 1
and 2). The other 665 are `pending`. Not all 729 families have been
semantically reviewed.

## Files

| File | Content |
|---|---|
| `extract.py` | Reproducible extraction, merge and validation (`--check` validates without writing) |
| `inventory.jsonl` | One record per family (729), sorted by review rank |
| `semantic_reviews.json` | Hand-written semantic reviews (batches 1–2, 64 families), each bound to a constructor sha256 |
| `probes/` | Small read-only, seeded measurement scripts cited by batch-2 reviews |
| `summary.json` | Counts, ID lists, all batches, validation errors (currently none) |

```bash
PYTHONPATH=. .venv/bin/python arc_agi2/reports/diversity-v1/native-domain-review-20261024/extract.py
```

Running the script twice gives byte-identical `inventory.jsonl` and
`summary.json`. `REVIEWED_BATCHES` in `extract.py` (currently `(1, 2)`) sets
which batches must be fully and currently reviewed. Validation fails if any
other batch has a non-`pending` record.

## Provenance

- **Baseline (worktree HEAD at extraction):** `5436f3fe035f261cdcf7996565c108148efa37fb`.
  This commit includes the seven native repairs of `1ed7790`.
- **Ordering commit (pinned):** the same sha. Batch membership uses constructor
  hashes at this commit, so later edits do not reshuffle batches.
- **Audit:** `output/generator-domain-audit-20261024`, fork `cdf50ed`,
  128 samples per sampler. 713 of 729 audit records match the current
  constructor hash. 16 are stale and must be remeasured. These are the seven
  `1ed7790` repairs, plus `aaecdb9a`, `45bbe264`, `0934a4d8`, `00dbd492`,
  `3a301edc`, `009d5c81`, `3194b014`, `09c534e7` and `ecb67b6d`.
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

Mechanical extraction is not semantic review. All 665 families outside
batches 1–2 are `semantic_review.status = "pending"`.

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

## Batch 1 semantic review (32 families)

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
- **High (11):** `03560426`, `0a1d4ef5`, `0b17323b`, `0f63c0b9`, `1478ab18`,
  `14b8e18c`, `1b8318e3`, `1c02dbbe`, `332202d5`, `342ae2ed`, `42f14c03`.
- **Medium (18).**
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
  - `14b8e18c`: 41 valid out of 43, with 2 timeouts.
  - `20fb2937` and `22806e14` used up the 16 s budget at 76 and 104 draws.

  Fix feasibility first and re-audit before judging diversity.
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
- **Latent source defects (no patch applied):**
  - `0f63c0b9`: it has a `size` parameter, but the canvas is a literal
    `grids(15, 15)` (line 38).
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
    - `0f63c0b9`: the odd-gap tie-break;
    - `1d61978c`: the majority orientation versus a fixed mapping;
    - `22806e14`: both plus outcomes;
    - `332202d5`: equal-colour band merging;
    - `305b1341`: legend z-order under flips.

  Episode-level coverage of these was not measured.

## Batch 2 semantic review (32 families, ranks 33–64)

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
- **High (8):** `4f537728`, `50c07299`, `54db823b`, `782b5218`, `7e2bad24`,
  `7e576d6e`, `917bccba`, `94414823`.
- **Medium (22).**
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
- **Latent defect.** In `782b5218`, line 52 rejects lines that leave the top
  edge but not the bottom. `probes/line_span_782b5218.py` found 136 of 3000
  native inputs (4.5%) with a column containing no red; those columns are
  cleared to 0. The factory's flood fill agreed with the native output on all
  3000.
- **Tiny or single-geometry domains.**
  - `94414823`: one geometry. The domain is 56 colour pairs × 4 orientations;
    the audit found 1 orbit.
  - `50c07299`: 56 inputs. Every segment lies on the main anti-diagonal.
    Every canonical example is also the L-th term of a corner-anchored series.
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
  part of the original rule.
- `692cd3b6`: whether the extra-bit rules for the 12 opening-direction
  combinations not in the fixtures are faithful.
- `7c9b52a0`: why 3×3 and 5×5 windows are excluded.
- Domain sizes for `4e469f39`, `917bccba` and `692cd3b6` are hand counts, not
  enumerations.
- No proposed patch has been implemented or recertified.

## Not covered

- **No changes:** constructors, factories, fixtures and admission code are
  untouched. No certificate was rerun.
- **Dispositions are judgements:** they rest on reading the source; fixtures
  are finite examples. "Intrinsic" means the cited line serves the rule.
  It does not mean the original task forbids alternatives.
- **Proposed patches are hypotheses:** each needs recertification, and where
  noted, verifier review.
- **Probes are not audits:** the `probes/` scripts are local seeded runs.
  They are smaller than the 128-sample audit and use a different time limit.
  They do not replace re-auditing after a patch.
- **Stale reviews:** if a constructor changes after review, `extract.py` marks
  that review `stale`.

## Next batch (batch 3, ranks 65–96, tier A, audit-current)

`996ec1f3 9a4bb226 9c1e755f 9caba7c3 9f27f097 9f8de559 a1aa0c1e a416fc5b
aa300dc3 aaef0977 ad38a9d0 af24b4cc afe3afe9 b2bc3ffd b7fb29bc b9630600
bb52a14b bd283c4a c35c1b4c c6e1b8da c7d4e6ad cf133acc cfb2ce5a d304284e
d47aa2ff d753a70b d94c3b52 da2b0fe3 db7260a4 dc2aa30b dc46ea44 e0fb7511`

`bb52a14b` is an audit-shortfall case. Before reading anything into its
fixed-size signal, time its draws directly, as was done for `54db823b`.
