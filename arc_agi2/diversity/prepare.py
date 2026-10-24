"""Prepare readable, verified PNG/program/grid episodes from expanded domains.

This is a supplement to the full 1,120-family corpus, not a replacement. The
default scope is the admitted RE-ARC overlap plus the reviewed native repairs.
It never uploads, changes an existing release, or starts model training.
"""

import argparse
import hashlib
import importlib
import json
import random
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from ..augmentation import transformed
from ..episode_shape_policy import profile_from_task, select_demonstrations
from ..finite_input_policy import POLICY_SIGNATURE, identity_key, input_split
from ..program_targets import make_record
from ..runtime import BASE, call, grid, reference, verification_solver
from ..visual_dataset import render
from .sampler import admission, eligible, sample_checked

REPAIRED = ("007bbfb7", "009d5c81", "00dbd492", "0934a4d8", "09c534e7", "1e0a9b12", "3194b014",
            "3a301edc", "45bbe264", "aaecdb9a", "ecb67b6d")


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def input_orbit(g):
    variants = []
    for d4 in range(8):
        a = transformed(g, d4, list(range(10)))
        palette, flat = {}, []
        for row in a:
            for colour in row:
                if colour not in palette:
                    palette[colour] = len(palette)
                flat.append(palette[colour])
        variants.append(bytes([len(a), len(a[0]), *flat]))
    return hashlib.sha256(min(variants)).hexdigest()


def feasible_queries(pool, profile, identity):
    """Find query shapes with enough distinct context, using inputs only."""
    groups = defaultdict(set)
    for p in pool:
        groups[(len(p["input"]), len(p["input"][0]))].add(p[identity])
    all_ids = set().union(*groups.values()) if groups else set()
    result = []
    for query in pool:
        shape = (len(query["input"]), len(query["input"][0]))
        qid = query[identity]
        for pattern in profile["patterns"]:
            uniform = pattern["demo_input_shapes"] == "uniform"
            seen = pattern["query_input_shape"] == "seen"
            if uniform:
                possible = any(
                    len(ids - {qid}) >= 3 and ((s == shape) == seen) for s, ids in groups.items()
                )
            elif seen:
                possible = (
                    len(all_ids - {qid}) >= 3
                    and bool(groups[shape] - {qid})
                    and any(s != shape and ids - {qid} for s, ids in groups.items())
                )
            else:
                other = [ids - {qid} for s, ids in groups.items() if s != shape]
                possible = sum(bool(ids) for ids in other) >= 2 and len(set().union(*other)) >= 3
            if possible:
                result.append(query)
                break
    return result


def prepare(item):
    tid, options = item
    root = Path(options["out"])
    report_path = root / "reports" / (tid + ".json")
    if report_path.exists():
        old = json.loads(report_path.read_text())
        if old.get("complete"):
            for name, expected in old["file_sha256"].items():
                if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
                    raise ValueError("Completed output changed: " + name)
            return old
    started = time.monotonic()
    module = importlib.import_module("tasks.task_" + tid)
    check = verification_solver(tid)
    use_broader = eligible(tid)
    randomizer = random.Random(int(digest([options["seed"], tid])[:15], 16))
    pools = {"train": [], "validation": []}
    profile = profile_from_task(reference(tid)["canonical"])
    identity = identity_key(tid)
    seen, rejected, sources, counts = set(), Counter(), Counter(), Counter()
    target_pool = max(160, options["train"] * 2 + options["validation"] * 8)
    for trial in range(target_pool * 40):
        if time.monotonic() - started > options["seconds"] * 0.6:
            break
        seed = int(digest([options["seed"], tid, "pair", trial])[:15], 16)
        mode = "rearc-compatible-v1" if use_broader and randomizer.random() < 0.5 else "native"
        try:
            if mode == "native":
                random.seed(seed)
                pair = call(module.generate, seconds=2)
                pair = {k: grid(pair[k]) for k in ("input", "output")}
                if grid(call(check, pair["input"], seconds=2)) != pair["output"]:
                    raise ValueError("Independent verifier disagrees")
            else:
                pair, _ = sample_checked(tid, seed)
            orbit = input_orbit(pair["input"])
            exact = digest(pair["input"])
            if exact in seen:
                rejected["duplicate_input"] += 1
                continue
            seen.add(exact)
            split = input_split(orbit)
            pair.update(
                input_hash=exact, canonical_input_hash=orbit, generator_mode=mode, seed=seed
            )
            pools[split].append(pair)
            sources[mode] += 1
            if trial % 64 == 63 and all(len(pools[s]) >= max(40, options[s] * 2) for s in pools):
                if all(
                    len({p[identity] for p in feasible_queries(pools[s], profile, identity)})
                    >= options[s]
                    for s in pools
                ):
                    break
        except Exception as exc:
            rejected["pair:" + type(exc).__name__ + ":" + str(exc)[:120]] += 1
    paths = []
    shape_patterns = Counter()
    for split, pool in pools.items():
        query_candidates = feasible_queries(pool, profile, identity)
        folder = root / split / tid
        folder.mkdir(parents=True, exist_ok=True)
        pending = folder / "metadata.jsonl.tmp"
        used_queries = set()
        with pending.open("w") as stream:
            for _attempt in range(max(100, options[split] * 40)):
                if (
                    counts[split] >= options[split]
                    or time.monotonic() - started > options["seconds"]
                ):
                    break
                if len(pool) < 4 or not query_candidates:
                    rejected[split + ":no_shape_compatible_distinct_query_context"] += 1
                    break
                query = randomizer.choice(query_candidates)
                if query[identity] in used_queries:
                    continue
                candidates = [p for p in pool if p[identity] != query[identity]]
                demos, shape_report = select_demonstrations(
                    candidates, query["input"], randomizer, profile, identity
                )
                if demos is None:
                    rejected["insufficient_demo_identities"] += 1
                    continue
                # Preserve the family's demonstrated shape pattern; do not
                # silently fall back to unrelated demo dimensions.
                if not shape_report["matched"]:
                    rejected["shape_pattern_unavailable"] += 1
                    continue
                palette = list(range(10))
                randomizer.shuffle(palette)
                d4 = randomizer.randrange(8)
                four = [*demos, query]
                values = [
                    {k: transformed(p[k], d4, palette) for k in ("input", "output")} for p in four
                ]
                eid = f"diversity-v1-{tid}-{split}-{counts[split]:05d}"
                ep = {
                    "episode_id": eid,
                    "task_id": tid,
                    "train": values[:3],
                    "test": [{"input": values[3]["input"]}],
                    "solutions": [values[3]["output"]],
                    "d4_transform": d4,
                    "color_permutation": palette,
                }
                try:
                    record = make_record(
                        ep,
                        source_repo="ritwikareddykancharla/ARC-GEN",
                        source_revision=options["source_signature"],
                    )
                    record.update(
                        split=split,
                        file_name=eid + ".png",
                        pair_provenance=[
                            {
                                k: p.get(k)
                                for k in (
                                    "seed",
                                    "generator_mode",
                                    "input_hash",
                                    "canonical_input_hash",
                                    "source_colour_map",
                                )
                            }
                            for p in four
                        ],
                        shape_policy=shape_report,
                        image_usage="Human audit only; includes the query answer.",
                    )
                    image = folder / record["file_name"]
                    render(record).save(image, format="PNG", compress_level=3)
                    stream.write(json.dumps(record, separators=(",", ":")) + "\n")
                    paths.append(image)
                    counts[split] += 1
                    used_queries.add(query[identity])
                    shape_patterns[digest(shape_report["observed"])] += 1
                except Exception as exc:
                    rejected["episode:" + type(exc).__name__ + ":" + str(exc)[:120]] += 1
        final = folder / "metadata.jsonl"
        pending.replace(final)
        paths.append(final)
    report = {
        "task_id": tid,
        "counts": dict(counts),
        "requested": {s: options[s] for s in pools},
        "pool_counts": {s: len(p) for s, p in pools.items()},
        "pool_sources": dict(sources),
        "rejections": dict(rejected),
        "seconds": round(time.monotonic() - started, 2),
        "complete": all(counts[s] == options[s] for s in pools),
        "file_sha256": {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
        },
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--train", type=int, default=200)
    parser.add_argument("--validation", type=int, default=20)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--seconds", type=int, default=180)
    parser.add_argument("--seed", type=int, default=2026102401)
    parser.add_argument("--tasks", nargs="+")
    args = parser.parse_args()
    ids = sorted(set(admission()["admitted"]) | set(REPAIRED))
    if args.tasks:
        if not set(args.tasks) <= set(ids):
            raise ValueError("Only reviewed supplement families are supported")
        ids = sorted(args.tasks)
    root = Path(args.out)
    root.mkdir(parents=True, exist_ok=True)
    (root / "reports").mkdir(exist_ok=True)
    files = list(BASE.rglob("*.py")) + list((BASE / "diversity").glob("*.json"))
    files += [BASE.parent / "tasks" / ("task_" + tid + ".py") for tid in ids]
    files.append(BASE.parent / "common.py")
    for tid in ids:
        files.append(BASE / "references" / (tid + ".json"))
        files += [
            p
            for p in (
                BASE / "direct_factories" / (tid + ".json"),
                BASE / "reports/direct-certificates" / (tid + ".json"),
            )
            if p.exists()
        ]
    signature = digest(
        {
            str(p.relative_to(BASE.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)
        }
    )
    options = dict(
        vars(args), source_signature=signature, global_split_policy=POLICY_SIGNATURE, task_ids=ids
    )
    config = root / "config.json"
    if config.exists() and json.loads(config.read_text()) != options:
        raise ValueError("Use a fresh output directory: source or requested dataset changed")
    config.write_text(json.dumps(options, indent=2) + "\n")
    reports = []
    with ProcessPoolExecutor(args.workers) as pool:
        futures = {pool.submit(prepare, (tid, options)): tid for tid in ids}
        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as exc:
                result = {"task_id": futures[future], "complete": False, "error": repr(exc)}
            reports.append(result)
            print(
                json.dumps(
                    {
                        k: v
                        for k, v in result.items()
                        if k in ("task_id", "counts", "complete", "error")
                    }
                ),
                flush=True,
            )
            manifest = {
                "kind": "expanded-domain supplement; not full 1120-family release",
                "source_signature": signature,
                "requested_families": len(ids),
                "completed_families": len(reports),
                "quota_complete_families": sum(r["complete"] for r in reports),
                "counts": {
                    s: sum(r.get("counts", {}).get(s, 0) for r in reports)
                    for s in ("train", "validation")
                },
                "reports": [{k: v for k, v in r.items() if k != "file_sha256"} for r in reports],
            }
            (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
