"""Repair episodes from pinned, hash-verified saved pools; never generate pools.

Default is a read-only plan. --execute builds an isolated local stage; --publish
also commits that entire stage atomically against the pinned source revision.
An active source manifest blocks execution unless --source-job-id is supplied
and HF confirms that job has terminated. No jobs are created or canceled.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
from unittest.mock import patch

SPLITS = ("train", "validation")
TERMINAL = {"complete", "complete_with_shortfall"}
TERMINAL_JOBS = {"COMPLETED", "CANCELED", "ERROR", "DELETED"}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024**2), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_path(name):
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or "\\" in name:
        raise ValueError("Unsafe repository path: " + name)
    return name


def load_reports(root):
    result = {}
    for path in sorted((Path(root) / "episode_reports").glob("*.json")):
        report = read(path)
        tid = report["task_id"]
        if not re.fullmatch("[0-9a-f]{8}", tid) or path.stem != tid:
            raise ValueError("Invalid family report: " + str(path))
        result[tid] = report
    return result


def allocations(allocation):
    result = {}
    for split in SPLITS:
        for tid, quota in allocation.get(split + "_by_family", {}).items():
            if not re.fullmatch("[0-9a-f]{8}", tid):
                raise ValueError("Invalid allocated family")
            if any(not isinstance(v, int) or v < 0 for v in quota.values()):
                raise ValueError("Invalid allocated quota")
            result.setdefault(tid, {s: {} for s in SPLITS})[split] = quota
    return result


def selection(manifest, allocation, reports):
    quotas = allocations(allocation)
    errors = {e.get("task_id") for e in manifest.get("errors", [])}
    result = {}
    for tid in sorted(set(quotas) | errors - {None}):
        if not re.fullmatch("[0-9a-f]{8}", tid):
            raise ValueError("Invalid error family")
        requested = {s: sum(quotas.get(tid, {}).get(s, {}).values()) for s in SPLITS}
        actual = {s: reports.get(tid, {}).get("splits", {}).get(s, {}).get("fresh_episodes", 0)
                  for s in SPLITS}
        if tid in errors or any(actual[s] < requested[s] for s in SPLITS):
            result[tid] = {"requested": requested, "actual": actual,
                           "has_error": tid in errors, "allocated": tid in quotas}
    return result


def require_terminal(manifest, api=None, job_id=None, namespace=None):
    if manifest.get("status") in TERMINAL and not job_id:
        return {"kind": "terminal_manifest", "status": manifest["status"]}
    if api is None or not job_id:
        raise RuntimeError("Source manifest is active; wait for completion or provide a terminal source job ID")
    job = api.inspect_job(job_id=job_id, namespace=namespace)
    stage = getattr(job.status.stage, "value", job.status.stage)
    if stage not in TERMINAL_JOBS:
        raise RuntimeError("Source job is still active: " + str(stage))
    return {"kind": "terminal_job", "job_id": job_id, "namespace": namespace, "stage": stage}


def totals(reports):
    result = {"episode_files": {s: [] for s in SPLITS}}
    for split in SPLITS:
        for field in ("episodes", "fresh_episodes", "symmetric_variants_removed"):
            result[split + "_" + field] = sum(r.get("splits", {}).get(split, {}).get(field, 0)
                                               for r in reports.values())
        result["episode_files"][split] = sorted({safe_path(p) for r in reports.values()
                                                for p in r.get("splits", {}).get(split, {}).get("files", [])})
    result["represented_train_families"] = sum(r.get("splits", {}).get("train", {}).get("episodes", 0) > 0
                                               for r in reports.values())
    return result


def verify_source_counts(manifest, reports):
    computed = totals(reports)
    for split in SPLITS:
        for field in ("episodes", "fresh_episodes"):
            key = split + "_" + field
            if computed[key] != manifest.get(key, 0):
                raise ValueError("Pinned reports do not account for manifest " + key)
        if set(computed["episode_files"][split]) != set(manifest.get("episode_files", {}).get(split, [])):
            raise ValueError("Pinned reports do not account for manifest files: " + split)


def validate_pool(root, tid, manifest, revision):
    path = Path(root) / "pools" / (tid + ".parquet")
    report_path = Path(root) / "pool_reports" / (tid + ".json")
    if not path.exists() or not report_path.exists():
        raise FileNotFoundError("Missing saved pool or pool report")
    report = read(report_path)
    if report.get("task_id") != tid or not report.get("complete"):
        raise ValueError("Saved pool report is incomplete or belongs to another family")
    if not report.get("source_signature") or sha256(path) != report.get("sha256"):
        raise ValueError("Saved pool signature missing or SHA256 mismatch")
    if report.get("seed") != manifest.get("seed"):
        raise ValueError("Saved pool seed differs from source manifest")
    return {"source_dataset_revision": revision, "source_commit": manifest.get("source_commit"),
            "source_pool_report": deepcopy(report), "pool_sha256": report["sha256"],
            "reuse_policy": "Original pool provenance retained; current episode gates recheck every constructed target."}


def nonregressing(old, new):
    return all(new.get("splits", {}).get(s, {}).get(key, 0) >= old.get("splits", {}).get(s, {}).get(key, 0)
               for s in SPLITS for key in ("episodes", "fresh_episodes"))


def verify_artifacts(work, report):
    for split, detail in report["splits"].items():
        expected = set()
        for shard in detail.get("shards", []):
            if shard["episodes"] != shard["viewer_index"]["episodes"]:
                raise ValueError("Repaired source/index episode counts differ")
            for meta in (shard, shard["viewer_index"]):
                if not meta["file"].startswith(report["task_id"] + "-") or "/" in meta["file"]:
                    raise ValueError("Repaired artifact belongs to a different family")
                path = f"shards/{split}/" + meta["file"]
                safe_path(path)
                if sha256(Path(work) / path) != meta["sha256"]:
                    raise ValueError("Repaired shard SHA256 mismatch: " + path)
                expected.add(path)
        if expected != set(detail["files"]):
            raise ValueError("Repaired report files differ from verified shard/index pairs")
        if sum(s["episodes"] for s in detail.get("shards", [])) != detail["episodes"]:
            raise ValueError("Repaired shard count mismatch")


def size_audit(reports, manifest):
    result = {}
    for split in SPLITS:
        hist = {g: {a: Counter() for a in ("height", "width", "longest", "shapes")}
                for g in ("input", "output")}
        relations = Counter()
        for report in reports.values():
            x = report.get("splits", {}).get(split, {})
            relations.update(x.get("relations", {}))
            for g in hist:
                for a in hist[g]:
                    hist[g][a].update(x.get("query_histograms", {}).get(g, {}).get(a, {}))
        result[split] = {"pairs": manifest[split + "_episodes"], **hist, "relations": relations}
    return result


def stage_repairs(snapshot, stage, manifest, allocation, reports, chosen, revision,
                  repair_commit, terminal_proof, builder):
    stage, snapshot = Path(stage), Path(snapshot)
    if stage.exists() and any(stage.iterdir()):
        raise ValueError("Stage must be empty; never overwrite an earlier repair")
    stage.mkdir(parents=True, exist_ok=True)
    verify_source_counts(manifest, reports)
    quotas = allocations(allocation)
    updated = deepcopy(reports)
    outcomes = {}
    accepted = []
    for tid in chosen:
        work = stage / "work" / tid
        promoted = []
        if tid not in quotas:
            outcomes[tid] = {"status": "no_saved_allocation", "needs_pool_or_allocation_repair": True}
            continue
        try:
            provenance = validate_pool(snapshot, tid, manifest, revision)
        except FileNotFoundError as exc:
            outcomes[tid] = {"status": "missing_pool", "error": str(exc)}
            continue
        except ValueError as exc:
            outcomes[tid] = {"status": "invalid_pool", "error": str(exc)}
            continue
        try:
            (work / "pools").mkdir(parents=True)
            shutil.copy2(snapshot / "pools" / (tid + ".parquet"), work / "pools" / (tid + ".parquet"))
            with patch.object(builder, "OUT", work), patch.object(builder, "SEED", manifest["seed"]), \
                    patch.object(builder, "OUTPUT_FORMAT", "program-grid-png"), \
                    patch.dict(os.environ, {"ARCGEN_SOURCE_COMMIT": repair_commit}):
                candidate = builder.make_episodes((tid, quotas[tid]))
            if candidate["task_id"] != tid or set(candidate["splits"]) != set(SPLITS):
                raise ValueError("Repair must return both splits for the same family")
            verify_artifacts(work, candidate)
            if not nonregressing(reports.get(tid, {}), candidate):
                outcomes[tid] = {"status": "regression_preserved_original", "candidate": candidate}
                continue
            candidate["repair_provenance"] = {**provenance, "episode_repair_commit": repair_commit}
            write(work / "episode_reports" / (tid + ".json"), candidate)
            for name in [f"episode_reports/{tid}.json", *[p for x in candidate["splits"].values() for p in x["files"]]]:
                destination = stage / safe_path(name)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(work / name, destination)
                promoted.append(destination)
            updated[tid] = candidate
            accepted.append(tid)
            outcomes[tid] = {"status": "repaired", "remaining": {
                s: {"allocated": sum(quotas[tid][s].values()), "actual": candidate["splits"][s]["fresh_episodes"],
                    "failures": candidate["splits"][s]["failures"],
                    "query_context_shortfalls": len(candidate["splits"][s].get("query_context_shortfalls", []))}
                for s in SPLITS}}
        except Exception as exc:
            for path in promoted:
                path.unlink(missing_ok=True)
            outcomes[tid] = {"status": "repair_error_preserved_original", "error": repr(exc)}
        finally:
            shutil.rmtree(work, ignore_errors=True)
    m = deepcopy(manifest)
    m.update(totals(updated))
    m["errors"] = [e for e in manifest.get("errors", [])
                   if not (e.get("task_id") in accepted and e.get("stage") == "episodes")]
    for split in SPLITS:
        m[split + "_fresh_shortfall"] = max(0, m["target_" + split + "_fresh_episodes"] - m[split + "_fresh_episodes"])
    m["status"] = "complete_with_shortfall" if m["errors"] or any(m[s + "_fresh_shortfall"] for s in SPLITS) else "complete"
    m["repair_history"] = [*m.get("repair_history", []), {
        "source_dataset_revision": revision, "source_commit": manifest.get("source_commit"),
        "episode_repair_commit": repair_commit, "terminal_source_proof": terminal_proof,
        "accepted_families": accepted, "outcomes": outcomes}]
    old_files = set().union(*(set(manifest.get("episode_files", {}).get(s, [])) for s in SPLITS))
    new_files = set().union(*(set(m["episode_files"][s]) for s in SPLITS))
    plan = {"source_dataset_revision": revision, "accepted_families": accepted,
            "delete_files": sorted(old_files - new_files), "outcomes": outcomes,
            "remaining_shortfalls": selection(m, allocation, updated)}
    write(stage / "manifest.json", m)
    write(stage / "size-audit.json", size_audit(updated, m))
    write(stage / "repair-report.json", plan)
    from .visual_card import card
    (stage / "README.md").write_text(card(m))
    return plan


def publish_stage(api, repo, revision, snapshot, stage, plan, job_id=None, namespace=None):
    if api.dataset_info(repo, revision="main").sha != revision:
        raise RuntimeError("Dataset changed since pinned revision; rebuild the repair against the new head")
    require_terminal(read(Path(snapshot) / "manifest.json"), api, job_id, namespace)
    from huggingface_hub import CommitOperationAdd, CommitOperationDelete
    paths = sorted(p for p in Path(stage).rglob("*") if p.is_file() and "work" not in p.relative_to(stage).parts)
    operations = [CommitOperationAdd(path_in_repo=str(p.relative_to(stage)), path_or_fileobj=str(p)) for p in paths]
    operations += [CommitOperationDelete(path_in_repo=safe_path(p)) for p in plan["delete_files"]]
    return api.create_commit(repo, repo_type="dataset", parent_commit=revision,
                             operations=operations, commit_message="Repair episode shortfalls from verified saved pools")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="ritwika96/arc-agi2-program-grid-sft")
    ap.add_argument("--revision", required=True, help="Exact 40-character HF dataset commit")
    ap.add_argument("--snapshot", type=Path, required=True, help="Pinned metadata/pool download directory")
    ap.add_argument("--stage", type=Path, required=True)
    ap.add_argument("--offline", action="store_true", help="Use an already downloaded pinned snapshot")
    ap.add_argument("--execute", action="store_true", help="Build local repair artifacts; default only plans")
    ap.add_argument("--publish", action="store_true", help="Also commit atomically; implies --execute")
    ap.add_argument("--source-job-id")
    ap.add_argument("--namespace")
    ap.add_argument("--tasks", nargs="+")
    args = ap.parse_args()
    if not re.fullmatch("[0-9a-f]{40}", args.revision):
        ap.error("--revision must be an exact commit SHA, never main or a moving tag")
    if args.offline and args.publish:
        ap.error("--publish requires online head/job checks")
    from huggingface_hub import HfApi, snapshot_download, hf_hub_download
    api = None if args.offline else HfApi()
    if api:
        marker = args.snapshot / "repair-snapshot.json"
        if args.snapshot.exists() and any(args.snapshot.iterdir()):
            if not marker.exists() or read(marker) != {"repo": args.repo, "revision": args.revision}:
                raise ValueError("Use an empty snapshot directory or the same recorded pinned revision")
        snapshot_download(args.repo, repo_type="dataset", revision=args.revision, local_dir=args.snapshot,
                          allow_patterns=["manifest.json", "allocation.json", "episode_reports/*.json", "pool_reports/*.json"])
        write(args.snapshot / "repair-snapshot.json", {"repo": args.repo, "revision": args.revision})
    if read(args.snapshot / "repair-snapshot.json") != {"repo": args.repo, "revision": args.revision}:
        raise ValueError("Snapshot provenance does not match requested pinned revision")
    manifest, allocation = read(args.snapshot / "manifest.json"), read(args.snapshot / "allocation.json")
    if manifest.get("output_format") != "program-grid-png":
        raise ValueError("Only combined program/grid visual datasets can be repaired")
    reports = load_reports(args.snapshot)
    verify_source_counts(manifest, reports)
    chosen = selection(manifest, allocation, reports)
    if args.tasks:
        if not set(args.tasks) <= set(chosen):
            ap.error("--tasks must select only shortfall/error families")
        chosen = {tid: chosen[tid] for tid in args.tasks}
    if not (args.execute or args.publish):
        print(json.dumps({"mode": "plan_only", "source_status": manifest["status"], "families": chosen}, indent=2))
        return
    terminal = require_terminal(manifest, api, args.source_job_id, args.namespace)
    if api:
        from huggingface_hub.errors import EntryNotFoundError
        for tid in chosen:
            try:
                hf_hub_download(args.repo, f"pools/{tid}.parquet", repo_type="dataset", revision=args.revision, local_dir=args.snapshot)
            except EntryNotFoundError:
                pass  # Report missing pools; do not generate replacements or fabricate quota.
    repair_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1], text=True).strip()
    from . import build_million as builder
    plan = stage_repairs(args.snapshot, args.stage, manifest, allocation, reports, chosen,
                         args.revision, repair_commit, terminal, builder)
    if args.publish:
        commit = publish_stage(api, args.repo, args.revision, args.snapshot, args.stage, plan,
                               args.source_job_id, args.namespace)
        print(json.dumps({"published_revision": commit.oid, "accepted_families": plan["accepted_families"]}))
    else:
        print(json.dumps({"mode": "local_stage_only", "stage": str(args.stage), **plan}, indent=2))


if __name__ == "__main__":
    main()
