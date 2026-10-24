"""Exact small-shape input-orbit capacity for the batch F self-tilers (read-only).

Enumerates EVERY input the current default samplers can produce at small
shapes, then groups them with the pipeline's own prepare.input_orbit (D4 plus
first-occurrence palette relabelling) and assigns finite_input_policy
input_split. Colour identities are irrelevant to the orbit, so inputs are
enumerated as restricted-growth labellings (labels 1..K mapped to colours 1..K).

Default domains enumerated:
* 27f8ce4f: K = 3..min(5, area-1) colours, all used, unique maximum count.
* 48f8583b: legacy nominal subset (2..4 colours) not all required: any input
  with 1..4 used colours and a unique minimum count (one colour included).
* 5b6cbef5: non-empty single-ink binary masks.

A strict same-shape episode needs 3 demonstrations plus a query with distinct
input orbits in the same split; this file counts orbits, it does not run prepare.
2xW and Wx2 inputs share orbits because input_orbit includes transposition.

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-f/small_shape_orbits.py
"""
import hashlib
import json
from collections import Counter
from itertools import product
from pathlib import Path

from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.finite_input_policy import input_split

OUT = Path(__file__).resolve().parent
SHAPES = [(2, 2), (2, 3), (3, 2), (2, 4), (3, 3)]


def rgs(n, kmax):
    """Restricted-growth strings of length n with at most kmax labels."""
    def rec(prefix, k):
        if len(prefix) == n:
            yield prefix
            return
        for v in range(min(k + 1, kmax)):
            yield from rec(prefix + [v], max(k, v + 1))
    yield from rec([], 0)


def domain(tid, h, w):
    area = h * w
    if tid == "5b6cbef5":
        for bits in product((0, 1), repeat=area):
            if any(bits):
                yield [1 if b else 0 for b in bits]
        return
    for labels in rgs(area, 5 if tid == "27f8ce4f" else 4):
        counts = sorted(Counter(labels).values())
        k = len(counts)
        if tid == "27f8ce4f":
            ok = 3 <= k <= min(5, area - 1) and (k == 1 or counts[-1] != counts[-2])
        else:
            ok = k <= 4 and counts.count(counts[0]) == 1
        if ok:
            yield [v + 1 for v in labels]


def main():
    report = {"method": "exhaustive restricted-growth enumeration; prepare.input_orbit; "
                        "finite_input_policy.input_split",
              "source_sha256": {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in (
                  "arc_agi2/diversity/prepare.py", "arc_agi2/finite_input_policy.py",
                  "tasks/task_27f8ce4f.py", "tasks/task_48f8583b.py", "tasks/task_5b6cbef5.py")},
              "families": {}}
    for tid in ("27f8ce4f", "48f8583b", "5b6cbef5"):
        rows = {}
        for h, w in SHAPES:
            orbits = set()
            for flat in domain(tid, h, w):
                orbits.add(input_orbit([flat[r * w:(r + 1) * w] for r in range(h)]))
            split = Counter(input_split(o) for o in orbits)
            rows[f"{h}x{w}"] = {"labellings": sum(1 for _ in domain(tid, h, w)),
                                "orbits": len(orbits),
                                "train_orbits": split.get("train", 0),
                                "validation_orbits": split.get("validation", 0),
                                # 3 demos + query, all distinct orbits, one split
                                "four_distinct_orbits_train": split.get("train", 0) >= 4,
                                "four_distinct_orbits_validation": split.get("validation", 0) >= 4}
        report["families"][tid] = rows
    (OUT / "small-shape-orbits.json").write_text(json.dumps(report, indent=2) + "\n")
    for tid, rows in report["families"].items():
        print(tid, {s: (r["orbits"], r["train_orbits"], r["validation_orbits"]) for s, r in rows.items()})


if __name__ == "__main__":
    main()
