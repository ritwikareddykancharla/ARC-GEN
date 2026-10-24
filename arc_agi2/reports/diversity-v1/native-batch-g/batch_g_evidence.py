"""Native batch G evidence: domains, finite competing hypotheses, witnesses.

Read-only measurement (writes only batch-g-evidence.json beside this file).
Seeded; two runs give byte-identical output.

For 8ba14f53 and 4cd1b7b2 it records:
* domain statistics of the legacy (base e72190b, sha pinned) and current
  default samplers, and archived-checker agreement on every draw;
* ungated ambiguity of independent contexts (3 demonstrations, 1 query).
  These counts use the batch-G gate's named rule set, at d4 = 0 with the
  identity palette. Two context kinds are measured: recertify-style
  independent draws, and (8ba14f53 current) same-shape draws matching the
  query's canvas, as prepare's uniform/seen policy does. For each
  competitor it counts the contexts in which that rule fits every
  demonstration but answers the query differently from the native rule. The
  legacy rows show that the gap predates the domain expansion;
* for 4cd1b7b2, the 2x2-box (Sudoku) rule. Its survivors either reproduce
  the native answer or have no completion on the query input, and never
  produce a different grid;
* one concrete witness context per competitor (4cd1b7b2) or per single
  deviating factor (8ba14f53; combined deviations are counted, not stored):
  the first seeded context in which it survives and disagrees. The tests
  replay these witnesses.

Usage (worktree root): PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-g/batch_g_evidence.py
"""
import collections
import hashlib
import itertools
import json
import random
import subprocess
import sys
import types
from pathlib import Path

from arc_agi2 import hole_tally_8ba14f53_evidence as tally
from arc_agi2 import latin_fill_4cd1b7b2_evidence as latin
from arc_agi2.runtime import BASE, grid, verification_solver

BASE_COMMIT = "e72190b"
LEGACY_SHA = {"8ba14f53": "4f1cca95b331ef528f60627fc1cbe6be1307a4f02cee7fb678976c8660e9ca7b",
              "4cd1b7b2": "30bf33e553a02c15ef38065146c5f8688946a435e58b63760246d5cdad5a6c2c"}
CONTEXTS = 2000
DOMAIN_DRAWS = 2000
OUT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def legacy(tid):
    src = subprocess.run(["git", "show", f"{BASE_COMMIT}:tasks/task_{tid}.py"],
                         capture_output=True, check=True, cwd=BASE.parent).stdout
    if sha(src) != LEGACY_SHA[tid]:
        raise RuntimeError("legacy constructor bytes changed")
    module = types.ModuleType(f"legacy_{tid}")
    exec(compile(src, f"legacy/task_{tid}.py", "exec"), module.__dict__)
    return module


def current(tid):
    import importlib
    return importlib.import_module(f"tasks.task_{tid}")


def draw(module, checker, **kw):
    p = module.generate(**kw)
    p = {k: grid(p[k]) for k in ("input", "output")}
    if grid(checker(p["input"])) != p["output"]:
        raise RuntimeError("archived checker disagrees with constructor label")
    return p


def as_list(g):
    return None if g is None else [list(r) for r in g]


# ---------------------------------------------------------------- domains
def domain_stats(tid, module, seed):
    checker = verification_solver(tid)
    random.seed(seed)
    shapes, inputs, hist = set(), set(), collections.Counter()
    extra = collections.Counter()
    for _ in range(DOMAIN_DRAWS):
        p = draw(module, checker)
        g = p["input"]
        shapes.add((len(g), len(g[0])))
        inputs.add(json.dumps(g))
        if tid == "4cd1b7b2":
            hist[sum(v == 0 for r in g for v in r)] += 1
        else:
            measures, extent = tally.analyse(g, 0)
            hist[tuple(measures["cells"][c] for c in
                       sorted(extent, key=lambda c: extent[c][2]))] += 1
            extra["notched_boxes"] += sum(measures["cells"][c] != measures["bbox"][c]
                                          for c in measures["cells"])
            (l, r) = sorted(extent, key=lambda c: extent[c][2])
            extra["right_box_strictly_higher"] += extent[r][0] < extent[l][0]
            extra["left_box_fewer_holes"] += measures["cells"][l] < measures["cells"][r]
            gap = extent[r][2] - extent[l][3] - 1
            extra["gap_" + (str(gap) if gap < 2 else "2+")] += 1
            extra["box_rows_overlap"] += not (extent[l][1] < extent[r][0]
                                              or extent[r][1] < extent[l][0])
    stats = {"draws": DOMAIN_DRAWS, "archived_checker_agreement": DOMAIN_DRAWS,
             "distinct_inputs": len(inputs), "input_shapes": len(shapes),
             "height_range": [min(s[0] for s in shapes), max(s[0] for s in shapes)],
             "width_range": [min(s[1] for s in shapes), max(s[1] for s in shapes)]}
    if tid == "4cd1b7b2":
        stats["blank_count_histogram"] = {str(k): v for k, v in sorted(hist.items())}
    else:
        stats["hole_count_pairs_left_first"] = len(hist)
        stats["hole_total_histogram"] = {str(k): v for k, v in sorted(
            collections.Counter(sum(k) for k in hist.elements()).items())}
        stats.update(sorted(extra.items()))
    return stats


# ------------------------------------------------- competing hypotheses
def name(tid, i):
    if tid == "4cd1b7b2":
        return latin.RULES[i]
    return "/".join(map(str, tally.RULES[i]))


def factor(tid, i):
    """Coarse factor of a competitor (8ba14f53) or the rule name itself."""
    if tid == "4cd1b7b2":
        return latin.RULES[i]
    order, slot, layout, measure = tally.RULES[i]
    parts = []
    if not order.startswith("edge-L"):
        parts.append("order:" + "-".join(order.split("-")[:2]))
    if slot:
        parts.append("slot-order")
    if layout != "new-row":
        parts.append("continuous")
    if measure != "cells":
        parts.append("bbox-measure")
    return "+".join(parts) or "native-equivalent"


def native_index(tid):
    return (latin.RULES.index(latin.NATIVE_RULE) if tid == "4cd1b7b2"
            else tally.RULES.index(tally.NATIVE_RULE))


def predictions(tid, g):
    if tid == "4cd1b7b2":
        return latin.variants(g, 0, {1, 2, 3, 4})
    return tally.variants(g, 0)


def survivors(tid, demos):
    return (latin.surviving_rules(demos) if tid == "4cd1b7b2"
            else tally.surviving_rules(demos))


LATIN_SQUARES = [rows for rows in itertools.product(itertools.permutations((1, 2, 3, 4)), repeat=4)
                 if all(len({r[c] for r in rows}) == 4 for c in range(4))]


def box_valid(sq):
    return all(len({sq[r + i][c + j] for i in (0, 1) for j in (0, 1)}) == 4
               for r in (0, 2) for c in (0, 2))


def box_completions(g):
    return [sq for sq in LATIN_SQUARES if box_valid(sq)
            and all(g[r][c] in (0, sq[r][c]) for r in range(4) for c in range(4))]


def ambiguity(tid, module, seed, same_shape):
    checker = verification_solver(tid)
    native = native_index(tid)
    random.seed(seed)
    ambiguous, by_rule, by_factor, witnesses = 0, collections.Counter(), collections.Counter(), {}
    sudoku = collections.Counter()
    for n in range(CONTEXTS):
        query = draw(module, checker)
        kw = ({"height": len(query["input"]), "width": len(query["input"][0])}
              if same_shape else {})
        demos = [draw(module, checker, **kw) for _ in range(3)]
        alive = survivors(tid, demos)
        if native not in alive:
            raise RuntimeError("native rule does not fit native demonstrations")
        opts = predictions(tid, query["input"])
        if as_list(opts[native]) != query["output"]:
            raise RuntimeError("native rule disagrees with the label")
        wrong = sorted(i for i in alive if opts[i] != opts[native])
        ambiguous += bool(wrong)
        by_rule.update(name(tid, i) for i in wrong)
        by_factor.update({factor(tid, i) for i in wrong})
        for i in wrong:
            key = factor(tid, i)
            if "+" not in key and key not in witnesses:   # single-factor deviations
                witnesses[key] = {"context": n, "rule": name(tid, i),
                                  "demonstrations": demos, "query_input": query["input"],
                                  "native_answer": query["output"],
                                  "competitor_answer": as_list(opts[i])}
        if tid == "4cd1b7b2":
            if all(box_valid(d["output"]) for d in demos):
                sols = box_completions(query["input"])
                kind = ("same" if sols == [tuple(map(tuple, query["output"]))]
                        else "none" if not sols else "different")
                sudoku[kind] += 1
                if kind == "none" and "sudoku_no_completion" not in witnesses:
                    witnesses["sudoku_no_completion"] = {
                        "context": n, "rule": "latin+2x2-box",
                        "demonstrations": demos, "query_input": query["input"],
                        "native_answer": query["output"], "competitor_answer": None}
    report = {"contexts": CONTEXTS, "context_kind": "same_shape" if same_shape else "independent",
              "palette": "identity", "d4": 0,
              "ambiguous_contexts": ambiguous,
              "by_factor_contexts": dict(sorted(by_factor.items())),
              "top_competing_rules": dict(by_rule.most_common(12))}
    if tid == "4cd1b7b2":
        report["sudoku_rule_when_all_demo_outputs_box_valid"] = dict(sorted(sudoku.items()))
    return report, witnesses


def main():
    files = {"constructor_8ba14f53": BASE.parent / "tasks/task_8ba14f53.py",
             "constructor_4cd1b7b2": BASE.parent / "tasks/task_4cd1b7b2.py",
             "hole_tally_8ba14f53_evidence": BASE / "hole_tally_8ba14f53_evidence.py",
             "latin_fill_4cd1b7b2_evidence": BASE / "latin_fill_4cd1b7b2_evidence.py",
             "colour_evidence": BASE / "colour_evidence.py",
             "verified_rules": BASE / "verified_rules.py",
             "factory_8ba14f53": BASE / "direct_factories/task_8ba14f53.py",
             "factory_4cd1b7b2": BASE / "direct_factories/task_4cd1b7b2.py",
             "harness": Path(__file__)}
    out = {"base_commit": BASE_COMMIT, "legacy_constructor_sha256": LEGACY_SHA,
           "source_sha256": {k: sha(p.read_bytes()) for k, p in files.items()},
           "rule_counts": {"8ba14f53": len(tally.RULES), "4cd1b7b2": len(latin.RULES)},
           "families": {}}
    for k, tid in enumerate(("8ba14f53", "4cd1b7b2")):
        fam = {"domain": {}, "ambiguity": {}, "witnesses": {}}
        for j, (label, module) in enumerate((("legacy", legacy(tid)), ("current", current(tid)))):
            fam["domain"][label] = domain_stats(tid, module, 1000 + 10 * k + j)
            kinds = [False] + ([True] if (tid == "8ba14f53" and label == "current") else [])
            for same in kinds:
                rep, wit = ambiguity(tid, module, 2000 + 10 * k + j + 5 * same, same)
                fam["ambiguity"][label + ("@same_shape" if same else "")] = rep
                for key, w in wit.items():
                    fam["witnesses"].setdefault(key, dict(w, domain=label))
        out["families"][tid] = fam
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"
    if "--no-write" not in sys.argv:
        (OUT / "batch-g-evidence.json").write_text(text)
    for tid, fam in out["families"].items():
        print(tid, json.dumps(fam["domain"]))
        print(tid, json.dumps(fam["ambiguity"]))
        print(tid, "witnesses:", sorted(fam["witnesses"]))


if __name__ == "__main__":
    main()
