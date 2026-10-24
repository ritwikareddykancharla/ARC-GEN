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
  * review_history.json  (superseded reviews; each entry is checked against git:
    verbatim review text at its commits, constructor hash at its source commits,
    and the mechanical record it was written against)

Every reviewed record must also bind to the constructor at its own
baseline_commit, not only to the current file.

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
# Batches whose every family must carry a hand-written, current semantic review.
# All other batches must stay "pending". Coverage need not be consecutive:
# batch 22 was reviewed ahead of batches 7..21, which remain pending.
REVIEWED_BATCHES = (1, 2, 3, 4, 5, 6, 22)

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


def load_history():
    p = HERE / "review_history.json"
    return json.loads(p.read_text())["history"] if p.exists() else {}


def git_blob(commit, path):
    """Bytes of path at commit, or None if absent."""
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{path}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def check_history(reviews, history, recs):
    """Superseded reviews must be verbatim, source-bound and linked from a current rereview."""
    errs = []
    cur = {r["task_id"]: r["source"]["sha256"] for r in recs}
    review_rel = rel(HERE / "semantic_reviews.json")
    inventory_rel = rel(HERE / "inventory.jsonl")
    for tid, entries in sorted(history.items()):
        rv = reviews.get(tid)
        if not entries or rv is None or "supersedes" not in rv:
            errs.append(f"{tid}: history without a current superseding review")
            continue
        sup = rv["supersedes"]
        idx = sup.get("history_index")
        if not isinstance(idx, int) or not 0 <= idx < len(entries) or idx != len(entries) - 1:
            errs.append(f"{tid}: supersedes.history_index does not point at the latest history entry")
            continue
        if entries[idx]["review"].get("constructor_sha256") != sup.get("constructor_sha256"):
            errs.append(f"{tid}: supersedes.constructor_sha256 does not match the history entry")
        for n, e in enumerate(entries):
            old, sb = e["review"], e["source_binding"]
            if old.get("status") != "reviewed" or old.get("constructor_sha256") == cur[tid]:
                errs.append(f"{tid}: history[{n}] is not a superseded reviewed record")
            if sb["constructor_sha256"] != old.get("constructor_sha256"):
                errs.append(f"{tid}: history[{n}] source binding disagrees with its review")
            for c in (sb["verified_at_commit"], sb["last_commit_with_this_source"]):
                b = git_blob(c, sb["path"])
                if b is None or sha(b) != sb["constructor_sha256"]:
                    errs.append(f"{tid}: history[{n}] constructor hash not found at {c}")
            b = git_blob(sb["replaced_by_commit"], sb["path"])
            if b is None or sha(b) == sb["constructor_sha256"]:
                errs.append(f"{tid}: history[{n}] replaced_by_commit does not change the constructor")
            # The replacing commit must be the one that made the change (its parent still
            # holds the reviewed source) and must hold the recorded replacement source.
            if sb["last_commit_with_this_source"] != sb["replaced_by_commit"] + "^":
                errs.append(f"{tid}: history[{n}] last_commit_with_this_source is not replaced_by_commit^")
            if b is None or sha(b) != sb.get("replacement_constructor_sha256"):
                errs.append(f"{tid}: history[{n}] replacement_constructor_sha256 is not the source at replaced_by_commit")
            for c in (e["first_committed_in"], e["archived_from_commit"]):
                b = git_blob(c, review_rel)
                if b is None or json.loads(b)["reviews"].get(tid) != old:
                    errs.append(f"{tid}: history[{n}] review is not verbatim at {c}")
            b = git_blob(e["first_committed_in"], inventory_rel)
            mech = None
            for line in (b or b"").decode().splitlines():
                r = json.loads(line)
                if r["task_id"] == tid:
                    r.pop("semantic_review", None)
                    mech = r
            if mech is None or mech != e.get("mechanical_record_at_review"):
                errs.append(f"{tid}: history[{n}] mechanical record differs from {e['first_committed_in'][:7]}")
    for tid, rv in reviews.items():
        if ("supersedes" in rv or rv.get("review_kind") == "rereview_after_native_repair") \
                and tid not in history:
            errs.append(f"{tid}: rereview without preserved history")
    return errs


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
    history = load_history()
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
        # Superseded reviews live in review_history.json; only their count is copied here.
        r["semantic_review_history"] = len(history.get(r["task_id"], []))
    meta = {"baseline_commit": head, "ordering_commit": ordering,
            "audit_fork_commit": json.loads((AUDIT / "provenance.json").read_text())["fork_commit"],
            "worklist": str(WORKLIST), "audit_dir": str(AUDIT),
            "families": len(recs), "batch_size": BATCH,
            "note": "mechanical fields are extraction, not semantic review; release_ready is never set",
            "certified_evidence_basis": "current = some certificate's constructor sha256 (and factory sha256 for "
                                        "direct factories) equals the current file; direct-source program hashes are "
                                        "not rebuilt here; a certificate is a finite audit, not a proof"}
    return meta, recs, ids


def next_pending_batch(batch_numbers, reviewed):
    """First batch in the fixed batch order that is not reviewed, or None.

    Reviewed coverage may have holes (for example 1..6 and 22), so the next
    batch is the lowest unreviewed number, not max(reviewed) + 1.
    """
    for b in sorted(batch_numbers):
        if b not in reviewed:
            return b
    return None


def check_next_batch_selector(recs):
    """Focused check of next_pending_batch on fixed cases and on the inventory."""
    errs = []
    cases = [((1, 2, 3, 4, 5, 6, 22), 7), (tuple(range(1, 24)), None), ((), 1),
             ((2,), 1), ((1, 2, 3), 4), ((1, 2, 3, 4, 5, 6), 7)]
    for reviewed, want in cases:
        got = next_pending_batch(range(1, 24), reviewed)
        if got != want:
            errs.append(f"next_pending_batch({reviewed}) = {got}, expected {want}")
    numbers = sorted({r["priority"]["batch"] for r in recs})
    nb = next_pending_batch(numbers, REVIEWED_BATCHES)
    if nb is not None and (nb in REVIEWED_BATCHES
                           or any(b not in REVIEWED_BATCHES for b in numbers if b < nb)):
        errs.append(f"next pending batch {nb} is not the first unreviewed batch")
    return errs


def check(meta, recs, ids):
    errs = []
    errs += check_next_batch_selector(recs)
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
    reviewed_scope = [r for r in recs if r["priority"]["batch"] in REVIEWED_BATCHES]
    for r in reviewed_scope:
        sr = r["semantic_review"]
        tid = r["task_id"]
        if sr.get("status") != "reviewed":
            errs.append(f"{tid}: batch-{r['priority']['batch']} record not reviewed ({sr.get('status')})")
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
        # Source binding: the reviewed constructor must be the one at the review's baseline.
        b = git_blob(sr.get("baseline_commit", ""), r["source"]["path"])
        if b is None or sha(b) != sr["constructor_sha256"]:
            errs.append(f"{tid}: constructor_sha256 is not the source at baseline_commit")
        if sr.get("review_kind") == "rereview_after_native_repair":
            rd = sr.get("repair_delta", {})
            if any(len(str(rd.get(k, ""))) < 4 for k in ("expanded", "retained", "unsolved")):
                errs.append(f"{tid}: rereview repair_delta incomplete")
            if sr.get("review_batch") != r["priority"]["batch"]:
                errs.append(f"{tid}: rereview review_batch disagrees with inventory batch")
            if git_blob(sr.get("repair_commit", ""), r["source"]["path"]) is None:
                errs.append(f"{tid}: rereview repair_commit missing")
            for ev in sr.get("evidence") or [None]:
                p = str(ev).split(" (")[0]
                if not ((HERE / p).exists() if p.startswith("probes/") else (ROOT / p).exists()):
                    errs.append(f"{tid}: rereview evidence path missing: {ev}")
    reviews = json.loads((HERE / "semantic_reviews.json").read_text())["reviews"]
    errs += check_history(reviews, load_history(), recs)
    others = [r for r in recs if r["priority"]["batch"] not in REVIEWED_BATCHES]
    for r in others:
        if r["semantic_review"]["status"] != "pending":
            errs.append(f"{r['task_id']}: record outside reviewed batches is not pending")
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
        "reviewed_batches": list(REVIEWED_BATCHES),
        "rereviewed_ids": [r["task_id"] for r in rev
                           if r["semantic_review"].get("review_kind") == "rereview_after_native_repair"],
        "review_history_ids": [r["task_id"] for r in recs if r["semantic_review_history"]],
        "stale_reviewed_constructors": [r["task_id"] for r in recs
                                        if r["semantic_review"]["status"] == "stale"],
        "pending_batches": [b for b in batches if b not in REVIEWED_BATCHES],
        "next_batch_number": next_pending_batch(batches, REVIEWED_BATCHES),
        "next_batch": batches.get(next_pending_batch(batches, REVIEWED_BATCHES), []),
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
