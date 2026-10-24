"""Check candidate RE-ARC domains under D4/palette episode augmentation."""

import argparse
import hashlib
import importlib
import json
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ..colour_evidence import require_colour_evidence
from ..program_targets import audit_target, compile_target, verify
from ..runtime import BASE
from .colour_roles import ROLE_ALIGNED
from .recertify import episode


def check(tid):
    evidence = json.loads((BASE / "reports/diversity-v1" / (tid + ".json")).read_text())
    pairs = evidence["accepted_pairs"]
    result = {"task_id": tid, "verified_variants": 0, "passed": False}
    try:
        text, _ = compile_target(tid)
        result["program_sha256"] = hashlib.sha256(text.encode()).hexdigest()
        pair_budget = 1024 if tid in ROLE_ALIGNED else 32
        result["available_pairs"] = len(pairs)
        result["requested_pair_checks"] = pair_budget
        for offset in range(0, min(len(pairs) - 3, pair_budget), 4):
            palette = list(range(10))
            random.Random(4811 + offset).shuffle(palette)
            for d4 in range(8):
                ep = episode(pairs[offset : offset + 4], d4, palette)
                require_colour_evidence(tid, ep["train"], ep["test"], palette, d4)
                text, _ = compile_target(tid, d4, palette)
                audit_target(tid, text)
                verify(text, ep, seconds=2)
                result["verified_variants"] += 1
        required = 2048 if tid in ROLE_ALIGNED else 32
        result["passed"] = result["verified_variants"] >= required
    except Exception as exc:
        result["error"] = repr(exc)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    candidates = json.loads((BASE / "reports/diversity-v1/summary.json").read_text())
    ids = [
        r["task_id"]
        for r in candidates
        if r.get("candidate_ready")
        and r["task_id"] not in ("7b7f7511", "269e22fb")
        and not getattr(
            importlib.import_module("tasks.task_" + r["task_id"]), "SYNTHETIC_VARIANT", None
        )
    ]
    with ProcessPoolExecutor(args.workers) as pool:
        results = list(pool.map(check, ids))
    root = Path(__file__).parent
    hashes = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((root / "rearc").glob("*"))
        if p.is_file()
    }
    target_files = [
        BASE / name
        for name in (
            "direct_programs.py",
            "direct_certificates.py",
            "verified_rules.py",
            "program_targets.py",
            "runtime.py",
            "helpers.py",
            "colour_evidence.py",
            "feca6190_evidence.py",
        )
    ]
    for result in results:
        if not result["passed"]:
            continue
        tid = result["task_id"]
        target_files += [BASE.parent / "tasks" / ("task_" + tid + ".py")]
        target_files += [
            p
            for p in (
                BASE / "direct_factories" / ("task_" + tid + ".py"),
                BASE / "direct_factories" / (tid + ".json"),
                BASE / "reports/direct-certificates" / (tid + ".json"),
            )
            if p.exists()
        ]
    report = {
        "version": "rearc-compatible-v1",
        "source_hashes": hashes,
        "target_source_hashes": {
            str(p.relative_to(BASE.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in target_files
        },
        "proposal_source_hashes": {
            "colour_roles.py": hashlib.sha256((root / "colour_roles.py").read_bytes()).hexdigest()
        },
        "candidate_families": len(ids),
        "admitted": {r["task_id"]: r for r in results if r["passed"]},
        "not_admitted": [r for r in results if not r["passed"]],
        "policy": (
            "Supplement native constructors only. Check each proposed label with both verifiers; "
            "independently verify every final augmented program/episode. No changed labels. "
            "Context evidence and global input-orbit splitting remain required."
        ),
    }
    (root / "admission.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"candidate_families": len(ids), "admitted": len(report["admitted"])}))


if __name__ == "__main__":
    main()
