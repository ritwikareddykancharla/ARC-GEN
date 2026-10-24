"""Certify reviewed program repairs for broader RE-ARC domains, one family at a time.

These families need no colour-role alignment. Their RE-ARC labels already pass
both verifiers, but the earlier direct programs failed some augmented episodes.
The factory headers in ``direct_factories/`` record the reviewed semantics.
Each factory must already hold a native certificate from ``recertify``
(1,000 fresh native pairs, 8,000 D4 checks and 16 fixture variants).

This module reuses the existing gates with the colour-role budget. It runs
``probe.probe`` (both verifiers, then fresh episodes against the program) and
``admit.check`` on at least 1,024 accepted pairs: 2,048 complete episodes under
all eight D4 transforms and random palettes. Proposal counts are set per
family so that this budget is reachable after archived-verifier rejections.
Every rejection is counted. The large evidence goes to the ignored
``reports/diversity-v1/<id>.json``. A small certificate goes to
``reports/diversity-v1/program-certificates/<id>.json``. Neither
``summary.json`` nor ``admission.json`` is modified.
"""

import argparse
import hashlib
import json
import random
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ..direct_certificates import certified_factory_source
from ..program_targets import compile_target
from ..runtime import BASE, call, grid, verification_solver
from . import admit, probe
from .certify_roles import fixture_checks
from .colour_roles import ROLE_SPECS

ROOT = Path(__file__).parent
OUT = BASE / "reports/diversity-v1/program-certificates"
PAIR_BUDGET, EPISODE_BUDGET = 1024, 2048

# Proposals per family, sized from measured archived-verifier acceptance.
PROGRAM_REPAIRS = {
    "1a07d186": 1536,
    "272f95fa": 1152,
    "57aa92db": 1152,
    "63613498": 3456,
    "8403a5d5": 1152,
    "aabf363d": 2688,
    "fcb5c309": 3456,
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fork_rejection_analysis(tid, count):
    """For proposals RE-ARC verifies, compare the archived verifier with the program.

    This attributes rejections; it never admits a pair the archived verifier rejects.
    """
    from .rearc import generators, utils, verifiers
    gen = getattr(generators, "generate_" + tid)
    check = getattr(verifiers, "verify_" + tid)
    saved = verification_solver(tid)
    namespace = {}
    exec(compile(compile_target(tid)[0], "<target>", "exec"), namespace)
    tally = Counter()
    for i in range(count):
        seed = int(hashlib.sha256(f"diversity-v1:{tid}:{i}".encode()).hexdigest()[:8], 16)
        random.seed(seed)
        utils.rng.clear()
        try:
            proposal = call(gen, 0.0, 1.0, seconds=1)
            pair = {k: grid(proposal[k]) for k in ("input", "output")}
            if grid(call(check, tuple(map(tuple, pair["input"])), seconds=1)) != pair["output"]:
                continue
        except Exception:
            continue
        try:
            fork = grid(call(saved, pair["input"], seconds=1)) == pair["output"]
        except Exception:
            fork = False
        try:
            program = grid(call(namespace["solve"], [], pair["input"], seconds=1)) == pair["output"]
        except Exception:
            program = False
        tally[("archived_verifier_" + ("agrees" if fork else "rejects")) + "/program_"
              + ("exact" if program else "not_exact")] += 1
    return dict(sorted(tally.items()))


def certify(tid):
    samples = PROGRAM_REPAIRS[tid]
    began = time.monotonic()
    factory = BASE / "direct_factories" / ("task_" + tid + ".py")
    native = BASE / "direct_factories" / (tid + ".json")
    report = {"task_id": tid, "passed": False, "requested_proposals": samples,
              "colour_alignment": None}
    try:
        if tid in ROLE_SPECS:
            raise ValueError("Role-aligned families use certify_roles")
        if certified_factory_source(tid, 0, list(range(10))) is None:
            raise ValueError("Factory lacks a current native certificate")
        native_cert = json.loads(native.read_text())
        report["native_certificate"] = {
            k: native_cert.get(k) for k in ("fresh_pairs_checked", "augmented_pair_checks",
                                            "fixture_variants_checked", "unique_base_inputs",
                                            "finite_default_domain")
            if k in native_cert}
        report.update(fixture_checks(tid))
        evidence = probe.probe((tid, samples), deadline=300)
        (BASE / "reports/diversity-v1" / (tid + ".json")).write_text(
            json.dumps(evidence, indent=2) + "\n")
        report.update(
            accepted_pairs=evidence["accepted"],
            probe_rejections=evidence["rejections"],
            probe_verified_episodes=evidence["verified_episodes"],
            bounded_stop=evidence.get("bounded_stop", False),
            input_shape_count=len(evidence["input_shapes"]),
            fork_rejection_analysis=fork_rejection_analysis(tid, samples),
        )
        gate = admit.check(tid, pair_budget=PAIR_BUDGET, required=EPISODE_BUDGET)
        report.update(augmented_episode_checks=gate["verified_variants"],
                      augmented_pair_checks=4 * gate["verified_variants"],
                      admission_gate_passed=gate["passed"],
                      program_sha256=gate.get("program_sha256"))
        if "error" in gate:
            report["admission_gate_error"] = gate["error"]
        report["passed"] = bool(gate["passed"] and evidence["accepted"] >= PAIR_BUDGET
                                and evidence["verified_episodes"] >= 4
                                and not report["bounded_stop"])
    except Exception as exc:
        report["error"] = repr(exc)
    report["dependency_sha256"] = {
        "diversity/rearc/generators.py": sha(ROOT / "rearc/generators.py"),
        "diversity/rearc/verifiers.py": sha(ROOT / "rearc/verifiers.py"),
        "direct_factories/task_" + tid + ".py": sha(factory) if factory.exists() else None,
        "direct_factories/" + tid + ".json": sha(native) if native.exists() else None,
    }
    report["seconds"] = round(time.monotonic() - began, 3)
    report["limitations"] = ("Finite sampled checks of a reviewed program on archived-verifier "
                             "accepted RE-ARC pairs; not proof of unrestricted semantic "
                             "equivalence. Archived-verifier rejections remain excluded.")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / (tid + ".json")).write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task_ids", nargs="+")
    parser.add_argument("--workers", type=int, default=7)
    args = parser.parse_args()
    unknown = set(args.task_ids) - set(PROGRAM_REPAIRS)
    if unknown:
        raise ValueError("No reviewed program repair: " + " ".join(sorted(unknown)))
    with ProcessPoolExecutor(max_workers=min(args.workers, len(args.task_ids))) as pool:
        for r in pool.map(certify, args.task_ids):
            print(json.dumps({k: r.get(k) for k in (
                "task_id", "passed", "accepted_pairs", "augmented_episode_checks",
                "probe_rejections", "fork_rejection_analysis", "error",
                "admission_gate_error")}), flush=True)


if __name__ == "__main__":
    main()
