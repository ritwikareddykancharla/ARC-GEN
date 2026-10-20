# Combined program and grid dataset

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
   explicit provenance. Three unresolved native-label conflicts remain outside
   the admitted program set.

Fresh native-program audits distinguish sampler failures from program failures.
They do not retry mismatching programs until an easy example passes. Five
previous sampler failures passed on the bounded recheck; all failures remain
recorded. Passing finite audits does not prove unrestricted generalization.

## Current verified evidence

- 213 native direct-coordinate certificates admitted after fresh audits and
  supplied-fixture checks.
- 808 admitted factories. Each passed 1,000 fresh pairs, 8,000 augmented pair
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
- The union currently admits 1027 of 1,120 families; 93 still need direct
  augmented program admission. Constructor coverage and program coverage are
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
