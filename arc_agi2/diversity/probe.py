"""Check broader RE-ARC proposals against both labels and current program targets.

Writes admission evidence, never substitutes a verifier output for a constructor
label. No existing fixtures, dataset records, or training jobs are modified.
"""

import argparse
import concurrent.futures
import hashlib
import json
import multiprocessing
import random
import time
from collections import Counter
from pathlib import Path

from ..colour_evidence import require_colour_evidence
from ..program_targets import audit_target, compile_target, verify
from ..runtime import BASE, call, grid, verification_solver
from .colour_roles import align_pair
from .rearc import generators, utils, verifiers


def probe(item, deadline=35):
    """``deadline`` bounds proposal sampling; exceeding it sets ``bounded_stop``."""
    tid, count = item
    began = time.monotonic()
    gen = getattr(generators, "generate_" + tid)
    check = getattr(verifiers, "verify_" + tid)
    result = {
        "task_id": tid,
        "requested_proposals": count,
        "rejections": {},
        "accepted_pairs": [],
        "episodes": [],
        "source": "rearc-mit-e5b7f1d",
        "all_original_fixtures_unchanged": True,
    }
    reject = Counter()
    shapes = Counter()
    seen = set()
    try:
        saved = verification_solver(tid)
        program, basis = compile_target(tid)
        audit_target(tid, program)
        result["program_basis"] = basis
        result["program_sha256"] = hashlib.sha256(program.encode()).hexdigest()
    except Exception as exc:
        result["setup_error"] = repr(exc)
        return result
    for i in range(count):
        if time.monotonic() - began > deadline:
            result["bounded_stop"] = True
            break
        seed = int(hashlib.sha256(f"diversity-v1:{tid}:{i}".encode()).hexdigest()[:8], 16)
        random.seed(seed)
        utils.rng.clear()
        try:
            proposal = call(gen, 0.0, 1.0, seconds=1)
            pair = {k: grid(proposal[k]) for k in ("input", "output")}
            expected = pair["output"]
            if grid(call(check, tuple(map(tuple, pair["input"])), seconds=1)) != expected:
                reject["rearc_verifier_disagreement"] += 1
                continue
            pair, source_palette = align_pair(tid, pair)
            expected = pair["output"]
            if grid(call(saved, pair["input"], seconds=1)) != expected:
                reject["fork_verifier_disagreement"] += 1
                continue
            identity = json.dumps(pair["input"], separators=(",", ":"))
            if identity in seen:
                reject["duplicate_input"] += 1
                continue
            seen.add(identity)
            result["accepted_pairs"].append({"seed": seed, "source_colour_map": source_palette,
                                              **pair})
            shapes[f"{len(pair['input'])}x{len(pair['input'][0])}"] += 1
        except Exception as exc:
            reject[type(exc).__name__] += 1
    # Fresh demonstrations, never the reference fixtures, condition the target.
    pairs = result["accepted_pairs"]
    for offset in range(0, len(pairs) - 3, 4):
        four = pairs[offset : offset + 4]
        episode = {
            "train": [{k: p[k] for k in ("input", "output")} for p in four[:3]],
            "test": [{"input": four[3]["input"]}],
            "solutions": [four[3]["output"]],
        }
        try:
            require_colour_evidence(tid, episode["train"], episode["test"], list(range(10)), 0)
            evidence = verify(program, episode, seconds=1)
            result["episodes"].append({"seeds": [p["seed"] for p in four], **evidence})
        except Exception as exc:
            reject["episode_" + type(exc).__name__] += 1
    result.update(
        rejections=dict(reject),
        input_shapes=dict(shapes),
        accepted=len(pairs),
        verified_episodes=len(result["episodes"]),
        seconds=round(time.monotonic() - began, 3),
    )
    # Evidence only: source hashes and context policy are checked by the sampler.
    result["candidate_ready"] = len(pairs) >= 32 and len(result["episodes"]) >= 4
    result["limitations"] = (
        "Bounded compatibility tests; not proof of demonstration sufficiency "
        "or semantic equivalence."
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--out", required=True)
    parser.add_argument("--tasks", nargs="+")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ids = [
        r["task_id"]
        for r in json.loads((BASE / "reference_index.json").read_text())["tasks"]
        if hasattr(generators, "generate_" + r["task_id"])
    ]
    if args.tasks:
        if not set(args.tasks) <= set(ids):
            raise ValueError("Task has no RE-ARC counterpart")
        ids = sorted(set(args.tasks))
    summary = []
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=args.workers, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        futures = {pool.submit(probe, (tid, args.samples)): tid for tid in ids}
        for future in concurrent.futures.as_completed(futures):
            tid = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {"task_id": tid, "audit_error": repr(exc)}
            (out / f"{tid}.json").write_text(json.dumps(result, indent=2) + "\n")
            summary.append(
                {k: v for k, v in result.items() if k not in ("accepted_pairs", "episodes")}
            )
            if len(summary) % 20 == 0 or len(summary) == len(ids):
                print(
                    json.dumps(
                        {
                            "completed": len(summary),
                            "total": len(ids),
                            "candidate_ready": sum(
                                r.get("candidate_ready", False) for r in summary
                            ),
                        }
                    ),
                    flush=True,
                )
    if args.tasks and (out / "summary.json").exists():
        summary += [r for r in json.loads((out / "summary.json").read_text())
                    if r["task_id"] not in set(ids)]
    (out / "summary.json").write_text(
        json.dumps(sorted(summary, key=lambda r: r["task_id"]), indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
