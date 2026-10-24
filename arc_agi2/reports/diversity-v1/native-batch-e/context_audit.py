"""Gate-aware query-preserving context audit for native batch E.

recertify.check only calls program_targets.verify, which does not run the
colour/demonstration evidence gates; make_record does. This audit supplements
(does not replace) the standard 1000/8000/16 certificates:

* each of QUERIES fresh queries is drawn once and kept FIXED;
* the three demonstrations are drawn at the query's own input dimensions
  (strict same-shape context, the canonical 'uniform/seen' shape profile of
  all four families), resampled at most MAX_CONTEXTS times;
* a context is accepted only if, for all eight D4 transforms under a seeded
  palette, make_record succeeds (evidence gate + exported program verify) AND,
  for the gated families, the unique prediction of the surviving candidate
  rules equals the constructor label;
* every pair label is gated by runtime.verification_solver;
* a query that exhausts its budget fails the audit (queries are never dropped).

The default run draws queries from the default domain; the min-corner run
keeps every query at the smallest RANDOM canvas (MIN_CORNER), where
uninformative contexts are most frequent. First-context ambiguity is also
recorded for strict same-shape contexts and for recertify-style mixed-shape
contexts (three independent default draws).

The version before the e0fb7511 threshold candidates is kept as
context-audit-pre-threshold-b9480e9.json.

Run from the worktree root (two workers):
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-e/context_audit.py
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
from arc_agi2.diversity.recertify import episode
from arc_agi2.mirror_neighbourhood_evidence import TASK_IDS as GATED, candidate_predictions
from arc_agi2.program_targets import make_record
from arc_agi2.runtime import BASE, call, grid, verification_solver

TASKS = ("0c786b71", "e0fb7511", "f0df5ff0", "f3cdc58f")
QUERIES = 250
MAX_CONTEXTS = 64
METHOD = "gate-aware-query-preserving-same-shape-context"
METHOD_VERSION = 2   # v2: gate predictions via candidate_predictions (e0 thresholds)
# smallest RANDOM input canvas (width, height) per family
MIN_CORNER = {"0c786b71": (2, 2), "e0fb7511": (6, 6), "f0df5ff0": (6, 6), "f3cdc58f": (4, 4)}
OUT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def seed_of(*parts):
    return int(sha(":".join(map(str, ("batch-e-context",) + parts)).encode())[:12], 16)


def draw(module, checker, **kw):
    p = call(module.generate, seconds=3, **kw)
    p = {k: grid(p[k]) for k in ("input", "output")}
    if grid(call(checker, p["input"])) != p["output"]:
        raise RuntimeError("Independent verifier disagrees with constructor label")
    return p


def gate_prediction(tid, ep, palette):
    """Unique answer implied by the demonstrations alone (None if unresolved)."""
    answers = candidate_predictions(tid, ep["train"], ep["test"][0]["input"], palette)
    return answers[0] if len(answers) == 1 else None


def audit(job):
    tid, corner = job
    tag = ["corner"] if corner else []
    query_kw = dict(zip(("width", "height"), MIN_CORNER[tid])) if corner else {}
    started = time.monotonic()
    module = importlib.import_module("tasks.task_" + tid)
    checker = verification_solver(tid)
    files = {"constructor": BASE.parent / "tasks" / f"task_{tid}.py",
             "factory": BASE / "direct_factories" / f"task_{tid}.py",
             "factory_certificate": BASE / "direct_factories" / f"{tid}.json",
             "mirror_neighbourhood_evidence": BASE / "mirror_neighbourhood_evidence.py",
             "colour_evidence": BASE / "colour_evidence.py",
             "verified_rules": BASE / "verified_rules.py",
             "program_targets": BASE / "program_targets.py",
             "harness": Path(__file__)}
    report = {"task_id": tid, "query_domain": "min_corner" if corner else "default",
              "passed": False, "method": METHOD, "method_version": METHOD_VERSION,
              "gated": tid in GATED,
              "source_sha256": {k: sha(p.read_bytes()) for k, p in files.items()},
              "queries_requested": QUERIES, "queries_accepted": 0, "queries_failed": [],
              "max_contexts_per_query": MAX_CONTEXTS, "context_retries": 0,
              "context_retry_histogram": {}, "context_failure_reasons": {},
              "make_record_calls": 0, "pair_draws": 0,
              "first_context_ambiguous": {"same_shape": 0, "mixed_shape": 0},
              "query_input_shapes": 0}
    reasons, hist, shapes = Counter(), Counter(), set()
    try:
        for q in range(QUERIES):
            random.seed(seed_of(tid, "query", q, *tag))
            query = draw(module, checker, **query_kw)
            h, w = len(query["input"]), len(query["input"][0])
            shapes.add((h, w))
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
                demos = [draw(module, checker, width=w, height=h) for _ in range(3)]
                report["pair_draws"] += 3
                palette = list(range(10))
                random.Random(cseed + 1).shuffle(palette)
                try:
                    for d4 in range(8):
                        ep = episode(demos + [query], d4, palette)
                        ep.update(task_id=tid, episode_id=f"audit-{tid}-{q}-{attempt}-{d4}",
                                  d4_transform=d4, color_permutation=palette)
                        make_record(ep)
                        report["make_record_calls"] += 1
                        if tid in GATED and gate_prediction(tid, ep, palette) != ep["solutions"][0]:
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
        if report["queries_failed"]:
            raise ValueError("Queries exhausted the bounded context budget")
        report["passed"] = True
    except Exception as exc:
        report["error"] = repr(exc)
    report.update(context_retry_histogram=dict(sorted(hist.items(), key=lambda kv: int(kv[0]))),
                  context_failure_reasons=dict(reasons), query_input_shapes=len(shapes),
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
