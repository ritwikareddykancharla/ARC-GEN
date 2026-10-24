"""Gate-aware fixed-query context audits for 7491f3cf and 98c475bf.

Supplements (does not replace) the certificates. QUERIES queries per domain
are drawn once under fixed seeds and never replaced or dropped; only the
three demonstrations are resampled, at the query's own shape (prepare's
uniform/seen policy for both families), at most MAX_CONTEXTS times.

7491f3cf has no demonstration-evidence gate: require_colour_evidence falls
through for it. Each context is therefore accepted unless its four inputs are
not distinct D4/palette orbits, and the production path
program_targets.make_record (evidence dispatch, certified factory program,
exact verification of every demonstration and the query) must then succeed
under all eight D4 transforms with a seeded palette. A make_record failure
fails the audit; it never selects another context. Every pair label is
checked by the archived verifier.

98c475bf domains reuse certify_98c475bf.audit_domain (the certificate's own
gate-selected, label-blind context search plus soundness checks); the default
domain is covered by the 1000-query certificate and is not repeated here.

The standard-harness diagnostic replays arc_agi2.diversity.recertify's own
seeds (four independent default pairs per episode) for the legacy and the
current constructor and classifies each episode: mixed canvas widths, same
width but an undemonstrated query marker colour, or gate-accepted. This shows
why the standard harness cannot certify 98c475bf before or after the change.

Run from the worktree root:
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-routing-motif-20261025/context_audit.py
"""
import hashlib
import importlib
import json
import random
import subprocess
import sys
import time
import types
from collections import Counter
from pathlib import Path

from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.program_targets import make_record
from arc_agi2.runtime import BASE, call, grid, verification_solver

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import certify_98c475bf as cert98  # noqa: E402

QUERIES = 250
MAX_CONTEXTS = 64
STANDARD_SEEDS = 300
LEGACY_COMMIT = "99def42"
DOMAINS_7491 = {
    "default": {},
    "legacy_square_5x5": {"panel_size": 5},
    "small_3x4": {"panel_height": 3, "panel_width": 4},
    "small_4x3": {"panel_height": 4, "panel_width": 3},
    "tall_28x6": {"panel_height": 28, "panel_width": 6},
}
DOMAINS_98 = {
    "min_canvas_12x18": {"height": 12, "width": 18},
    "legacy_canvas_20x20": {"height": 20, "width": 20},
    "max_width_30": {"width": 30},
}
PINNED = {
    "context_audit": HERE / "context_audit.py",
    "certify_98c475bf": HERE / "certify_98c475bf.py",
    "constructor_7491f3cf": BASE.parent / "tasks" / "task_7491f3cf.py",
    "constructor_98c475bf": BASE.parent / "tasks" / "task_98c475bf.py",
    "factory_7491f3cf": BASE / "direct_factories" / "task_7491f3cf.py",
    "factory_98c475bf": BASE / "direct_factories" / "task_98c475bf.py",
    "record_7491f3cf": BASE / "direct_factories" / "7491f3cf.json",
    "record_98c475bf": BASE / "direct_factories" / "98c475bf.json",
    "colour_evidence": BASE / "colour_evidence.py",
    "line_motif_evidence": BASE / "line_motif_evidence.py",
    "program_targets": BASE / "program_targets.py",
    "verified_rules": BASE / "verified_rules.py",
    "reference_7491f3cf": BASE / "references" / "7491f3cf.json",
    "reference_98c475bf": BASE / "references" / "98c475bf.json",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def seed_of(*parts):
    return int(sha(":".join(map(str, ("routing-motif-context",) + parts)).encode())[:12], 16)


def audit_7491(domain, query_kw):
    tid = "7491f3cf"
    module = importlib.import_module("tasks.task_" + tid)
    checker = verification_solver(tid)
    out = {"query_kwargs": query_kw, "queries_requested": QUERIES, "queries_accepted": 0,
           "queries_failed": [], "evidence_gate": "none (require_colour_evidence falls through)",
           "rejected_context_draws": Counter(), "context_retries": 0,
           "make_record_calls": 0, "augmented_pair_checks": 0, "pair_labels_verified": 0,
           "query_shapes": Counter(), "sampler_rejections": 0}
    raw, episodes = set(), set()

    def draw(**kw):
        p = call(module.generate, seconds=3, **kw)
        p = {k: grid(p[k]) for k in ("input", "output")}
        if grid(call(checker, p["input"])) != p["output"]:
            raise AssertionError("Archived verifier disagrees with constructor label")
        out["pair_labels_verified"] += 1
        return p

    for q in range(QUERIES):
        random.seed(seed_of(tid, domain, "query", q))
        query = draw(**query_kw)
        h, w = len(query["input"]) - 2, (len(query["input"][0]) - 5) // 4
        out["query_shapes"][f"{h}x{w}"] += 1
        raw.add(json.dumps(query["input"]))
        qid = input_orbit(query["input"])
        palette = list(range(10))
        random.Random(seed_of(tid, domain, "palette", q)).shuffle(palette)
        accepted = None
        for attempt in range(MAX_CONTEXTS):
            random.seed(seed_of(tid, domain, "context", q, attempt))
            try:
                demos = [draw(panel_height=h, panel_width=w) for _ in range(3)]
            except RuntimeError:
                out["sampler_rejections"] += 1
                out["rejected_context_draws"]["sampler_exhausted"] += 1
                continue
            ids = [input_orbit(d["input"]) for d in demos] + [qid]
            if len(set(ids)) != 4:
                out["rejected_context_draws"]["duplicate_identity"] += 1
                continue
            accepted = (demos, attempt, ids)
            break
        if accepted is None:
            out["queries_failed"].append(q)
            continue
        demos, attempt, ids = accepted
        for d4 in range(8):
            ep = cert98.episode(demos + [query], d4, palette)
            ep.update(task_id=tid, episode_id=f"audit-{tid}-{domain}-{q}-{d4}",
                      d4_transform=d4, color_permutation=palette)
            make_record(ep)   # raises on any gate or exactness failure
            out["make_record_calls"] += 1
            out["augmented_pair_checks"] += 4
        key = (ids[-1], tuple(sorted(ids[:3])))
        if key in episodes:
            raise AssertionError("Duplicate episode identity")
        episodes.add(key)
        out["queries_accepted"] += 1
        out["context_retries"] += attempt
    out["unique_query_raw_inputs"] = len(raw)
    out["query_shapes"] = dict(sorted(out["query_shapes"].items()))
    out["rejected_context_draws"] = dict(out["rejected_context_draws"])
    out["passed"] = out["queries_accepted"] == QUERIES and not out["queries_failed"]
    return out


def legacy_module(tid):
    text = subprocess.run(["git", "show", f"{LEGACY_COMMIT}:tasks/task_{tid}.py"], check=True,
                          capture_output=True, text=True, cwd=BASE.parent).stdout
    module = types.ModuleType(f"legacy_{tid}")
    exec(compile(text, f"legacy/{tid}", "exec"), module.__dict__)
    return module, sha(text.encode())


def standard_diagnostic():
    """Classify recertify.check's own episodes for 98c475bf."""
    tid = "98c475bf"
    out = {}
    for version in ("before", "after"):
        if version == "before":
            module, source = legacy_module(tid)
        else:
            module = importlib.import_module("tasks.task_" + tid)
            source = sha(Path(module.__file__).read_bytes())
        classes = Counter()
        first_failure = None
        for i in range(STANDARD_SEEDS):
            random.seed(int(sha(f"diversity-recert:{tid}:{i}".encode())[:12], 16))
            pairs = [{k: grid(p[k]) for k in ("input", "output")}
                     for p in [module.generate() for _ in range(4)]]
            if len({len(p["input"][0]) for p in pairs}) > 1:
                cls = "mixed_widths"
            else:
                try:
                    require_colour_evidence(tid, pairs[:3], [{"input": pairs[3]["input"]}],
                                            list(range(10)), 0)
                    cls = "gate_accepted"
                except MissingColourEvidence:
                    cls = "same_width_undemonstrated_marker"
            classes[cls] += 1
            if cls != "gate_accepted" and first_failure is None:
                first_failure = {"episode": i, "class": cls}
        out[version] = {"constructor_sha256": source, "episodes": STANDARD_SEEDS,
                        "classes": dict(sorted(classes.items())),
                        "first_non_accepted_episode": first_failure}
    return out


def main():
    started = time.monotonic()
    result = {"audit": "context_audit.py", "queries_per_domain": QUERIES,
              "max_contexts_per_query": MAX_CONTEXTS,
              "source_sha256": {k: sha(p.read_bytes()) for k, p in PINNED.items()},
              "7491f3cf": {}, "98c475bf": {}}
    for domain, kw in DOMAINS_7491.items():
        result["7491f3cf"][domain] = audit_7491(domain, kw)
    harness = cert98.Harness()
    for domain, kw in DOMAINS_98.items():
        report = cert98.audit_domain(kw, QUERIES, "audit-" + domain, harness)
        report["passed"] = report["queries_accepted"] == QUERIES and not report["queries_failed"]
        result["98c475bf"][domain] = report
    result["98c475bf"]["pair_labels_verified_total"] = harness.labels
    result["98c475bf_standard_harness_diagnostic"] = standard_diagnostic()
    result["passed"] = all(r["passed"] for fam in ("7491f3cf", "98c475bf")
                           for r in result[fam].values() if isinstance(r, dict))
    result["seconds"] = round(time.monotonic() - started, 1)
    (HERE / "context-audit.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"passed": result["passed"], "seconds": result["seconds"]}))


if __name__ == "__main__":
    main()
