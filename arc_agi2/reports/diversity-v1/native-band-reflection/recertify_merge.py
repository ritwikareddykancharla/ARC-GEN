"""Re-certify e74e1818 with the standard harness and keep reviewed history.

arc_agi2.diversity.recertify.check overwrites the admitted factory record and
its native-certificates mirror with measured fields only. This script reads
both records first (they must be identical), runs the unmodified harness,
keeps its raw output as standard-recertify-e74e1818.json, and writes one
merged record to both paths: fresh measured fields, then every non-measured
key of the earlier record verbatim, plus a certificate_history entry holding
the superseded measured fields. On failure both records are restored.

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-band-reflection/recertify_merge.py
"""
import hashlib
import json
from pathlib import Path

from arc_agi2.diversity.recertify import check
from arc_agi2.runtime import BASE

TID = "e74e1818"
SUPERSEDED_COMMIT = "238f085"
PATHS = (BASE / "direct_factories" / f"{TID}.json",
         BASE / "reports/diversity-v1/native-certificates" / f"{TID}.json")
SCOPE = (
    "Certified: the default random grammar of tasks/task_e74e1818.py (colors=None; "
    "independent height and width 3..30, 1..9 contiguous bands with distinct colours, "
    "symmetric or asymmetric nonempty monochromatic rows, native black border; "
    "num_bands/symmetric controls validated) and the 16 canonical fixture variants. "
    "Explicit width/height/colors calls run the pre-238f085 draw() for compatibility. "
    "Scenes that only that path accepts (repeated nonadjacent colours, border ink, "
    "sides below 3, partial colour lists, mixed-colour rows) are not certified. On them "
    "the coordinate checker (per-colour row-span reflection) and the factory may "
    "disagree with the legacy labels.")
PROVENANCE = (
    "Measured fields written by the unmodified standard harness "
    "(arc_agi2.diversity.recertify.check). Non-measured keys are carried verbatim "
    "from the record at 238f085 by native-band-reflection/recertify_merge.py.")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    texts = [p.read_text() for p in PATHS]
    if texts[0] != texts[1]:
        raise ValueError("Admitted record and mirror differ before certification")
    old = json.loads(texts[0])
    try:
        fresh = check(TID)
        if not fresh.get("passed"):
            raise ValueError(f"Certification failed: {fresh.get('error')}")
        current = {
            "constructor_sha256": sha((BASE.parent / "tasks" / f"task_{TID}.py").read_bytes()),
            "factory_sha256": sha((BASE / "direct_factories" / f"task_{TID}.py").read_bytes()),
        }
        if any(fresh.get(k) != v for k, v in current.items()):
            raise ValueError("Certificate hashes do not match current bytes")
    except BaseException:
        for path, text in zip(PATHS, texts):
            path.write_text(text)
        raise
    here = Path(__file__).resolve().parent
    (here / f"standard-recertify-{TID}.json").write_text(json.dumps(fresh, indent=2) + "\n")
    merged = dict(fresh)
    for key, value in old.items():
        if key not in fresh:
            merged[key] = value
    history = list(old.get("certificate_history", []))
    history.append(dict(
        {k: old[k] for k in fresh if k in old},
        status=(f"superseded; record at {SUPERSEDED_COMMIT}. Constructor bytes changed only to "
                "restore historical explicit-call labels; the random grammar is unchanged.")))
    merged["certificate_history"] = history
    merged["certificate_scope"] = SCOPE
    merged["certification_provenance"] = PROVENANCE
    text = json.dumps(merged, indent=2) + "\n"
    for path in PATHS:
        path.write_text(text)
    print(json.dumps({k: fresh[k] for k in ("passed", "fresh_pairs_checked", "augmented_pair_checks",
                                            "fixture_variants_checked", "unique_base_inputs",
                                            "constructor_sha256", "factory_sha256")}))


if __name__ == "__main__":
    main()
