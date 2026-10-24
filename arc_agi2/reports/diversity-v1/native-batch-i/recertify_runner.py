"""Re-certify the batch I constructors with the unmodified recertify.check (2 workers).

recertify.check rewrites both native-certificates/<id>.json and, on success,
direct_factories/<id>.json. Afterwards this runner merges back the factory
record's provenance and draft notes from base 96be803. It also records the
previous constructor hash and the old-domain limitations. Only the stale
seed/d4 fields are dropped. Certification itself is untouched.

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-i/recertify_runner.py
"""
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from arc_agi2.diversity.recertify import check
from arc_agi2.runtime import BASE

BASE_COMMIT = "96be803"
TASKS = ("18447a8d", "b4a43f3b")
ROOT = BASE.parent
OLD_DOMAIN = {
    "18447a8d": ("Before batch I the random path drew 3..4 bands, so canonical train[1] "
                 "(2 bands) was unreachable, and it used an unbounded while-True rejection "
                 "loop. Now: 2..7 bands (num_bands), distinct lock profiles sampled directly, "
                 "and complete explicit lefts/rights/colors kept verbatim."),
    "b4a43f3b": ("Before batch I the random path drew exactly three axis segments on a fixed "
                 "6x6 map at motif scale 2 (13x6 -> 18x18), so canonical train[1] (four "
                 "segments) was unreachable, and it used the unbounded "
                 "diagonally_connected_sprite loop. Now: any non-empty map (1..8 segments plus "
                 "0..2 free cells, or a uniform-count scatter), scale 1..3, map height 1..10, "
                 "enumerated spanning 8-connected masks, and the complete explicit 13x6 path "
                 "kept verbatim. The registered pair checker is now "
                 "verified_rules.separated_motif_stamp."),
}


def old_record(tid):
    text = subprocess.run(["git", "show", f"{BASE_COMMIT}:arc_agi2/direct_factories/{tid}.json"],
                          cwd=ROOT, check=True, capture_output=True, text=True).stdout
    return json.loads(text)


def merge(tid, report):
    old = old_record(tid)
    path = BASE / "direct_factories" / f"{tid}.json"
    record = json.loads(path.read_text())
    for key in ("provenance", "draft_notes"):
        if key in old:
            record[key] = old[key]
    record["previous_constructor_sha256"] = old["constructor_sha256"]
    record["previous_domain_limitations"] = OLD_DOMAIN[tid]
    if old.get("factory_sha256") != record.get("factory_sha256"):
        raise RuntimeError(f"{tid}: factory changed unexpectedly")
    text = json.dumps(record, indent=2) + "\n"
    path.write_text(text)
    # Both records are consumed by production certificate validation. Keep
    # restored provenance in the mirror as well as in the factory record.
    (BASE / "reports/diversity-v1/native-certificates" / f"{tid}.json").write_text(text)
    return record


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=2) as pool:
        reports = list(pool.map(check, TASKS))
    for tid, report in zip(TASKS, reports):
        summary = {k: report.get(k) for k in ("task_id", "passed", "fresh_pairs_checked",
                                              "augmented_pair_checks", "fixture_variants_checked",
                                              "unique_base_inputs", "sampler_rejections",
                                              "constructor_sha256", "factory_sha256", "error")}
        print(json.dumps(summary), flush=True)
        if report.get("passed"):
            merge(tid, report)
