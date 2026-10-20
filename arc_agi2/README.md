> **2026-10-20: Coverage first.** The million-episode job was canceled at the user’s request. All 1,120 public tasks are now in scope. No bulk generation or model training is running from this work. Standalone new modules use `tasks/task_<id>.py` with `generate(...)` and `validate()`. Claude CLI drafts are not counted before validation and review.
>
> Target after coverage: **1,120 × 1,000 = 1,120,000 fresh episodes**, then all eight D4 transforms, **up to 8,960,000 episodes** before symmetry deduplication and adaptive family shortfalls. The old million-episode builder needs the exhaustive-expansion update before relaunch; its full-coverage guard currently blocks bulk use.
>
> Colours are sampled by native generators. Extra episode-wide colour permutation is opt-in, not mandatory. Rotations/reflections always transform all demonstration and query grids consistently. Native solver validation occurs before augmentation: the augmented rule is `T f T^-1`, not necessarily the original direction-specific rule.

# ARC-AGI-2 procedural generator research

This fork adds a reference-guided generator workflow and an adaptive episode builder. Reviewed standalone additions extend `task_list.task_list()` without replacing upstream entries. Older constructive drafts remain in `arc_agi2.generators.registry` while conversion proceeds.

## Current evidence

- All **1,120** canonical tasks inventoried with saved Opus/Fable explanations, `transform(grid)` programs, provenance and separately labelled teaching fixtures.
- **891 existing upstream generators** reproduce the canonical pair sets (pair ordering can differ between releases).
- **89 new constructive implementations** have passed bounded validation, covering counting, selection, geometry, legends, relational motion, scaling, pattern construction and repair. Standalone conversion and review are tracked separately below.
- **Two variable-size extensions**: `0692e18c` (inverse self-tiling) and `00576224` (three-by-three tiling with mirrored middle band).
- All 91 constructors (89 new families plus two size extensions) passed **300 random differential tests each**, and their reference solvers reproduce all original examples. Outputs are constructed independently from latent parameters, then compared with the saved transform.
- **22 additional fixed-size families / 111 size-parameter configurations** passed bounded 12-seed differential tests. Every such generated pair is checked again during generation. This is agreement evidence, not proof of semantic correctness.
- **140 tasks still need constructive generators**. A saved transform is not itself an input generator. Reference packets and `reports/generator-roadmap.csv` provide the task-by-task backlog.

## Inspect

[Interactive histogram and task browser](https://ritwika96-arc-episode-gallery.static.hf.space/coverage/index.html) · [All integer-size counts](reports/exact-size-histograms.csv) · [All rectangular-shape counts](reports/exact-shape-histograms.csv) · [Generator roadmap](reports/generator-roadmap.csv)

The report separates 1,000 training tasks from 120 public evaluation tasks, query grids from demonstration grids, and source coverage from candidate mechanism tags. The latter are overlapping lexical tags from teacher explanations, not gold semantic labels.

## Generate

Install Python 3.12+, numpy, pyarrow and huggingface-hub. From the repository root:

```sh
python -m unittest arc_agi2.test_pipeline -v
python -m arc_agi2.audit --workers 4
python -m arc_agi2.validate_parameters
ARCGEN_WORKERS=32 python -m arc_agi2.build_million
```

HF target: `ritwika96/arc-agi2-arcgen-1m-episodes`. Requires a write-capable `HF_TOKEN` in the environment. Use `--local` for no Hub writes and `--tasks ID ...` for a small test. `ARCGEN_TARGET_EPISODES`, `ARCGEN_POOL_SIZE`, `ARCGEN_FAMILY_SECONDS`, and `ARCGEN_BUILD_ROOT` configure generation. Master seed 20261021.

The builder first makes fresh pools of unique inputs, then allocates training/validation episodes adaptively by observed diversity. It targets the exact **query longest-side bins 1–30 jointly with output shape-change category** from all 1,120 tasks; it reports full height/width histograms too. It does not guarantee matching all joint dimensions or reasoning difficulty. Unsupported bins are published as shortfalls, never silently replaced by easy duplicates. A finite pool means the first build can finish below one million. Allocation and achieved counts are explicit.

Each episode contains three demonstrations and one query. Targets are output-grid JSON only. No solver code, reasoning or query labels are included in the prompt. Shared palette/D4 augmentation is recorded; fresh native episode hashes ignore demonstration order and augmentation. Equivalent input grids under palette renaming/D4 are assigned to the same split globally before episode construction. All 1,120 tasks, including the former 20 holdouts, are training-eligible after validation. The historical flags remain provenance only. Public evaluation families used in training are no longer independent evaluations.

## Getting to full coverage

For each missing task:

1. Inspect original demonstrations and teacher explanation. Write a rule specification including counterexamples, object connectivity, parameter ranges and ambiguous cases.
2. Construct random valid latent scenes. Vary semantic parameters (object count, relations, graph structure, legend length, occlusion, path length, composition depth) as well as dimensions. Do not generate arbitrary noise and merely run the solver on it.
3. Derive outputs independently from those latent scenes and compare against `transform(grid)`.
4. Reproduce canonical examples; keep corrected teaching copies separate. Validate random and adversarial seeds across 1–30 grids, preserving task constraints.
5. Check demonstration identifiability against plausible alternative rules. Passing a solver check alone does not establish unambiguous episodes.
6. Report input uniqueness, size histograms, output-shape changes, difficulty proxies and new-input validation performance. Only then register the generator as training eligible.

Research extensions currently cover restricted constructive subfamilies. They do not claim every original edge case or a validated difficulty match. No generic image scaling is used to fake larger puzzles.

## Tinker to eight H200 GPUs

The planned grid-only rank-128 LoRA SFT can continue from exported learned weights. Before credits run out, export the adapter, exact base-model revision/tokenizer, data revision/cursor, LoRA configuration, loss masks and learning-rate schedule. Tinker training state can resume on Tinker; its optimizer state is not assumed portable to an external trainer. On H200s, validate logits/loss after the supported Tinker-to-PEFT conversion, then resume with a new optimizer and brief warmup, or merge into the exact base model for full fine-tuning. This repository does not launch model training.

## Provenance and licensing

Upstream ARC-GEN is Copyright Google LLC and licensed Apache-2.0. This is an independent research fork. Canonical ARC task data retain their original attribution and licence; see `references/` and the official ARC-AGI-2 repository. Teacher packets are selected solution artifacts from our project, not full CLI conversations or credentials. Eight teaching fixtures are labelled corrected variants. Frozen replay provenance is retained; generalization of teacher code beyond supplied examples must be tested.

## Standalone task-file conversion campaign

User-requested upstream format: `tasks/task_<id>.py`, optional-parameter `generate(...)`, and `validate()` reconstructing original pairs through generator calls. Completed and reviewed entries are registered through `arc_agi2/task_registry.py` and included in `task_list.task_list()`. Drafts remain outside that registry.

First reviewed conversion: [`tasks/task_62593bfd.py`](../tasks/task_62593bfd.py). It reconstructs all four original pairs from latent objects and passed 1,000 new seeds. The CLI candidate report is in `reports/standalone/62593bfd.json`; its declared restrictions remain visible.

The authoring campaign uses eight concurrent Claude CLI processes under the user’s Max subscription; API credentials are removed from their environment and there is no API fallback. Every candidate is checked for original fixture reconstruction, valid grids, bounded execution, nonidentity examples, native input diversity and 300 fresh comparisons against the saved solver. Registration additionally requires review. Constructors generate new latent scenes rather than transformed copies of original examples.

A zero-error differential check is a bounded agreement test. It does not prove the saved solver is universally correct or that every original mechanism variant is covered.

**83 standalone modules are now reviewed and registered** (the exact list lives in `task_registry.py`). Each passed 1,000 seed checks and exact original train/test fixture reconstruction. The first sixteen used seeds 0..999 (including their 300 author-validation seeds); the next sixty-seven used independent seeds 20,000..20,999. The regression suite also checks registered source hashes and seeds 10,000..10,019.

Twenty-four conversions replace earlier research constructors with the upstream task-file interface. The total is now 89 new constructive families, with 6 still awaiting standalone conversion/review. Remaining CLI drafts are authored and validated locally. Restricted shape and dimension ranges are documented per file and in `reports/standalone/`; the size-matching builder must respect those ranges.

Independent validation exposed a background-inference failure in the saved `d4c90558` solver: a thick frame can dominate a small grid, causing the checker to interpret the wrong colour as background. The constructor now samples the explicit domain where 0 strictly outnumbers every other colour. The failing examples are retained in `reports/standalone/d4c90558-counterexamples.json`. This restriction is not evidence that the conceptual counting rule fails on denser scenes.

Semantic review also corrected `e872b94a`: its generated walls must partition the background into N+1 connected regions, as every original pair does. Floating paths that merely satisfy the saved wall-count shortcut are excluded. The independent 1,000-seed check produced 998 distinct inputs (two repeats), so unique input count is reported separately from sample count.

New authoring uses **Opus 5.5 via Claude Max CLI**, with eight workers. Fable authoring was explicitly stopped; earlier completed artifacts remain archived and retain their original model attribution. API fallback remains disabled.

The first reviewed Opus 5.5 additions, `2ba387bc` and `4c3d4a41`, add two previously missing families rather than converting existing drafts. Both reconstruct all original fixtures and pass 1,000 independent seeds. Remaining missing family count: 140.


The next six reviewed Opus additions are `8698868d` (match panels by hole counts), `b5ca7ac4` (directional object stacking), `b0039139` (combine four instruction panels), `c4d067a0` (anchor a scaled legend), `c7f57c3e` (swap decorations across scales), and `da515329` (construct interleaved spirals). All six reconstruct the original fixtures and pass 1,000 independent seed checks. Five produced 1,000 unique inputs; `da515329` produced 982, reflecting its more limited native parameter space. Review fixed ignored parameter overrides, removed a canned fallback, and included diagonal hole contacts present in the originals. The eleven-test regression suite passes. Supported ranges and limitations remain in each task's report.

The following six reviewed additions bring standalone coverage to 41: `136b0064` (glyph programs), `e376de54` (middle-segment length), `e87109e9` (legend-steered beams), `edb79dae` (template/colour composition), `4c7dc4dd` (embedded analogy) and `de809cff` (overlap, denoising and hole marking). Each passed 1,000 independent seeds with 1,000 distinct inputs. `e376de54` samples all square sides 10..30 instead of inheriting the examples' fixed 16x16 size; `136b0064` varies output width 7..22 instead of fixing it at 7. Canonical fixtures retain their exact dimensions. Analogy examples must uniquely distinguish the three supported relation classes. Fixture-input replay for the analogy's hand-made noisy backgrounds is separate from its random scene sampler.

The pair-pool builder now always selects the reviewed standalone version when available. It does not mix that version with an earlier research draft. Cached pools require matching source fingerprints, requested pool size and file hashes; Python and NumPy are seeded for each construction. Bulk generation additionally requires every new family to have a reviewed standalone file. Seventeen regression tests pass, including original fixtures, new size bounds, ambiguity rejection and cache invalidation. Bulk generation remains stopped.

The next six reviewed additions bring standalone coverage to 47: `14754a24` (complete noisy plus fragments), `17829a00` (move or stretch objects toward matching borders), `18419cfa` (reflect motifs inside marked frames), `1acc24af` (classify pieces by recess fit), `1ae2feb7` (periodic row propagation with overlap precedence), and `1b59e163` (copy templates onto markers). All six passed 1,000 independent seeds with 1,000 distinct inputs. Review expanded supported canvas sizes up to 30, added up to four recesses, fixed ignored dimension overrides and removed canned whole-scene fallbacks. Original fixture dimensions are unchanged. The border-stretch exception remains supported by only one demonstration; that limitation is recorded explicitly.

Four further reviewed additions bring standalone coverage to 51: `0934a4d8` (recover a masked symmetric patch), `09c534e7` (propagate seed colours through connected block interiors), `13e47133` (corner-coded concentric ring fills), and `184a9768` (translate pieces into uniquely tileable holes). Each passed 1,000 independent seed checks with 1,000 distinct inputs and exact original fixture reconstruction. The symmetry task preserves its original 30x30 fixtures and explicitly labels block-size extensions yielding sides 14, 18, 22 and 26. Connected structures can contain up to nine blocks on large canvases; jigsaw frame sides can reach 18. Silent canned-scene/count fallbacks were removed, dimension overrides are honored, and the tests cover ring chains starting with background and ambiguous coloured jigsaws.

Four more reviewed additions bring standalone coverage to 55: `142ca369` (bouncing diagonal rays), `1da012fc` (miniature-map recolouring), `20270e3b` (join marked pieces), and `2037f2c7` (find damage by comparing copies). Each passed 1,000 independent seeds and exact fixture reconstruction. Ray canvases now reach 30 and include a dense parallel branch; a separate 300-scene audit exercised up to 13 emitters and six total bounces. Legend sampling now includes border dots (91/300 audited scenes) and honors dimension/colour requests. Damaged figures can be taller than 14 when placed side by side; default height now reaches 20. Tests check the three-bounce colour sequence, piece-cell conservation, border-dot coordinates and tall-figure recovery.

Four further additions bring standalone coverage to 59: `21897d95` (marker-directed region repainting and rotation), `221dfab4` (periodic ladders crossing blobs), `247ef758` (overlapping legend stamps), and `25c199f5` (ordered falling pieces). All passed 1,000 independent seeds. Region construction now supports connected irregular boundaries; 100 separately audited 24x30 scenes each had six regions and exactly four requested markers. Two initial counterexamples exposed the saved solver's any-colour L-marker heuristic; they are preserved in `reports/standalone/21897d95-counterexamples.json`, and incidental five-cell corners are excluded. Stamp canvases reach 30x30 with up to five motifs. Stacking preserves original three-panel 5x5 fixtures while explicitly labelling larger sizes/counts as synthetic extrapolations. Bulk generation remains stopped.

Two further reviewed additions bring standalone coverage to 61: `271d71e2` (boxes push walls while converting movement counts into 7s) and `291dc1e1` (read border-directed lanes and center their blocks). Both reconstruct every original fixture and pass 1,000 independent seeds with 1,000 unique inputs. Box sampling now honors requested dimensions/counts and supports sides up to 30, interiors up to 12 and gaps up to 14. Lane sampling has no fixed fallback, honors width, and labels extra lanes as synthetic mechanism extrapolations. Regression tests cover stationary/moving boxes, all four movement directions, all eight border orientations and 2..5 lanes. All 18 tests pass.

Two further reviewed generators bring standalone coverage to 63: `16b78196` (unique-cover jigsaw chains locking into notched walls) and `28a6681f` (local nearest-drop water flow). Each reconstructs all canonical fixtures and passes 1,000 independent seeds. Jigsaw parameter checks prevent silently missing pieces and reject incomplete geometry; 100 additional rectangular scenes preserve every colour count and the wall mask in both orientations. Water generation now reaches side 30, with larger water counts explicitly labelled as synthetic extensions. Another 100 30x24 examples preserve exactly 40 water cells and all solid terrain, covering blobs/columns with ramps on/off. All 19 regression tests pass.

Three further reviewed generators bring standalone coverage to 66: `20a9e565` (extrapolate growing sequences through a marked window), `2b83f449` (ladder endpoint routing), and `2c181942` (rotate matching shapes into a coloured hub). Each passes 1,000 independent seeds and reconstructs all canonical fixtures. The retried sequence task supports four latent families, with 100 additional 30x30 examples checked per family; staircase colour cycles now show a repeated cycle before prediction. Requested canvas dimensions are honored without upscaling objects. Another 100 large ladder scenes preserve all 28 markers, and 100 alternate-background hub scenes preserve the hub and erase distractors. Partial rung/hub parameters are rejected rather than ignored; the fixed hub-shape fallback is removed. All 20 regression tests pass.

Three further reviewed generators bring standalone coverage to 69: `195c6913` (legend-controlled paths), `2ccd9fef` (growing objects in framed panel sequences), and `2d0172a1` (containment diagrams). Each passed 1,000 independent seeds with exact fixture reconstruction. Review fixed palette reservation, rejected ignored partial parameters, expanded panel cross-dimensions to 30, and removed fixed scene fallback and late simplicity downgrade from containment sampling. Another 100 explicit-palette path scenes, 100 30x30 panel strips covering both axes/periods, and 120 containment scenes covering all six styles were checked. Pair style now honors two outside blobs instead of silently clamping to one. The containment renderer inherits the saved rule's narrow dot-snapping convention, explicitly documented as a limitation. All 21 regression tests pass.

Three further reviewed additions bring standalone coverage to 72: `2f767503` (erase ray-hit connected blobs), `31f7f899` (sort bar extents along a divider), and `320afe60` (translate and recolour open/closed objects). Each passed 1,000 independent seeds with exact fixture reconstruction, plus 100 requested-size and invariant checks. Review fixed ignored controls and distractor counting, extended ray canvases to 30, rejected ambiguous bar ties and inconsistent openness labels, and removed fixed fallbacks. All 22 regression tests pass. Coverage is now 969/1,120, with 151 missing.

`269e22fb` remains unregistered: its draft varies crops of one fixed picture. Fresh-picture generalization requires an episode-level shared template and contextual verification; independent templates must never be mixed within an episode. See `reports/review-blockers/269e22fb.json`.

Three further reviewed additions bring standalone coverage to 75: `332f06d7` (sliding squares through corridors), `3391f8c0` (repeated/odd shape exchange), and `351d6448` (panel sequence continuation). Each passed 1,000 independent seeds, exact fixture reconstruction, and 120 extra large-grid checks. Sliding scenes now include widened rectangular/staircase rooms and optional cycles, with requested reachability and unique farthest stops checked. Shape exchange now honors dimensions, palettes and copy count, mixes loose and tight identifiable placements, and supports masks up to 6x6. Sequence panels can reach height 9 with input height capped at 30; all three mechanisms and both directions were audited at 29x30. Fixed mask/motif fallbacks and ignored controls were removed. All 23 regression tests pass. Coverage is 972/1,120 with 148 missing.

Four further reviewed additions bring standalone coverage to 79: `35ab12c3` (polygon outlines and companion copies), `36a08778` (branching streams), `38007db0` (odd-panel extraction), and `396d80d7` (diagonal-contact colouring). Each passed 1,000 independent seeds, exact fixture reconstruction, and 120 extra parameter/invariant cases. Review fixed ignored controls, removed fixed scene/motif fallbacks, added L-shaped obstacle clusters and rectangular panels, and expanded canvas/figure ranges with synthetic extensions labelled. The extra checks verify requested shape/companion counts, preservation of stream sources and walls, exact odd-panel extraction, and the complete diagonal-only changed-cell mask. All 24 regression tests pass. Coverage is 976/1,120 with 144 missing.

Four further reviewed additions bring standalone coverage to 83: `3a25b0d8` (template-to-outline pocket transfer), `3ad05f52` (door-linked room routes), `3d588dc9` (nearest aligned key selection), and `3dc255db` (cup marker emission). Each passed 1,000 independent seeds, exact fixture reconstruction, and 120 additional parameter/invariant cases. Room sampling now includes dead-end attachments that remain unfilled and cannot shortcut the route. Key scenes now exercise the nearest-of-two aligned candidate decision. Cup scenes include diagonal arches, exact counts and clipped emissions. Template controls now reserve explicit colours and reject incomplete geometry. The native template family is still banded, with free-form fixture art confined to explicit replay. All 25 regression tests pass. Coverage is 980/1,120 with 140 missing.
