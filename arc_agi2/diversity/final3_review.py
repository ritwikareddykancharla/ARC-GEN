"""Semantic review of the three remaining excluded RE-ARC families.

Families: ``0b148d64`` (odd-quadrant crop), ``1b2d62fb`` (two-panel NOR) and
``de1cd16c`` (region with the most noise). Every check here is diagnostic.
Nothing in this module is imported by the factories, admission, preparation or
any certificate path, and it writes no certificate status.

The review shows the following:

* Each current factory hard-codes a native colour role or statistic that RE-ARC
  varies. That is why its admission episode fails.
* Native and RE-ARC rules are compatible. Each family's ``CANDIDATES`` program
  is exact or rejects on both domains, by the source arguments in
  ``PROOFS``. It never returns a wrong grid.
* Unchanged ``recertify`` cannot certify any replacement factory. Its
  "independent" checker is the archived reference solver
  (``references/<id>.json``), and that solver disagrees with correct native
  constructor labels on recertify's fixed seeds, before any program runs. A
  reviewed override in ``verified_rules.py`` is another lane, so these
  families stay excluded.
* Program correctness is not demonstration sufficiency. ``ambiguity`` checks
  small hypothesis families against real sampled episodes.

Run: ``python -m arc_agi2.diversity.final3_review`` (writes
``reports/diversity-v1/final3-review/``; large probe evidence goes to the
ignored ``reports/diversity-v1/<id>.json`` path used by ``certify_programs``).
"""

import argparse
import hashlib
import importlib
import json
import random
import time
from collections import Counter
from pathlib import Path

from ..augmentation import transformed
from ..program_targets import audit_target, verify
from ..runtime import BASE, call, grid, reference, solver, verification_solver
from .recertify import episode

FAMILIES = ("0b148d64", "1b2d62fb", "de1cd16c")
OUT = BASE / "reports/diversity-v1/final3-review"
ROOT = Path(__file__).parent
SECOND_PALETTE = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
# Proposal counts chosen so >= 1,024 pairs survive both verifiers (all >= 1,152).
PROPOSALS = {"0b148d64": 1280, "1b2d62fb": 2560, "de1cd16c": 2048}

ODD_QUADRANT = r'''
def solve(demonstrations, grid):
    height, width = len(grid), len(grid[0])
    # Background: the only colour owning both a full row and a full column (the bands).
    row_colours = {grid[r][0] for r in range(height) if len(set(grid[r])) == 1}
    col_colours = {grid[0][c] for c in range(width)
                   if all(grid[r][c] == grid[0][c] for r in range(height))}
    shared = row_colours & col_colours
    if len(shared) != 1:
        raise ValueError("Expected one background colour forming both bands")
    background = shared.pop()
    boxes = {}
    for r in range(height):
        for c in range(width):
            ink = grid[r][c]
            if ink != background:
                t, l, b, rt = boxes.get(ink, (r, c, r, c))
                boxes[ink] = (min(t, r), min(l, c), max(b, r), max(rt, c))
    if len(boxes) != 2:
        raise ValueError("Expected exactly two quadrant colours")
    # The odd colour's box holds only itself and background; the shared colour's
    # box always reaches into the odd quadrant. Both pure -> undecidable, reject.
    pure = [ink for ink, (t, l, b, rt) in boxes.items()
            if all(grid[r][c] in (ink, background)
                   for r in range(t, b + 1) for c in range(l, rt + 1))]
    if len(pure) != 1:
        raise ValueError("Odd quadrant colour not uniquely determined")
    t, l, b, rt = boxes[pure[0]]
    return [row[l:rt + 1] for row in grid[t:b + 1]]
'''

CENTRE_DIVIDER = r'''
EMPTY = %d
MARK = %d


def solve(demonstrations, grid):
    height, width = len(grid), len(grid[0])
    found = []
    if width %% 2:
        line = {row[width // 2] for row in grid}
        if len(line) == 1 and EMPTY not in line:
            found.append("column")
    if height %% 2:
        line = set(grid[height // 2])
        if len(line) == 1 and EMPTY not in line:
            found.append("row")
    if len(found) != 1:
        raise ValueError("Expected exactly one central divider line")
    if found[0] == "column":
        half = width // 2
        first = [row[:half] for row in grid]
        second = [row[half + 1:] for row in grid]
    else:
        half = height // 2
        first, second = grid[:half], grid[half + 1:]
    return [[MARK if a == EMPTY and b == EMPTY else EMPTY for a, b in zip(ra, rb)]
            for ra, rb in zip(first, second)]
'''

NOISE_TILING = r'''
def solve(demonstrations, grid):
    height, width = len(grid), len(grid[0])
    boxes = {}
    for r in range(height):
        for c in range(width):
            ink = grid[r][c]
            t, l, b, rt = boxes.get(ink, (r, c, r, c))
            boxes[ink] = (min(t, r), min(l, c), max(b, r), max(rt, c))

    def tiling_without(noise):
        owner = [[None] * width for _ in range(height)]
        for ink, (t, l, b, rt) in boxes.items():
            if ink == noise:
                continue
            for r in range(t, b + 1):
                for c in range(l, rt + 1):
                    if owner[r][c] is not None or grid[r][c] not in (ink, noise):
                        return None
                    owner[r][c] = ink
        if any(cell is None for line in owner for cell in line):
            return None
        return owner

    if len(boxes) < 3:
        raise ValueError("Expected at least two regions and a noise colour")
    fits = [(ink, owner) for ink in boxes for owner in [tiling_without(ink)] if owner]
    if len(fits) != 1:
        raise ValueError("Noise colour not uniquely determined by a rectangle tiling")
    noise, owner = fits[0]
    tally = {}
    for r in range(height):
        for c in range(width):
            if grid[r][c] == noise:
                tally[owner[r][c]] = tally.get(owner[r][c], 0) + 1
    if not tally:
        raise ValueError("No noise cells")
    best = max(tally.values())
    winners = [ink for ink, n in tally.items() if n == best]
    if len(winners) != 1:
        raise ValueError("Tied noise counts")
    return [[winners[0]]]
'''

PROOFS = {
    "0b148d64": [
        "Background: both constructors leave >= 1 full row and >= 1 full column of background "
        "between quadrants (native rowthick, colthick >= 2; RE-ARC di, dj >= 2). Any full row "
        "crosses the vertical band and any full column crosses the horizontal band, so no "
        "quadrant colour has both. The background is the unique colour with both.",
        "Odd colour box is pure: its cells lie in one corner quadrant, which holds only it and "
        "background (native quad assignment; RE-ARC fill(trg)).",
        "RE-ARC shared colour is impure: subf puts a cell on all four edges of each of its three "
        "quadrant boxes, and any three corner quadrants touch all four grid edges. Its box is "
        "the whole grid and contains the odd colour's cells.",
        "Native shared colour: impure unless its 0.9-density quadrants are almost empty. Then "
        "both boxes are pure and the program raises. It never returns a wrong grid.",
        "Label equality: native output crops the rarest non-zero colour's box. Its selection "
        "loop forces that colour to be the odd colour. RE-ARC output is subgrid(trg), and subf "
        "makes the odd colour's box equal trg.",
    ],
    "1b2d62fb": [
        "Both constructors put a divider of one non-empty colour on the exact centre line "
        "(native: blue column 3 of 7; RE-ARC: barcol between two w-wide halves, hconcat, then "
        "an optional dmirror). D4 maps the centre line to a centre line.",
        "The perpendicular centre line (if any) contains the divider cell and >= 2 half cells. "
        "Half cells are empty or panel colours, never the divider colour (native 0/9 vs 1; "
        "RE-ARC remcols removes barcol before cola/colb). It is never uniform non-empty, so "
        "exactly one divider is found.",
        "Both outputs mark 8 where both halves are 0 at the same relative cell (native "
        "grid_intersect: n=maroon is 'full', y=black is 'empty'; RE-ARC ofcolor(gia,0) & "
        "ofcolor(gib,0)), else 0. D4 mirrors both halves together and NOR is symmetric. "
        "Palette maps the fixed 0 and 8 roles to palette[0] and palette[8].",
    ],
    "de1cd16c": [
        "Both constructors tile the grid with axis-aligned rectangles. Native: a 2x2 grid with "
        "distinct colours; canonical fixtures merge equal adjacent colours into rectangles. "
        "RE-ARC: guillotine cuts that give each piece a new distinct colour. The noise colour "
        "differs from every region colour.",
        "Removing the true noise colour N: RE-ARC puts noise only in backdrop(inbox(obj)), so each "
        "region keeps its whole border and its box is exactly its rectangle; the boxes tile. "
        "Native dots may lie on region edges. A tiling is still found unless one full edge line "
        "of a region is all dots, in which case the program raises.",
        "No other colour X qualifies. Removing X needs N's box to contain only N or X, so all "
        "noise lies inside X's region, strictly inside the border in RE-ARC. X's border ring "
        "is then uncovered and the tiling fails. Natively, at least 3 quadrants have dots, so "
        "N's box crosses region boundaries.",
        "If the tiling holds, each box lies inside its true rectangle and the boxes cover the "
        "grid. So every box equals its rectangle and each dot is counted in its true region.",
        "Unique maximum: native counts are distinct samples from range(6); RE-ARC decrements "
        "every tied maximum except the first. Ties are rejected regardless.",
    ],
}

CANDIDATES = {"0b148d64": ODD_QUADRANT, "1b2d62fb": CENTRE_DIVIDER, "de1cd16c": NOISE_TILING}


def candidate_source(tid, d4=0, palette=None):
    palette = list(range(10)) if palette is None else [int(x) for x in palette]
    if tid == "1b2d62fb":
        return CENTRE_DIVIDER % (palette[0], palette[8])
    return CANDIDATES[tid]


def compiled(source):
    """One-argument callable for a standalone ``solve(demonstrations, grid)`` program."""
    namespace = {"__name__": "final3_candidate"}
    exec(compile(source, "<final3-candidate>", "exec"), namespace)
    solve = namespace["solve"]
    return lambda query: solve([], query)


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def run(fn, grid_in):
    try:
        return grid(call(fn, grid_in, seconds=3))
    except Exception as exc:  # noqa: BLE001 - outcome is recorded, never substituted
        return repr(exc)


# --------------------------------------------------------------------------------------
# Minimal native-domain counterexamples (explicit constructor parameters).
# --------------------------------------------------------------------------------------

def minimal_counterexamples():
    """Smallest-grid native inputs on which the archived checker is wrong.

    Each uses the native ``generate`` with explicit parameters that its random sampler
    reaches with positive probability. The constructor computes the label itself (0b, 1b)
    or takes the stated ``mostest`` (de1, recomputed below from the dot placement).
    """
    cases = {}
    # 0b148d64: 15x15, row=col=5, thickness 2. Top-left, top-right and bottom-left
    # quadrants are full of 1 (105 cells, modal). The bottom-right 8x8 quadrant is full
    # of 2 (64 cells). The background-0 bands have 56 cells: rarer than 2, not modal.
    g = [[0] * 15 for _ in range(15)]
    for r in range(15):
        for c in range(15):
            if r in (5, 6) or c in (5, 6):
                continue
            g[r][c] = 2 if r >= 7 and c >= 7 else 1
    module = importlib.import_module("tasks.task_0b148d64")
    pair = module.generate(width=15, height=15, colors=[v for row in g for v in row])
    cases["0b148d64"] = {
        "construction": "generate(width=15, height=15, colors=<grid>); row=col=5, "
                        "rowthick=colthick=2, odd quadrant 3 (bottom-right) fully painted",
        "pair": pair}
    # 1b2d62fb: the only black pixels are left-panel column 0, so column 0 is uniform 0
    # while maroon 9 is modal.
    module = importlib.import_module("tasks.task_1b2d62fb")
    pair = module.generate(rows=[0, 1, 2, 3, 4], cols=[0, 0, 0, 0, 0])
    cases["1b2d62fb"] = {"construction": "generate(rows=[0,1,2,3,4], cols=[0,0,0,0,0])",
                         "pair": pair}
    # de1cd16c: 10x10, four 5x5 quadrants (1, 2 / 3, 4), dot colour 6, distinct counts
    # 0, 1, 4, 3. The four bottom-left dots form a 2x2 block in the quadrant's top-right
    # corner. Archived 4-neighbour majority skips dot neighbours, and its Counter ties go to
    # the first neighbour inserted (up before left/right). So (5,3) and (5,4) go to quadrant
    # 1, and the archived tally is 1:2, 2:1, 3:2, 4:3, giving 4 instead of 3.
    module = importlib.import_module("tasks.task_de1cd16c")
    rows = [1, 5, 5, 6, 6, 7, 8, 8]
    cols = [7, 3, 4, 3, 4, 7, 8, 6]
    pair = module.generate(wides=[5, 5], talls=[5, 5], colors=[1, 2, 3, 4], rows=rows,
                           cols=cols, mostest=3, pcolor=6)
    quadrant = [[(1, 2), (3, 4)][r // 5][c // 5] for r, c in zip(rows, cols)]
    counts = Counter(quadrant)
    assert sorted(counts.get(k, 0) for k in (1, 2, 3, 4)) == [0, 1, 3, 4]
    assert max(counts, key=counts.get) == 3
    cases["de1cd16c"] = {
        "construction": "generate(wides=[5,5], talls=[5,5], colors=[1,2,3,4], rows=%r, cols=%r, "
                        "mostest=3, pcolor=6); true per-quadrant counts %r" % (
                            rows, cols, dict(sorted(counts.items()))),
        "pair": pair}
    for tid, case in cases.items():
        pair = {k: grid(v) for k, v in case["pair"].items()}
        case["pair"] = pair
        case["archived_output"] = run(solver(tid), pair["input"])
        case["archived_agrees"] = case["archived_output"] == pair["output"]
        case["candidate_output"] = run(compiled(candidate_source(tid)), pair["input"])
        case["candidate_exact"] = case["candidate_output"] == pair["output"]
    return cases


# --------------------------------------------------------------------------------------
# Native replay of recertify's fixed seeds (diagnostic; never writes certificates).
# --------------------------------------------------------------------------------------

def native_review(tid):
    """Replays recertify.check's sampling exactly.

    Unlike ``recertify.check``, this does not stop at the first archived-checker
    disagreement. It counts them all, and checks the candidate against the
    constructor label on every pair under recertify's eight D4 maps and palette.
    """
    module = importlib.import_module("tasks.task_" + tid)
    checker = verification_solver(tid)
    report = {"fresh_pairs": 0, "candidate_augmented_pair_checks": 0, "candidate_failures": [],
              "archived_disagreements": [], "fixture_variants_checked": 0}
    fixture = reference(tid)["canonical"]
    for palette in (list(range(10)), SECOND_PALETTE):
        for d4 in range(8):
            source = candidate_source(tid, d4, palette)
            audit_target(tid, source)
            verify(source, episode(fixture["train"] + fixture["test"], d4, palette))
            report["fixture_variants_checked"] += 1
    seen = set()
    for i in range(300):
        seed = int(sha_bytes(f"diversity-recert:{tid}:{i}".encode())[:12], 16)
        random.seed(seed)
        pairs = [{k: grid(p[k]) for k in ("input", "output")}
                 for p in [call(module.generate, seconds=3) for _ in range(4)]]
        for j, pair in enumerate(pairs):
            seen.add(sha_bytes(json.dumps(pair["input"]).encode()))
            got = run(checker, pair["input"])
            if got != pair["output"]:
                report["archived_disagreements"].append(
                    {"recertify_index": i, "seed": seed, "pair_in_group": j,
                     "shape": [len(pair["input"]), len(pair["input"][0])],
                     "archived_error": got if isinstance(got, str) else None})
        palette = list(range(10))
        random.Random(seed + 1).shuffle(palette)
        for d4 in range(8):
            solve = compiled(candidate_source(tid, d4, palette))
            for j, pair in enumerate(pairs):
                expected = transformed(pair["output"], d4, palette)
                got = run(solve, transformed(pair["input"], d4, palette))
                report["candidate_augmented_pair_checks"] += 1
                if got != expected:
                    report["candidate_failures"].append({"seed": seed, "pair_in_group": j,
                                                         "d4": d4, "outcome": str(got)[:200]})
        report["fresh_pairs"] += 4
        if report["fresh_pairs"] >= 1000:
            break
    report["unique_base_inputs"] = len(seen)
    first = report["archived_disagreements"][:1]
    report["recertify_would_fail_at"] = first[0] if first else None
    report["archived_error_count"] = sum(1 for d in report["archived_disagreements"]
                                         if d["archived_error"])
    return report


# --------------------------------------------------------------------------------------
# RE-ARC gates, run through the unchanged probe/admit code with the candidate injected.
# --------------------------------------------------------------------------------------

def rearc_review(tid, proposals=None):
    """Runs ``probe.probe`` and ``admit.check`` unchanged, with the candidate injected.

    Only ``direct_programs.direct_source`` is patched, in-process, to return the
    candidate for ``tid``. Probe evidence goes to the ignored
    ``reports/diversity-v1/<tid>.json`` path, the convention ``certify_programs`` uses.
    """
    from .. import direct_programs
    from . import admit, probe
    from .rearc import generators, utils, verifiers
    proposals = proposals or PROPOSALS[tid]
    original = direct_programs.direct_source

    def patched(task_id, d4, palette):
        return candidate_source(task_id, d4, palette) if task_id == tid else original(
            task_id, d4, palette)

    direct_programs.direct_source = patched
    try:
        evidence = probe.probe((tid, proposals), deadline=600)
        (BASE / "reports/diversity-v1" / (tid + ".json")).write_text(
            json.dumps(evidence, indent=2) + "\n")
        gate = admit.check(tid, pair_budget=1024, required=2048)
    finally:
        direct_programs.direct_source = original
    # Attribute archived-verifier rejections; never admits a rejected pair.
    gen = getattr(generators, "generate_" + tid)
    check = getattr(verifiers, "verify_" + tid)
    archived = verification_solver(tid)
    solve = compiled(candidate_source(tid))
    tally = Counter()
    for i in range(proposals):
        seed = int(hashlib.sha256(f"diversity-v1:{tid}:{i}".encode()).hexdigest()[:8], 16)
        random.seed(seed)
        utils.rng.clear()
        try:
            raw = call(gen, 0.0, 1.0, seconds=1)
            pair = {k: grid(raw[k]) for k in ("input", "output")}
            if grid(call(check, tuple(map(tuple, pair["input"])), seconds=1)) != pair["output"]:
                tally["rearc_verifier_rejects"] += 1
                continue
        except Exception as exc:  # noqa: BLE001
            tally["proposal_" + type(exc).__name__] += 1
            continue
        fork = run(archived, pair["input"]) == pair["output"]
        exact = run(solve, pair["input"]) == pair["output"]
        tally[("archived_agrees" if fork else "archived_rejects") + "/candidate_"
              + ("exact" if exact else "not_exact")] += 1
    return {
        "requested_proposals": proposals,
        "accepted_pairs": evidence.get("accepted"),
        "probe_rejections": evidence.get("rejections"),
        "probe_verified_episodes": evidence.get("verified_episodes"),
        "bounded_stop": evidence.get("bounded_stop", False),
        "input_shape_count": len(evidence.get("input_shapes", {})),
        "augmented_episode_checks": gate["verified_variants"],
        "augmented_pair_checks": 4 * gate["verified_variants"],
        "admission_gate_passed": gate["passed"],
        "admission_gate_error": gate.get("error"),
        "candidate_program_sha256": gate.get("program_sha256"),
        "rejection_attribution": dict(sorted(tally.items())),
    }


# --------------------------------------------------------------------------------------
# Demonstration sufficiency: rival hypotheses on real sampled episodes.
# --------------------------------------------------------------------------------------

def _boxes(g, skip=()):
    boxes = {}
    for r, row in enumerate(g):
        for c, ink in enumerate(row):
            if ink in skip:
                continue
            t, l, b, rt = boxes.get(ink, (r, c, r, c))
            boxes[ink] = (min(t, r), min(l, c), max(b, r), max(rt, c))
    return boxes


def _crop(g, box):
    t, l, b, rt = box
    return [row[l:rt + 1] for row in g[t:b + 1]]


def _rarest_crop(g, background):
    counts = Counter(v for row in g for v in row if v != background)
    if not counts:
        raise ValueError("empty")
    least = min(counts.values())
    ties = [k for k, v in counts.items() if v == least]
    if len(ties) != 1:
        raise ValueError("tie")
    return _crop(g, _boxes(g)[ties[0]])


def _band_colour(g):
    rows = {row[0] for row in g if len(set(row)) == 1}
    cols = {g[0][c] for c in range(len(g[0])) if len({row[c] for row in g}) == 1}
    shared = rows & cols
    if len(shared) != 1:
        raise ValueError("no unique band colour")
    return shared.pop()


def hypotheses_0b(g):
    counts = Counter(v for row in g for v in row)
    candidate = _cached("0b_candidate", lambda: compiled(ODD_QUADRANT))
    return {"odd_quadrant (candidate)": lambda: grid(candidate(g)),
            "rarest_non_modal (archived solver)":
                lambda: _rarest_crop(g, counts.most_common(1)[0][0]),
            "rarest_non_band (native behaviour of current factory)":
                lambda: _rarest_crop(g, _band_colour(g)),
            "rarest_overall": lambda: _rarest_crop(g, None),
            "smallest_box (RE-ARC verifier)": lambda: _smallest_box(g)}


def _smallest_box(g):
    ranked = sorted(((b - t + 1) * (r - l + 1), k) for k, (t, l, b, r) in _boxes(g).items())
    if len(ranked) < 2 or ranked[0][0] == ranked[1][0]:
        raise ValueError("tie")
    return _crop(g, _boxes(g)[ranked[0][1]])


_OPS = {"nor": lambda a, b: a and b, "and_full": lambda a, b: not a and not b,
        "xnor": lambda a, b: a == b, "xor": lambda a, b: a != b,
        "either_empty": lambda a, b: a or b, "first_empty": lambda a, b: a,
        "second_empty": lambda a, b: b}


def _masks_1b(g):
    """(op, empty colour) -> Boolean mask on the visible centre split."""
    height, width = len(g), len(g[0])
    if width % 2 and len({row[width // 2] for row in g}) == 1:
        first = [row[:width // 2] for row in g]
        second = [row[width // 2 + 1:] for row in g]
    elif height % 2 and len(set(g[height // 2])) == 1:
        first, second = g[:height // 2], g[height // 2 + 1:]
    else:
        return {}
    return {(name, empty): [[op(a == empty, b == empty) for a, b in zip(ra, rb)]
                            for ra, rb in zip(first, second)]
            for name, op in _OPS.items() for empty in range(10)}


def episode_ambiguity_1b(four):
    """Hypotheses: op x empty colour x mark colour x other colour (mark != other).

    Mark and other colours are solved from each demonstration, not enumerated.
    """
    allowed = None
    for demo in four[:3]:
        out = demo["output"]
        fits = {}
        for key, mask in _masks_1b(demo["input"]).items():
            if len(mask) != len(out) or any(len(a) != len(b) for a, b in zip(mask, out)):
                continue
            on = {v for mr, orow in zip(mask, out) for m, v in zip(mr, orow) if m}
            off = {v for mr, orow in zip(mask, out) for m, v in zip(mr, orow) if not m}
            if len(on) <= 1 and len(off) <= 1:
                fits[key] = (on or set(range(10)), off or set(range(10)))
        if allowed is None:
            allowed = fits
        else:
            allowed = {k: (allowed[k][0] & v[0], allowed[k][1] & v[1])
                       for k, v in fits.items() if k in allowed}
        allowed = {k: v for k, v in allowed.items()
                   if v[0] and v[1] and any(a != b for a in v[0] for b in v[1])}
    predictions = {}
    count = 0
    masks = _masks_1b(four[3]["input"])
    for key, (marks, others) in sorted(allowed.items()):
        mask = masks.get(key)
        if mask is None:
            continue
        for mark in sorted(marks):
            for other in sorted(others):
                if mark == other:
                    continue
                count += 1
                value = json.dumps([[mark if v else other for v in row] for row in mask])
                predictions.setdefault(value, []).append(str(key + (mark, other)))
    truth = json.dumps(four[3]["output"])
    return {"fitting": count, "distinct_query_predictions": len(predictions),
            "truth_predicted": truth in predictions,
            "rivals": {("TRUE" if k == truth else "WRONG_%d" % i): v[:6]
                       for i, (k, v) in enumerate(predictions.items())}}


def _partition(g):
    """Noise colour and owner map from the candidate tiling, or None."""
    height, width = len(g), len(g[0])
    boxes = _boxes(g)
    for noise in boxes:
        owner = [[None] * width for _ in range(height)]
        ok = True
        for ink, (t, l, b, rt) in boxes.items():
            if ink == noise or not ok:
                continue
            for r in range(t, b + 1):
                for c in range(l, rt + 1):
                    if owner[r][c] is not None or g[r][c] not in (ink, noise):
                        ok = False
                    owner[r][c] = ink
        if ok and all(v is not None for row in owner for v in row):
            return noise, owner, boxes
    return None


def _region_pick(g, score):
    part = _partition(g)
    if part is None:
        raise ValueError("no tiling")
    noise, owner, boxes = part
    tally = Counter(owner[r][c] for r, row in enumerate(g) for c, v in enumerate(row)
                    if v == noise)
    keys = {ink: score(tally.get(ink, 0), (b - t + 1) * (rt - l + 1))
            for ink, (t, l, b, rt) in boxes.items() if ink != noise}
    best = max(keys.values())
    win = [k for k, v in keys.items() if v == best]
    if len(win) != 1:
        raise ValueError("tie")
    return [[win[0]]]


_CACHE = {}


def _cached(key, make):
    if key not in _CACHE:
        _CACHE[key] = make()
    return _CACHE[key]


def hypotheses_de1(g):
    current = _cached("de1_current", lambda: compiled(importlib.import_module(
        "arc_agi2.direct_factories.task_de1cd16c").build_program(0, list(range(10)))))
    archived = _cached("de1_archived", lambda: solver("de1cd16c"))
    candidate = _cached("de1_candidate", lambda: compiled(NOISE_TILING))
    return {
        "most_noise (candidate)": lambda: grid(candidate(g)),
        "highest_noise_density": lambda: _region_pick(g, lambda n, a: n / a),
        "fewest_noise": lambda: _region_pick(g, lambda n, a: -n),
        "largest_region": lambda: _region_pick(g, lambda n, a: a),
        "smallest_region": lambda: _region_pick(g, lambda n, a: -a),
        "archived_solver": lambda: grid(archived(g)),
        "rarest_dot_partition (current factory)": lambda: grid(current(g)),
    }


HYPOTHESES = {"0b148d64": hypotheses_0b, "de1cd16c": hypotheses_de1}


def _predict(fn):
    try:
        return grid(fn())
    except Exception:  # noqa: BLE001 - an undefined hypothesis neither fits nor predicts
        return None


def episode_ambiguity(tid, four):
    """Rival hypotheses fitting all three demonstrations, compared on the query."""
    if tid == "1b2d62fb":
        return episode_ambiguity_1b(four)
    make = HYPOTHESES[tid]
    fitting = None
    for demo in four[:3]:
        hyps = make(demo["input"])
        fit = {name for name, fn in hyps.items() if _predict(fn) == demo["output"]}
        fitting = fit if fitting is None else fitting & fit
    hyps = make(four[3]["input"])
    predictions = {}
    for name in sorted(fitting, key=str):
        if name in hyps:
            value = _predict(hyps[name])
            if value is not None:
                predictions.setdefault(json.dumps(value), []).append(name)
    truth = json.dumps(four[3]["output"])
    return {"fitting": len(fitting), "distinct_query_predictions": len(predictions),
            "truth_predicted": truth in predictions,
            "rivals": {("TRUE" if k == truth else "WRONG_%d" % i): sorted(map(str, v))[:6]
                       for i, (k, v) in enumerate(predictions.items())}}


def ambiguity(tid, rearc_pairs, native_groups):
    """Search real sampled episodes for demonstrated ambiguity (no synthetic search)."""
    result = {}
    fixture = reference(tid)["canonical"]
    fx = fixture["train"] + fixture["test"]
    result["canonical_fixture"] = episode_ambiguity(tid, fx[-4:])
    for name, groups in (("rearc_admission_episodes", [rearc_pairs[o:o + 4] for o in
                                                       range(0, min(len(rearc_pairs) - 3, 1024), 4)]),
                         ("native_recertify_episodes", native_groups)):
        stats = Counter()
        witnesses = []
        for four in groups:
            info = episode_ambiguity(tid, four)
            stats["episodes"] += 1
            if info["distinct_query_predictions"] > 1:
                stats["demonstrated_ambiguous"] += 1
                if len(witnesses) < 2:
                    witnesses.append({"seeds": [p.get("seed") for p in four],
                                      "train": [{k: p[k] for k in ("input", "output")}
                                                for p in four[:3]],
                                      "query": {k: four[3][k] for k in ("input", "output")},
                                      **info})
            if not info["truth_predicted"]:
                stats["truth_not_among_fitting"] += 1
        result[name] = {**dict(stats), "witnesses": witnesses}
    return result


def native_groups(tid, groups=250):
    module = importlib.import_module("tasks.task_" + tid)
    out = []
    for i in range(groups):
        seed = int(sha_bytes(f"diversity-recert:{tid}:{i}".encode())[:12], 16)
        random.seed(seed)
        out.append([{"seed": seed, **{k: grid(p[k]) for k in ("input", "output")}}
                    for p in [call(module.generate, seconds=3) for _ in range(4)]])
    return out


# --------------------------------------------------------------------------------------

def source_bindings(tid):
    paths = [BASE.parent / "tasks" / ("task_" + tid + ".py"),
             BASE / "direct_factories" / ("task_" + tid + ".py"),
             BASE / "direct_factories" / (tid + ".json"),
             BASE / "references" / (tid + ".json"),
             ROOT / "rearc/generators.py", ROOT / "rearc/verifiers.py",
             ROOT / "recertify.py", ROOT / "probe.py", ROOT / "admit.py",
             ROOT / "certify_programs.py", BASE / "program_targets.py", BASE / "runtime.py",
             BASE / "helpers.py", BASE / "augmentation.py", BASE / "colour_evidence.py",
             BASE / "verified_rules.py", BASE / "direct_programs.py",
             BASE / "direct_certificates.py", Path(__file__)]
    hashes = {str(p.relative_to(BASE.parent)): sha_bytes(p.read_bytes()) for p in paths}
    hashes["archived_solver_code"] = sha_bytes(reference(tid)["code"].encode())
    hashes["candidate_program_identity_palette"] = sha_bytes(candidate_source(tid).encode())
    return hashes


def review(tid, minimal):
    began = time.monotonic()
    report = {"task_id": tid, "certificate": False,
              "status": "EXCLUDED: native recertification blocked by archived checker",
              "proof_of_candidate_semantics": PROOFS[tid]}
    report["minimal_native_counterexample"] = minimal[tid]
    report["native"] = native_review(tid)
    report["rearc"] = rearc_review(tid)
    pairs = json.loads((BASE / "reports/diversity-v1" / (tid + ".json")).read_text())
    report["demonstration_ambiguity"] = ambiguity(tid, pairs["accepted_pairs"],
                                                  native_groups(tid))
    report["source_sha256"] = source_bindings(tid)
    report["seconds"] = round(time.monotonic() - began, 3)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task_ids", nargs="*", default=list(FAMILIES))
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    minimal = minimal_counterexamples()
    for tid in args.task_ids:
        report = review(tid, minimal)
        (OUT / (tid + ".json")).write_text(json.dumps(report, indent=1) + "\n")
        print(json.dumps({"task_id": tid,
                          "archived_native_disagreements": len(
                              report["native"]["archived_disagreements"]),
                          "candidate_native_failures": len(report["native"]["candidate_failures"]),
                          "rearc_accepted": report["rearc"]["accepted_pairs"],
                          "rearc_episodes": report["rearc"]["augmented_episode_checks"],
                          "rearc_gate": report["rearc"]["admission_gate_passed"]}), flush=True)


if __name__ == "__main__":
    main()
