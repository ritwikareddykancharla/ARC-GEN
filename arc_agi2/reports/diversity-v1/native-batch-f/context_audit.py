"""Gate-aware query-preserving context audit for native batch F.

recertify.check only calls program_targets.verify, which does not run the
colour/demonstration evidence gates; make_record does. This audit supplements
(does not replace) the standard 1000/8000/16 certificates, and it is NOT a
production export (no prepare/admission run):

* each of QUERIES fresh queries is drawn once and kept FIXED;
* three demonstrations are drawn at the query's own input dimensions (strict
  same-shape context, the canonical 'uniform/seen' shape profile of all three
  families), exact-input distinct from each other and from the query, and
  resampled at most MAX_CONTEXTS times;
* a context is accepted only if, for all eight D4 transforms under a seeded
  palette, make_record succeeds (self-tiler evidence gate + exported program
  verify) AND the gate's unique candidate prediction equals the constructor label;
* every pair label is gated by runtime.verification_solver;
* a query that exhausts its budget fails the audit (queries are never dropped).

The default run draws queries from the default domain; the min-corner run keeps
every query at 2x2, the smallest random canvas. Accepted contexts are also
classified by whether their four inputs have distinct prepare.input_orbit
values (small-shape-orbits.json): at 2x2, 27f8ce4f and 48f8583b have only two
orbits, so four-distinct-orbit episodes are impossible there; 5b6cbef5 has
exactly four orbits, all train, so it has no validation support and only
limited train support (every such episode uses all four orbits). Contexts that
this audit accepts with fewer distinct orbits are not pipeline-buildable.

Run from the worktree root (two workers):
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-f/context_audit.py
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

from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import make_record
from arc_agi2.runtime import BASE, call, grid, verification_solver
from arc_agi2.self_tiler_evidence import candidate_predictions

TASKS = ("27f8ce4f", "48f8583b", "5b6cbef5")
QUERIES = 250
MAX_CONTEXTS = 64
MAX_DISTINCT_REDRAWS = 50
METHOD = "gate-aware-query-preserving-same-shape-context"
METHOD_VERSION = 1
MIN_CORNER = (2, 2)
OUT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def seed_of(*parts):
    return int(sha(":".join(map(str, ("batch-f-context",) + parts)).encode())[:12], 16)


def draw(module, checker, **kw):
    p = call(module.generate, seconds=3, **kw)
    p = {k: grid(p[k]) for k in ("input", "output")}
    if grid(call(checker, p["input"])) != p["output"]:
        raise RuntimeError("Independent verifier disagrees with constructor label")
    return p


def audit(job):
    tid, corner = job
    tag = ["corner"] if corner else []
    query_kw = dict(zip(("height", "width"), MIN_CORNER)) if corner else {}
    started = time.monotonic()
    module = importlib.import_module("tasks.task_" + tid)
    checker = verification_solver(tid)
    files = {"constructor": BASE.parent / "tasks" / f"task_{tid}.py",
             "factory": BASE / "direct_factories" / f"task_{tid}.py",
             "factory_certificate": BASE / "direct_factories" / f"{tid}.json",
             "self_tiler_evidence": BASE / "self_tiler_evidence.py",
             "colour_evidence": BASE / "colour_evidence.py",
             "verified_rules": BASE / "verified_rules.py",
             "program_targets": BASE / "program_targets.py",
             "prepare_input_orbit": BASE / "diversity" / "prepare.py",
             "harness": Path(__file__)}
    report = {"task_id": tid, "query_domain": "min_corner" if corner else "default",
              "passed": False, "method": METHOD, "method_version": METHOD_VERSION,
              "gated": True,
              "source_sha256": {k: sha(p.read_bytes()) for k, p in files.items()},
              "queries_requested": QUERIES, "queries_accepted": 0, "queries_failed": [],
              "max_contexts_per_query": MAX_CONTEXTS, "context_retries": 0,
              "context_retry_histogram": {}, "context_failure_reasons": {},
              "make_record_calls": 0, "pair_draws": 0, "distinctness_redraws": 0,
              "accepted_with_four_distinct_orbits": 0,
              "first_context_ambiguous": {"same_shape": 0, "mixed_shape": 0},
              "query_input_shapes": 0, "query_classes": {}}
    reasons, hist, shapes, classes = Counter(), Counter(), set(), Counter()
    try:
        for q in range(QUERIES):
            random.seed(seed_of(tid, "query", q, *tag))
            query = draw(module, checker, **query_kw)
            h, w = len(query["input"]), len(query["input"][0])
            shapes.add((h, w))
            counts = Counter(v for r in query["input"] for v in r)
            classes[f"colours={len(counts)}" if tid != "5b6cbef5" else
                    "full" if 0 not in counts else
                    "ink_majority" if counts[0] * 2 < h * w else
                    "ink_tie" if counts[0] * 2 == h * w else "ink_minority"] += 1
            random.seed(seed_of(tid, "mixed", q, *tag))
            mixed = [draw(module, checker) for _ in range(3)]
            report["pair_draws"] += 4
            try:
                require_colour_evidence(tid, mixed, [{"input": query["input"]}])
            except MissingColourEvidence:
                report["first_context_ambiguous"]["mixed_shape"] += 1
            accepted = None
            for attempt in range(MAX_CONTEXTS):
                cseed = seed_of(tid, "context", q, attempt, *tag)
                random.seed(cseed)
                demos, used = [], {json.dumps(query["input"])}
                for _ in range(MAX_DISTINCT_REDRAWS * 3):
                    p = draw(module, checker, height=h, width=w)
                    report["pair_draws"] += 1
                    if json.dumps(p["input"]) in used:
                        report["distinctness_redraws"] += 1
                        continue
                    used.add(json.dumps(p["input"]))
                    demos.append(p)
                    if len(demos) == 3:
                        break
                else:
                    raise RuntimeError("could not draw three distinct demonstrations")
                palette = list(range(10))
                random.Random(cseed + 1).shuffle(palette)
                try:
                    for d4 in range(8):
                        ep = episode(demos + [query], d4, palette)
                        ep.update(task_id=tid, episode_id=f"audit-{tid}-{q}-{attempt}-{d4}",
                                  d4_transform=d4, color_permutation=palette)
                        make_record(ep)
                        report["make_record_calls"] += 1
                        answers = candidate_predictions(tid, ep["train"], ep["test"][0]["input"],
                                                        palette)
                        if answers != [ep["solutions"][0]]:
                            raise RuntimeError("Gate prediction disagrees with constructor label")
                    accepted = attempt
                    break
                except MissingColourEvidence as exc:
                    reasons[str(exc)] += 1
                    if attempt == 0:
                        report["first_context_ambiguous"]["same_shape"] += 1
            if accepted is None:
                report["queries_failed"].append({"query": q, "seed": seed_of(tid, "query", q, *tag),
                                                 "input_shape": [h, w]})
                continue
            report["queries_accepted"] += 1
            report["context_retries"] += accepted
            hist[str(accepted)] += 1
            if len({input_orbit(p["input"]) for p in demos + [query]}) == 4:
                report["accepted_with_four_distinct_orbits"] += 1
        if report["queries_failed"]:
            raise ValueError("Queries exhausted the bounded context budget")
        report["passed"] = True
    except Exception as exc:
        report["error"] = repr(exc)
    report.update(context_retry_histogram=dict(sorted(hist.items(), key=lambda kv: int(kv[0]))),
                  context_failure_reasons=dict(reasons), query_input_shapes=len(shapes),
                  query_classes=dict(sorted(classes.items())),
                  seconds=round(time.monotonic() - started, 2))
    return report


if __name__ == "__main__":
    ids = [a for a in sys.argv[1:] if not a.startswith("--")] or list(TASKS)
    with ProcessPoolExecutor(max_workers=2) as pool:
        jobs = [(t, False) for t in ids] + [(t, True) for t in ids]
        reports = list(pool.map(audit, jobs))
    for r in reports:
        print(json.dumps({k: v for k, v in r.items() if k != "source_sha256"}), flush=True)
    if "--no-write" not in sys.argv:
        path = OUT / "context-audit.json"
        existing = json.loads(path.read_text()) if path.exists() else {}
        existing.update({r["task_id"] + ("@min_corner" if r["query_domain"] == "min_corner" else ""): r
                         for r in reports})
        path.write_text(json.dumps(existing, indent=2) + "\n")
