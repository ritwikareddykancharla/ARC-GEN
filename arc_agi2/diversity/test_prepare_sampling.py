"""Regression checks for strict, identity-fair supplement episode sampling."""

import random
import time
from collections import Counter, defaultdict
from itertools import product

import pytest

from arc_agi2.diversity import prepare as P

ID = "canonical_input_hash"
PATTERNS = [
    {"demo_input_shapes": u, "query_input_shape": q}
    for u, q in product(("uniform", "mixed"), ("seen", "novel"))
]


def profile(*patterns):
    return {"version": "input-shape-pattern-v1", "patterns": list(patterns)}


def row(h, w, ident, n):
    g = [[(n + r * w + c) % 10 for c in range(w)] for r in range(h)]
    return {"input": g, "output": g, ID: ident, "input_hash": f"{ident}-{h}x{w}-{n}"}


def reference_feasible(pool, prof, identity):
    """The pre-fix implementation, kept verbatim as an oracle."""
    groups = defaultdict(set)
    for p in pool:
        groups[(len(p["input"]), len(p["input"][0]))].add(p[identity])
    all_ids = set().union(*groups.values()) if groups else set()
    result = []
    for query in pool:
        shape = (len(query["input"]), len(query["input"][0]))
        qid = query[identity]
        for pattern in prof["patterns"]:
            uniform = pattern["demo_input_shapes"] == "uniform"
            seen = pattern["query_input_shape"] == "seen"
            if uniform:
                possible = any(
                    len(ids - {qid}) >= 3 and ((s == shape) == seen) for s, ids in groups.items()
                )
            elif seen:
                possible = (
                    len(all_ids - {qid}) >= 3
                    and bool(groups[shape] - {qid})
                    and any(s != shape and ids - {qid} for s, ids in groups.items())
                )
            else:
                other = [ids - {qid} for s, ids in groups.items() if s != shape]
                possible = sum(bool(ids) for ids in other) >= 2 and len(set().union(*other)) >= 3
            if possible:
                result.append(query)
                break
    return result


@pytest.mark.parametrize("pattern_set", [[p] for p in PATTERNS] + [PATTERNS[:2], PATTERNS[1:]])
def test_fast_feasibility_matches_reference(pattern_set):
    rng = random.Random(7)
    prof = profile(*pattern_set)
    for trial in range(150):
        pool = []
        for n in range(rng.randrange(1, 14)):
            h, w = rng.choice([(2, 2), (2, 3), (3, 2), (4, 4)])
            # Small identity space: identities repeat and may span shapes,
            # as a canonical D4 orbit does for rotated inputs.
            pool.append(row(h, w, f"id{rng.randrange(7)}", n))
        expected = [id(p) for p in reference_feasible(pool, prof, ID)]
        assert [id(p) for p in P.feasible_queries(pool, prof, ID)] == expected, trial


def run(pool, prof, quota, emit, attempts=None):
    rejected = Counter()
    produced, stats = P.assemble_split(
        pool, prof, ID, quota, random.Random(3), emit,
        attempts=attempts if attempts is not None else max(100, quota * 40),
        deadline=time.monotonic() + 60, rejected=rejected, split="validation",
    )
    return produced, stats, rejected


def test_identity_fair_queries_do_not_starve_rare_identities():
    # One identity has 300 exact rows; twenty rare identities have one each.
    # Exact-row sampling would spend most attempts re-drawing the used heavy
    # identity. Identity-uniform sampling needs exactly one attempt each.
    pool = [row(3, 3, "heavy", n) for n in range(300)]
    pool += [row(3, 3, f"rare{k}", 1000 + k) for k in range(20)]
    episodes = []

    def emit(demos, query, report):
        episodes.append((demos, query, report))

    produced, stats, rejected = run(pool, profile(PATTERNS[0]), 21, emit, attempts=21)
    assert produced == 21 and stats["attempts"] == 21 and not rejected
    assert "shortfall" not in stats
    queries = [q[ID] for _, q, _ in episodes]
    assert len(set(queries)) == 21  # one episode per query identity
    for demos, query, report in episodes:
        ids = {d[ID] for d in demos} | {query[ID]}
        assert len(ids) == 4  # distinct demonstration and query identities
        assert len({d["input_hash"] for d in demos} | {query["input_hash"]}) == 4
        assert all(any(d is p for p in pool) for d in demos)  # same split pool only
        assert report["matched"] and report["fallback"] is None


def test_strict_shape_gate_reports_bounded_shortfall():
    # Five 3x3 identities support uniform/seen; the two 4x4 identities do not,
    # and must never be paired with 3x3 demonstrations.
    pool = [row(3, 3, f"a{k}", k) for k in range(5)] + [row(4, 4, f"b{k}", k) for k in range(2)]
    episodes = []

    def emit(demos, query, report):
        episodes.append((demos, query))

    produced, stats, _ = run(pool, profile(PATTERNS[0]), 10, emit)
    assert produced == 5 and stats["feasible_query_identities"] == 5
    for demos, query in episodes:
        assert {P._shape(d["input"]) for d in demos} == {P._shape(query["input"])} == {(3, 3)}
    shortfall = stats["shortfall"]
    assert shortfall["stop"] == "bounded_pool_query_support"
    assert shortfall["produced"] == 5 and shortfall["requested"] == 10
    assert "not a finite-capacity claim" in shortfall["note"]


def test_permanently_failing_queries_are_retired_after_bounded_attempts():
    pool = [row(3, 3, f"id{k}", k) for k in range(8)]
    bad = {"id0", "id1", "id2"}
    calls = Counter()

    def emit(demos, query, report):
        calls[query[ID]] += 1
        if query[ID] in bad:
            raise ValueError("missing colour evidence")

    produced, stats, rejected = run(pool, profile(PATTERNS[0]), 8, emit, attempts=10_000)
    assert produced == 5
    assert all(calls[b] == P.MAX_QUERY_FAILURES for b in bad)
    assert stats["retired_query_identities"] == 3
    assert stats["attempts"] == 5 + 3 * P.MAX_QUERY_FAILURES
    assert rejected["episode:ValueError:missing colour evidence"] == 3 * P.MAX_QUERY_FAILURES
    assert stats["shortfall"]["stop"] == "query_identities_retired_after_bounded_failures"


def test_mixed_novel_pattern_is_matched_not_relaxed():
    pool = [row(2, 2, "q", 0), row(3, 3, "a", 1), row(4, 4, "b", 2), row(4, 4, "c", 3)]
    reports = []

    def emit(demos, query, report):
        reports.append(report)

    produced, stats, _ = run(pool, profile(PATTERNS[3]), 4, emit)
    assert produced == stats["feasible_query_identities"] >= 1
    assert all(r["matched"] and r["observed"] == PATTERNS[3] for r in reports)
