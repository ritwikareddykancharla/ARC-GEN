"""Re-certify changed constructors against existing standalone target programs.

No hashes are refreshed unless supplied fixtures and 1,000 fresh pairs pass
all eight spatial transforms. Every exported episode still needs its own check.
"""

import argparse
import hashlib
import importlib
import json
import random
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ..audit_direct_candidates import candidate
from ..augmentation import transformed
from ..direct_programs import direct_source
from ..program_targets import audit_target, verify
from ..runtime import BASE, call, grid, reference, verification_solver


def sha(value):
    return hashlib.sha256(value).hexdigest()


def episode(pairs, d4, palette):
    four = [{k: transformed(p[k], d4, palette) for k in ("input", "output")} for p in pairs]
    return {
        "train": four[:-1],
        "test": [{"input": four[-1]["input"]}],
        "solutions": [four[-1]["output"]],
    }


def check(tid):
    started = time.monotonic()
    module = importlib.import_module("tasks.task_" + tid)
    factory_path = BASE / "direct_factories" / ("task_" + tid + ".py")
    factory = (
        importlib.import_module("arc_agi2.direct_factories.task_" + tid)
        if factory_path.exists()
        else None
    )
    builtin = None if factory else direct_source(tid, 0, list(range(10)))
    native = None if factory else (builtin or candidate(tid)[0])

    def source(d4, palette):
        text = (factory.build_program(d4, palette) if factory else
                direct_source(tid, d4, palette) if builtin else native)
        audit_target(tid, text)
        return text

    report = {
        "task_id": tid,
        "passed": False,
        "fresh_pairs_checked": 0,
        "augmented_pair_checks": 0,
        "fixture_variants_checked": 0,
        "constructor_sha256": sha(Path(module.__file__).read_bytes()),
        "auditor_sha256": sha(Path(__file__).read_bytes()),
        "requires_per_episode_verification": True,
        "sampler_rejections": [],
        "program_provider": "factory" if factory else "direct_source" if builtin else "native_candidate",
    }
    if factory:
        report["factory_sha256"] = sha(factory_path.read_bytes())
        report["factory_version"] = 1
    else:
        report["program_sha256"] = sha(native.encode())
        report["certificate_version"] = 1
    seen = set()
    try:
        fixture = reference(tid)["canonical"]
        replay = module.validate()
        # Upstream validate() may list the original demonstrations in a
        # different order; compare the full pair multiset within each split.
        if any(
            sorted(json.dumps(p, sort_keys=True) for p in replay[split])
            != sorted(json.dumps(p, sort_keys=True) for p in fixture[split])
            for split in ("train", "test")
        ):
            raise ValueError("Original fixture replay changed")
        for palette in (list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]):
            for d4 in range(8):
                verify(
                    source(d4, palette), episode(fixture["train"] + fixture["test"], d4, palette)
                )
                report["fixture_variants_checked"] += 1
        checker = verification_solver(tid)
        for i in range(300):
            if time.monotonic() - started > 300:
                raise TimeoutError("Five-minute certification budget exhausted")
            seed = int(sha(f"diversity-recert:{tid}:{i}".encode())[:12], 16)
            random.seed(seed)
            try:
                pairs = [
                    {k: grid(p[k]) for k in ("input", "output")}
                    for p in [call(module.generate, seconds=3) for _ in range(4)]
                ]
            except Exception as exc:
                report["sampler_rejections"].append({"seed": seed, "error": repr(exc)})
                continue
            for pair in pairs:
                if grid(call(checker, pair["input"])) != pair["output"]:
                    raise ValueError("Independent verifier disagrees with constructor label")
                seen.add(sha(json.dumps(pair["input"]).encode()))
            palette = list(range(10))
            random.Random(seed + 1).shuffle(palette)
            for d4 in range(8):
                verify(source(d4, palette), episode(pairs, d4, palette), seconds=2)
                report["augmented_pair_checks"] += 4
            report["fresh_pairs_checked"] += 4
            if report["fresh_pairs_checked"] >= 1000:
                break
        report["unique_base_inputs"] = len(seen)
        if report["fresh_pairs_checked"] < 1000 or len(seen) < 100:
            raise ValueError("Insufficient verified fresh examples")
        report.update(passed=True, fixture_basis="canonical", seconds=time.monotonic() - started)
    except Exception as exc:
        report["error"] = repr(exc)
    out = BASE / "reports/diversity-v1/native-certificates"
    out.mkdir(parents=True, exist_ok=True)
    (out / (tid + ".json")).write_text(json.dumps(report, indent=2) + "\n")
    if report["passed"]:
        target = (
            (BASE / "direct_factories") if factory else (BASE / "reports/direct-certificates")
        ) / (tid + ".json")
        target.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("task_ids", nargs="+")
    args = parser.parse_args()
    with ProcessPoolExecutor(max_workers=min(8, len(args.task_ids))) as pool:
        for report in pool.map(check, args.task_ids):
            print(json.dumps(report), flush=True)
