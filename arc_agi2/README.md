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
- **33 new constructive implementations** have passed bounded validation: the original three plus 30 additional counting, selection, geometry, legend, relational-motion and repair constructors. Standalone conversion and review are tracked separately below.
- **Two variable-size extensions**: `0692e18c` (inverse self-tiling) and `00576224` (three-by-three tiling with mirrored middle band).
- All 35 research constructors (33 new families plus two size extensions) passed **300 random differential tests each**, and their reference solvers reproduce all original examples. Outputs are constructed independently from latent parameters, then compared with the saved transform.
- **22 additional fixed-size families / 111 size-parameter configurations** passed bounded 12-seed differential tests. Every such generated pair is checked again during generation. This is agreement evidence, not proof of semantic correctness.
- **196 tasks still need constructive generators**. A saved transform is not itself an input generator. Reference packets and `reports/generator-roadmap.csv` provide the task-by-task backlog.

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

The authoring campaign uses three concurrent Claude CLI processes under the user’s Max subscription; API credentials are removed from their environment and there is no API fallback. Every candidate is checked for original fixture reconstruction, valid grids, bounded execution, nonidentity examples, native input diversity and 300 fresh comparisons against the saved solver. Registration additionally requires review. Constructors generate new latent scenes rather than transformed copies of original examples.

A zero-error differential check is a bounded agreement test. It does not prove the saved solver is universally correct or that every original mechanism variant is covered.

Reviewed standalone modules now include `135a2760`, `16de56c4`, and `62593bfd`; each passed 1,000 fresh seed checks and exact original-fixture reconstruction. Remaining CLI drafts are being authored and validated locally.
