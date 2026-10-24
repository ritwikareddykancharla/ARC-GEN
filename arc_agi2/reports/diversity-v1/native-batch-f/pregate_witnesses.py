"""Pre-gate demonstration-ambiguity witnesses for the batch F self-tilers.

Run on the shared sources BEFORE colour_evidence dispatches these IDs (the
script refuses otherwise). Contexts are strict same-shape: three demonstrations
and a query drawn from the current default constructor at one input shape, with
FOUR DISTINCT pipeline input orbits (prepare.input_orbit), as prepare requires.
A context is a witness for a hypothesis when the named competitor rule
reproduces all three demonstration outputs exactly but gives a different answer
on the query input, while make_record (all 8 D4, seeded palette) accepts the
episode. Competitors are evaluated in visible coordinates by
self_tiler_evidence.predict with fill = palette[0].

Hypotheses (from supervisor review; measured, not assumed):
* fixed_colour: demos all select the same colour c; the query selects another.
* frequency_swap: modal <-> minority (and, for one-ink masks, ink sparse/dense).
* stamp_all: every cell selected (only possible when every demo selects all).
* monochrome_fill: 48f8583b demos that never show the fill (all monochrome).
* corner_anchor: cells equal to a corner's colour (added by batch F).

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-f/pregate_witnesses.py
"""
import hashlib
import importlib
import inspect
import json
import random
from collections import Counter
from pathlib import Path

from arc_agi2 import colour_evidence
from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import make_record
from arc_agi2.runtime import BASE, call, grid, verification_solver
from arc_agi2.self_tiler_evidence import CORNERS, predict

OUT = Path(__file__).resolve().parent
SHAPES = {"27f8ce4f": [(3, 3), (2, 4)], "48f8583b": [(3, 3), (2, 4)],
          "5b6cbef5": [(4, 4), (3, 3)]}
CONTEXTS = 1000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def competitors(tid, bg):
    named = {"stamp_all": [("all", "id", "id", bg)],
             "corner_anchor": [(f"corner:{k}", "id", "id", bg) for k in CORNERS],
             "fixed_colour": [(f"colour:{c}", "id", "id", bg) for c in range(10) if c != bg]}
    if tid == "27f8ce4f":
        named["frequency_swap"] = [("minority", "id", "id", bg)]
    elif tid == "48f8583b":
        named["frequency_swap"] = [("modal", "id", "id", bg)]
        named["monochrome_fill"] = [("minority", "id", "id", f) for f in range(10) if f != bg]
    else:
        named["frequency_swap"] = [("minority", "id", "id", bg), ("modal", "id", "id", bg)]
    return named


def fits(cand, demos):
    return all(predict(d["input"], *cand) == d["output"] for d in demos)


def draw(module, checker, h, w):
    p = call(module.generate, seconds=3, height=h, width=w)
    p = {k: grid(p[k]) for k in ("input", "output")}
    assert grid(checker(p["input"])) == p["output"]
    return p


def main():
    if "self_tiler" in inspect.getsource(colour_evidence):
        raise SystemExit("colour_evidence already dispatches the self-tiler gate; "
                         "pre-gate witnesses must be measured before wiring")
    report = {"method": "strict same-shape, four distinct prepare.input_orbit inputs, "
                        "competitor fits every demo and differs on the query; make_record "
                        "accepts on all 8 D4 with a seeded palette",
              "contexts_per_shape": CONTEXTS,
              "source_sha256": {p: sha((BASE.parent / p).read_bytes()) for p in (
                  "arc_agi2/colour_evidence.py", "arc_agi2/self_tiler_evidence.py",
                  "arc_agi2/program_targets.py", "tasks/task_27f8ce4f.py",
                  "tasks/task_48f8583b.py", "tasks/task_5b6cbef5.py",
                  "arc_agi2/direct_factories/27f8ce4f.json",
                  "arc_agi2/direct_factories/48f8583b.json",
                  "arc_agi2/direct_factories/5b6cbef5.json")},
              "families": {}}
    for tid in SHAPES:
        module = importlib.import_module("tasks.task_" + tid)
        checker = verification_solver(tid)
        named = competitors(tid, 0)
        fam = report["families"][tid] = {}
        for h, w in SHAPES[tid]:
            rates, witnesses, orbit_retries = Counter(), {}, 0
            for i in range(CONTEXTS):
                rng_seed = int(sha(f"batch-f-pregate:{tid}:{h}x{w}:{i}".encode())[:12], 16)
                random.seed(rng_seed)
                for _ in range(50):
                    pairs = [draw(module, checker, h, w) for _ in range(4)]
                    if len({input_orbit(p["input"]) for p in pairs}) == 4:
                        break
                    orbit_retries += 1
                else:
                    raise RuntimeError("no four-orbit context in 50 draws")
                demos, query = pairs[:3], pairs[3]
                for name, cands in named.items():
                    hit = next((c for c in cands if fits(c, demos)
                                and predict(query["input"], *c) != query["output"]), None)
                    if hit is None:
                        continue
                    rates[name] += 1
                    if name in witnesses:
                        continue
                    palette = list(range(10))
                    random.Random(rng_seed + 1).shuffle(palette)
                    for d4 in range(8):
                        ep = episode(pairs, d4, palette)
                        ep.update(task_id=tid, episode_id=f"pregate-{tid}-{i}-{d4}",
                                  d4_transform=d4, color_permutation=palette)
                        make_record(ep)
                    witnesses[name] = {
                        "context_seed": rng_seed, "competitor": list(hit),
                        "demonstrations": demos, "query_input": query["input"],
                        "label": query["output"],
                        "competitor_query_answer": predict(query["input"], *hit),
                        "make_record_accepted_d4": list(range(8)),
                        "palette": palette}
            fam[f"{h}x{w}"] = {"witness_rate": {k: rates[k] for k in named},
                              "orbit_redraws": orbit_retries, "witnesses": witnesses}
            print(tid, f"{h}x{w}", dict(rates), "orbit redraws", orbit_retries, flush=True)
    (OUT / "pregate-witnesses.json").write_text(json.dumps(report, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
