"""Certify reviewed RE-ARC colour-role alignments one family at a time.

Reuses the existing gates: ``probe.probe`` (both verifiers, then fresh
episodes against the direct program) and ``admit.check`` (complete episodes
under all eight D4 transforms and random palettes). Writes the large sampled
evidence to the ignored ``reports/diversity-v1/<id>.json`` and a small
certificate to ``reports/diversity-v1/role-certificates/<id>.json``. It does
not modify ``summary.json`` or ``admission.json``; global admission is rebuilt
separately with ``admit.py``.
"""

import argparse
import hashlib
import json
import random
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ..program_targets import audit_target, compile_target, verify
from ..runtime import BASE, call, grid, reference
from . import admit, probe
from .colour_roles import ROLE_SPECS, align_pair
from .recertify import episode

ROOT = Path(__file__).parent
OUT = BASE / "reports/diversity-v1/role-certificates"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixture_checks(tid):
    """Native fixtures must be role-fixed points and pass every augmented target."""
    fixture = reference(tid)["canonical"]
    pairs = fixture["train"] + fixture["test"]
    for pair in pairs:
        _, palette = align_pair(tid, {k: pair[k] for k in ("input", "output")})
        if palette != list(range(10)):
            raise ValueError("Native fixture is not a fixed point of the role mapping")
    variants = 0
    for palette in (list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]):
        for d4 in range(8):
            text, _ = compile_target(tid, d4, palette)
            audit_target(tid, text)
            verify(text, episode(pairs, d4, palette))
            variants += 1
    return {"fixture_pairs_identity_mapped": len(pairs), "fixture_variants_checked": variants}


def alignment_rejections(tid, count):
    """Re-derive probe proposals to attribute each alignment rejection to a reason."""
    from .rearc import generators, utils, verifiers
    reasons = Counter()
    gen = getattr(generators, "generate_" + tid)
    check = getattr(verifiers, "verify_" + tid)
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
            align_pair(tid, pair)
        except ValueError as exc:
            reasons[str(exc)] += 1
    return dict(reasons)


def certify(item):
    tid, samples = item
    began = time.monotonic()
    report = {"task_id": tid, "passed": False, "role_spec": ROLE_SPECS[tid],
              "requested_proposals": samples}
    try:
        report.update(fixture_checks(tid))
        evidence = probe.probe((tid, samples))
        (BASE / "reports/diversity-v1" / (tid + ".json")).write_text(
            json.dumps(evidence, indent=2) + "\n")
        report.update(
            accepted_pairs=evidence["accepted"],
            probe_rejections=evidence["rejections"],
            probe_verified_episodes=evidence["verified_episodes"],
            bounded_stop=evidence.get("bounded_stop", False),
            input_shape_count=len(evidence["input_shapes"]),
            alignment_rejection_reasons=alignment_rejections(tid, samples),
        )
        gate = admit.check(tid)
        report.update(augmented_episode_checks=gate["verified_variants"],
                      augmented_pair_checks=4 * gate["verified_variants"],
                      admission_gate_passed=gate["passed"],
                      program_sha256=gate.get("program_sha256"))
        if "error" in gate:
            report["admission_gate_error"] = gate["error"]
        report["passed"] = bool(gate["passed"] and evidence["verified_episodes"] >= 4
                                and not report["bounded_stop"])
    except Exception as exc:
        report["error"] = repr(exc)
    factory = BASE / "direct_factories" / ("task_" + tid + ".py")
    report["dependency_sha256"] = {
        "diversity/colour_roles.py": sha(ROOT / "colour_roles.py"),
        "diversity/rearc/generators.py": sha(ROOT / "rearc/generators.py"),
        "diversity/rearc/verifiers.py": sha(ROOT / "rearc/verifiers.py"),
        "direct_factories/task_" + tid + ".py": sha(factory) if factory.exists() else None,
    }
    report["seconds"] = round(time.monotonic() - began, 3)
    report["limitations"] = ("Finite sampled checks of a bijective pre-palette colour "
                             "mapping; not proof of unrestricted semantic equivalence.")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / (tid + ".json")).write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task_ids", nargs="+")
    parser.add_argument("--samples", type=int, default=1152)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    unknown = set(args.task_ids) - set(ROLE_SPECS)
    if unknown:
        raise ValueError("No reviewed role specification: " + " ".join(sorted(unknown)))
    with ProcessPoolExecutor(max_workers=min(args.workers, len(args.task_ids))) as pool:
        for r in pool.map(certify, [(t, args.samples) for t in args.task_ids]):
            print(json.dumps({k: r.get(k) for k in (
                "task_id", "passed", "accepted_pairs", "augmented_episode_checks",
                "probe_rejections", "alignment_rejection_reasons", "error",
                "admission_gate_error")}), flush=True)


if __name__ == "__main__":
    main()
