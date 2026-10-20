"""Admission records for native programs verified directly in augmented coordinates.

These records admit a program to the builder; every exported episode must still
pass execution verification. A finite audit is not a proof of generalization.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path

from .runtime import BASE

CERTIFICATES = BASE / "reports" / "direct-certificates"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def current_hashes(task_id, source):
    module = importlib.import_module("tasks.task_" + task_id)
    return {
        "program_sha256": sha(source.encode()),
        "constructor_sha256": sha(Path(module.__file__).read_bytes()),
    }


def qualifies(report):
    finite = report.get("finite_default_domain", {})
    diversity_ok = report.get("unique_base_inputs", 0) >= 100
    # A reviewed finite native domain is not made richer by repeating it.
    # Such families retain explicit small counts and adaptive episode quotas.
    if (finite.get("exhaustive") is True
            and finite.get("cases_checked", 0) == report.get("unique_base_inputs", 0)
            and finite.get("cases_checked", 0) > 0
            and finite.get("augmented_checks", 0) >= 16 * finite["cases_checked"]):
        diversity_ok = True
    return (
        report.get("passed") is True
        and report.get("fresh_pairs_checked", 0) >= 1000
        and report.get("augmented_pair_checks", 0)
        >= 8 * report.get("fresh_pairs_checked", 0)
        and diversity_ok
    )


def certified_source(task_id):
    path = CERTIFICATES / (task_id + ".json")
    if not path.exists():
        return None
    report = json.loads(path.read_text())
    if report.get("task_id") != task_id or not qualifies(report):
        return None
    # Rebuild the candidate instead of trusting an old serialized program.
    # native_program also includes any currently reviewed verifier override.
    from .audit_direct_candidates import candidate
    source, _ = candidate(task_id)
    if any(report.get(k) != v for k, v in current_hashes(task_id, source).items()):
        return None
    return source


def certified_factory_source(task_id, d4, palette):
    folder = BASE / "direct_factories"
    path = folder / (task_id + ".json")
    if not path.exists():
        return None
    report = json.loads(path.read_text())
    if (report.get("task_id") != task_id or not qualifies(report)
            or report.get("fixture_variants_checked") != 16):
        return None
    source_path = folder / ("task_" + task_id + ".py")
    constructor = BASE.parent / "tasks" / ("task_" + task_id + ".py")
    if (sha(source_path.read_bytes()) != report.get("factory_sha256")
            or sha(constructor.read_bytes()) != report.get("constructor_sha256")):
        return None
    module = importlib.import_module(".direct_factories.task_" + task_id, package="arc_agi2")
    return module.build_program(d4, list(palette))


def register(directory):
    from .audit_direct_candidates import candidate
    from .program_targets import audit_target
    fixture_report = json.loads((BASE / "reports/direct-candidate-audit.json").read_text())
    fixtures = {r["task_id"]: r for r in fixture_report["tasks"] if r["passed"]}
    accepted, rejected = [], {}
    CERTIFICATES.mkdir(parents=True, exist_ok=True)
    for path in sorted(Path(directory).glob("????????.json")):
        report = json.loads(path.read_text())
        tid = report["task_id"]
        if not qualifies(report):
            rejected[tid] = "Fresh audit incomplete, failed, or insufficient diversity"
            continue
        source, _ = candidate(tid)
        hashes = current_hashes(tid, source)
        if any(report.get(k) != v for k, v in hashes.items()):
            rejected[tid] = "Source changed since fresh audit"
            continue
        fixture = fixtures.get(tid, {})
        if (fixture.get("program_sha256") != hashes["program_sha256"]
                or fixture.get("checked_variants") != 16):
            rejected[tid] = "Missing matching fixture audit"
            continue
        audit_target(tid, source)
        report = dict(report, certificate_version=1,
                      fixture_variants_checked=16,
                      fixture_basis=fixture["fixture"],
                      requires_per_episode_verification=True)
        (CERTIFICATES / (tid + ".json")).write_text(json.dumps(report, indent=2) + "\n")
        accepted.append(tid)
    return {"registered": len(accepted), "task_ids": accepted, "not_registered": rejected}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", type=Path)
    args = parser.parse_args()
    result = register(args.reports)
    result["available_task_ids"] = [
        p.stem for p in sorted(CERTIFICATES.glob("????????.json"))
        if certified_source(p.stem) is not None
    ]
    result["available_families"] = len(result["available_task_ids"])
    (CERTIFICATES / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"registered": result["registered"],
                      "not_registered": len(result["not_registered"])}))


if __name__ == "__main__":
    main()
