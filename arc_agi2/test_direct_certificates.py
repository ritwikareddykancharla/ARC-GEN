import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from . import direct_certificates as cert
from .audit_direct_candidates import candidate
from .augmentation import transformed
from .program_targets import verify
from .runtime import reference


class Certificates(unittest.TestCase):
    def test_factories_produce_direct_programs_for_all_orientations(self):
        from .program_targets import compile_target, audit_target
        palette = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
        for tid in ("62593bfd", "e4888269", "fc7cae8d", "65b59efc", "142ca369", "f931b4a8"):
            task = reference(tid)["canonical"]
            for d4 in range(8):
                source, _ = compile_target(tid, d4, palette)
                audit_target(tid, source)
                ep = {
                    "train": [{k: transformed(p[k], d4, palette) for k in ("input", "output")}
                              for p in task["train"]],
                    "test": [{"input": transformed(p["input"], d4, palette)} for p in task["test"]],
                    "solutions": [transformed(p["output"], d4, palette) for p in task["test"]],
                }
                self.assertTrue(verify(source, ep)["all_exact"], (tid, d4))
                self.assertNotIn("_episode_inverse", source)
                self.assertNotIn("_episode_forward", source)

    def test_stale_or_incomplete_audits_cannot_admit_program(self):
        tid = "5c2c9af4"
        source, _ = candidate(tid)
        record = dict(task_id=tid, passed=True, fresh_pairs_checked=1000,
                      augmented_pair_checks=8000, unique_base_inputs=1000,
                      **cert.current_hashes(tid, source))
        with tempfile.TemporaryDirectory() as folder, patch.object(cert, "CERTIFICATES", Path(folder)):
            path = Path(folder) / (tid + ".json")
            self.assertIsNone(cert.certified_source(tid))
            for field, bad in (("program_sha256", "stale"),
                               ("constructor_sha256", "stale"),
                               ("augmented_pair_checks", 7999),
                               ("passed", False)):
                path.write_text(json.dumps(dict(record, **{field: bad})))
                self.assertIsNone(cert.certified_source(tid), field)
            path.write_text(json.dumps(record))
            self.assertEqual(cert.certified_source(tid), source)
            task = reference(tid)["canonical"]
            palette = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
            for d4 in range(8):
                ep = {
                    "train": [{k: transformed(p[k], d4, palette)
                               for k in ("input", "output")} for p in task["train"]],
                    "test": [{"input": transformed(p["input"], d4, palette)}
                             for p in task["test"]],
                    "solutions": [transformed(p["output"], d4, palette) for p in task["test"]],
                }
                self.assertTrue(verify(source, ep)["all_exact"])
            self.assertNotIn("_episode_inverse", source)
            self.assertNotIn("_episode_forward", source)
