"""Annotate existing generated episodes with execution-verified program targets.

No teacher calls, training or new bulk scene generation. Each published row holds
both a direct program and output grid. Storage is PNG/Python/JSONL, not Parquet.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import time

import pyarrow.parquet as pq
from huggingface_hub import HfApi, CommitOperationAdd, hf_hub_download
from .program_targets import make_record
from .visual_dataset import write_bundle

SOURCE = 'ritwika96/arc-agi2-arcgen-100k-episodes'
DEST = 'ritwika96/arc-agi2-program-grid-sft'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(path)


def family(args):
    source, revision, remote, output, limit = args
    root = Path(output)
    tid = Path(remote).stem
    report_path = root/'reports'/f'{tid}.json'
    file = hf_hub_download(source, remote, repo_type='dataset', revision=revision)
    rows = pq.read_table(file).to_pylist()
    if limit:
        # Sample across native/augmented halves instead of only the first rows.
        rows = [rows[i*len(rows)//min(limit,len(rows))] for i in range(min(limit,len(rows)))]
    accepted, rejected = [], []
    metadata = root/"episodes"/tid/"metadata.jsonl"
    if metadata.exists():
        raise RuntimeError("Refusing to append duplicate rows to an existing image shard; use a fresh output directory")
    errors = Counter()
    start = time.monotonic()
    for row in rows:
        try:
            record = make_record(row, source, revision)
            write_bundle(record, root)
            accepted.append(record)
        except Exception as exc:
            reason = type(exc).__name__+': '+str(exc)[:800]
            errors[reason] += 1
            # Keep exact episode identifiers; source labels remain in the source repo.
            rejected.append(dict(episode_id=row.get('episode_id'),task_id=tid,reason=reason))
    files = [str(path.relative_to(root)) for folder in (root/'episodes'/tid,root/'programs'/tid)
             if folder.exists() for path in sorted(folder.glob('*')) if path.is_file()]
    reject_path = root/'rejections'/f'{tid}.json'
    save(reject_path,rejected)
    files.append(str(reject_path.relative_to(root)))
    report = dict(task_id=tid,attempted=len(rows),accepted=len(accepted),rejected=len(rejected),errors=dict(errors),seconds=time.monotonic()-start,files=files,source_revision=revision)
    save(report_path,report);report['files'].append(str(report_path.relative_to(root)))
    return report


def card(m):
    images = '\n\n'.join(
        f'![Episode {Path(path).stem}]({path})' for path in m.get('preview_images', [])[:3]
    )
    return f'''---
license: apache-2.0
task_categories:
- text-generation
language:
- en
configs:
- config_name: default
  default: true
  data_files:
  - split: train
    path:
    - episodes/**/*.png
    - episodes/**/metadata.jsonl
---
# ARC episodes · program + output grid

**One episode, one row, both targets together.** The image shows demonstrations and the query answer for human inspection. The same row contains the readable program and output-grid JSON. The assistant completion contains a Python block followed by a JSON block.

**Status: {m['status']} · {m['episode_rows']:,} episodes.** These are converted existing episodes, not the planned million-episode expansion. Missing direct-program variants remain in the repair queue; the builder will not use augmentation wrappers as a fallback.

## See the grids

Click an image to open its full-resolution lossless PNG. Each image contains demonstrations and the query answer for human inspection.

{images}

## Open the files

- [PNG episodes](episodes): sharp colour-only cells, demonstrations and query grids.
- [Python programs](programs): directly readable `.py` files.
- [Manifest](manifest.json): unique episode count and verification results.
- [Rejected episodes](rejections): unresolved solver or rewrite failures.

No new Parquet files are written by this builder. Small `metadata.jsonl` files associate each PNG with its program and target so the HF image viewer can display them together. Existing legacy files, if present, are excluded from this configuration.

## Training record

The model input is `prompt`, containing demonstration pairs and query inputs. The `completion` is the program followed by the output-grid JSON. The overview image includes the answer and is **for auditing**, not a model input. Each program is executed against every demonstration and query before acceptance, with fresh module state on each call. This is bounded execution verification, not a proof of generalization or a security sandbox.

For augmented episodes, direct programs express the transformed rule in the visible grid coordinates. No undo-transform / native-solver / redo-transform adapter is used. Missing rewrites are rejected explicitly.

Source episodes: [{m['source_repo']}](https://huggingface.co/datasets/{m['source_repo']}) at `{m['source_revision']}`. Solver/build revision: `{m['code_revision']}`. This initial conversion is training-only and claims no independent validation split for the older source. Model training has not been launched.

Upstream ARC-GEN: Google LLC, Apache-2.0. New pipeline and reviewed additions: Ritwika Kancharla. Original ARC data retain their attribution; this is an independent research dataset.
'''


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',default=SOURCE);ap.add_argument('--revision',required=True)
    ap.add_argument('--destination',default=DEST);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--workers',type=int,default=16);ap.add_argument('--limit-per-family',type=int,default=0)
    ap.add_argument('--tasks',nargs='*');ap.add_argument('--publish',action='store_true')
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    api=HfApi()
    files=sorted(f for f in api.list_repo_files(a.source,repo_type='dataset',revision=a.revision) if f.startswith('data/') and f.endswith('.parquet'))
    if a.tasks:files=[f for f in files if Path(f).stem in a.tasks]
    if not files:raise ValueError('No source episode shards selected')
    m=dict(status='verifying_program_targets',source_repo=a.source,source_revision=a.revision,destination=a.destination,code_revision=os.environ.get('ARCGEN_SOURCE_COMMIT','local'),workers=a.workers,source_families=len(files),completed_families=0,episode_rows=0,rejected_rows=0,attempted_rows=0,failed_families=[],model_training_launched=False,new_teacher_calls=0,limit_per_family=a.limit_per_family)
    if a.publish:
        if api.whoami()['name']!='ritwika96':raise RuntimeError('Unexpected HF account')
        api.create_repo(a.destination,repo_type='dataset',private=False,exist_ok=True)
    def publish(changed):
        save(a.output/'manifest.json',m);(a.output/'README.md').write_text(card(m))
        if a.publish:
            # Don't expose an empty dataset configuration before the first shard.
            names=['manifest.json',*changed]+(['README.md'] if m['episode_rows'] else [])
            ops=[CommitOperationAdd(path_in_repo=f,path_or_fileobj=str(a.output/f)) for f in names]
            for attempt in range(5):
                try:
                    api.create_commit(a.destination,repo_type='dataset',operations=ops,commit_message=f"{m['episode_rows']} combined program/grid episodes; {m['completed_families']} families")
                    return
                except Exception:
                    if attempt==4:raise
                    time.sleep(2**attempt)
    publish([]);changed=[];last=time.monotonic()
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        fs={pool.submit(family,(a.source,a.revision,f,str(a.output),a.limit_per_family)):f for f in files}
        for future in as_completed(fs):
            remote=fs[future]
            try:
                report=future.result();m['episode_rows']+=report['accepted'];m['rejected_rows']+=report['rejected'];m['attempted_rows']+=report['attempted'];changed+=report['files']
                pngs = [f for f in report['files'] if f.endswith('.png')]
                if pngs and len(m.setdefault('preview_images', [])) < 3:
                    m['preview_images'].append(pngs[0])
            except Exception as exc:m['failed_families'].append(dict(file=remote,error=repr(exc)))
            m['completed_families']+=1
            print(json.dumps({k:m[k] for k in ['completed_families','episode_rows','rejected_rows']}),flush=True)
            if len(changed)>=24 or time.monotonic()-last>30:
                publish(changed);changed=[];last=time.monotonic()
    m['status']='conversion_complete_with_exclusions' if m['rejected_rows'] or m['failed_families'] else 'conversion_complete'
    publish(changed)


if __name__=='__main__':main()
