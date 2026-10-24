"""Native batch I evidence gates (arc_agi2/native_i_evidence.py) for 18447a8d and b4a43f3b.

Every named competitor gets a constructor-built witness. The competitor
reproduces all demos and its own query prediction differs from the label
(or is undefined), so the gate rejects. The separable b4 evaluation is
cross-checked by brute force. Verdicts are D4-covariant. The 18447a8d raw
colour-number orders are palette-dependent by design (documented seed-9
case). The all-orders priority family is a report-scoped ablation only.
"""
import json
import random
import time
from pathlib import Path

import numpy as np
import pytest

from arc_agi2 import native_i_evidence as ev
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import make_record, verify
from arc_agi2.runtime import BASE, reference
from tasks import task_18447a8d as keys_task
from tasks import task_b4a43f3b as stamp_task

PALETTES = ([*range(10)], [3, 9, 0, 7, 2, 8, 1, 6, 4, 5], [6, 0, 8, 1, 9, 3, 2, 5, 7, 4])
REPORT = BASE / "reports/diversity-v1/native-batch-i"
K, B = "18447a8d", "b4a43f3b"


def decisions(tid, pairs):
    out = set()
    for pal in PALETTES:
        for d4 in range(8):
            ep = episode(pairs, d4, pal)
            try:
                ev.require_native_i_evidence(tid, ep["train"], ep["test"], pal, d4)
                answers = ev.candidate_predictions(tid, ep["train"], ep["test"][0]["input"], pal, d4)
                assert answers == [ep["solutions"][0]]
                out.add(True)
            except MissingColourEvidence:
                out.add(False)
    return out


def rejected_everywhere(tid, pairs):
    return decisions(tid, pairs) == {False}


def native_prediction_differs(pred, label):
    return pred is None or pred.tolist() != label


# ------------------------------------------------------------ 18447a8d builders
def key_scene(locks, assign, colours):
    """Band b receives the key drawn in band assign[b]; colours[i] colours band i's key."""
    n = len(locks)
    rights = [None] * n
    for b, i in enumerate(assign):
        rights[i] = [5 - v for v in locks[b]]
    return keys_task.generate(lefts=sum(locks, []), rights=sum(rights, []), colors=colours)


def random_locks(rng, n, tie=None):
    while True:                                          # bounded by the caller's search
        locks = [[rng.randint(1, 4) for _ in range(3)] for _ in range(n)]
        if len({tuple(x) for x in locks}) < n:
            continue
        areas = [sum(x) for x in locks]
        if tie is None or (len(set(areas)) < n) == tie:
            return locks


def aliases(pairs, competitor):
    """Named rules that make the same band assignment as ``competitor`` in every demo."""
    out = {competitor}
    for name in ev._key_assignments(np.array(pairs[0]["input"]), 7, 8)[1]:
        if all(ev._key_assignments(np.array(p["input"]), 7, 8)[1][name] ==
               ev._key_assignments(np.array(p["input"]), 7, 8)[1][competitor] for p in pairs[:3]):
            out.add(name)
    return out


def search(build, competitor, tries=3000, seed=0):
    """Find demos whose survivors are only the native rule and the competitor (or its aliases)."""
    rng = random.Random(seed)
    for _ in range(tries):
        pairs = build(rng)
        alive = ev.surviving_rules(K, pairs[:3])
        if competitor in alive and alive <= {"complement"} | aliases(pairs, competitor):
            return pairs
    raise AssertionError(f"no witness for {competitor} in {tries} tries")


POSITIONAL = {
    "same_band": (2, lambda n: list(range(n))),
    "reverse": (3, lambda n: [n - 1 - b for b in range(n)]),
    "shift_down_1": (3, lambda n: [(b - 1) % n for b in range(n)]),
    "shift_up_1": (3, lambda n: [(b + 1) % n for b in range(n)]),
}


@pytest.mark.parametrize("name", sorted(POSITIONAL))
def test_positional_competitor_witness(name):
    n, rule = POSITIONAL[name]

    def build(rng):
        demos = [key_scene(random_locks(rng, n, tie=True), rule(n), rng.sample([1, 2, 3, 4, 5, 6, 9], n))
                 for _ in range(3)]
        perm = rule(n)
        while perm == rule(n):
            perm = rng.sample(range(n), n)
        return demos + [key_scene(random_locks(rng, n, tie=False), perm, rng.sample([1, 2, 3, 4, 5, 6, 9], n))]

    pairs = search(build, name)
    pred = ev.key_lock_predictions(pairs[3]["input"], list(range(10)), 0)[name]
    assert native_prediction_differs(pred, pairs[3]["output"])
    assert rejected_everywhere(K, pairs)


def test_area_competitor_witness():
    def build(rng):
        demos = [key_scene(random_locks(rng, 3, tie=False), rng.sample(range(3), 3),
                           rng.sample([1, 2, 3, 4, 5, 6, 9], 3)) for _ in range(3)]
        return demos + [key_scene(random_locks(rng, 3, tie=True), rng.sample(range(3), 3),
                                  rng.sample([1, 2, 3, 4, 5, 6, 9], 3))]

    pairs = search(build, "area")
    assert ev.key_lock_predictions(pairs[3]["input"], list(range(10)), 0)["area"] is None
    assert rejected_everywhere(K, pairs)


@pytest.mark.parametrize("name", ["colour_ascending", "colour_descending"])
def test_raw_numeric_colour_order_competitor_witness(name):
    """Demos deal keys in raw colour-number order (identity palette); query does not."""
    def build(rng):
        demos = []
        for _ in range(3):
            n = rng.randint(2, 4)
            assign = rng.sample(range(n), n)
            chosen = sorted(rng.sample([1, 2, 3, 4, 5, 6, 9], n), reverse=name.endswith("descending"))
            colours = [None] * n
            for b, i in enumerate(assign):
                colours[i] = chosen[b]
            demos.append(key_scene(random_locks(rng, n, tie=True), assign, colours))
        return demos + [key_scene(random_locks(rng, 3, tie=True), rng.sample(range(3), 3),
                                  rng.sample([1, 2, 3, 4, 5, 6, 9], 3))]

    pairs = search(build, name)
    pred = ev.key_lock_predictions(pairs[3]["input"], list(range(10)), 0)[name]
    assert native_prediction_differs(pred, pairs[3]["output"])
    assert d4_decisions(K, pairs, list(range(10))) == {False}


def d4_decisions(tid, pairs, palette):
    out = set()
    for d4 in range(8):
        ep = episode(pairs, d4, palette)
        try:
            ev.require_native_i_evidence(tid, ep["train"], ep["test"], palette, d4)
            assert ev.candidate_predictions(tid, ep["train"], ep["test"][0]["input"],
                                            palette, d4) == [ep["solutions"][0]]
            out.add(True)
        except MissingColourEvidence:
            out.add(False)
    return out


def test_seed9_raw_numeric_order_verdict_is_documented_palette_dependent():
    """Bounded raw-numeric family: identity palette leaves colour_ascending alive and
    ambiguous; the seeded palette reorders the visible numbers and refutes it. Each
    verdict is D4-covariant (same for all eight transforms)."""
    random.seed(9)
    pairs = [keys_task.generate(num_bands=2) for _ in range(4)]
    assert "colour_ascending" in ev.surviving_rules(K, pairs[:3])
    assert d4_decisions(K, pairs, list(range(10))) == {False}
    assert d4_decisions(K, pairs, [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]) == {True}


def test_18447a8d_fixtures_accepted_everywhere():
    for version in ("canonical", "teaching_fixture"):
        fx = reference(K)[version]
        assert decisions(K, fx["train"] + fx["test"]) == {True}


def test_report_scoped_all_orders_ablation_helper_matches_brute_force():
    import importlib.util
    spec = importlib.util.spec_from_file_location("priority_ablation", REPORT / "priority_ablation.py")
    ab = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ab)
    check = ab.self_check(cases=60)
    assert check["agree"] == 60 and check["family_alive_cases"] > 10
    # The original ARC demos fit priority 1<9<2<3<6<4, and the query colour 5 is unseen:
    # all-orders would reject the canonical task; the production family does not.
    fx = reference(K)["canonical"]
    assert [ab.priority_chain(d, list(range(10)), 0) for d in fx["train"]] == \
        [[1, 9, 3], [9, 2], [2, 3, 6, 4]]
    assert len(ab.priority_predictions(fx["train"], fx["test"][0]["input"], list(range(10)), 0)) == 4
    report = json.loads((REPORT / "priority-ablation.json").read_text())
    natural, all_orders = report["arms"]
    assert natural["arm"] == "natural" and natural["accepted"] == natural["queries"]
    assert all_orders["total_retries"] > natural["total_retries"]


# ------------------------------------------------------------ b4a43f3b builders
def motif_invariant(colours, k):
    a = np.array([int(c) for c in colours]).reshape(3, 3)
    return (ev._d4(a, k) == a).all()


def motifs(rng, k=None, full=False, mono=None):
    """A constructor-domain motif; with k, coloured per orbit so it is k-invariant."""
    masks = [m for m in stamp_task.MOTIF_MASKS if (not full or len(m) == 9)]
    if k is not None:
        masks = [m for m in masks if motif_invariant(
            "".join("1" if (r, c) in m else "0" for r in range(3) for c in range(3)), k)]
    cells = rng.choice(masks)
    colour = {}
    for r, c in sorted(cells):
        if (r, c) in colour:
            continue
        ink = mono or rng.choice((1, 2, 3, 6))
        a = np.zeros((3, 3), dtype=int)
        a[r, c] = 1
        for _ in range(8):                      # orbit under the cyclic group of k
            for rr, cc in zip(*np.nonzero(a)):
                colour[(int(rr), int(cc))] = ink
            if k is None:
                break
            a = ev._d4(a, k)
    s = "".join(str(colour.get((r, c), 0)) for r in range(3) for c in range(3))
    assert k is None or motif_invariant(s, k)
    return s


def symmetric_map(rng, k, side=6):
    a = np.array([[rng.random() < 0.3 for _ in range(side)] for _ in range(side)])
    a[rng.randrange(side), rng.randrange(side)] = True
    m, orbit = a.copy(), a
    for _ in range(4):
        orbit = ev._d4(orbit, k)
        m |= orbit
    return "".join("2" if v else "0" for v in m.flatten())


def asymmetric_query(rng, motif_k=None, map_k=None, **kw):
    for _ in range(5000):
        colours = motifs(rng)
        if motif_k is not None and motif_invariant(colours, motif_k):
            continue
        pattern = "".join(rng.choice("0002") for _ in range(36))
        if "2" not in pattern:
            continue
        if map_k is not None:
            a = np.array([c == "2" for c in pattern]).reshape(6, 6)
            if (ev._d4(a, map_k) == a).all():
                continue
        return stamp_task.generate(colors=colours, pattern=pattern, scale=2, map_height=6, **kw)
    raise AssertionError("no query")


def b4_survives(pairs, tile_key, mask_key):
    return (tile_key, mask_key) in ev.surviving_rules(B, pairs[:3])


def generic_map(rng):
    return "".join(rng.choice("02") for _ in range(35)) + "2"


@pytest.mark.parametrize("k", range(1, 8))
def test_motif_transform_competitors(k):
    rng = random.Random(100 + k)
    demos = [stamp_task.generate(colors=motifs(rng, k=k), pattern=generic_map(rng)) for _ in range(3)]
    pairs = demos + [asymmetric_query(rng, motif_k=k)]
    assert b4_survives(pairs, ("to_3x3", k, "native"), (0, "marked"))
    assert rejected_everywhere(B, pairs)


@pytest.mark.parametrize("k", range(1, 8))
def test_map_transform_competitors(k):
    rng = random.Random(200 + k)
    demos = [stamp_task.generate(colors=motifs(rng), pattern=symmetric_map(rng, k)) for _ in range(3)]
    pairs = demos + [asymmetric_query(rng, map_k=k)]
    assert b4_survives(pairs, ("to_3x3", 0, "native"), (k, "marked"))
    assert rejected_everywhere(B, pairs)


def test_all_cells_selector_competitor():
    rng = random.Random(1)
    demos = [stamp_task.generate(colors=motifs(rng), pattern="2" * 36) for _ in range(3)]
    pairs = demos + [asymmetric_query(rng)]
    assert b4_survives(pairs, ("to_3x3", 0, "native"), (0, "all"))
    assert rejected_everywhere(B, pairs)


def test_unmarked_selector_competitor_on_checkerboards():
    rng = random.Random(2)
    checker = "".join("2" if (r + c) % 2 else "0" for r in range(6) for c in range(6))
    demos = [stamp_task.generate(colors=motifs(rng), pattern=checker) for _ in range(3)]
    pairs = demos + [asymmetric_query(rng)]
    assert b4_survives(pairs, ("to_3x3", 0, "native"), (4, "unmarked"))
    assert rejected_everywhere(B, pairs)


def test_zero_fill_competitor_on_full_motifs():
    rng = random.Random(3)
    demos = [stamp_task.generate(colors=motifs(rng, full=True), pattern=generic_map(rng)) for _ in range(3)]
    query = stamp_task.generate(colors="120030201", pattern=generic_map(rng))
    pairs = demos + [query]
    assert b4_survives(pairs, ("to_3x3", 0, "zeros_to_mark"), (0, "marked"))
    assert rejected_everywhere(B, pairs)


def test_silhouette_competitor_on_mark_coloured_motifs():
    rng = random.Random(4)
    demos = [stamp_task.generate(colors=motifs(rng, mono=2), pattern=generic_map(rng)) for _ in range(3)]
    query = stamp_task.generate(colors="120030201", pattern=generic_map(rng))
    pairs = demos + [query]
    assert b4_survives(pairs, ("to_3x3", 0, "silhouette"), (0, "marked"))
    assert rejected_everywhere(B, pairs)


@pytest.mark.parametrize("demo_scale,query_scale", [(2, 1), (1, 3), (3, 2)])
def test_fixed_factor_extraction_competitors_across_scales(demo_scale, query_scale):
    rng = random.Random(10 * demo_scale + query_scale)
    demos = [stamp_task.generate(colors="120030201", scale=demo_scale, map_height=4,
                                 pattern="".join(rng.choice("02") for _ in range(12 * demo_scale - 1)) + "2")
             for _ in range(3)]
    query = stamp_task.generate(colors="120030201", scale=query_scale, map_height=4,
                                pattern="2" * (12 * query_scale))
    pairs = demos + [query]
    assert b4_survives(pairs, (f"by_{demo_scale}", 0, "native"), (0, "marked"))
    assert rejected_everywhere(B, pairs)
    same = demos + [stamp_task.generate(colors="120030201", scale=demo_scale, map_height=4,
                                        pattern="2" * (12 * demo_scale))]
    assert decisions(B, same) == {True}


def brute_b4(demos, query, palette=list(range(10))):
    """Independent: stamp every (tile, mask) candidate in full and compare."""
    def parts(g):
        g = np.array(g)
        top, mp = ev._parse_motif_map(g, palette[5])
        return ev._tiles(top, palette[0], palette[2]), ev._masks(mp, palette[0])
    alive = None
    for d in demos:
        tiles, masks = parts(d["input"])
        want = np.array(d["output"])
        fit = {(tk, qk) for tk, t in tiles.items() if t is not None for qk, m in masks.items()
               if (s := ev._stamp(t, m, palette[0])).shape == want.shape and (s == want).all()}
        alive = fit if alive is None else alive & fit
    return alive


def test_separable_b4_matches_brute_force():
    for seed in range(25):
        random.seed(seed)
        scale = 1 + seed % 3
        pairs = [stamp_task.generate(scale=scale, map_height=1 + seed % 4) for _ in range(4)]
        assert ev.surviving_rules(B, pairs[:3]) == brute_b4(pairs[:3], pairs[3])


def test_b4_fixtures_accepted_everywhere():
    for version in ("canonical", "teaching_fixture"):
        fx = reference(B)[version]
        assert decisions(B, fx["train"] + fx["test"]) == {True}


# ------------------------------------------------------------ invariance and plumbing
@pytest.mark.parametrize("tid,module", [(K, keys_task), (B, stamp_task)])
def test_random_context_verdicts_are_d4_covariant(tid, module):
    for seed in range(40):
        random.seed(seed)
        pairs = [module.generate() for _ in range(4)]
        for palette in PALETTES:
            assert len(d4_decisions(tid, pairs, palette)) == 1


def test_b4_verdicts_are_also_palette_invariant():
    for seed in range(40):
        random.seed(seed)
        assert len(decisions(B, [stamp_task.generate() for _ in range(4)])) == 1


def test_pre_gate_witnesses_rejected_by_make_record_but_programs_verify():
    from arc_agi2.direct_factories import task_18447a8d as fk, task_b4a43f3b as fb
    witnesses = json.loads((REPORT / "pre-gate-witnesses-96be803.json").read_text())
    for tid, factory in ((K, fk), (B, fb)):
        pairs = witnesses[tid]["pairs"]
        for pal in PALETTES[:2]:
            for d4 in range(8):
                ep = episode(pairs, d4, pal)
                verify(factory.build_program(d4, pal), ep)          # program is exact
                ep.update(task_id=tid, episode_id="t", d4_transform=d4, color_permutation=pal)
                with pytest.raises(MissingColourEvidence):
                    make_record(ep)
                with pytest.raises(MissingColourEvidence):
                    require_colour_evidence(tid, ep["train"], ep["test"], pal, d4)


def test_gate_runtime_bounded_at_largest_scenes():
    random.seed(77)
    k_pairs = [keys_task.generate(num_bands=7) for _ in range(4)]
    b_pairs = [stamp_task.generate(scale=3, map_height=10) for _ in range(4)]
    for tid, pairs in ((K, k_pairs), (B, b_pairs)):
        started = time.monotonic()
        decisions(tid, pairs)
        assert time.monotonic() - started < 10
