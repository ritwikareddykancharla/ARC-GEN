"""Evidence for the reviewed b4a43f3b pair checker (verified_rules.separated_motif_stamp).

* canonical and teaching fixtures exact;
* old 1000 / new 1000: default draws of the base-96be803 constructor and of the
  working-tree constructor, checked against the constructor labels (the
  reviewed checker must agree on all; archived disagreements are counted);
* adversarial explicit scenes (scale-1 full single-colour motif rows, legacy
  colour-5 motif rows, all-0 motif, empty / full maps, extreme heights);
* the direct factory on all 8 D4 under two palettes for every adversarial scene
  inside the factory's palette[5]-unique domain;
* the archived-checker counterexample, written to
  b4a43f3b-archived-verifier-counterexample.json.

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-i/verifier_b4_evidence.py
"""
import hashlib
import importlib
import json
import random
from pathlib import Path

import numpy as np

from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import verify
from arc_agi2.runtime import BASE, grid, reference, solver
from arc_agi2.verified_rules import separated_motif_stamp as reviewed

from legacy_equivalence import old_module  # same directory

TID = "b4a43f3b"
OUT = Path(__file__).resolve().parent
PALETTES = (list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5])


def sha(b):
    return hashlib.sha256(b).hexdigest()


def archived_result(archived, g):
    try:
        out = np.array(archived(g))
        return grid(out.tolist()), list(out.shape), None
    except Exception as exc:
        try:
            shape = list(np.array(archived(g)).shape)
        except Exception:
            shape = None
        return None, shape, repr(exc)


def draws(module, tag, n=1000):
    out = []
    for i in range(n):
        random.seed(int(sha(f"b4-verifier:{tag}:{i}".encode())[:12], 16))
        p = module.generate()
        out.append({k: grid(p[k]) for k in ("input", "output")})
    return out


ADVERSARIAL = [
    # scale-1 full single-colour motif rows (archived picks them as separator)
    dict(colors="111202030", pattern="020222020000", scale=1),
    dict(colors="020333010", pattern="222", scale=1),
    dict(colors="606060222", pattern="200020002", scale=1),
    dict(colors="111111111", pattern="2" * 30, scale=1),
    dict(colors="123000333", pattern="020", scale=1),
    # legacy explicit 13x6 with colour-5 motif rows / columns, all-0 motif, empty map
    dict(colors="555010101", pattern="000000002000022220002000000000000000"),
    dict(colors="101555010", pattern="202000002000222222002000002000002000"),
    dict(colors="000000000", pattern="000000220000220000002000000200000000"),
    dict(colors="136010221", pattern="0" * 36),
    dict(colors="101020320", pattern="999000" * 6),
    # extremes of the new domain
    dict(colors="222222222", pattern="2" * 9, scale=3, map_height=1),
    dict(colors="101010101", pattern=("2" + "0" * 8) * 10, scale=3),
    dict(colors="333030333", pattern="2" * 60, scale=2),
    dict(colors="010101010", pattern="000" * 9 + "002", scale=1),
]


def main():
    archived = solver(TID)
    report = {"task_id": TID, "checker": "arc_agi2.verified_rules.separated_motif_stamp",
              "source_sha256": {
                  "verified_rules": sha((BASE / "verified_rules.py").read_bytes()),
                  "constructor": sha((BASE.parent / "tasks" / f"task_{TID}.py").read_bytes()),
                  "factory": sha((BASE / "direct_factories" / f"task_{TID}.py").read_bytes()),
                  "harness": sha(Path(__file__).read_bytes())}}
    ref = reference(TID)
    fixtures = [p for v in ("canonical", "teaching_fixture") for s in ("train", "test")
                for p in ref[v][s]]
    report["fixtures"] = {"pairs": len(fixtures),
                          "reviewed_exact": sum(reviewed(p["input"]) == p["output"] for p in fixtures),
                          "archived_exact": sum(archived_result(archived, p["input"])[0] == p["output"]
                                                for p in fixtures)}
    old, old_sha = old_module(TID)
    new = importlib.import_module("tasks.task_" + TID)
    for tag, module in (("old_1000", old), ("new_1000", new)):
        pairs = draws(module, tag)
        bad_archived = [i for i, p in enumerate(pairs)
                        if archived_result(archived, p["input"])[0] != p["output"]]
        report[tag] = {"draws": len(pairs),
                       "reviewed_agree": sum(reviewed(p["input"]) == p["output"] for p in pairs),
                       "archived_agree": len(pairs) - len(bad_archived),
                       "archived_disagreement_draws": bad_archived[:20],
                       "unique_inputs": len({json.dumps(p["input"]) for p in pairs})}
    report["old_1000"]["constructor_sha256"] = old_sha
    factory = importlib.import_module("arc_agi2.direct_factories.task_" + TID)
    cases = []
    for kw in ADVERSARIAL:
        p = new.generate(**kw)
        a_out, a_shape, a_err = archived_result(archived, p["input"])
        in_factory_domain = sum(v == 5 for r in p["input"] for v in r) == len(p["input"][0])
        factory_checks = 0
        if in_factory_domain:
            for pal in PALETTES:
                for d4 in range(8):
                    verify(factory.build_program(d4, pal), episode([p, p], d4, pal))
                    factory_checks += 1
        cases.append({"kwargs": kw, "reviewed_exact": reviewed(p["input"]) == p["output"],
                      "archived_exact": a_out == p["output"], "archived_shape": a_shape,
                      "archived_error": a_err, "factory_domain": in_factory_domain,
                      "factory_8d4_checks": factory_checks})
    report["adversarial"] = {"cases": len(cases),
                             "reviewed_exact": sum(c["reviewed_exact"] for c in cases),
                             "archived_exact": sum(c["archived_exact"] for c in cases),
                             "details": cases}
    kw = ADVERSARIAL[0]
    p = new.generate(**kw)
    a_out, a_shape, a_err = archived_result(archived, p["input"])
    counter = {"task_id": TID, "generate_kwargs": kw, "input": p["input"],
               "constructor_output": p["output"], "archived_solver_result": a_out,
               "archived_solver_shape": a_shape, "archived_solver_error": a_err,
               "reviewed_result": reviewed(p["input"]),
               "explanation": "Legal native scale-1 scene. The motif 111/202/030 has every row and column "
                              "occupied and is 8-connected. Its row 0 is a full line of colour 1, and 1 "
                              "occurs only there (3 = W times), so the archived first-unique-uniform-row "
                              "heuristic takes row 0 as the separator and returns a 0x9 grid. The reviewed "
                              "checker reads the separator at row W (colour 5) by geometry."}
    (OUT / f"{TID}-archived-verifier-counterexample.json").write_text(json.dumps(counter) + "\n")
    report["passed"] = (report["fixtures"]["reviewed_exact"] == len(fixtures)
                        and report["old_1000"]["reviewed_agree"] == 1000
                        and report["new_1000"]["reviewed_agree"] == 1000
                        and report["adversarial"]["reviewed_exact"] == len(cases)
                        and a_out != p["output"])
    (OUT / f"verifier-evidence-{TID}.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "adversarial"}, indent=1))
    print({k: v for k, v in report["adversarial"].items() if k != "details"})


if __name__ == "__main__":
    main()
