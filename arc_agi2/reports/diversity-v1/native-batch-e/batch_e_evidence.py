"""Before/after coverage and pre-gate witness rates for native batch E.

"Before" draws run the LEGACY constructor bytes (read from git revision BASE_REV
and hash-checked); "after" draws run the current constructors with default
arguments. Every pair label is checked by runtime.verification_solver.

The witness probe draws strict same-shape contexts (three demonstrations and
a query at one input size) and counts contexts where a competing candidate
rule fits every demonstration but changes the query answer, i.e. contexts
make_record accepted before the batch E gates. The e0fb7511 component-size
threshold (size >= 3) competitor is measured too but is NOT gated (proposal
only). Every call has a 3 s deadline. Writes batch-e-evidence.json.

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-e/batch_e_evidence.py
"""
import hashlib
import importlib
import json
import random
import statistics
import subprocess
import types
from collections import Counter
from pathlib import Path

from arc_agi2.mirror_neighbourhood_evidence import (ADJACENCIES, ANCHORS, DILATIONS,
                                                    surviving_rules, variants_for)
from arc_agi2.runtime import BASE, call, grid, verification_solver

OUT = Path(__file__).resolve().parent
BASE_REV = "c201cfe"
TASKS = ("0c786b71", "e0fb7511", "f0df5ff0", "f3cdc58f")
LEGACY_SHA = {"0c786b71": "7fc6d170003af1a888887129b02bf336afb967f350691ae23e6551c102e0d8e8",
              "e0fb7511": "3857588ff73d8b3866193818d618dc323c66986853ee719a64ee247ff18c48f4",
              "f0df5ff0": "df76beda51cd578c92874de3457086aa71845949a4ca3f6b77e69dea34205dba",
              "f3cdc58f": "763478e511a8fd9bd9ec13580b1bd30bfa19642e3a8f356018efa81c7c328f94"}
WITNESS_SHAPES = {"0c786b71": [(2, 2), (3, 2), (2, 3), (3, 4)], "e0fb7511": [(6, 6), (13, 13)],
                  "f0df5ff0": [(6, 6), (15, 15)]}
WITNESS_CONTEXTS = 2000
NAMES = {"0c786b71": ANCHORS, "e0fb7511": ADJACENCIES, "f0df5ff0": DILATIONS}
NATIVE = {"0c786b71": ANCHORS.index("BR"), "e0fb7511": 0, "f0df5ff0": 0}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def legacy_module(tid):
    src = subprocess.run(["git", "show", f"{BASE_REV}:tasks/task_{tid}.py"], check=True,
                         capture_output=True, cwd=BASE.parent).stdout
    if sha(src) != LEGACY_SHA[tid]:
        raise RuntimeError(f"{tid}: legacy bytes at {BASE_REV} do not match the recorded hash")
    module = types.ModuleType(f"legacy_{tid}")
    exec(compile(src, f"legacy/task_{tid}.py", "exec"), module.__dict__)
    return module


def seeded(tid, mode, i):
    random.seed(int(sha(f"batch-e-evidence:{tid}:{mode}:{i}".encode())[:12], 16))


def draws(module, tid, mode, n):
    out = []
    for i in range(n):
        seeded(tid, "draw", i)   # same seeds before and after
        p = call(module.generate, seconds=3)
        out.append({k: grid(p[k]) for k in ("input", "output")})
    return out


def components(a, colour):
    h, w = len(a), len(a[0])
    seen, sizes = set(), []
    for y in range(h):
        for x in range(w):
            if a[y][x] != colour or (y, x) in seen:
                continue
            stack, n = [(y, x)], 0
            seen.add((y, x))
            while stack:
                cy, cx = stack.pop()
                n += 1
                for p in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= p[0] < h and 0 <= p[1] < w and p not in seen and a[p[0]][p[1]] == colour:
                        seen.add(p)
                        stack.append(p)
            sizes.append(n)
    return sizes


def diagonal_only_contact(a):
    h, w = len(a), len(a[0])
    return any(a[y][x] == 0 and a[y + 1][x + dx] == 0 and a[y][x + dx] and a[y + 1][x]
               for y in range(h - 1) for x in range(w) for dx in (-1, 1) if 0 <= x + dx < w)


def family_stats(tid, pairs):
    ins = [p["input"] for p in pairs]
    area = lambda a: len(a) * len(a[0])
    if tid == "0c786b71":
        sym = sum(a == [r[::-1] for r in a] or a == a[::-1] for a in ins)
        return {"distinct_colours_histogram": dict(sorted(Counter(
                    len({v for r in a for v in r}) for a in ins).items())),
                "mirror_symmetric_inputs": sym}
    if tid == "e0fb7511":
        dens = [sum(r.count(0) for r in a) / area(a) for a in ins]
        marked = [sum(r.count(8) for r in p["output"]) for p in pairs]
        sizes = [components(a, 0) for a in ins]
        return {"black_density": [round(min(dens), 3), round(statistics.median(dens), 3),
                                  round(max(dens), 3)],
                "azure_cells": [min(marked), max(marked)],
                "largest_black_component": [min(max(s) for s in sizes), max(max(s) for s in sizes)],
                "inputs_with_component_size_2": sum(2 in s for s in sizes),
                "inputs_with_diagonal_only_contact": sum(map(diagonal_only_contact, ins)),
                "inputs_with_singleton": sum(1 in s for s in sizes)}
    if tid == "f0df5ff0":
        seeds = [sum(r.count(1) for r in a) for a in ins]
        conf = [sum(v > 1 for r in a for v in r) / area(a) for a in ins]
        return {"seed_count_range": [min(seeds), max(seeds)], "distinct_seed_counts": len(set(seeds)),
                "confetti_density": [round(min(conf), 3), round(statistics.median(conf), 3),
                                     round(max(conf), 3)]}
    counts = [tuple(sum(r.count(c) for r in a) for c in (1, 2, 3, 4)) for a in ins]
    return {"max_bar": max(max(c) for c in counts),
            "pairs_with_a_bar_above_8": sum(max(c) > 8 for c in counts),
            "distinct_count_tuples": len(set(counts)),
            "ink_density": [round(min(sum(c) / area(a) for c, a in zip(counts, ins)), 3),
                            round(max(sum(c) / area(a) for c, a in zip(counts, ins)), 3)]}


def stats(tid, pairs):
    checker = verification_solver(tid)
    ishape = Counter((len(p["input"]), len(p["input"][0])) for p in pairs)
    oshape = {(len(p["output"]), len(p["output"][0])) for p in pairs}
    hs = [s[0] for s in ishape.elements()]
    ws = [s[1] for s in ishape.elements()]
    return {"draws": len(pairs),
            "unique_inputs": len({json.dumps(p["input"]) for p in pairs}),
            "input_shapes": len(ishape), "output_shapes": len(oshape),
            "input_h": [min(hs), max(hs)], "input_w": [min(ws), max(ws)],
            "output_h": [min(s[0] for s in oshape), max(s[0] for s in oshape)],
            "output_w": [min(s[1] for s in oshape), max(s[1] for s in oshape)],
            "shapes_with_4_or_more_pairs": sum(v >= 4 for v in ishape.values()),
            "registered_verifier_disagreements": sum(
                grid(checker(p["input"])) != p["output"] for p in pairs),
            **family_stats(tid, pairs)}


def threshold_three(a):
    """Unimplemented competitor: only 4-components of size >= 3 turn 8."""
    out = [r[:] for r in a]
    h, w = len(a), len(a[0])
    seen = set()
    for y in range(h):
        for x in range(w):
            if a[y][x] or (y, x) in seen:
                continue
            comp, stack = [], [(y, x)]
            seen.add((y, x))
            while stack:
                cy, cx = stack.pop()
                comp.append((cy, cx))
                for p in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= p[0] < h and 0 <= p[1] < w and p not in seen and a[p[0]][p[1]] == 0:
                        seen.add(p)
                        stack.append(p)
            if len(comp) >= 3:
                for cy, cx in comp:
                    out[cy][cx] = 8
    return out


def witness(tid, module):
    rows = {}
    variants = variants_for(tid, list(range(10)))
    for h, w in WITNESS_SHAPES[tid]:
        wrong, extra, first = Counter(), 0, None
        for i in range(WITNESS_CONTEXTS):
            seeded(tid, f"witness-{h}x{w}", i)
            ps = [call(module.generate, seconds=3, width=w, height=h) for _ in range(4)]
            alive = surviving_rules(tid, ps[:3])
            options = variants(ps[3]["input"])
            bad = sorted(NAMES[tid][k] for k in alive if options[k] != ps[3]["output"])
            if bad:
                wrong[",".join(bad)] += 1
                if first is None:
                    first = {"context": i, "competitors": bad}
            if tid == "e0fb7511":
                fits = all(threshold_three(p["input"]) == p["output"] for p in ps[:3])
                extra += fits and threshold_three(ps[3]["input"]) != ps[3]["output"]
        row = {"contexts": WITNESS_CONTEXTS,
               "ambiguous_contexts": sum(wrong.values()),
               "by_surviving_wrong_candidates": dict(wrong), "first": first}
        if tid == "e0fb7511":
            row["ungated_size3_threshold_ambiguous"] = extra
        rows[f"{h}x{w}"] = row
    return rows


def main():
    result = {"base_revision": BASE_REV, "witness_definition":
              "same-shape context where a competing candidate rule reproduces all three "
              "demonstrations but changes the query answer (accepted by make_record before "
              "the batch E gates)"}
    for tid in TASKS:
        current = importlib.import_module("tasks.task_" + tid)
        src = (BASE.parent / "tasks" / f"task_{tid}.py").read_bytes()
        entry = {"constructor_sha256": sha(src), "previous_constructor_sha256": LEGACY_SHA[tid],
                 "before": stats(tid, draws(legacy_module(tid), tid, "before", 1000)),
                 "after": stats(tid, draws(current, tid, "after", 1000))}
        if tid in WITNESS_SHAPES:
            entry["pre_gate_witnesses_current_constructor"] = witness(tid, current)
        result[tid] = entry
    result["source_sha256"] = {
        name: sha((BASE / rel).read_bytes()) for name, rel in (
            ("mirror_neighbourhood_evidence", "mirror_neighbourhood_evidence.py"),
            ("verified_rules", "verified_rules.py"), ("colour_evidence", "colour_evidence.py"))}
    result["source_sha256"]["harness"] = sha(Path(__file__).read_bytes())
    (OUT / "batch-e-evidence.json").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
