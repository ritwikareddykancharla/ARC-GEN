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
- 428 admitted factories. Each passed 1,000 fresh pairs, 8,000 augmented pair
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
- The union currently admits 647 of 1,120 families; 473 still need direct
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
programs. The regression suite passed 249 tests at this checkpoint.


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
