"""Opt-in broader proposals, retaining native coverage and all episode gates."""

import hashlib
import json
import random
from functools import lru_cache
from pathlib import Path

from ..program_targets import compile_target
from ..runtime import BASE, call, grid, verification_solver
from .colour_roles import align_pair

ROOT = Path(__file__).parent
PROFILE = "rearc-compatible-v1"


@lru_cache(maxsize=1)
def admission():
    report = json.loads((ROOT / "admission.json").read_text())
    if report["version"] != PROFILE:
        raise ValueError("Diversity admission version mismatch")
    for name, digest in report["source_hashes"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError("RE-ARC source changed since compatibility checks: " + name)
    for name, digest in report.get("target_source_hashes", {}).items():
        if hashlib.sha256((BASE.parent / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Target dependency changed since diversity admission: " + name)
    for name, digest in report.get("proposal_source_hashes", {}).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Proposal alignment changed since admission: " + name)
    return report


@lru_cache(maxsize=1120)
def eligible(tid):
    record = admission()["admitted"].get(tid)
    if not record:
        return False
    text, _ = compile_target(tid)
    if hashlib.sha256(text.encode()).hexdigest() != record["program_sha256"]:
        raise ValueError(tid + ": program changed since diversity admission")
    return True


@lru_cache(maxsize=1120)
def fork_checker(tid):
    return verification_solver(tid)


def sample_checked(tid, seed):
    """One proposal; incompatibility raises, and caller must count the rejection."""
    if not eligible(tid):
        raise ValueError(tid + ": broader source not admitted")
    from .rearc import generators, utils, verifiers

    state = random.getstate()
    try:
        random.seed(seed)
        utils.rng.clear()
        proposal = call(getattr(generators, "generate_" + tid), 0.0, 1.0, seconds=2)
        pair = {k: grid(proposal[k]) for k in ("input", "output")}
        expected = pair["output"]
        external = call(
            getattr(verifiers, "verify_" + tid), tuple(map(tuple, pair["input"])), seconds=2
        )
        if grid(external) != expected:
            raise ValueError("RE-ARC constructor/verifier disagreement")
        pair, source_palette = align_pair(tid, pair)
        expected = pair["output"]
        if grid(call(fork_checker(tid), pair["input"], seconds=2)) != expected:
            raise ValueError("Fork/RE-ARC domain disagreement")
        pair["source_colour_map"] = source_palette
        return pair, {
            "mode": PROFILE,
            "seed": seed,
            "attempts": [],
            "label_source": "constructor",
            "verifiers_checked": 2,
            "source_colour_map": source_palette,
        }
    finally:
        random.setstate(state)
        utils.rng.clear()
