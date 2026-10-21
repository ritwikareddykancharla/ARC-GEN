import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
import pyarrow as pa

from PIL import Image
from .program_targets import make_record
from .test_program_targets import ProgramTargets
from .visual_shards import VisualShardWriter


class VisualShards(unittest.TestCase):
    def test_one_failed_orientation_rejects_whole_base_episode(self):
        from unittest.mock import patch
        from . import build_million as builder
        from .runtime import reference
        from .program_targets import TargetError
        tid = "00dbd492"
        fixture = reference(tid)["canonical"]
        rows = []
        for index, pair in enumerate((fixture["train"] + fixture["test"])[:4]):
            rows.append(dict(pair, task_id=tid, split="train", seed=index,
                             parameters="{}", generator_mode="test_fixture",
                             input_hash=builder.digest(pair["input"]),
                             canonical_input_hash=builder.canonical_input(pair["input"]),
                             stratum=builder.stratum(pair)))
        self.assertEqual(len({r["canonical_input_hash"] for r in rows}), 4)
        def reject_quarter_turn(episode, **kwargs):
            if episode["d4_transform"] == 1:
                raise TargetError("Deliberately wrong quarter-turn program")
            return make_record(episode, **kwargs)
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(builder, "OUT", Path(directory)), \
                patch.object(builder, "OUTPUT_FORMAT", "program-grid-png"), \
                patch.object(builder, "make_record", side_effect=reject_quarter_turn):
            pool = Path(directory) / "pools" / (tid + ".parquet")
            pool.parent.mkdir()
            builder.pq.write_table(builder.pa.Table.from_pylist(rows), pool)
            result = builder.make_episodes((tid, {"train": {rows[0]["stratum"]: 1}}))
            self.assertEqual(result["splits"]["train"]["fresh_episodes"], 0)
            self.assertEqual(result["splits"]["train"]["episodes"], 0)
            self.assertGreater(result["splits"]["train"]["failures"]["post_gate_program_rejected"], 0)
            self.assertFalse(list(Path(directory).rglob("*.tar")))

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
            self.assertEqual(len(writer.paths), 4)
            archives = [p for p in writer.paths if p.suffix == ".tar"]
            indexes = [p for p in writer.paths if p.suffix == ".arrow"]
            self.assertEqual(len(archives), 2)
            self.assertEqual(len(indexes), 2)
            self.assertEqual([p.name for p in archives], ["00576224-00000.tar", "00576224-00001.tar"])
            for path in archives:
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
                    indexed = pa.ipc.open_stream(path.with_suffix(".arrow")).read_all().to_pylist()
                    self.assertEqual(len(indexed), 1)
                    self.assertEqual(indexed[0]["image"]["bytes"], archive.extractfile(png).read())
                    self.assertEqual(json.loads(indexed[0]["episode_json"]), row)
            self.assertEqual(sum(m["episodes"] for m in writer.manifest), 2)
            self.assertTrue(all(m["viewer_index"]["episodes"] == m["episodes"] for m in writer.manifest))
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

    def test_card_uses_only_arrow_and_keeps_combined_family_counts(self):
        from .visual_card import card
        text = card(dict(status="test", train_episodes=24, train_fresh_episodes=3,
                         target_train_fresh_episodes=1120000,
                         episode_files={"train": ["shards/train/00576224-00000.tar",
                                                  "shards/train/00576224-00000.arrow",
                                                  "shards/train/00dbd492-00000.arrow"],
                                        "validation": ["shards/validation/00576224-00000.arrow"]}))
        metadata = json.loads(text.split("---\n")[1])
        self.assertEqual(len(metadata["configs"]), 2)
        self.assertEqual(metadata["configs"][0]["config_name"], "family_00576224")
        self.assertEqual(sum(bool(c.get("default")) for c in metadata["configs"]), 1)
        paths = [p for c in metadata["configs"] for s in c["data_files"] for p in s["path"]]
        self.assertTrue(all(p.endswith(".arrow") for p in paths))
        self.assertIn("24 published training episodes", text)
