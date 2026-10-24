"""Gate-aware fixed-query context audit for native batch c7d4/d47a.

recertify.check calls program_targets.verify only; it does not run the
demonstration-evidence gate. make_record does. This audit supplements (does
not replace) the standard 1000/8000/16 certificates.

For every query domain, QUERIES queries are drawn once and kept FIXED. Per query:

* mixed: one recertify-style context of three independent default draws is
  checked with the batch competitor sets (identity palette, d4 = 0). Only
  its ambiguity is recorded;
* panel: PANEL same-shape contexts (demos drawn at the query's dimensions,
  as prepare's uniform/seen policy prefers) are ALL evaluated. A context is
  accepted only if
    1. the query and the three demonstrations have four distinct
       prepare.input_orbit identities (inputs only);
    2. make_record succeeds for all eight D4 transforms under a seeded palette
       (evidence gate - d47aa2ff only - plus exported program verification);
    3. the batch competitor set (competitors.py) leaves one answer on the
       query INPUT. For d47aa2ff this is the shipped gate's rule set, and its
       d4 = 0 verdict must equal make_record's (cross-check). For c7d4e6ad,
       which has no gate, this is a diagnostic: any ambiguity here is a
       measured gap and fails the audit.
  After acceptance only, as a soundness check, the unique competitor answer
  must equal the label in every D4 frame. A D4-dependent verdict is counted
  and fails the audit;
* search: if no panel context is accepted, further contexts are drawn up to
  MAX_CONTEXTS in total. Queries are never dropped or replaced. A query that
  exhausts the budget stays in the report as a failure with a reason:
  ``same_shape_orbit_capacity`` when every one of its contexts failed only on
  orbit distinctness and the sampled orbit count at its shape is below four
  (e.g. c7d4e6ad 3x3, a valid pair domain with ONE input orbit), otherwise
  ``context_budget_exhausted``. The valid pair domain is not narrowed to make
  this audit pass; strict orbit shortfalls belong to the production assembler.

Verdicts: ``semantic_checks_passed`` (no D4-dependent verdict, no gate versus
competitor disagreement, no ungated competitor ambiguity, every failure is
finite capacity), ``all_queries_accepted``, and strict ``passed`` = both.

Every pair label is checked by runtime.verification_solver. Selection sees
demonstrations and the query INPUT only (recertify.episode puts no answer in
'test'); no context is chosen by comparing against the query answer.

Run from the worktree root (two worker processes):
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-c7d4-d47a/context_audit.py
"""
import hashlib
import importlib
import importlib.util
import json
import random
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from arc_agi2 import dot_motion_d47aa2ff_evidence as motion
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import make_record
from arc_agi2.runtime import BASE, call, grid, verification_solver

OUT = Path(__file__).resolve().parent
TASKS = ("c7d4e6ad", "d47aa2ff")
QUERY_DOMAINS = {
    "c7d4e6ad": {"default": {}, "legacy_canvas": {"height": 10, "width": 10},
                 "min_canvas": {"height": 3, "width": 3},
                 "thin_3x30": {"height": 3, "width": 30},
                 "narrow_30x3": {"height": 30, "width": 3},
                 "max_canvas": {"height": 30, "width": 30}},
    "d47aa2ff": {"default": {}, "legacy_panels": {"height": 10, "width": 10},
                 "min_panels": {"height": 3, "width": 3},
                 "max_panels": {"height": 30, "width": 14}},
}
QUERIES = 250
PANEL = 8
MAX_CONTEXTS = 64
METHOD = "gate-aware-fixed-query-same-shape-orbit-distinct-context-panel"
METHOD_VERSION = 2
CAPACITY_DRAWS = 2000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def seed_of(*parts):
    return int(sha(":".join(map(str, ("batch-c7d4-d47a-context",) + parts)).encode())[:12], 16)


def competitors():
    spec = importlib.util.spec_from_file_location("batch_c7d4_d47a_competitors",
                                                  OUT / "competitors.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def draw(module, checker, **kw):
    p = call(module.generate, seconds=3, **kw)
    p = {k: grid(p[k]) for k in ("input", "output")}
    if grid(call(checker, p["input"])) != p["output"]:
        raise RuntimeError("Independent verifier disagrees with constructor label")
    return p


def shape_kw(tid, query):
    g = query["input"]
    return ({"height": len(g), "width": len(g[0])} if tid == "c7d4e6ad"
            else {"height": len(g), "width": (len(g[0]) - 1) // 2})


def sampled_orbits(module, kw, cache):
    """Distinct input orbits in CAPACITY_DRAWS seeded draws at one shape (cached)."""
    key = tuple(sorted(kw.items()))
    if key not in cache:
        state = random.getstate()
        random.seed(seed_of("capacity", key))
        cache[key] = len({input_orbit(module.generate(**kw)["input"])
                          for _ in range(CAPACITY_DRAWS)})
        random.setstate(state)
    return cache[key]


def native_label(tid, ep, palette, d4):
    """Label mapped back to the native frame (soundness check only)."""
    return tuple(tuple(r) for r in motion.native_frame(ep["solutions"][0], palette, d4))


def evaluate(tid, demos, query, cseed, comp, report, reasons):
    """(accepted, reason) for one context; selection never reads the query answer."""
    if len({input_orbit(p["input"]) for p in demos + [query]}) != 4:
        reasons["duplicate_input_orbit"] += 1
        return False
    if comp.ambiguous(tid, demos, query["input"]):
        reasons["batch_competitors_ambiguous"] += 1
        competitor_ok = False
    else:
        competitor_ok = True
    palette = list(range(10))
    random.Random(cseed + 1).shuffle(palette)
    verdicts = []
    for d4 in range(8):
        ep = episode(demos + [query], d4, palette)
        ep.update(task_id=tid, episode_id=f"audit-{tid}-{cseed}-{d4}",
                  d4_transform=d4, color_permutation=palette)
        try:
            make_record(ep)
            report["make_record_calls"] += 1
        except MissingColourEvidence as exc:
            reasons[str(exc)] += 1
            verdicts.append(False)
            continue
        verdicts.append(True)
        if tid == "d47aa2ff" and competitor_ok:
            answers = motion.candidate_predictions(ep["train"], ep["test"][0]["input"], palette, d4)
            if answers != [native_label(tid, ep, palette, d4)]:
                raise RuntimeError("Accepted context: gate prediction disagrees with label")
    if len(set(verdicts)) != 1:
        report["d4_inconsistent_contexts"] += 1
    if tid == "d47aa2ff" and verdicts[0] != competitor_ok:
        report["gate_competitor_disagreements"] += 1
    if tid == "c7d4e6ad" and competitor_ok:
        answers = comp.candidate_predictions(tid, demos, query["input"])
        if [list(r) for r in answers[0]] != query["output"]:
            raise RuntimeError("Accepted context: competitor prediction disagrees with label")
    return all(verdicts) and competitor_ok


def audit(job):
    tid, domain = job
    query_kw = QUERY_DOMAINS[tid][domain]
    started = time.monotonic()
    comp = competitors()
    module = importlib.import_module("tasks.task_" + tid)
    checker = verification_solver(tid)
    files = {"constructor": BASE.parent / "tasks" / f"task_{tid}.py",
             "factory": BASE / "direct_factories" / f"task_{tid}.py",
             "factory_certificate": BASE / "direct_factories" / f"{tid}.json",
             "dot_motion_d47aa2ff_evidence": BASE / "dot_motion_d47aa2ff_evidence.py",
             "colour_evidence": BASE / "colour_evidence.py",
             "verified_rules": BASE / "verified_rules.py",
             "program_targets": BASE / "program_targets.py",
             "prepare": BASE / "diversity" / "prepare.py",
             "competitors": OUT / "competitors.py",
             "harness": Path(__file__)}
    report = {"task_id": tid, "query_domain": domain, "query_kwargs": query_kw,
              "passed": False, "method": METHOD, "method_version": METHOD_VERSION,
              "gated": tid == "d47aa2ff",
              "source_sha256": {k: sha(p.read_bytes()) for k, p in files.items()},
              "queries_requested": QUERIES, "queries_accepted": 0, "queries_failed": [],
              "panel_contexts_per_query": PANEL, "max_contexts_per_query": MAX_CONTEXTS,
              "make_record_calls": 0, "pair_draws": 0, "contexts_evaluated": 0,
              "contexts_rejected": 0, "d4_inconsistent_contexts": 0,
              "gate_competitor_disagreements": 0,
              "mixed_first_context_ambiguous": 0, "panel_first_context_rejected": 0}
    reasons, panel_hist, first_hist = Counter(), Counter(), Counter()
    capacity_cache, failure_kinds = {}, Counter()
    rule_sets_hist, answers_hist, shapes, query_hashes = Counter(), Counter(), set(), []
    try:
        for q in range(QUERIES):
            random.seed(seed_of(tid, domain, "query", q))
            query = draw(module, checker, **query_kw)
            report["pair_draws"] += 1
            shapes.add((len(query["input"]), len(query["input"][0])))
            query_hashes.append(sha(json.dumps(query["input"]).encode()))
            fixed_input = json.dumps(query["input"])
            random.seed(seed_of(tid, domain, "mixed", q))
            mixed = [draw(module, checker) for _ in range(3)]
            report["pair_draws"] += 3
            report["mixed_first_context_ambiguous"] += comp.ambiguous(tid, mixed, query["input"])
            accepted, first, rule_sets, max_answers = 0, None, set(), 0
            orbit_only = True
            for attempt in range(MAX_CONTEXTS):
                if attempt >= PANEL and first is not None:
                    break
                cseed = seed_of(tid, domain, "context", q, attempt)
                random.seed(cseed)
                demos = [draw(module, checker, **shape_kw(tid, query)) for _ in range(3)]
                report["pair_draws"] += 3
                report["contexts_evaluated"] += 1
                if attempt < PANEL:
                    rule_sets.add(frozenset(comp.surviving(tid, demos)))
                    max_answers = max(max_answers, len(comp.candidate_predictions(
                        tid, demos, query["input"])))
                before = reasons["duplicate_input_orbit"]
                ok = evaluate(tid, demos, query, cseed, comp, report, reasons)
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
            rule_sets_hist[str(len(rule_sets))] += 1
            answers_hist[str(max_answers)] += 1
            if first is None:
                orbits = sampled_orbits(module, shape_kw(tid, query), capacity_cache)
                kind = ("same_shape_orbit_capacity" if orbit_only and orbits < 4
                        else "context_budget_exhausted")
                failure_kinds[kind] += 1
                report["queries_failed"].append({
                    "query": q, "seed": seed_of(tid, domain, "query", q), "reason": kind,
                    "shape": [len(query["input"]), len(query["input"][0])],
                    "sampled_orbits_at_shape": orbits, "capacity_draws": CAPACITY_DRAWS,
                    "input": query["input"]})
                continue
            if first >= PANEL:
                report["queries_needing_search_beyond_panel"] = (
                    report.get("queries_needing_search_beyond_panel", 0) + 1)
            first_hist[str(first)] += 1
            report["queries_accepted"] += 1
        if failure_kinds["context_budget_exhausted"]:
            raise ValueError("Queries exhausted the context budget without a capacity reason")
        if report["d4_inconsistent_contexts"]:
            raise ValueError("Gate verdict depends on the D4 transform")
        if report["gate_competitor_disagreements"]:
            raise ValueError("Gate verdict differs from the batch competitor verdict")
        if tid == "c7d4e6ad" and reasons["batch_competitors_ambiguous"]:
            raise ValueError("Ungated family shows competitor ambiguity")
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
                  distinct_surviving_rule_sets_per_query_histogram=dict(sorted(rule_sets_hist.items(), key=key)),
                  max_candidate_answers_in_panel_histogram=dict(sorted(answers_hist.items(), key=key)),
                  context_failure_reasons=dict(sorted(reasons.items())),
                  query_input_shapes=len(shapes),
                  query_inputs_sha256=sha("\n".join(query_hashes).encode()),
                  panel_acceptance_rate=round(sum(int(k) * v for k, v in panel_hist.items())
                                              / (PANEL * QUERIES), 4),
                  seconds=round(time.monotonic() - started, 2))
    return report


if __name__ == "__main__":
    ids = [a for a in sys.argv[1:] if not a.startswith("--")] or list(TASKS)
    jobs = [(t, d) for t in ids for d in QUERY_DOMAINS[t]]
    with ProcessPoolExecutor(max_workers=2) as pool:
        reports = list(pool.map(audit, jobs))
    for r in reports:
        print(json.dumps({k: v for k, v in r.items()
                          if k not in ("source_sha256", "context_failure_reasons", "queries_failed")}),
              flush=True)
    if "--no-write" not in sys.argv:
        path = OUT / "context-audit.json"
        existing = json.loads(path.read_text()) if path.exists() else {}
        existing.update({r["task_id"] + ("" if r["query_domain"] == "default" else "@" + r["query_domain"]): r
                         for r in reports})
        path.write_text(json.dumps(existing, indent=2, sort_keys=True) + "\n")
