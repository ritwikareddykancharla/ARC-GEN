# Combined program and grid dataset

Production exports use **one episode per row**, containing a lossless PNG and a
JSON record with both the program and the output grids. Images include query
answers for human inspection; only `prompt` and `completion` are model inputs
and targets. TAR shards group PNG/JSON pairs using the same episode identifier.
Hugging Face's viewer may internally convert them to Parquet.

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
- Six additional reviewed factories: `62593bfd`, `e4888269`, `fc7cae8d`,
  `65b59efc`, `142ca369`, `f931b4a8`. Each passed 1,000 fresh pairs, 8,000
  augmented pair checks and 16 supplied-fixture variants.
- Existing hand-reviewed direct rewrites supplement these sets; overlap means
  counts must be computed as a union, not added.
- Local exporter test: 18 fresh base episodes, 144 augmented PNG/program/grid
  records. It requested 20 bases and reported a two-episode shortfall.
- 229 regression tests pass.

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
