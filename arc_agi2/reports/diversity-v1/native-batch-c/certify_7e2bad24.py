"""Query-preserving informative-context certificate for 7e2bad24 (native batch C).

Root-approved exception to the generic recertify.check: the archived pair
solver uses the diagonal-target mirror reading, the native constructor uses
the side-contact reading, and three demonstrations do not always determine
which endpoint convention applies. Instead of dropping hard queries this
harness:

* draws each fresh query once and keeps it FIXED;
* resamples only the three demonstrations (bounded attempts per query) until
  the independent gate arc_agi2.beam_endpoint_evidence.require_endpoint_evidence
  accepts the episode AND its unique surviving prediction equals the
  constructor label AND the direct-factory program reproduces every pair under
  all eight D4 transforms;
* logs every retry and failure; any query that exhausts its context budget
  fails the certificate (queries are never dropped);
* records endpoint-sensitive query coverage (queries where the four endpoint
  readings disagree) and within-episode wall-orientation mixing.

Every drawn pair label is gated by runtime.verification_solver, the reviewed
native side-contact replay registered in verified_rules (the same checker that
production prepare.prepare applies to native pool pairs). The archived pair
solver is still run on every accepted pair and its disagreements are reported
only, as evidence of the coverage the archived checker used to remove.

Run from the worktree root:
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-c/certify_7e2bad24.py
"""
import hashlib
import json
import random
import sys
import time
from pathlib import Path

from arc_agi2.augmentation import transformed
from arc_agi2.beam_endpoint_evidence import beam_predictions, require_endpoint_evidence
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.direct_factories import task_7e2bad24 as factory
from arc_agi2.program_targets import audit_target, verify
from arc_agi2.runtime import BASE, call, grid, reference, solver, verification_basis, verification_solver

TID = "7e2bad24"
METHOD = "query-preserving-informative-context"
METHOD_VERSION = 2
QUERIES = 250
MAX_CONTEXTS = 64
FIXTURE_PALETTES = (list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def seed_of(*parts):
    return int(sha(":".join(map(str, ("batch-c-7e2bad24",) + parts)).encode())[:12], 16)


def episode(pairs, d4, palette):
    four = [{k: transformed(p[k], d4, palette) for k in ("input", "output")} for p in pairs]
    return {"train": four[:-1], "test": [{"input": four[-1]["input"]}],
            "solutions": [four[-1]["output"]]}


def axis(g):
    walls = {(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v in (2, 3)}
    return "h" if any((r, c + 1) in walls for r, c in walls) else "v"


def draw(module):
    p = call(module.generate, seconds=3)
    return {k: grid(p[k]) for k in ("input", "output")}


def sensitive(g):
    answers = {p for p in beam_predictions(g, list(range(10))) if p is not None}
    return len(answers) > 1


def certify(write=True):
    import importlib
    started = time.monotonic()
    module = importlib.import_module("tasks.task_" + TID)
    factory_path = BASE / "direct_factories" / ("task_" + TID + ".py")
    archived = solver(TID)
    checker = verification_solver(TID)
    report = {
        "task_id": TID, "passed": False,
        "method": METHOD, "method_version": METHOD_VERSION,
        "harness_sha256": sha(Path(__file__).read_bytes()),
        "constructor_sha256": sha(Path(module.__file__).read_bytes()),
        "factory_sha256": sha(factory_path.read_bytes()),
        "factory_version": 1,
        "evidence_gate": "arc_agi2.beam_endpoint_evidence.require_endpoint_evidence",
        "evidence_gate_sha256": sha((BASE / "beam_endpoint_evidence.py").read_bytes()),
        "pair_verifier": verification_basis(TID),
        "pair_verifier_sha256": sha((BASE / "verified_rules.py").read_bytes()),
        "requires_per_episode_verification": True,
        "fresh_pairs_checked": 0, "augmented_pair_checks": 0, "fixture_variants_checked": 0,
        "queries_requested": QUERIES, "queries_accepted": 0, "queries_failed": [],
        "max_contexts_per_query": MAX_CONTEXTS,
        "context_retries": 0, "context_retry_histogram": {}, "context_failure_reasons": {},
        "endpoint_sensitive_queries": 0, "endpoint_sensitive_accepted": 0,
        "native_pair_draws": 0, "sampler_rejections": [],
        "mixed_orientation_episodes": 0, "query_axes": {"h": 0, "v": 0},
        "archived_solver_pair_disagreements": 0,
        "archived_solver_query_disagreements": 0,
    }
    seen = set()
    reasons = {}
    try:
        fixture = reference(TID)["canonical"]
        replay = module.validate()
        if any(sorted(json.dumps(p, sort_keys=True) for p in replay[s])
               != sorted(json.dumps(p, sort_keys=True) for p in fixture[s]) for s in ("train", "test")):
            raise ValueError("Original fixture replay changed")
        fpairs = fixture["train"] + fixture["test"]
        for palette in FIXTURE_PALETTES:
            for d4 in range(8):
                ep = episode(fpairs, d4, palette)
                require_endpoint_evidence(ep["train"], ep["test"], palette)
                src = factory.build_program(d4, palette)
                audit_target(TID, src)
                verify(src, ep)
                report["fixture_variants_checked"] += 1
        for q in range(QUERIES):
            if time.monotonic() - started > 1500:
                raise TimeoutError("Certification budget exhausted")
            random.seed(seed_of("query", q))
            query = draw(module)
            report["native_pair_draws"] += 1
            if grid(call(checker, query["input"])) != query["output"]:
                raise ValueError("Independent verifier disagrees with constructor label")
            is_sensitive = sensitive(query["input"])
            report["endpoint_sensitive_queries"] += is_sensitive
            accepted = None
            for attempt in range(MAX_CONTEXTS):
                cseed = seed_of("context", q, attempt)
                random.seed(cseed)
                try:
                    demos = [draw(module) for _ in range(3)]
                except Exception as exc:
                    report["sampler_rejections"].append({"seed": cseed, "error": repr(exc)})
                    continue
                report["native_pair_draws"] += 3
                if any(grid(call(checker, d["input"])) != d["output"] for d in demos):
                    raise ValueError("Independent verifier disagrees with constructor label")
                rng = random.Random(cseed + 1)
                palette = list(range(10))
                rng.shuffle(palette)
                pairs = demos + [query]
                try:
                    for d4 in range(8):
                        ep = episode(pairs, d4, palette)
                        require_endpoint_evidence(ep["train"], ep["test"], palette)
                        # Independent label: the unique prediction of every
                        # demonstrated endpoint rule must equal the constructor.
                        from arc_agi2.beam_endpoint_evidence import surviving_endpoint_rules
                        alive = surviving_endpoint_rules(ep["train"], palette)
                        preds = beam_predictions(ep["test"][0]["input"], palette)
                        answers = {preds[i] for i in alive if preds[i] is not None}
                        if answers != {tuple(map(tuple, ep["solutions"][0]))}:
                            raise ValueError("Independent endpoint evidence disagrees with constructor label")
                        src = factory.build_program(d4, palette)
                        audit_target(TID, src)
                        verify(src, ep, seconds=3)
                    accepted = (demos, palette, attempt)
                    break
                except MissingColourEvidence as exc:
                    reasons[str(exc)] = reasons.get(str(exc), 0) + 1
                except Exception as exc:
                    key = type(exc).__name__ + ":" + str(exc)[:100]
                    reasons[key] = reasons.get(key, 0) + 1
                    if "disagrees with constructor" in key:
                        raise
            if accepted is None:
                report["queries_failed"].append({"query": q, "seed": seed_of("query", q),
                                                 "endpoint_sensitive": is_sensitive})
                continue
            demos, palette, attempt = accepted
            report["context_retries"] += attempt
            h = report["context_retry_histogram"]
            h[str(attempt)] = h.get(str(attempt), 0) + 1
            report["queries_accepted"] += 1
            report["endpoint_sensitive_accepted"] += is_sensitive
            report["fresh_pairs_checked"] += 4
            report["augmented_pair_checks"] += 32
            axes = [axis(p["input"]) for p in demos + [query]]
            report["query_axes"][axes[-1]] += 1
            report["mixed_orientation_episodes"] += len(set(axes)) > 1
            for i, p in enumerate(demos + [query]):
                seen.add(sha(json.dumps(p["input"]).encode()))
                if grid(call(archived, p["input"])) != p["output"]:
                    report["archived_solver_pair_disagreements"] += 1
                    report["archived_solver_query_disagreements"] += i == 3
        report["context_failure_reasons"] = reasons
        report["unique_base_inputs"] = len(seen)
        if report["queries_failed"]:
            raise ValueError("Queries exhausted the bounded context budget")
        if report["fresh_pairs_checked"] < 1000 or len(seen) < 100:
            raise ValueError("Insufficient verified fresh examples")
        report.update(passed=True, fixture_basis="canonical",
                      seconds=round(time.monotonic() - started, 2))
    except Exception as exc:
        report["context_failure_reasons"] = reasons
        report["error"] = repr(exc)
    if write:
        out = BASE / "reports/diversity-v1/native-certificates" / (TID + ".json")
        out.write_text(json.dumps(report, indent=2) + "\n")
        if report["passed"]:
            # The production factory certificate keeps the reviewed provenance
            # of the unchanged factory; the measured fields are replaced.
            target = BASE / "direct_factories" / (TID + ".json")
            old = json.loads(target.read_text()) if target.exists() else {}
            merged = dict(report)
            for key in ("provenance", "draft_notes"):
                if key in old:
                    merged[key] = old[key]
            if old.get("constructor_sha256") not in (None, report["constructor_sha256"]):
                merged["previous_constructor_sha256"] = old["constructor_sha256"]
            elif "previous_constructor_sha256" in old:
                merged["previous_constructor_sha256"] = old["previous_constructor_sha256"]
            target.write_text(json.dumps(merged, indent=2) + "\n")
    return report


if __name__ == "__main__":
    r = certify(write="--no-write" not in sys.argv)
    print(json.dumps({k: v for k, v in r.items() if k not in ("context_failure_reasons",)}, indent=1))
    print(json.dumps(r["context_failure_reasons"], indent=1))
