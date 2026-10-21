import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

import pyarrow as pa
from datasets import Features, Image as ImageFeature
from PIL import Image

from .visual_arrow_index import rows_from_shard, write_arrow_index


class VisualArrowIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def shard(self, *, verified=True, png=True, duplicate=False):
        source = self.root / "deadbeef-00000.tar"
        row = dict(episode_id="episode-1", task_id="deadbeef", verification={"all_exact": verified},
                   program="def solve(demos, grid): return grid", output_json='{"outputs":[[[1]]]}',
                   prompt="Demonstrations and query", completion="Program and grid")
        image = io.BytesIO()
        Image.new("RGB", (2, 2), "blue").save(image, format="PNG")
        members = [("episode-1.json", json.dumps(row).encode())]
        if png:
            members.append(("episode-1.png", image.getvalue()))
        if duplicate:
            members.append(members[0])
        with tarfile.open(source, "w") as archive:
            for name, payload in members:
                item = tarfile.TarInfo(name)
                item.size = len(payload)
                archive.addfile(item, io.BytesIO(payload))
        return source

    def test_exact_combined_row_and_image_feature(self):
        source = self.shard()
        target = self.root / "index.arrow"
        result = write_arrow_index(source, target, batch_rows=1)
        table = pa.ipc.open_stream(target).read_all()
        self.assertEqual(result["episodes"], 1)
        self.assertEqual(table.to_pylist(), list(rows_from_shard(source)))
        self.assertIsInstance(Features.from_arrow_schema(table.schema)["image"], ImageFeature)
        Image.open(io.BytesIO(table.to_pylist()[0]["image"]["bytes"])).verify()

    def test_missing_image_unverified_and_duplicate_rejected_atomically(self):
        for kwargs in ({"png": False}, {"verified": False}, {"duplicate": True}):
            with self.subTest(kwargs=kwargs):
                target = self.root / "bad.arrow"
                with self.assertRaises(ValueError):
                    write_arrow_index(self.shard(**kwargs), target)
                self.assertFalse(target.exists())
                self.assertFalse(target.with_suffix(".arrow.tmp").exists())

    def test_batch_rows_must_be_bounded(self):
        for count in (0, 1001):
            with self.subTest(count=count), self.assertRaises(ValueError):
                write_arrow_index(self.shard(), self.root / "index.arrow", count)


if __name__ == "__main__":
    unittest.main()
