"""Re-review probe for the 11 batch-B/C repaired constructors. Read-only, seeded.

Run from the worktree root:
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-domain-review-20261024/probes/rereview_batch_bc.py

Sections:
  bindings  - certificate constructor/factory/program/dependency hashes against
              the current files, production certificate lookup, and canonical
              replay of validate(). The extract.py check binds only the
              constructor and factory hashes; this also reports auditor,
              harness, gate and pair-verifier hashes.
  domain    - seeded statistics (seed 0) for open questions in the earlier
              reviews. Exact counts are enumerations of the default sampler
              ranges read from the source. Everything else is a sample
              statistic, not a guarantee.
  timing    - wall-clock per draw. This section varies from run to run and is
              not deterministic.

Nothing is written. No certificate, audit, factory or constructor is changed.
"""
import collections
import hashlib
import importlib
import itertools
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
import numpy as np  # noqa: E402

from arc_agi2 import runtime  # noqa: E402

ROOT = Path(".").resolve()
IDS = ["03560426", "0becf7df", "0f63c0b9", "14b8e18c", "21f83797", "2685904e",
       "2a28add5", "50c07299", "7e2bad24", "7e576d6e", "94414823"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def mod(tid):
    return importlib.import_module("tasks.task_" + tid)


def draws(tid, n, seed=0, **kw):
    random.seed(seed)
    m = mod(tid)
    return [m.generate(**kw) for _ in range(n)]


def q(values, ps=(0, 0.1, 0.5, 0.9, 1)):
    v = sorted(values)
    return [round(v[min(len(v) - 1, int(p * (len(v) - 1)))], 3) for p in ps]


def bindings():
    from arc_agi2.audit_direct_candidates import candidate
    from arc_agi2.direct_certificates import certified_factory_source, certified_source
    cur = {
        "recertify.py": sha("arc_agi2/diversity/recertify.py"),
        "verified_rules.py": sha("arc_agi2/verified_rules.py"),
        "beam_endpoint_evidence.py": sha("arc_agi2/beam_endpoint_evidence.py"),
        "certify_7e2bad24.py": sha("arc_agi2/reports/diversity-v1/native-batch-c/certify_7e2bad24.py"),
    }
    print("current dependency sha256:", json.dumps({k: v[:12] for k, v in cur.items()}))
    for tid in IDS:
        con = sha(f"tasks/task_{tid}.py")
        row = {"constructor": con[:12]}
        for kind, p in (("direct_factory", f"arc_agi2/direct_factories/{tid}.json"),
                        ("direct_certificate", f"arc_agi2/reports/direct-certificates/{tid}.json"),
                        ("native_certificate", f"arc_agi2/reports/diversity-v1/native-certificates/{tid}.json")):
            if not Path(p).exists():
                continue
            c = json.loads(Path(p).read_text())
            r = {"passed": c.get("passed"), "constructor_eq": c.get("constructor_sha256") == con,
                 "unique": c.get("unique_base_inputs"),
                 "fresh/aug/fix": [c.get("fresh_pairs_checked"), c.get("augmented_pair_checks"),
                                   c.get("fixture_variants_checked")]}
            fp = Path(f"arc_agi2/direct_factories/task_{tid}.py")
            if "factory_sha256" in c:
                r["factory_eq"] = fp.exists() and sha(fp) == c["factory_sha256"]
            if "program_sha256" in c:
                r["program_eq"] = hashlib.sha256(candidate(tid)[0].encode()).hexdigest() == c["program_sha256"]
            if "auditor_sha256" in c:
                r["auditor_eq_current_recertify"] = c["auditor_sha256"] == cur["recertify.py"]
                r["auditor"] = c["auditor_sha256"][:12]
            for key, name in (("harness_sha256", "certify_7e2bad24.py"),
                              ("evidence_gate_sha256", "beam_endpoint_evidence.py"),
                              ("pair_verifier_sha256", "verified_rules.py")):
                if key in c:
                    r[key.replace("_sha256", "_eq")] = c[key] == cur[name]
            row[kind] = r
        row["prod_factory_source"] = certified_factory_source(tid, 5, [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]) is not None
        if not Path(f"arc_agi2/direct_factories/task_{tid}.py").exists():
            row["prod_direct_source"] = certified_source(tid) is not None
        can = runtime.reference(tid)["canonical"]
        rep = mod(tid).validate()
        row["validate_replays_canonical"] = all(
            sorted(json.dumps(p, sort_keys=True) for p in rep[s])
            == sorted(json.dumps(p, sort_keys=True) for p in can[s]) for s in ("train", "test"))
        row["canonical_pairs"] = [len(can["train"]), len(can["test"])]
        row["canonical_shapes"] = sorted({f"{len(p['input'])}x{len(p['input'][0])}"
                                          for s in ("train", "test") for p in can[s]})
        print(tid, json.dumps(row, sort_keys=True))


def shapes(pairs):
    return collections.Counter((len(p["input"]), len(p["input"][0])) for p in pairs)


def shape_summary(pairs):
    s = shapes(pairs)
    return {"distinct_shapes": len(s), "h_gt_w": sum(v for (h, w), v in s.items() if h > w),
            "h_lt_w": sum(v for (h, w), v in s.items() if h < w),
            "square": sum(v for (h, w), v in s.items() if h == w),
            "h": [min(h for h, _ in s), max(h for h, _ in s)],
            "w": [min(w for _, w in s), max(w for _, w in s)],
            "max_pairs_one_shape": max(s.values())}


def f03560426():
    pairs = draws("03560426", 1000)
    boxes, maxh, blank, used, out_used = collections.Counter(), collections.Counter(), 0, [], []
    for p in pairs:
        g = np.asarray(p["input"]); o = np.asarray(p["output"]); H, W = g.shape
        starts = [c for c in range(W) if g[H - 1, c] and (c == 0 or not g[H - 1, c - 1])]
        boxes[len(starts)] += 1
        hs = [int((g[:, c] != 0).sum()) for c in starts]
        maxh[max(hs)] += 1
        blank += int(not g[:, W - 1].any())
        used.append(max(hs) / H)
        out_used.append(int(o.any(axis=1).sum()) / H)
    can = runtime.reference("03560426")["canonical"]
    canon = [round(int(np.asarray(p["input"]).any(axis=1).sum()) / len(p["input"]), 3)
             for s in ("train", "test") for p in can[s]]
    print("03560426", json.dumps({
        "canonical_input_rows_used_fraction": canon,
        **shape_summary(pairs), "box_counts": dict(sorted(boxes.items())),
        "max_box_height": dict(sorted(maxh.items())), "trailing_blank_column": blank,
        "input_rows_used_fraction_q": q(used), "output_rows_used_fraction_q": q(out_used),
        "note": "width = span or span+1 by construction (line 108)"}))


def region_density(p):
    g = np.asarray(p["input"]); H, W = g.shape
    return float((g[1:H - 1, 2:W - 2] != 0).mean())


def f0becf7df():
    pairs = draws("0becf7df", 500)
    can = runtime.reference("0becf7df")["canonical"]
    canon = [region_density(p) for s in ("train", "test") for p in can[s]]
    big = [region_density(p) for p in pairs if min(len(p["input"]), len(p["input"][0])) >= 20]
    print("0becf7df", json.dumps({
        **shape_summary(pairs), "figure_region_density_q": q([region_density(p) for p in pairs]),
        "figure_region_density_q_min_side_ge_20": q(big), "n_min_side_ge_20": len(big),
        "canonical_region_density": [round(v, 3) for v in canon]}))


def ties(rows):
    return sum((b - a) % 2 == 0 for a, b in zip(rows, rows[1:]))


def f0f63c0b9():
    pairs = draws("0f63c0b9", 1000)
    tie = []
    for p in pairs:
        g = np.asarray(p["input"])
        rows = sorted(int(r) for r in np.nonzero(g)[0])
        tie.append(ties(rows) > 0)
    rng = random.Random(1)
    blind = tied_q = 0
    for _ in range(20000):
        idx = rng.sample(range(len(pairs)), 4)
        if tie[idx[3]]:
            tied_q += 1
            blind += not any(tie[i] for i in idx[:3])
    can = runtime.reference("0f63c0b9")["canonical"]
    canon = [ties(sorted(int(r) for r in np.nonzero(np.asarray(p["input"]))[0]))
             for s in ("train", "test") for p in can[s]]
    counts = collections.Counter(int((np.asarray(p["input"]) != 0).sum()) for p in pairs)
    print("0f63c0b9", json.dumps({
        **shape_summary(pairs), "seed_counts": dict(sorted(counts.items())),
        "pairs_with_tie_gap": sum(tie),
        "episodes_tied_query": tied_q, "episodes_tied_query_no_tied_demo": blind,
        "episode_model": "4 independent native draws (3 demos + query), shape policy ignored",
        "canonical_tie_gaps_per_pair": canon}))


def f14b8e18c():
    pairs = draws("14b8e18c", 400)
    from arc_agi2.helpers import objects
    nsq, kinds, one_sq, nested = collections.Counter(), collections.Counter(), 0, 0
    for p in pairs:
        g = np.asarray(p["input"]); o = np.asarray(p["output"])
        marks = int((o == 2).sum())
        nsq[marks // 8] += 1
        one_sq += marks == 8
        for ob in objects(g, bg=7):
            y0, x0, y1, x1 = ob["box"]; h, w = y1 - y0 + 1, x1 - x0 + 1
            if ob["size"] == 1: kinds["single_cell"] += 1
            elif h == w: kinds["square_bbox"] += 1
            else: kinds["rectangle_or_bar"] += 1
            if h == w and h >= 3 and (g[y0 + 1:y1, x0 + 1:x1] != 7).any():
                nested += 1
    print("14b8e18c", json.dumps({
        **shape_summary(pairs), "marked_squares": dict(sorted(nsq.items())),
        "scenes_with_exactly_one_marked_square": one_sq,
        "component_kinds": dict(kinds), "squares_with_nested_content": nested,
        "note": "single_cell components are diagonal cells (4-connected)"}))


def f2685904e():
    pairs = draws("2685904e", 1000)
    L, last, matches = collections.Counter(), 0, collections.Counter()
    for p in pairs:
        g = np.asarray(p["input"]); H, W = g.shape
        n = int((g[0] == 8).sum())
        d = [y for y in range(H) if (g[y] == 5).all()][0]
        data = [y for y in range(d + 1, H) if g[y].any()][0]
        last += data == H - 1
        L[n] += 1
        cnt = collections.Counter(g[data].tolist())
        matches[sum(v == n for v in cnt.values())] += 1
    print("2685904e", json.dumps({
        **shape_summary(pairs), "length_max": max(L), "length_ge_6": sum(v for k, v in L.items() if k >= 6),
        "data_row_is_last_row": last, "matching_colours_per_scene": dict(sorted(matches.items()))}))


def f2a28add5():
    pairs = draws("2a28add5", 1000)
    checker = runtime.verification_solver("2a28add5")
    lone, rows6, dens, lone_pairs, lone_agree = 0, 0, [], 0, 0
    for p in pairs:
        g = np.asarray(p["input"])
        dens.append(float(((g != 7) & (g != 6)).mean()))
        here = 0
        for row in g:
            if (row == 6).any():
                rows6 += 1
                here += int(((row != 7) & (row != 6)).sum() == 0)
        lone += here
        if here:
            lone_pairs += 1
            lone_agree += runtime.grid(runtime.call(checker, p["input"])) == p["output"]
    can = runtime.reference("2a28add5")["canonical"]
    cd = [round(float(((np.asarray(p["input"]) != 7) & (np.asarray(p["input"]) != 6)).mean()), 3)
          for s in ("train", "test") for p in can[s]]
    print("2a28add5", json.dumps({
        **shape_summary(pairs), "magenta_rows": rows6, "magenta_rows_without_other_ink": lone,
        "pairs_with_such_rows": lone_pairs, "archived_verifier_agrees_on_them": lone_agree,
        "noise_density_q": q(dens), "canonical_noise_density": cd}))


def f50c07299():
    # Exact count of the default sampler's support (lines 34-40): every
    # (height, width) in 5..30, length 1..(c-1)//2 and row 0..c-1-2L where
    # c = min(height, width). Distinct parameters give distinct inputs.
    total = sum(sum(c - 2 * L for L in range(1, (c - 1) // 2 + 1))
                for H in range(5, 31) for W in range(5, 31) for c in [min(H, W)])
    pairs = draws("50c07299", 1000)
    lengths = collections.Counter(int((np.asarray(p["input"]) == 2).sum()) for p in pairs)
    print("50c07299", json.dumps({
        **shape_summary(pairs), "exact_default_inputs": total, "old_default_inputs": 56,
        "segment_length_max": max(lengths), "length_le_3": sum(v for k, v in lengths.items() if k <= 3)}))


def axis_7e2bad24(g):
    g = np.asarray(g)
    walls = (g == 2) | (g == 3)
    horiz = (walls[:, 1:] & walls[:, :-1]).any()
    vert = (walls[1:, :] & walls[:-1, :]).any()
    return "h" if horiz and not vert else "v" if vert and not horiz else "both"


def f7e2bad24():
    from arc_agi2.beam_endpoint_evidence import beam_predictions
    pairs = draws("7e2bad24", 300)
    axes = collections.Counter(axis_7e2bad24(p["input"]) for p in pairs)
    sensitive = 0
    for p in pairs:
        preds = beam_predictions(p["input"], list(range(10)))
        sensitive += len({json.dumps(x) for x in preds}) > 1
    print("7e2bad24", json.dumps({**shape_summary(pairs), "wall_axes": dict(axes),
                                  "endpoint_sensitive_pairs": sensitive}))


def f7e576d6e():
    # Replays the layout draw of lines 73-83 and asks the constructor (explicit
    # arguments, same draw()) whether the alternation filter rejects it.
    m = mod("7e576d6e")
    rng = random.Random(0)
    tried = rejected = 0
    for _ in range(3000):
        colors = rng.sample(range(1, 10), 4)
        sc, er, ec = rng.randint(4, 25), rng.randint(25, 28), rng.randint(4, 25)
        row, rows = 0, []
        while True:
            row += rng.randint(3, 8)
            if row + 7 >= 30: break
            rows.append(row)
        if len(rows) not in (3, 4): continue
        cols = rng.sample(range(4, 25), len(rows))
        if sc in cols or ec in cols: continue
        tried += 1
        out = m.generate(start_row=1, start_col=sc, end_row=er, end_col=ec, rows=rows,
                         cols=cols, colors=colors, xpose=False)
        rejected += out["input"] is None
    pairs = draws("7e576d6e", 500)
    axes = collections.Counter("v" if any(len(set(np.asarray(p["input"])[:, c].tolist())) == 1
                                          for c in range(30)) else "h" for p in pairs)
    print("7e576d6e", json.dumps({"layouts_reaching_draw": tried,
                                  "rejected_by_alternation_only": rejected,
                                  "line_axes": dict(axes), **shape_summary(pairs)}))


def f94414823():
    # Exact count of geometries reachable by the default sampler (lines 47-54):
    # height 5..30, width 6..30, even size 4..min(h-1, w-2), brow 1..h-size,
    # bcol 1..w-size-1. Each geometry carries 8*7 ordered marker colours and
    # 4 flip/transpose settings, which give distinct inputs.
    geo = 0
    for H in range(5, 31):
        for W in range(6, 31):
            for s in range(4, min(H - 1, W - 2) + 1, 2):
                geo += (H - s) * (W - s - 1)
    pairs = draws("94414823", 1000)
    sides = collections.Counter()
    for p in pairs:
        g = np.asarray(p["input"])
        ys, xs = np.nonzero(g == 5)
        sides[int(max(ys.max() - ys.min(), xs.max() - xs.min()) + 1)] += 1
    print("94414823", json.dumps({
        **shape_summary(pairs), "exact_geometries": geo, "exact_default_inputs": geo * 56 * 4,
        "old_default_inputs": 224, "square_sides": dict(sorted(sides.items()))}))


def timing():
    out = {}
    for tid in IDS:
        m = mod(tid)
        random.seed(0)
        ts = []
        for _ in range(100):
            t = time.perf_counter(); m.generate(); ts.append(time.perf_counter() - t)
        out[tid] = {"median_ms": round(1000 * sorted(ts)[50], 2), "max_ms": round(1000 * max(ts), 1)}
    print("timing (not deterministic):", json.dumps(out))


if __name__ == "__main__":
    print("== bindings")
    bindings()
    print("== domain (seed 0)")
    for f in (f03560426, f0becf7df, f0f63c0b9, f14b8e18c, f2685904e, f2a28add5,
              f50c07299, f7e2bad24, f7e576d6e, f94414823):
        f()
    print("== timing")
    timing()
