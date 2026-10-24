"""Carry reviewed provenance forward into a freshly measured factory record.

A certificate run replaces every measured field. This helper only adds the
drafting provenance and notes from the record at LEGACY_COMMIT, verbatim,
plus an explicit statement of which notes describe the superseded domain.
It never edits a measured field or a hash, and it refuses to write a record
whose hashes do not match the current constructor and factory bytes.

The raw standard-harness output is kept as standard-recertify-<tid>.json in
this directory; the merged record is written to the admitted factory record
and its native-certificates mirror, which must be identical.

Usage after the standard harness passes (7491f3cf):
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-routing-motif-20261025/history.py 7491f3cf
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from arc_agi2.runtime import BASE

LEGACY_COMMIT = "99def42"
CARRIED = ("provenance", "draft_notes")

HISTORICAL = {
    "7491f3cf": (
        "historical: draft_notes were written for the legacy square-panel constructor "
        "(N x N panels, N in 4..6). Statements about square panels, (N+2) x (4N+5) grids and "
        "the 4..6 panel_size range describe that domain only. The factory code they explain is "
        "unchanged; it reads panels from frame-colour dividers and handles H x W panels. The "
        "current domain is in certificate_scope."),
    "98c475bf": (
        "historical: draft_notes were written for the legacy fixed-width-20 constructor. The "
        "statements that a template stores 'the along-length (20)' and that anchoring matches "
        "'the constructor's fixed width of 20' describe that domain only: the unchanged factory "
        "stores the demonstrated line span of whatever width the demonstrations show and refuses "
        "other spans. host_validation describes the superseded 250-query audit, whose measured "
        "values are kept under previous_certificate. The 'Nothing has been run or tested' "
        "limitation refers to the original draft. The current domain is in certificate_scope."),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def previous(tid):
    text = subprocess.run(
        ["git", "show", f"{LEGACY_COMMIT}:arc_agi2/direct_factories/{tid}.json"],
        check=True, capture_output=True, text=True, cwd=BASE.parent).stdout
    return json.loads(text)


def current_hashes(tid):
    return {
        "constructor_sha256": sha((BASE.parent / "tasks" / f"task_{tid}.py").read_bytes()),
        "factory_sha256": sha((BASE / "direct_factories" / f"task_{tid}.py").read_bytes()),
    }


def merge(tid, report, scope, certification_provenance):
    if report.get("task_id") != tid or report.get("passed") is not True:
        raise ValueError("Only a passed certificate for this family can be recorded")
    for key, value in current_hashes(tid).items():
        if report.get(key) != value:
            raise ValueError(f"{key} in the certificate does not match the current bytes")
    old = previous(tid)
    merged = dict(report)
    for key in CARRIED:
        merged[key] = old[key]
    merged["draft_notes_status"] = HISTORICAL[tid]
    merged["certificate_scope"] = scope
    merged["certification_provenance"] = certification_provenance
    merged["previous_certificate"] = dict(
        {k: v for k, v in old.items() if k not in CARRIED},
        status=f"superseded; record at {LEGACY_COMMIT}, hashes refer to the legacy constructor")
    return merged


SCOPE_7491 = (
    "Default sampler of tasks/task_7491f3cf.py: four H x W panels, H 3..28, W 3..6, 3x3 "
    "excluded under the retained two-cells-per-region guard; legacy square 4/5/6 on one draw "
    "in four. Standard harness arc_agi2.diversity.recertify: independent default draws, four "
    "per episode, archived verifier on every pair, factory exact under 8 D4 with a seeded "
    "palette, 16 canonical fixture variants. 7491f3cf has no demonstration-evidence gate.")
PROVENANCE_7491 = (
    "Measured fields written by the unmodified standard harness "
    "(python -m arc_agi2.diversity.recertify 7491f3cf); provenance and draft_notes carried "
    "verbatim from the record at 99def42 by native-routing-motif-20261025/history.py.")


def write_record(tid, merged):
    """Admitted factory record and its native-certificates mirror, identical.

    test_pipeline.native_recertification requires the mirror to equal the
    admitted record, as the standard harness writes them on a pass.
    """
    text = json.dumps(merged, indent=2) + "\n"
    paths = (BASE / "direct_factories" / f"{tid}.json",
             BASE / "reports/diversity-v1/native-certificates" / f"{tid}.json")
    for path in paths:
        path.write_text(text)
    return [str(p.relative_to(BASE.parent)) for p in paths]


def main(tid):
    if tid != "7491f3cf":
        raise SystemExit("98c475bf records are written by certify_98c475bf.py")
    here = Path(__file__).resolve().parent
    raw = here / f"standard-recertify-{tid}.json"
    native = BASE / "reports/diversity-v1/native-certificates" / f"{tid}.json"
    if not raw.exists():
        # First call after the harness: keep its output byte-for-byte.
        if "certificate_scope" in json.loads(native.read_text()):
            raise ValueError("No unmerged standard harness output to record")
        raw.write_bytes(native.read_bytes())
    standard = json.loads(raw.read_text())
    record = json.loads((BASE / "direct_factories" / f"{tid}.json").read_text())
    if {k: v for k, v in record.items() if k in standard} != standard:
        raise ValueError("Factory record differs from the standard harness output")
    written = write_record(tid, merge(tid, standard, SCOPE_7491, PROVENANCE_7491))
    print(json.dumps({"task_id": tid, "written": written}))


if __name__ == "__main__":
    main(sys.argv[1])
