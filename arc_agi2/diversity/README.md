# Broader generator domains, with program-target checks

The fork retains constructors for all **1,120 public task IDs**. This change
expands the variation within a subset of those families; it does not claim
coverage of every possible rule or a new full dataset release.

The source audit compared 391 overlapping families against Michael Hodel's
[RE-ARC](https://github.com/michaelhodel/re-arc), pinned at
`e5b7f1d06362a76f9d3b8c25154ff1fafca897ce`. The other 729 families have no
matching RE-ARC constructor. The MIT source and attribution are in `rearc/`.
Only imports were adapted; plotting imports are lazy. Constructor and verifier
algorithms are unchanged.

## Native constructor repairs

| Family | Change | Program validation |
|---|---|---|
| `1e0a9b12` | Gravity: independently sampled height/width, 4–30; repeated colours across columns and empty columns | 1,000 fresh pairs, 8,000 augmented pair checks |
| `007bbfb7` | Self-tiling: 2–5 rows and columns independently; output is h²×w², within ARC limits | Same |
| `3194b014` | Largest blob: adds sheared bands and grown connected polyominoes; dimensions up to 30 | Same |
| `aaecdb9a` | Object counts: removes the explicit dense-scene small-shape restriction and retry-time simplification | Same |
| `ecb67b6d` | Diagonal classification: adds larger irregular positive and negative shapes, dimensions up to 30; removes fixed fallback | Same |
| `0934a4d8` | Reflection completion: chooses edge/interior layout before block size, eliminating the unintended 11.25% edge proposal rate | Same |
| `009d5c81` | Legend recolouring: canvas up to 30×30, larger drawings and separated strokes as well as connected blobs; no fixed fallback | Same |
| `00dbd492` | Box filling: rectangular canvases 7–30, one through six boxes where packing permits; fixed size-to-colour rule retained | Same |
| `09c534e7` | Room propagation: adds clear corridors between already-connected rooms, allowing cyclic layouts | Same |
| `45bbe264` | Crossed seed lines: independent height/width 6–30 and two through six seeds | Same |
| `3a301edc` | Nested frames: thicknesses 1–5 and independent dimensions up to 30 | Same |

Every repaired constructor reproduces the original supplied pairs; tests also
check all eight spatial transforms and a second palette on original fixtures.
Certificates are in `reports/diversity-v1/native-certificates/` and are tied to
the constructor and program source hashes. These tests are finite checks, not
a proof of unrestricted correctness or sufficient demonstration context.

Two later batches widen fourteen more native domains under the same
1,000-fresh-pair, 8,000-augmented-check and 16-fixture-variant certificate:
`137f0df0`, `31adaf00`, `84db8fc4`, `a406ac07`, `ce039d91`, `d282b262` and
`f45f5ca7` (`reports/diversity-v1/native-domain-expansion-20261024/`), and the
no-RE-ARC families `03560426`, `0becf7df`, `0f63c0b9`, `14b8e18c`, `21f83797`,
`2685904e` and `2a28add5` (`reports/diversity-v1/native-batch-b-domains.json`).
`22806e14` was deferred unchanged: its archived verifier disagrees with the
constructor on 160 of 300 fresh scenes and needs a reviewed verifier first.

Three archived verifier restrictions were exposed by these changes. The tiling
verifier allocated a fixed three-times size even though its rule needs squared
dimensions. The object-count verifier used the modal colour as background,
which fails in valid dense scenes. Reviewed replacements are in
`verified_rules.py`; the original archived code and benchmark labels remain
unchanged. The nested-frame verifier now identifies containment using bounding boxes: a thin outer frame can have fewer ink cells than its interior. A dense-scene counterexample is saved in the report directory.

## Compatible RE-ARC supplement

`probe.py` samples 128 proposals per overlapping family under bounded deadlines.
It checks the constructor label against RE-ARC's verifier and the fork's verifier,
then checks fresh three-demo/one-query episodes against the current program target.
152 families now pass the initial threshold (the 18 colour-role families use
1,152 proposals). `admit.py` additionally checks complete episodes under all eight
D4 transforms and random palette permutations; **140** passed that gate. The other
12 fail exact program checks on some augmented episodes and stay excluded.
`admission.json` lists the IDs, checks and dependency hashes.

Every sampled proposal still runs both verifiers. Every exported augmented
episode still runs its standalone program on all demonstrations and the query.
Labels are never replaced with a verifier's answer. Rejected proposals are
counted, so this filtered supplement must not be described as the full RE-ARC
distribution. A rejected broader domain remains a review blocker for the hybrid release. The presence of an existing native constructor does not resolve its diversity gap.

The existing pool builder supports the opt-in environment setting
`ARCGEN_DIVERSITY_PROFILE=rearc-compatible-v1`. It proposes the broader source
with probability 0.5 for admitted families, retaining its native mixture for
the remainder. Accepted proportions can differ because of rejection. Changed
profiles and source hashes invalidate old pool caches. Shared-context tasks and
versioned synthetic variants are excluded from this generic mixture.

## Reviewed colour roles and measured variation

Seven broader sources now use a recorded bijective colour mapping before the
shared episode palette: `00d62c1b`, `025d127b`, `10fcaaa3`, `1e0a9b12`,
`2013d3e2`, `253bf280`, and `44d8ac46`. Native programs use background zero; RE-ARC randomizes it.
The endpoint colour in `253bf280` is also aligned to native cyan while its
green fill is preserved. Geometry and input/output correspondence are unchanged.
Only these reviewed families receive alignment; ambiguous backgrounds are rejected.
Each passed 1,024 accepted pairs grouped into fresh episodes under all eight
spatial transforms: 2,048 episode checks, or 8,192 pair checks, per family.
Every exported episode is checked again with its own demonstrations and palette.

A second reviewed batch adds eighteen families to `ROLE_SPECS` in
`colour_roles.py`. For fifteen of them, the RE-ARC constructors differ from the
native programs only by colour roles. Background only: `0a938d79`, `25ff71a9`, `4347f46a`, `46f33fce`
and `7468f01a`. Background with fixed constructor markers kept in place:
`0ca9ddb6`, `1caeab9d`, `31aa019c`, `50cb2852` and `60b61512`. Background plus
one named foreground: `3aa6fb7a`, `4258a5f9`, `6d75e8bb` and `6e82a1ae`, plus
`56dc2b01`, which also has a fixed bar and marker. The mapping reads input
grids only. Every native fixture is a fixed point of its family's mapping.
`certify_roles.py` reuses the probe and admission gates and writes per-family
certificates to `reports/diversity-v1/role-certificates/`. All fifteen passed
with the same 2,048-episode budget.
Recorded alignment rejections:
- `31aa019c`: 104 of 1,152 proposals, because a red background would hide the red ring.
- `46f33fce`: 84 of 1,152, all single-colour, empty inputs.
- `3aa6fb7a`: 2 of 1,152, both modal ties.

Three more families needed reviewed program repairs as well as alignment. The
native programs assumed one object colour or one object per colour, so in
roughly 97% of aligned RE-ARC pairs they did not reproduce the label:
- `22233c11`: diagonal square pairs may now use any non-cyan colour and pair within their own colour.
- `543a7ed5`: objects of every non-background colour get rings and hole fills; the background is aligned to native cyan.
- `5c0a986e`: each square shoots its own ray.

Native inputs give unchanged results. The repaired factories were re-certified
on 1,000 fresh native pairs and 16 fixture variants. Both verifiers agree with
them on the broader domain, and all three passed the same 2,048-episode gate.
All eighteen families are in the regenerated `admission.json`.

A separate 1,000-sample measurement records actual generated variation in
`extension-domain-measurements.json`: `09c534e7` has 943 rectangular scenes and
197 scenes with added cycles; `45bbe264` has 952 rectangular scenes and all seed
counts from two through six; `3a301edc` has 903 rectangular scenes. These are
sample statistics, not guarantees about every generated episode.

The original 121-family, 200/20 export completed with 24,054 training and 2,358
validation episodes; 113 families met both quotas. That export predates these
new fixes and is an intermediate artifact, not the complete hybrid dataset.

## Reviewed program repairs without colour alignment

Twelve probe-ready families failed the augmented admission gate even though
both verifiers accepted their RE-ARC labels. Their programs made assumptions
the broader domain violates. Nine of them, plus `d13f3404`, are repaired in
`direct_factories/`; each factory header states the rule and the defect.
Each program reads its roles from the visible grid and rejects ambiguous
scenes instead of guessing.

| Family | Earlier assumption | Reviewed rule |
|---|---|---|
| `63613498` | frame = largest object (reading-order ties) | corner bracket found geometrically |
| `57aa92db` | template = best ratio (complete scaled copies tie) | ties go to the unscaled, then largest, object |
| `aabf363d` | marker = smallest component; modal background | rarer colour; border background |
| `1a07d186` | strays cleared and redrawn one at a time | clear all strays, then dock |
| `fcb5c309` | largest box | box enclosing the most dots |
| `272f95fa` | palette[0] lines skipped | unique colour with two full rows and columns |
| `8403a5d5` | background palette[0] | background = everything but the seed |
| `c8cbb738` | each piece centred, rounding down | most cells on the ring, then exact centre |
| `264363fd` | legend centre = floor of box midpoint | cell with a complete neighbourhood |
| `d13f3404` | background palette[0] | strict modal input colour |

`recertify` gave each factory a native certificate: 1,000 fresh pairs, 8,000
D4 checks and 16 fixture variants. `8403a5d5` has 80 possible native inputs,
so all of them are also enumerated (`recertify.FINITE_DOMAINS`).
`certify_programs.py` then applies the role-family budget. Each family has at
least 1,024 accepted pairs and 2,048 augmented episodes (8,192 pair checks).
Certificates are in `reports/diversity-v1/program-certificates/`. They include
`summary-subset.json`, rows for the shared summary.

The archived verifier still filters proposals, and its rejections remain
excluded. The repaired program reproduced every RE-ARC label in those rejected
cases but one, so archived-verifier defects now limit acceptance. Accepted
proposals:

- `c8cbb738`: 1,152 of 4,608
- `fcb5c309`: 1,132 of 3,456
- `63613498`: 1,177 of 3,456
- `aabf363d`: 1,269 of 2,688
- `264363fd`: 1,163 of 1,920

`0b148d64`, `1b2d62fb` and `de1cd16c` have candidate repairs that are exact on
the RE-ARC domain. Native recertification rejects them because their archived
verifiers disagree with the native constructor. Their factories are unchanged
pending reviewed verifiers; see `blocked-verifier-defects.json`.

`background-role-candidates.json` lists 17 further families whose sampled
labels pass the program once the modal background is mapped to 0. They are
not adopted. Adoption needs a per-family review of fixed colours, plus
refreshed certificates for every role family after `colour_roles.py` changes.

## Third reviewed colour-role batch

Ten of those candidates were reviewed against their RE-ARC generator and
verifier, native constructor, and saved program. They are now in `ROLE_SPECS`.
Each natively has a fixed size or square grids; RE-ARC sizes height and width
independently. Only the background moves; programs, labels and fixtures are
unchanged. Each fixed colour is an output colour that RE-ARC never samples for
background or foreground:

| Family | Fixed | Input colours | Rule |
|---|---|---|---|
| `834ec97d` | 4 | 2 | one pixel moves down under yellow stripes |
| `a5313dff` | 1 | any | enclosed background turns blue; wall colour generic |
| `a5f85a15` | 4 | 2 | every second diagonal cell turns yellow |
| `a79310a0` | 2 | 2 | shape moves down one row and turns red |
| `aba27056` | 4 | 2 | cup fills and spills yellow |
| `ae4f1146` | 1 | any | crop the card with the most blue; card colour generic |
| `cdecee7f` | none | any | pixels by column into a 3×3 snake |
| `d06dbe63` | 5 | 2 | grey staircase from every dot |
| `d5d6de2d` | 3 | any | box interiors turn green; frame colours generic |
| `fcc82909` | 3 | any | green tail, one row per box colour |

Each family got 1,152 proposals and passed with at least 1,148 accepted pairs.
Each also passed 2,048 augmented episodes (8,192 pair checks) and 16 fixture
variants; every native fixture maps to itself. Rejections, all counted:
- `834ec97d`: 3 duplicate inputs
- `a5313dff`: 3 RE-ARC verifier disagreements
- `fcc82909`: 4 modal-background ties
- The other seven: none

Certificates are in `role-certificates/`; `role-certificates/summary-subset.json`
has summary rows for all 28 certified role families. The 18 earlier role
certificates pin `colour_roles.py`, so all were rerun; only that hash and the
timing changed. The first seven role families have no per-family certificate.
Their specifications are unchanged, but admission must still be rebuilt. `f8b3ba0a` is rejected because its role is
ambiguous: in 88 of 256 sampled inputs the cell filler, not the grid-line
colour, is modal, so the native line role would move.

## Fourth reviewed colour-role batch

The six deferred candidates are now adopted under the same rules: background
alignment only, with programs, labels and fixtures unchanged. Each fixed colour
is hard-coded with the same meaning by both constructors. Most are output colours
that RE-ARC never samples for background or foreground. In `d4a91cb9`, cyan 8
and red 2 are also the input endpoints.

| Family | Fixed | Input colours | Rule |
|---|---|---|---|
| `7b6016b9` | 2, 3 | 2 | enclosed background turns red, open background green |
| `8eb1be9a` | none | any | the occupied band tiles vertically with its own height |
| `97999447` | 5 | any | each dot shoots a ray right, alternating with grey |
| `ba97ae07` | none | 3 | the hidden band is drawn on top at the crossing |
| `d4a91cb9` | 2, 4, 8 | 3 | yellow elbow from cyan along its column, then to red |
| `f35d900a` | 5 | 3 | partner-colour rings at corners; grey dots along the edges |

Each family got 1,152 proposals and passed with at least 1,149 accepted
pairs. Each also passed 2,048 augmented episodes (8,192 pair checks) and 16
fixture variants; every native fixture maps to itself. Rejections, all
counted:
- `7b6016b9`: 1 modal tie. In 2 more inputs the line colour is modal, so
  input-only inference assigns the wrong role. The archived verifier rejects
  those labels, so they are excluded.
- `d4a91cb9`: 1 duplicate input
- The other four: none

Four families from the earlier "alignment insufficient" triage list were also
reviewed and adopted. In three, RE-ARC randomizes the colour that the native
program names as grey 5. The existing named-foreground role covers this, and
their programs are unchanged:

| Family | Fixed | Foreground | Rule |
|---|---|---|---|
| `95990924` | 1, 2, 3, 4 | 5 | four corner colours around each 2×2 square |
| `b60334d2` | 1 | 5 | each dot becomes a blue plus with grey corners |
| `ce22a75a` | 1 | 5 | each dot becomes a blue 3×3 block |

`868de0fa` (fixed 2, 7) also needed a program repair. The native program
filled only blue frames, while RE-ARC draws each frame in its own colour.
The repaired factory treats every non-background colour's four-connected
components as frames. Native inputs give unchanged results. It was re-certified
on 1,000 fresh native pairs (999 distinct inputs), 8,000 D4 checks and 16 fixture
variants under the current auditor hash. Its native certificate is mirrored in
`native-certificates/`.

All four passed the same 1,152-proposal, 2,048-episode role gate. Accepted
pairs: 1,152 each for `868de0fa`, `b60334d2` and `ce22a75a`. `95990924` has
1,146 accepted pairs; its 6 rejections are single-colour inputs where RE-ARC
placed no square.

Because `colour_roles.py` changed, all earlier role certificates were rerun.
Only that hash and the timing changed. `role-certificates/summary-subset.json`
now has 38 rows. Admission is rebuilt separately.

Still not adopted:
- `941d9a10`: its grey grid lines are modal in 3 of the 4 native fixtures, so
  modal inference would move the native line role. It needs a reviewed
  corner-based role rule.
- `f8b3ba0a`: same issue (cell filler modal in 88 of 256 inputs). The line
  colour is the whole outer border, but `colour_roles.py` has no reviewed border
  rule yet.

## Readable episode preparation

`prepare.py` prepares a **supplement**, comprising the 140 admitted families and
the 26 native repairs in `prepare.REPAIRED` (164 distinct IDs; `1e0a9b12` and `feca6190` overlap).
The three program-only repairs `22233c11`, `543a7ed5` and `5c0a986e` enter through admission, not `REPAIRED`. Each row contains the program, demonstrations,
query input and expected query grid together, with a lossless PNG alongside it.
There are no Arrow or Parquet publication files. It does not upload or alter an
existing dataset, and it does not launch training.

```bash
python -m arc_agi2.diversity.prepare \
  --out /path/to/new-expanded-supplement \
  --train 200 --validation 20 --workers 16 --seconds 180
```

The quotas are requested counts, not fabricated guarantees. Input D4/palette
orbits use the existing global train/validation split before episode assembly.
Three distinct demonstration inputs are required, and the query is distinct.
The original family's uniform/mixed and seen/novel dimension pattern is retained.
Existing demonstration-evidence checks run before program verification.
Output directories are signature-bound; incompatible resumes fail explicitly.
Shortfalls, rejected pairs and checksums are recorded by family.

The initial two-train/two-validation export check produced **468 verified
episodes: 242 train and 226 validation**. All 121 families produced training rows;
113 produced both requested validation rows. Eight validation shortfalls remain
under the strict dimension/orbit policy: `0d3d703e`, `44f52bb0`, `952a094c`,
`a78176bb`, `c9e6f938`, `d631b094`, `ed36ccf7`, `feca6190`.
They need targeted context sampling, not a relaxed split or duplicate queries.
This small export is an integration check, not the 200-per-family training set.

## Remaining work

The full audit identifies more restrictions than this first repair batch fixes.
For example, `0934a4d8` still has its documented transpose-band restriction.
The attempted `f3e14006` rectangular expansion exposed a boundary/parity disagreement
with the archived verifier and was rolled back. Its failed candidate certificate
and counterexample are retained as evidence, not as an admission. Some broader
RE-ARC domains conflict with our archived verifier or saved program domain and
need family-level semantic review before adoption. Dense-scene packing can
still induce distribution bias even after its explicit small-shape shortcut
is removed. None of those issues is marked resolved here.

Reproduce the compatibility checks before changing admission:

```bash
python -m arc_agi2.diversity.probe --samples 128 --workers 12 \
  --out arc_agi2/reports/diversity-v1
python -m arc_agi2.diversity.admit --workers 8
python -m arc_agi2.diversity.recertify \
  007bbfb7 009d5c81 00dbd492 0934a4d8 09c534e7 1e0a9b12 3194b014 3a301edc 45bbe264 aaecdb9a ecb67b6d
```

Re-run admission after re-certification changes any admitted dependency.
Large sampled-pair audit files are local artifacts; the summary, admission
manifest, certificates and counterexample are checked into the repository.
