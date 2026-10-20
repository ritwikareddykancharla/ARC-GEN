"""Dataset card for verified combined targets and PNG audit images."""
import json


def card(manifest):
    files = manifest.get("episode_files", {})
    configs = []
    for split in ("train", "validation"):
        if files.get(split):
            configs.append({"split": split, "path": sorted(files[split])})
    # JSON is a subset of YAML and avoids hand-escaping thousands of filenames.
    metadata = {"license": "apache-2.0", "task_categories": ["text-generation"],
                "configs": [{"config_name": "default", "default": True, "data_files": configs}]}
    count = manifest.get("train_episodes", 0)
    fresh = manifest.get("train_fresh_episodes", 0)
    target = manifest["target_train_fresh_episodes"]
    return "---\n" + json.dumps(metadata, indent=2) + "\n---\n" + f"""# ARC: verified programs and grids

**{count:,} published training episodes from {fresh:,} fresh base episodes.**
Build status: **{manifest['status']}**. Target: **{target:,} fresh episodes**,
each expanded into up to eight distinct rotations/reflections. These counts
describe the files in this build, not the earlier 24-row format preview.

## Read an episode

[Open the image viewer](https://huggingface.co/datasets/ritwika96/arc-agi2-program-grid-sft/viewer/default/train)
· [Interactive gallery](https://huggingface.co/spaces/ritwika96/arc-episode-gallery)
(the gallery currently displays the earlier corpus).

Each row contains a high-resolution, lossless **PNG** of demonstrations and query,
plus one JSON record containing **both the executable program and output grids**.
The PNGs and records are grouped into TAR shards so millions of episodes do not
require millions of repository files. No Parquet source is required. Hugging Face
may create its own Parquet cache to display the viewer.

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
distribution of the 1,120 public tasks. Published measurements, not the target
distribution alone, show whether a completed build achieves that match.

Approved teaching corrections are labelled in each record. Canonical benchmark
files remain unchanged. Public evaluation families included here become training
data. Model training is not launched by this dataset builder.

Upstream ARC-GEN: Google LLC, Apache-2.0. Reviewed additions and dataset pipeline:
Ritwika Kancharla. This is an independent research dataset.
"""
