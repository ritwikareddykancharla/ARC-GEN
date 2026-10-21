from copy import deepcopy
import json
import io
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import tempfile
import tarfile
import unittest
from unittest.mock import Mock, patch

from . import repair_episode_shortfalls as repair

TID = "00576224"
OTHER = "00dbd492"
REV = "a" * 40

# Importable deterministic builder for real spawn-process orchestration tests.
OUT = None
SEED = 0
OUTPUT_FORMAT = "legacy"


def make_episodes(arg):
    tid, quotas = arg
    spec = repair.read(OUT / "pools" / (tid + ".parquet"))
    assert SEED == 17 and OUTPUT_FORMAT == "program-grid-png"
    assert os.environ["ARCGEN_SOURCE_COMMIT"] == "new-source"
    stage = OUT.parents[1]
    assert not (stage / "shards").exists(), "Parent promoted while a worker was active"
    assert not (stage / "manifest.json").exists(), "Parent finalized before construction ended"
    event = {"task_id": tid, "pid": os.getpid(), "stage": stage.name}
    fd = os.open(spec["events"], os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, (json.dumps(event) + "\n").encode())
    finally:
        os.close(fd)
    if spec.get("barrier") and "parallel" in stage.name:
        deadline = time.monotonic() + 10
        while True:
            seen = [json.loads(line) for line in Path(spec["events"]).read_text().splitlines()]
            if len({e["task_id"] for e in seen if e["stage"] == stage.name}) == 2:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("Both isolated workers did not start")
            time.sleep(0.01)
    time.sleep(spec.get("delay", 0))
    if spec.get("failure"):
        partial = OUT / "shards/train" / (tid + "-partial.tar")
        partial.parent.mkdir(parents=True)
        partial.write_bytes(b"must never be promoted")
        if spec["failure"] == "exit":
            os._exit(23)
        raise RuntimeError("synthetic family failure")
    result = report(tid, spec["train"], spec["validation"], "new")
    for data in result["splits"].values():
        if not data["episodes"]:
            continue
        metas = []
        for name in data["files"]:
            target = OUT / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(name.encode())
            metas.append({"file": target.name, "sha256": repair.sha256(target), "episodes": data["episodes"]})
        data["shards"] = [{**metas[0], "viewer_index": metas[1]}]
    assert not (stage / "shards").exists(), "Early promotion before the last worker returned"
    return result


def report(tid, train=2, validation=1, tag="old"):
    result = {"task_id": tid, "splits": {}}
    for split, n in (("train", train), ("validation", validation)):
        paths = [f"shards/{split}/{tid}-{tag}.{suffix}" for suffix in ("tar", "arrow")] if n else []
        result["splits"][split] = {"files": paths, "episodes": n * 8, "fresh_episodes": n,
                                   "symmetric_variants_removed": 0, "failures": {}, "shards": []}
    return result


class RepairShortfallsTests(unittest.TestCase):
    def parallel_fixture(self, root, failure=None, barrier=False):
        manifest, allocation, reports = self.fixture(root)
        reports[OTHER] = report(OTHER)
        manifest.update(repair.totals(reports))
        repair.write(root / "manifest.json", manifest)
        for tid, r in reports.items():
            repair.write(root / "episode_reports" / (tid + ".json"), r)
            for split in r["splits"].values():
                for name in split["files"]:
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b"original published bytes")
            path = root / "pools" / (tid + ".parquet")
            repair.write(path, {"train": 4, "validation": 1, "events": str(root / "events.jsonl"),
                                "barrier": barrier, "delay": 0.1 if tid == TID else 0,
                                "failure": failure if tid == TID else None})
            repair.write(root / "pool_reports" / (tid + ".json"), {
                "task_id": tid, "complete": True, "seed": 17, "source_signature": "original-signature",
                "sha256": repair.sha256(path)})
        return manifest, allocation, reports

    def fixture(self, root):
        reports = {TID: report(TID), OTHER: report(OTHER, 4)}
        manifest = {"status": "complete_with_shortfall", "seed": 17, "source_commit": "old-source",
                    "output_format": "program-grid-png", "target_train_fresh_episodes": 8,
                    "target_validation_fresh_episodes": 2, "errors": [], **repair.totals(reports)}
        allocation = {"train_by_family": {TID: {"3|same": 4}, OTHER: {"3|same": 4}},
                      "validation_by_family": {TID: {"3|same": 1}, OTHER: {"3|same": 1}}}
        repair.write(root / "manifest.json", manifest)
        repair.write(root / "allocation.json", allocation)
        for tid, r in reports.items():
            repair.write(root / "episode_reports" / (tid + ".json"), r)
        pool = root / "pools" / (TID + ".parquet")
        pool.parent.mkdir()
        pool.write_bytes(b"hash-protected test pool")
        repair.write(root / "pool_reports" / (TID + ".json"), {
            "task_id": TID, "complete": True, "seed": 17, "source_signature": "original-signature",
            "sha256": repair.sha256(pool), "termination_reason": "family_time_budget", "pairs": 50})
        return manifest, allocation, reports

    def builder(self, candidate):
        builder = SimpleNamespace(OUT=None, SEED=0, OUTPUT_FORMAT="legacy")
        def run(arg):
            self.assertEqual(arg[0], TID)
            self.assertEqual(set(arg[1]), {"train", "validation"})
            self.assertEqual(builder.SEED, 17)
            self.assertEqual(builder.OUTPUT_FORMAT, "program-grid-png")
            result = deepcopy(candidate)
            for split, data in result["splits"].items():
                if not data["episodes"]:
                    continue
                metas = []
                for path in data["files"]:
                    target = builder.OUT / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(path.encode())
                    metas.append({"file": target.name, "sha256": repair.sha256(target), "episodes": data["episodes"]})
                data["shards"] = [{**metas[0], "viewer_index": metas[1]}]
            return result
        builder.make_episodes = Mock(side_effect=run)
        return builder

    def test_refresh_adds_old_quota_fulfilled_family_without_changing_validation(self):
        from . import build_million as builder
        old = {'train_by_family': {TID: {'3|same': 98}, OTHER: {'3|same': 1000}},
               'validation_by_family': {TID: {'3|same': 10}},
               'train': {'desired': {'3|same': 2000}}, 'validation': {'allocated': 10}}
        manifest = {'seed': 17, 'target_train_fresh_episodes': 2000, 'errors': []}
        pools = {TID: {'task_id': TID, 'complete': True, 'train_canonical': 49,
                       'train_strata': {'3|same': 1167}},
                 OTHER: {'task_id': OTHER, 'complete': True, 'train_canonical': 1000,
                         'train_strata': {'3|same': 1200}}}
        reports = {TID: report(TID,98,10), OTHER: report(OTHER,1000,0)}
        self.assertEqual(repair.selection(manifest,old,reports),{})
        refreshed = repair.refresh_training_allocation(old,manifest,pools,builder)
        self.assertEqual(refreshed['train_by_family'][TID],{'3|same':1000})
        self.assertEqual(refreshed['train']['family_capacity'][TID],1000)
        self.assertEqual(refreshed['train_by_family'][OTHER],old['train_by_family'][OTHER])
        self.assertEqual(refreshed['validation_by_family'],old['validation_by_family'])
        self.assertEqual(refreshed['validation'],old['validation'])
        self.assertEqual(set(repair.selection(manifest,refreshed,reports)),{TID})
        self.assertFalse(refreshed['training_quota_refresh']['shortfall_approval'])
        self.assertEqual(old['train_by_family'][TID],{'3|same':98})

    def test_refresh_rejects_quota_regression_and_never_pads_ineligible_pool(self):
        from . import build_million as builder
        old={'train_by_family':{TID:{'3|same':98}},'train':{'desired':{'3|same':1000}}}
        manifest={'seed':17,'target_train_fresh_episodes':1000}
        pools={TID:{'task_id':TID,'complete':True,'train_canonical':3,'train_strata':{'3|same':1200}}}
        with self.assertRaisesRegex(ValueError,'reduce'):
            repair.refresh_training_allocation(old,manifest,pools,builder)
        old['train_by_family'][TID]={}
        refreshed=repair.refresh_training_allocation(old,manifest,pools,builder)
        self.assertEqual(refreshed['train_by_family'][TID],{})
        self.assertEqual(refreshed['train']['allocation_shortfall'],1000)

    def test_selects_actual_shortfalls_and_errors_not_completed_families(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest, allocation, reports = self.fixture(Path(temp))
            self.assertEqual(set(repair.selection(manifest, allocation, reports)), {TID})
            manifest["errors"] = [{"task_id": OTHER, "stage": "episodes"}]
            self.assertEqual(set(repair.selection(manifest, allocation, reports)), {TID, OTHER})

    def test_repairs_both_splits_replaces_files_recounts_and_preserves_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, allocation, reports = self.fixture(root)
            builder = self.builder(report(TID, 4, tag="new"))
            plan = repair.stage_repairs(root, root / "stage", manifest, allocation, reports, [TID],
                                        REV, "new-source", {"kind": "terminal_manifest"}, builder)
            new = repair.read(root / "stage/manifest.json")
            self.assertEqual(new["train_fresh_episodes"], 8)
            self.assertEqual(new["train_episodes"], 64)
            self.assertEqual(new["validation_fresh_episodes"], 2)
            self.assertEqual(new["status"], "complete")
            self.assertEqual(plan["accepted_families"], [TID])
            self.assertEqual(len(plan["delete_files"]), 4)
            self.assertEqual(new["source_commit"], "old-source")
            record = repair.read(root / f"stage/episode_reports/{TID}.json")
            provenance = record["repair_provenance"]
            self.assertEqual(provenance["source_pool_report"]["source_signature"], "original-signature")
            self.assertEqual(provenance["source_pool_report"]["termination_reason"], "family_time_budget")
            self.assertEqual(provenance["episode_repair_commit"], "new-source")
            self.assertEqual(builder.OUT, None)
            self.assertIn("64 published training episodes", (root / "stage/README.md").read_text())
            self.assertFalse(list((root / "stage/work").rglob("*.parquet")))

    def test_regression_in_validation_preserves_whole_original_family(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, allocation, reports = self.fixture(root)
            plan = repair.stage_repairs(root, root / "stage", manifest, allocation, reports, [TID],
                                        REV, "new", {}, self.builder(report(TID, 4, 0, "new")))
            self.assertEqual(plan["accepted_families"], [])
            self.assertEqual(plan["outcomes"][TID]["status"], "regression_preserved_original")
            self.assertEqual(repair.read(root / "stage/manifest.json")["episode_files"], manifest["episode_files"])
            self.assertFalse((root / "stage/shards").exists())

    def test_missing_and_hash_corrupt_pool_never_invoke_constructor(self):
        for mode in ("missing", "corrupt"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest, allocation, reports = self.fixture(root)
                pool = root / "pools" / (TID + ".parquet")
                if mode == "missing":
                    pool.unlink()
                else:
                    pool.write_bytes(b"corrupt")
                builder = self.builder(report(TID, 4))
                plan = repair.stage_repairs(root, root / "stage", manifest, allocation, reports, [TID],
                                            REV, "new", {}, builder)
                builder.make_episodes.assert_not_called()
                self.assertEqual(plan["outcomes"][TID]["status"], "missing_pool" if mode == "missing" else "invalid_pool")

    def test_active_manifest_requires_terminal_job_and_never_cancels(self):
        api = Mock()
        api.inspect_job.return_value = SimpleNamespace(status=SimpleNamespace(stage="RUNNING"))
        with self.assertRaisesRegex(RuntimeError, "active"):
            repair.require_terminal({"status": "constructing_episodes"})
        with self.assertRaisesRegex(RuntimeError, "active"):
            repair.require_terminal({"status": "constructing_episodes"}, api, "job")
        with self.assertRaisesRegex(RuntimeError, "active"):
            repair.require_terminal({"status": "complete"}, api, "job")
        api.inspect_job.return_value.status.stage = "ERROR"
        proof = repair.require_terminal({"status": "constructing_episodes"}, api, "job")
        self.assertEqual(proof["stage"], "ERROR")
        api.cancel_job.assert_not_called()

    def test_publish_rejects_moved_head_and_pins_atomic_commit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            stage = root / "stage"
            stage.mkdir()
            (stage / "manifest.json").write_text("{}")
            api = Mock()
            api.dataset_info.return_value.sha = "b" * 40
            with self.assertRaisesRegex(RuntimeError, "changed"):
                repair.publish_stage(api, "repo", REV, root, stage, {"delete_files": []})
            api.create_commit.assert_not_called()
            api.dataset_info.return_value.sha = REV
            repair.publish_stage(api, "repo", REV, root, stage, {"delete_files": ["shards/train/obsolete.tar"]})
            self.assertEqual(api.create_commit.call_args.kwargs["parent_commit"], REV)
            self.assertEqual(len(api.create_commit.call_args.kwargs["operations"]), 2)

    def test_incomplete_source_reports_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest, _, reports = self.fixture(Path(temp))
            del reports[OTHER]
            with self.assertRaisesRegex(ValueError, "account"):
                repair.verify_source_counts(manifest, reports)

    def test_local_dry_run_with_active_source_does_not_touch_job_api(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, _, _ = self.fixture(root)
            manifest["status"] = "constructing_episodes"
            repair.write(root / "manifest.json", manifest)
            repair.write(root / "repair-snapshot.json", {"repo": "test/repo", "revision": REV})
            argv = ["repair", "--repo", "test/repo", "--revision", REV, "--snapshot", str(root),
                    "--stage", str(root / "stage"), "--offline", "--source-job-id", "job"]
            with patch("sys.argv", argv), patch("huggingface_hub.HfApi") as api, \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                repair.main()
            api.assert_not_called()
            self.assertEqual(json.loads(output.getvalue())["mode"], "plan_only")
            self.assertFalse((root / "stage").exists())

    def test_finite_migration_scans_shared_orbit_in_nonfinite_family(self):
        from . import build_million as builder
        from .finite_input_policy import GLOBAL_TRAIN_ORBITS, POLICY_SIGNATURE
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = {"completed_pools": 2, "seed": 17, "source_commit": "old-source"}
            for tid in ("833966f4", "feca6190"):
                rows = []
                for shift in range(4):
                    g = [[(n + shift) % 10] for n in range(5)]
                    canonical = builder.canonical_input(g)
                    self.assertIn(canonical, GLOBAL_TRAIN_ORBITS)
                    rows.append({"task_id": tid, "input": g, "output": g,
                                 "input_hash": builder.digest(g), "canonical_input_hash": canonical,
                                 "split": "validation", "stratum": "5|same"})
                path = root / "pools" / (tid + ".parquet")
                path.parent.mkdir(exist_ok=True)
                builder.pq.write_table(builder.pa.Table.from_pylist(rows), path)
                repair.write(root / "pool_reports" / (tid + ".json"), {
                    "task_id": tid, "complete": True, "seed": 17, "pairs": 4, "requested_pool_size": 4,
                    "source_signature": "original-" + tid, "sha256": repair.sha256(path),
                    "train_strata": {}, "validation_strata": {"5|same": 4},
                    "train_canonical": 0, "validation_canonical": 1})
            overrides, reports, affected, audit = repair.prepare_finite_pools(root, root / "prepared", manifest, REV, builder)
            self.assertEqual(affected, {"833966f4", "feca6190"})
            self.assertEqual(audit["policy_signature"], POLICY_SIGNATURE)
            self.assertEqual(audit["all_complete_pools_scanned"], 2)
            parallel, parallel_reports, parallel_affected, parallel_audit = repair.prepare_finite_pools(
                root, root / "parallel-prepared", manifest, REV, builder, workers=2)
            self.assertEqual(parallel_reports, reports)
            self.assertEqual(parallel_affected, affected)
            self.assertEqual(parallel_audit, audit)
            for tid in affected:
                self.assertEqual(parallel[tid]["sha256"], overrides[tid]["sha256"])
            for tid in affected:
                self.assertEqual(reports[tid]["validation_strata"], {})
                self.assertEqual(reports[tid]["train_strata"], {"5|same": 4})
                self.assertNotIn("source_signature", reports[tid])
                self.assertEqual(reports[tid]["split_migration"]["original_source_signature"], "original-" + tid)
                self.assertEqual(reports[tid]["original_pool_provenance"]["source_commit"], "old-source")
                source = builder.pq.read_table(root / "pools" / (tid + ".parquet")).to_pylist()
                migrated = builder.pq.read_table(overrides[tid]["path"]).to_pylist()
                self.assertTrue(all(p["split"] == "validation" for p in source))
                self.assertTrue(all(p["split"] == "train" for p in migrated))
            (root / "pools/feca6190.parquet").unlink()
            with self.assertRaises(FileNotFoundError):
                repair.prepare_finite_pools(root, root / "missing-audit", manifest, REV, builder)
            with self.assertRaises(FileNotFoundError):
                repair.prepare_finite_pools(root, root / "parallel-missing-audit", manifest, REV, builder, workers=2)
            self.assertFalse((root / "parallel-missing-audit/finite-policy-audit.json").exists())

    def test_finite_allocation_recovers_zero_train_family_without_changing_other_quotas(self):
        from . import build_million as builder
        recounted = {
            "833966f4": {"task_id": "833966f4", "train_strata": {"5|same": 20},
                         "train_canonical": 1, "validation_strata": {}, "validation_canonical": 0},
            OTHER: {"task_id": OTHER, "train_strata": {"5|same": 10}, "train_canonical": 10,
                    "validation_strata": {}, "validation_canonical": 0}}
        allocation = {"train": {"desired": {"5|same": 1}}, "validation": {"desired": {"5|same": 1}},
                      "train_by_family": {OTHER: {"5|same": 4}}, "validation_by_family": {}}
        manifest = {"seed": 17, "target_train_fresh_episodes": 14, "target_validation_fresh_episodes": 0}
        result = repair.finite_allocation(allocation, manifest, recounted, {"833966f4"}, builder)
        self.assertEqual(result["train_by_family"][OTHER], {"5|same": 4})
        self.assertEqual(sum(result["train_by_family"]["833966f4"].values()), 10)
        self.assertEqual(result["validation_by_family"]["833966f4"], {})
        self.assertEqual(result["train"]["allocated"], 14)

    def test_validation_reduction_requires_hash_verified_explicit_episode_evidence(self):
        from .finite_input_policy import GLOBAL_TRAIN_ORBITS, POLICY_SIGNATURE
        from .build_million import canonical_input
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "shards/validation/feca6190-old.tar"
            path.parent.mkdir(parents=True)
            with tarfile.open(path, "w") as archive:
                for index, grid in enumerate(([[n] for n in range(5)], [[0]])):
                    orbit = canonical_input(grid)
                    row = {"task_id": "feca6190", "split": "validation", "episode_id": f"e{index}",
                           "base_episode_id": f"b{index}", "train": [{"input": grid}] * 3, "test": [{"input": grid}],
                           "canonical_input_hashes": [orbit] * 4}
                    data = json.dumps(row).encode()
                    member = tarfile.TarInfo(f"e{index}.json")
                    member.size = len(data)
                    archive.addfile(member, io.BytesIO(data))
            old = {"task_id": "feca6190", "splits": {
                "train": {"episodes": 8, "fresh_episodes": 1},
                "validation": {"episodes": 2, "fresh_episodes": 2,
                               "shards": [{"file": path.name, "sha256": repair.sha256(path)}]}}}
            evidence = repair.validation_removal_evidence(root, old, POLICY_SIGNATURE)
            self.assertEqual(evidence["episodes"], 1)
            self.assertEqual(evidence["fresh_episodes"], 1)
            self.assertEqual(evidence["removed_episode_ids"], ["e0"])
            new = deepcopy(old)
            new["splits"]["validation"].update(episodes=1, fresh_episodes=1)
            self.assertFalse(repair.nonregressing(old, new))
            self.assertTrue(repair.nonregressing(old, new, evidence))
            new["splits"]["train"]["episodes"] = 7
            self.assertFalse(repair.nonregressing(old, new, evidence))
            path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "SHA256"):
                repair.validation_removal_evidence(root, old, POLICY_SIGNATURE)

    def test_incomplete_global_migration_cannot_publish_even_with_unchanged_head(self):
        api = Mock()
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            repair.publish_stage(api, "repo", REV, Path("unused"), Path("unused"),
                                 {"publishable": False, "delete_files": []})
        api.dataset_info.assert_not_called()
        api.create_commit.assert_not_called()

    def test_serial_parallel_artifacts_match_and_promotion_waits_for_all_workers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, allocation, reports = self.parallel_fixture(root, barrier=True)
            builder = sys.modules[__name__]
            stages = [root / "stage-serial", root / "stage-parallel"]
            plans = [repair.stage_repairs(root, stage, manifest, allocation, reports,
                         [OTHER, TID], REV, "new-source", {}, builder, workers=workers)
                     for stage, workers in zip(stages, (1, 2))]
            self.assertEqual(plans[0]["execution"], {"workers": 1, "start_method": "in_process"})
            self.assertEqual(plans[1]["execution"], {"workers": 2, "start_method": "spawn"})
            self.assertEqual(*[{k: v for k, v in plan.items() if k != "execution"} for plan in plans])
            self.assertEqual(plans[1]["accepted_families"], sorted([TID, OTHER]))
            def hashes(stage):
                result = {}
                for p in stage.rglob("*"):
                    if not p.is_file():
                        continue
                    if p.name in {"manifest.json", "repair-report.json"}:
                        data = repair.read(p)
                        container = data["repair_history"][-1] if p.name == "manifest.json" else data
                        execution = container.pop("execution")
                        self.assertEqual(execution, plans[stages.index(stage)]["execution"])
                        result[str(p.relative_to(stage))] = json.dumps(data, sort_keys=True)
                    else:
                        result[str(p.relative_to(stage))] = repair.sha256(p)
                return result
            self.assertEqual(hashes(stages[0]), hashes(stages[1]))
            events = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
            parallel_pids = {e["pid"] for e in events if e["stage"] == stages[1].name}
            self.assertEqual(len(parallel_pids), 2)
            self.assertNotIn(os.getpid(), parallel_pids)
            self.assertIsNone(builder.OUT)
            self.assertEqual(builder.SEED, 0)
            self.assertEqual(builder.OUTPUT_FORMAT, "legacy")

    def test_parallel_worker_failure_preserves_original_and_blocks_global_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, allocation, reports = self.parallel_fixture(root, failure="exception")
            originals = {p: repair.sha256(p) for p in root.rglob("*") if p.is_file()}
            stage = root / "stage"
            plan = repair.stage_repairs(root, stage, manifest, allocation, reports, [OTHER, TID],
                       REV, "new-source", {}, sys.modules[__name__], workers=2,
                       required_families=[TID, OTHER])
            self.assertEqual(plan["accepted_families"], [OTHER])
            self.assertEqual(plan["outcomes"][TID]["status"], "repair_error_preserved_original")
            self.assertIn("synthetic family failure", plan["outcomes"][TID]["error"])
            self.assertFalse(plan["publishable"])
            self.assertEqual(plan["required_families_not_rebuilt"], [TID])
            self.assertFalse(list(stage.rglob("*partial.tar")))
            self.assertFalse((stage / "episode_reports" / (TID + ".json")).exists())
            self.assertFalse(list((stage / "work").rglob("*.parquet")))
            for path, original in originals.items():
                self.assertEqual(repair.sha256(path), original)
            new = repair.read(stage / "manifest.json")
            for split in repair.SPLITS:
                self.assertTrue(set(reports[TID]["splits"][split]["files"]) <= set(new["episode_files"][split]))
                self.assertFalse(set(reports[TID]["splits"][split]["files"]) & set(plan["delete_files"]))
            repair.finish_finite_stage(stage, root / "never-prepared", plan, allocation, {})
            self.assertFalse((stage / "allocation.json").exists())
            api = Mock()
            with self.assertRaisesRegex(RuntimeError, "incomplete"):
                repair.publish_stage(api, "repo", REV, root, stage, plan)
            api.create_commit.assert_not_called()

    def test_abrupt_worker_exit_preserves_original_and_never_promotes_partial_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, allocation, reports = self.parallel_fixture(root, failure="exit")
            stage = root / "stage"
            plan = repair.stage_repairs(root, stage, manifest, allocation, reports, [TID],
                       REV, "new-source", {}, sys.modules[__name__], workers=2,
                       required_families=[TID])
            self.assertEqual(plan["accepted_families"], [])
            self.assertEqual(plan["outcomes"][TID]["status"], "repair_error_preserved_original")
            self.assertFalse(plan["publishable"])
            self.assertEqual(repair.read(stage / "manifest.json")["episode_files"], manifest["episode_files"])
            self.assertFalse((stage / "shards").exists())
            self.assertFalse(list((stage / "work").rglob("*.parquet")))

    def test_malformed_candidate_does_not_update_manifest_after_failed_promotion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, allocation, reports = self.fixture(root)
            candidate = report(TID, 4, 1, "new")
            del candidate["splits"]["validation"]["failures"]
            stage = root / "stage"
            plan = repair.stage_repairs(root, stage, manifest, allocation, reports,
                       [TID], REV, "new-source", {}, self.builder(candidate))
            self.assertEqual(plan["accepted_families"], [])
            self.assertEqual(plan["outcomes"][TID]["status"], "repair_error_preserved_original")
            self.assertEqual(repair.read(stage / "manifest.json")["episode_files"], manifest["episode_files"])
            self.assertFalse((stage / "shards").exists())

    def test_workers_validation_rejects_threads_or_unimportable_test_builder(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, allocation, reports = self.fixture(root)
            builder = self.builder(report(TID, 4))
            for workers in (0, -1, True):
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    repair.stage_repairs(root, root / "stage", manifest, allocation, reports,
                                         [TID], REV, "new", {}, builder, workers=workers)
            with self.assertRaisesRegex(ValueError, "importable builder module"):
                repair.stage_repairs(root, root / "stage", manifest, allocation, reports,
                                     [TID], REV, "new", {}, builder, workers=2)
            self.assertFalse((root / "stage").exists())


if __name__ == "__main__":
    unittest.main()
