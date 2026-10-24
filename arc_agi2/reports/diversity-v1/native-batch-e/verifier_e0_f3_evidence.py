"""Evidence for the reviewed e0fb7511 / f3cdc58f pair checkers (native batch E).

Measured on the LEGACY constructor bytes (explicit-argument draws only reach
the expanded content) plus independently built adversarial grids. Labels are
computed here by an independent restatement of each native rule, never by the
checker under test. Writes the evidence JSON and one counterexample per ID.

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-e/verifier_e0_f3_evidence.py
"""
import hashlib
import importlib
import json
import random
from pathlib import Path

from arc_agi2.runtime import BASE, grid, reference, solver
from arc_agi2.verified_rules import fixed_colour_histogram, native_zero_adjacency

OUT = Path(__file__).resolve().parent
NEW = {"e0fb7511": native_zero_adjacency, "f3cdc58f": fixed_colour_histogram}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def e0_label(g):
    """Independent: a 0 cell turns 8 iff some orthogonal neighbour is 0."""
    h, w = len(g), len(g[0])
    zero = {(y, x) for y in range(h) for x in range(w) if g[y][x] == 0}
    return [[8 if (y, x) in zero and zero & {(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)}
             else g[y][x] for x in range(w)] for y in range(h)]


def f3_label(g):
    """Independent: column x < 4 holds colour x + 1 in its bottom count(x + 1) rows."""
    h, w = len(g), len(g[0])
    flat = [v for r in g for v in r]
    height_from_bottom = lambda y: h - 1 - y
    return [[x + 1 if x < 4 and height_from_bottom(y) < flat.count(x + 1) else 0
             for x in range(w)] for y in range(h)]


def e0_adversarial():
    rng = random.Random(7)
    cases = {
        "all_black_13x13": [[0] * 13 for _ in range(13)],
        "all_blue_13x13": [[1] * 13 for _ in range(13)],
        "checkerboard_diagonal_only_13x13": [[(y + x) % 2 for x in range(13)] for y in range(13)],
        "checkerboard_diagonal_only_30x30": [[(y + x) % 2 for x in range(30)] for y in range(30)],
        "single_singleton_13x13": [[0 if (y, x) == (6, 6) else 1 for x in range(13)] for y in range(13)],
        "corner_pair_13x13": [[0 if (y, x) in ((0, 0), (0, 1)) else 1 for x in range(13)] for y in range(13)],
        "full_black_row": [[0 if y == 4 else 1 for x in range(13)] for y in range(13)],
        "full_black_column": [[0 if x == 12 else 1 for x in range(13)] for y in range(13)],
        "blue_full_row_on_black": [[1 if y == 4 else 0 for x in range(13)] for y in range(13)],
        "tied_half_black_2x2": [[0, 1], [1, 0]],
        "tied_half_black_rows_4x4": [[0] * 4, [1] * 4, [0] * 4, [1] * 4],
        "one_by_one_black": [[0]],
        "one_by_one_blue": [[1]],
        "one_by_two_black": [[0, 0]],
        "thirty_by_one_alternating": [[y % 2] for y in range(30)],
        "one_by_thirty_black_pair_end": [[1] * 28 + [0, 0]],
    }
    for k in range(6):
        cases[f"dense_30x30_p{50 + 5 * k}"] = [[0 if rng.random() < 0.5 + 0.05 * k else 1
                                                for _ in range(30)] for _ in range(30)]
    return cases


def f3_adversarial():
    rng = random.Random(11)
    cases = {
        "ten_each_10x4": [[1, 2, 3, 4] for _ in range(10)],
        # counts 10, 9, 9, 9 of 40 cells: colour 1 is modal, 3 black cells
        "colour1_modal_10x4": [[1, 2, 3, 4] for _ in range(9)] + [[1, 0, 0, 0]],
        # 4 and black tie at 5 cells each (counts 1:4, 2:3, 3:3, 4:5)
        "tie_black_and_4_5x4": [[4, 1, 2, 3], [4, 1, 2, 3], [4, 1, 2, 3], [4, 1, 0, 0],
                                [4, 0, 0, 0]],
        "no_black_background_4x4": [[1, 2, 3, 4] for _ in range(4)],
        "one_row_1x4": [[4, 3, 2, 1]],
        "full_columns_30x30": [[(x % 4) + 1 if x < 4 else 0 for x in range(30)] for _ in range(30)],
        "full_rows_4x30": [[c] * 4 for c in (1, 2, 3, 4)] + [[0] * 4 for _ in range(26)],
        "counts_equal_height_5x6": [[1, 2, 3, 4, 0, 0] for _ in range(5)],
        "max_30x30_dense": None,
    }
    g = [[0] * 30 for _ in range(30)]
    cells = rng.sample(range(900), 4 * 30)
    for i, cell in enumerate(cells):
        g[cell // 30][cell % 30] = i // 30 + 1
    cases["max_30x30_dense"] = g
    return cases


def main():
    archived = {t: solver(t) for t in NEW}
    result = {"source_sha256": {
        "verified_rules": sha(BASE / "verified_rules.py"),
        "constructor_e0fb7511": sha(BASE.parent / "tasks/task_e0fb7511.py"),
        "constructor_f3cdc58f": sha(BASE.parent / "tasks/task_f3cdc58f.py"),
        "harness": sha(__file__)}}
    label = {"e0fb7511": e0_label, "f3cdc58f": f3_label}
    for tid, check in NEW.items():
        rep = {}
        packet = reference(tid)
        exact = 0
        total = 0
        for name in ("canonical", "teaching_fixture"):
            for p in packet[name]["train"] + packet[name]["test"]:
                total += 1
                exact += check(p["input"]) == p["output"] == label[tid](p["input"])
        rep["fixtures_exact"] = [exact, total]
        mod = importlib.import_module("tasks.task_" + tid)
        bad_old = bad_new = 0
        for i in range(1000):
            random.seed(int(hashlib.sha256(f"batch-e-verifier:{tid}:{i}".encode()).hexdigest()[:12], 16))
            p = mod.generate()
            assert label[tid](p["input"]) == p["output"]
            bad_old += grid(archived[tid](p["input"])) != p["output"]
            bad_new += check(p["input"]) != p["output"]
        rep["legacy_default_1000"] = {"archived_disagree": bad_old, "reviewed_disagree": bad_new}
        explicit = {}
        if tid == "e0fb7511":
            for dens in (0.125, 0.2, 0.3, 0.35, 0.4, 0.5, 0.6):
                old = new = n = 0
                for i in range(500):
                    rng = random.Random(f"{dens}:{i}")
                    colors = [0 if rng.random() < dens else 1 for _ in range(169)]
                    p = mod.generate(colors=colors)
                    if p["input"] is None:   # legacy explicit-colour guard (<13 eights)
                        continue
                    n += 1
                    old += grid(archived[tid](p["input"])) != p["output"]
                    new += check(p["input"]) != p["output"]
                explicit[f"density_{dens}"] = {"pairs": n, "archived_disagree": old,
                                               "reviewed_disagree": new}
        else:
            for hi in (8, 10):
                old = new = 0
                for i in range(500):
                    rng = random.Random(f"{hi}:{i}")
                    cnt = [rng.randint(1, hi) for _ in range(4)]
                    cells = rng.sample(range(100), sum(cnt))
                    colors = [0] * 100
                    for k, cell in enumerate(cells):
                        colors[cell] = next(c for c in range(1, 5) if k < sum(cnt[:c]))
                    p = mod.generate(colors=colors)
                    old += grid(archived[tid](p["input"])) != p["output"]
                    new += check(p["input"]) != p["output"]
                explicit[f"counts_1_to_{hi}_10x10"] = {"pairs": 500, "archived_disagree": old,
                                                     "reviewed_disagree": new}
        rep["legacy_explicit_colours"] = explicit
        adv = e0_adversarial() if tid == "e0fb7511" else f3_adversarial()
        rows = {}
        first = None
        for name, g in adv.items():
            want = label[tid](g)
            try:
                got = grid(archived[tid](g))
            except Exception as exc:    # archived crash counts as disagreement
                got = repr(exc)
            ok_new = check(g) == want
            rows[name] = {"shape": [len(g), len(g[0])], "archived_agrees": got == want,
                          "reviewed_agrees": ok_new}
            if got != want and first is None:
                first = {"case": name, "input": g, "expected": want, "archived": got}
        rep["adversarial"] = rows
        rep["adversarial_archived_disagree"] = sum(not r["archived_agrees"] for r in rows.values())
        rep["adversarial_reviewed_disagree"] = sum(not r["reviewed_agrees"] for r in rows.values())
        result[tid] = rep
        if tid == "e0fb7511":
            g = [[0] * 13 for _ in range(13)]
            p = mod.generate(colors=[0] * 169)
            first = {"case": "generate(colors=[0]*169) on the legacy constructor",
                     "input": p["input"], "constructor_output": p["output"],
                     "archived": grid(archived[tid](g))}
        else:
            g = adv["ten_each_10x4"]
            first = {"case": "legal 10x4 histogram, ten cells of each colour 1..4",
                     "input": g, "expected": label[tid](g), "archived": grid(archived[tid](g))}
        (OUT / f"{tid}-archived-verifier-counterexample.json").write_text(
            json.dumps(first, separators=(",", ":")) + "\n")
    (OUT / "verifier-evidence-e0fb7511-f3cdc58f.json").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
