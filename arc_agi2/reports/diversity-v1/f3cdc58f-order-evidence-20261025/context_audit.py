"""Gate-aware, profile-honouring fixed-query context audit for f3cdc58f.

Runs the actual program_targets.make_record (histogram_order_evidence gate via
colour_evidence, then exported-program verification) on episodes shaped like
production's:

* QUERIES fixed queries per domain, drawn once and never dropped or replaced:
  'default' (generate(), W and H 4..30) and 'min_4x4' (the random minimum);
* demonstrations honour the canonical shape profile (uniform/seen: all three
  demos at the query's input shape), checked with episode_shape_policy.describe;
* all four inputs are DISTINCT prepare.input_orbit identities;
* every demo is in the query's finite_input_policy.input_split, redrawn per
  slot at most SPLIT_DRAWS times;
* at most MAX_CONTEXTS context attempts per query; an attempt is accepted only
  if make_record succeeds for all 8 D4 under the attempt's seeded palette AND
  the gate's unique prediction equals the constructor label (soundness check,
  after the gate verdict). A context whose verdict differs across D4 is counted;
* every pair label is checked by runtime.verification_solver.

Selection uses demonstrations and the query INPUT only (recertify.episode
puts no answer in 'test'). Not a production export: prepare is not run, no
quota is claimed, constructor/factory/checker are not recertified.

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/f3cdc58f-order-evidence-20261025/context_audit.py
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
from arc_agi2.histogram_order_evidence import candidate_predictions, surviving_rules
from arc_agi2.program_targets import make_record
from arc_agi2.runtime import BASE, call, grid, reference, verification_solver

TID = "f3cdc58f"
DOMAINS = {"default": {}, "min_4x4": {"width": 4, "height": 4}}
QUERIES = 250
MAX_CONTEXTS = 64
SPLIT_DRAWS = 400
METHOD = "gate-aware-profile-honouring-split-matched-fixed-query-context"
METHOD_VERSION = 1
OUT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def seed_of(*parts):
    return int(sha(":".join(map(str, ("f3-order-context",) + parts)).encode())[:12], 16)


def draw(module, checker, **kw):
    p = call(module.generate, seconds=3, **kw)
    p = {k: grid(p[k]) for k in ("input", "output")}
    if grid(call(checker, p["input"])) != p["output"]:
        raise RuntimeError("Registered checker disagrees with constructor label")
    return p


def legend_counts(g):
    flat = [v for row in g for v in row]
    return [flat.count(c) for c in (1, 2, 3, 4)]


def count_class(n):
    """Query count class in legend order; decides which readings it separates."""
    if len(set(n)) == 1:
        return "all_tied"
    up = all(a <= b for a, b in zip(n, n[1:]))
    down = all(a >= b for a, b in zip(n, n[1:]))
    return "nondecreasing" if up else "nonincreasing" if down else "non_monotone"


def audit(domain):
    started = time.monotonic()
    module = importlib.import_module("tasks.task_" + TID)
    checker = verification_solver(TID)
    wanted = profile_from_task(reference(TID)["canonical"])["patterns"][0]
    files = {"constructor": BASE.parent / "tasks" / f"task_{TID}.py",
             "factory": BASE / "direct_factories" / f"task_{TID}.py",
             "factory_certificate": BASE / "direct_factories" / f"{TID}.json",
             "histogram_order_evidence": BASE / "histogram_order_evidence.py",
             "colour_evidence": BASE / "colour_evidence.py",
             "verified_rules": BASE / "verified_rules.py",
             "program_targets": BASE / "program_targets.py",
             "augmentation": BASE / "augmentation.py",
             "episode_shape_policy": BASE / "episode_shape_policy.py",
             "finite_input_policy": BASE / "finite_input_policy.py",
             "prepare": BASE / "diversity" / "prepare.py",
             "recertify": BASE / "diversity" / "recertify.py",
             "harness": Path(__file__)}
    report = {"task_id": TID, "query_domain": domain, "passed": False,
              "method": METHOD, "method_version": METHOD_VERSION, "shape_profile": wanted,
              "split_scope": ("demos drawn from the query's input_split; validation queries are a "
                              "~1/20 hash fraction of these fixed queries, not a production quota"),
              "source_sha256": {k: sha(p.read_bytes()) for k, p in files.items()},
              "queries_requested": QUERIES, "queries_accepted": 0, "queries_failed": [],
              "max_contexts_per_query": MAX_CONTEXTS, "max_split_draws_per_slot": SPLIT_DRAWS,
              "make_record_calls": 0, "d4_inconsistent_contexts": 0}
    reasons, hist, shapes, palettes = Counter(), Counter(), Counter(), set()
    split_q, draws, slots = Counter(), Counter(), Counter()
    by_class = {}
    survivors_first, survivors_accepted = Counter(), Counter()
    try:
        for q in range(QUERIES):
            random.seed(seed_of(domain, "query", q))
            query = draw(module, checker, **DOMAINS[domain])
            h, w = len(query["input"]), len(query["input"][0])
            qorbit = input_orbit(query["input"])
            split = input_split(qorbit)
            split_q[split] += 1
            shapes[f"{h}x{w}"] += 1
            n = legend_counts(query["input"])
            cls = count_class(n)
            stats = by_class.setdefault(cls, {"queries": 0, "accepted": 0, "retries": 0,
                                              "first_context_rejected": 0, "tied_pairs": Counter()})
            stats["queries"] += 1
            stats["tied_pairs"][str(sum(a == b for i, a in enumerate(n) for b in n[i + 1:]))] += 1
            accepted = None
            for attempt in range(MAX_CONTEXTS):
                cseed = seed_of(domain, "context", q, attempt)
                rng = random.Random(cseed)
                orbits, demos = {qorbit}, []
                try:
                    for slot in range(3):
                        for _ in range(SPLIT_DRAWS):
                            random.seed(rng.getrandbits(48))
                            pair = draw(module, checker, width=w, height=h)
                            draws[split] += 1
                            orbit = input_orbit(pair["input"])
                            if orbit not in orbits and input_split(orbit) == split:
                                break
                        else:
                            raise MissingColourEvidence("split/orbit draw budget exhausted")
                        slots[split] += 1
                        orbits.add(orbit)
                        demos.append(pair)
                    if describe(demos, query["input"]) != wanted:
                        raise RuntimeError(f"shape profile violated: {describe(demos, query['input'])}")
                    alive = ",".join(sorted(surviving_rules(demos)))
                    if attempt == 0:
                        survivors_first[alive] += 1
                    palette = list(range(10))
                    random.Random(cseed + 1).shuffle(palette)
                    palettes.add(tuple(palette))
                    verdicts = []
                    for d4 in range(8):
                        ep = episode(demos + [query], d4, palette)
                        ep.update(task_id=TID, episode_id=f"audit-{domain}-{q}-{attempt}-{d4}",
                                  d4_transform=d4, color_permutation=palette)
                        report["make_record_calls"] += 1
                        try:
                            make_record(ep)
                            verdicts.append(True)
                        except MissingColourEvidence as exc:
                            verdicts.append(False)
                            last = exc
                            continue
                        answers = candidate_predictions(ep["train"], ep["test"][0]["input"],
                                                        palette, d4)
                        if answers != [ep["solutions"][0]]:
                            raise RuntimeError("Gate prediction disagrees with constructor label")
                    if len(set(verdicts)) > 1:
                        report["d4_inconsistent_contexts"] += 1
                    if not all(verdicts):
                        raise last
                    survivors_accepted[alive] += 1
                    accepted = attempt
                    break
                except MissingColourEvidence as exc:
                    reasons[str(exc)] += 1
                    if attempt == 0:
                        stats["first_context_rejected"] += 1
            if accepted is None:
                report["queries_failed"].append({"query": q, "seed": seed_of(domain, "query", q),
                                                 "split": split, "input_shape": [h, w],
                                                 "legend_counts": n, "count_class": cls})
                continue
            report["queries_accepted"] += 1
            stats["accepted"] += 1
            stats["retries"] += accepted
            hist[str(accepted)] += 1
        report["passed"] = (not report["queries_failed"]
                            and report["d4_inconsistent_contexts"] == 0)
        if report["queries_failed"]:
            report["error"] = "Queries exhausted the bounded context budget (reported, not dropped)"
    except Exception as exc:
        report["error"] = repr(exc)
    for stats in by_class.values():
        stats["tied_pairs"] = dict(sorted(stats["tied_pairs"].items()))
    report.update(
        context_retries=sum(int(k) * v for k, v in hist.items()),
        context_retry_histogram=dict(sorted(hist.items(), key=lambda kv: int(kv[0]))),
        max_retry=max((int(k) for k in hist), default=0),
        context_failure_reasons=dict(reasons),
        query_split=dict(split_q), demo_draws=dict(draws), demo_slots=dict(slots),
        query_count_classes=dict(sorted(by_class.items())),
        first_context_survivors=dict(survivors_first),
        accepted_context_survivors=dict(survivors_accepted),
        query_input_shapes=len(shapes),
        query_heights=[min(int(s.split("x")[0]) for s in shapes),
                       max(int(s.split("x")[0]) for s in shapes)] if shapes else None,
        query_widths=[min(int(s.split("x")[1]) for s in shapes),
                      max(int(s.split("x")[1]) for s in shapes)] if shapes else None,
        distinct_seeded_palettes=len(palettes),
        seconds=round(time.monotonic() - started, 2))
    return report


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=2) as pool:
        reports = list(pool.map(audit, list(DOMAINS)))
    for r in reports:
        print(json.dumps({k: v for k, v in r.items() if k != "source_sha256"}), flush=True)
    if "--no-write" not in sys.argv:
        (OUT / "context-audit.json").write_text(
            json.dumps({f"{TID}@{r['query_domain']}": r for r in reports}, indent=2) + "\n")
