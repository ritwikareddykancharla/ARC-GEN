# Combined program and grid dataset

**Current status (2026-10-21): 1,120 / 1,120 families admitted for program-target generation; none remain.** Expanded generation is the next stage; no dataset or training run was launched during coverage. The dated entries below are historical progress. Coverage includes explicitly labelled teaching contexts, not a claim of solving every original benchmark context.

Exports use **one episode per row**, containing a lossless PNG and a
JSON record with both the program and the output grids. Images include query
answers for human inspection; only `prompt` and `completion` are model inputs
and targets. TAR shards group PNG/JSON pairs using the same episode identifier.
Hugging Face's viewer may internally convert them to Parquet. The archive-backed
viewer is not production-ready: its hosted conversion failed in Hugging Face's
stream-file size tracking. The current public exporter test therefore uses
individual PNGs with ImageFolder metadata instead.

The target is 1,120,000 fresh base episodes, with up to eight distinct spatial
variants each (8,960,000 before symmetry deduplication). Colour mapping is shared
across every demonstration and query in an episode. Limited diversity and
unsupported size strata produce explicit shortfalls, not padding.

## Gates

1. All 1,120 families need reviewed generator coverage.
2. Each selected family needs a direct-coordinate program for augmentation.
   `direct_certificates.py` rejects stale constructor/program hashes. Factories
   in `direct_factories/` carry separate source hashes and execution evidence.
3. Every exported demonstration and query must match exactly. If any spatial
   variant fails, none of that base episode's variants are accepted.
4. Original benchmark labels are unchanged. Approved teaching corrections keep
   explicit provenance. Remaining native-label conflicts stay outside
   the admitted program set until reviewed.

Fresh native-program audits distinguish sampler failures from program failures.
They do not retry mismatching programs until an easy example passes. Five
previous sampler failures passed on the bounded recheck; all failures remain
recorded. Passing finite audits does not prove unrestricted generalization.

## Current verified evidence

- 213 native direct-coordinate certificates admitted after fresh audits and
  supplied-fixture checks.
- 901 admitted factories. Each passed 1,000 fresh pairs, 8,000 augmented pair
  checks and 16 supplied-fixture variants. Their audit records retain draft
  limitations and source/constructor hashes. These checks are finite evidence,
  not proof of correctness on every generated input.
- The native domain of `0b17323b` has only six inputs. All six were checked
  exhaustively across eight orientations and two palettes; its small domain is
  recorded explicitly rather than counted as 1,000 unique examples.
- Existing hand-reviewed direct rewrites supplement these sets; overlap means
  counts must be computed as a union, not added.
- Local exporter test: 18 fresh base episodes, 144 augmented PNG/program/grid
  records. It requested 20 bases and reported a two-episode shortfall.
- The union admits all 1120 families. A final independent execution pass checked all 17,920 declared-fixture variants (eight orientations × two palettes × 1,120 families). Constructor coverage and program coverage are
  different gates.
- Synthetic labels for `00d62c1b` now fill every enclosed background component,
  including incidental pockets. The `0bb8deee` sampler reserves room for its
  three-cell sprite. Original supplied fixtures are unchanged.

The full expanded dataset is **not complete**. The exporter test is not a
production-size corpus or a claim of full program coverage. No model training
is launched by these tools.

## Build

```bash
python -m arc_agi2.build_million --format program-grid-png
```

The CLI selects combined targets and propagates that format to spawned workers.
It checks program coverage before generating pair pools or publishing a card.
Use `--local --tasks ...` with bounded `ARCGEN_TARGET_EPISODES`,
`ARCGEN_POOL_SIZE` and `ARCGEN_VALIDATION_EPISODES` for integration checks.
The older library API and explicit `--format legacy-grid-parquet` remain for
grid-only regression tests; they are not the production program-target format.

The viewer must use one loader format. Do not mix ImageFolder PNG configurations
and WebDataset TAR configurations in one card: the loader can be inferred as
ImageFolder for both, returning zero rows for TAR files.

The 144-row direct-PNG publication is an integration test, not the full corpus.
Do not treat a successful `first-rows` response as sufficient: verify `/rows`
pagination and image retrieval too. ZIP/JSONL and TAR experiments remain archived
but are excluded from the default viewer.

The `0d87d2a6` sampler now places rectangles incrementally rather than rejecting
whole crowded layouts. Its refreshed audit passed 1,000 fresh pairs and 8,000
augmented checks in 17 seconds without sampler rejections; fixtures are unchanged.

## Resumed solver audit and synthetic sampling repairs

Constructor source coverage is still 1,120/1,120. Work here builds and validates
the separate direct-coordinate program targets. Original benchmark fixtures
remain unchanged. Each admitted target still requires per-episode verification.

- `1c56ad9f`: resample infeasible copy-count/offset combinations before selecting
  rectangle dimensions; no infinite size rejection on an impossible layout.
- `1e5d6875`: place crowded boxes incrementally, preserving shape and count rules.
- `2072aba6`: sample all nine motif cells rather than only five.
- `1190e5a7`: retain random band thicknesses, conditioned on the 30-cell ARC limit.
- `34cfa167`: vertical frame-bar bounds now use the row origin, fixing an
  accidental dependence on horizontal placement. Both constructor and solver
  were repaired; translation-invariance and original fixtures were checked.
- `1d61978c`: prevent negative-index diagonal wrapping and sample the correct
  starting-column interval. Its packed sampler passed 1,000 fresh pairs and 8,000 augmented checks in 6.3 seconds with no sampler rejections.

The finite default domains of `17cae0c1`, `25ff71a9`, `28e73c20`, `332efdb3`,
`3618c87e`, and `4522001f` were exhausted (60, 70, 16, 14, 11 and 4 inputs).
These counts are recorded as limits, not inflated by repeated random draws.
Ambiguous random-label cases and disputed fixture mechanisms stay outside
admission until reviewed. Drafting workers cannot admit or publish their own
programs. The regression suite passed 273 tests at this checkpoint.


## Visible evidence and latest verification

The exporter rejects any base episode whose D4 variants contain identical
visible demonstrations and query input but conflicting query answers. It does
not count demonstration order as a clue, and records these attempts as
`ambiguous_augmented_context_attempts`.

The random constructors for `0e206a2e`, `150deff5`, and `228f6490` now reject
ambiguous marker assignments, brick colourings, and dust/shape assignments,
respectively. They preserve explicit benchmark fixtures. Saved ambiguous
inputs are regression cases; the repaired factories each passed fresh execution
audits before admission. No arbitrary tie-break is used to choose a label.

Additional finite native domains were checked exhaustively: `50c07299` (56),
`695367ec` (36), `6f8cd79b` (49), `8403a5d5` (80), `8597cfd7` (92),
`8b28cd80` (81), and `8a371977` (61). Each received all eight orientations and
two palettes. Finite domains receive adaptive quotas rather than duplicate padding.

The public ImageFolder table has now passed `/rows` pagination across all 144
rows in config `episodes`; every row has image, program and grid fields. First
and last image URLs decoded at full resolution. This resolves the table error
for the current exporter test, not the still-unresolved scalable TAR converter.


## Additional program review and episode evidence

Program coverage is now **872/1,120** (653 factory certificates plus overlapping
native/manual targets). Subscription-only Opus 5.5 CLI workers completed 247 independent
reviews before reaching the session limit. No API fallback was used. A review does not admit a program: admission requires
host review, source-hash agreement, full fixture checks and fresh execution.

`colour_evidence.py` rejects query-required associations absent from demonstration
answers: mask/ring colours, movement colour pairs, hole-pattern legends, interior
position keys, diagonal stamp colours, chart slots and overlay precedence. It
also checks evidence for inverted-board blank outputs, crop-hole fill and
parity-conditioned cropping. These checks receive query inputs, never query
answers. They do not establish that every possible ARC hypothesis is identifiable.

Six further constructor repairs retain original fixture labels:
- `6ca952ad`: check object separation at the grid border as well as its interior.
- `7039b2d7`: separate divider rows so invisible duplicate/empty panels are not counted.
- `78e78cff`: add frame origin to right/bottom leak coordinates.
- `780d0b14`: retain panel counts while sampling dimensions within 30 cells and
  reject accidental full-background lines that look like extra dividers.
- `855e0971`: retain stratum count while sampling heights within 30 cells.
- `6ffe8f07`: bounded sequential rectangle placement retains the sampled 4–12
  object count. It passed 1,000 unique inputs and 8,000 transformed checks in
  7.22 seconds with no sampler rejections. Placement distribution changes are
  recorded; no uniform-layout claim is made.

Finite domains additionally exhausted: `995c5fa3` (64), `a9f96cdd` (15),
`a416fc5b` (16), `a85d4709` (6). Each is checked with eight orientations and two
palettes. Duplicate draws do not increase these counts.

Native ImageFolder ZIP packaging (PNG plus internal metadata.jsonl) loads all
144 test rows locally and converts on HF, but the hosted row renderer returns
HTTP 500 for its `zip://` image paths. The failed optional archive-check config
has been removed from the public viewer selector; experiment files remain.
The default individual-PNG config returned HTTP 200 with 144 rows before this
card cleanup. Expanded archive publishing still requires a working solution.

## Latest reviewed additions and repairs

48 further factories were admitted after source review and fresh checks, bringing
the union to 802/1,120. Two synthetic constructor repairs preserve fixtures:
- `69889d6e`: reject sequences that wrap to negative rows, retaining the initially
  sampled sequence length. Test both path painting and obstacle placement.
- `b2862040`: reject latent open/closed labels that disagree with visible holes,
  retaining object count. A concrete two-box/barnacle counterexample tests the
  rejection rather than relying only on random audits.

New evidence gates require a demonstrated fill mapping for each queried square
frame size (`c0f76784`) and a demonstrated crossing colour (`bcb3040b`). They read
no query answers and are tested across D4 and a nonidentity palette.

Five further finite native domains were exhausted with all orientations and two
palettes: `b7fb29bc` (49), `ba26e723` (22), `bdad9b1f` (18), `be03b35f` (14),
`c1990cce` (13). They remain subject to adaptive quotas. Full regression suite:
273 tests passed. No expanded generation or model training launched.


## Earlier continuation: 872 verified families

Seventy additional factories bring program-target coverage to **872/1,120**,
with 248 still pending. All 1,120 generator files already exist. Each training
record remains one episode with both a program and grid target.

- `c1d99e64`: reject synthetic noise that accidentally becomes an unlabelled
  full line after the intended lines are painted. Requested geometry stays fixed.
- `db7260a4`: keep the simulated water-drop position local, so validation cannot
  change the initial position used for the final example. Reproduced with seed 239.
- `c920a713`: retain the known background role even if no background pixel is
  visible; do not discard a real box colour via a majority-colour fallback.

The repaired sources each passed 1,000 fresh pairs, 8,000 augmented pair checks
and 16 supplied-fixture variants. Original fixture labels are unchanged.
The finite domain of `d4f3cd78` was also exhausted: 28 inputs, 448 checks.

Episode evidence checks now compare alternative rules on the same visible query
for mirror extension, drip direction, centre-axis selection and panel precedence.
Colour mappings, clipped arm colours, even-length anchors and output-strip axes
must be demonstrated when required by the query. These checks do not see query
answers and are not a proof against every conceivable alternative ARC rule.

[Fresh episode audit](reports/episode-evidence-continuation-audit.json): 400 base
episodes across 20 families, 392 accepted and 8 rejected for missing evidence.
All **3,136** accepted augmented program/grid records executed exactly; evidence
decisions were invariant across all eight orientations. **288 regression tests
passed.**

HF's default viewer again returned HTTP 200 with 144 preview rows; a returned
image decoded at 1188×1974 pixels. Scalable archive viewing remains unresolved.
Full expanded generation and model training have not launched.

## Earlier continuation: 890 verified families

Eighteen more reviewed factories bring direct program coverage to **890/1,120**
(671 factory certificates, with overlapping native/manual targets). All 1,120
constructors already exist; 230 program targets remain unadmitted.

New episode gates check tank fill order against all eight candidate orders on
the same query input, distinguish peak and valley tie evidence, require the
centred-line axis and NOR output colour to be demonstrated, and reject
ambiguous folded-panel output sides. These gates never consume query answers.
For `e45ef808`, the generator's leftmost valley tie convention differs from the
archived prose; a tied-valley query now requires tied-valley demonstration
evidence. Original fixtures contain no such tie and remain unchanged.

The fresh audit sampled 360 base episodes across 18 families: 356 accepted and
four rejected for insufficient demonstration evidence. All **2,848** accepted
augmented program-and-grid records executed exactly; gate decisions were
invariant across all eight orientations. Report:
`reports/episode-evidence-890-audit.json`. **291 regression tests passed.**
The finite `e179c5f4` input domain was exhaustively checked: nine native inputs,
144 checks across eight orientations and two palettes. Finite families must use
adaptive quotas rather than duplicate inputs to claim extra diversity.

The public HF exporter preview remains 144 rows. Expanded generation and model
training have not launched. Production target remains 1.12M fresh base episodes
and up to 8.96M augmented rows before deduplication and adaptive reductions,
with both program and grid in each row.

## Latest continuation: 914 verified program families

Twenty-four more factories bring coverage to **914/1,120** (695 factory
certificates with overlapping native/manual targets). All 1,120 constructors
already exist; 206 program targets remain.

New episode checks require demonstrated crossing colours, size-to-colour
associations, command shapes, and overlay precedence (including transitive
evidence). These checks consume demo answers and query inputs only. Across 480
fresh base episodes, 478 passed and two were rejected for missing evidence.
All **3,824 accepted augmented program/grid records** executed exactly and
evidence decisions stayed invariant across the eight orientations. Report:
`reports/episode-evidence-914-audit.json`.

Two constructor repairs preserve supplied fixture outputs:

- `e88171ec` now rejects incidental zero rectangles that tie or beat the intended
  rectangle, including three-cell-wide competitors. It resamples the background
  while preserving sampled scene dimensions and intended box geometry.
- `e87109e9` now terminates rays on an exit, unknown obstacle or repeated state,
  without a silent 2,000-step cutoff. Finite window-position/direction states
  guarantee termination. Its standalone certificate was revalidated on 1,000
  independent seeds, as well as its 1,000-pair/all-D4 program audit.

Both repaired constructors passed 1,000 fresh pairs, 8,000 augmented checks and
16 fixture variants. Exhaustive audits additionally checked the 80 native
command-strip inputs (`e6de6e8f`, 1,280 augmented checks) and 72 two-colour inputs
(`e9afcf9a`, 1,152 checks). These are **pair counts**, not episode counts: an
episode combines demonstrations and a distinct query. Recombination does not
create new underlying inputs; report both measures separately.

Remaining work is categorized: 65 source/context holds, 75 failed execution
audits, seven missing program factories, and 59 pending independent reviews.
A live Claude CLI retry still returned its subscription limit; no API fallback.
The public HF preview remains 144 rows. Full generation and training have not
launched. Target stays 1.12M fresh base episodes and up to 8.96M augmented rows
before deduplication/adaptive reductions, with program and grid in each row.

Final regression result for this checkpoint: **302 tests passed**.

## Boundary-repair checkpoint: 917 verified program families

Repaired three native constructors and admitted their direct program factories:

- `39e1d7f9`: cap sampled lattice spacing so logical size eight does not expand to 31×31; all six logical sizes remain supported.
- `538b439f`: support native width 18 with a valid central divider sampling interval.
- `2b9ef948`: reject path writes within the source box and its margin, preventing destruction of the evidence needed to infer the translation.

All original supplied fixtures are byte-for-byte unchanged. Each family passed
1,000 fresh-pair checks, 8,000 D4 checks and 16 fixture variants. A separate
episode check passed 60 base episodes / 480 augmented records, with no evidence
rejections or failures (`reports/episode-evidence-917-audit.json`). These are
validation samples, not the expanded training corpus.

Production remains configured for **1,000 fresh episodes per family**, three
demonstrations and one query each, with **program and grid in the same record**.
The target is 1,120,000 base episodes and up to 8,960,000 spatial variants before
symmetry deduplication. Limited valid input diversity and unsupported size strata
produce explicit shortfalls; counts are never padded with duplicate episodes.
Bulk generation and model training have not been launched at this checkpoint.

Regression validation for the boundary-repair checkpoint: **307 tests passed**.

## Sampling and missing-target checkpoint: 925 verified families

Eight additional direct factories bring coverage to **925/1,120**, with
**195 remaining** and 706 factory certificates.

- `e21a174a`: preserve the band palette across rejected-scene retries; support narrow canvas margins.
- `e74e1818`: exclude impossible band-count/height combinations before sampling; support narrow margins.
- `d749d46f`: reject box dimensions whose rotated output exceeds ARC's 30-cell extent, retaining four to six boxes.
- `e6721834`: keep combined horizontal panels within 30 columns. Independently enumerate valid marker placements and reject multiple distinct paintings. Repeated marker colours remain allowed, and equivalent assignments with the same painting remain accepted.
- `62c24649`, `a406ac07`, `bd4472b8`, `e41c6fd3`: added missing direct programs for mirrored expansion, edge-legend intersections, repeated colour bands, and anchor alignment. These four factories are host-authored; the other four began as CLI drafts.

Every family passed 1,000 fresh pairs, 8,000 D4 pair checks and 16 supplied-fixture
variants. All supplied fixtures of the four repaired constructors are unchanged.
A separate audit passed 160 base episodes / 1,280 augmented program-and-grid records
with no errors or evidence exclusions. Hash-pinned evidence is in
`reports/episode-evidence-925-audit.json`.

The production target remains 1,000 fresh episodes per family before augmentations.
Full dataset generation and training remain unlaunched while coverage is incomplete.

Regression validation for this checkpoint: **316 tests passed**.

## Visible-evidence checkpoint: 930 verified program families

Five additional factories bring coverage to **930/1,120**, with **190 remaining**
and 711 factory certificates.

- `2dd70a9a`: reject random obstacle scenes with competing successful sliding routes. The check uses an input-only state graph, backward reachability and a single terminating route. U/S geometry is retained; only obstacle noise is resampled.
- `342dd610`: reject overlapping source dots whose overwritten colour would otherwise leave an invisible output target.
- `3af2c5a8`: specialize the mirrored expansion's input corner correctly under D4. The previous implementation incorrectly assumed full D4 commutation.
- `446ef5d2`: preserve exact-cover factorization and component tie ordering across D4, in addition to the cell scan. Fresh scenes have verified unique paintings; some supplied fixtures permit multiple framed arrangements, for which the archived deterministic ordering is retained.
- `5ecac7f7`: distinguish full separator lines from separator-coloured content within a panel. The latter occurs in a supplied fixture and must remain eligible when identifying the middle strip.

Each family passed 1,000 fresh pairs / 8,000 augmented pair checks / 16 supplied
fixture variants. The complete-episode audit passed 100 base episodes / 800
augmented program-and-grid records, with zero errors. Evidence is recorded in
`reports/episode-evidence-930-audit.json`. All 322 regression tests passed.

A separate investigation of `d753a70b` found that its first demonstration uses
a one-column offset for a growing bottom-edge diamond, while random generation
uses concentric growth. A ten-cell concentric alternative was prepared locally
for investigation only. No fixture labels were changed, and the family remains
on hold pending a justified rule or approved teaching correction.

The production setting remains 1,000 fresh episodes per family before shared
rotations/reflections/colour augmentation. Bulk generation and training have not
been launched.

## Bounded-placement checkpoint: 937 verified program families

Seven more families bring coverage to **937/1,120**, with **183 remaining**
and 718 direct factory certificates.

A bounded randomized rectangle packer replaces repeated sampling of entire
crowded layouts. It keeps requested rectangle counts and sizes, returns positions
in the caller's order, preserves the original spacing convention, and fails
closed on its search budget. It never shrinks rectangles or drops objects.
Packing changes the layout sampling distribution; it does not claim uniform
sampling over all possible layouts.

- `22806e14`: place all squares, then choose a legal plus centre matching the requested alignment state. Correct the centre-versus-corner clearance check.
- `230f2e48`: incrementally validate straight and bent footprints for all one to seven segments; use full valid anchor coordinates in every direction.
- `2753e76c`: pack the distinct colour-count groups without changing counts or square-size support.
- `2c0b0aff`: pack panels and their pluses, keeping dust separate from plus components and rejecting accidental extra crosses. The program checks the exact five-cell cross rather than a loose bounding-box proxy.
- `37d3e8b2`: pack outer rectangles and internal holes; require demo evidence for each query hole-count-to-colour association.
- `48634b99`: pack all 10–15 lines using clearance rectangles that may extend one cell beyond the visible canvas; actual line pixels stay within it.
- `5e6bbc0b`: sample a valid checkerboard column/parity pair directly, avoiding an impossible fixed-parity retry when width is three.

Each family passed 1,000 fresh-pair checks, 8,000 augmented checks and 16 supplied
fixture variants, without sampler rejections. All original supplied fixtures
remain unchanged. A separate audit sampled 140 base episodes, admitted 139 and
excluded one missing a demonstrated hole-count association. All 1,112 augmented
records from the admitted episodes passed program-and-grid verification.
Hash-pinned evidence: `reports/episode-evidence-937-audit.json`.

The production target remains 1,000 fresh episodes per family, each containing
three demonstrations, one query, a program and its grid answer; augmentations
follow. Bulk generation and training are still unlaunched.

Regression validation for this checkpoint: **331 tests passed**.

## Crowded-rectangle checkpoint: 938 verified program families

`a934301b` now uses bounded rectangle packing instead of unbounded joint
position rejection. It retains six/seven objects, 2..6-cell object dimensions,
the 12..16-cell canvas range, one-cell separation and exactly three surviving
objects with fewer than two markers. Marker sampling remains Bernoulli,
conditioned on that survivor count. Exhaustion raises instead of simplifying
the scene. Layout sampling is randomized, not uniform over valid packings.
Original fixture hashes are unchanged.

The unchanged visible-coordinate solver passed 1,000 fresh unique inputs,
8,000 augmented checks and 16 fixture variants with no sampler rejections
in 8.09 seconds. Twenty complete episodes passed all 160 D4 record checks.
Evidence: `reports/episode-evidence-938-audit.json`. All **332 regression tests
passed**, including the seven-object case on a 12x12 canvas.

Coverage is 938/1,120, leaving 182 families. Bulk generation remains gated.
The requested quota remains **1,000 fresh episodes per family**, with program
and grid together, followed by augmentation; the audits above are not the
expanded training corpus.

## Bounded-scene checkpoint: 943 verified program families

Five additional direct program factories are admitted: `6bcdb01e`, `e57337a4`,
`f0f8a26d`, `ba9d41b8`, and `ad38a9d0`. Coverage is **943/1,120**, with **177
remaining** and 724 factory certificates.

- `6bcdb01e`: construct obstacle constraints for a ray with the requested 3..6
  turns, then add 20% noise in unconstrained cells. Preserve the 5..10 canvas
  range and check the result using the original simulator. Bounded exhaustion
  raises instead of reducing turn count. A feasibility claim is not made for
  every size/turn-count combination.
- `e57337a4`: clear rejected pixel lists before retrying. Previously, a draw
  above three markers accumulated indefinitely and could never be accepted.
  Preserve the 15x15-to-3x3 reduction, per-block marker probability and offsets.
- `f0f8a26d`: place every requested odd-length line while checking input edge
  clearance and rotated-output nonoverlap. Preserve size-4 lines, the original
  length range, both orientations, and at most one singleton.
- `ba9d41b8`: pack all requested checkerboard rectangles and resample an
  impossible canvas without dropping boxes. Preserve the original dimension
  ranges. The episode evidence gate now checks all four anchor-corner rules;
  demonstrations must disambiguate any different query predictions.
- `ad38a9d0`: pack exact silhouettes with four-neighbour clearance, allowing
  diagonal contact. Retain all six shapes plus 0..2 extras on the 9x9 canvas.
  Every fresh demonstration includes all six shape-to-colour associations.

These are bounded, randomized constructors, not uniform samplers over all valid
scenes. Original supplied fixtures are unchanged. Every factory passed 1,000
fresh pair draws, 8,000 D4/palette checks and 16 fixture variants without sampler
rejections. Unique input counts were respectively 991, 979, 1,000, 1,000 and
1,000; repeated draws are not counted as extra unique inputs.

Complete-episode validation accepted 100 base episodes and verified all 800
augmented records. Evidence: `reports/episode-evidence-943-audit.json`.
**340 regression tests passed**, including input-only checkerboard ambiguity,
crowded object counts, ray turn counts, and unchanged fixture hashes.

A separate investigation confirmed an eight-cell disagreement for `985ae207`:
the constructor stamps a tile when its centre reaches a thin bar even when its
frame extends beyond it, whereas the archived solver omits that last stamp.
`reports/985ae207-bar-overshoot-investigation.json` contains a legal-parameter
counterexample. It remains on semantic hold; no labels were changed.

Bulk generation has not launched. The production target remains 1,000 fresh
episodes per family, with program and grid together, then D4 augmentation.

## Marker, room and assignment checkpoint: 947 verified families

Four more program families are admitted: `6a1e5592`, `d2abd087`, `e39e9282`,
and `e681b708`. The union is **947/1,120**, leaving **173**; 728 factories have
fresh execution certificates.

- `d2abd087`: pack all requested 3..6 sprite boxes with spacing, retaining the
  original dimensions and biased 4..8-pixel connected shapes. Demonstrations
  must teach each query-required size/paint branch.
- `e39e9282`: pack all blocks and select side markers with unique destinations
  and exactly one neighbouring block. Preserve up to seven blocks and up to five
  markers per block. Demonstrations must evidence any queried absorb/dissolve
  colour role. One of 20 sampled episodes lacked that evidence and was excluded.
- `e681b708`: retain the 16..30-cell axes and partial wall layouts, but reject
  nonrectangular open rooms. A saved counterexample showed that the old
  constructor could label L-shaped rooms using a bounding rectangle that crossed
  an internal wall. Every supplied fixture and the archived explanation use
  rectangular rooms. Dot sampling now uses only eligible cells with unique
  perimeter votes and rechecks at least two dot colours after isolation filtering.
- `6a1e5592`: pack ceiling/floor spans while retaining all three/four pieces.
  A saved fresh counterexample proved pairwise footprint inequality insufficient:
  a piece could cover several bays, allowing different complete output paintings.
  An independent visible-input search now verifies unique complete placement,
  requiring all pieces. It rejects ambiguity and budget exhaustion. Every supplied
  fixture has a unique painting matching its original label.

These changes preserve supplied fixture hashes. Randomized packing and the
explicit validity/uniqueness filters change sampling distributions; no uniform
sampling or coverage of every latent combination is claimed. Each factory passed
1,000 fresh draws, 8,000 augmented checks and 16 supplied-fixture variants with
zero sampler rejections. Unique inputs: 1,000 for all except `e39e9282` (998).

Complete-episode verification accepted 79/80 base episodes and checked all 632
augmented records exactly. The exclusion was missing demonstration evidence,
not a discarded solver mismatch. Evidence:
`reports/episode-evidence-947-audit.json`. **350 regression tests passed**.

Separately, `f3b10344` remains on semantic hold: a legal 25x25 five-box scene
produces 24 differing cells between the constructor's trimmed bridge blocking
rule and the archived solver's full-width blocking rule. The counterexample is
in `reports/f3b10344-bridge-boundary-investigation.json`; no labels were changed.

Bulk generation and training have not started. Target: 1,000 fresh episodes per
family, program and grid together, followed by consistent D4 augmentation.


## Coverage checkpoint: 952 families

Five more direct program families passed source review and execution checks:
`7d18a6fb`, `97a05b5b`, `465b7d93`, `fbf15a0b`, and `4612dd53`.
There are now 733 factory certificates and 213 native certificates; with the
existing manual rewrites and overlap accounted for, the union is **952/1,120**.
The remaining 168 comprise 68 semantic/context holds, 38 execution failures,
three unresolved native-label conflicts, and 59 pending independent reviews.

- `7d18a6fb`: bounded packing retains all four to six sprites and pins the board
  at its chosen corner. Resample an infeasible canvas within the original range.
- `97a05b5b`: bounded packing retains all one to five keys, and random examples
  exercise rotations already present in canonical fixtures. An independent
  visible-input search rejects multiple distinct complete paintings or search
  exhaustion. Equivalent assignments with identical final paintings remain valid.
- `465b7d93`: correct the reversed coordinate/size pairing in frame/seed placement
  so the seed cannot overwrite the frame. Keep all original frame lengths.
- `fbf15a0b`: reserve grey instruction-marker colour when sampling pattern colour.
  Previously, patterned dots could masquerade as crop-direction markers.
- `4612dd53`: preserve frame/cut geometry and resample only erased cells until
  frame extrema remain visible and any cut retains two interior points. A saved
  single-point counterexample supports two legal, different output completions;
  the solver must not be trained on an arbitrary tie. The investigation is in
  `reports/4612dd53-single-cell-cut-investigation.json`.

Original supplied fixtures remain unchanged. Bounded placement and visibility
filters condition the random distribution; they do not claim uniform sampling
of the old domain. Each family passed 1,000 sampled pairs, 8,000 D4 checks and
16 fixture variants. The frame/seed family had 994 distinct inputs; the other
four had 1,000. These are validation draws, not completed training episodes.

Complete-episode verification passed 100 base episodes and all 800 augmented
program/grid records, with no missing-evidence exclusions or mismatches. Report:
`reports/episode-evidence-952-audit.json`. **362 regression tests passed**.

The production requirement remains **1,000 fresh episodes per family**, each
with program and grid together, then consistent rotation/reflection/colour
augmentation. Neither bulk production nor training has started.


## Coverage checkpoint: 957 families

Five further families are admitted: `36d67576`, `5792cb4d`, `ce8d95cc`,
`e7a25a18`, and `ad173014`. The union is **957/1,120**, with 738 factory
certificates. Remaining: 68 semantic/context holds, 33 failed execution audits,
three native-label conflicts, and 59 pending independent source reviews.

- Motif copying (`36d67576`): reject a motif only when a symmetry preserves the
  visible core but changes its hidden decoration. Keep all three core types,
  requested colour counts, and three/four copies. Bounded packing keeps the
  chosen transformations; equivalent full-motif symmetries are allowed.
- Path reversal (`5792cb4d`): check that a candidate destination is unvisited.
  The old check omitted that cell, permitting backtracking and overwritten
  colours which the expected output still used. Retain the original minimum
  length, stopping probability and palette.
- Grid compression (`ce8d95cc`): fix reversed row/column direction tags in the
  random sampler. Height now bounds row lines and width bounds column lines.
- Quadrant expansion (`e7a25a18`): copy the source pattern before clearing the
  output. The former NumPy view was accidentally cleared with the output slice.
- Perimeter colour rotation (`ad173014`): include the loop's row offset in both
  side scans. The missing offset could omit objects and introduce unseen colours.

Original supplied fixture hashes remain unchanged. Each family passed 1,000
fresh input pairs (all unique), 8,000 D4 checks and 16 fixture variants. The
perimeter sampler had 15 recorded per-call deadlines during the fresh audit;
these are explicit sampler failures, not ignored program mismatches. Other
four families had no sampler rejections. Complete-episode checking passed all
100 base episodes and 800 augmented records. See
`reports/episode-evidence-957-audit.json`. **370 regression tests passed**.

The production target remains 1,000 fresh episodes per family, program and grid
in the same row, with shared D4/colour augmentation afterward. These audit
counts are not production dataset counts. Bulk generation and training remain
unlaunched while coverage is incomplete.

## 979-family checkpoint

22 independently reviewed factories were admitted after host source review. The
complete-episode audit sampled 440 bases, accepted 436, and verified all 3,488
D4 records. Four `ed74f2f2` episodes lacked a demonstrated query glyph and were
excluded. Evidence gates also cover overlay precedence and emitted fill/ray
colours; they read query inputs, never query answers. All 372 regression tests
passed. See `reports/episode-evidence-979-audit.json`.

Two small default domains were exhaustively checked: `ea786f4a` has 54 distinct
inputs (864 orientation/palette checks), and `eb281b96` has 36 (576 checks).
They require explicit diversity shortfalls, not padding to 1,000 unique inputs.
All 306 independent source reviews are now complete; review completion does not
automatically admit a program. Bulk generation and model training remain unlaunched.

## 993-family checkpoint

Fourteen additional factories passed host review. Same-query rule checks now
require corridor start-side evidence and distinguish tiled-line axis and fill
colour. The colour-to-edge family `f3e62deb` requires demonstrated movement for
the query colour; its original colour-3 test remains underdetermined and is
excluded by the teaching gate, without changing its benchmark labels.

The complete-episode audit sampled 280 bases, accepted 268, excluded 12 for
missing evidence, and verified 2,144 D4 records. `f3e62deb` has exactly 64
default inputs, all checked in 1,024 D4/palette combinations. The 76 structural
settings of `f8c80d96` passed 1,216 D4/palette checks, with all preferred candidate
centres agreeing on the final painting. These checks do not expand the default
size domain. See `reports/episode-evidence-993-audit.json`.

The `f8a8fe49` sampler now retries empty content masks and empty halves before
connectivity checks. A reproduced IndexError is removed; gripper sizes and
original fixtures are preserved. The repaired sampler passed 1,000 fresh pairs
and 8,000 augmented pair checks, with 970 unique inputs and no sampler failures.

All 377 regression tests passed at this checkpoint.

## 1012-family checkpoint

Nineteen additional factories passed source review and complete-episode checks.
The audit sampled 380 base episodes, accepted 373, excluded seven whose demos
lacked required evidence, and verified 2,984 D4 records. Six new evidence tests
cover corner-shape mappings, NOR paint colour, long-plus marker colour, diagonal
repair, duplicate-part ordering and partial-X order. Query answers are never
used by those evidence gates. All 383 regression tests passed.

The mosaic repair family was also checked with all four occlusion families at
sizes 16 and 30, across eight D4 transforms and two palettes: 1,280 checks.
The original diagonal-repair benchmark query lacks that stage in its demos;
its labels are unchanged and synthetic teaching episodes require the stage.

See `reports/episode-evidence-1012-audit.json`. The remaining 108 families comprise
72 semantic/context holds, 33 execution failures and three missing factories.
Bulk production and training remain unlaunched. The target remains 1,000 fresh
base episodes per family, followed by consistent episode augmentations.

## 1016-family checkpoint

Four prior semantic holds were resolved. `f8be4b64` had a reproduced input
collision: a hidden hollow plus changed the answer without changing any input
pixel. Random generation now requires a uniquely evidenced arm for a hollow
plus, retaining valid shared arms and spurious pockets. A separate 1,000-scene
audit retained 170 overlapping-box scenes, 64 shared-arm scenes and 37 spurious
pockets; four unidentifiable placement attempts were rejected. Original fixtures
are unchanged. The ray-priority teaching gate requires demos that distinguish
vertical and horizontal precedence when the query depends on it.

`f8f52ecc` had a reproduced colour-order dependency. Each colour is now certified
after every relevant subset of other completed colours; the emitted program
uses visible colour ordering rather than an inverse-palette priority. The new
check rejects the counterexample and accepts its visible-wall repair. Forced
scenes with one through six route colours passed every permutation plus D4
controls: 1,938 checks. Both repaired samplers passed 1,000 fresh pairs, 8,000
augmented pair checks and 16 fixture variants with no sampler rejections.

`eee78d87` now requires evidence distinguishing corner occupancy from inverted
edge-midpoint readings; `f28a3cbb` requires evidence distinguishing nearest-face
clamping from diagonal sliding whenever their query predictions differ. These
checks preserve the full generator domains and never read query answers.

The complete-episode audit sampled 80 bases, accepted 77, excluded three for
missing evidence, and verified 616 augmented records. All 393 regression tests
passed. See `reports/episode-evidence-1016-audit.json` and the two saved
counterexamples. Remaining: 68 semantic/context holds, 33 execution failures,
and three missing factories. Bulk generation and training remain unlaunched.

## 1019-family checkpoint

Three prior execution failures were repaired. `f8cc533f` now searches shared
D4-symmetric templates using the union of raw surviving pixels, replacing
independent per-fragment symmetrisation and scan-order alignment guesses. The
unique minimum-addition completion must match the independently drawn latent
answer. Equal-score different outputs and search exhaustion are rejected. The
search retains the native maximum motif size of seven; it is not an unrestricted
symmetry solver. A real identical-input/two-output placement collision is saved.

`95755ff2` uses diamond geometry to identify interior cells. A wall-coloured
obstacle at the first interior cell now stops the ray, instead of being skipped
by colour-based flood filling. Wall-coloured legends still work.

`68bc2e87` combines visible overlap precedence with the generator's consecutive
outline-intersection constraint. Its unique chain replaces arbitrary colour
priority. Original-generator probes found 983 uniquely inferred correct inputs
and 17 ambiguous cases; a saved input has two constructor-accepted layer orders.
Random generation rejects ambiguous chains; original explicit fixtures remain
unchanged. All original fixture hashes for the two changed generators match.

Each program passed 1,000 fresh pairs and 8,000 augmented pair checks, with
1,000 unique inputs and no sampler rejections. The complete-episode audit
accepted all 60 bases and verified 480 D4 records. All 402 tests pass. See
`reports/episode-evidence-1019-audit.json` and the saved counterexamples.

Remaining: 68 semantic/context holds, 30 execution failures and three missing
factories. Bulk generation and model training remain unlaunched.

## 1020-family checkpoint

`6ad5bdfd` exposed a synthetic-label defect: hidden domino drawing order
allowed a far piece to pass through an undrawn nearer piece, which could later
overwrite it. The saved counterexample has identical input but two outputs,
including one with a lost cell. Random sampling now sorts the accepted dominoes
nearest-wall first, preserving the sampled scene and giving physical stacking.
Explicit calls and original fixtures are unchanged. Placement retries are bounded.

The direct visible-coordinate program passed 1,000 fresh pairs, 8,000 augmented
checks and 16 fixture variants; all 1,000 inputs were unique. Three bounded
sampler rejections were recorded rather than padded with duplicate examples.
All 20 complete episodes passed (160 D4 records), and all 406 regression tests
passed. See the hidden-order
counterexample and `reports/episode-evidence-1020-audit.json`.

Remaining: 68 semantic/context holds, 29 execution failures and three missing
factories. Bulk generation and model training remain unlaunched.

## 1024-family checkpoint

Four more execution failures were repaired and admitted. `8698868d` now
recognizes isolated pixels inside the panel block as panel material rather than
extra loose shapes. The generator is unchanged.

`7b6016b9` had synthetic scenes where line extensions enclosed a pocket outside
the declared rectangles, but latent box-based labels still called it open.
Random generation now requires labels to agree with visible border connectivity;
inconsistent scenes are rejected, not relabelled. Explicit fixtures are unchanged.

`83b6b474` had ambiguous ring assemblies despite its heuristic legality check.
The random sampler now exhaustively counts translation-only tilings and requires
exactly one. The emitted program also rejects ambiguity instead of choosing a
reading-order solution. Original fixture assemblies are unique and unchanged.

`97239e3d` now restores the lattice underneath input markers before painting
rectangles. Random sampling excludes shared-centre rectangles whose labels
depended on hidden native-colour iteration order. Explicit fixture calls remain
unchanged. All sampling loops modified here have finite rejection bounds.

Each family passed 1,000 fresh pairs, 8,000 D4/palette checks and 16 fixture
variants, with no sampler failures. The first three had 1,000 distinct inputs;
`97239e3d` had 975. These are verification pairs, not production episode counts.
The complete-episode check accepted 80 bases and verified all 640 D4 records.
Counterexamples, source hashes and episode results are saved in `reports/`.

Remaining: 68 semantic/context holds, 25 execution failures and three missing
factories. Bulk generation and training remain unlaunched.

All 415 regression tests passed at the 1024-family checkpoint.

## 1027-family checkpoint

`652646ff` uses complete scene explanations to distinguish partial rings from
noise and recover the visible occlusion chain. Unlike the proposed draft
restriction, it does not require eight visible cells on the top ring. A stress
probe produced 5,076 legal scenes with 1–7 visible top-ring cells: 2,932 had
unique output orders and 2,144 were ambiguous. The latent true order was among
the feasible explanations in every case. All 23,456 D4/palette checks of the
unique cases passed. Random sampling rejects nonunique output orders, preserving
identifiable weak rings and the independently drawn latent outputs. Explicit
fixtures are unchanged. Multiple placements with the same output order remain
allowed. The scope remains the native ring template and noise model.

`6cbe9eb8` now recognizes a frame fragmented into four pieces and propagates
texture exclusions. The suggested solid-inside-solid constructor change was
rejected: the original generator already forbids overwriting a solid interior.
Its generator is unchanged.

`ce602527` now requires a unique output source for a scale-two clipped clue.
The generator rejects ambiguous sprite identities; the program does not use
palette-priority ties or unsupported scale fallbacks. The random sampler's
misplaced hidden-cell check was corrected and retries bounded. Explicit
fixtures remain unchanged.

All three passed 1,000 fresh pairs and 8,000 augmented checks each, with 1,000
unique inputs per family. Frame generation hit nine five-second deadlines
during that audit. Complete-episode validation accepted 59 bases and checked
472 D4 records; one further frame episode hit its sampling deadline. These
failed sampling attempts are recorded, not padded with duplicates.

The 30-task Opus CLI repair batch has finished: 27 repair drafts and three
diagnoses. Host review continues. Two drafts were moved to semantic/fixture
holds rather than admitted through demo memorization or hidden-latent rules.
Remaining: 70 semantic/context holds, 20 execution failures and three missing
factories. No bulk generation or model training has launched.

All 422 regression tests passed at the 1027-family checkpoint.

## 1031-family checkpoint

Four more families have direct programs with complete fresh-pair evidence.

- `5b37cb25`: notch templates work even when small boxes have disconnected
  corner fragments. Differently coloured overlapping plus stamps are rejected
  in random sampling and by the solver, instead of following hidden draw order.
  A saved identical-input/two-output witness demonstrates the ambiguity.
  Equal-colour overlaps remain allowed; explicit historical calls are unchanged.
- `8a004b2b`: scaled-template placements are enumerated and must yield one
  output. The draft's margin-one assumption failed the approved query, whose
  sprite touches the bottom edge. The repaired search permits edge contact
  while retaining the four corner markers. No scale-one or scan-order fallback.
- `b7256dcd`: different-colour markers seeding the same shape cell no longer
  silently overwrite one another in random generation. The program rejects
  conflicting component colours; same-colour markers remain valid. Explicit
  historical calls and fixture labels are unchanged.
- `e40b9e2f`: generated latent pinwheels are accepted only if they are the
  unique minimum-addition quarter-turn completion. The program enumerates
  integer/half-cell centres and rejects output ties, without distance or
  reading-order tie breaks. The saved failure has an eleven-cell completion
  whereas its latent label adds twelve.

All four passed 1,000 fresh pairs, 8,000 augmented pair checks and 16 fixture
variants each. Distinct-input counts were 1,000, 1,000, 999 and 997 respectively.
All 80 complete episodes passed, giving 640 D4 records. All 429 regression tests
passed. Source hashes and counterexamples are saved with the audit report.

Remaining: 70 semantic/context holds, 16 execution failures and three missing
factories. A separate subscription-CLI batch is drafting repairs for the 68
older semantic holds, using their explicit host-review concerns. Those drafts
are not automatically applied or admitted. No bulk generation or training has
launched.

## 1032-family checkpoint

`8731374e` now searches all colour components for solid-border rectangles with
single-colour interior dots in distinct rows and columns. It returns a unique
maximum-area output, rejecting ties instead of using enumeration order. A
larger plain noise component does not distract it. The old majority-edge crop
failed when adjacent noise occupied exactly half an edge.

Noise can also extend an entire box edge, yielding the same input with different
latent crop labels. A regression constructs that ambiguity explicitly. Random
sampling accepts only labels matching the unique largest visible dotted box;
explicit calls and original fixture labels remain unchanged. This largest-box
convention is a documented restriction, not an assertion that latent crops can
always be recovered from arbitrary noise.

The repair passed 1,000 distinct fresh inputs, 8,000 augmented pair checks,
16 fixture variants and 20 complete episodes (160 D4 records). The saved failure,
large-component decoy, ambiguous crop widths, tied outputs and fixture hashes
have regression coverage. Remaining: 70 semantic/context holds, 15 execution
failures and three missing factories. Bulk generation has not launched.

All 434 regression tests passed for this checkpoint.

## 1034-family checkpoint

- `b9630600`: infer pipe connections using the unique minimum spanning tree
  of visible, line-clear candidates. Equal lengths remain allowed when they
  do not create competing trees. A saved witness changes only hidden rectangle
  order and produces different labels for the same input; random generation
  and emitted programs reject those ambiguous cases. Corrected swapped initial
  rectangle bounds. The CLI draft's whole-gap-empty restriction was removed: a
  pipe can enclose another box when its two drawn lines are clear.
- `896d5239`: replace distance clustering with an exact cover of cone markers.
  Missing arm cells can leave a valid marker three cells from its neighbours,
  so distance alone cannot identify the objects. Search compares completed
  output grids, allowing multiple latent covers if their outputs agree. It
  raises on search exhaustion or conflicting outputs rather than returning
  the first cover or unchanged input. Corrected swapped apex row/column bounds;
  clipped cones remain supported.

Both passed 1,000 distinct fresh inputs, 8,000 augmented pair checks and
16 fixture variants each. All 40 complete episodes passed, producing 320 D4
records without sampler rejections. Original fixture hashes are unchanged.
Remaining: 70 semantic/context holds, 13 execution failures and three missing
factories. Parallel CLI drafts still need host review and execution checks.
Bulk generation and model training have not launched.

All 442 regression tests passed for this checkpoint.

## 1037-family checkpoint

- `50846271`: exact covers allow hidden centres and clipped arms, comparing
  outputs across all shared arm lengths. The program no longer prefers the
  shortest arms or first centre. Solutions are deduplicated by completed cells
  before stopping the search. Random generation paints each centre once, fixing
  the accidental second paint that forced it grey. A saved identical-input
  witness demonstrates ambiguous length-two versus length-three crosses.
- `8dab14c2`: reconstruct the clean L and evaluate all valid defect patterns,
  including adjacent bumps and notches. Reject conflicting destination writes
  and distinct-output explanations; remove local-neighbour and colour-frequency
  fallbacks. Three different completions of one sampled input are saved as an
  ambiguity witness. Native margin-two and thickness-three-to-six scope remains
  explicit.
- `90f3ed37`: compare all supported motif parses rather than voting by parse
  count. A native reference boundary is at most four columns from the anchor
  (pre-sampling A width1..2 times1..2). The draft's unrestricted boundary admitted
  a false split at column8 of the original zigzag fixture; correcting that
  hypothesis space preserved all fixture labels. A saved pair of valid latent
  phases demonstrates identical inputs with different continuation outputs.

Each family passed 1,000 fresh pairs, 8,000 augmented pair checks and 16 fixture
variants. Distinct input counts were 1,000, 1,000 and 990, respectively. All 60
complete episodes passed, producing 480 D4 records without sampler rejections.
Remaining: 70 semantic/context holds, 10 execution failures and 3 missing factories.
Bulk generation and model training have not launched.

All 453 regression tests passed for this checkpoint.

## 1039-family checkpoint

- `52df9849`: preserve covered staircase shapes through explicit shape and
  layer inference, rather than accepting the draft's blanket rejection of them.
  Candidate masks include rectangles, diagonals and inward-shaved strips with
  visible endpoints. Enumerate both layer roles and require one completed
  output. Original test2 requires actual pixel separation: its same-layer
  diagonal and rectangle have overlapping bounding boxes. Saved regressions
  include a recoverable covered staircase and a truly ambiguous hidden corner.
  Random placement now enumerates legal positions after each proposed size,
  avoiding simultaneous-packing failures for three objects per layer. Counts
  remain independently 1..3 and sizes 1..16; the proposal distribution changes
  toward packable scenes, with explicit fixtures unchanged.
- `1190bc91`: cast rays from the head of the coloured sequence, then flood
  connected background regions from their actual adjacent markers. Reject
  conflicting marker colours in one region. Random placement requires each
  marker to seed the region its label fills; old explicit calls remain
  unchanged. Exhaustive canonical-geometry analysis examined 1,540 trials,
  with 885 legacy-valid scenes: all 870 marker-consistent scenes were exact,
  while 15 disconnected-marker cases differed and are excluded from random
  generation. Geometry sampling uses exact enumeration with the original 1:9
  absent/present side-marker weighting.

Both passed 1,000 fresh pairs, 8,000 augmented pair checks and 16 fixture variants.
Distinct-input counts were 1,000 and 997. All 40 complete episodes passed, yielding
320 D4 records with no sampler rejections. Original fixture hashes are unchanged.
Remaining: 69 semantic/context holds, 9 execution failures and 3 missing factories.
Bulk generation and model training have not launched.

All 461 regression tests passed for this checkpoint.

## 1043-family checkpoint

Four episode-evidence holds are resolved without changing the native generators
or the previously verified direct-coordinate programs:

- `b0c4d837`: compare snake and raster traversal in all eight orientations.
  Retain hypotheses fitting demonstration outputs and require agreement on each
  query input. A three-cell line does not teach the fourth-cell turn; a lone
  corner does not teach the line direction. Shorter queries remain admissible
  when surviving hypotheses agree.
- `e133d23d`: retain blank panel pairs. A nonempty query union requires a
  demonstration showing its output paint; an empty query does not.
- `b27ca6d3`: retain identity scenes without dominoes. A query needing an outline
  requires a demonstrated outline-colour change at an actual domino ring cell.
- `d94c3b52`: the native sampler already guarantees between-tile fills. The
  episode gate independently checks matching tile masks and between positions
  before requiring demonstrated fill colour, including externally supplied
  episodes outside that stricter sampler domain.

No query answers enter these gates. All four existing certificates were checked
against current source hashes: each records 1,000 fresh pairs, 8,000 D4 pair
checks and 16 fixture variants. New complete-episode auditing accepted 77 of
80 bases, rejected three cup episodes with insufficient traversal evidence,
and verified all 616 augmented records. Constructors, original fixtures and
single-pair distributions are unchanged. Remaining: 65 semantic/context holds,
9 execution failures, 3 missing factories. Bulk generation and model training
have not launched.

## 1046-family checkpoint

- `ae3edfdc`: require a demonstrated satellite-to-centre association for each
  satellite colour used by a query. Keep zero-petal flowers in the native
  generator; do not force both associations into every single pair.
- `e509e548`: require demonstration evidence for each query L/U/H category's
  output colour. Topology is measured from connected objects, branch degree
  and corners. Keep the independent shape-type draws, including scenes missing
  one or two categories. Replace simultaneous random-box rejection with bounded
  randomized backtracking (256 size draws, 1,024 search nodes each). Height
  10..20, width height+-2, box count 1+max(height,width)//3, box sizes 3..5 and
  one-cell spacing remain. Position probabilities change; there is no lattice
  or small-size fallback. The four previously timed-out audit seeds now produce
  placements, and the full fresh audit records zero sampler timeouts (previously
  four). The original fixture hash is unchanged.
- `e5790162`: preserve two-segment paths. Compare all four independent
  clockwise/counterclockwise assignments for the two obstacle colours, retain
  those fitting every demonstration, then require agreement on each query.
  Infer initial heading from the visible noncorner border start. Reject cyclic
  alternative hypotheses using visited states. Do not assume that seeing one
  colour teaches the other by elimination.

The gates consume demonstration outputs and query inputs only. All three have
hash-matched certificates for 1,000 fresh pairs, 8,000 D4 checks and 16 fixture
variants; `e509e548` was re-audited after its packing change. The 60 new complete
episodes all passed, yielding 480 augmented records without sampler rejections.
Remaining: 62 semantic/context holds, 9 execution failures, 3 missing factories.
Bulk generation and training have not launched.

All 475 regression tests passed for this checkpoint.

## 1049-family checkpoint

- `ac605cbb`: compute seed stamps, copies and crossings from the query input.
  Require each query seed's association and crossing paint to be demonstrated.
  Compare four diagonal directions plus crossing-only against demonstration
  outputs and require agreement on the same query. An explicit clipped-border
  regression shows why a crossing colour alone need not reveal ray direction.
- `dc2e9a9d`: parse each connected frame's nub side and project its reflected
  copy. Require colour evidence at copied cells for every query-needed visible
  axis. Preserve one-object grids and single-axis demonstrations; odd D4
  rotations swap the colour roles consistently.
- `db93a21d`: preserve beamless/clipped scenes. Compare down/left/up/right beam
  hypotheses on demonstrations and require same-query agreement. Also require
  demonstrated beam colour when a query needs a beam. An all-clipped query is
  allowed when the surviving hypotheses agree.

No constructor or direct-factory source changed. All three current certificate
hashes were rechecked (1,000 fresh pairs, 8,000 augmented checks and 16 fixture
variants each). New complete-episode checks accepted 57 of 60 bases and excluded
three lacking evidence, verifying 456 augmented records with no execution errors
or sampler rejections. All 481 regression tests passed. Remaining: 59 semantic/
context holds, 9 execution failures and 3 missing factories. Bulk generation and
training have not launched.

## 1051-family checkpoint

- `dfadab01`: learn actual coloured and blank motif cells from demonstrated
  outputs and visible legends, without consulting the fixed motif lookup table
  or query answers. Evaluate all four anchor corners; remove hypotheses with
  conflicting observations, unexplained output paint, or incompatible legend
  keys. Every surviving hypothesis must know all query-visible cells and predict
  the same query output. A clipped query can pass with only partial motif
  evidence, even when all exposed cells are blank. Full queries cannot borrow
  unseen pattern cells or output colours from the factory constants. Retain
  visible query legends, the ring-corner ordinary marker and irregular layouts.
- `e3721c99`: require demonstrated erasure when a query has a grey blob whose
  hole count matches no interior key. Identify border-touching dividers
  structurally, including L dividers. Preserve zero-distractor scenes and queries
  that need no erasure; no changes to object counts or size feasibility.

Original constructors and direct factories are unchanged. Their current hashes
match certificates containing 1,000 fresh pairs, 8,000 D4 pair checks and 16
fixture variants per family. New complete-episode auditing accepted 38 of 40
bases and excluded two missing-evidence cases, verifying all 304 augmented
records with no sampler rejections or execution errors. Remaining: 57 semantic/
context holds, 9 execution failures and 3 missing factories. Bulk generation
and model training have not launched.

All 489 regression tests passed for this checkpoint.

## 1054-family checkpoint

- `d56f2372`: retain doubly symmetric scenes. Compare unique-colour-crop
  selection on both reflection axes, fitting demonstration outputs. Discard
  hypotheses with no unique selection on a query; require the remaining
  predictions to agree. No largest-shape or palette-order tie-break is used
  to establish episode evidence.
- `caa06a1f`: infer the frame and visible tile periods, then compare four
  unit shifts on demonstration outputs and the same query. The original
  canonical episode is genuinely ambiguous under these hypotheses: all three
  demos are checkerboards, while the three-colour test has three distinct
  possible predictions. Its immutable fixture labels are preserved, and the
  ambiguity is recorded in `caa06a1f-canonical-shift-ambiguity.json`; there is no
  training-export exemption. Fresh episodes with distinguishing three-colour
  demonstration evidence pass. Both two- and three-colour scenes remain in
  the generator, with the original size coupling.
- `cad67732`: extract diagonal and off-diagonal periods independently of the
  direct factory. Compare all four combinations of main/anti-axis end-anchor
  phases. An example on one axis cannot fix the other axis's phase. Queries
  whose two anchor predictions agree need no distinguishing example. Native
  synthetic anti-diagonal labels use top-right anchoring; archived opposite-end
  anchoring differs at nonmultiple sizes. The original fixtures do not expose
  that difference. A concrete witness is saved in `cad67732-anchor-phase-witness.json`.

No constructor, program-factory source or fixture labels changed. Existing
certificates match current hashes and each records 1,000 fresh pairs, 8,000 D4
checks and 16 fixture variants. New complete-episode auditing accepted 56 of 60
bases, excluded four missing-evidence cases and verified 448 augmented records.
Remaining: 54 semantic/context holds, 9 execution failures, 3 missing factories.
Bulk generation and model training have not launched.

All 495 regression tests passed for this checkpoint.

## 1056-family checkpoint

- `c87289bb`: independently simulate both nearest-edge detour tie conventions
  in visible coordinates. Fit them to all demonstrations and compare surviving
  predictions on each query input. Untied queries need no symmetric-detour
  demonstration; hard tied queries remain supported with teaching evidence.
- `cc9053aa`: independently build a shortest-path DAG from the visible lattice
  and compute minimum/maximum turn counts, including endpoint legs. A query
  whose shortest paths differ in turns needs a demonstration showing that
  choice. Equal minimum-cost routes are rejected rather than resolved by
  search order. The original three demos have unique shortest routes, whereas
  the original test has 20-step routes with two and six turns. This limited
  tie-break ambiguity is documented in `cc9053aa-canonical-turn-evidence.json`;
  original labels remain unchanged, with no training-export exemption. A
  synthetic distinguishing demonstration restores admission of the hard query.

No constructor or program-factory source changed. Existing certificates were
reused after matching both source hashes: each covers 1,000 fresh pairs, 8,000
D4 pair checks and 16 fixture variants. New complete-episode auditing accepted
38 of 40 bases, excluded two missing-evidence assemblies, and verified 304
augmented records with no sampler rejections or execution errors. Gates never
read query labels. The independent path search also matched 100 freshly sampled
native shortest-route solutions in regression tests.

All 501 regression tests passed. Remaining: 52 semantic/context holds,
9 execution failures and 3 missing factories. Bulk generation and model
training have not launched; production remains 1,000 fresh bases per family
plus consistent D4 augmentation, with program and grid together.

## 1058-family checkpoint

- `8e5c0c38`: preserve default tied-axis sampling (20%), split groups and
  horizontal-symmetry distractors. Independently compare sixteen hypotheses:
  row-only, column-only, or best of both with either orientation priority,
  each with independent low/high axis ties. Demonstrations filter hypotheses;
  survivors must agree on the same query. The canonical first query has four
  cells whose labels depend on a tie convention absent from its demos. The
  second query is unambiguous under these candidates. Save this evidence in
  `8e5c0c38-canonical-axis-tie-evidence.json`, preserve the original labels,
  and require a distinguishing synthetic demonstration before exporting a
  tied query. No default tie-free narrowing was applied.
- `a32d8b75`: preserve soft tiles, up arrows, rectangular tiles and multiple
  legends. Independently parse the visible legend sections, corner, arrow,
  tile and shape. Compare 32 tile hypotheses: colour swap/no swap, eight fixed
  tile D4 transforms, and following/not following the arrow rotation. Fit
  demonstration answers; query geometry can eliminate hypotheses whose full
  stamp boxes do not fit or overlap. No clipping is used. Remaining predictions
  must agree. Tests demonstrate soft-only and up-arrow-only ambiguity, recovery
  with teaching examples, and all-D4 equivalence of complete hypothesis sets.

Neither constructor nor direct program source changed. Their current hashes
match the existing 1,000-pair, 8,000-D4-check, 16-fixture-variant certificates.
New auditing accepted 38 of 40 complete base episodes, excluded two missing-
evidence symmetry assemblies and verified 304 augmented records, with no
sampler rejections or execution errors. All 507 regression tests passed.

Remaining: 50 semantic/context holds, 9 execution failures and 3 missing
factories. Bulk generation and training remain pending complete coverage.

## 1060-family checkpoint

- `9385bd28`: retain deeply nested reservations, including reserve rows with
  no remaining free cell. Independently parse visible legend rows and key
  rectangles; compare 48 hypotheses spanning early/inline/no erasure,
  ordinary filling, reservation, ignored rows, and legend/reverse/area order.
  Require surviving predictions to agree on each query. The canonical first
  query exposes an area-order ambiguity not excluded by its original demos.
  The original labels remain unchanged, without a training-export exemption.
  `9385bd28-erase-reserve-order-evidence.json` records this and a concrete nested
  reserve witness. Adding that witness as a demonstration distinguishes the
  native rule and recovers the hard query. No blanket nested-case rejection.
- `bd283c4a`: retain equal-count scatter cases. Compare eight fill paths and
  eight first-appearance tie scans, fitting demonstration outputs. Tied queries
  need evidence when their predictions differ; untied queries need no tie
  demonstration. Uniform demos cannot silently teach a fill direction. This
  is a finite comparison of spatial conventions, not all arbitrary colour
  priority rules. No tie-free generator narrowing was applied.

Original constructor and direct-factory sources are unchanged and their hashes
match existing 1,000-pair, 8,000-D4-check, 16-fixture certificates. New complete-
episode auditing accepted 32 of 40 independent base assemblies, excluded eight
paint-order assemblies missing teaching evidence and verified 256 augmented
records, without sampler rejections or execution errors.

The production assembler now fixes each query before retrying demonstration
selection, rather than silently switching to an easier query on rejection.
It tries up to 50 contexts and records an explicit `query_context_shortfalls`
entry on failure. Shared-picture contexts are indivisible and receive one
attempt. Existing reuse limits remain. A local audit with 64 fresh 20x20
paint-family pairs completed all 20 requested bases, resolved 11 evidence
retries and verified all 160 augmented program/grid records. Its report is
`query-preserving-assembly-1060-audit.json`; those are audit records, not a
production dataset launch.

All 518 regression tests passed. Remaining: 48 semantic/context holds,
9 execution failures, 3 missing factories. Bulk generation and training
have not launched.

## 1062-family checkpoint

- `7447852a`: keep every native width, including odd strips whose input has
  a mirror or half-turn symmetry but whose pocket colouring does not. Render
  all eight visible frames, fit demo input/output pairs and query input pixels,
  and require agreement among survivors. No D4 prior is used to admit ambiguous
  contexts. Tests cover all 441 native single-demo/query width combinations
  and both ambiguity classes under all D4 transforms. Default generation has
  only 21 distinct inputs (height 3, widths 5–25), so it needs an adaptive
  diversity quota, not duplicate padding. A new finite-domain audit executed
  the program with all 21 cases under eight D4 transforms and two palettes:
  336 checks. See `7447852a-finite-phase-audit.json`.
- `b0722778`: preserve odd-cell analogy bands and recolouring bands.
  Independently parse visible A/B/C blocks, enumerate fitting D4 operations
  and compare all 40,320 operation priorities for each of two stages: pure
  geometry, then geometry plus a colour map. Demonstrations constrain priority
  orders; surviving query predictions must agree. This covers mirror/rotation
  ties and the secondary identity/recolouring ambiguity. It retains the stated
  geometry-before-recolouring structure, rather than claiming identifiability
  against all possible rules. Tests show recovery with relevant demos and
  rejection of inconsistent priorities or changed separator cells.

Constructor and direct-factory sources remain unchanged. Their previous
1,000-sampled-pair/8,000-D4/16-fixture audits match current hashes; the zigzag
audit repeats its finite 21-input domain, not 1,000 distinct inputs. New
complete-episode auditing accepted 30 of 40 independent bases, excluded ten
analogy contexts missing evidence and verified 240 augmented program/grid
records, with no sampler rejections or execution errors. The production
assembler retries demonstrations while retaining the selected query.

All 525 regression tests passed. Remaining: 46 semantic/context holds,
9 execution failures and 3 missing factories. Bulk generation and model
training have not launched.

## 1063-family checkpoint

- `d8e07eb2`: preserve variable catalogue sizes, narrow glyphs, partial row or
  column selections and near misses. An independent decoder reads the visible
  divider bands and fixed slots; it does not reuse the solver's tight-box
  snapping. Compare nine combinations of disabled/full/partial line rules on
  both axes. Demonstrations independently teach frame, success-query,
  success-result and failure-result paint roles. Surviving predictions must
  agree on the query and match the program target. Query answers are never
  passed to this gate. Original full-line demonstrations do not alone teach
  partial-line success; adding a suitable partial-line demo resolves that
  ambiguity without removing the hard query from the generator.

Constructor and direct program remain unchanged. Their hashes match the prior
1,000-fresh-pair/8,000-augmented-check/16-fixture-variant execution certificate;
that certificate was reused, not rerun. New complete-episode auditing accepted
13 of 20 independent contexts and verified 104 augmented program/grid records.
The seven contexts lacking evidence were excluded, with no execution errors.

A separate production-assembler audit used 256 fresh pairs and completed all
83 requested base episodes, retaining each selected query through 70 evidence
retries. It kept 17 partial-line successes, 21 full-line successes and 45
failures, with zero query-context shortfalls. All 664 augmented rows passed
combined program/grid verification. See
`reports/query-preserving-assembly-1063-audit.json`.

All 530 regression tests passed. Remaining: 45 semantic/context holds,
9 execution failures and 3 missing factories. These are local audit records;
bulk generation and model training have not launched.

## 1064-family checkpoint

- `6df30ad6`: replace the draft's unsupported majority-vote tie handling with
  the constructor's actual nearest-marker rule and scan-order tie convention.
  The emitted program computes Chebyshev distance in visible coordinates and
  specializes two cardinal scan directions for D4; it does not wrap an inverse
  grid transform. Native generator and original labels remain unchanged.
- An independent episode gate compares 96 policies: three primary metrics
  (Chebyshev, Manhattan, squared Euclidean), four secondary criteria (none,
  nearest-marker colour count, Manhattan, squared Euclidean), and eight spatial
  scans. Complete demonstrations filter policies and surviving query answers
  must agree. This finite comparison is not universal identifiability. Query
  labels and augmentation direction metadata are not passed to the gate.
- Keep cross-colour ties rather than applying the CLI proposal to reject
  all explicit scenes on which invariant alternatives disagree. Tests include
  a case where majority chooses the wrong colour, a primary-metric ambiguity,
  recovery with new teaching demonstrations, and 40 explicit tied-marker
  scenes checked under every D4 transform. No arbitrary colour-ID fallback.

The rewritten factory passed a new 1,000-unique-pair, 8,000-augmented-check,
16-fixture-variant execution audit. Independent complete-episode auditing
accepted 16 of 20 native contexts and verified 128 augmented records; four
contexts lacked sufficient teaching evidence and none had execution errors.

The production-assembler stress audit used 128 native random scenes plus 128
explicit tied-marker scenes. It completed 83/83 requested base episodes with
68 demonstration retries and zero query-context shortfalls: 41 cross-colour
nearest-distance ties and 42 unique-nearest-colour queries. All 664 augmented
program/grid records verified. See
`reports/query-preserving-assembly-1064-audit.json`.

All 535 regression tests passed. Remaining: 44 semantic/context holds,
9 execution failures and 3 missing factories. Bulk generation and training
have not launched; these records are local validation artifacts.

## 1065-family checkpoint

- `b7cb93ac`: preserve native tie layouts, including an above-left winner and
  varied output-slot relationships. Do not apply the draft proposal restricting
  winners to below-left and left-ordered output slots. An independent exact-
  cover dynamic program enumerates all minimum-rotation tilings with identical
  piece multiplicities. Compare four keep-orientation directions and sixteen
  strict input/output relative-order mappings. Policy ties retain all painted
  answers. Demonstrations determine rectangle dimensions and filter policies;
  all surviving query paintings must agree. The hypothesis class assumes this
  family's minimum-number-of-rotated-pieces objective, not every possible cost.
- Original demonstrations have unique painted answers; the original query has
  two minimum-cost paintings. No original labels were changed or exempted from
  context checks. Two fresh tied demonstrations plus a unique one resolve that
  query; all 16 D4/palette combinations verify. The report
  `b7cb93ac-positional-tie-evidence.json` includes the teaching context and seeds.
- Removed the emitted solver's silent 5,000-tiling storage cap. The new factory
  passed 1,000 unique fresh pairs, 8,000 augmented checks and 16 fixture variants.
  The constructor source is unchanged. Native episode auditing accepted 12/20
  independent contexts and verified 96 augmented records, with zero errors.

Production assembly now searches up to three distinct policy-evidence groups
for this family using demo answers and query INPUT only. It respects existing
split, canonical-input distinctness and pair-reuse limits. Equivalent evidence
is grouped, less-used witnesses are preferred, and unique-painting examples
fill spare demo slots so rare tie evidence is preserved for hard queries.
Tests cover a query requiring all three examples, absence of a suitable context,
canonical-equivalent duplicate exclusion, usage balancing, and D4 closure of
the complete candidate sets. A query is never swapped for an easier one during
context selection.

Diagnostic development audits are saved separately: random-context selection
completed 48/82 bases on a 256-pair pool; evidence search completed 81/82 there;
on a 1,200-pair pool the unbalanced selector exhausted useful witnesses and
completed 898/1,000. These are separate seeded assembly runs, not a matched-query
accuracy comparison, because context RNG consumption affects later strata.

The final production-assembler audit uses 1,200 native fresh pairs and completes
**1,000/1,000 fresh episodes**, including **354 swap-tie queries** and 646 unique
paintings. **All 8,000 augmented program/grid records verified**, with zero
context shortfalls and no raised reuse caps. The earlier small-pool shortfall
also gains a three-demo context in this larger pool. See
`reports/query-preserving-assembly-1065-audit.json`.

All 543 regression tests passed. Remaining: 43 semantic/context holds,
9 execution failures and 3 missing factories. Audit rows were generated in a
local temporary directory; this was not the expanded public dataset launch.
Bulk generation and model training remain pending complete coverage.

## 1067-family checkpoint

- `e5c44e8f`: retain early-stop spirals. An independent segment-pair simulator
  compares all four initial headings and both turn senses using complete demo
  outputs and query inputs. A single immediate obstacle can teach a heading
  without teaching the turn; four adjacent obstacles leave all orientations
  equivalent for a fully stopped query. Require agreement on the actual query,
  not a minimum painted-path heuristic. Tests cover unobstructed exits and
  re-entry at all 121 native start cells, D4 closure, contradictory demos and
  recovery with an informative example. Constructor and factory hashes are
  unchanged; their matching 1,000-sampled-pair/8,000-augmented/16-fixture audit
  is reused (927 distinct inputs).
- `98c475bf`: remove the fixed colour-to-motif fallback and plain-line default.
  Every target motif is read from full demonstrated input/output lines.
  Conflicting patterns, missing colours, span mismatch, clipping and overlaps
  raise instead of guessing. An independent gate infers the visible border
  axis and reads templates without D4 metadata. It now protects `make_record`
  for every augmentation, in addition to the existing native `motif_context`
  builder check. A counterfactual test changes a demonstrated motif while
  keeping the query input fixed: the program follows the changed pattern in
  all eight orientations, rather than the constructor's private motif table.

The new motif execution audit keeps each of 250 fresh queries fixed while
resampling three-demo contexts from visible evidence. It verifies 1,000 unique
pairs, 8,000 augmented pair checks and 16 fixture variants, with 40 context
retries and no sampler failures. No query answer is used to select the context.
Neither native constructor nor benchmark labels changed.

An independent episode audit accepted 36/40 contexts, excluded four missing-
evidence contexts, and verified 288 augmented program/grid records without
execution errors. Full-quota production-assembler audits then used 1,200 unique
native pool pairs per family and completed **1,000/1,000 bases each**:

| Family | Verified augmented records | Demo retries | Query-context shortfalls |
|---|---:|---:|---:|
| e5c44e8f | 8,000 | 1 | 0 |
| 98c475bf | 8,000 | 202 | 0 |

The spiral set retains 38 immediate-stop queries. Pair reuse peaks at 11 and 10,
respectively, below the existing cap. Audit rows were temporary local artifacts;
reports are saved as `query-preserving-assembly-1067-<task_id>.json`.

All 552 regression tests passed. Remaining: 41 semantic/context holds,
9 execution failures and 3 missing factories. Bulk publication and model
training remain pending complete coverage.


## Coverage checkpoint: 1,068 families

Added `c3202e5a`, selecting the unique background-plus-one-colour panel from
a regular divider grid. The constructor and original fixtures are unchanged.
The suspected smaller-period ambiguity is impossible within the native domain:
any smaller candidate cut intersects both a perpendicular real divider (colour D)
and the unique panel (only background and F, both different from D). Therefore
it cannot be a uniform full line. The true divider period remains visible.

The emitted program now rejects missing periodic structure or multiple qualifying
panels instead of using heuristic fallback lines, colour counts or reading order.
It operates in visible coordinates, with no inverse-transform wrapper.

Validation:

- New source-matched audit: 1,000 unique inputs, 8,000 augmented pair checks,
  16 fixture variants, no sampler rejections.
- Adversarial tests: all 222 native geometry/target positions, plus 385
  smaller-period/target cases that preserve misleading divider lines everywhere
  outside the target. Each runs under eight D4 transforms and two palettes:
  3,552 and 6,160 checks respectively. These test every supported geometry and
  position, not every possible pixel filling.
- Independent episode audit: 20/20 base contexts, 160 verified D4 records,
  no missing-evidence exclusions or execution errors.
- Local production-assembler audit: 1,200 unique pool pairs produce all
  1,000 requested bases and 8,000 verified combined program/grid records,
  no shortfalls; maximum pair reuse 11. Temporary audit rows were removed.
- Full regression: 555 tests passed.

Evidence is in `reports/c3202e5a-divider-period-proof.json`,
`reports/episode-evidence-1068-audit.json`, and
`reports/query-preserving-assembly-1068-c3202e5a.json`.
Remaining: 40 semantic/context holds, 9 execution failures and 3 missing
factories. Expanded bulk publication and model training remain pending coverage.


## Coverage checkpoint: 1,069 families

Added `c35c1b4c` without changing its constructor or benchmark labels.
The foreground is not necessarily the most common colour: native seed 1 has
29 foreground cells and 30 cells of a noise colour. The old program selected
an anchor and axis from generator metadata. The new program learns both from
complete demonstration pairs: four relative central-cell selectors times two
mirror axes, retaining all matching rules and requiring their query predictions
to agree. No D4-derived anchor, majority-colour heuristic or coordinate clamp
remains. A separately implemented NumPy mask check gates episode assembly.

A query-fixed contextual audit verified 1,000 unique pairs, 8,000 augmented
checks and 16 fixture variants, requiring 26 demonstration-context retries.
The initial unconditioned audit correctly stopped on an ambiguous context;
this is preserved in the local audit history. Six tests cover minority-colour
foregrounds, ambiguous-context rejection and recovery, query-label poisoning,
D4 closure, multiple agreeing hypotheses and invalid contexts. Replacing the
demonstrated axis changes the prediction for the same query input in all D4
orientations; the program actually follows its context.

The independent episode audit accepted 19/20 contexts, excluded one ambiguous
context and verified 152 augmented records. The full-quota production assembler
completed 1,000/1,000 bases and 8,000 combined program/grid records using 55
context retries, zero shortfalls and maximum pair reuse 9. Query answers are
used for final verification only, not demonstration selection. Audit records
were temporary local artifacts, not a bulk dataset publication.

All 561 regression tests passed. Reports:
`c35c1b4c-demonstrated-mirror-evidence.json`, `episode-evidence-1069-audit.json`,
and `query-preserving-assembly-1069-c35c1b4c.json` in `arc_agi2/reports`.

Also confirmed a true native label collision for `7b7f7511`: the same 4x4 input
can be produced by horizontal or vertical repetition, with different output
shapes. The concrete witness is `reports/7b7f7511-latent-collision.json`.
That family remains held: independent random orientations cannot be recovered
from a demonstration vote. Retaining both cases requires consistent episode-level
conventions and informative demonstrations, not blanket removal of the cases.

Remaining: 39 semantic/context holds, 9 execution failures and 3 missing
factories. Expanded bulk publication and model training remain pending coverage.


## Coverage checkpoint: 1,070 families

Resolved `7b7f7511` by constructing consistent episodes, preserving both native
answers for doubly repeating 4x4 inputs. The shared convention is chosen before
query sampling. All ambiguous pairs in that episode use it, and an ambiguous
query receives an informative demonstration from a different input-equivalence
class. Every pair stores exact parameters that replay through the original
native constructor. Original `generate()`, `validate()` and benchmark labels
remain unchanged. No query answer is used to choose the convention or context.

The direct program enumerates valid repeated tiles with sides 2–4. It fits both
tie conventions to all demonstrations and rejects the query if their predictions
still differ. There is no fixed D4-derived tie direction or demonstration-majority
fallback. Unambiguous square inputs and doubly repeating non-square inputs stay
supported. Existing independently sampled ambiguous episodes without sufficient
context remain invalid; the historical collision report is still correct.

The production pool builder stores complete context bundles for this family.
Every tenth sampling attempt explicitly exercises the rare ambiguous query;
the remainder uses the native dimensions and colour distribution with the shared
tie convention. This intentionally changes episode correlations and critical-case
frequency, not native input/label support. Canonical-input split isolation and
four distinct input-equivalence classes per episode remain enforced. There are
no approved size-override configurations being displaced for this family.

Validation:

- 250 contextual episodes: 1,000 native pair replays, 998 distinct inputs,
  8,000 augmented pair checks and 16 unchanged fixture variants; 25 ambiguous
  and 225 unambiguous queries. Both conventions represented.
- Six targeted tests include all 256 two-by-two patterns over four colours,
  both native labels and all D4 orientations; opposite informative demonstrations
  for the same query; weak/conflicting context rejection; split isolation and
  native replay; original fixtures and non-square repetition.
- Independent record audit: 20/20 contexts, including 10 forced ambiguous queries,
  160 verified augmented records. Poisoned query answers do not affect admission.
- Actual production pool generation: 1,200 unique queries, 1,116 training and
  84 validation context bundles. Only one duplicate-input draw rejected.
- Actual full-quota assembler: 1,000/1,000 bases, 8,000 verified combined records,
  105 ambiguous queries and 895 unambiguous queries, 493 row-tie episodes and
  507 column-tie episodes. Zero failures or shortfalls; maximum pair reuse 2,
  maximum query reuse 1. All 4,000 base pair occurrences replayed natively.
- Full regression: 567 tests passed.

Reports: `reports/7b7f7511-shared-convention-resolution.json`,
`reports/episode-evidence-1070-audit.json`, and
`reports/query-preserving-assembly-1070-7b7f7511.json`.
These were temporary local audit records, not bulk dataset publication.

Remaining: 38 semantic/context holds, 9 execution failures and 3 missing
factories. Expanded dataset publication, SFT and RLVR remain outstanding.


## Coverage checkpoint: 1,071 families

Added `a680ac02` while preserving its original constructor and benchmark labels.
The native rule concatenates hollow frames along the uniquely separated projection
axis. Overall coordinate spread is an insufficient shortcut: hollow-frame corners
(0,0), (2,5), (20,10) have row gaps 2 and 18, and column gaps 5 and 5. The native
rule concatenates horizontally, although total row spread exceeds column spread.
This is a reachable placement, with non-overlapping boxes and native dimensions.

The direct program fits three hypotheses to complete demonstration pairs:
projection-gap separation and total spread with either equal-spread tie convention.
All surviving query predictions must agree. It has no preferred-rule fallback.
A separate colour-coordinate/border parser performs the same evidence check before
context selection. Both tie conventions remain present so rotating an episode
does not silently change whether its context is sufficient. Hard outlier queries
are retained and their demonstrations supply the distinction.

Validation:

- Source-matched contextual audit: 1,000 unique pairs, 8,000 augmented pair checks,
  16 fixture variants and 46 demonstration retries, with each query held fixed.
- Five targeted tests cover reachable outliers, equal spreads under every D4,
  opposite demonstrated rules for the same query, insufficient context recovery,
  query-answer poisoning, canonical fixtures and invalid examples.
- Independent episode audit: 20/20 accepted contexts and 160 verified records.
- Full-quota assembler: 1,200 unique pool pairs yield 1,000/1,000 bases and
  8,000 verified combined records. Of the queries, 72 require distinguishing
  spacing evidence and 928 have agreeing rule predictions. There are 414 context
  retries, zero shortfalls, and maximum pair reuse 9. Audit records are temporary
  local artifacts, not a bulk publication.
- Full regression: 572 tests passed.

Reports: `reports/a680ac02-demonstrated-spacing-evidence.json`,
`reports/episode-evidence-1071-audit.json`, and
`reports/query-preserving-assembly-1071-a680ac02.json`.
Remaining: 37 semantic/context holds, 9 execution failures and 3 missing
factories. Expanded dataset publication, SFT and RLVR remain outstanding.


## Coverage checkpoint: 1,072 families

Added `a1aa0c1e` without changing its constructor or benchmark labels. Its native
encoding ranks ladder lengths; counting visible rungs is a different rule that
happens to fit the original fixtures. A reachable [1,6,7] length configuration
has rank encoding [1,2,3] versus rung counts [0,3,3]. The new program fits both
modes to all demonstration outputs and requires their query predictions to agree.
It no longer defaults to rank when context is insufficient or contradictory.

The independent evidence decoder finds full level lines and the floor directly
in the visible input, then collects off-level colour coordinates. It validates
contiguous ladder lanes and alternating two-cell rails/three-cell rungs. Query
answers never enter context selection. The target emits cells directly in the
augmented coordinate system with affine placement, without inverse-grid wrappers.

Validation:

- Contextual execution audit: 1,000 unique pairs, 8,000 augmented checks,
  16 fixture variants and five demonstration retries, keeping queries fixed.
- Six targeted tests cover all 1,818 native start-row/gap/length combinations
  with fixed allowed colours/columns, plus D4 and palette checks on absent,
  one-cell, even-length, partial and equal-length ladders. Other colours and
  columns are sampled in the random audit. Equal native lengths can be 3,4,5;
  the earlier worker examples 6 and 7 cannot fit the native row constraints.
- Counterfactual demonstrations change the selected mode for the same query;
  weak or contradictory contexts fail closed, and query-answer poisoning cannot
  change admission.
- Independent episode audit: 20/20 contexts and 160 verified augmented records.
- Full-quota assembler: 1,200 unique pool pairs produce 1,000/1,000 bases and
  8,000 verified combined records. There are 30 demonstration retries, zero
  shortfalls and maximum pair reuse 10. Of the queries, 628 need rule evidence
  and 372 have agreeing predictions. Overlapping category counts are: 446 with
  an absent ladder, 186 with a one-cell stub, 785 with a positive even length,
  and 22 with all equal lengths. No hard-case restriction was introduced.
- Full regression: 578 tests passed.

Reports: `reports/a1aa0c1e-demonstrated-ladder-evidence.json`,
`reports/episode-evidence-1072-audit.json`, and
`reports/query-preserving-assembly-1072-a1aa0c1e.json`.
These were temporary local audit records, not expanded dataset publication.
Remaining: 36 semantic/context holds, 9 execution failures and 3 missing
factories. Expanded dataset publication, SFT and RLVR remain outstanding.


### Verified program coverage: 1,073 / 1,120

aa300dc3 now learns full-diagonal versus contiguous-run interpretation and visible tie rules from demonstrations. Broken diagonals remain in the native domain; unresolved ties reject instead of choosing scan order. Independent evidence checks never read query outputs. Fresh execution audit passed 1,000 unique pairs, 8,000 augmented checks and 16 fixture variants. Full-quota assembly produced 1,000 base episodes and 8,000 verified combined program/grid records, including 56 broken-line queries; 291 context retries, no shortfalls. All 584 regression tests passed. These are local validation records, not the expanded published corpus. 47 program families remain; bulk generation and model training have not launched.


### Verified program coverage: 1,074 / 1,120

5168d44c learns signed frame motion from demonstrations and compares it against the dot-majority heuristic. No default direction from augmentation metadata. Native contrary-majority cases are retained. Audit: 1,000 fresh pairs (895 distinct inputs), 8,000 augmented checks, 16 fixture variants. Full quota: 1,000 bases, 8,000 verified program/grid records, 272 minority-directed queries, 319 context retries, no shortfalls. Six focused tests and all 590 regression tests passed. 46 program families remain. Local audit only; expanded dataset and training have not launched.


### Verified program coverage: 1,075 / 1,120

afe3afe9 uses demos to distinguish packing toward the marked colour from clockwise/counterclockwise packing relative to the border. Both native handednesses remain. Independent component decoder checks the vectorized target. Audit: 1,000 unique fresh pairs, 8,000 augmented checks, 16 fixture variants. Full quota: 1,000 bases, 8,000 verified combined records, 515 clockwise-aligned and 485 counterclockwise-aligned queries, 134 context retries, zero shortfalls. Six focused tests and all 596 regression tests passed. 45 program families remain. Expanded bulk generation and training have not launched.


### Verified program coverage: 1,077 / 1,120

72ca375d now learns symmetry predicates from demonstrations; transverse-symmetric decoys remain. 3a301edc now requires agreement among demonstrated band-thickness rules; original non-square fixture stays unchanged. Both pass 1,000 fresh pair audits, 8,000 augmented checks and 16 fixture variants. Full-quota assembly produces 1,000 fresh bases each: 8,000 symmetry records (110 transverse-decoy queries) and 7,996 band records (four equivalent variants removed, with independent transform-group checks). No quota shortfalls. All 608 tests pass. 43 program families remain. These local audits are not the expanded published dataset.


### Verified program coverage: 1,085 / 1,120

Eight families added: d9fac9be, abbfd121, 94be5b80, 93b4f4b3, 4852f2fa, 6cf79266, 3345333e, 891232d6. Each passes 1,000 fresh native pair checks, 8,000 augmented checks and 16 fixture variants. Direct programs reject unresolved visible ambiguities; demo-dependent conventions use demonstration answers only. Native constructors remain unchanged except a valid-draw-preserving empty-shape guard in 93b4f4b3. All 654 regression tests pass. The ring, wallpaper, legend and gallery full-quota audits each retain 1,000 bases / 8,000 combined program-grid records under explicitly audit-only local partitions. No production data or SFT launch. 35 verified-program families remain.


### Verified program coverage: 1,093 / 1,120

Eight families added: 22425bda, 337b420f, 4290ef0e, 447fd412, 6e4f6532, 782b5218, 7e2bad24, 80214e03. Each passes 1,000 fresh pair checks, 8,000 augmented checks and 16 fixture variants. Independent visible-evidence gates reject unresolved interpretations; queries with insufficient demonstration evidence are retained while the context is resampled. Exact-cover stamping requires all solutions to agree. Clipped/off-grid frame centres and mirror-end grazing/piercing are retained.

The 80214e03 synthetic domain now explicitly requires every latent mosaic row/column band to remain partly visible, eliminating completely hidden bands. Individual erased blocks remain possible, with ambiguous inputs rejected by an independent gate. This is a documented generator validity change, not proof that the original unconstrained family was identifiable. A 10,000-draw probe observed no whole-band resampling and 97 other ambiguous reconstructions; all original fixtures remain unchanged.

All 703 regression tests pass. 27 program families remain. This is verification coverage, not a claim that the requested 1,000-episode-per-family expanded corpus is already generated or published. Production generation and SFT have not launched.


### Verified program coverage: 1,094 / 1,120

de809cff now partitions solid-core fragments into rectangle hypotheses, checks the single/domino-hole grammar, and requires agreement across every surviving complete reconstruction. It preserves the original fragmented-core query and correctly handles a native-valid foreign-pixel bridge that defeated the old run-merging heuristic. Native constructor unchanged. Audit: 1,000 unique native pairs, 8,000 augmentation checks, 16 fixture variants; five focused tests pass in addition to the preceding 703-test suite. 26 families remain; expanded dataset and SFT still await coverage.


### Verified program coverage: 1,102 / 1,120

Eight more families: 9356391f, 963c33f8, 985ae207, a3f84088, b230c067, d931c21c, df8cc377, e1d2900e. Each has 1,000 fresh pair checks and 8,000 augmentation checks; these audits are not the requested production quota of 1,000 episodes per family. Reports retain distinct-input counts and any sampling rejections.

9356391f now marks clipped rings consistently; e1d2900e selects the nearest square using Chebyshev distance, with demonstrated tie conventions. Their original fixtures are unchanged. The 963c33f8 six-cell teaching hypothesis, a3f84088 one-cell teaching correction and d931c21c one-cell upstream-proposed correction are explicitly labelled and hash-pinned; original benchmark labels stay unchanged. Competing interpretations for 963c33f8 remain documented.

df8cc377 requires a context-enriched teaching fixture: one native demonstration identifies checkerboard phase. All original pairs remain unchanged, but the original three-demo context still abstains and is NOT counted as an unaided benchmark solution. Its 16 fixture checks refer to the enriched context. Fresh queries retain their inputs while phase-insufficient demonstrations are resampled.

985ae207 retains its slow native domain. A compiled proposal sampler preserves its proposal/acceptance rules and is checked against the unchanged native renderer; the audit required about 716 million proposals. Production acceleration remains separate work.

18 program families remain under parallel repair/review. Production dataset generation and SFT have not launched.


### Verified program coverage: 1,107 / 1,120

Five more families: b942fd60, dd2401ed, b7955b3c, 85fa5666, e5062a87. Original labels and native constructors remain unchanged. Demonstrations select explicit ray thresholds, cursor recolouring and stamping hypotheses. Missing context triggers demo resampling with the query retained; intrinsic box-occlusion ambiguity rejects the query with a witness. Hypothesis agreement is relative to the documented candidate rules, not proof that no other ARC interpretation exists.

All five pass 1,000 fresh pair checks, 8,000 augmented checks and 16 canonical fixture variants. Three also passed a second independent Claude CLI review and repeated audits. The 748-test regression had one outdated canonical-only fixture test: it now follows the explicit hash-pinned teaching-fixture policy and passes across the current factory set. The other 747 tests passed unchanged. Additional integrated gate/program tests pass. Thirteen program families remain; production dataset generation and model training remain pending coverage.


### Verified program coverage: 1,109 / 1,120

e048c9ed and f3e14006 now select between explicit visible mechanisms using demonstrations, retaining every original label. Each passes 1,000 fresh pair checks, 8,000 D4/palette checks and 16 canonical variants; 21 focused tests pass together. Context-only retries retain queries. e048c9ed has 913 distinct inputs and 68 context retries; f3e14006 has 1,000 distinct inputs and 123 retries.

The e048c9ed hypothesis family excludes marker-coloured bars when choosing a repeated-length reference. This is an explicit scope assumption: including the rival that counts those bars makes the original query ambiguous. The retained report demonstrates that ambiguity; no universal-rule claim is made. f3e14006 enumerates plain weave and nearest-marker parity-boundary variants, including tied markers and orientations.

Eleven program families remain. Production data and SFT still await coverage.


### Verified program coverage: 1,114 / 1,120

b1986d4b, 9772c176, d753a70b, c6e1b8da and d5c634a2 are admitted. Each has 1,000 fresh-pair checks, 8,000 augmentation checks and16 fixture variants. c6 additionally passed12,000 independently examined native/dense scenes; intrinsically ambiguous visible inputs are rejected rather than assigned contradictory targets. b198 enumerates possible visible backgrounds instead of assuming the majority colour.

d753 uses an explicitly labelled ten-cell concentric teaching hypothesis. Its original canonical context remains unsolved; original labels and query answers are unchanged in the benchmark. d5's random sampler now rejects exact duplicate latent placements, which were invisible but counted twice in outputs. Its explicit fixture branch is unchanged, and the live patched source passed a new full audit. These are finite checks under the documented rule hypotheses and context gates.

This is coverage work, not production episode counts. The dataset quota remains1,000 fresh base episodes per family with program AND grid in each record, followed by consistent D4/colour augmentation. SFT has not launched.


### Verified program coverage: 1,115 / 1,120

ac0c5833 passes1,000 unique fresh pairs,8,000 augmentation checks,16 original fixture variants and11 tests. It distinguishes ordinary template copies from a geometric hollow-outline trim using demonstrations. Overlapping stamps combine their painted pixels; there is no learned per-shape lookup table. Original labels and native constructor remain unchanged. Context resampling retains the query; the gate consumes query inputs only. Five families remain.


### Verified program coverage: 1,117 / 1,120

bd14c3bf passed1,000 fresh-pair checks and8,000 augmentation checks, with slow native sampling explicitly recorded. Independent review additionally exhaustively checked8,320 template/object combinations and tested1,000 context-gated episodes, retaining all88 queries on which competing shape rules differed. Missing demonstration evidence resamples demos while preserving the query.

ba1aa698 uses a labelled four-cell uniform-motion teaching copy consistent with its unchanged synthetic generator. Original labels and query answers stay unchanged; the original canonical demonstration conflict is not claimed solved. The audited proposed generate() is AST-identical to the live native sampler, and15 portable tests verify original refusal, teaching-copy success and query-label isolation.

Three remaining families:1b8318e3,a64e4611,f3b10344. Production generation and SFT remain pending.

### Final coverage checkpoint — 2026-10-21

All 1,120 declared task families are admitted. The final cross-family replay passed 17,920 fixture variants, with exact demonstration/query outputs. [Machine-readable replay](reports/coverage-evidence/final-coverage-replay.json). This is generator/program preparation, not a trained-model result.

- `1b8318e3`: independent input-only docking gate; 1,000 fresh distinct pairs, 8,000 augmented checks and 16 canonical variants. Hidden-order ambiguous inputs are explicitly rejected; demonstration retries retain the query.
- `f3b10344`: one additional native demonstration disambiguates centred versus overlapping bridge pairing. Original pairs and query answers are unchanged. Coverage uses the labelled enriched context; the original context remains ambiguous within the documented rival family.
- `a64e4611`: `visible-clearance-v1` is an explicitly versioned synthetic definition. All original fixture variants pass. It preserves native random inputs but changes 1,372 of 2,536 synthetic labels in the audit, so it is **not native-equivalent**. The original constructor is archived. Targets fit 930 parameter hypotheses to demonstrations and require agreement on the query, with no privileged parameter choice. Every exported episode carries variant provenance. [Evidence and comparison image](reports/coverage-evidence/a64e4611/README.md).

These finite audits remain supplemented by exact per-episode verification during the future dataset build. No bulk generation, SFT or RL was launched by this checkpoint.
