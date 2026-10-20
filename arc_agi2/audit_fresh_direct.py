"""Verify direct-coordinate candidates on fresh generated puzzles and D4/palettes.

Each report is resumable by constructor and program content hash. This audits
programs for the expanded build; it neither trains nor publishes episode counts.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import importlib
import json
from pathlib import Path
import random
import time

from .runtime import BASE, call, grid
from .audit_direct_candidates import candidate
from .augmentation import transformed
from .program_targets import audit_target, verify


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check(args):
    tid, requested, destination = args
    root = Path(destination); path = root / f"{tid}.json"
    module = importlib.import_module("tasks.task_" + tid)
    source, basis = candidate(tid); audit_target(tid, source)
    signature = dict(program_sha256=digest(source.encode()),
        constructor_sha256=digest(Path(module.__file__).read_bytes()),
        samples_requested=requested,
        auditor_sha256=digest(Path(__file__).read_bytes()))
    if path.exists():
        old = json.loads(path.read_text())
        if all(old.get(k)==v for k,v in signature.items()):
            return old
    report = dict(task_id=tid, **signature, passed=False, basis=basis,
        fresh_pairs_checked=0, augmented_pair_checks=0)
    seen = set(); start = time.monotonic()
    try:
        for episode_index in range((requested+3)//4):
            if time.monotonic()-start > 300:
                raise TimeoutError("Family audit exceeded five minutes; incomplete, not accepted")
            seed = int(hashlib.sha256(f"fresh-direct:{tid}:{episode_index}".encode()).hexdigest()[:12],16)
            random.seed(seed)
            report["last_seed"] = seed
            if hasattr(module, "generate_episode"):
                scene = call(module.generate_episode, seconds=5)
                pairs = scene["train"] + scene["test"]
                demos = scene["train"]
                queries = scene["test"]
            else:
                pairs = [call(module.generate, seconds=5) for _ in range(4)]
                demos, queries = pairs[:3], pairs[3:]
            for pair in pairs:
                grid(pair["input"]); grid(pair["output"])
                seen.add(digest(json.dumps(pair["input"]).encode()))
            palette = list(range(10)); random.Random(seed+1).shuffle(palette)
            for d4 in range(8):
                ep = dict(
                    train=[{k:transformed(p[k],d4,palette) for k in ("input","output")} for p in demos],
                    test=[{"input":transformed(p["input"],d4,palette)} for p in queries],
                    solutions=[transformed(p["output"],d4,palette) for p in queries])
                report["last_d4"] = d4
                verify(source,ep,seconds=1)
                report["augmented_pair_checks"] += len(pairs)
            report["fresh_pairs_checked"] += len(pairs)
            if report["fresh_pairs_checked"] >= requested:
                break
        report["passed"] = True
    except Exception as exc:
        report["error"] = type(exc).__name__ + ": " + str(exc)[:600]
        if "ep" in locals():
            (root / f"{tid}-counterexample.json").write_text(json.dumps({
                "seed":report["last_seed"],"d4":report.get("last_d4"),
                "palette":palette,"episode":ep},separators=(",",":"))+"\n")
    report.update(unique_base_inputs=len(seen),seconds=time.monotonic()-start)
    path.write_text(json.dumps(report,indent=2)+"\n")
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--workers",type=int,default=4)
    parser.add_argument("--samples",type=int,default=1000)
    parser.add_argument("--candidates",type=Path,default=BASE/"reports/direct-candidate-audit.json")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    ids=[r["task_id"] for r in json.loads(args.candidates.read_text())["tasks"] if r["passed"]]
    results=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(check,(tid,args.samples,str(args.output))) for tid in ids]
        for future in as_completed(futures):
            result=future.result();results.append(result)
            print(json.dumps({"task_id":result["task_id"],"passed":result["passed"],
                "completed":len(results),"total":len(ids),
                "passed_families":sum(r["passed"] for r in results)}),flush=True)
    summary={"scope":"Fresh generated direct programs with random palettes and all eight D4 transforms; each accepted program requires per-episode verification during dataset generation.",
        "candidates":len(ids),"passed":sum(r["passed"] for r in results),
        "fresh_pairs_checked":sum(r["fresh_pairs_checked"] for r in results),
        "augmented_pair_checks":sum(r["augmented_pair_checks"] for r in results),
        "tasks":sorted(results,key=lambda r:r["task_id"])}
    (args.output/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({k:v for k,v in summary.items() if k!="tasks"}),flush=True)


if __name__=="__main__":
    main()
