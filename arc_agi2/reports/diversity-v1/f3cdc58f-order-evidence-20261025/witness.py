"""Pre-gate witness: f3cdc58f episodes whose demonstrations do not fix the bar order.

Native rule: count colours 1..4 and draw bottom-aligned bars in the FIXED legend
order 1, 2, 3, 4 (columns 0..3). Natural competitor readings order the four
bars by ascending or descending count, ties broken by that same legend order
(the order every demonstration's bars show). A context of three
demonstrations whose counts are monotone in legend order fits a count-sorted
reading as well as the fixed legend; a query whose counts are not monotone then
has two different answers.

For each competitor this script searches, with a fixed seed and a bounded
budget, for ONE fixed 4x4 query plus three 4x4 demonstrations such that

* all four inputs have DISTINCT production prepare.input_orbit identities and
  the three demos share the query's finite_input_policy.input_split;
* every pair label equals runtime.verification_solver (the registered checker);
* the episode matches the canonical shape profile (uniform/seen);
* the competitor reproduces every demonstration output exactly and differs
  from the native answer on the query INPUT;
* the ORIGINAL program_targets.make_record accepts the episode for all 8 D4
  transforms under a seeded palette and under the identity palette.

The competitor is reimplemented here, independent of the gate module, so the
witness can be (and was) generated on the pre-gate base commit. Query answers
are recorded for the archive only; nothing is selected by comparing a
candidate with the query answer except the witness condition itself, which is
the point of a counterexample.

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/f3cdc58f-order-evidence-20261025/witness.py
"""
import hashlib
import importlib
import json
import random
import subprocess
import sys
from pathlib import Path

from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.diversity.recertify import episode
from arc_agi2.episode_shape_policy import describe, profile_from_task
from arc_agi2.finite_input_policy import input_split
from arc_agi2.program_targets import make_record
from arc_agi2.runtime import BASE, grid, reference, verification_solver

TID = "f3cdc58f"
OUT = Path(__file__).resolve().parent
SHAPE = (4, 4)
MAX_QUERY_DRAWS = 2000
MAX_DEMO_DRAWS = 20000
LEGEND = (1, 2, 3, 4)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def counts(g):
    flat = [v for row in g for v in row]
    return [flat.count(c) for c in LEGEND]


def order(g, rule):
    n = dict(zip(LEGEND, counts(g)))
    if rule == "ascending_count":
        return sorted(LEGEND, key=lambda c: (n[c], LEGEND.index(c)))
    if rule == "descending_count":
        return sorted(LEGEND, key=lambda c: (-n[c], LEGEND.index(c)))
    return list(LEGEND)


def render(g, rule):
    h, w = len(g), len(g[0])
    n = dict(zip(LEGEND, counts(g)))
    out = [[0] * w for _ in range(h)]
    for col, colour in enumerate(order(g, rule)):
        for r in range(n[colour]):
            out[h - 1 - r][col] = colour
    return out


def search(rule, seed):
    module = importlib.import_module("tasks.task_" + TID)
    checker = verification_solver(TID)
    rng = random.Random(seed)

    def draw():
        s = rng.getrandbits(48)
        random.seed(s)
        p = module.generate(width=SHAPE[1], height=SHAPE[0])
        p = {k: grid(p[k]) for k in ("input", "output")}
        if grid(checker(p["input"])) != p["output"]:
            raise RuntimeError("registered checker disagrees with label")
        return s, p

    for qd in range(1, MAX_QUERY_DRAWS + 1):
        qseed, query = draw()
        if render(query["input"], rule) != query["output"]:
            break
    else:
        return None
    qorbit = input_orbit(query["input"])
    split = input_split(qorbit)
    demos, seeds, orbits, dd = [], [], {qorbit}, 0
    while len(demos) < 3 and dd < MAX_DEMO_DRAWS:
        dd += 1
        s, p = draw()
        o = input_orbit(p["input"])
        if o in orbits or input_split(o) != split:
            continue
        if render(p["input"], rule) == p["output"]:
            demos.append(p)
            seeds.append(s)
            orbits.add(o)
    if len(demos) < 3:
        return None
    return {"rule": rule, "search_seed": seed, "query_draws": qd, "demo_draws": dd,
            "query_seed": qseed, "demo_seeds": seeds, "query": query, "demos": demos,
            "split": split}


def certify(w):
    profile = profile_from_task(reference(TID)["canonical"])["patterns"][0]
    demos, query = w["demos"], w["query"]
    assert describe(demos, query["input"]) == profile
    orbits = [input_orbit(p["input"]) for p in demos + [query]]
    assert len(set(orbits)) == 4
    assert {input_split(o) for o in orbits} == {w["split"]}
    assert all(render(d["input"], w["rule"]) == d["output"] for d in demos)
    competitor = render(query["input"], w["rule"])
    assert competitor != query["output"]
    palette = list(range(10))
    random.Random(w["search_seed"] + 1).shuffle(palette)
    accepted = []
    for pal_name, pal in (("identity", list(range(10))), ("seeded", palette)):
        for d4 in range(8):
            ep = episode(demos + [query], d4, pal)
            ep.update(task_id=TID, episode_id=f"witness-{w['rule']}-{pal_name}-{d4}",
                      d4_transform=d4, color_permutation=pal)
            make_record(ep)
            accepted.append({"palette": pal_name, "d4": d4})
    return {
        "competitor": w["rule"],
        "tie_break": "fixed legend order shown by every demonstration's bars (native 1,2,3,4)",
        "shape": list(SHAPE),
        "shape_profile": profile,
        "split": w["split"],
        "input_orbits": orbits,
        "search": {k: w[k] for k in ("search_seed", "query_draws", "demo_draws",
                                     "query_seed", "demo_seeds")},
        "demonstrations": [{"input": d["input"], "output": d["output"],
                            "legend_counts": counts(d["input"])} for d in demos],
        "query": {"input": query["input"], "legend_counts": counts(query["input"]),
                  "native_answer": query["output"], "competitor_answer": competitor},
        "seeded_palette": palette,
        "pregate_make_record_accepted": accepted,
    }


def main():
    files = {"constructor": BASE.parent / "tasks" / f"task_{TID}.py",
             "colour_evidence": BASE / "colour_evidence.py",
             "program_targets": BASE / "program_targets.py",
             "verified_rules": BASE / "verified_rules.py",
             "prepare": BASE / "diversity" / "prepare.py",
             "harness": Path(__file__)}
    report = {
        "task_id": TID,
        "purpose": "pre-gate counterexample: demonstrations fit a count-sorted bar order",
        "generated_at_commit": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                              text=True).stdout.strip(),
        "source_sha256": {k: sha(p.read_bytes()) for k, p in files.items()},
        "witnesses": {},
    }
    for i, rule in enumerate(("ascending_count", "descending_count")):
        w = search(rule, 20261025 + i)
        report["witnesses"][rule] = None if w is None else certify(w)
        print(rule, "found" if w else "not found within budget", file=sys.stderr)
    (OUT / "pregate-witness.json").write_text(json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()
