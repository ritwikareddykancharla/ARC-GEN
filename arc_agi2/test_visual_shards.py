import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from PIL import Image
from .program_targets import make_record
from .test_program_targets import ProgramTargets
from .visual_shards import VisualShardWriter


class VisualShards(unittest.TestCase):
    def test_one_image_and_combined_target_per_row_and_shard_rotation(self):
        with tempfile.TemporaryDirectory() as directory:
            writer = VisualShardWriter(directory, "00576224", max_records=1)
            for d4 in range(2):
                episode = ProgramTargets().episode("00576224", d4)
                episode["episode_id"] += f"-d4-{d4}"
                record = make_record(episode)
                writer.write(record)
            writer.close()
            self.assertEqual(writer.records, 2)
            self.assertEqual(len(writer.paths), 2)
            for path in writer.paths:
                with tarfile.open(path) as archive:
                    names = archive.getnames()
                    self.assertEqual(len(names), 2)
                    png = next(n for n in names if n.endswith(".png"))
                    meta = next(n for n in names if n.endswith(".json"))
                    self.assertEqual(png[:-4], meta[:-5])
                    Image.open(io.BytesIO(archive.extractfile(png).read())).verify()
                    row = json.load(archive.extractfile(meta))
                    self.assertEqual(row["mode"], "PROGRAM_AND_GRID")
                    self.assertIn(row["program"].strip(), row["completion"])
                    self.assertEqual(json.loads(row["output_json"])["outputs"], row["solutions"])
            self.assertFalse(list(Path(directory).glob("*.tmp")))

    def test_unverified_and_duplicate_records_are_rejected(self):
        record = make_record(ProgramTargets().episode("00576224"))
        with tempfile.TemporaryDirectory() as directory:
            writer = VisualShardWriter(directory, "00576224")
            with self.assertRaisesRegex(ValueError, "verified"):
                writer.write(dict(record, verification={"all_exact": False}))
            self.assertFalse(list(Path(directory).iterdir()))
            writer.write(record)
            with self.assertRaisesRegex(ValueError, "duplicate"):
                writer.write(record)
            writer.close()
            writer.abort()
            self.assertFalse(list(Path(directory).iterdir()))
