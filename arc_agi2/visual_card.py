"""Dataset card for verified combined targets and PNG audit images."""
import json


def card(manifest):
    files = manifest.get("episode_files", {})
    families = {}
    for split in ("train", "validation"):
        for path in files.get(split, []):
            if not path.endswith(".arrow"):
                continue  # Source TARs are downloadable, not viewer loader inputs.
            family = path.rsplit("/", 1)[-1].split("-", 1)[0]
            if len(family) != 8 or any(c not in "0123456789abcdef" for c in family):
                raise ValueError("Unexpected viewer index family filename: " + path)
            families.setdefault(family, {}).setdefault(split, []).append(path)
    configs = [{"config_name": "family_" + family,
                "data_files": [{"split": split, "path": sorted(paths)}
                               for split, paths in sorted(splits.items())]}
               for family, splits in sorted(families.items())]
    if configs:
        configs[0]["default"] = True
    first_config = configs[0]["config_name"] if configs else "default"
    # JSON is a subset of YAML and avoids escaping thousands of filenames.
    metadata = {"license": "apache-2.0", "task_categories": ["text-generation"],
                "configs": configs}
    count = manifest.get("train_episodes", 0)
    fresh = manifest.get("train_fresh_episodes", 0)
    target = manifest["target_train_fresh_episodes"]
    return "---\n" + json.dumps(metadata, indent=2) + "\n---\n" + f"""# ARC: verified programs and grids

**{count:,} published training episodes from {fresh:,} fresh base episodes.**
Build status: **{manifest['status']}**. Target: **{target:,} fresh episodes**,
each expanded into up to eight distinct rotations/reflections. These counts
describe the files in this build, not the earlier 24-row format preview.

## Read an episode

[Open the image viewer](https://huggingface.co/datasets/ritwika96/arc-agi2-program-grid-sft/viewer/{first_config}/train)
· [Interactive gallery](https://ritwika96-arc-episode-gallery.static.hf.space/program-grid.html)
(browse the published program-and-grid episodes).

**Select a task family in the viewer's subset menu.** Each family contains its
own combined episode records; the selected family's row count is not the total
corpus count above. Family configurations limit conversion size because Hugging
Face may truncate non-Parquet previews beyond 5 GB per configuration. They do
not split programs from grid targets.

Each row displays a full-resolution, lossless **PNG**, readable Python program,
output-grid JSON, prompt, and combined completion. Authoritative PNG/JSON pairs
are grouped into downloadable TAR shards. Compressed Arrow support indexes embed
exactly the same PNG bytes and records for the viewer, avoiding millions of
individual repository files and failing archive image paths. Episode training
shards are PNG/JSON TARs with Arrow viewer indexes, not Parquet. Separate internal
reusable pair pools may use Parquet; they are not episode viewer inputs or
additional training episodes. Hugging Face may create its own display cache.
Source and index row counts are identical and are counted only once.

**The PNG shows the expected query answer for human inspection. Do not feed it
to the model.** Use the record's `prompt` as input and `completion` as the target.
The completion contains a Python program followed by the grid JSON.

## Verification and augmentation

All demonstration and query grids must match the program exactly. Every distinct
D4 variant must pass before its base episode is accepted; failed variants are not
silently dropped. Programs operate in the visible grid coordinates, without
undo-transform / native-program / redo-transform wrappers.

The same rotation/reflection and colour permutation apply to every pair within an
episode. Symmetric duplicate variants are removed and counted. Shortfalls and
low-diversity families are reported rather than filled with duplicate episodes.

[Build manifest](manifest.json) · [Per-family reports](episode_reports)
· [Exact size histograms](size-audit.json) · [Allocation](allocation.json)

The size allocation targets the measured query-size and input/output-shape
distribution of the 1,120 public tasks. Demonstration selection also prefers each
family's original uniform/mixed input dimensions and whether the query size was
seen among the demonstrations. Required semantic contexts take priority;
unsupported size patterns and deviations are recorded per family.
Published measurements, not the target
distribution alone, show whether a completed build achieves that match.

Approved teaching corrections are labelled in each record. Canonical benchmark
files remain unchanged. Public evaluation families included here become training
data. Model training is not launched by this dataset builder.

Upstream ARC-GEN: Google LLC, Apache-2.0. Reviewed additions and dataset pipeline:
Ritwika Kancharla. This is an independent research dataset.
"""
