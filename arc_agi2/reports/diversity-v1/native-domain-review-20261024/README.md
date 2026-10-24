# Native-domain review inventory: 729 no-RE-ARC families (2026-10-24)

This directory is a review record only. No constructor, factory, fixture,
prepare/admission or release-readiness code was changed. `release_ready` is
`false` for every record. A source review is not enough to set it, and neither
is a smoke test.

## Files

| File | Content |
|---|---|
| `extract.py` | Reproducible extraction, merge and validation (`--check` validates without writing) |
| `inventory.jsonl` | One record per family (729), sorted by review rank |
| `semantic_reviews.json` | Hand-written semantic reviews (batch 1, 32 families), each bound to a constructor sha256 |
| `summary.json` | Counts, ID lists, all batches, validation errors (currently none) |

```bash
PYTHONPATH=. .venv/bin/python arc_agi2/reports/diversity-v1/native-domain-review-20261024/extract.py
```

Running the script twice gives byte-identical `inventory.jsonl`.

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

Mechanical extraction is not semantic review. All 697 families outside
batch 1 are `semantic_review.status = "pending"`.

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

## Not covered

- **No changes:** constructors, factories, fixtures and admission code are
  untouched. No certificate was rerun.
- **Dispositions are judgements:** they rest on reading the source; fixtures
  are finite examples. "Intrinsic" means the cited line serves the rule.
  It does not mean the original task forbids alternatives.
- **Proposed patches are hypotheses:** each needs recertification, and where
  noted, verifier review.
- **Stale reviews:** if a constructor changes after review, `extract.py` marks
  that review `stale`.

## Next batch (batch 2, ranks 33–64, tier A, audit-current)

`4c177718 4e469f39 4f537728 50c07299 522fdd07 52df9849 54db823b 575b1a71
5792cb4d 5b37cb25 639f5a19 668eec9a 689c358e 68bc2e87 692cd3b6 69889d6e
73182012 782b5218 7c8af763 7c9b52a0 7e02026e 7e2bad24 7e576d6e 7ee1c6ea
85b81ff1 8e301a54 917bccba 9356391f 94414823 95755ff2 97239e3d 981571dc`

`54db823b` is also an audit-shortfall case (1 valid draw).
