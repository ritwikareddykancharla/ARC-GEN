"""Standard recertify.check for the batch F constructors, two workers.

Runs the unmodified arc_agi2.diversity.recertify.check (fixture replay, 16
fixture variants, 1000 fresh pairs gated by the archived independent checker,
8000 D4 program checks) for the three IDs. recertify writes passing reports
over direct_factories/<id>.json, which drops the factory's provenance, so the
factory record at BASE_REV is merged back afterwards: provenance and
draft_notes (explanation, limitations) are kept verbatim, the stale draft-time
seed/d4 fields are dropped, and previous_constructor_sha256 records the legacy
constructor. The draft notes describe the legacy 3x3/4x4 domain, so a
recertification_note states what changed.

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-f/recertify_batch_f.py
"""
import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor

from arc_agi2.diversity.recertify import check
from arc_agi2.runtime import BASE

TASKS = ("27f8ce4f", "48f8583b", "5b6cbef5")
BASE_REV = "e72190b"
NOTE = ("Native batch F recertified this unchanged factory on a widened constructor: input "
        "height and width are sampled independently in 2..5 (output H*H x W*W <= 25x25). "
        "{domain} The draft notes below were written for the legacy {legacy} domain and are "
        "kept verbatim. The factory already handled general H x W inputs.")
DOMAIN = {
    "27f8ce4f": "3..min(5, H*W-1) colours, all used, unique modal colour.",
    "48f8583b": "Legacy nominal 2..4-colour subset, not all required (1..4 used colours, "
                "monochrome included), unique least frequent colour.",
    "5b6cbef5": "Non-empty single-ink masks, ink 1..9 (legacy 1..4), fair-coin cells.",
}
LEGACY = {"27f8ce4f": "3x3", "48f8583b": "3x3", "5b6cbef5": "4x4"}


def legacy_record(tid):
    return json.loads(subprocess.run(
        ["git", "show", f"{BASE_REV}:arc_agi2/direct_factories/{tid}.json"],
        check=True, capture_output=True, cwd=BASE.parent).stdout)


def merge(report):
    tid = report["task_id"]
    old = legacy_record(tid)
    if report["factory_sha256"] != old["factory_sha256"]:
        raise RuntimeError(f"{tid}: factory changed; batch F must not edit factories")
    report.update(provenance=old["provenance"], draft_notes=old["draft_notes"],
                  previous_constructor_sha256=old["constructor_sha256"],
                  recertification_note=NOTE.format(domain=DOMAIN[tid], legacy=LEGACY[tid]))
    path = BASE / "direct_factories" / f"{tid}.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    ids = sys.argv[1:] or list(TASKS)
    with ProcessPoolExecutor(max_workers=2) as pool:
        reports = list(pool.map(check, ids))
    failed = False
    for report in reports:
        if report["passed"]:
            merge(report)
        else:
            failed = True
        print(json.dumps({k: report.get(k) for k in (
            "task_id", "passed", "fresh_pairs_checked", "augmented_pair_checks",
            "fixture_variants_checked", "unique_base_inputs", "sampler_rejections",
            "constructor_sha256", "factory_sha256", "seconds", "error")}), flush=True)
    sys.exit(1 if failed else 0)
