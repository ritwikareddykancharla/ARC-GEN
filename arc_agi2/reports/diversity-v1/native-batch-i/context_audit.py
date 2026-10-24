"""Gate-aware, profile-honouring fixed-query context audit for native batch I.

recertify.check verifies programs only. This audit runs the actual
program_targets.make_record, which applies the native_i_evidence gate and
exports the program, on episodes shaped like production's:

* QUERIES fixed queries per run, drawn once and never dropped: a 'default'
  run, and a 'min_corner' run (18447a8d 2 bands; b4a43f3b scale 1, map
  height 1, i.e. 5x3 inputs);
* demonstrations honour the canonical episode-shape profile
  (episode_shape_policy.profile_from_task): 18447a8d mixed/seen (one demo at
  the query band count, two at other band counts); b4a43f3b uniform/seen
  (all at the query's scale and map height). Each context is validated with
  episode_shape_policy.describe;
* all four inputs are DISTINCT prepare.input_orbit identities;
* every demo is in the query's split (finite_input_policy.input_split of its
  orbit), redrawn per slot at most SPLIT_DRAWS times; the draw cost is
  reported;
* at most MAX_CONTEXTS context attempts per query; an attempt is accepted
  only if make_record succeeds for all 8 D4 under the attempt's seeded
  palette AND the gate's unique prediction equals the constructor label;
* every pair label is checked by runtime.verification_solver.

This is NOT a production export. prepare is not run, no quota is claimed,
and no policy is changed or monkeypatched.

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-i/context_audit.py
"""
import hashlib
import importlib
import json
import random
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.diversity.recertify import episode
from arc_agi2.episode_shape_policy import describe, profile_from_task
from arc_agi2.finite_input_policy import input_split
from arc_agi2.native_i_evidence import candidate_predictions
from arc_agi2.program_targets import make_record
from arc_agi2.runtime import BASE, call, grid, reference, verification_solver

TASKS = ("18447a8d", "b4a43f3b")
QUERIES = 250
MAX_CONTEXTS = 64
SPLIT_DRAWS = 400
METHOD = "gate-aware-profile-honouring-split-matched-fixed-query-context"
METHOD_VERSION = 1
OUT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def seed_of(*parts):
    return int(sha(":".join(map(str, ("batch-i-context",) + parts)).encode())[:12], 16)


def draw(module, checker, **kw):
    p = call(module.generate, seconds=3, **kw)
    p = {k: grid(p[k]) for k in ("input", "output")}
    if grid(call(checker, p["input"])) != p["output"]:
        raise RuntimeError("Registered checker disagrees with constructor label")
    return p


def query_kwargs(tid, corner):
    if not corner:
        return {}
    return {"num_bands": 2} if tid == "18447a8d" else {"scale": 1, "map_height": 1}


def slot_kwargs(tid, query, slot, rng):
    """Shape arguments for demo slot 0..2 so the canonical profile holds."""
    h, w = len(query["input"]), len(query["input"][0])
    if tid == "18447a8d":
        n = (h - 1) // 4
        if slot == 0:
            return {"num_bands": n}
        return {"num_bands": rng.choice([k for k in range(2, 8) if k != n])}
    return {"scale": w // 3, "map_height": h - w - 1}


def audit(job):
    tid, corner = job
    tag = ["corner"] if corner else []
    started = time.monotonic()
    module = importlib.import_module("tasks.task_" + tid)
    checker = verification_solver(tid)
    profile = profile_from_task(reference(tid)["canonical"])
    wanted = profile["patterns"][0]
    files = {"constructor": BASE.parent / "tasks" / f"task_{tid}.py",
             "factory": BASE / "direct_factories" / f"task_{tid}.py",
             "factory_certificate": BASE / "direct_factories" / f"{tid}.json",
             "native_i_evidence": BASE / "native_i_evidence.py",
             "colour_evidence": BASE / "colour_evidence.py",
             "verified_rules": BASE / "verified_rules.py",
             "program_targets": BASE / "program_targets.py",
             "episode_shape_policy": BASE / "episode_shape_policy.py",
             "finite_input_policy": BASE / "finite_input_policy.py",
             "prepare": BASE / "diversity" / "prepare.py",
             "harness": Path(__file__)}
    report = {"task_id": tid, "query_domain": "min_corner" if corner else "default",
              "passed": False, "method": METHOD, "method_version": METHOD_VERSION,
              "shape_profile": wanted, "split_scope": (
                  "demos drawn from the query's input_split; validation queries are a "
                  "~1/20 hash fraction of these fixed queries, not a production quota"),
              "source_sha256": {k: sha(p.read_bytes()) for k, p in files.items()},
              "queries_requested": QUERIES, "queries_accepted": 0, "queries_failed": [],
              "max_contexts_per_query": MAX_CONTEXTS, "max_split_draws_per_slot": SPLIT_DRAWS,
              "context_retries": 0, "context_retry_histogram": {},
              "context_failure_reasons": {}, "make_record_calls": 0,
              "query_split": {"train": 0, "validation": 0},
              "demo_draws": {"train": 0, "validation": 0},
              "demo_slots": {"train": 0, "validation": 0},
              "query_input_shapes": 0, "max_retry": 0}
    reasons, hist, shapes = Counter(), Counter(), set()
    try:
        for q in range(QUERIES):
            random.seed(seed_of(tid, "query", q, *tag))
            query = draw(module, checker, **query_kwargs(tid, corner))
            qorbit = input_orbit(query["input"])
            split = input_split(qorbit)
            report["query_split"][split] += 1
            shapes.add((len(query["input"]), len(query["input"][0])))
            accepted = None
            for attempt in range(MAX_CONTEXTS):
                cseed = seed_of(tid, "context", q, attempt, *tag)
                rng = random.Random(cseed)
                orbits, demos = {qorbit}, []
                try:
                    for slot in range(3):
                        kw = slot_kwargs(tid, query, slot, rng)
                        for _ in range(SPLIT_DRAWS):
                            random.seed(rng.getrandbits(48))
                            pair = draw(module, checker, **kw)
                            report["demo_draws"][split] += 1
                            orbit = input_orbit(pair["input"])
                            if orbit not in orbits and input_split(orbit) == split:
                                break
                        else:
                            raise MissingColourEvidence("split/orbit draw budget exhausted")
                        report["demo_slots"][split] += 1
                        orbits.add(orbit)
                        demos.append(pair)
                    rng.shuffle(demos)
                    if describe(demos, query["input"]) != wanted:
                        raise RuntimeError(f"shape profile violated: {describe(demos, query['input'])}")
                    palette = list(range(10))
                    random.Random(cseed + 1).shuffle(palette)
                    for d4 in range(8):
                        ep = episode(demos + [query], d4, palette)
                        ep.update(task_id=tid, episode_id=f"audit-{tid}-{q}-{attempt}-{d4}",
                                  d4_transform=d4, color_permutation=palette)
                        make_record(ep)
                        report["make_record_calls"] += 1
                        answers = candidate_predictions(tid, ep["train"], ep["test"][0]["input"],
                                                        palette, d4)
                        if answers != [ep["solutions"][0]]:
                            raise RuntimeError("Gate prediction disagrees with constructor label")
                    accepted = attempt
                    break
                except MissingColourEvidence as exc:
                    reasons[str(exc)] += 1
            if accepted is None:
                report["queries_failed"].append({"query": q, "seed": seed_of(tid, "query", q, *tag),
                                                 "split": split,
                                                 "input_shape": [len(query["input"]),
                                                                 len(query["input"][0])]})
                continue
            report["queries_accepted"] += 1
            report["context_retries"] += accepted
            hist[str(accepted)] += 1
        report["passed"] = not report["queries_failed"]
        if report["queries_failed"]:
            report["error"] = "Queries exhausted the bounded context budget (reported, not dropped)"
    except Exception as exc:
        report["error"] = repr(exc)
    report.update(context_retry_histogram=dict(sorted(hist.items(), key=lambda kv: int(kv[0]))),
                  context_failure_reasons=dict(reasons), query_input_shapes=len(shapes),
                  max_retry=max((int(k) for k in hist), default=0),
                  seconds=round(time.monotonic() - started, 2))
    return report


if __name__ == "__main__":
    ids = [a for a in sys.argv[1:] if not a.startswith("--")] or list(TASKS)
    with ProcessPoolExecutor(max_workers=2) as pool:
        jobs = [(t, False) for t in ids] + [(t, True) for t in ids]
        reports = list(pool.map(audit, jobs))
    for r in reports:
        print(json.dumps({k: v for k, v in r.items() if k not in ("source_sha256",)}), flush=True)
    if "--no-write" not in sys.argv:
        path = OUT / "context-audit.json"
        existing = json.loads(path.read_text()) if path.exists() else {}
        existing.update({r["task_id"] + ("@min_corner" if r["query_domain"] == "min_corner" else ""): r
                         for r in reports})
        path.write_text(json.dumps(existing, indent=2) + "\n")
