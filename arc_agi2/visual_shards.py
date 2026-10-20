"""Lossless PNG + combined program/grid records in bounded WebDataset shards.

The image contains the answer for human inspection. Training consumes the JSON
record's prompt and completion, never the audit image.
"""
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

from .visual_dataset import render


class VisualShardWriter:
    def __init__(self, directory, family, max_records=1000, max_bytes=512 * 1024**2):
        if not re.fullmatch("[0-9a-f]{8}", family):
            raise ValueError("Invalid family identifier")
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.family = family
        self.max_records, self.max_bytes = max_records, max_bytes
        self.archive = None
        self.paths = []
        self.records = 0
        self.shard_records = 0
        self.shard_bytes = 0
        self.seen = set()
        self.manifest = []

    def _finish(self):
        if self.archive is None:
            return
        self.archive.close()
        self.temporary.replace(self.destination)
        self.paths.append(self.destination)
        hasher = hashlib.sha256()
        with self.destination.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024**2), b""):
                hasher.update(chunk)
        self.manifest.append(dict(file=self.destination.name, episodes=self.shard_records,
                                  bytes=self.destination.stat().st_size,
                                  sha256=hasher.hexdigest()))
        self.archive = None

    def write(self, record):
        if not record.get("verification", {}).get("all_exact"):
            raise ValueError("Only verified program-and-grid episodes may be published")
        eid = record["episode_id"]
        if not re.fullmatch("[A-Za-z0-9_-]+", eid) or eid in self.seen:
            raise ValueError("Unsafe or duplicate episode identifier")
        if record["task_id"] != self.family:
            raise ValueError("Record belongs to another family")
        # Serialize before opening a shard, so rendering/encoding failure cannot
        # create a half-record containing an image without its training target.
        image = io.BytesIO()
        render(record).save(image, format="PNG", compress_level=3)
        metadata = dict(record, image_usage="Human audit only: image includes query answer.")
        payloads = [("png", image.getvalue()),
                    ("json", json.dumps(metadata, separators=(",", ":")).encode())]
        nbytes = sum(len(data) for _, data in payloads)
        if self.archive is not None and (
                self.shard_records >= self.max_records
                or self.shard_bytes + nbytes > self.max_bytes):
            self._finish()
        if self.archive is None:
            self.destination = self.directory / f"{self.family}-{len(self.paths):05d}.tar"
            self.temporary = self.destination.with_suffix(".tar.tmp")
            self.archive = tarfile.open(self.temporary, "w")
            self.shard_records = self.shard_bytes = 0
        for extension, data in payloads:
            member = tarfile.TarInfo(f"{eid}.{extension}")
            member.size = len(data)
            member.mtime = 0
            member.mode = 0o644
            self.archive.addfile(member, io.BytesIO(data))
        self.seen.add(eid)
        self.records += 1
        self.shard_records += 1
        self.shard_bytes += nbytes

    def close(self):
        self._finish()

    def abort(self):
        if self.archive is not None:
            self.archive.close()
            self.archive = None
            self.temporary.unlink(missing_ok=True)
        for path in self.paths:
            path.unlink(missing_ok=True)
        self.paths.clear()
