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
from functools import lru_cache

from ..augmentation import transformed
from ..episode_shape_policy import profile_from_task, select_demonstrations
from ..finite_input_policy import POLICY_SIGNATURE, identity_key, input_split
from ..program_targets import make_record
from ..runtime import BASE, call, grid, reference, verification_solver
from ..visual_dataset import render
from .sampler import admission, eligible, sample_checked

REPAIRED = ("007bbfb7", "009d5c81", "00dbd492", "0934a4d8", "09c534e7", "1e0a9b12", "3194b014",
            "3a301edc", "45bbe264", "aaecdb9a", "ecb67b6d", "feca6190",
            # Native domain expansion A (reports/diversity-v1/native-domain-expansion-20261024).
            "137f0df0", "31adaf00", "84db8fc4", "a406ac07", "ce039d91", "d282b262", "f45f5ca7",
            # Native batch B (reports/diversity-v1/native-batch-b-domains.json).
            "03560426", "0becf7df", "0f63c0b9", "14b8e18c", "21f83797", "2685904e", "2a28add5",
            # Native batch C: orientation and rectangular domain coverage.
            "7e2bad24", "7e576d6e", "94414823", "50c07299",
            # Native batch D: rectangular panel domains with context evidence gates.
            "195ba7dc", "281123b4", "31d5ba1a", "34b99a2b")

# Reviewed adequate existing domains, not constructor expansions. Each has a
# current semantic review and fresh 1000/8000/16 native recertification.
REVIEWED_NATIVE = ("981571dc", "dc2aa30b")


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


# A query identity that keeps failing (demonstration, colour-evidence or
# program checks) is retired after this many attempts, so a fixed attempt
# budget is not consumed by one permanently invalid query.
MAX_QUERY_FAILURES = 8
# Pool sampling may continue up to this multiple of the base trial budget, but
# only while some split lacks strict shape-compatible query support and the
# pool time share remains. Every extra proposal passes the same checks.
POOL_EXTENSION_FACTOR = 4
SHORTFALL_NOTE = (
    "Observed bounded-pool shortfall under the strict shape/orbit policy; "
    "not a finite-capacity claim about the source domain."
)


def _shape(g):
    return (len(g), len(g[0]))


def _possible(groups, all_ids, shape, qid, pattern):
    """Exact strict shape-pattern feasibility for one (query shape, identity).

    Equivalent to checking groups with qid removed, without copying sets.
    The query row itself is in the pool, so qid is always in groups[shape].
    """
    def others(ids):
        return len(ids) - (qid in ids)

    uniform = pattern["demo_input_shapes"] == "uniform"
    seen = pattern["query_input_shape"] == "seen"
    if uniform:
        if seen:
            return others(groups[shape]) >= 3
        return any(s != shape and others(ids) >= 3 for s, ids in groups.items())
    if seen:
        return (
            others(all_ids) >= 3
            and others(groups[shape]) >= 1
            and any(s != shape and others(ids) >= 1 for s, ids in groups.items())
        )
    nonempty, union = 0, set()
    for s, ids in groups.items():
        if s == shape or not others(ids):
            continue
        nonempty += 1
        union.update(ids)
        union.discard(qid)
        if nonempty >= 2 and len(union) >= 3:
            return True
    return False


def query_support(pool, profile, identity):
    """Map each strictly feasible query identity to its feasible pool rows.

    Inputs only; outputs are never inspected. A query is feasible when at least
    one original shape pattern could be matched with three other identities.
    Iteration follows pool order, so results do not depend on hash seeds.
    """
    groups = defaultdict(set)
    for p in pool:
        groups[_shape(p["input"])].add(p[identity])
    all_ids = set().union(*groups.values()) if groups else set()
    memo, support = {}, {}
    for query in pool:
        key = (_shape(query["input"]), query[identity])
        if key not in memo:
            memo[key] = any(
                _possible(groups, all_ids, key[0], key[1], pattern)
                for pattern in profile["patterns"]
            )
        if memo[key]:
            support.setdefault(key[1], []).append(query)
    return support


def feasible_queries(pool, profile, identity):
    """Find query rows with enough distinct shape-compatible context."""
    rows = {id(p) for ps in query_support(pool, profile, identity).values() for p in ps}
    return [p for p in pool if id(p) in rows]


def repeated_strip_colour(pair):
    cells = [c for row in pair['input'] for c in row if c != 0]
    return len(cells) > len(set(cells))


def evidence_query_support(tid, pool, profile, identity):
    """Count strip queries only when their required repeated-colour demo exists.

    This is an input-only sampling constraint, before shared episode transforms.
    make_record still verifies the actual evidence and all program outputs.
    """
    support = query_support(pool, profile, identity)
    if tid != 'feca6190':
        return support
    expected = {'demo_input_shapes': 'uniform', 'query_input_shape': 'seen'}
    if any(p != expected for p in profile['patterns']):
        raise ValueError('Re-review strip evidence sampling for changed shape profile')
    witnesses = defaultdict(set)
    for pair in pool:
        if repeated_strip_colour(pair):
            witnesses[_shape(pair['input'])].add(pair[identity])
    filtered = {}
    for qid, queries in support.items():
        viable = [q for q in queries if not repeated_strip_colour(q)
                  or witnesses[_shape(q['input'])] - {qid}]
        if viable:
            filtered[qid] = viable
    return filtered


def select_task_demonstrations(tid, candidates, query, randomizer, profile, identity):
    demos, report = select_demonstrations(candidates, query['input'], randomizer,
                                           profile, identity)
    if tid == 'feca6190' and demos and report['matched'] and repeated_strip_colour(query):
        if not any(repeated_strip_colour(p) for p in demos):
            # Preserve the original uniform/seen shape pattern and distinct IDs.
            kept_ids = {p[identity] for p in demos[1:]} | {query[identity]}
            witnesses = [p for p in candidates if p[identity] not in kept_ids
                         and _shape(p['input']) == _shape(query['input'])
                         and repeated_strip_colour(p)]
            if witnesses:
                demos[0] = randomizer.choice(witnesses)
                randomizer.shuffle(demos)
    return demos, report


def assemble_split(pool, profile, identity, quota, randomizer, emit, attempts, deadline,
                   rejected, split, task_id=None):
    """Emit up to quota episodes, one per distinct query identity.

    Query identities, not exact rows, are drawn uniformly, so identities with
    many exact rows cannot starve rare ones. A query identity is retired after
    MAX_QUERY_FAILURES failed attempts. The original shape pattern is strict:
    demonstrations that do not match it are rejected, never used. emit(demos,
    query, shape_report) must perform all semantic/program checks and raise on
    failure. Returns (produced, stats).
    """
    support = evidence_query_support(task_id, pool, profile, identity)
    remaining = list(support)
    failures = Counter()
    stats = {
        "pool_rows": len(pool),
        "pool_identities": len({p[identity] for p in pool}),
        "shape_bins": len({_shape(p["input"]) for p in pool}),
        "feasible_query_identities": len(support),
        "used_query_identities": 0,
        "retired_query_identities": 0,
        "attempts": 0,
    }
    produced, stop = 0, None
    if len(pool) < 4 or not remaining:
        rejected[split + ":no_shape_compatible_distinct_query_context"] += 1
    while produced < quota:
        if not remaining:
            stop = ("query_identities_retired_after_bounded_failures"
                    if stats["retired_query_identities"] else "bounded_pool_query_support")
            break
        if stats["attempts"] >= attempts:
            stop = "attempt_budget"
            break
        if time.monotonic() > deadline:
            stop = "time_budget"
            break
        stats["attempts"] += 1
        qid = randomizer.choice(remaining)
        query = randomizer.choice(support[qid])
        candidates = [p for p in pool if p[identity] != qid]
        demos, shape_report = select_task_demonstrations(
            task_id, candidates, query, randomizer, profile, identity)
        failure = None
        if demos is None:
            failure = "insufficient_demo_identities"
        elif not shape_report["matched"]:
            # Preserve the family's demonstrated shape pattern; do not
            # silently fall back to unrelated demo dimensions.
            failure = "shape_pattern_unavailable"
        else:
            try:
                emit(demos, query, shape_report)
            except Exception as exc:
                failure = "episode:" + type(exc).__name__ + ":" + str(exc)[:120]
        if failure is None:
            produced += 1
            remaining.remove(qid)
            stats["used_query_identities"] += 1
            continue
        rejected[failure] += 1
        failures[qid] += 1
        if failures[qid] >= MAX_QUERY_FAILURES:
            remaining.remove(qid)
            stats["retired_query_identities"] += 1
    if produced < quota:
        stats["shortfall"] = {"requested": quota, "produced": produced, "stop": stop,
                              "note": SHORTFALL_NOTE}
    return produced, stats


@lru_cache(maxsize=4)
def reserved_validation_orbits(path, expected_sha256):
    """Protect validation inputs from previous training stages without relabelling splits."""
    if not path:
        return frozenset()
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Reserved validation orbit ledger changed")
    values = json.loads(raw)
    if not isinstance(values, list) or any(
        not isinstance(x, str) or len(x) != 64 or any(c not in "0123456789abcdef" for c in x)
        for x in values
    ):
        raise ValueError("Expected a JSON list of canonical SHA256 input orbits")
    return frozenset(values)


def prepare(item):
    tid, options = item
    root = Path(options["out"])
    reserved = reserved_validation_orbits(options.get("reserved_validation_orbits"), options.get("reserved_validation_sha256"))
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
    base_trials = target_pool * 40
    margin = {s: max(2, -(-options[s] // 10)) for s in pools}
    pool_stop, pool_trials = "trial_budget", 0
    for trial in range(base_trials * POOL_EXTENSION_FACTOR):
        if time.monotonic() - started > options["seconds"] * 0.6:
            pool_stop = "time_share"
            break
        if trial and trial % 64 == 0 and all(
            len(pools[s]) >= max(40, options[s] * 2) for s in pools
        ):
            # Within the base budget, stop once strict query support has a
            # small margin for evidence failures; beyond it, extend only while
            # some split still lacks support for its requested quota.
            extra = margin if trial < base_trials else dict.fromkeys(pools, 0)
            if all(
                len(evidence_query_support(tid, pools[s], profile, identity)) >= options[s] + extra[s]
                for s in pools
            ):
                pool_stop = "support" if trial < base_trials else "support_after_extension"
                break
        pool_trials += 1
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
            if split == "train" and orbit in reserved:
                rejected["reserved_prior_validation_orbit"] += 1
                continue
            pair.update(
                input_hash=exact, canonical_input_hash=orbit, generator_mode=mode, seed=seed
            )
            pools[split].append(pair)
            sources[mode] += 1
        except Exception as exc:
            rejected["pair:" + type(exc).__name__ + ":" + str(exc)[:120]] += 1
    paths = []
    shape_patterns = Counter()
    support_stats = {}
    for split, pool in pools.items():
        folder = root / split / tid
        folder.mkdir(parents=True, exist_ok=True)
        pending = folder / "metadata.jsonl.tmp"
        with pending.open("w") as stream:

            def emit(demos, query, shape_report, split=split, folder=folder, stream=stream):
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
                # Colour/demonstration evidence and program verification run
                # here; any failure raises and is counted against the query.
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
                shape_patterns[digest(shape_report["observed"])] += 1

            _, support_stats[split] = assemble_split(
                pool, profile, identity, options[split], randomizer, emit,
                attempts=max(100, options[split] * 40),
                deadline=started + options["seconds"],
                rejected=rejected, split=split, task_id=tid,
            )
        final = folder / "metadata.jsonl"
        pending.replace(final)
        paths.append(final)
    report = {
        "task_id": tid,
        "counts": dict(counts),
        "requested": {s: options[s] for s in pools},
        "pool_counts": {s: len(p) for s, p in pools.items()},
        "pool_sources": dict(sources),
        "pool_trials": pool_trials,
        "pool_stop": pool_stop,
        "query_support": support_stats,
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
    parser.add_argument("--reserved-validation-orbits", help="JSON orbit ledger from earlier validation; exclude these inputs from train pools")
    args = parser.parse_args()
    ids = sorted(set(admission()["admitted"]) | set(REPAIRED) | set(REVIEWED_NATIVE))
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
    if args.reserved_validation_orbits:
        ledger = Path(args.reserved_validation_orbits).resolve()
        options["reserved_validation_orbits"] = str(ledger)
        options["reserved_validation_sha256"] = hashlib.sha256(ledger.read_bytes()).hexdigest()
        reserved_validation_orbits(str(ledger), options["reserved_validation_sha256"])
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
