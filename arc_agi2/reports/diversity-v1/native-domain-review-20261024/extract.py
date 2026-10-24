"""Mechanical inventory and semantic-review merge for the 729 no-RE-ARC families.

Mechanical extraction is NOT semantic review.  Every record carries
``semantic_review.status == "pending"`` unless a hand-written review exists in
``semantic_reviews.json`` and that review is bound to the current constructor
sha256.  A review whose constructor has since changed is reported as ``stale``.

Usage (from the worktree root)::

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-domain-review-20261024/extract.py
    PYTHONPATH=. python .../extract.py --check     # validate only, no writes

Inputs (read only):
  * docs/hybrid-generator-review/family-worklist.json  (rearc_overlap=false selects 729)
  * output/generator-domain-audit-20261024/families/<id>.json  (128-sample audit, fork cdf50ed)
  * tasks/task_<id>.py at the worktree HEAD (constructor source)
  * arc_agi2.runtime.reference(id)["canonical"]  (original public fixture)
  * certificate records: arc_agi2/direct_factories/<id>.json,
    arc_agi2/reports/direct-certificates/<id>.json,
    arc_agi2/reports/diversity-v1/native-certificates/<id>.json

Batch order is pinned to ORDERING_COMMIT so that later constructor edits do not
reshuffle batches.  Tier A = audit-sampled input height and width both fixed and
>= 8 (constructor unchanged since the audit first, then audit-stale ones); tier B
= every other family, least sampled shape variety first.
"""
import argparse
import ast
import collections
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]  # worktree root
MAIN = Path("/Users/ritwika/projects/arc-agi2")
WORKLIST = MAIN / "docs/hybrid-generator-review/family-worklist.json"
AUDIT = MAIN / "output/generator-domain-audit-20261024"
ORDERING_COMMIT = "5436f3fe035f261cdcf7996565c108148efa37fb"
BATCH = 32
MAX_CONSTRAINTS = 28

CERT_DIRS = {
    "direct_factory": ROOT / "arc_agi2/direct_factories",
    "direct_certificate": ROOT / "arc_agi2/reports/direct-certificates",
    "native_certificate": ROOT / "arc_agi2/reports/diversity-v1/native-certificates",
}

RANDOM_CALLS = {
    "randint", "randints", "choice", "choices", "sample", "shuffle", "random",
    "random_color", "random_colors", "random_pixels", "uniform", "randrange",
}
AXES = ["dimensions", "objects", "placement", "density_colours",
        "rule_parameters", "demonstration_context"]
DISPOSITIONS = {"incidental_restriction", "intrinsic_or_rule_supported", "mixed",
                "broadly_variable", "unknown"}
EVIDENCE_STATES = {"current", "stale", "unavailable"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                          capture_output=True).stdout


def rel(p):
    return str(Path(p).resolve().relative_to(ROOT))


def call_name(node):
    f = node.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return None


def generate_constraints(src):
    """Line-numbered generate() lines that draw, allocate, loop or guard."""
    tree = ast.parse(src)
    gen = next((n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == "generate"), None)
    if gen is None:
        return None
    lines = src.splitlines()
    kinds = collections.defaultdict(set)
    for node in ast.walk(gen):
        ln = getattr(node, "lineno", None)
        if ln is None:
            continue
        if isinstance(node, ast.Call):
            name = call_name(node)
            if name in ("grid", "grids"):
                kinds[ln].add("canvas")
            elif name in RANDOM_CALLS or (name or "").endswith("_sprite"):
                kinds[ln].add("draw")
        elif isinstance(node, ast.While):
            kinds[ln].add("loop")
        elif isinstance(node, (ast.Raise, ast.Assert)):
            kinds[ln].add("guard")
        elif isinstance(node, ast.Return) and isinstance(node.value, ast.Constant) \
                and node.value.value is None:
            kinds[ln].add("reject")
        elif isinstance(node, ast.Continue):
            kinds[ln].add("retry")
    params = []
    a = gen.args
    defaults = [None] * (len(a.args) - len(a.defaults)) + list(a.defaults)
    for arg, d in zip(a.args, defaults):
        params.append(arg.arg if d is None else f"{arg.arg}={ast.unparse(d)}")
    out = [{"line": ln, "kind": sorted(k),
            "text": lines[ln - 1].strip()[:140]} for ln, k in sorted(kinds.items())]
    return {
        "start_line": gen.lineno, "end_line": gen.end_lineno,
        "body_lines": gen.end_lineno - gen.lineno + 1,
        "parameters": params,
        "constraint_lines_total": len(out),
        "constraints": out[:MAX_CONSTRAINTS],
        "kind_counts": dict(collections.Counter(k for r in out for k in r["kind"])),
    }


def span(v):
    return v if v is None else [v[0], v[1]]


def audit_summary(a, current_sha):
    def side(s):
        if not s or "input" not in s:
            return None
        i, o = s["input"], s["output"]
        return {
            "requested": s.get("requested"),
            "valid": s.get("valid"), "attempted": s.get("attempted"),
            "errors": len(s.get("errors", [])),
            "seconds": s.get("seconds"),
            # fewer valid draws than requested: time budget or timeouts, so
            # the sampled ranges below may describe very few scenes
            "sample_shortfall": (s.get("valid") or 0) < (s.get("requested") or 0),
            "input_h": span(i["height"]), "input_w": span(i["width"]),
            "input_shapes": len(i["shapes"]),
            "rect_rate": i["rectangular_rate"],
            "colour_count": span(i["colour_count"]),
            "nonmodal_fraction": span(i["nonmodal_fraction"]),
            "components": span(i["nonmodal_monochrome_components"]),
            "output_h": span(o["height"]), "output_w": span(o["width"]),
            "output_shapes": len(o["shapes"]),
            "unique_inputs": s.get("unique_inputs"),
            "unique_input_orbits": s.get("unique_input_orbits"),
            "shape_relation": s.get("shape_relation"),
        }
    return {
        "audit_source_sha256": a["source"]["sha256"],
        "audit_matches_current_source": a["source"]["sha256"] == current_sha,
        "legacy_extension_available": a.get("legacy_extension_available"),
        "native": side(a.get("native")),
        "configured": side(a.get("configured")),
    }


def fixture_summary(ref):
    can = ref["canonical"]
    def shp(g):
        return f"{len(g)}x{len(g[0])}"
    pairs = [("train", p) for p in can["train"]] + [("test", p) for p in can["test"]]
    cols = sorted({c for _, p in pairs for row in p["input"] for c in row})
    return {
        "train": len(can["train"]), "test": len(can["test"]),
        "input_shapes": [shp(p["input"]) for _, p in pairs],
        "output_shapes": [shp(p["output"]) for _, p in pairs],
        "input_colours": cols,
    }


def certificates(tid, current_sha):
    out = []
    for kind, folder in CERT_DIRS.items():
        p = folder / f"{tid}.json"
        if not p.exists():
            continue
        r = json.loads(p.read_text())
        rec = {"kind": kind, "path": rel(p), "passed": r.get("passed"),
               "constructor_sha256_matches": r.get("constructor_sha256") == current_sha}
        if kind == "direct_factory":
            fp = folder / f"task_{tid}.py"
            rec["factory_sha256_matches"] = fp.exists() and sha(fp.read_bytes()) == r.get("factory_sha256")
        out.append(rec)
    state = "unavailable"
    if out:
        ok = [c for c in out if c["constructor_sha256_matches"]
              and c.get("factory_sha256_matches", True)]
        state = "current" if ok else "stale"
    return state, out


def factory_info(tid):
    p = CERT_DIRS["direct_factory"] / f"task_{tid}.py"
    if not p.exists():
        return None
    src = p.read_text()
    # mechanical lead only: does the emitted program body mention demonstrations
    body_mentions = src.count("demonstrations") - src.count("def solve(demonstrations")
    return {"path": rel(p), "sha256": sha(src.encode()),
            "references_demonstrations_beyond_signature": body_mentions > 0}


def tier_key(rec, ordering_sha):
    n = rec["audit"]["native"]
    h, w = n["input_h"], n["input_w"]
    fixed = h[0] == h[1] and w[0] == w[1]
    if fixed and h[0] >= 8 and w[0] >= 8:
        unchanged = rec["_ordering_sha"] == rec["audit"]["audit_source_sha256"]
        return (0, 0 if unchanged else 1, rec["task_id"])
    one_fixed = h[0] == h[1] or w[0] == w[1]
    return (1, 0 if fixed else (1 if one_fixed else 2), n["input_shapes"], rec["task_id"])


def build():
    wl = json.loads(WORKLIST.read_text())
    ids = sorted(f["task_id"] for f in wl["families"] if f["rearc_overlap"] is False)
    wlmap = {f["task_id"]: f for f in wl["families"]}
    head = git("rev-parse", "HEAD").decode().strip()
    ordering = git("rev-parse", ORDERING_COMMIT).decode().strip()
    dirty = set(git("status", "--porcelain", "--", "tasks").decode().split()[1::2])
    sys.path.insert(0, str(ROOT))
    from arc_agi2 import runtime
    reviews = json.loads((HERE / "semantic_reviews.json").read_text())["reviews"]
    recs = []
    for tid in ids:
        path = ROOT / "tasks" / f"task_{tid}.py"
        data = path.read_bytes()
        cur = sha(data)
        ordering_sha = sha(git("show", f"{ordering}:tasks/task_{tid}.py"))
        a = json.loads((AUDIT / "families" / f"{tid}.json").read_text())
        state, certs = certificates(tid, cur)
        w = wlmap[tid]
        rec = {
            "task_id": tid,
            "source": {"path": rel(path), "sha256": cur,
                       "lines": len(data.decode().splitlines()),
                       "uncommitted_change": rel(path) in dirty},
            "generate": generate_constraints(data.decode()),
            "audit": audit_summary(a, cur),
            "fixture": fixture_summary(runtime.reference(tid)),
            "certified_evidence": {"state": state, "records": certs},
            "factory": factory_info(tid),
            "worklist": {"native_repaired": w["native_repaired"],
                         "pending_checks": w["pending_checks"]},
            "release_ready": False,
            "_ordering_sha": ordering_sha,
        }
        recs.append(rec)
    recs.sort(key=lambda r: tier_key(r, ordering))
    for i, r in enumerate(recs):
        n = r["audit"]["native"]
        fixed8 = tier_key(r, ordering)[0] == 0
        r["priority"] = {"rank": i + 1, "batch": i // BATCH + 1,
                         "tier": "A_fixed_dims_ge8" if fixed8 else "B_other",
                         "audit_stale_at_ordering_commit":
                             r["_ordering_sha"] != r["audit"]["audit_source_sha256"]}
        del r["_ordering_sha"]
        rv = reviews.get(r["task_id"])
        if rv is None:
            r["semantic_review"] = {"status": "pending"}
        else:
            rv = dict(rv)
            if rv["constructor_sha256"] != r["source"]["sha256"]:
                rv["status"] = "stale"
            r["semantic_review"] = rv
    meta = {"baseline_commit": head, "ordering_commit": ordering,
            "audit_fork_commit": json.loads((AUDIT / "provenance.json").read_text())["fork_commit"],
            "worklist": str(WORKLIST), "audit_dir": str(AUDIT),
            "families": len(recs), "batch_size": BATCH,
            "note": "mechanical fields are extraction, not semantic review; release_ready is never set",
            "certified_evidence_basis": "current = some certificate's constructor sha256 (and factory sha256 for "
                                        "direct factories) equals the current file; direct-source program hashes are "
                                        "not rebuilt here; a certificate is a finite audit, not a proof"}
    return meta, recs, ids


def check(meta, recs, ids):
    errs = []
    got = [r["task_id"] for r in recs]
    if len(got) != 729 or len(set(got)) != 729 or sorted(got) != ids:
        errs.append("inventory ids do not equal the 729 expected ids")
    from arc_agi2 import runtime
    for r in recs:
        p = ROOT / r["source"]["path"]
        if not p.exists() or sha(p.read_bytes()) != r["source"]["sha256"]:
            errs.append(f"{r['task_id']}: source hash mismatch")
        can = runtime.reference(r["task_id"])["canonical"]
        if (len(can["train"]), len(can["test"])) != (r["fixture"]["train"], r["fixture"]["test"]):
            errs.append(f"{r['task_id']}: fixture counts")
        if r["release_ready"] is not False:
            errs.append(f"{r['task_id']}: release_ready set")
    first = [r for r in recs if r["priority"]["batch"] == 1]
    for r in first:
        sr = r["semantic_review"]
        tid = r["task_id"]
        if sr.get("status") != "reviewed":
            errs.append(f"{tid}: batch-1 record not reviewed ({sr.get('status')})")
            continue
        lines = (ROOT / r["source"]["path"]).read_text().splitlines()
        for ax in AXES:
            a = sr.get("axes", {}).get(ax)
            if not a or a.get("disposition") not in DISPOSITIONS or len(a.get("why", "")) < 40:
                errs.append(f"{tid}: axis {ax} incomplete")
                continue
            if a["disposition"] != "unknown" and not a.get("lines"):
                errs.append(f"{tid}: axis {ax} has no line refs")
            for ln in a.get("lines", []):
                if not (1 <= ln <= len(lines)) or not lines[ln - 1].strip():
                    errs.append(f"{tid}: axis {ax} bad line {ln}")
        for k in ("mechanism", "proposal", "uncertainties", "fixture_evidence"):
            if len(str(sr.get(k, ""))) < 30:
                errs.append(f"{tid}: {k} missing")
        if sr.get("certified_evidence") not in EVIDENCE_STATES or \
                sr["certified_evidence"] != r["certified_evidence"]["state"]:
            errs.append(f"{tid}: certified_evidence disagrees with mechanical state")
    others = [r for r in recs if r["priority"]["batch"] != 1]
    if any(r["semantic_review"]["status"] != "pending" for r in others):
        errs.append("a non-batch-1 record is not pending")
    return errs


def summarise(meta, recs):
    rev = [r for r in recs if r["semantic_review"]["status"] == "reviewed"]
    disp = {ax: dict(collections.Counter(r["semantic_review"]["axes"][ax]["disposition"]
                                         for r in rev)) for ax in AXES}
    batches = collections.OrderedDict()
    for r in recs:
        batches.setdefault(r["priority"]["batch"], []).append(r["task_id"])
    return {
        **meta,
        "semantic_status": dict(collections.Counter(r["semantic_review"]["status"] for r in recs)),
        "tiers": dict(collections.Counter(r["priority"]["tier"] for r in recs)),
        "certified_evidence": dict(collections.Counter(r["certified_evidence"]["state"] for r in recs)),
        "audit_matches_current_source": sum(r["audit"]["audit_matches_current_source"] for r in recs),
        "audit_stale_ids": [r["task_id"] for r in recs if not r["audit"]["audit_matches_current_source"]],
        "certified_unavailable_ids": [r["task_id"] for r in recs if r["certified_evidence"]["state"] == "unavailable"],
        "audit_native_sample_shortfall_ids": [r["task_id"] for r in recs if r["audit"]["native"]["sample_shortfall"]],
        "reviewed_patch_priority_ids": {p: [r["task_id"] for r in rev if r["semantic_review"]["patch_priority"] == p]
                                        for p in ("high", "medium", "low", "none")},
        "reviewed_axis_dispositions": disp,
        "reviewed_patch_priority": dict(collections.Counter(r["semantic_review"]["patch_priority"] for r in rev)),
        "next_batch": batches.get(2, []),
        "batches": {str(k): v for k, v in batches.items()},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate without writing")
    args = ap.parse_args()
    meta, recs, ids = build()
    errs = check(meta, recs, ids)
    if not args.check:
        with open(HERE / "inventory.jsonl", "w") as f:
            for r in recs:
                f.write(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n")
        summary = summarise(meta, recs)
        summary["validation_errors"] = errs
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    for e in errs:
        print("ERROR", e)
    print(f"{len(recs)} records; {len(errs)} validation errors")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
