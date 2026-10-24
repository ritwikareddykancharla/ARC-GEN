"""Report-scoped ablation for 18447a8d: raw numeric colour orders vs ALL colour priorities.

Production (arc_agi2/native_i_evidence.py) keeps the bounded natural family:
complement (native) plus same_band, reverse, cyclic shifts, area, and raw
visible colour_ascending/descending. This experiment swaps the two numeric
orders for EVERY linear priority order of key colours. Survivors are the
linear extensions of the transitive closure of the demo output colour
chains, and a cycle refutes the family. It then measures what that costs on
identical inputs:

* the same QUERIES fixed minimum-corner (2-band) queries;
* the same demo random sequence per (query, attempt) in both arms, drawn at
  the query shape (2 bands), at most MAX_CONTEXTS attempts;
* every attempt checked under all 8 D4 with the attempt's seeded palette;
* queries are never dropped; exhausted budgets are recorded.

A self-check compares the closure method with brute force over every order
of the colours present (<= 7! orders) on small random contexts.

Run (two workers, one per arm):
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-i/priority_ablation.py
"""
import hashlib
import json
import random
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from itertools import permutations
from pathlib import Path

import numpy as np

from arc_agi2 import native_i_evidence as ev
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.diversity.recertify import episode
from arc_agi2.runtime import BASE

OUT = Path(__file__).resolve().parent
TID = "18447a8d"
QUERIES = 250
MAX_CONTEXTS = 64
BANDS = 2


def sha(b):
    return hashlib.sha256(b).hexdigest()


def seed_of(*parts):
    return int(sha(":".join(map(str, ("batch-i-priority-ablation",) + parts)).encode())[:12], 16)


# ----------------------------------------------------------- all-orders family
def priority_chain(demo, palette, d4):
    g, want = ev.to_native(demo["input"], d4), ev.to_native(demo["output"], d4)
    bg, lock = palette[7], palette[8]
    parsed, _ = ev._key_assignments(g, bg, lock)
    if parsed is None:
        return None
    bands, _, keys = parsed
    colour_of = {c: k for k, (c, _) in enumerate(keys)}
    if len(colour_of) != len(keys) or want.shape != g.shape:
        return None
    chain = []
    for b in bands:
        seen = {int(v) for i in b for v in want[i] if v not in (bg, lock)}
        if len(seen) != 1:
            return None
        c = seen.pop()
        if c not in colour_of:
            return None
        chain.append(c)
    drawn = ev._draw_keys(g, parsed, [colour_of[c] for c in chain], bg, lock)
    return None if drawn is None or (drawn != want).any() else chain


def priority_closure(demonstrations, palette, d4):
    edges = set()
    for demo in demonstrations:
        chain = priority_chain(demo, palette, d4)
        if chain is None:
            return None
        edges.update(zip(chain, chain[1:]))
    nodes = {x for e in edges for x in e}
    closure = set(edges)
    for k in nodes:
        for i in nodes:
            if (i, k) in closure:
                for j in nodes:
                    if (k, j) in closure:
                        closure.add((i, j))
    return None if any((x, x) in closure for x in nodes) else closure


def priority_orders(closure, colours):
    return [o for o in permutations(sorted(colours))
            if not any((o[j], o[i]) in closure for i in range(len(o)) for j in range(i + 1, len(o)))]


def priority_predictions(demonstrations, query_input, palette, d4):
    closure = priority_closure(demonstrations, palette, d4)
    if closure is None:
        return None
    g = ev.to_native(query_input, d4)
    parsed, _ = ev._key_assignments(g, palette[7], palette[8])
    if parsed is None:
        return [None]
    colour_of = {c: k for k, (c, _) in enumerate(parsed[2])}
    if len(colour_of) != len(parsed[2]):
        return [None]
    return [ev._draw_keys(g, parsed, [colour_of[c] for c in o], palette[7], palette[8])
            for o in priority_orders(closure, colour_of)]


def all_orders_gate(demonstrations, query_input, palette, d4):
    """Natural family without the numeric orders, plus every colour priority."""
    alive = ev._surviving_key_rules(demonstrations, palette, d4) - {
        "colour_ascending", "colour_descending"}
    preds = ev.key_lock_predictions(query_input, palette, d4)
    native = [preds[n] for n in alive] + (
        priority_predictions(demonstrations, query_input, palette, d4) or [])
    if not alive and priority_closure(demonstrations, palette, d4) is None:
        raise MissingColourEvidence("fit no candidate")
    keys = {None if p is None else p.tobytes() for p in native}
    if len(keys) != 1 or None in keys:
        raise MissingColourEvidence("ambiguous")


def natural_gate(demonstrations, query_input, palette, d4):
    ev.require_native_i_evidence(TID, demonstrations, [{"input": query_input}], palette, d4)


# ----------------------------------------------------------- brute-force self-check
def brute_priority(demos, query):
    def draw(g, order):
        g = np.array(g)
        rows = [i for i in range(g.shape[0]) if (g[i] != 7).any()]
        bands = []
        for i in rows:
            if bands and i == bands[-1][-1] + 1:
                bands[-1].append(i)
            else:
                bands.append([i])
        keys = {}
        for b in bands:
            cs = {int(v) for i in b for v in g[i]} - {7, 8}
            if len(cs) != 1:
                return None
            c = cs.pop()
            if c in keys:
                return None
            keys[c] = [int((g[i] == c).sum()) for i in b]
        present = [c for c in order if c in keys]
        out = np.where(g == 8, 8, 7)
        for b, c in zip(bands, present):
            for i, kw in zip(b, keys[c]):
                lw = int((g[i] == 8).sum())
                out[i, lw:lw + kw] = c
        return out.tolist()

    colours = sorted({int(v) for p in demos + [query] for r in p["input"] for v in r} - {7, 8})
    fit, preds = False, set()
    for order in permutations(colours):
        if all(draw(d["input"], order) == d["output"] for d in demos):
            fit = True
            preds.add(json.dumps(draw(query["input"], order)))
    return fit, preds


def self_check(cases=300):
    from tasks import task_18447a8d as m
    agreed, with_family = 0, 0
    for seed in range(cases):
        rng = random.Random(seed)
        random.seed(seed)
        n = rng.choice([2, 2, 3])
        pairs = [m.generate(num_bands=n, colors=rng.sample([1, 2, 3, 4, 5, 6, 9], n)) for _ in range(4)]
        fit, brute = brute_priority(pairs[:3], pairs[3])
        mine = priority_predictions(pairs[:3], pairs[3]["input"], list(range(10)), 0)
        ok = (mine is not None) == fit and (mine is None or
                                            {json.dumps(p.tolist()) for p in mine} == brute)
        agreed += ok
        with_family += mine is not None
    return {"cases": cases, "agree": agreed, "family_alive_cases": with_family}


# ----------------------------------------------------------- paired ablation
def arm(name):
    from tasks import task_18447a8d as m
    gate = natural_gate if name == "natural" else all_orders_gate
    started = time.monotonic()
    hist, failed, retries = Counter(), [], 0
    unseen_query_colour_first = 0
    for q in range(QUERIES):
        random.seed(seed_of("query", q))
        query = m.generate(num_bands=BANDS)
        for attempt in range(MAX_CONTEXTS):
            cseed = seed_of("context", q, attempt)
            random.seed(cseed)
            demos = [m.generate(num_bands=BANDS) for _ in range(3)]
            palette = list(range(10))
            random.Random(cseed + 1).shuffle(palette)
            pairs = demos + [query]
            try:
                for d4 in range(8):
                    ep = episode(pairs, d4, palette)
                    gate(ep["train"], ep["test"][0]["input"], palette, d4)
                break
            except MissingColourEvidence:
                if attempt == 0:
                    qc = {v for r in query["input"] for v in r} - {7, 8}
                    dc = {v for d in demos for r in d["input"] for v in r} - {7, 8}
                    unseen_query_colour_first += bool(qc - dc)
        else:
            failed.append({"query": q, "seed": seed_of("query", q)})
            continue
        hist[attempt] += 1
        retries += attempt
    return {"arm": name, "queries": QUERIES, "bands": BANDS, "max_contexts": MAX_CONTEXTS,
            "accepted": QUERIES - len(failed), "failed": failed, "total_retries": retries,
            "max_retry": max(hist) if hist else None,
            "first_context_accepted": hist.get(0, 0),
            "first_context_rejected_with_unseen_query_colour": unseen_query_colour_first,
            "retry_histogram": {str(k): v for k, v in sorted(hist.items())},
            "seconds": round(time.monotonic() - started, 1)}


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=2) as pool:
        arms = list(pool.map(arm, ["natural", "all_orders"]))
    report = {"task_id": TID, "method": "paired-fixed-query-same-demo-sequence-ablation",
              "self_check_vs_brute_force": self_check(),
              "arms": arms,
              "source_sha256": {
                  "native_i_evidence": sha((BASE / "native_i_evidence.py").read_bytes()),
                  "constructor": sha((BASE.parent / "tasks/task_18447a8d.py").read_bytes()),
                  "harness": sha(Path(__file__).read_bytes())}}
    print(json.dumps(report, indent=1))
    if "--no-write" not in sys.argv:
        (OUT / "priority-ablation.json").write_text(json.dumps(report, indent=1) + "\n")
