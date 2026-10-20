> **2026-10-20: Coverage first.** The million-episode job was canceled at the user’s request. All 1,120 public tasks are now in scope. No bulk generation or model training is running from this work. Standalone new modules use `tasks/task_<id>.py` with `generate(...)` and `validate()`. Claude CLI drafts are not counted before validation and review.
>
> Target after coverage: **1,120 × 1,000 = 1,120,000 fresh episodes**, then all eight D4 transforms, **up to 8,960,000 episodes** before symmetry deduplication and adaptive family shortfalls. The builder now emits every D4 variant, deduplicates symmetric episodes, and reports fresh and augmented counts separately. Its full-coverage and reviewed-standalone guards still block bulk use.
>
> Next model-training stage, as clarified by the user: **full-parameter SFT on query output grids on the user’s 8 × H200 GPUs**, using demonstration/query inputs, without hints or reasoning targets. Mastery-based family sampling is a proposed SFT curriculum and must be evaluated using free-generated exact grids.
>
> Colours are sampled by native generators. Extra episode-wide colour permutation is opt-in, not mandatory. Rotations/reflections always transform all demonstration and query grids consistently. Native solver validation occurs before augmentation: the augmented rule is `T f T^-1`, not necessarily the original direction-specific rule.

# ARC-AGI-2 procedural generator research

This fork adds a reference-guided generator workflow and an adaptive episode builder. Reviewed standalone additions extend `task_list.task_list()` without replacing upstream entries. Older constructive drafts remain in `arc_agi2.generators.registry` while conversion proceeds.

## Current evidence

- All **1,120** canonical tasks inventoried with saved Opus/Fable explanations, `transform(grid)` programs, provenance and separately labelled teaching fixtures.
- **891 existing upstream generators** reproduce the canonical pair sets (pair ordering can differ between releases).
- **196 new constructive implementations** have passed bounded validation, covering counting, selection, geometry, legends, relational motion, scaling, pattern construction and repair. Standalone conversion and review are tracked separately below.
- **Two variable-size extensions**: `0692e18c` (inverse self-tiling) and `00576224` (three-by-three tiling with mirrored middle band).
- All 198 constructors (196 new families plus two size extensions) passed **300 bounded randomized checks each**: 195 use the archived pair solver, `78332cb0` uses the documented complete-chain verifier, `de493100` uses the dimension-aware reflection verifier, and `269e22fb` uses a demonstration-conditioned episode verifier. Of these, 197 reproduce all original examples; `581f7754` uses the explicitly approved, hash-pinned eight-cell teaching correction. Its unchanged canonical replay is reported separately as 4/5, versus 5/5 on the teaching copy. Outputs are constructed independently from latent parameters. New pictures in `269e22fb` are compared with an independent contextual verifier; its original fixtures still match the archived fixed-picture transform.
- **22 additional fixed-size families / 111 size-parameter configurations** passed bounded 12-seed differential tests. Every such generated pair is checked again during generation. This is agreement evidence, not proof of semantic correctness.
- **33 tasks still need constructive generators**. A saved transform is not itself an input generator. Reference packets and `reports/generator-roadmap.csv` provide the task-by-task backlog.

## Inspect

[Interactive histogram and task browser](https://ritwika96-arc-episode-gallery.static.hf.space/coverage/index.html) · [All integer-size counts](reports/exact-size-histograms.csv) · [All rectangular-shape counts](reports/exact-shape-histograms.csv) · [Generator roadmap](reports/generator-roadmap.csv)

The report separates 1,000 training tasks from 120 public evaluation tasks, query grids from demonstration grids, and source coverage from candidate mechanism tags. The latter are overlapping lexical tags from teacher explanations, not gold semantic labels.

## Generate

Install Python 3.12+, numpy, pyarrow and huggingface-hub. From the repository root:

```sh
python -m unittest arc_agi2.test_pipeline arc_agi2.test_contextual arc_agi2.test_verified_rules -v
python -m arc_agi2.audit --workers 8
python -m arc_agi2.validate_parameters
ARCGEN_WORKERS=32 python -m arc_agi2.build_million
```

HF target: `ritwika96/arc-agi2-arcgen-1m-episodes`. Requires a write-capable `HF_TOKEN` in the environment. Use `--local` for no Hub writes and `--tasks ID ...` for a small test. `ARCGEN_TARGET_EPISODES`, `ARCGEN_POOL_SIZE`, `ARCGEN_FAMILY_SECONDS`, and `ARCGEN_BUILD_ROOT` configure generation. Master seed 20261021.

The builder first makes fresh pools of unique inputs, then allocates training/validation episodes adaptively by observed diversity. It targets the exact **query longest-side bins 1–30 jointly with output shape-change category** from all 1,120 tasks; it reports full height/width histograms too. It does not guarantee matching all joint dimensions or reasoning difficulty. Unsupported bins are published as shortfalls, never silently replaced by easy duplicates. A finite pool or unavailable size strata can leave the build below the 1.12M fresh-episode target. The fresh quota is capped at 1,000 per family and reduced for limited diversity; unsupported counts remain explicit shortfalls. Allocation and achieved counts are explicit.

Each episode contains three demonstrations and one query. Targets are output-grid JSON only. No solver code, reasoning or query labels are included in the prompt. All eight D4 transforms are emitted for each accepted fresh episode, with symmetric duplicates stored once and the represented transforms recorded in `equivalent_d4`. Optional palette mapping is simultaneous and shared. Fresh native episode hashes ignore demonstration order and augmentation. Parquet output is buffered in groups of 64 rows to avoid holding an entire augmented family in memory. Equivalent input grids under palette renaming/D4 are assigned to the same split globally before episode construction. All 1,120 tasks, including the former 20 holdouts, are training-eligible after validation. The historical flags remain provenance only. Public evaluation families used in training are no longer independent evaluations.

## Getting to full coverage

For each missing task:

1. Inspect original demonstrations and teacher explanation. Write a rule specification including counterexamples, object connectivity, parameter ranges and ambiguous cases.
2. Construct random valid latent scenes. Vary semantic parameters (object count, relations, graph structure, legend length, occlusion, path length, composition depth) as well as dimensions. Do not generate arbitrary noise and merely run the solver on it.
3. Derive outputs independently from those latent scenes and compare against `transform(grid)`.
4. Reproduce canonical examples; keep corrected teaching copies separate. Validate random and adversarial seeds across 1–30 grids, preserving task constraints.
5. Check demonstration identifiability against plausible alternative rules. Passing a solver check alone does not establish unambiguous episodes.
6. Report input uniqueness, size histograms, output-shape changes, difficulty proxies and new-input validation performance. Only then register the generator as training eligible.

Research extensions currently cover restricted constructive subfamilies. They do not claim every original edge case or a validated difficulty match. No generic image scaling is used to fake larger puzzles.

## Current model training plan

Use the user's eight H200 GPUs for full-parameter grid-only SFT. The main candidate is a pretrained 4B Qwen; compare a larger checkpoint before committing the full training budget. No model is launched by this repository. Tinker and rank-128 LoRA were earlier proposals and are superseded for this run. No hint, reasoning or Python-program target is included. If only a multimodal model's language component is used, report that component explicitly and verify all intended parameters receive gradients.

## Provenance and licensing

Upstream ARC-GEN is Copyright Google LLC and licensed Apache-2.0. This is an independent research fork. Canonical ARC task data retain their original attribution and licence; see `references/` and the official ARC-AGI-2 repository. Teacher packets are selected solution artifacts from our project, not full CLI conversations or credentials. Eight teaching fixtures are labelled corrected variants. Frozen replay provenance is retained; generalization of teacher code beyond supplied examples must be tested.

## Standalone task-file conversion campaign

User-requested upstream format: `tasks/task_<id>.py`, optional-parameter `generate(...)`, and `validate()` reconstructing original pairs through generator calls. Completed and reviewed entries are registered through `arc_agi2/task_registry.py` and included in `task_list.task_list()`. Drafts remain outside that registry.

First reviewed conversion: [`tasks/task_62593bfd.py`](../tasks/task_62593bfd.py). It reconstructs all four original pairs from latent objects and passed 1,000 new seeds. The CLI candidate report is in `reports/standalone/62593bfd.json`; its declared restrictions remain visible.

The authoring campaign uses eight concurrent Claude CLI processes under the user’s Max subscription; API credentials are removed from their environment and there is no API fallback. Every candidate is checked for original fixture reconstruction, valid grids, bounded execution, nonidentity examples, native input diversity and 300 fresh comparisons against the saved solver. Registration additionally requires review. Constructors generate new latent scenes rather than transformed copies of original examples.

A zero-error differential check is a bounded agreement test. It does not prove the saved solver is universally correct or that every original mechanism variant is covered.

**190 standalone modules are now reviewed and registered** (the exact list lives in `task_registry.py`). Each passed 1,000 seed checks and exact reconstruction of its approved validation fixture: canonical for 189 modules, the labelled teaching copy for `581f7754`. The first sixteen used seeds 0..999 (including their 300 author-validation seeds); the next one hundred and seventy-four used independent seeds 20,000..20,999. The regression suite also checks registered source hashes and seeds 10,000..10,019.

Twenty-four conversions replace earlier research constructors with the upstream task-file interface. The total is now 188 new constructive families, with 6 still awaiting standalone conversion/review. Remaining CLI drafts are authored and validated locally. Restricted shape and dimension ranges are documented per file and in `reports/standalone/`; the size-matching builder must respect those ranges.

Independent validation exposed a background-inference failure in the saved `d4c90558` solver: a thick frame can dominate a small grid, causing the checker to interpret the wrong colour as background. The constructor now samples the explicit domain where 0 strictly outnumbers every other colour. The failing examples are retained in `reports/standalone/d4c90558-counterexamples.json`. This restriction is not evidence that the conceptual counting rule fails on denser scenes.

Semantic review also corrected `e872b94a`: its generated walls must partition the background into N+1 connected regions, as every original pair does. Floating paths that merely satisfy the saved wall-count shortcut are excluded. The independent 1,000-seed check produced 998 distinct inputs (two repeats), so unique input count is reported separately from sample count.

Authoring used **Opus 5.5 via Claude Max CLI**, ultimately with sixteen workers; the subsequent 24-worker review pass has completed all 145 candidates. Host integration and an eight-worker coverage audit continue. Fable authoring was explicitly stopped; earlier completed artifacts remain archived and retain their original model attribution. API fallback remains disabled.

The first reviewed Opus 5.5 additions, `2ba387bc` and `4c3d4a41`, add two previously missing families rather than converting existing drafts. Both reconstruct all original fixtures and pass 1,000 independent seeds. Remaining missing family count at the current checkpoint: 101.


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

The exhaustive-expansion regression suite now has **26 passing tests**. It checks the eight-transform partition for every saved base episode, consistent transformations of demonstrations and query answers, symmetry deduplication including demo-order symmetry, separate fresh/expanded accounting, family quotas, and disjoint synthetic splits. No bulk generation or training was launched.

Four more reviewed additions bring standalone coverage to 87: `3e6067c3` (legend-labelled box paths), `409aa875` (pointer targets and collisions), `446ef5d2` (framed jigsaw assembly), and `4a21e3da` (marker-directed corner splitting). Each passed 1,000 independent seeds, exact fixture reconstruction, and 120 additional controlled examples. Host review added exact legend canvas controls, fixed partial jigsaw palette collisions, expanded jigsaw rectangles through side 24, and strengthened explicit geometry checks. Extra tests verify pointer shape-hit precedence, all four jigsaw anchors with colour-count preservation, repeated-label paths and correct two-line quadrant deletion. All 27 regression tests pass. Coverage is **984/1,120**, with **136 missing**.

Four additional reviewed modules bring standalone coverage to 91: `4acc7107` (nearest-partner stacking), `4b6b68e5` (closed-region dot voting), `4c416de3` (corner template stamping), and `4e34c42c` (overlapping connector assembly). Each passed 1,000 independent seeds and 120 targeted examples. Pairing cases distinguish nearest-neighbour choice from size sorting. Voting now includes closed regions with no votes. Corner checks cover asymmetric templates, multiple frames and depth 3 on small canvases. Assembly now mixes strips with procedural two-dimensional trees and fresh connector patterns; a conservative partial-assembly dominance check permits inferior partial overlaps while excluding winning alternatives. Its earlier dense-case failure is preserved in the review report. All 28 regression tests pass. Coverage is **988/1,120**, with **132 missing**.

Four further reviewed modules bring standalone coverage to 95: `4e45f183` (panel-position routing), `4ff4c9da` (plaid template reconstruction), `50f325b5` (hidden D4 template matching), and `53fb4810` (periodic striped extensions). Each passed 1,000 independent seeds and 120 controlled examples. Requested motif style now fails explicitly instead of silently switching; planted near-miss distractors survive cleanup. Plaid sampling now includes masked mirror cells requiring clean-row/column recovery. Extra checks cover all panel sizes and styles, 30x30 templates with three exact copies, four extension directions, and overwriting of fired strips. All 29 regression tests pass. Coverage is **992/1,120**, with **128 missing**. Bulk generation and training remain stopped.

Four further reviewed modules bring standalone coverage to 99: `54dc2872` (L-corner target alignment), `5545f144` (dot-eating animation), `5623160b` (objects pushed away from anchors), and `581f7754` (edge-marker alignment). Each passed 1,000 independent seeds and 120 targeted cases. Added exact long-path and large-mover controls; checks include 12-step walks, 19/24-cell movers, all directions, multi-key shapes and clipping. The saved `5545f144` prose omits two final test moves; generator validation follows the executable rule and canonical answer. All 32 regression tests pass. Coverage is **996/1,120**, with **124 missing**.

`fixture_policy.py` pins the original and approved corrected versions of `581f7754`. Canonical data is never overwritten; the gallery shows the changed demonstration outputs separately, and future episodes carry correction provenance outside the model prompt. Unapproved curated packets cannot silently replace canonical fixtures. The bulk-generation and training gates remain in force.

Four further reviewed modules bring standalone coverage to 103: `5833af48` (motif/pattern composition), `58490d8a` (legend-based object counts), `58f5dbd5` (negative glyph stamping), and `5961cc34` (beam relays). Each passed 1,000 independent seeds, exact canonical fixtures and 120 targeted cases. Requested 30x30 canvases are preserved. Counting now samples fresh procedural masks, including diagonal connectivity; glyph checks cover all four sides and disconnected/eight-cell masks. Beam checks cover exact zero through four hits with distractors. Documented native restrictions remain explicit. All 33 regression tests pass. Coverage is **1,000/1,120**, with **120 missing**. Bulk generation and model training remain stopped.

Four further reviewed modules bring standalone coverage to 107: `5a719d11` (paired-panel swaps), `5adee1b2` (legend-coloured exterior frames), `5b692c0f` (dot-guided symmetry repair), and `5dbc8537` (exact piece tiling). Each passed 1,000 independent seeds, exact canonical fixtures and 120 targeted cases. Explicit geometry checks now reject inconsistent layouts. Tiling has an exact piece-count control and rejects ambiguous coloured solutions; targeted 30x30 scenes exercised eight and twelve pieces, compound holes and all four frame sides. Other checks include invisible panel swaps, clipped frames, enclosed holes and addition/deletion symmetry repairs. All 34 regression tests pass. Coverage is **1,004/1,120**, with **116 missing**. Bulk generation and model training remain stopped.

Four further reviewed modules bring standalone coverage to 111: `6165ea8f` (D4 shape comparison tables), `6350f1f4` (noisy panel role swapping), `64efde09` (device-relative marker indices), and `65b59efc` (motif/map/paint composition). Each passed 1,000 independent seeds, exact canonical fixtures and 120 targeted cases. Shape comparison now supports exact areas up to 25 cells; checks include 2,096 equal-area unequal pairs and 219 reflection-required pairs. Sixty panel scenes had 40% noise. Device checks cover short templates, exact device/marker counts, all directions and reversed indexing. Every composition scene defeats a same-column shortcut. All 35 regression tests pass. Coverage is **1,008/1,120**, with **112 missing**. Bulk generation and training remain stopped.

Four further reviewed modules bring standalone coverage to 115: `66ac4c3b` (reflection between dotted lines), `67e490f4` (shape-class colour voting), `696d4842` (snake extension and tail repainting), and `6df30ad6` (nearest-marker recolouring). Each passed 1,000 independent seeds, exact canonical fixtures and 120 targeted cases. Hole generation now includes fresh procedural polyominoes: the audit exercised 114 non-catalogue classes and 322 holes with competing colours. Exact snake controls produced 244 corner-crossing tail repaints. Proximity controls cover 64/100-cell shapes with 32 markers and fix two-marker requests; canonical diagonal marker adjacency is preserved. All 36 regression tests pass. Coverage is **1,012/1,120**, with **108 missing**. Bulk generation and training remain stopped.

Two further reviewed modules bring standalone coverage to 117: `6e453dd6` (slide shapes to a divider and mark gapped contacting rows) and `71e489b6` (erase specks, then ring original zero holes). Both passed 1,000 independent seeds and 120 targeted 30x30 cases with exact canonical reconstruction. Sliding checks include 508 moving and 242 flush shapes, 11 gapped noncontact rows and a diagonal-connectivity adversary. Defect generation now includes attached specks, two-cell-thick regions and all four three-arm bridge orientations; targeted checks cover 360 attached bumps, 60 erased-then-ringed centres and 57 thin-region scenes. Explicit malformed scenes are rejected. The archived sliding rule is retained as a synthetic extension despite alternative rules that also fit the finite original examples; this ambiguity is documented. All 37 regression tests pass. Coverage is **1,014/1,120**, with **106 missing**. Sixteen subscription-only Opus 5.5 CLI workers are independently auditing the remaining staged sources; they do not automatically register generators. Bulk generation and training remain stopped.

Two further reviewed modules bring standalone coverage to 119: `6e4f6532` (multi-wall ship docking) and `6ffbe589` (legend-count layer rotation). Both passed 1,000 independent seeds, exact original fixture reconstruction and 120 targeted 30x30 cases. Docking now generates markers with multiple body neighbours and evaluates anchor priority after orientation; tests include all eight transforms, 212 reflection-required ships, 414 such markers and 837 partly satisfied competing orientations. Random short sides now include 13, checked with 24 original-regime scenes. Layer generation includes actual periodic dashes, all legend counts 1..9, complete cycles and optional four-way-distinguishable rotations. Tests cover 16/20/24-square outputs, 374 distinguishable rotated layers and 120 absent-legend layers; 24 extra all-cycle scenes preserve the cropped figure. Invalid bounds, palettes, transforms and impossible control combinations are rejected explicitly. All 38 regression tests pass. Coverage is **1,016/1,120**, with **104 missing**. Bulk generation and training remain stopped.

Three further reviewed modules bring standalone coverage to 122: `7491f3cf` (dot-selected panel routing), `753ea09b` (pocket filling) and `7666fa5d` (all-pairs diagonal bands). Each passed 1,000 independent seeds and 120 targeted cases. Panel routing now excludes whole-panel overlay shortcuts; checks exercise both wall overlay branches and dense 4x4 rings. Pocket generation adds outward attachments, bent rungs and along-strip spurs: 706 attached exterior cells are preserved, with 119 bent rungs and 202 edge-touching inside regions. Its original-grid replay path is explicitly separate and disabled during targeted random tests; opposite-edge procedural strips remain a documented restriction. Diagonal modes now require crossing or notch decisions: 119 targeted scenes defeat adjacent-only filling and 67 preserve consequential collinear gaps. Two initial forced-notch sampling failures were repaired with direct latent notch construction; the final 1,000-seed run passes. Extra checks cover 14x14/14x30/30x14 pocket grids and 6x30/30x6 eight-segment band grids. All 39 regression tests pass. Coverage is **1,019/1,120**, with **101 missing**. Bulk generation and training remain stopped.

### Shared-picture completion now uses complete episode context

`269e22fb` is now a fresh structured-picture generator, rather than recolourings/crops of one constant bitmap. The seven original fixtures still reconstruct the canonical 20x20 picture exactly. Fresh templates combine paths, outlined rectangles, filled blocks and staircases on 12..30 canvases, a labelled synthetic extension. Every episode shares one picture across three demonstrations and a query; each pair independently varies crop, orientation and colours, with a unique-placement check.

An independent string-matching verifier derives the picture from a supplied demonstration output. It receives no query answer or hidden template. The 1,000-episode test checks 4,000 pairs from 1,000 distinct native pictures with canonical lookup disabled: zero canonical-picture reuse, 2,310 boundary-touching crops, 1,690 internal crops and 826 minority-to-majority inversions. The builder preserves all four pairs together, verifies augmented episodes, limits fresh capacity to complete bundles and places both the picture and every crop equivalence class in one split. Incorrect answers and mixed-picture episodes are rejected.

Coverage is **1,020/1,120**, with **100 missing** and **123 reviewed standalone modules**. All **45 regression tests** pass. No bulk generation or model training was launched. The shape vocabulary is deliberately documented; passing these checks does not establish equal perceptual difficulty to the original drawing.

### Motif negatives and capacity distractors

`79369cc6` and `7acdf6d3` add two reviewed standalone families. Each passes its canonical fixtures, 1,000 independent seeds (20,000..20,999) and 120 targeted 30x30 scenes. Both now sample default grid sides up to 30. Motif construction includes protected false copies with an extra 6 in a required 4-position. Tests preserve 311 blocked near-copy regions, paint 1,752 cells in true copies and exercise all eight orientations and 88 edge clips. No corner clip occurred in the 120 random scenes, so 24 explicit corner cases were added and passed. Cup tests cover six candidates per scene, 60 capacity-near-miss distractors, 92 cases where the target is not the largest and 86 where it is not the smallest, plus 24 non-square cases. Strict controls reject malformed coordinates/counts/colours and ambiguous overlapping/interior-filler scenes. All 46 regression tests pass.

Coverage: **1,022/1,120**, **98 missing**, **125 reviewed standalone**. Bulk generation and training remain stopped.

A separate `78332cb0` counterexample shows that the archived greedy chain solver fails when the middle and last panels of canonical train[2] swap positions. The original data is unchanged. That candidate remains unregistered until its complete-chain verification is resolved; restricting generated reading order to hide the solver failure is insufficient.

### Complete-chain verification removes reading-order bias

`78332cb0` now samples freely shuffled panel chains with repeated contacts. The archived reference is preserved, but its first-match greedy step is disproven by a permutation of canonical train[2]. A separate verifier enumerates complete panel orders, requires exactly one connected chain using every panel, and reconstructs its strip. It uses no constructor state or expected answer. Canonical fixtures remain unchanged and both verifiers solve all five.

All 1,000 independent generator seeds pass the complete-chain verifier; **202 disagree with the archived greedy solver**, 342 use repeated contacts, 26 have non-adjacent repeat detours, 302 use a single shape colour and 72 contain full-line shape distractors. All 120 targeted greedy traps pass, including 60 six-panel cases with output long-side29. Tests cover every permutation and transpose of the canonical three-panel case, ambiguous-chain rejection, controls and the actual pair-pool builder using the stronger verifier. Generated targets still come from independently sampled latent chains; no canonical output was changed.

Coverage: **1,023/1,120**, **97 missing**, **126 reviewed standalone**. All **51 regression tests** pass. The 32-worker repair campaign finished with101 passes and5 held candidates; one of those five passed a separate independent-failure repair. The remaining four depend on unapproved curated fixture differences and have not been registered. Bulk generation and model training remain stopped.


## Graph routes, path unrolling and piece assembly

Registered `7b0280bc`, `7b5033c1` and `7b3084d4` after canonical replay, 1,000 independent seeds each and targeted mechanism checks. Explicit graph scenes now reject tied/disconnected/stroke-free routes. Path controls reject boolean or fractional values instead of coercing them. Assembly sampling filters impossible size requests before retrying and preserves ordered palette controls.

- Graph audit: 520 scenes independently reparsed into a touching-piece graph; all outputs agree. All keep unused nodes and strokes. 241/400 default networks have competing endpoint routes, plus 79/80 large cyclic networks.
- Path audit: 1,110 scenes independently walked. Of 1,000 defaults, 395 contain repeated nonadjacent colours, 207 defeat reading-order run sorting, and 352 include upward motion. Dense 8x8 length-30 paths and large/rectangular grids pass.
- Assembly audit: 200 targeted scenes, including 80 with 14x14 outputs inside 20x20 inputs and 30 explicit size-16 outputs. Ordered corner colours and rectangular inputs checked.
- All 97 adversarial parameter trials for these three modules pass after repairs. Published scope limits retain bounded graph layouts, biased random path growth and quadrant/tab assembly sampling; these checks do not establish exhaustive semantic coverage.

Coverage: **1,026/1,120**, **94 missing**, **129 reviewed standalone**. All **54 regression tests** pass. The 32-worker Opus audit campaign feeds eight local validators; ten additional Opus revision workers received concrete reference-disagreement cases. Nine audit-format failures were recovered from saved responses without more model calls. Bulk episode generation and model training remain stopped until coverage is complete.


## Count selection, band stamping and mirror occlusion

Registered `7bb29440`, `7c66cb00` and `7ed72f31`, each with canonical fixture replay and 1,000 independent seeds. Rectangle construction now rejects impossible five-box 10x10 requests by a lattice packing bound and separates special-cell blobs under eight-connectivity. The band constructor supports a single three-colour nest with three bands and rejects colliding explicit stamps. Mirror revisions enforce background dominance and type checks, while adding diagonal-only line contact and optional occlusion.

- 1,160 rectangle scenes independently parsed and cropped. In 1,000 defaults, 269 have a blob-counting decoy, 381 have a density decoy, 661 have a smaller rival, and 847 have a one-cell count near-miss.
- 1,240 band scenes independently re-derived from painted bands and object components. Included 160 forced three-colour nests, 60 at height20, and 80 four-band scenes. Default scenes contain 105 staggered colour parts; joint per-colour alignment is labelled as a synthetic extension.
- 1,240 mirror scenes independently reflected from their painted inputs. Default 800 scenes include 53 clipped and 48 occluded cells. The 300 forced-occlusion scenes include 115 occluded cells; original occupied cells stay unchanged. The 40-canvas-cells/object check is documented as a conservative sampler restriction, not an impossibility theorem.
- All 97 adversarial parameter trials pass for this batch; all 57 regression tests pass.

Coverage: **1,029/1,120**, **91 missing**, **132 reviewed standalone**. The 99-family audit and local execution are complete: 2,240 expected successes, 741 expected rejections, 118 unexpected acceptances, 28 reference disagreements and 59 unexpected failures in the original drafts. These labels need adjudication; they are not all proven generator defects. Fourteen concrete-counterexample revisions and a separate 32-worker/72-task parameter-repair campaign are staged for review. Task `de493100` is specifically held for host review because a repair removed variable-size support to match a size-specialized reference. Passing default checks does not approve that scope reduction. Bulk generation and model training remain stopped.


## Restoring variable-size mosaic reconstruction

`de493100` is now registered after resolving the scope regression in its staged repair. The archived solver uses mirror coordinate 31 for the original 30x30 crop. The synthetic constructor preserves the same two-cell crop geometry at even side N with mirror coordinate N+1. An independent verifier groups visible cells into reflection orbits, rejects inconsistent visible partners and reconstructs the masked patch without the latent quadrant or target. The eight cells needing a weak transpose fallback in original train[0] still reproduce exactly. Both archived teacher code and canonical grids are unchanged.

- 1,000 independent default seeds pass. All five original pairs match both the archived and reviewed verifiers.
- 2,260 targeted checks pass: 100 examples at each even side 12..30; 1,000 weighted defaults; 100 requested 1x1 masks; and 160 motif block-size, offset, palette and partial-diagonal controls.
- The archived solver disagrees on 868/1,000 balanced-size cases; the new verifier matches all 1,000. A concrete size 12 counterexample is saved in `reports/review-blockers/de493100.json`.
- All 34 original adversarial parameter cases pass after conditioning random size selection on requested mask dimensions. Explicit coordinate masks default to 30, preserving the original coordinate convention. Unsupported controls and corrupted visible symmetry are rejected.
- A real 24-pair local pool build retains multiple grid sizes and uses the reviewed verifier. All 61 regression tests pass.

Random masks still require direct visible partners: fresh examples do not yet require the weak transpose fallback. That limitation is explicit. Non-30 sizes are labelled synthetic extensions, not claimed to be uniquely established by the canonical data.

Coverage: **1,030/1,120**, **90 missing**, **133 reviewed standalone**. Bulk episode generation and model training remain stopped pending complete coverage and review.


### Branch-count decisions and clipped diamond rays (1,032 covered)

Registered `800d221b` and `80a900e0`, bringing reviewed standalone additions to 135 and missing families to 88. Both reproduce their canonical fixtures and pass 1,000 independent seeds. The branch constructor now rejects coerced fractional/boolean texture cells and waypoints, while preserving valid digit-string texture rows. An independent painted-input oracle checked 1,120 unique scenes: 934 defeat at least one of five shortcuts, including 82 attachment-count and 80 corridor-only counterexamples; 255 have a relative centre-count margin below 0.1. These frequencies are measured results, not guaranteed mixture quotas. One large six-patch case exceeded a concurrent three-second check; the same three seeds replayed correctly in 2.054, 0.089 and 0.413 seconds. No universal latency guarantee is claimed.

The diamond constructor passed 1,152 independent input-derived ray checks: 702 clipped scenes, 40 exact-four-badge controls, 80 rectangular controls and 32 explicit boundary controls. Default samples included 61 four-badge cases in 1,000. Rays arise from segment endpoints, not the middle cell, and preserve checker-zero cells. Original checker colours/phase, fully visible rings and nonintersecting rays remain documented restrictions. The canonical second test centre is `(14,12)`; a `(14,13)` typo in archived explanation text does not affect fixture reconstruction.

A separate 32-worker Opus5.5 CLI campaign is reviewing 84 revised candidates; eight local validators execute its proposed tests. It does not automatically register or publish candidates.


### Line-repair topology and gravity (1,034 covered)

Registered `7b80bb43` and `825aa9e9`: 137 reviewed standalone additions, 143 new families, 86 still missing. Both reconstruct every canonical example and pass 1,000 independent seed checks. Explicit line-repair controls now reject empty line systems, ambiguous diagonal roots, order-dependent rays and declared edits that contradict the visible structure; outputs remain constructed from latent edits. Its independent input-derived graph/ray audit passed 1,080 unique scenes, observing 1,060 loose chains, 503 escaping roots, 870 length-three ray fills with two-cell stairs and 248 interior isolated remnants. The latter are declared distractors. Larger gaps, free-end rays and T-junction repairs remain labelled synthetic extensions.

The gravity audit independently discovers ground and rigid objects, then computes drop distance from obstacle clearances rather than replaying the constructor's step loop. It passed 1,080 unique scenes, including 60 eight-object controls: 1,190 body-stacking events and 3,123 multi-cell bodies. It observed 55 cases of bodies touching ground laterally; this is a documented extension consistent with the saved program, not uniquely established by the original pairs. Ground-free scenes and more than eight explicit movers now reject. No fallback was used in the main audit. Separate width-three/eight-object controls used a singleton fallback once in five valid trials; an infeasible control rejected in 0.046 seconds. This limitation remains visible rather than being counted as rich shape diversity.

All 84 final Opus audit reports are saved, including two recovered without new model calls after the critic returned too many parameter cases. The local checks recorded 1,984 successful trials, 687 expected rejections, 47 unexpected failures, six unexpected acceptances and two output disagreements. Expectations are hypotheses requiring host adjudication. The two output discrepancies were sent to targeted Opus CLI repair workers, but both stopped at the Claude Max session limit (reported reset: 2:50pm Asia/Kolkata). No API fallback was used; saved drafts remain available for local review.


### Stencil identification and ring-path crossing repairs (1,036 covered)

The two output disagreements from the final parallel review were repaired locally after the Claude Max limit stopped their CLI revisions. Registered `bf45cf4b` and `8b7bacbf`, bringing reviewed standalone additions to 139 and missing families to 84. Each reconstructs all canonical pairs and passes 1,000 independent seeds.

Stencil stamping now conditions random tile dimensions on a supplied mask before drawing the tile and checks output bounds for every combination of explicit/random controls. A seven-row mask can use random tile heights three or four; an eleven-row mask cannot use a random tile of minimum height three and rejects. Tile identification requires a unique highest-ranked multicolour component spanning the full tile box. This rejects the detached-core counterexample while preserving identifiable disconnected interior islands. An independent painted-input stamping audit passed 5,521 unique scenes, including 500 partial-control cases, 100 full masks and 52 scenes with disconnected tile islands.

Ring fixture replay now verifies that every declared fill has a visible marker/path witness and that no reachable pockets are omitted. The normal generator still constructs targets from latent routes; the replay graph never supplies random-generation targets. Crossings now permit local contact around the crossed stretch while forbidding remote contacts and noncentral overwrites. In matched 200-seed forced-crossing trials, diagonal paths crossed by orthogonal paths increased from zero to 110; every revised output matched the archived verifier. All four orthogonal/diagonal orientation combinations occurred. Another 1,000 default scenes agreed with both the archived verifier and the replay graph, including 2,117 filled and 2,433 unfilled pockets; all 1,000 omitted-fill variants rejected. The graph shares conceptual rules with the verifier, so agreement is not an independent proof of universal correctness.

One critic probe was corrected from expected success to expected rejection because its proposed fill colour had no marker in the input. Original outputs and expectations remain archived. Revised parameter probes passed 18 successes/13 rejections for stamping and 22 successes/9 rejections for ring paths. Large requested ring counts remain bounded but not guaranteed constructible: 22 rings at 30x30 exhausted retries in 0.765 seconds, while 40 distractor rings reject immediately under the grid budget. Narrow native scope restrictions remain in the per-task reports.


### Compact legend layouts and shape matching — 845d6e51

The legend recolouring constructor now samples the narrow right-hand strips and compact heights found in the original demonstrations. Of 1,000 default scenes, 298 have two to five columns to the right of the wall and 47 have height 10 with wall row 3. This corrects a sampling restriction; canonical fixtures are unchanged. Malformed explicit shape lists and coordinates now raise ValueError consistently.

An independent matcher parses the painted input, enumerates rotations/reflections and recolours green components by the matching legend class. All 1,240 distinct scenes pass, including 927 equal-area class sets, 609 reflection-required scenes, 40 compact scenes and 40 requests for exactly 40 green shapes. The dense requests all succeeded; the hypothesised high-density failure was not reproduced, so the supported count was retained. A separate 1,000-seed archived-solver comparison passes, as do 29 successful and 10 rejected adversarial trials.

The legend remains at the top left with fixed semantic colours 0/3/5. Chiral mirror copies and grids larger than 18 are labelled extensions. All 72 regression tests pass. Coverage is **1,037/1,120**, with **83 missing**, **140 reviewed standalone additions**, and six older constructive modules awaiting conversion. Bulk generation and model training remain stopped.


### Border-region colour cycles — 880c1354

The border-colour constructor passed independent painted-input verification: components determine regions, polar-angle sorting recovers their clockwise order, and a predecessor-colour map predicts every output cell. All 1,240 unique scenes pass, including 40 trials each at 6x6/four regions, 6x7/four regions, 30x30/eight regions, 30x6/eight regions, 6x30/eight regions and an explicit six-colour cycle. No small-grid packing failure was reproduced, so those supported controls remain available.

Default scenes contain 113 two-region swaps, 373 three-region, 325 four-region and 189 five-region examples. Thus 887/1,000 defaults distinguish the direction of colour movement. The full audit includes 877 arcs crossing the usual top-left start and 633 scenes where zero is a region colour. Skeleton colours 4 and 7 remain unchanged.

The generator's morphology is broader than the finite staircase-wedge fixtures: 962 regions contain holes (1,682 enclosed cells), and 962 of the 1,240 scenes contain some 7 cells not directly adjacent to a region. These properties are documented rather than presented as original-fixture morphology. All non-8x8 sizes and counts above four are synthetic extensions. Explicit layouts check the rule's invariants without requiring the random sampler's one connected 4 body. A malformed first layout row now raises ValueError consistently.

A separate 1,000-seed reference comparison and all four canonical fixtures pass. Final adversarial checks report 26 successes and nine expected rejections. All 75 regression tests pass. Coverage is **1,038/1,120**, with **82 missing**, **141 reviewed standalone additions**, and six older constructive modules awaiting conversion. Bulk generation and training remain stopped.


### Slab assembly and rejection-sampling bias — 83eb0a57

The constructor now retains the initial piece count through rejection retries instead of repeatedly redrawing it. On the same 1,000 default seeds, one-piece scenes change from 400 to 162 and four-piece scenes from 25 to 165. The corrected count histogram is 162/365/308/165 for one/two/three/four pieces. This removes a bias toward simpler, easier-to-pack scenes without lowering the supported count.

An independent painted-input verifier extracts solid rectangles, sorts by area and computes all signed colour-match scores through NumPy windows. All 1,073 distinct audit scenes have unique intended alignments and correct outputs. Positive-match-only placement produces wrong final outputs in 306 scenes; ascending-area placement fails in 375. The audit includes 372 nested-footprint scenes, ten tight 18x18 four-piece nested decoys and twenty 18x30 two-piece nonnested decoys. All requested controls succeeded.

One critic expectation was overturned with evidence: an explicit offset (0,1) defines the host's keys at that offset, so the critic's assumed correct location (1,1) is not applicable. The independent scorer recovers (0,1) uniquely. The original audit remains archived, and the retest records the override. Explicit partial overlap and six-piece construction also pass independently, so those valid extensions are documented instead of prohibited. Malformed patterns and piece containers now reject with ValueError.

The single-piece sampler still has no unrelated host-only keys; random patterns use blocks, lines, rings and single cells, and input sizes 18..30. These limits are reported. A separate 1,000-seed reference comparison, all four canonical fixtures, and the final adversarial retest (21 successes, eight expected rejections) pass. All 79 regression tests pass. Coverage is **1,039/1,120**, with **81 missing**, **142 reviewed standalone additions**, and six older constructive modules awaiting conversion. Bulk generation and training remain stopped.


### Legend sliding: wall markers must not consume pillars — 88e364bc

The original candidate selected wall markers from both outline rings and interior pillars. On 80 forced wall-marker-plus-pillar trials it consumed a pillar in 24 cases, and in two cases removed every pillar. The revised constructor restricts candidate starting cells to the outline ring while keeping pillars in the obstacle set. All 80 matched-control trials retain every pillar and include an actual outline marker.

An independent input-only verifier decodes the visible two-tail-cell arrows, finds the enclosing background component and outline colour, and computes each unobstructed ray prefix with diagonal side-cell checks. All 1,160 distinct scenes pass, containing 5,577 markers and 496 corner-guard stops across all eight directions. Controls include forty 16x16 diagonal wall-marker scenes without pillars and forty 30x30 multicolour scenes with touching outlines, pillars and wall markers together.

Explicit replay now rejects missing/empty marker sets and a marker starting on another marker's path. Malformed unhashable colours reject with ValueError. All five canonical pairs still reconstruct exactly. Documentation now states the two-outline-per-colour cap below 500 cells, touching versus shared-wall semantics, and the limits of explicit replay's trusted direction annotations. Generated regions have a single bordering legend colour; this does not cover multi-colour boundary-majority inference.

A separate 1,000-seed archived-solver comparison and 30 successful/six rejected adversarial trials pass. All 82 regression tests pass. Coverage is **1,040/1,120**, with **80 missing**, **143 reviewed standalone additions**, and six older constructive modules awaiting conversion. Bulk generation and training remain stopped.


### Snake routing: make the target reading unambiguous — 88bcf3b4

The original sampler guaranteed nearest-target uniqueness only for Chebyshev distance from the anchor. An independent audit of 500 original grids found 174 of their 785 snake scenes choose different nearest targets under plausible alternate readings. The revised random sampler requires the same unique target under Chebyshev, Manhattan and squared-Euclidean distance, each measured from the anchor, line end and whole snake. This is a synthetic ambiguity filter, not a claim that the finite original fixtures establish one particular distance convention.

Input-only component parsing and direct three-phase path reconstruction pass on 1,220 distinct grids with 2,058 snake scenes. All nine target readings agree in every scene. The audit includes 267 clipped snakes, 915 distractor objects, all eight direction/side combinations and sixty requested 30x30 three-scene layouts. The sampled count now persists through retries, replacing both repeated count draws and the late one-scene fallback. Default count frequencies are 527/308/165 for one/two/three scenes. Explicit count requests retain bounded packing attempts; the deliberately infeasible 7x7/three-scene check raises RuntimeError in 0.87 seconds.

The sampler retains and labels 26 later hug segments crossing the line axis and 119 orthogonal line-target contacts as synthetic geometries. Under-specified slack approaches remain excluded. Explicit replay now checks required fields, cell shapes, duplicates, connectivity and overlaps, while target assignments remain caller-provided. All seven original fixtures reconstruct unchanged.

A separate 1,000-seed archived-solver comparison, 30 successful/seven rejected adversarial trials, and all 85 regression tests pass. Coverage is **1,041/1,120**, with **79 missing**, **144 reviewed standalone additions**, and six older constructive modules awaiting conversion. Bulk generation and model training remain stopped.

### Overlapping frames: visible evidence and iterative reconstruction

`89565ca0` adds a reviewed constructor for counting compartments in occluded frames and ordering equal counts by visible layering. Explicit scenes now obey the same reconstruction check as random scenes: a counterexample with a completely hidden five-cell divider is rejected instead of emitting an answer unsupported by its input. All four canonical fixtures and their 17 frames remain readable and unchanged. Frame count is sampled once per scene and retained across construction retries, avoiding a retry bias toward fewer frames.

The independent input-only audit checks 1,180 unique puzzles: a single-cell-only bridge baseline fails on 1,179; a one-pass baseline fails on 1,072; 400 puzzles contain visible count ties. Reconstruction takes up to five passes. All 90 five-frame boundary cases (14x22, 22x14 and 18x18) succeed, with maximum measured generation time below 0.066 seconds. A separate 1,000-seed archived-solver comparison passes, as do 23 successful parameter calls and eight expected rejections. All **88 regression tests** pass. Native compartments remain banded rectangles, with at most one tied pair; broader explicit geometry must still be readable. These are bounded semantic checks, not proof of complete support.

Coverage is **1,042/1,120**, with **78 missing** and **145 reviewed standalone additions**. The requested CLI concurrency is 48 Opus 5.5 workers; the current subscription-limit state has zero generator workers running and no API fallback. Bulk generation and model training remain stopped pending full reviewed coverage.

### Scaled pieces and combined glyph evidence

`898e7135` adds scaled polyomino-piece assembly. Scale is retained across rejected scene attempts instead of being redrawn toward easier layouts: the 1,000 default samples contain 674 scale-two and 326 scale-three scenes. An independent 1,240-puzzle audit checks actual block scaling, board identification, D4 shape matching and noise removal. It includes 487 equal-area shape competitions, 317 reflection-required scenes, 627 repeated-class scenes and 262 scenes with noise inside concave piece boxes. All 90 minimum-canvas trials at scales two, three and four succeed. Valid explicit one-class layouts, larger noise blobs identified by isolated dots and a fitting scale-five scene remain supported rather than being artificially excluded. Native scale-four shapes are explicitly labelled easier; no claim is made that every puzzle needs shape discrimination.

`8a6d367c` adds partial-hint glyph selection and coarse-grid completion. Distractors that contain the entire target are rejected early because no positive hint subset could distinguish them. Explicit malformed rows, coordinates, containers and noninteger controls now reject consistently. Of 1,240 unique independently decoded samples, 794 require joint evidence from multiple hints, 940 contain close distractors, 1,124 contain disconnected glyphs, 352 use rectangular coarse cells and 139 use zero as the fill colour. Tight six-glyph/six-hint controls, unit cells and six-pixel cells all pass. Upper-row glyphs with a lower frame remain the declared native layout.

Both modules reproduce their unchanged canonical fixtures and pass another 1,000 independent seeds each. Critic parameter rechecks give 52 successful calls and 16 expected rejections. All **92 regression tests** pass. Coverage is **1,044/1,120**, with **76 missing** and **147 reviewed standalone additions**. Local coverage auditing now uses 16 processes. Claude CLI remains quota-limited; no API fallback, bulk generation or model training is launched.

### Vertical symmetry: construct and teach tied axes

`8e5c0c38` now reconstructs all four original pairs from explicit symmetric cores and stray cells. The old full-input replay is no longer used by `validate()`. This includes the genuine tie in test 1: its intended core uses the leftmost of equally scoring vertical axes. Explicit latent validation accepts that rule rather than requiring artificial uniqueness.

Fresh generation adds a separately labelled tied-axis family, selected per shape with `tie_rate` (default 0.2; zero and one force unique-only or tied-only regimes). Each row has two latent core cells and one stray arranged so two vertical axes tie and no earlier axis wins. Row positions, dimensions and placement vary; this is a synthetic morphology, not a claim to cover every possible tied shape. Ordinary split cores are now kept as two components after stray growth; the earlier sampler merged seven of 574 split cores in a 1,000-scene audit.

With replay disabled, an independent row-pair-sum audit verifies 1,240 unique scenes: 841 tied shapes appear in 603 puzzles, and the rightmost-tie alternative fails on all 603. Bounding-box-centre mirroring fails on 1,146 puzzles; 798 contain a shape whose horizontal symmetry scores better than its required vertical symmetry. All 515 ordinary split cores retain two components. Forty tied 8x8 single-shape scenes, forty tied 30x30 four-shape scenes, unique-only, rectangular and horizontal-decoy controls pass. The separate 1,000-seed reference check and 24 successful/eight rejected critic parameter calls also pass. JSON replay keys and malformed latent containers now have explicit validation.

All **95 regression tests** pass. Coverage is **1,045/1,120**, with **75 missing** and **148 reviewed standalone additions**. Local audit uses 16 processes. No bulk generation or model training is launched.

### Sliding-slot contact decisions and shape-count tallies

`8b9c3697` adds a reviewed comb-slot constructor. An independent coordinate-projection collision audit verifies 1,200 unique scenes, including 2,363 accepted pieces and 7,262 discarded pieces. Omitting bounding-box containment changes 931 outputs; omitting the endpoint-width check changes 941. All four directions, inside-slot starts, long trails and forty 14x14 minimum cases occur. Explicit full-depth fills, too-deep pieces, overhang contacts, narrow/wide pieces and a rejected piece inside a successful piece's path match the rule. Random exclusion of overly deep aligned pieces and path-sharing reds remains documented; valid broader explicit scenes are retained.

`8f215267` adds frame-colour shape counting and spaced dot tallies. The 1,180-puzzle independent audit includes 579 scenes with empty frames, 622 with a full-capacity frame, 800 with distractor colours and 992 with differently sized shapes sharing a frame colour. Tests include seven short frames, zero counts, exact capacities, narrow/tall canvases and 27-column frames. List controls now reject malformed/unordered inputs cleanly; the documented maximum is seven frames, with six/seven requiring frame height three. Larger partially filled bordered shapes remain valid counted objects, rather than being confused with hollow frames.

A deliberately dense custom request for two 27x9 frames with counts `[12,12]` succeeds on four of five seeds; one exhausts the bounded retry budget. It is neither claimed universally reliable nor rejected as geometrically impossible. The default distribution and declared targeted suite pass. Each module also passes unchanged canonical reconstruction and 1,000 independent archived-solver checks. Critic parameter rechecks give 46 successes and 16 expected rejections. All **99 regression tests** pass.

Coverage is **1,047/1,120**, with **73 missing** and **150 reviewed standalone additions**. Bulk generation and model training remain stopped; local coverage auditing uses 16 processes.


## Reachable boundary review — 2026-10-20

Registered `8f3a5a89`: bottom-left marker reachability, whole-object survival/erasure, and framing only surviving objects connected to the grid border. The standalone constructor reproduces all four canonical examples from latent rectangle unions. Native scenes mix absent, line, corner and box separators, with border and floating shapes on 10..30 grids; dimensions above 20 are labelled synthetic extensions.

Fixed separator bulges growing into the unreachable side (212/1,000 fixed-line probes before repair, zero after), validated explicit rectangle bounds before allocation, and retained the selected separator mode through failed proposals. Corrected the empty-pocket documentation to describe placement attempts rather than accepted proportions.

An independent input-component oracle agrees on 1,280 distinct scenes: 623 erase objects, 981 contain unframed floating survivors, 1,055 distinguish whole-object survival from per-cell erasure, and 784 distinguish the marker from a wall. Four canonical and four additional explicit scenes also pass. Forced 10x10 box scenes succeed in all 40 trials but predominantly erase singleton objects; that diversity limitation remains explicit. The final critic parameter suite gives 27 successes and 7 intended rejections. Another 1,000 independent seeds agree with the archived solver.

All 102 regression tests pass. Coverage is **1,048/1,120**, with **72 missing** and **151 reviewed standalone additions**. Bulk generation and model training remain stopped. Local audit parallelism is 16 processes; the requested 48 Opus CLI workers are inactive until the subscription quota resets.


## Noise triangles and ordered legends — 2026-10-20

Registered `902510d5` and `9385bd28`, with all eleven canonical pairs reconstructed and 1,000 independent solver checks each. Four new regression tests bring the suite to 106 passing tests.

For `902510d5`, the largest 8-connected figure is preserved while the remaining non-corner pixels determine a corner triangle's size and colour. The figure now scales with larger grids instead of remaining a small motif on an empty canvas. In 40 matched 30x30 trials, the mean figure grew from 12.225 to 85.65 cells and input occupancy from 2.06% to 10.22%. The revised figures remain connected, avoid filled 2x2 blocks, and preserve all fixture rules. An independent input-only audit covers 1,280 distinct pairs, including 746 cases where counting noise components instead of individual pixels is wrong, 707 with figure-coloured strays, and 246 where incorrectly including the corner marker creates a colour-vote tie. Malformed explicit containers now raise ValueError. The critic parameter suite has 23 successes and nine intended rejections.

For `9385bd28`, a two-column legend controls fills, reservations and erasures of rectangles marked by corner pieces. Added `require_erase_first`: this controls whether the scene must distinguish erasing all marked pieces before any fill from erasing at each legend row. It is retained across retries and scheduled for 25% of default calls whose background is not fixed to zero. Forced minimum and large-grid cases all succeed. The independent 1,320-pair audit contains 1,072 order-sensitive, 324 reservation-sensitive, 402 erase-first-sensitive and 283 original-input-key-lookup-sensitive examples. Among 1,000 defaults, erase-first is decisive in 287. Explicit scenes now reject an undetectable legend or non-dominant background. All 30 critic parameter trials pass. Distractor overlap and individual matches to area-sorted alternatives remain measured, documented scope rather than hidden assumptions.

Coverage is **1,050/1,120**, with **70 missing** and **153 reviewed standalone additions**. No bulk generation or model training was launched.


## Bracket mirrors and marker-directed orientation — 2026-10-20

Registered `93c31fbe` and `94133066`. Both preserve all four canonical examples and pass another 1,000 independent solver checks. All 110 regression tests pass.

For `93c31fbe`, an input-only bracket detector checks local reflection along the longer frame axis and erasure outside frames. The audit covers 1,240 generated pairs (1,239 distinct), 3,678 frames, 1,866 wide and 1,812 tall. All pairs distinguish the wrong mirror axis, and 1,216 distinguish rotation instead of reflection. In 813 scenes, stray marker cells touch a bracket; per-colour segmentation still identifies the frame correctly. The generator now retains its chosen frame count through retries. A random tiling constructor handles narrow packing after 50 failed free-placement attempts, preserving requested counts; it was used in 72 audit scenes. A separate single-marker/no-stray pattern fallback remains documented but was never used in this audit. Explicit scenes with output-dominant markers and more than five frames remain supported. Thirty critic parameter trials pass.

For `94133066`, panel dimensions and orientation are chosen from analytically feasible layouts before random placement. Fixed dot starts constrain panel-position intervals, and the perpendicular axis must fit the transformed dot span. This fixes false rejection of valid small canvases. Thirty trials each for square canvases 11..16, 7x11, 11x7, narrow large panels and partial position/size controls all succeed. An independent NumPy oracle enumerates all eight transforms and requires exactly one pairwise marker-order match on 1,440 distinct pairs. The audit includes 607 output-shape changes and 1,205 nonsquare panels. A shape enclosing a small pocket could previously outgrow the border-connected panel object despite a larger total count of panel-colour cells; the generator now rejects that case using connected-component sizes. All 36 critic parameter trials pass.

Two teacher-prose errors were corrected in `references/94133066.json`: the third training example is `flip_v`, and the query is `anti_transpose`. Independent canonical enumeration confirms these exact transforms. The original explanation is preserved verbatim in `original_teacher_explanation`; the labelled correction leaves the puzzle grids, solver code, source artifact hashes and provenance unchanged.

Coverage is **1,052/1,120**, with **68 missing** and **155 reviewed standalone additions**. Bulk generation and training remain stopped pending complete coverage.

### Anchor-based reflection review — 2026-10-20

Registered `963f59bc` after five exact canonical pairs, 1,000 independent archived-solver checks and 1,320 input-only displacement checks (1,317 distinct pairs). The original random path admitted axis-symmetric shapes on2/1000 seeds, allowing a rotation shortcut, and never sampled sides28..30. Both axis symmetries are now excluded from sampled shapes and each feasible canvas side samples through30. All1,320 tested scenes distinguish anchor-centred rotation;1,162 distinguish anchoring at the facing bounding-box edge. Explicit clipping and canonical symmetric/edge cases are preserved. Four8x8-shape copies fit on26x26; narrow and minimum grids pass targeted trials. Final critic cases:22 successes,11 intended rejections. Malformed containers reject cleanly. All112 regression tests pass.

Coverage is **1,053/1,120**, with **67 missing** and **156 reviewed standalone additions**. Scope restrictions, accepted-distribution caveats and finite validation limits remain in the task report. No bulk generation or model training launched.

## Containment erasure — 9720b24f

Registered after five exact canonical pairs, 1,000 independent archived-solver checks and 1,360 distinct input-only oracle checks. The rule erases a monochromatic eight-connected object inside the bounding box of a strictly larger, differently coloured object. Zero remains background even when it is not modal. Open outlines and objects touching the bounding-box border are retained as meaningful cases.

Default supported canvas sampling now reaches 30 cells, and default loose-object targets reach ten; the earlier target stopped at five despite nine loose objects in the canonical query. Optional `num_loose` requests an exact count from zero through twelve, with bounded failure on unsuccessful placements. Forty 30×30 cases each with nine and twelve loose objects passed. Default placement remains best-effort on crowded scenes; no uniform accepted-distribution claim is made.

The independent audit distinguishes four-connected grouping in 1,060 scenes and closed-outline flood fill in 962. It includes 1,181 scenes retaining and erasing objects of the same colour, 1,900 kept objects straddling a larger bounding box, and 56 scenes with nonmodal zero background. Explicit same-colour and equal/larger-size exceptions, cut-corner containment and valid identity cases are tested extensions; their full range is not claimed for native random generation. Final critic parameter retests had 26 successes and eight intended rejections. All 115 regression tests pass.

Coverage is **1,054/1,120**, with **66 missing** and **157 reviewed standalone additions**. Bulk generation and model training remain stopped pending complete reviewed coverage.

## Rowwise relocation — 984d8a3e

Registered after three exact canonical pairs, 1,000 independent archived-solver checks and 2,609 distinct input-only checks. Each row moves cells from its left-colour run against its right-colour run, filling as much as available toward the globally leftmost right-run boundary. An independent oracle performs cell deletion/reinsertion and checks per-row colour conservation and unchanged right blocks.

Default dimensions now reach 30 cells. Fixed left-run cap nine and right-edge spread seven were removed, allowing the actual features to scale with width. The audit includes 1,000 defaults, all 783 supported rectangular dimensions, 100 large scenes, all 720 ordered three-colour palettes, three canonical pairs and three explicit extensions. It observes 2,725 rows with left runs longer than nine, 399 scenes with right-edge spread greater than seven, and 184 scenes distinguishing anchors that have no left run. That last rule distinction is labelled a synthetic extension consistent with the archived explanation, not uniquely established by canonical fixtures.

The minimum width-four sampler remains structurally limited and documented; valid explicit width-three profiles are preserved. Profiles require strict border-colour majorities and at least one moved cell. Fifteen malformed/infeasible controls reject deliberately; critic retests have 29 successful reference matches and seven intended rejections. All 117 regression tests pass.

Coverage is **1,055/1,120**, with **65 missing** and **158 reviewed standalone additions**. Bulk generation and model training remain stopped pending complete reviewed coverage.

## Demonstrated colour-to-motif lookup — 98c475bf

Registered after five exact canonical pairs, 1,000 independent archived-solver checks and 1,745 independent scene checks (1,738 unique inputs). The verifier extracts motif shapes from demonstration grids; it does not import the generator's fixed template dictionary. Tests cover heights12..30, all five motif colours, one through four marker pairs, and100 tight height22/four-marker cases. Width20 and the five native templates are retained because absolute horizontal coordinates and colour-specific shapes define the observed rule.

Pair correctness is insufficient for this family. Query marker colours must have their shapes shown in demonstration inputs or outputs. In1,000 verified three-demonstration episodes,367 candidate demonstration sets lacked necessary evidence and were rejected. The active episode builder now applies this context check before D4/palette augmentation, counts missing-evidence attempts, and raises on disagreement with the constructed answer. It never passes query labels to the context solver. The verifier is included in the pool source fingerprint. Native colour-to-shape mappings remain fixed, so these checks do not establish freedom from memorization.

The builder regression proves an unsupported pool emits zero episodes; adding a demonstration of the missing colour permits an episode and its augmented versions. Other tests establish that changing query labels cannot change the context solver's answer and conflicting demonstration templates are rejected. Malformed containers now raise ValueError; the impossible four-marker height21 request rejects immediately. Critic retests have26 successful reference matches and10 intended rejections. All120 regression tests pass.

Coverage is **1,056/1,120**, with **64 missing** and **159 reviewed standalone additions**. Bulk generation and model training remain stopped pending complete reviewed coverage.

## Marked stack arithmetic — 9aaea919

Registered after four exact canonical pairs, 1,000 independent archived-solver checks and 2,337 unique input-only component checks. A red bar recolours its source stack grey; a green bar extends its target by the total number of shapes in red-marked stacks. Marker bars disappear. The independent audit counts connected shapes and copies the observed shape mask, without reading the generator's latent heights.

The inferred column count now respects a supplied width and offset, including feasible two-column layouts that previously failed. Stack-height sampling uses the canvas capacity instead of fixed caps of three for sources and four for targets/distractors. The audit covers 968 fitting size/column-count combinations, 200 partial-width calls, 20 partial-offset calls, 140 palette cases and explicit extremes. It observes 606 sources above height three, 36 targets above height four and 445 distractors above height four.

Across target columns, 2,442 checks distinguish adding one, 2,250 distinguish counting source markers, 2,475 distinguish doubling the target and 1,025 distinguish using only the tallest source. Multi-target scenes give each target the complete sum; this and three/four-source scenes are labelled synthetic extrapolations. The canonical two-source sum uses query-answer evidence, and individual low-capacity scenes need not disambiguate every alternative rule. Shape mask, spacing, pitch and bottom marker placement remain fixed.

Sixteen malformed/infeasible controls reject deliberately. Critic retests have 22 successes and nine intended rejections. All 122 regression tests pass.

Coverage is **1,057/1,120**, with **63 missing** and **160 reviewed standalone additions**. Bulk generation and model training remain stopped pending complete reviewed coverage.

## Cross-panel defect repair — 9b5080bb

Registered after four exact canonical pairs, 1,000 independent archived-solver checks and 1,356 distinct input-only scene checks. The independent oracle enumerates rectangles from corner presence and legal defect positions, rather than reusing the archived majority-count boundary estimator. It verifies 3,706 shapes, 4,228 notches, 3,615 bumps and 15,686 changed cells; every repair is a two-cell bar painted with the other panel's colour.

A palette-validation defect could previously paint None into a panel when frame and shape colours were fixed. Such controls now reject explicitly. Fifty trials each cover minimum 8×14, narrow 12×30 free layouts, wide/tall split layouts, large free/split layouts and a fixed palette. Minimum layouts took at most seven retries and narrow-free layouts at most twelve in these tests. At 8×14 each panel necessarily held one shape in the sample, but twelve rectangle dimensions occurred. There is no claim that small canvases support the multiplicity of larger ones.

In 843 scenes a repaired bar touches a foreign colour while its cells remain in their own panel. This corrects the critic's claim that all foreign-colour adjacency is excluded. Adjacent notches, 12×12 rectangles and scenes without visible frame remain valid explicit extensions, separately documented from native sampling. All four defect directions and 376 overlapping panel-box cases were observed. Eleven invalid controls reject; critic retests have 20 successful reference matches and 10 intended rejections. All 124 regression tests pass.

Coverage is **1,058/1,120**, with **62 missing** and **161 reviewed standalone additions**. Bulk generation and model training remain stopped pending complete reviewed coverage.


## Dotted-path connectivity review — 2026-10-20

Registered `9ba4a9aa`: follow the colour of the first dot from a checkerboard through connected dotted paths and extract the reached ring. Added disconnected same-colour tails behind a different-colour barrier, so colour matching alone can select a wrong ring. This is a labelled synthetic extension with an explicit `disconnected_decoy` control. Random scenes now receive post-construction target and solid-window checks.

All four canonical pairs replay exactly; 1,000 independent random inputs agree with the archived solver. A separate input-only box detector and union-find connectivity audit passes 1,693 distinct scenes, including every supported height/width combination from 14 to 30. Of those scenes, 1,024 contain a same-colour decoy; 480 of 1,000 defaults contain one. Forced decoys work at every supported shape. Ten invalid controls reject, and the critic-case retest records 29 successful calls and eight intended rejections.

The random generator covers spaced tree layouts with optional non-main continuation beyond the target; it does not claim arbitrary cyclic graph coverage. Ring count and walk length remain sampled controls. The full regression suite passes **126 tests**, including a disconnected-target counterexample and forced decoy checks at 14×14 and 30×30.

Coverage is **1,059/1,120**, with **61 missing** and **162 reviewed standalone additions**. Six older constructive drafts still need standalone conversion and review. Bulk generation and model training remain stopped pending complete reviewed coverage.


## Chiral marker reflection and size scaling — 2026-10-20

Registered `9bebae7a`: decode the long arm of a magenta T or asymmetric cross, rotate that direction by 90 degrees, erase the marker and reflect the yellow figure into the adjacent bounding box. The rule is chiral; the four additional marker orientations are defined by rotation equivariance. Colours stay fixed at 0/4/6.

The original draft capped figure boxes at 7×8 even on larger grids, and a 100-case independent probe found five examples also solvable by a half-turn. The revised sampler scales figure extents with available canvas space and requires asymmetry about both axes. It retains broader explicit patterns for canonical reconstruction and deliberately labels their weaker symmetry requirement. Invalid arm containers and impossible coordinates now reject promptly; basic axis constraints are checked before placement search.

All six original examples match exactly. Independent marker-arm decoding and coordinate reflection pass **2,233 distinct scenes**, including all 625 shapes from 6×6 to 30×30, 400 large scenes covering every marker orientation, 100 extreme-size repeats and 100 partial-position controls. All **2,225 random cases** defeat both translation and 180-degree-rotation shortcuts. The two broader explicit controls intentionally need not defeat rotation. Figure extents reach 30 cells and 222 yellow cells; 782 scenes exceed the old extent caps. Copies overwrite marker cells in 996 scenes. Nineteen invalid controls reject; all 19 valid and nine rejection cases from the critic retest pass.

The new source also passes 1,000 independent seeds against the archived solver. The regression suite passes **128 tests**. Coverage is **1,060/1,120**, with **60 missing** and **163 reviewed standalone additions**. Six older drafts still await standalone review. Bulk generation and model training remain stopped pending full coverage.


## Projectile splitting with geometric decoys — 2026-10-20

Registered `9f669b64`: select the projectile that hits a target with equal positive side margins, split that target, and move the projectile flush to the destination edge. The revised constructor scales projectile size, target thickness, margins and gaps with the canvas. Lateral twin, isolated and nonrectangular decoys prevent selecting the middle of three collinear objects as a shortcut. Explicit two-object scenes are a labelled broader API case.

All four canonical pairs and 1,000 independent archived-solver checks pass. A separate geometric oracle passes **2,754 targeted cases with 2,752 distinct inputs**: these include all 700 supported up-direction rectangles, 200 minimum-size repeats, forced decoys in all four directions, large geometry and fixed colours. There are 1,044 lateral-decoy scenes; projectile width and length each reach ten, and target thickness reaches twelve. All 22 invalid controls reject promptly; the critic retest passes 23 valid and nine rejection cases. The sampler still requires a unique valid projectile-target pairing and does not cover arbitrary occlusions.

The full regression suite passes **130 tests**. Coverage is **1,061/1,120**, with **59 missing**, **164 reviewed standalone additions**, and six older constructors still awaiting standalone review. Bulk generation and model training remain stopped pending full coverage.


## Corridor traversal with leftward and three-turn routes — 2026-10-20

Registered `9bbf930d`: release a marker only when the neighbouring bars share both colour and starting coordinate and its exit cell is clear. Traverse background corridors, turning only through a unique valid flanked opening, and place the marker at the endpoint. The earlier sampler never generated leftward travel or three-turn routes even though those occur in the canonical task. The revised latent designs include both, with a public `zigzag=True` control, and now support one through seven released markers.

All four original examples reconstruct exactly and 1,000 independent archived-solver checks pass. An independent event-jump verifier passes **2,085 distinct scenes**, including all 210 supported canvas shapes with and without forced zigzags, minimum-height layouts for every supported marker count, and 100 large dense seven-marker zigzags. Across 5,542 routes, 1,062 travel left and 1,004 have at least three turns; the longest measured route has 67 steps. Tests include 678 fork stops, 2,071 equal-colour/different-start negatives and 1,234 blocked exits. Seventeen invalid supported controls reject promptly. The critic's unsupported palette keyword correctly raises Python TypeError, recorded separately from its six ValueError rejections and 29 valid controls.

Random canvases remain width10..30 and odd height11..29, with disjoint paired bars and at most three turns. More general canonical topologies are explicitly replayed, not claimed as fully randomized. Dense requests may require bounded retries and simpler local routes after400 attempts, while preserving a forced zigzag; the measured maximum was430 attempts and0.055seconds. These scope limits remain published.

The regression suite passes **132 tests**. Coverage is **1,062/1,120**, with **58 missing**, **165 reviewed standalone additions**, and six older constructors still awaiting standalone review. Bulk generation and model training remain stopped pending full coverage.


## Symmetry, motif anchors and multi-legend instructions — 2026-10-20

Three more reviewed generators are registered. Each reconstructs every canonical pair and passes 1,000 independent seeds against the archived input-only solver.

- `a09f6c25` recolours connected glyphs by symmetry and erases isolated noise. Slot-conditioned packing fixes dense 14×14 scenes with nine glyphs. A separate coordinate-symmetry oracle passes **1,756 distinct scenes**, covering every supported rectangular size, maximum counts, all backgrounds and **2,311 square axial glyphs / 2,095 reversed-aspect axial glyphs**. These prevent bounding-box shape from replacing symmetry recognition. A bounded small-template fallback remains documented; no tested mask exhausted the 80 growth trials.
- `a251c730` matches markers to the uniquely occurring anchor colour inside a motif. The revised sampler allows another motif's body to reuse that colour. **1,333 distinct scenes** pass an independent pixel/anchor checker inside known construction boxes, plus the separate input-only reference solver for box discovery. **358 scenes** contain cross-anchor body colours; 616 exceed the old 18-cell box cap, with extents up to 24. Explicit inconsistent patterns sharing an unused anchor now reject.
- `a32d8b75` combines an arrow, anchor, shape and two-colour tile. The `hard_tile=True` control distinguishes colour swapping from every D4 transform and makes accidental tile rotation observable. Random stamps leave room on both canvas axes. An independent input-pixel legend decoder passes **1,645 distinct scenes**, including 360 canvas shapes, all supported tile sizes/sides and fixed-canvas controls. The 2,090 decoded legends include 2,030 hard-swap tiles and 232 rectangular tiles. Canonical ambiguous tiles retain their original behaviour.

The three generators retain explicit restrictions: separated glyphs with fixed foreground colour; motifs from a small <=3×3 library; and one or two non-overlapping legend stamps with bounded tile sizes. These are constructive subfamilies, not a proof of exhaustive mechanism or difficulty coverage. The socket constructor `a25697e4` is still excluded after a dense three-pair placement failure; repair is ongoing.

The regression suite passes **137 tests**. Coverage is **1,065/1,120**, with **55 missing**, **168 reviewed standalone additions**, and six older constructors awaiting standalone review. Bulk generation and model training remain stopped pending full coverage.


## Constraint-aware socket seating and dense placement repair — 2026-10-20

Registered `a25697e4`: rigidly transform two-colour chains to fill socket holes, swap their colours only for reflected placements, and reject alternatives blocked by the border or occupied cells. `hard_negative=True` forces at least one shape-matching but illegal alternative. All five canonical examples reconstruct exactly.

The first revised source failed seed 91597 on a 12×30 canvas with three pairs and a forced hard negative. The failure and source are archived. The repair plans sockets first, checks fit uniqueness incrementally, then places loose chains into enumerated free positions. It reduces padding on cramped canvases and reduces the work budget rather than merely extending retries. The failed seed now passes, along with **164 dense regression cases** across 12×30, 30×12, 20×20 and 30×30 canvases.

A separate parser and signed-coordinate isometry oracle passes **1,726 distinct scenes**, including every 10..30 rectangular shape with a forced hard negative, multiple pairs and every background colour. The scenes contain **2,869 chain/socket pairs**, **1,452 reflected placements** and **4,125 blocked geometric alternatives**. The largest piece has nine cells; the longest measured targeted generation call took 0.565 seconds. One thousand independent archived-solver seeds also pass. Fifteen invalid controls reject. Explicit zero-fit identity scenes now correctly reject rather than being counted as training examples.

The generator retains a finite constructive scope: one to three pairs; spaced objects; rectangular socket envelopes with cut-out holes; unique final seating; and size-conditioned piece/padding limits. Bounded search still has a theoretical exhaustion case, so failures must remain visible during bulk generation.

The regression suite passes **139 tests**. Coverage is **1,066/1,120**, with **54 missing**, **169 reviewed standalone additions**, and six older constructors awaiting standalone review. Bulk generation and model training remain stopped pending full coverage.


## Constellation-guided copying with stable clipping controls — 2026-10-20

Registered `a395ee82`: interpret the dot constellation as offsets measured in whole shape-bounding-box units, erase the dots, recolour the original shape, and stamp its copies. All four canonical 22×22 examples reconstruct exactly; none clips a copy. The archived prose claiming left-edge clipping in the third pair is incorrect and is not used to justify generated labels.

The revised generator resolves clipping mode once per call, then conditions placement on that choice instead of redrawing the mode after failures. An independent input-component and lattice decoder passes **1,806 distinct scenes**, including all 361 rectangular sizes from 12..30 in both forced clipping modes and up to 24 dots. **155 of 1,000 default scenes clip**, consistent with the intended 15%; all 516 selected clipping cases clip, and all 1,286 no-clipping cases fit completely. Fourteen invalid controls reject promptly, including impossible shape coordinates. One thousand independent archived-solver seeds and all 22 valid / nine rejected critic controls pass.

Clipping and non-22×22 canvases remain labelled synthetic extensions. Random shapes remain connected non-full masks with bounding boxes at most 4×4; the larger canvas does not imply larger motifs. Explicit broader shapes are a separate API scope.

The regression suite passes **141 tests**. Coverage is **1,067/1,120**, with **53 missing**, **170 reviewed standalone additions**, and six older constructors awaiting standalone review. Bulk generation and model training remain stopped pending full coverage.


### Staircase motion with explicit ambiguity rejection

`97c75046` adds constructive staircase/ball scenes, exact replay of all four original pairs, and 1,000 independent archived-solver checks. A separate input-derived geometry probe passes 2,052 distinct scenes: 728 supported canonical rectangles, 320 oriented 30x30 cases, 1,000 default scenes and four fixtures. The set contains 872 sliding cases, 1,180 straight-only cases and 362 edge endings. Ten malformed or ambiguous requests are rejected. The regression suite passes 143 tests.

The constructor rejects competing diagonal paths and configurations where continuing down beside a wall is a plausible alternative to stopping. Its common-base vertical-run staircases and canonical-axis size controls are documented restrictions; transpose swaps the emitted dimensions. Coverage is **1,068/1,120**, with **52 missing**, **171 reviewed standalone additions**, and six older constructors awaiting standalone review. Bulk generation and training remain stopped pending complete coverage.


### Enclosed-hole topology and interlocking stencil legends

Two further reviewed generators add `aa4ec2a5` and `abc82100`. Each reconstructs its original fixtures and passes 1,000 independent archived-solver checks. Their independent input-only audits cover:

- Hole topology: 1,835 pairs (1,833 distinct inputs), all 529 rectangles from 8x8 to 30x30 with two objects, six-object scenes, 573 diagonal-only leak cases and 50 irregular-hole cases. An open channel remains exterior; a diagonal-only gap does not open a four-connected pocket. Fifteen invalid requests reject. The primitive-shape fallback was never called in this audit, but remains documented.
- Stencil legends: 1,841 distinct scenes, all 676 rectangles from 5x5 to 30x30 with one legend, 223 interlocked layouts, 426 mapped-colour runs, 1,262 clipping cases and 774 swap/chain cases. The longest run spans 29 cells. Forced four-legend interlocking and long-run controls pass. Seventeen malformed requests reject, including a loose cell covering an anchor that must remain background or stencil.

The generators document their restrictions: separated rectangle-union objects for holes; finite stencil families and collision-free random stamps for legends. These are bounded mechanism checks, not claims of exhaustive semantic or difficulty coverage. The regression suite passes **147 tests**. Coverage is **1,070/1,120**, with **50 missing**, **173 reviewed standalone additions**, and six older constructors awaiting standalone review. Bulk generation and training remain stopped pending complete coverage.


### Occluded wires with hard endpoint pairings

`a47bf94d` now constructs glyphs, routes and occluders explicitly and derives the output from those latent connections. All four original fixtures replay exactly, including free-form wiring and the four-occluder test. Random controls support up to four occluders, rather than the draft's three.

An input-only glyph/port tracer and the archived solver pass 1,682 distinct scenes: 1,000 defaults, 528 wire-count/block-count/orientation combinations, 120 dense four-block scenes, 30 single-source controls and four fixtures. All default scenes contain an inversion among actual unresolved source-to-empty-end pairings, defeating straight-across and positional-rank shortcuts. The audit contains 480 odd-port scenes, 701 wires beside occluders, 662 exterior turns near occluders and 628 hidden-turn scenes. Sixteen invalid controls reject; all 23 valid and nine rejection critic probes pass.

Random routes remain limited to two facing marker rows with zero, two or four turns. General routes and perpendicular-side markers are explicit-only; these restrictions remain in the report. All **149 regression tests** pass. Coverage is **1,071/1,120**, with **49 missing**, **174 reviewed standalone additions**, and six older constructors awaiting standalone review. Bulk generation and training remain stopped pending complete coverage.


### Unique shortest paths and glyph matching without an easy fallback

`b15fca0b` constructs comb mazes from wall openings and latent crossing rows. Independent BFS checks all rendered paths for both optimality and uniqueness: 1,891 cases (1,887 distinct inputs), covering all 784 height/wall-count/orientation combinations, 100 extra 3-row/14-wall stress cases and six canonical fixtures. Longest tested path: 282 steps; largest detour: 248 steps. The generator remains limited to comb topology, with synthetic larger sizes clearly labelled. Its 1,000 independent reference checks produced 994 distinct inputs, so native uniqueness must be measured when allocating episodes.

`b20f7c8b` matches legend glyphs under rotation/reflection and redraws solid boxes using the unrotated legend. Review removed a retry branch that dropped same-cell-count distractors. Minimum single-box defaults now retain at least two glyphs; one-glyph scenes require an explicit request. A separate input-only audit passes 1,491 distinct scenes, including every supported rectangle, 100 minimum-size distractor cases and 100 dense eight-glyph/eight-box cases. All sampler calls keep the strict matching requirement.

Both reconstruct every canonical fixture, pass 1,000 independent reference checks, and reject malformed controls. All **153 regression tests** pass. Coverage is **1,073/1,120**, with **47 missing**, **176 reviewed standalone additions**, and six older constructors awaiting standalone review. Bulk generation and training remain stopped pending complete coverage.


### Odd-pattern selection with dense constructive packing

`aee291af` adds repeated framed patterns hidden in noise, with one unique interior. Its answer is constructed from the latent odd pattern. A separate row-bitset oracle exhaustively examines candidate square windows: 1,362 distinct scenes pass, including 755 same-cell-count odd patterns, 384 rotated/reflected odd patterns and 366 scenes containing nested windows. All four canonical fixtures reconstruct exactly; 1,000 independent archived-solver seeds pass.

The three formerly failing dense requests now succeed: 16 size-5 boxes, 16 size-4 boxes in 19x19, and nine size-8 boxes in 30x30. Randomized lattice fallback preserves counts when greedy placement jams; it was used in 56/1,000 defaults and 167 audit scenes overall. Thirteen malformed or geometrically impossible requests reject promptly. Default scenes have exactly one unique candidate across all window sizes; canonical replay retains the original order-sensitive rule. The report records the limited arrangement diversity near packing capacity.

All **155 regression tests** pass. Coverage is **1,074/1,120**, with **46 missing**, **177 reviewed standalone additions**, and six older constructors awaiting standalone review. Bulk generation and training remain stopped pending complete coverage.


### Reviewed reflection, gravity and quadrant scaling

`ad3b40cf`, `ac2e8ecf` and `b10624e5` each pass 1,000 independent archived-solver checks with 1,000 distinct inputs, and reconstruct all canonical fixtures. Their independent, input-derived mechanism audits add:

- Minority-colour reflection: **2,354 cases / 2,350 unique inputs**, all four mirror orientations, 850 diagonal-offset controls, strict count-versus-object-size adversaries, and minimal 6x6 diagonal geometry. Canonical diagonal corner contact is retained. The default witness fallback was not used in this audit; a forced-failure regression separately exercises it.
- Frame/cross gravity: **1,747 cases / 1,746 unique inputs**, all 441 canvas shapes from 10..30 per side, all counts up to six of each kind, and dense minimum grids. Independent cell-by-cell and box-level gravity agree on all 1,745 default/canonical cases; two explicit box-gap extensions intentionally differ. Among 1,000 defaults, 918 stack and 891 require opposite kinds to pass one another. No safe fallback was needed.
- Quadrant scaling: **1,931 distinct inputs**, 800 extreme-layout controls across both modes and all quadrants, 600 shrinking cases, 1,035 clipped cases and 1,011 nonsquare grids. Every target retains all attachment colours and differs from all three incorrect mirror orientations.

All **161 regression tests** pass. Coverage is **1,077/1,120**, with **43 missing**, **180 reviewed standalone additions**, and six older constructors awaiting standalone review. Per-file reports preserve restrictions: reflection uses small separated polyominoes; gravity uses vertical lanes; scaling uses aligned/fine rectangular templates with lossless scale ratios. Bulk generation and training remain stopped pending complete coverage.


### Reviewed nested-scale tile-pattern completion

`b99e7126` reconstructs all four original pairs and passes 1,000 independent archived-solver checks with 1,000 distinct inputs. The host review corrected the documented size-sampling bias and directly constructs the two possible three-cell diagonal masks rather than relying on repeated growth attempts.

An independent input-only tile-frequency, new-colour and translation oracle passes **1,664 cases / 1,662 unique inputs**. This includes every 196 supported size/offset combination, all **232 supported 3x3 masks**, and 464 rendered checks using their minimum/maximum unique shown-subset sizes. The mask audit enumerates 9,924 uniquely locating shown subsets; it checks alternatives extending outside the lattice, so an edge cannot be the sole disambiguator. There are 1,157 scenes where non-mask tile cells also change, and 992 nonsquare scenes. Eleven malformed/ambiguous controls reject; all 21 valid and ten rejection critic cases pass.

The fixed 3x3 tiles, one-cell dividers, 3..8-cell masks and 4..7-tile sides remain explicit restrictions. Three-cell masks have only two native geometries, so a large episode quota cannot be assumed to yield independent shapes. Smaller/rectangular lattices are labelled extensions of the original 7x7 lattice. Coverage is **1,078/1,120**, with **42 missing**, **181 reviewed standalone additions**, and six older constructors awaiting standalone review. Bulk generation and training remain stopped pending complete coverage.

All **163 regression tests** pass after this addition.


### Reviewed lattice compression with larger rectangular distractors

`b71a7747` reconstructs all three canonical pairs and passes 1,000 independent archived-solver checks with 1,000 distinct inputs. An independent input-only connected-component and row/column compression oracle passes **1,321 distinct scenes**, including 54 block-size/gap combinations, all 44 small-block count combinations, 120 thin/large controls and 100 forced non-square rectangular distractors. All 100 distractors contain a solid rectangle larger than a block; 53 remain isolated rectangular components after noise. The audit counts 96 larger foreign rectangular components overall and 388 unequal row/column gaps.

Explicit paths now obey the same minimum-three-touched-block and free-block constraints as random paths. Impossible fixed paths are rejected before rendering; malformed container controls raise ValueError. Twelve invalid controls and all 20 valid/nine rejection critic probes pass. The critic's prior one-block explicit success is correctly rejected under the strengthened contract.

The square-selection rule uses whole connected components, not arbitrary square patches inside rectangles. Random line-centred lattices and bounded path growth remain scope restrictions. Default positive margins limit blocks of size9+ to 2x2; zero margins allow 3x3 blocks of size9 with gap1, which is explicitly tested. Coverage is **1,079/1,120**, with **41 missing**, **182 reviewed standalone additions**, and six older constructors awaiting standalone review. Bulk generation and training remain stopped pending complete coverage.

All **165 regression tests** pass after this addition.


## Scaffold deletion and rigid settling — reviewed checkpoint

Registered `b6f77b65` after all seven original pairs, 1,000 independent seed checks and an independent input-derived support-graph audit of **1,951 distinct scenes** passed. The oracle separately handles floor support, contact/overlap, two-sided wedging and simultaneous falling. Both four- and eight-connected parses agree on the checked scenes.

The audit includes all 484 canvas shapes from 9..30 per side, 400 forced-mode/extreme-size cases and 60 eight-colour legends. Of 1,000 defaults, 853 cause movement and 78 release a wedged foot; 54 identity cases and 93 nonmoving deletions remain intentional. Some deletions expose a hidden pole tip without moving it. Across the full audit, 191 scenes release wedged feet, the longest pole has 11 cells and the longest fall spans 20 rows. No late mode relaxation was reached. Thirteen malformed controls reject; duplicate legend colours intentionally reject despite two older critic expectations.

Band-based layouts, interior columns, top-left legends and a restricted pole/bar/foot vocabulary remain documented limitations. Hidden pole-tip extension follows the archived task rule, not a general physical law. Two regression tests cover exposed extensions and lost wedge support. **167 regression tests pass. Coverage: 1,080/1,120; 40 missing; 183 reviewed standalone additions.** Six older constructors still need standalone conversion. Bulk generation and model training remain stopped pending coverage.


## Clockwise corner copying — reviewed checkpoint

Registered `bc93ec48`. Four canonical pairs, 1,000 independent seed checks and **1,942 distinct input-only oracle checks** pass, including all 676 rectangles from 5x5 to 30x30, 160 count/extreme controls and 100 alternate-background extensions. The oracle independently finds each original corner component and translates its exact cells clockwise; it verifies preservation of uncovered pixels and distinguishes copying from moving on all 1,000 default scenes.

Defaults include 392 scenes where the translated bounding box reaches a destination corner but the actual shape does not cover that corner, 144 with foreign colours inside a corner object's bounding box, and 456 with foreign-colour contacts. An explicit component occupying two grid corners now rejects, resolving an ambiguity in the draft. Thirteen invalid controls reject. The critic's 22 valid/eight rejection cases pass; its old success expectation for the multi-corner component intentionally fails. Background 7, sub-half-grid random corner objects, nonoverlapping stamps and restrictions on same-colour adjacency remain explicit limitations.

**169 regression tests pass. Coverage: 1,081/1,120; 39 missing; 184 reviewed standalone additions.** Six older constructors remain to convert. Bulk generation and model training remain stopped.


## Bracket fill and reflection — reviewed checkpoint

Registered `bf32578f`. All four original pairs, 1,000 independent seed checks and **2,206 distinct input-derived row-span/mirror checks** pass. Tests include all 784 rectangles from 3x3 to 30x30, 300 large native cases, 112 half-length/parity/cap combinations and six wider explicit stroke profiles. Of the 300 large cases, 80 have brackets taller than the previous 16-row ceiling and 44 exceed the previous 13-column ceiling; maximum native bracket dimensions are 30 rows and 15 columns.

The CLI repair initially imposed x1<=14 on explicit inputs as well as random proposals. Host review preserved wider valid explicit strokes by bounding coordinates before allocation and checking the actual mirrored footprint. Profiles with bracket widths up to 28 are independently tested. Eighteen invalid controls reject; extreme offsets/caps and excessive half-length reject before geometry allocation. Critic tests pass 21 valid and nine rejection cases. Fixed zero background, a single symmetric right-opening bracket, non-concave offsets, in-bounds mirrors and the native x1<=14 proposal remain documented restrictions. Larger/irregular shapes are synthetic extensions.

**171 regression tests pass. Coverage: 1,082/1,120; 38 missing; 185 reviewed standalone additions.** Six older constructors remain to convert. Bulk generation and model training remain stopped.


## Minimum-rotation tiling — reviewed checkpoint

Registered `b7cb93ac`. The former six-piece/6x6 failure was repaired with anchored connected partitions, stronger congruent-colour merging, valid rotation proposals and exact separated-piece packing. All four original pairs and 1,000 independent seed comparisons pass. An independent input-only exact-cover enumerator checks **1,465 distinct scenes**, including 200 count/extreme cases, 100 six-piece/6x6 scenes and 160 strict tie/critical combinations.

Among 1,000 defaults, 317 use the demonstrated left-piece swap tie-break, 880 have a higher-cost tiling that paints a different answer, and 619 require at least one piece rotation. Accepted piece counts are 446 two-piece, 400 three-piece, 133 four-piece and 21 five-piece scenes. All 100 tight six-piece cases succeed; their minimum cost is zero and all reuse colours. Thus the repair proves feasibility, not rich rotated-six-piece coverage. A bounded partition fallback was invoked 138 times across the audit; the slowest tight-six call took 2.461 seconds.

Preference-critical detection now compares painted grids, rather than treating every higher-cost rearrangement as informative. A regression demonstrates four identically coloured bars with both cheap and costly arrangements but the same painted answer. Twelve invalid controls reject; critic checks pass 14 valid and 11 rejection cases. Fixed 3x4 outputs, restricted tie patterns, acceptance-biased piece counts and bounded-search failures remain documented limitations.

**173 regression tests pass. Coverage: 1,083/1,120; 37 missing; 186 reviewed standalone additions.** Six older constructors remain to convert. Bulk generation and model training remain stopped.


## Funnel continuation and cyclic band filling — reviewed checkpoint

Registered `b9e38dc0` and `c4d1a9ae`, each after 1,000 independent seed checks and exact original fixture reconstruction.

- Funnel: **1,847 distinct scenes** pass an independent input-derived role/direction, shadow, flood and phase-counter oracle. Coverage includes every supported 9..30 by 10..30 rectangle, 300 large canvases and 80 minimum-canvas rotations. Default scenes include 331 border-boundary cases, 553 unequal boundary-pattern cases, 909 observable stream-shadow effects and 742 extra-wall scenes. Vessel height on 30x30 inputs reaches 26 rows; 155/300 exceed 17 rows. All random scenes visibly widen beyond the opening and fill at least two stream rows. Nineteen malformed controls reject; critic checks pass 29 valid/seven rejected. Converging/long-final-run behaviour remains an explicitly tested extension; native sides diverge.
- Bands: **1,393 cases / 1,386 unique inputs** pass independent separator detection and cyclic-colour filling, including all 232 height/count combinations, 28 band widths and 100 forced-margin cases. Fixed masks now choose directly among feasible weighted gap/margin layouts; impossible dense masks reject before rendering. All 1,000 defaults distinguish the rightward cycle from a leftward alternative. Default counts are 379 three-band, 237 four-band, 127 five-band, 127 six-band and 130 seven-band. Seventeen malformed controls reject; critic checks pass 23 valid/nine rejected. Dense masks may force nonzero margins, and constrained repeated masks account for seven duplicate audit inputs.

**176 regression tests pass. Coverage: 1,085/1,120; 35 missing; 188 reviewed standalone additions.** Six older constructors remain to convert. Bulk generation and model training remain stopped.


## Line/shape exchange and dense mirrored chains — reviewed checkpoint

Registered `c6141b15` and `c9680e90`. Each reconstructs all four original pairs and passes 1,000 independent seed comparisons. Line/shape inputs are all distinct; chain inputs contain one repeat.

- Line/shape exchange: **1,405 distinct scenes** pass independent component parsing, bounding-box centre extraction, aligned-pair rasterization and endpoint stamping. The audit covers all named/random templates across six layouts, rectangular canvases, eight segment directions and an explicit 1x30 extension. Defaults include 303 scenes distinguishing bbox centres from centroids, 333 with unaligned pairs and 745 needing multiple line directions. Actual shape halos now determine feasible triangle/square spacings. Impossible pinned coordinates, overlapping centres and malformed layouts reject up front, including when dimensions are omitted. Fifteen invalid cases reject; critic checks pass 24 valid/nine rejected.
- Mirrored chains: **2,371 cases / 2,304 distinct inputs** pass an independent BFS-distance/endpoints oracle. All 1,146 advertised-capacity controls preserve the exact requested count; 30 zero-capacity controls reject. Sixty tight 2x30-half tests produce 20 objects with touching reds allowed or 15 without touching. Another 160 tests cover 30-object scenes in both orientations and on either divider side. Defaults include 914 turning-chain scenes and 612 touching-red scenes; a separate explicit 30-cell turning chain passes. Host review restored feasible one-row halves (54 audit cases) instead of dropping that previously valid extension. Fifteen invalid controls reject; the critic's old rejection for three objects in 5x5 now succeeds because the new constructive capacity exceeds its former cap of two.

Dense chain capacity is the best packing found by the bounded constructive engine, not a proven mathematical maximum. Dense scenes trade chain length for count, and 67 repeated inputs in constrained audits remain visible. Line/shape heuristics can still exhaust retries on grown/bent/random-template controls; these limits remain documented.

**180 regression tests pass. Coverage: 1,087/1,120; 33 missing; 190 reviewed standalone additions.** Six older constructors remain to convert. Bulk generation and model training remain stopped.
