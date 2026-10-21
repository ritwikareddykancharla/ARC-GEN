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
import tarfile
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
    signature = report.get("source_signature") or report.get("split_migration", {}).get("original_source_signature")
    if not signature or sha256(path) != report.get("sha256"):
        raise ValueError("Saved pool signature missing or SHA256 mismatch")
    if report.get("seed") != manifest.get("seed"):
        raise ValueError("Saved pool seed differs from source manifest")
    return {"source_dataset_revision": revision, "source_commit": manifest.get("source_commit"),
            "source_pool_report": deepcopy(report), "pool_sha256": report["sha256"],
            "reuse_policy": "Original pool provenance retained; current episode gates recheck every constructed target."}


def nonregressing(old, new, validation_removals=None):
    removed = validation_removals or {}
    return all(new.get("splits", {}).get(s, {}).get(key, 0) >=
               old.get("splits", {}).get(s, {}).get(key, 0) - (removed.get(key, 0) if s == "validation" else 0)
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


def prepare_finite_pools(snapshot, destination, manifest, revision, builder):
    """Audit every complete pool before exposing any globally reserved orbit."""
    from .finite_input_policy import FINITE_INPUT_TASK_IDS, POLICY_SIGNATURE
    destination, snapshot = Path(destination), Path(snapshot)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Finite-policy staging directory must be empty")
    originals = {p.stem: read(p) for p in (snapshot / "pool_reports").glob("*.json") if read(p).get("complete")}
    if len(originals) != manifest["completed_pools"]:
        raise ValueError("Global migration requires every completed saved pool report")
    overrides, recounted, affected = {}, {}, set()
    for tid, original in sorted(originals.items()):
        provenance = validate_pool(snapshot, tid, manifest, revision)
        rows = builder.pq.read_table(snapshot / "pools" / (tid + ".parquet")).to_pylist()
        migrated, report, migration = builder.repartition_pool(rows, original)
        if not migration["original_source_signature"]:
            migration["original_source_signature"] = original.get("split_migration", {}).get("original_source_signature")
        report["split_migration"] = migration
        if migration["policy_signature"] != POLICY_SIGNATURE:
            raise ValueError("Repartition helper used a different finite-input policy")
        path = destination / "pools" / (tid + ".parquet")
        path.parent.mkdir(parents=True, exist_ok=True)
        # Unchanged bytes stay unchanged, while all reports are recounted.
        if migrated == rows:
            shutil.copy2(snapshot / "pools" / (tid + ".parquet"), path)
        else:
            builder.pq.write_table(builder.pa.Table.from_pylist(migrated,
                schema=builder.pq.read_schema(snapshot / "pools" / (tid + ".parquet"))), path, compression="zstd")
        report["sha256"] = sha256(path)
        report["original_pool_provenance"] = provenance
        write(destination / "pool_reports" / (tid + ".json"), report)
        overrides[tid] = {"path": str(path), "sha256": report["sha256"], "migration": migration}
        recounted[tid] = report
        if tid in FINITE_INPUT_TASK_IDS or migration["requires_episode_rebuild"]:
            affected.add(tid)
    audit = {"policy_signature": POLICY_SIGNATURE, "source_dataset_revision": revision,
             "all_complete_pools_scanned": len(recounted), "affected_families": sorted(affected),
             "retained_nonempty_pools": sum(bool(r["complete"]) for r in recounted.values()),
             "split_changed_families": sorted(t for t, x in overrides.items() if x["migration"]["requires_episode_rebuild"])}
    write(destination / "finite-policy-audit.json", audit)
    return overrides, recounted, affected, audit


def finite_allocation(original, manifest, recounted, affected, builder):
    """Preserve unaffected quotas; allocate remaining budget using audited support."""
    result = deepcopy(original)
    for split in SPLITS:
        retained = {t: q for t, q in original.get(split + "_by_family", {}).items() if t not in affected}
        target = manifest["target_" + split + "_fresh_episodes"]
        remaining = target - sum(sum(q.values()) for q in retained.values())
        if remaining < 0:
            raise ValueError("Existing unaffected quotas exceed total target")
        desired = original[split]["desired"]
        with patch.object(builder, "SEED", manifest["seed"]):
            replacement, _ = builder.allocate([recounted[t] for t in sorted(affected)], split, remaining, desired)
            _, all_stats = builder.allocate(list(recounted.values()), split, target, desired)
        # Explicit empty allocations ensure retired validation splits are rebuilt.
        combined = {**retained, **{t: replacement.get(t, {}) for t in sorted(affected)}}
        actual = Counter()
        for q in combined.values():
            actual.update(q)
        used = {t: sum(q.values()) for t, q in combined.items()}
        result[split + "_by_family"] = combined
        result[split] = {"requested": target, "allocated": sum(used.values()),
                         "allocation_shortfall": target - sum(used.values()),
                         "desired": desired, "actual": dict(actual), "family_allocated": used,
                         "family_capacity": all_stats["family_capacity"],
                         "policy": "Preserve unaffected quotas; reallocate affected families from globally re-split saved support."}
    result["finite_policy_source_allocation_sha256"] = hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest()
    return result



def refresh_training_allocation(original, manifest, recounted, builder):
    """Recover artificial low quotas from audited pools, preserving validation.

    Call only AFTER global repartition/hash verification. This does not generate
    pools, prove domain exhaustion, or approve any adaptive shortfall.
    """
    result = deepcopy(original)
    ceiling = builder.POLICY['planned_dataset']['fresh_episodes_per_family']
    previous = original.get('train_by_family', {})
    affected = {t for t, r in recounted.items() if r.get('complete')
                and sum(previous.get(t, {}).values()) < ceiling}
    retained = {t: q for t, q in previous.items() if t not in affected}
    target = manifest['target_train_fresh_episodes']
    remaining = target - sum(sum(q.values()) for q in retained.values())
    if remaining < 0:
        raise ValueError('Retained training allocation exceeds target')
    desired = original['train']['desired']
    with patch.object(builder, 'SEED', manifest['seed']):
        replacement, audit = builder.allocate([recounted[t] for t in sorted(affected)],
                                               'train', remaining, desired)
    combined = dict(retained)
    changes = {}
    for t in sorted(affected):
        old, new = previous.get(t, {}), replacement.get(t, {})
        if sum(new.values()) < sum(old.values()):
            raise ValueError('Quota refresh would reduce a training family: ' + t)
        combined[t] = new
        if sum(new.values()) > sum(old.values()):
            changes[t] = {'old': sum(old.values()), 'new': sum(new.values())}
    actual = Counter()
    for quota in combined.values(): actual.update(quota)
    used = {t: sum(q.values()) for t, q in combined.items()}
    if sum(used.values()) > target:
        raise ValueError('Refreshed training allocation exceeds target')
    result['train_by_family'] = combined
    capacities = {**original['train'].get('family_capacity', {}), **audit['family_capacity']}
    result['train'] = {'requested': target, 'desired': desired,
                       'allocated': sum(used.values()),
                       'allocation_shortfall': target - sum(used.values()),
                       'actual': dict(actual), 'family_allocated': used,
                       'family_capacity': capacities,
                       'family_capacity_shortfall': {t: ceiling-capacities.get(t,0) for t in recounted
                                                     if capacities.get(t,0)<ceiling},
                       'family_unused_capacity': {t: c-used.get(t,0) for t,c in capacities.items()
                                                  if c>used.get(t,0)},
                       'shortfall_by_stratum': {k: n-actual[k] for k,n in desired.items() if n>actual[k]},
                       'histogram_surplus_by_stratum': {k: n-desired.get(k,0) for k,n in actual.items()
                                                        if n>desired.get(k,0)},
                       'capacity_policy': audit.get('capacity_policy'),
                       'capacity_is_verified_episode_count': False,
                       'policy': 'Refresh undersized training quotas from hash-verified globally repartitioned exact-query support; validation quotas retained.'}
    result['training_quota_refresh'] = {
        'source_allocation_sha256': hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest(),
        'changed_families': changes, 'allocation_audit': audit,
        'shortfall_approval': False,
        'note': 'Allocation is a construction budget, not verified episode support or native-domain exhaustion.'}
    return result


def validation_removal_evidence(snapshot, report, policy_signature):
    """Hash-check old TARs; count only explicitly invalidated validation rows."""
    from .finite_input_policy import GLOBAL_TRAIN_ORBITS, POLICY_SIGNATURE
    from .build_million import canonical_input
    if policy_signature != POLICY_SIGNATURE:
        raise ValueError("Validation-removal policy mismatch")
    detail = report.get("splits", {}).get("validation", {})
    rows, all_bases, removed_bases, removed_ids = 0, set(), set(), []
    seen_ids, base_decisions = set(), {}
    files = []
    for shard in detail.get("shards", []):
        name = safe_path("shards/validation/" + shard["file"])
        path = Path(snapshot) / name
        if sha256(path) != shard["sha256"]:
            raise ValueError("Original validation shard SHA256 mismatch")
        files.append({"file": name, "sha256": shard["sha256"]})
        with tarfile.open(path) as archive:
            for member in archive:
                if not member.name.endswith(".json"):
                    continue
                if not member.isfile():
                    raise ValueError("Invalid validation archive member")
                row = json.load(archive.extractfile(member))
                if row["task_id"] != report["task_id"] or row["split"] != "validation":
                    raise ValueError("Unexpected original validation record")
                identities = row["canonical_input_hashes"]
                visible = [canonical_input(p["input"]) for p in row["train"] + row["test"]]
                if identities != visible:
                    raise ValueError("Validation identity evidence disagrees with visible inputs")
                if row["episode_id"] in seen_ids:
                    raise ValueError("Duplicate original validation episode")
                seen_ids.add(row["episode_id"])
                base = row["base_episode_id"]
                invalid = bool(set(identities) & GLOBAL_TRAIN_ORBITS)
                if base in base_decisions and base_decisions[base] != invalid:
                    raise ValueError("Base episode variants disagree on global split membership")
                base_decisions[base] = invalid
                rows += 1
                all_bases.add(base)
                if invalid:
                    removed_ids.append(row["episode_id"])
                    removed_bases.add(base)
    if rows != detail.get("episodes", 0) or len(all_bases) != detail.get("fresh_episodes", 0):
        raise ValueError("Original validation archives do not account for published counts")
    return {"reason": "Global train reservation invalidates these old validation episodes",
            "policy_signature": policy_signature, "reserved_orbits": sorted(GLOBAL_TRAIN_ORBITS),
            "source_shards": files, "episodes": len(removed_ids), "fresh_episodes": len(removed_bases),
            "removed_episode_ids": removed_ids, "removed_base_episode_ids": sorted(removed_bases)}


def finish_finite_stage(stage, prepared, plan, allocation, audit):
    """Keep all pool, allocation, and episode changes in the same commit."""
    stage, prepared = Path(stage), Path(prepared)
    if not plan["publishable"]:
        return  # Failed migration remains a local diagnostic, never a partial publish.
    for directory in ("pools", "pool_reports"):
        for source in (prepared / directory).glob("*"):
            destination = stage / directory / source.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    write(stage / "allocation.json", allocation)
    write(stage / "finite-policy-audit.json", audit)
    manifest = read(stage / "manifest.json")
    manifest["finite_input_policy_signature"] = audit["policy_signature"]
    manifest["finite_input_policy_migration"] = audit
    manifest["completed_pools"] = audit["retained_nonempty_pools"]
    write(stage / "manifest.json", manifest)
    from .visual_card import card
    (stage / "README.md").write_text(card(manifest) +
        "\n## Finite-input support and global split migration\n\n"
        "Audited finite families use four exact-distinct inputs, while all families share the same "
        "canonical-orbit split policy. Train-reserved orbits were removed from validation globally. "
        "Any reduced validation count is itemized in the repaired family's report. Single-orbit "
        "families do not provide independent unseen-orbit validation. Original pool provenance "
        "is retained; this repair does not generate additional native support.\n")


def stage_repairs(snapshot, stage, manifest, allocation, reports, chosen, revision,
                  repair_commit, terminal_proof, builder, pool_overrides=None,
                  validation_removals=None, required_families=()):
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
            override = (pool_overrides or {}).get(tid)
            pool_source = Path(override["path"]) if override else snapshot / "pools" / (tid + ".parquet")
            if override:
                if sha256(pool_source) != override["sha256"]:
                    raise ValueError("Repartitioned pool changed after audit")
                provenance["finite_policy_migration"] = override["migration"]
                provenance["repartitioned_pool_sha256"] = override["sha256"]
            shutil.copy2(pool_source, work / "pools" / (tid + ".parquet"))
            with patch.object(builder, "OUT", work), patch.object(builder, "SEED", manifest["seed"]), \
                    patch.object(builder, "OUTPUT_FORMAT", "program-grid-png"), \
                    patch.dict(os.environ, {"ARCGEN_SOURCE_COMMIT": repair_commit}):
                candidate = builder.make_episodes((tid, quotas[tid]))
            if candidate["task_id"] != tid or set(candidate["splits"]) != set(SPLITS):
                raise ValueError("Repair must return both splits for the same family")
            verify_artifacts(work, candidate)
            removal = (validation_removals or {}).get(tid)
            if not nonregressing(reports.get(tid, {}), candidate, removal):
                outcomes[tid] = {"status": "regression_preserved_original", "candidate": candidate}
                continue
            candidate["repair_provenance"] = {**provenance, "episode_repair_commit": repair_commit}
            if removal:
                candidate["repair_provenance"]["labelled_validation_removals"] = removal
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
            "remaining_shortfalls": selection(m, allocation, updated),
            "publishable": set(required_families) <= set(accepted),
            "required_families_not_rebuilt": sorted(set(required_families) - set(accepted))}
    write(stage / "manifest.json", m)
    write(stage / "size-audit.json", size_audit(updated, m))
    write(stage / "repair-report.json", plan)
    from .visual_card import card
    (stage / "README.md").write_text(card(m))
    return plan


def publish_stage(api, repo, revision, snapshot, stage, plan, job_id=None, namespace=None):
    if not plan.get("publishable", True):
        raise RuntimeError("Finite-policy migration is incomplete; publishing could leak train-reserved inputs into validation")
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
    ap.add_argument("--finite-policy", action="store_true", help="Globally audit/re-split all saved pools and rebuild every affected family")
    ap.add_argument("--refresh-training-quotas", action="store_true", help="With --finite-policy, repair artificial low allocations using verified exact-query support")
    args = ap.parse_args()
    if not re.fullmatch("[0-9a-f]{40}", args.revision):
        ap.error("--revision must be an exact commit SHA, never main or a moving tag")
    if args.offline and args.publish:
        ap.error("--publish requires online head/job checks")
    if args.refresh_training_quotas and not args.finite_policy:
        ap.error("--refresh-training-quotas requires --finite-policy so every pool is hash-verified and globally re-split first")
    if args.finite_policy and args.tasks:
        ap.error("--finite-policy is global and cannot be restricted with --tasks")
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
        print(json.dumps({"mode": "plan_only", "source_status": manifest["status"], "families": chosen,
                          "finite_policy": args.finite_policy,
                          "global_pool_scan_pending": args.finite_policy,
                          "training_quota_refresh_pending": args.refresh_training_quotas,
                          "note": "Finite-policy execution scans ALL saved pools and adds every affected family before repair." if args.finite_policy else ""}, indent=2))
        return
    terminal = require_terminal(manifest, api, args.source_job_id, args.namespace)
    if api:
        from huggingface_hub.errors import EntryNotFoundError
        pool_ids = ({p.stem for p in (args.snapshot / "pool_reports").glob("*.json") if read(p).get("complete")}
                    if args.finite_policy else chosen)
        for tid in pool_ids:
            try:
                hf_hub_download(args.repo, f"pools/{tid}.parquet", repo_type="dataset", revision=args.revision, local_dir=args.snapshot)
            except EntryNotFoundError:
                pass  # Report missing pools; do not generate replacements or fabricate quota.
    repair_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1], text=True).strip()
    from . import build_million as builder
    overrides, removals, required = {}, {}, set()
    if args.finite_policy:
        prepared = args.stage.with_name(args.stage.name + "-finite-pools")
        overrides, recounted, required, finite_audit = prepare_finite_pools(
            args.snapshot, prepared, manifest, args.revision, builder)
        allocation = finite_allocation(allocation, manifest, recounted, required, builder)
        if args.refresh_training_quotas:
            allocation = refresh_training_allocation(allocation, manifest, recounted, builder)
        chosen = sorted(set(selection(manifest, allocation, reports)) | required)
        for tid in required:
            old = reports.get(tid, {"task_id": tid, "splits": {}})
            if api:
                for shard in old.get("splits", {}).get("validation", {}).get("shards", []):
                    hf_hub_download(args.repo, safe_path("shards/validation/" + shard["file"]),
                                    repo_type="dataset", revision=args.revision, local_dir=args.snapshot)
            removals[tid] = validation_removal_evidence(args.snapshot, old, finite_audit["policy_signature"])
    plan = stage_repairs(args.snapshot, args.stage, manifest, allocation, reports, chosen,
                         args.revision, repair_commit, terminal, builder,
                         pool_overrides=overrides, validation_removals=removals, required_families=required)
    if args.finite_policy:
        finish_finite_stage(args.stage, prepared, plan, allocation, finite_audit)
    if args.publish:
        commit = publish_stage(api, args.repo, args.revision, args.snapshot, args.stage, plan,
                               args.source_job_id, args.namespace)
        print(json.dumps({"published_revision": commit.oid, "accepted_families": plan["accepted_families"]}))
    else:
        print(json.dumps({"mode": "local_stage_only", "stage": str(args.stage), **plan}, indent=2))


if __name__ == "__main__":
    main()
