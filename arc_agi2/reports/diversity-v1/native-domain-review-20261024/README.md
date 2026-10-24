# Native-domain review inventory: 729 no-RE-ARC families (2026-10-24)

This directory is a review record only. No constructor, factory, fixture,
prepare/admission or release-readiness code was changed. `release_ready` is
`false` for every record. A source review is not enough to set it, and neither
is a smoke test.

**Progress:** 128 of 729 families have hand-written semantic reviews (batches
1–4). The other 601 are `pending`. Not all 729 families have been
semantically reviewed.

## Files

| File | Content |
|---|---|
| `extract.py` | Reproducible extraction, merge and validation (`--check` validates without writing) |
| `inventory.jsonl` | One record per family (729), sorted by review rank |
| `semantic_reviews.json` | Hand-written semantic reviews (batches 1–4, 128 families), each bound to a constructor sha256 |
| `probes/` | Small read-only, seeded measurement scripts cited by batch-2, batch-3 and batch-4 reviews |
| `summary.json` | Counts, ID lists, all batches, validation errors (currently none) |

```bash
PYTHONPATH=. .venv/bin/python arc_agi2/reports/diversity-v1/native-domain-review-20261024/extract.py
```

Running the script twice gives byte-identical `inventory.jsonl` and
`summary.json`. `REVIEWED_BATCHES` in `extract.py` (currently `(1, 2, 3, 4)`) sets
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

Mechanical extraction is not semantic review. All 601 families outside
batches 1–4 are `semantic_review.status = "pending"`.

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
- **High (7):** `4f537728`, `50c07299`, `54db823b`, `7e2bad24`, `7e576d6e`,
  `917bccba`, `94414823`.
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

## Batch 3 semantic review (32 families, ranks 65–96)

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
    1/8, with an audit range of 0.107–0.219.
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

The 7 batch-1 families have different constructors in ARC-GEN than in this
worktree. Their reviews are `current` here, but would be stale against
ARC-GEN. They were left byte-for-byte unchanged. Re-review them once those
constructors land in this tree.

By the time of the `782b5218` correction commit, the worklist also flagged 4
batch-2 families: `50c07299`, `7e2bad24`, `7e576d6e` and `94414823`. Their
ARC-GEN constructors differ from this worktree, and their reviews are
likewise unchanged. Only their mechanical `worklist` fields were regenerated.
`782b5218` has the same constructor in both places.

## Batch 4 semantic review (32 families, ranks 97–128)

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

## Next batch (batch 5, ranks 129–160)

`195ba7dc 2072aba6 27f8ce4f 281123b4 31d5ba1a 337b420f 34b99a2b 3979b1a8
3d31c5b3 46c35fc7 48f8583b 4cd1b7b2 506d28a5 59341089 5ad8a7c0 5b6cbef5
5d2a5c43 626c0bcc 66e6c45b 66f2d22f 68b67ca3 6a11f6da 6d1d5c90 6ea4a07e
7953d61e 79cce52d 833966f4 8719f442 87ab05b8 8b28cd80 8ba14f53 8e2edd66`

All are tier B. Another lane owns implementation work for `195ba7dc`,
`281123b4`, `31d5ba1a` and `34b99a2b`; check their constructor hashes before
reviewing.
