"""Pre-gate demonstration-ambiguity witnesses for 18447a8d and b4a43f3b.

Each witness is three demonstrations plus a query, all built through the
constructors' explicit legacy argument paths (original labels). It records:

* that actual ``program_targets.make_record`` accepts the episode under all
  eight D4 transforms with the identity and a seeded palette;
* that a named competing rule reproduces every demonstration output but
  predicts a different query output than the constructor label;
* that the four inputs are distinct D4 x palette orbits.

Run with ``--archive NAME`` to write ``NAME`` (used once, on the pre-gate
sources). Without arguments it prints the result for the current sources.

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-i/witnesses.py
"""
import hashlib
import importlib
import json
import sys
from pathlib import Path

from arc_agi2.augmentation import transformed
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import make_record
from arc_agi2.runtime import BASE, grid, verification_solver

OUT = Path(__file__).resolve().parent
PALETTE = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def orbit_key(g):
    """Canonical D4 x palette orbit key of an input grid."""
    keys = []
    for d4 in range(8):
        t = transformed(g, d4, list(range(10)))
        order = {}
        relabel = [[order.setdefault(v, len(order)) for v in row] for row in t]
        keys.append(json.dumps(relabel))
    return min(keys)


# ----------------------------------------------------------------- 18447a8d
def same_band_key_move(g):
    """Competitor: every key slides left to abut the lock of its OWN band."""
    out = [row[:] for row in g]
    for row in out:
        locks = sum(1 for v in row if v == 8)
        keys = [v for v in row if v not in (7, 8)]
        for c in range(len(row)):
            if c >= locks:
                row[c] = 7
        for i, v in enumerate(keys):
            row[locks + i] = v
    return out


def witness_18447a8d():
    m = importlib.import_module("tasks.task_18447a8d")
    profiles = [[[1, 2, 3], [2, 3, 4]], [[1, 1, 2], [3, 4, 1]], [[4, 2, 1], [2, 1, 3]],
                [[1, 3, 1], [4, 1, 2]]]
    pairs = []
    for i, bands in enumerate(profiles):
        order = bands if i < 3 else bands[::-1]          # query: keys swapped
        lefts = [v for b in bands for v in b]
        rights = [5 - v for b in order for v in b]
        pairs.append(m.generate(lefts=lefts, rights=rights, colors=[1, 2]))
    return pairs, "same_band_key_move", same_band_key_move


# ----------------------------------------------------------------- b4a43f3b
def flipped_motif_stamp(g):
    """Competitor: stamp the left-right mirrored motif instead of the motif."""
    motif = [row[::-1] for row in [g[r][::2] for r in range(0, 6, 2)]]
    pat = g[7:]
    out = [[0] * 18 for _ in range(18)]
    for i in range(6):
        for j in range(6):
            if pat[i][j]:
                for r in range(3):
                    for c in range(3):
                        out[3 * i + r][3 * j + c] = motif[r][c]
    return out


def witness_b4a43f3b():
    m = importlib.import_module("tasks.task_b4a43f3b")
    fixture = m.validate()
    import re
    src = Path(m.__file__).read_text()
    patterns = re.findall(r'pattern="([0-9]{36})"', src)
    maps = patterns[:3] + [patterns[4]]                  # train 0..2 and test
    colours = ["101222101", "202030202", "121333121", "120030201"]
    assert len(fixture["train"]) == 4
    pairs = [m.generate(colors=c, pattern=p) for c, p in zip(colours, maps)]
    return pairs, "flipped_motif_stamp", flipped_motif_stamp


def run(tid, build):
    pairs, name, competitor = build()
    pairs = [{k: grid(p[k]) for k in ("input", "output")} for p in pairs]
    checker = verification_solver(tid)
    labels_ok = all(grid(checker(p["input"])) == p["output"] for p in pairs)
    demo_fit = all(grid(competitor(p["input"])) == p["output"] for p in pairs[:3])
    query_differs = grid(competitor(pairs[3]["input"])) != pairs[3]["output"]
    accepted, rejected = 0, []
    for palette in (list(range(10)), PALETTE):
        for d4 in range(8):
            ep = episode(pairs, d4, palette)
            ep.update(task_id=tid, episode_id=f"witness-{tid}-{d4}", d4_transform=d4,
                      color_permutation=palette)
            try:
                make_record(ep)
                accepted += 1
            except MissingColourEvidence as exc:
                rejected.append({"d4": d4, "palette": palette, "reason": str(exc)})
    files = {"constructor": BASE.parent / "tasks" / f"task_{tid}.py",
             "factory": BASE / "direct_factories" / f"task_{tid}.py",
             "colour_evidence": BASE / "colour_evidence.py",
             "program_targets": BASE / "program_targets.py",
             "verified_rules": BASE / "verified_rules.py"}
    gate = BASE / "native_i_evidence.py"
    if gate.exists():
        files["native_i_evidence"] = gate
    return {"task_id": tid, "competitor": name,
            "competitor_fits_all_demos": demo_fit,
            "competitor_differs_on_query": query_differs,
            "labels_match_registered_checker": labels_ok,
            "distinct_input_orbits": len({orbit_key(p["input"]) for p in pairs}),
            "make_record_accepted": accepted, "make_record_rejected": rejected,
            "variants": 16, "pairs": pairs,
            "source_sha256": {k: sha(p.read_bytes()) for k, p in files.items()}}


if __name__ == "__main__":
    results = {"18447a8d": run("18447a8d", witness_18447a8d),
               "b4a43f3b": run("b4a43f3b", witness_b4a43f3b)}
    for r in results.values():
        print(json.dumps({k: v for k, v in r.items() if k != "pairs"}))
    if "--archive" in sys.argv:
        name = sys.argv[sys.argv.index("--archive") + 1]
        (OUT / name).write_text(json.dumps(results, indent=1) + "\n")
