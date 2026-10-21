"""Bounded, compressed image-viewer index for authoritative PNG/JSON TAR shards.

Each index row contains the exact source PNG bytes and BOTH program and grid.
The source archive remains the downloadable, human-auditable data artifact.
Arrow is a viewer-support index; no Parquet files are created or uploaded here.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

import pyarrow as pa
from datasets import Features, Image as ImageFeature, Value
from PIL import Image


def index_features():
    return Features({
        "image": ImageFeature(),
        "episode_id": Value("string"),
        "task_id": Value("string"),
        "program": Value("string"),
        "output_json": Value("string"),
        "prompt": Value("string"),
        "completion": Value("string"),
        "verification": Value("string"),
        "episode_json": Value("string"),
        "image_usage": Value("string"),
    })


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(data)
    return hasher.hexdigest()


def rows_from_shard(source):
    """Read adjacent PNG/JSON pairs without extracting or buffering a shard."""
    current, payloads, seen = None, {}, set()
    with tarfile.open(source, "r:") as archive:
        for member in archive:
            if not member.isfile() or not re.fullmatch(r"[A-Za-z0-9_-]+\.(png|json)", member.name):
                raise ValueError("Unexpected or unsafe source member: " + member.name)
            key, extension = member.name.rsplit(".", 1)
            if current is not None and key != current:
                raise ValueError("Nonadjacent or incomplete PNG/JSON pair: " + current)
            if key in seen or extension in payloads:
                raise ValueError("Duplicate episode member: " + member.name)
            current = key
            payloads[extension] = archive.extractfile(member).read()
            if len(payloads) != 2:
                continue
            record = json.loads(payloads["json"])
            if (record.get("episode_id") != key
                    or not record.get("verification", {}).get("all_exact")
                    or not all(record.get(field) for field in
                               ("task_id", "program", "output_json", "prompt", "completion"))):
                raise ValueError("Incomplete or unverified combined record: " + key)
            with Image.open(io.BytesIO(payloads["png"])) as png:
                if png.format != "PNG":
                    raise ValueError("Expected PNG source image: " + key)
                png.verify()
            yield dict(image={"bytes": payloads["png"], "path": None},
                       **{field: record[field] for field in
                          ("episode_id", "task_id", "program", "output_json", "prompt", "completion")},
                       verification="All demonstration and query grids exact",
                       episode_json=payloads["json"].decode("utf-8"),
                       image_usage="Human audit only: includes query answers; train on prompt to completion.")
            seen.add(key)
            current, payloads = None, {}
    if payloads:
        raise ValueError("Incomplete final PNG/JSON pair: " + current)
    if not seen:
        raise ValueError("Empty source shard")


def write_arrow_index(source, destination, batch_rows=16):
    """Write one bounded IPC stream, preserving every source episode exactly.

    Call after a VisualShardWriter TAR is finalized. Publish the returned Arrow
    file under viewer/<split>/ and configure ONLY those Arrow files as viewer
    data_files. Keep source PNG/JSON archives outside the viewer file pattern.
    """
    source, destination = Path(source), Path(destination)
    if source.suffix != ".tar" or destination.suffix != ".arrow":
        raise ValueError("Expected a .tar source and .arrow index destination")
    if not 1 <= batch_rows <= 1000:
        raise ValueError("batch_rows must be between 1 and 1000")
    source_hash = digest(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".arrow.tmp")
    schema = index_features().arrow_schema
    count = 0
    ids = hashlib.sha256()
    try:
        with temporary.open("wb") as stream:
            options = pa.ipc.IpcWriteOptions(compression="zstd")
            with pa.ipc.new_stream(stream, schema, options=options) as writer:
                batch = []
                for row in rows_from_shard(source):
                    batch.append(row)
                    ids.update((row["episode_id"] + "\n").encode())
                    count += 1
                    if len(batch) == batch_rows:
                        writer.write_table(pa.Table.from_pylist(batch, schema=schema))
                        batch.clear()
                if batch:
                    writer.write_table(pa.Table.from_pylist(batch, schema=schema))
        if source_hash != digest(source):
            raise ValueError("Source shard changed while indexing")
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return dict(file=destination.name, episodes=count, bytes=destination.stat().st_size,
                sha256=digest(destination), source_file=source.name,
                source_sha256=source_hash, episode_order_sha256=ids.hexdigest(),
                format="arrow-ipc-stream-zstd", image_storage="exact embedded source PNG bytes",
                record_scope="One episode with both program and output grids", batch_rows=batch_rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--batch-rows", type=int, default=16)
    args = parser.parse_args()
    print(json.dumps(write_arrow_index(args.source, args.destination, args.batch_rows), indent=2))


if __name__ == "__main__":
    main()
