"""Gate-aware fixed-query context audit for native batch G (8ba14f53, 4cd1b7b2).

recertify.check only calls program_targets.verify, which does not run the
demonstration-evidence gates; make_record does. This audit supplements (does
not replace) the standard 1000/8000/16 certificates.

For every query domain, QUERIES queries are drawn once and kept FIXED. Per query:

* mixed: one recertify-style context of three independent default draws is
  checked by the gate (identity palette, d4 = 0). Only its ambiguity is
  recorded;
* panel: PANEL independent same-shape contexts are ALL evaluated. Demos are
  drawn at the query's input dimensions, matching prepare's uniform/seen
  policy (4cd1b7b2 is always 4x4; its demos come from the default sampler
  whatever the query domain). A context is accepted only if make_record
  succeeds for all eight D4 transforms under a seeded palette (evidence gate
  plus exported program verify), AND the gate's unique prediction equals the
  constructor label on each. A D4-dependent verdict is recorded as an
  inconsistency and fails the audit;
* search: if no panel context is accepted, further contexts are drawn up to
  MAX_CONTEXTS in total. A query that exhausts the budget fails the audit;
  queries are never dropped.

Every pair label is checked by runtime.verification_solver. The gate sees
demonstrations and the query INPUT only (recertify.episode puts no answer in
'test'); no context is chosen by comparing against the query answer. The
label comparison happens only after acceptance, as a soundness check.

Context variability is reported per query: panel acceptance counts, distinct
surviving-rule sets and distinct candidate-answer counts at d4 = 0 under the
identity palette.

Run from the worktree root:
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-g/context_audit.py
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

from arc_agi2 import hole_tally_8ba14f53_evidence as tally
from arc_agi2 import latin_fill_4cd1b7b2_evidence as latin
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import make_record
from arc_agi2.runtime import BASE, call, grid, verification_solver

TASKS = ("8ba14f53", "4cd1b7b2")
GATES = {"8ba14f53": tally, "4cd1b7b2": latin}
GATE_FILES = {"8ba14f53": "hole_tally_8ba14f53_evidence.py",
              "4cd1b7b2": "latin_fill_4cd1b7b2_evidence.py"}
QUERY_DOMAINS = {
    "8ba14f53": {"default": {}, "legacy_canvas": {"height": 4, "width": 9},
                 "min_canvas": {"height": 3, "width": 6}},
    "4cd1b7b2": {"default": {}, "blanks_1": {"blanks": 1}, "blanks_7": {"blanks": 7}},
}
QUERIES = 250
PANEL = 8
MAX_CONTEXTS = 64
METHOD = "gate-aware-fixed-query-same-shape-context-panel"
METHOD_VERSION = 1
OUT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def seed_of(*parts):
    return int(sha(":".join(map(str, ("batch-g-context",) + parts)).encode())[:12], 16)


def draw(module, checker, **kw):
    p = call(module.generate, seconds=3, **kw)
    p = {k: grid(p[k]) for k in ("input", "output")}
    if grid(call(checker, p["input"])) != p["output"]:
        raise RuntimeError("Independent verifier disagrees with constructor label")
    return p


def shape_kw(tid, query):
    return ({"height": len(query["input"]), "width": len(query["input"][0])}
            if tid == "8ba14f53" else {})


def evaluate(tid, demos, query, cseed, report, reasons):
    """(accepted, reason) for one context under all eight D4 transforms."""
    gate = GATES[tid]
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
        answers = gate.candidate_predictions(ep["train"], ep["test"][0]["input"], palette)
        if len(answers) != 1 or [list(r) for r in answers[0]] != ep["solutions"][0]:
            raise RuntimeError("Accepted context: gate prediction disagrees with label")
        verdicts.append(True)
    if len(set(verdicts)) != 1:
        report["d4_inconsistent_contexts"] += 1
    return all(verdicts)


def audit(job):
    tid, domain = job
    query_kw = QUERY_DOMAINS[tid][domain]
    started = time.monotonic()
    module = importlib.import_module("tasks.task_" + tid)
    checker = verification_solver(tid)
    gate = GATES[tid]
    files = {"constructor": BASE.parent / "tasks" / f"task_{tid}.py",
             "factory": BASE / "direct_factories" / f"task_{tid}.py",
             "factory_certificate": BASE / "direct_factories" / f"{tid}.json",
             "gate": BASE / GATE_FILES[tid],
             "colour_evidence": BASE / "colour_evidence.py",
             "verified_rules": BASE / "verified_rules.py",
             "program_targets": BASE / "program_targets.py",
             "harness": Path(__file__)}
    report = {"task_id": tid, "query_domain": domain, "query_kwargs": query_kw,
              "passed": False, "method": METHOD, "method_version": METHOD_VERSION,
              "source_sha256": {k: sha(p.read_bytes()) for k, p in files.items()},
              "queries_requested": QUERIES, "queries_accepted": 0, "queries_failed": [],
              "panel_contexts_per_query": PANEL, "max_contexts_per_query": MAX_CONTEXTS,
              "make_record_calls": 0, "pair_draws": 0, "contexts_evaluated": 0,
              "contexts_rejected": 0, "d4_inconsistent_contexts": 0,
              "mixed_first_context_ambiguous": 0,
              "panel_first_context_rejected": 0,
              "panel_accepted_histogram": {}, "first_accepted_index_histogram": {},
              "queries_needing_search_beyond_panel": 0,
              "distinct_surviving_rule_sets_per_query_histogram": {},
              "max_candidate_answers_in_panel_histogram": {},
              "context_failure_reasons": {}, "query_input_shapes": 0}
    reasons, panel_hist, first_hist = Counter(), Counter(), Counter()
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
            try:
                require_colour_evidence(tid, mixed, [{"input": query["input"]}])
            except MissingColourEvidence:
                report["mixed_first_context_ambiguous"] += 1
            accepted, first, rule_sets, max_answers = 0, None, set(), 0
            for attempt in range(MAX_CONTEXTS):
                if attempt >= PANEL and first is not None:
                    break
                cseed = seed_of(tid, domain, "context", q, attempt)
                random.seed(cseed)
                demos = [draw(module, checker, **shape_kw(tid, query)) for _ in range(3)]
                report["pair_draws"] += 3
                report["contexts_evaluated"] += 1
                if attempt < PANEL:
                    rule_sets.add(frozenset(gate.surviving_rules(demos)))
                    max_answers = max(max_answers, len(gate.candidate_predictions(
                        demos, query["input"])))
                ok = evaluate(tid, demos, query, cseed, report, reasons)
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
                report["queries_failed"].append({"query": q, "seed": seed_of(tid, domain, "query", q),
                                                 "input": query["input"]})
                continue
            if first >= PANEL:
                report["queries_needing_search_beyond_panel"] += 1
            first_hist[str(first)] += 1
            report["queries_accepted"] += 1
        if report["queries_failed"]:
            raise ValueError("Queries exhausted the bounded context budget")
        if report["d4_inconsistent_contexts"]:
            raise ValueError("Gate verdict depends on the D4 transform")
        report["passed"] = True
    except Exception as exc:
        report["error"] = repr(exc)
    key = lambda kv: int(kv[0])
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
    with ProcessPoolExecutor(max_workers=min(6, len(jobs))) as pool:
        reports = list(pool.map(audit, jobs))
    for r in reports:
        print(json.dumps({k: v for k, v in r.items() if k not in ("source_sha256", "context_failure_reasons")}),
              flush=True)
    if "--no-write" not in sys.argv:
        path = OUT / "context-audit.json"
        existing = json.loads(path.read_text()) if path.exists() else {}
        existing.update({r["task_id"] + ("" if r["query_domain"] == "default" else "@" + r["query_domain"]): r
                         for r in reports})
        path.write_text(json.dumps(existing, indent=2, sort_keys=True) + "\n")
