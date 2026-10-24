"""Re-review probe for the 4 native batch-E constructors. Read-only, seeded.

Run from the worktree root:
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-domain-review-20261024/probes/rereview_batch_e.py

It adds evidence that the batch-E repair measurements
(native-batch-e/batch-e-evidence.json, context-audit.json) do not contain.
It does not repeat their coverage or context-audit runs.

Sections:
  bindings    - production lookups at the worktree HEAD: certified factory
                source for all 8 D4 transforms, the verification solver kind,
                prepare.REPAIRED membership, the admission pin check, the
                colour-evidence dispatch, and side records that still describe
                the pre-repair constructors (family-status.csv).
  canonical   - validate() against the canonical fixture, the production
                verifier and the d4=0 factory program on every canonical pair;
                then each canonical input's latent parameters against the
                CURRENT random (default) path, read from the source. Explicit
                replay alone does not show that the random path reaches a
                fixture.
  domain      - seeded statistics (seed 0) for restrictions that remain in the
                default sampler. Exact statements are enumerations of the
                source formulas; everything else is a sample statistic.
  competitors - plausible rules that no gate enumerates: f3cdc58f column
                legends by count or first appearance (f3cdc58f has no gate),
                and an f0df5ff0 window rule that also overwrites confetti.
                Contexts are 3 demonstrations plus a query at one shape, as in
                the strict same-shape production profile. Counts are in native
                coordinates; each competitor is defined from colours and counts
                only (or row-major order, noted), so palette permutation does
                not change whether it fits.

Nothing is written. No certificate, audit, factory, verifier, gate or
constructor is changed. No timing is reported, so two runs print identical
output.
"""
import collections
import csv
import hashlib
import importlib
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, ".")

from arc_agi2 import runtime  # noqa: E402

ROOT = Path(".").resolve()
IDS = ["0c786b71", "e0fb7511", "f0df5ff0", "f3cdc58f"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def mod(tid):
    return importlib.import_module("tasks.task_" + tid)


def q(values, ps=(0, 0.1, 0.5, 0.9, 1)):
    v = sorted(values)
    return [round(v[min(len(v) - 1, int(p * (len(v) - 1)))], 3) for p in ps]


def run_program(source, grid):
    ns = {}
    exec(compile(source, "factory", "exec"), ns)
    return [list(map(int, r)) for r in ns["solve"]([], grid)]


# ---------------------------------------------------------------- bindings
def bindings():
    from arc_agi2.direct_certificates import certified_factory_source
    from arc_agi2.verified_rules import VERIFIERS
    from arc_agi2.diversity import prepare, sampler
    out = {}
    try:
        sampler.admission.cache_clear()
        sampler.admission()
        out["admission_pins_valid"] = True
    except ValueError as e:  # pragma: no cover - reported, not raised
        out["admission_pins_valid"] = f"ERROR {e}"
    status = {r["task_id"]: r for r in csv.DictReader(
        open("arc_agi2/reports/diversity-v1/family-status.csv"))}
    import arc_agi2.colour_evidence as ce

    def gate(tid):
        """Functional dispatch check: canonical demos/query must pass; no demos
        must raise iff a demonstration gate is dispatched for the task."""
        can = runtime.reference(tid)["canonical"]
        ce.require_colour_evidence(tid, can["train"], can["test"])
        try:
            ce.require_colour_evidence(tid, [], [{"input": can["test"][0]["input"]}])
        except ce.MissingColourEvidence as e:
            return f"gated (canonical passes; no demos -> {str(e).split(': ', 1)[1]})"
        return "no gate (returns without checking demonstrations)"

    for tid in IDS:
        cons = sha(f"tasks/task_{tid}.py")
        fac = json.loads(Path(f"arc_agi2/direct_factories/{tid}.json").read_text())
        nat = json.loads(Path(f"arc_agi2/reports/diversity-v1/native-certificates/{tid}.json").read_text())
        lookups = [certified_factory_source(tid, d4, list(range(10))) is not None for d4 in range(8)]
        row = status.get(tid, {})
        out[tid] = {
            "constructor_sha256": cons[:8],
            "factory_cert_binds_constructor": fac["constructor_sha256"] == cons,
            "native_cert_binds_constructor": nat["constructor_sha256"] == cons,
            "factory_sha_matches": fac["factory_sha256"] == sha(f"arc_agi2/direct_factories/task_{tid}.py"),
            "auditor_sha_matches_recertify": fac["auditor_sha256"] == sha("arc_agi2/diversity/recertify.py"),
            "certified_factory_source_d4_0_7": sum(lookups),
            "certificate_draft_review_constructor": (
                fac.get("draft_notes", {}).get("independent_source_review", {})
                .get("constructor_sha256", "")[:8] or None),
            "verification_solver": ("verified_rules." + VERIFIERS[tid].__name__) if tid in VERIFIERS
            else "archived_reference",
            "in_prepare_REPAIRED": tid in prepare.REPAIRED,
            "colour_evidence_gate": gate(tid),
            "family_status_csv": {"native_repaired": row.get("native_repaired"),
                                  "constructor_sha256": row.get("current_constructor_sha256", "")[:8],
                                  "matches_current": row.get("current_constructor_sha256") == cons},
        }
    return out


# --------------------------------------------------------------- canonical
def canonical():
    out = {}
    for tid in IDS:
        m = mod(tid)
        can = runtime.reference(tid)["canonical"]
        pairs = can["train"] + can["test"]
        val = m.validate()
        replay = [a == b for a, b in zip(val["train"] + val["test"], pairs)]
        check = runtime.verification_solver(tid)
        src = importlib.import_module(f"arc_agi2.direct_factories.task_{tid}").build_program(0, list(range(10)))
        verifier = [runtime.grid(check(p["input"])) == p["output"] for p in pairs]
        factory = [run_program(src, p["input"]) == p["output"] for p in pairs]
        rec = {"pairs": len(pairs), "validate_replay_exact": sum(replay),
               "verifier_exact": sum(verifier), "factory_d4_0_exact": sum(factory),
               "latent": [], "outside_random_path": []}
        names = [f"train[{i}]" for i in range(len(can["train"]))] + \
                [f"test[{i}]" for i in range(len(can["test"]))]
        for name, p in zip(names, pairs):
            g = p["input"]
            h, w = len(g), len(g[0])
            cells = [v for r in g for v in r]
            cnt = collections.Counter(cells)
            why = []
            if tid == "0c786b71":
                lat = {"shape": [h, w], "colours": len(cnt), "has_0": 0 in cnt}
                if not (2 <= h <= 15 and 2 <= w <= 15): why.append("dims outside random 2..15")
                if len(cnt) > 3 or 0 in cnt: why.append("colours outside the 3-colour 1..9 pool")
            elif tid == "e0fb7511":
                az = sum(v == 8 for r in p["output"] for v in r)
                dens = cnt[0] / (h * w)
                lat = {"shape": [h, w], "black_density": round(dens, 3), "azure": az,
                       "floor": m.default_min_marked(w, h)}
                if not (6 <= h <= 30 and 6 <= w <= 30): why.append("dims outside random 6..30")
                if az < m.default_min_marked(w, h): why.append("below the default azure floor")
                if not 0.15 <= dens <= 0.35: why.append("density outside random 0.15..0.35 (sample, not bound)")
            elif tid == "f0df5ff0":
                seeds = cnt[1]
                confetti = sorted(c for c in cnt if c not in (0, 1))
                dens = (h * w - cnt[0] - seeds) / (h * w - seeds)
                hi = m.default_max_boxes(w, h)
                lat = {"shape": [h, w], "seeds": seeds, "default_seed_range": [2, hi],
                       "confetti_colours": len(confetti), "confetti_density_non_seed": round(dens, 3)}
                if not (6 <= h <= 30 and 6 <= w <= 30): why.append("dims outside random 6..30")
                if not 2 <= seeds <= hi: why.append("seed count outside default range")
                # line 150: subset = common.choices(range(2, 10), 6) -> at most 6 distinct
                if len(confetti) > 6: why.append(f"{len(confetti)} confetti colours; choices(range(2,10), 6) gives <= 6")
            else:  # f3cdc58f
                lo, hi = m.placement_range(h)
                counts = [cnt[c] for c in (1, 2, 3, 4)]
                lat = {"shape": [h, w], "counts": counts, "placements_per_colour": [lo, hi]}
                if not (4 <= h <= 30 and 4 <= w <= 30): why.append("dims outside random 4..30")
                if any(not 1 <= c <= hi for c in counts): why.append("count above the placement maximum")
            lat["pair"] = name
            rec["latent"].append(lat)
            if why:
                rec["outside_random_path"].append({"pair": name, "why": why})
        out[tid] = rec
    return out


# ------------------------------------------------------------------ domain
class Counting:
    """Count calls of a common.* helper while it is temporarily wrapped."""

    def __init__(self, module, name):
        self.module, self.name, self.n = module, name, 0
        self.orig = getattr(module, name)

    def __enter__(self):
        def wrapped(*a, **k):
            self.n += 1
            return self.orig(*a, **k)
        setattr(self.module, self.name, wrapped)
        return self

    def __exit__(self, *exc):
        setattr(self.module, self.name, self.orig)


def domain(n=400):
    import common
    out = {}
    # 0c786b71
    m = mod("0c786b71")
    random.seed(0)
    hist, sym = collections.Counter(), 0
    for _ in range(n):
        g = m.generate()["input"]
        hist[len({v for r in g for v in r})] += 1
        sym += any(g == x for x in ([r[::-1] for r in g], g[::-1]))
    out["0c786b71"] = {"draws": n, "distinct_colours": dict(sorted(hist.items())),
                       "lr_or_tb_symmetric_inputs": sym,
                       "colour_0_possible": False,
                       "note": "random_colors(3) draws from 1..9 (common.py 560-566); explicit colours allow 0"}
    # e0fb7511: attempts per accepted draw (common.flatten is called once per attempt, line 99)
    m = mod("e0fb7511")
    random.seed(0)
    attempts, ratio, by_area = [], [], collections.defaultdict(list)
    for _ in range(n):
        with Counting(common, "flatten") as c:
            r = m.generate()
        h, w = len(r["input"]), len(r["input"][0])
        attempts.append(c.n)
        az = sum(v == 8 for row in r["output"] for v in row)
        ratio.append(az / (h * w))
        by_area["<=169" if h * w <= 169 else ("<=450" if h * w <= 450 else ">450")].append(c.n)
    out["e0fb7511"] = {
        "draws": n, "attempts_quantiles": q(attempts), "draws_needing_retry": sum(a > 1 for a in attempts),
        "retry_rate_by_area": {k: round(sum(a > 1 for a in v) / len(v), 3) for k, v in sorted(by_area.items())},
        "azure_fraction_quantiles": q(ratio), "legacy_floor_fraction": round(13 / 169, 4),
        "note": "floor max(2, round(13*HW/169)) is about 7.7% of the canvas; at density 0.15 the "
                "expected azure fraction is about 0.15*(1-0.85**4)=0.072 away from edges, so the floor "
                "rejects many low-density layouts"}
    # f0df5ff0
    m = mod("f0df5ff0")
    lattice_default = [(w, h) for w in range(6, 31) for h in range(6, 31)
                       if m.default_max_boxes(w, h) > m.window_capacity(w, h) // 2]
    random.seed(0)
    colours, fill, attempts = collections.Counter(), [], []
    for _ in range(n):
        with Counting(common, "grids") as c:
            r = m.generate()
        g = r["input"]
        h, w = len(g), len(g[0])
        colours[len({v for row in g for v in row} - {0, 1})] += 1
        fill.append(sum(v == 1 for row in g for v in row) / m.window_capacity(w, h))
        attempts.append(c.n)
    out["f0df5ff0"] = {
        "draws": n, "default_shapes_where_lattice_path_can_run": len(lattice_default),
        "distinct_confetti_colours": dict(sorted(colours.items())),
        "seed_fraction_of_window_capacity_quantiles": q(fill),
        "draw_attempts_quantiles": q(attempts), "draws_needing_retry": sum(a > 1 for a in attempts),
        "note": "default num_boxes <= default_max_boxes <= capacity//2 for every 6..30 shape, so the "
                "jittered lattice (line 165) runs only for explicit num_boxes"}
    # f3cdc58f
    m = mod("f3cdc58f")
    full = [h for h in range(4, 31) if m.placement_range(h)[1] >= h]
    random.seed(0)
    top, frac, ink = [], [], []
    for _ in range(n):
        g = m.generate()["input"]
        h, w = len(g), len(g[0])
        cnt = collections.Counter(v for row in g for v in row)
        mx = max(cnt[c] for c in (1, 2, 3, 4))
        top.append(mx)
        frac.append(mx / h)
        ink.append(sum(cnt[c] for c in (1, 2, 3, 4)) / (h * w))
    out["f3cdc58f"] = {
        "draws": n, "random_heights_allowing_full_height_bar": full,
        "max_bar_over_height_quantiles": q(frac), "max_bar_quantiles": q(top),
        "ink_density_quantiles": q(ink),
        "note": "placement_range caps placements at 4H//5 (line 37) for H >= 5, so a bar taller than "
                "4H//5 never occurs in default draws; explicit colours allow counts up to H"}
    return out


# ------------------------------------------------------------- competitors
def f3_competitors(grid):
    cnt = collections.Counter(v for r in grid for v in r)
    first = {}
    for i, v in enumerate(v for r in grid for v in r):
        first.setdefault(v, i)
    return {
        "ascending_count": sorted((1, 2, 3, 4), key=lambda c: (cnt[c], c)),
        "descending_count": sorted((1, 2, 3, 4), key=lambda c: (-cnt[c], c)),
        "first_appearance_row_major": sorted((1, 2, 3, 4), key=lambda c: first[c]),
    }


def f3_ambiguity(shape, contexts, seed):
    m = mod("f3cdc58f")
    random.seed(seed)
    survive, ambiguous = collections.Counter(), collections.Counter()
    for _ in range(contexts):
        if shape == "default":
            q_ = m.generate()
            h, w = len(q_["input"]), len(q_["input"][0])
        else:
            h, w = shape
            q_ = m.generate(width=w, height=h)
        demos = [m.generate(width=w, height=h) for _ in range(3)]
        for name in ("ascending_count", "descending_count", "first_appearance_row_major"):
            if all(f3_competitors(d["input"])[name] == [1, 2, 3, 4] for d in demos):
                survive[name] += 1
                if f3_competitors(q_["input"])[name] != [1, 2, 3, 4]:
                    ambiguous[name] += 1
    return {"contexts": contexts, "competitor_fits_all_demos": dict(survive),
            "fits_demos_and_changes_query": dict(ambiguous)}


def f0_overwrite(grid):
    """Competitor: every non-seed cell in a seed window becomes the seed colour."""
    h, w = len(grid), len(grid[0])
    out = [r[:] for r in grid]
    for y in range(h):
        for x in range(w):
            if grid[y][x] == 1:
                for yy in range(max(0, y - 1), min(h, y + 2)):
                    for xx in range(max(0, x - 1), min(w, x + 2)):
                        out[yy][xx] = 1
    return out


def f0_ambiguity(shape, contexts, seed):
    m = mod("f0df5ff0")
    random.seed(seed)
    fit = amb = 0
    for _ in range(contexts):
        h, w = shape
        demos = [m.generate(width=w, height=h) for _ in range(3)]
        q_ = m.generate(width=w, height=h)
        if all(f0_overwrite(d["input"]) == d["output"] for d in demos):
            fit += 1
            amb += f0_overwrite(q_["input"]) != q_["output"]
    return {"contexts": contexts, "competitor_fits_all_demos": fit, "fits_demos_and_changes_query": amb}


def competitors(contexts=2000):
    return {
        "f3cdc58f": {"4x4": f3_ambiguity((4, 4), contexts, 1), "10x10": f3_ambiguity((10, 10), contexts, 2),
                     "default_query_shape": f3_ambiguity("default", contexts, 3)},
        "f0df5ff0": {"6x6": f0_ambiguity((6, 6), contexts, 4), "15x15": f0_ambiguity((15, 15), contexts, 5)},
    }


def main():
    report = {"head": __import__("subprocess").run(["git", "rev-parse", "HEAD"], capture_output=True,
                                                   text=True).stdout.strip(),
              "sources": {tid: sha(f"tasks/task_{tid}.py")[:8] for tid in IDS} | {
                  "mirror_neighbourhood_evidence": sha("arc_agi2/mirror_neighbourhood_evidence.py")[:8],
                  "colour_evidence": sha("arc_agi2/colour_evidence.py")[:8],
                  "verified_rules": sha("arc_agi2/verified_rules.py")[:8],
                  "probe": sha(__file__)[:8]},
              "bindings": bindings(), "canonical": canonical(), "domain": domain(),
              "competitors": competitors()}
    print(json.dumps(report, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
