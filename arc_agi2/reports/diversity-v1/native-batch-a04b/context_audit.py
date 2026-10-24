"""Gate-aware fixed-query context audit for a04b2602 (native batch a04b).

recertify.check calls program_targets.verify only; it does not run the
demonstration-evidence gate. make_record does. This audit supplements (does
not replace) the standard 1000/8000/16 certificate.

Query domains (QUERIES fixed queries each, drawn once and never replaced):
* ``default``: the default sampler;
* ``gap1``: default draws whose INPUT has two rectangles exactly one cell
  apart (the newly admitted canonical train[0] geometry). The condition reads
  the query input only (competitors.rectangles); draws that fail it are
  counted, and the first draw that meets it is the fixed query.

Per query:
* mixed: one context of three independent default draws is checked with the
  competitor harness (identity palette, d4 = 0); only its ambiguity is
  recorded;
* panel: PANEL same-shape contexts (demos drawn at the query's dimensions,
  as prepare's uniform/seen policy prefers) are ALL evaluated. A context is
  accepted only if
    1. the query and the three demonstrations have four distinct
       prepare.input_orbit identities (inputs only);
    2. make_record succeeds for all eight D4 transforms under a seeded palette
       (evidence gate plus exported program verification);
    3. the competitor harness (competitors.py, an implementation independent
       of the gate) leaves one answer on the query INPUT.
  The gate verdict must equal the harness verdict (cross-check) and must not
  depend on the D4 transform. After acceptance only, as a soundness check,
  the gate's unique native-frame answer must equal the label in every D4
  frame;
* search: if no panel context is accepted, further contexts are drawn up to
  MAX_CONTEXTS in total. A query that exhausts the budget stays in the report
  as a failure with a reason: ``same_shape_orbit_capacity`` when every one of
  its contexts failed only on orbit distinctness and the sampled orbit count
  at its shape is below four, otherwise ``context_budget_exhausted``. The
  valid pair domain is not narrowed to make this audit pass.

Verdicts: ``semantic_checks_passed`` (no D4-dependent verdict, no gate
versus harness disagreement, every accepted answer equals the label),
``all_queries_accepted`` (every failure is reported with its reason), and
strict ``passed`` = both.

Every pair label is checked by runtime.verification_solver. Selection sees
demonstrations and the query INPUT only (recertify.episode puts no answer in
'test'); no context is chosen by comparing against the query answer.

Run from the worktree root (two worker processes, one per domain):
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-a04b/context_audit.py
"""
import hashlib
import importlib
import importlib.util
import json
import random
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from arc_agi2 import rect_ring_a04b2602_evidence as gate
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import make_record
from arc_agi2.runtime import BASE, call, grid, verification_solver

OUT = Path(__file__).resolve().parent
PATH = OUT / "context-audit.json"
TID = "a04b2602"
DOMAINS = ("default", "gap1")
QUERIES = 250
PANEL = 8
MAX_CONTEXTS = 64
QUERY_DRAW_LIMIT = 200
METHOD = "gate-aware-fixed-query-same-shape-orbit-distinct-context-panel"
METHOD_VERSION = 2
CAPACITY_DRAWS = 2000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def seed_of(*parts):
    return int(sha(":".join(map(str, ("batch-a04b-context",) + parts)).encode())[:12], 16)


def competitors():
    spec = importlib.util.spec_from_file_location("batch_a04b_competitors", OUT / "competitors.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def draw(module, checker, **kw):
    p = call(module.generate, seconds=3, **kw)
    p = {k: grid(p[k]) for k in ("input", "output")}
    if grid(call(checker, p["input"])) != p["output"]:
        raise RuntimeError("Independent verifier disagrees with constructor label")
    return p


def min_gap(comp, g):
    boxes = comp.rectangles(g)
    return min(max(max(a[0] - b[2], b[0] - a[2]) - 1, max(a[1] - b[3], b[1] - a[3]) - 1)
               for k, a in enumerate(boxes) for b in boxes[:k])


def sampled_orbits(module, kw, cache):
    key = tuple(sorted(kw.items()))
    if key not in cache:
        state = random.getstate()
        random.seed(seed_of("capacity", key))
        cache[key] = len({input_orbit(module.generate(**kw)["input"])
                          for _ in range(CAPACITY_DRAWS)})
        random.setstate(state)
    return cache[key]


def evaluate(demos, query, cseed, comp, report, reasons):
    """Accepted? Selection never reads the query answer."""
    if len({input_orbit(p["input"]) for p in demos + [query]}) != 4:
        reasons["duplicate_input_orbit"] += 1
        return False
    competitor_ok = not comp.ambiguous(demos, query["input"])
    if not competitor_ok:
        reasons["batch_competitors_ambiguous"] += 1
    palette = list(range(10))
    random.Random(cseed + 1).shuffle(palette)
    verdicts = []
    for d4 in range(8):
        ep = episode(demos + [query], d4, palette)
        ep.update(task_id=TID, episode_id=f"audit-{TID}-{cseed}-{d4}",
                  d4_transform=d4, color_permutation=palette)
        try:
            make_record(ep)
            report["make_record_calls"] += 1
        except MissingColourEvidence as exc:
            reasons[str(exc)] += 1
            verdicts.append(False)
            continue
        verdicts.append(True)
        # Soundness, after acceptance only: the unique answer is the label.
        answers = gate.candidate_predictions(ep["train"], ep["test"][0]["input"], palette, d4)
        label = tuple(map(tuple, gate.native_frame(ep["solutions"][0], palette, d4)))
        if answers != [label]:
            raise RuntimeError("Accepted context: gate prediction disagrees with label")
    if len(set(verdicts)) != 1:
        report["d4_inconsistent_contexts"] += 1
    if verdicts[0] != competitor_ok:
        report["gate_competitor_disagreements"] += 1
    return all(verdicts) and competitor_ok


def audit(domain):
    started = time.monotonic()
    comp = competitors()
    module = importlib.import_module("tasks.task_" + TID)
    checker = verification_solver(TID)
    files = {"constructor": BASE.parent / "tasks" / f"task_{TID}.py",
             "factory": BASE / "direct_factories" / f"task_{TID}.py",
             "factory_certificate": BASE / "direct_factories" / f"{TID}.json",
             "gate": BASE / "rect_ring_a04b2602_evidence.py",
             "colour_evidence": BASE / "colour_evidence.py",
             "verified_rules": BASE / "verified_rules.py",
             "program_targets": BASE / "program_targets.py",
             "prepare": BASE / "diversity" / "prepare.py",
             "competitors": OUT / "competitors.py",
             "harness": Path(__file__)}
    report = {"task_id": TID, "query_domain": domain, "passed": False,
              "method": METHOD, "method_version": METHOD_VERSION, "gated": True,
              "source_sha256": {k: sha(p.read_bytes()) for k, p in files.items()},
              "queries_requested": QUERIES, "queries_accepted": 0, "queries_failed": [],
              "panel_contexts_per_query": PANEL, "max_contexts_per_query": MAX_CONTEXTS,
              "make_record_calls": 0, "pair_draws": 0, "query_draws_not_meeting_domain": 0,
              "contexts_evaluated": 0, "contexts_rejected": 0, "d4_inconsistent_contexts": 0,
              "gate_competitor_disagreements": 0, "mixed_first_context_ambiguous": 0,
              "panel_first_context_rejected": 0}
    reasons, panel_hist, first_hist = Counter(), Counter(), Counter()
    capacity_cache, failure_kinds, gaps = {}, Counter(), Counter()
    shapes, query_hashes = set(), []
    try:
        for q in range(QUERIES):
            for k in range(QUERY_DRAW_LIMIT):
                random.seed(seed_of(domain, "query", q, k))
                query = draw(module, checker)
                report["pair_draws"] += 1
                if domain == "default" or min_gap(comp, query["input"]) == 1:
                    break
                report["query_draws_not_meeting_domain"] += 1
            else:
                raise RuntimeError("no gap-1 query input within the draw limit")
            gaps[str(min(min_gap(comp, query["input"]), 6))] += 1
            h, w = len(query["input"]), len(query["input"][0])
            shapes.add((h, w))
            query_hashes.append(sha(json.dumps(query["input"]).encode()))
            fixed_input = json.dumps(query["input"])
            random.seed(seed_of(domain, "mixed", q))
            mixed = [draw(module, checker) for _ in range(3)]
            report["pair_draws"] += 3
            report["mixed_first_context_ambiguous"] += comp.ambiguous(mixed, query["input"])
            accepted, first, orbit_only = 0, None, True
            for attempt in range(MAX_CONTEXTS):
                if attempt >= PANEL and first is not None:
                    break
                cseed = seed_of(domain, "context", q, attempt)
                random.seed(cseed)
                demos = [draw(module, checker, height=h, width=w) for _ in range(3)]
                report["pair_draws"] += 3
                report["contexts_evaluated"] += 1
                before = reasons["duplicate_input_orbit"]
                ok = evaluate(demos, query, cseed, comp, report, reasons)
                if not ok and reasons["duplicate_input_orbit"] == before:
                    orbit_only = False
                if json.dumps(query["input"]) != fixed_input:
                    raise RuntimeError("query input changed during the audit")
                if not ok:
                    report["contexts_rejected"] += 1
                    if attempt == 0:
                        report["panel_first_context_rejected"] += 1
                    continue
                if attempt < PANEL:
                    accepted += 1
                if first is None:
                    first = attempt
            panel_hist[str(accepted)] += 1
            if first is None:
                orbits = sampled_orbits(module, {"height": h, "width": w}, capacity_cache)
                kind = ("same_shape_orbit_capacity" if orbit_only and orbits < 4
                        else "context_budget_exhausted")
                failure_kinds[kind] += 1
                report["queries_failed"].append({
                    "query": q, "reason": kind, "shape": [h, w],
                    "sampled_orbits_at_shape": orbits, "capacity_draws": CAPACITY_DRAWS,
                    "input": query["input"]})
            else:
                if first >= PANEL:
                    report["queries_needing_search_beyond_panel"] = (
                        report.get("queries_needing_search_beyond_panel", 0) + 1)
                first_hist[str(first)] += 1
                report["queries_accepted"] += 1
            if (q + 1) % 25 == 0:
                print(f"{domain}: {q + 1}/{QUERIES} queries, {report['queries_accepted']} accepted, "
                      f"{report['contexts_rejected']}/{report['contexts_evaluated']} contexts rejected, "
                      f"{round(time.monotonic() - started)}s", flush=True)
        if report["d4_inconsistent_contexts"]:
            raise ValueError("Gate verdict depends on the D4 transform")
        if report["gate_competitor_disagreements"]:
            raise ValueError("Gate verdict differs from the competitor harness verdict")
        report["semantic_checks_passed"] = True
    except Exception as exc:
        report["error"] = repr(exc)
    report.setdefault("semantic_checks_passed", False)
    report["all_queries_accepted"] = report["queries_accepted"] == QUERIES
    report["passed"] = report["semantic_checks_passed"] and report["all_queries_accepted"]
    report["queries_failed_by_reason"] = dict(sorted(failure_kinds.items()))
    key = lambda kv: int(kv[0])
    report.setdefault("queries_needing_search_beyond_panel", 0)
    report.update(panel_accepted_histogram=dict(sorted(panel_hist.items(), key=key)),
                  first_accepted_index_histogram=dict(sorted(first_hist.items(), key=key)),
                  query_min_gap_histogram=dict(sorted(gaps.items(), key=key)),
                  context_failure_reasons=dict(sorted(reasons.items())),
                  query_input_shapes=len(shapes),
                  query_inputs_sha256=sha("\n".join(query_hashes).encode()),
                  panel_acceptance_rate=round(sum(int(k) * v for k, v in panel_hist.items())
                                              / (PANEL * QUERIES), 4),
                  seconds=round(time.monotonic() - started, 2))
    return report


def persist(report):
    existing = json.loads(PATH.read_text()) if PATH.exists() else {}
    existing[TID + ("" if report["query_domain"] == "default" else "@" + report["query_domain"])] = report
    PATH.write_text(json.dumps(existing, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    domains = [a for a in sys.argv[1:] if not a.startswith("--")] or list(DOMAINS)
    with ProcessPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(audit, d) for d in domains]
        for future in as_completed(futures):
            r = future.result()
            print(json.dumps({k: v for k, v in r.items()
                              if k not in ("source_sha256", "context_failure_reasons", "queries_failed")}),
                  flush=True)
            if "--no-write" not in sys.argv:
                persist(r)
