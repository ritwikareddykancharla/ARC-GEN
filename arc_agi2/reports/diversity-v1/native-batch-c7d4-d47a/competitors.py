"""Finite named competing rules for c7d4e6ad and d47aa2ff (native frame).

Each competitor is a deterministic function of ONE input grid in the native
orientation (identity palette: background 0, grey 5, markers 2/1). It returns
an output grid as a tuple of tuples, or None where the rule is undefined (a
tie, or no applicable key). None never fits a demonstration and always counts
as a distinct query answer.

* c7d4e6ad: 16 rules defined here. No gate: on the constructor domain every
  rule is either refuted by any single valid demonstration or equal to the
  native answer on every valid input (measured in batch-evidence.json).
* d47aa2ff: the 15 rules of the shipped gate
  ``arc_agi2/dot_motion_d47aa2ff_evidence.py`` (single source; not copied).

Both sets are bounded (one grid per rule per input) and are an assessment of
named alternatives, not an identifiability proof. "Learned lookup" readings,
which copy a demonstrated colour mapping instead of a visible colour, are
measured separately (``unseen_lookup_colours``) and are not counted as
competitors; see README.

Ambiguity criterion (as in the batch D/E/G gates): keep the rules that
reproduce EVERY demonstration output, then compare their answers on the query
INPUT. Query answers are never read here.
"""
from collections import Counter

from arc_agi2 import dot_motion_d47aa2ff_evidence as motion

BG, GREY = 0, 5


def _t(g):
    return tuple(tuple(int(v) for v in row) for row in g)


def _components(cells):
    cells, out = set(cells), []
    while cells:
        stack = [cells.pop()]
        comp = set(stack)
        while stack:
            r, c = stack.pop()
            for p in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if p in cells:
                    cells.remove(p)
                    comp.add(p)
                    stack.append(p)
        out.append(comp)
    return out


def _shape(g):
    return [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if c and v != BG]


def _legend(g):
    return [r for r in range(len(g)) if g[r][0] != BG]


def _recolour(g, key_of):
    """Every non-background cell outside column 0 takes key_of(r, c); None aborts."""
    out = [list(row) for row in g]
    for r, c in _shape(g):
        k = key_of(r, c)
        if k is None:
            return None
        out[r][c] = k
    return _t(out)


def row_key(g):
    """Native: key of the cell's own row in column 0 (black if that key is black)."""
    return _recolour(g, lambda r, c: g[r][0])


def _shift(k):
    def rule(g):
        return _recolour(g, lambda r, c: g[r + k][0] if 0 <= r + k < len(g) else BG)
    return rule


def _component(how):
    def rule(g):
        out = [list(row) for row in g]
        for comp in _components(_shape(g)):
            rows = sorted({r for r, _ in comp})
            if how == "majority":
                counts = Counter(g[r][0] for r, _ in comp).most_common()
                if len(counts) > 1 and counts[0][1] == counts[1][1]:
                    return None
                key = counts[0][0]
            else:
                key = g[rows[0] if how == "top" else rows[-1]][0]
            for r, c in comp:
                out[r][c] = key
        return _t(out)
    return rule


def _band(anchor):
    """Shape rows aligned to legend rows at one end, not by absolute row."""
    def rule(g):
        legend, rows = _legend(g), sorted({r for r, _ in _shape(g)})
        if not legend or not rows:
            return None
        offset = legend[0] - rows[0] if anchor == "top" else legend[-1] - rows[-1]
        return _recolour(g, lambda r, c: g[r + offset][0]
                         if 0 <= r + offset < len(g) and g[r + offset][0] != BG else None)
    return rule


def band_proportional(g):
    """Shape row span stretched onto the legend span."""
    legend, rows = _legend(g), sorted({r for r, _ in _shape(g)})
    if not legend or not rows:
        return None
    s0, span, n = rows[0], rows[-1] - rows[0] + 1, len(legend)
    return _recolour(g, lambda r, c: g[legend[0] + (r - s0) * n // span][0])


def legend_reversed(g):
    """Legend read bottom-to-top over its own span."""
    legend = _legend(g)
    if not legend:
        return None
    a, b = legend[0], legend[-1]
    return _recolour(g, lambda r, c: g[a + b - r][0] if a <= r <= b else None)


def nearest_key(g):
    """Nearest non-black legend cell (Euclidean); a tie between colours is undefined."""
    legend = _legend(g)
    if not legend:
        return None

    def key(r, c):
        d = sorted(((r - k) ** 2 + c * c, k) for k in legend)
        if len(d) > 1 and d[0][0] == d[1][0] and g[d[0][1]][0] != g[d[1][1]][0]:
            return None
        return g[d[0][1]][0]
    return _recolour(g, key)


def erase_legend(g):
    out = row_key(g)
    return None if out is None else tuple((BG,) + row[1:] for row in out)


def shape_colour_only(g):
    """Archived-solver reading: only the modal non-black colour outside column 0."""
    rest = Counter(v for row in g for v in row[1:] if v != BG).most_common()
    if not rest or (len(rest) > 1 and rest[0][1] == rest[1][1]):
        return None
    out = [list(row) for row in g]
    for r, c in _shape(g):
        if g[r][c] == rest[0][0] and g[r][0] != BG:
            out[r][c] = g[r][0]
    return _t(out)


C7 = {
    "row_key": row_key,
    "row_key_right_edge": lambda g: _recolour(g, lambda r, c: g[r][-1]),
    "col_key_top_edge": lambda g: _recolour(g, lambda r, c: g[0][c]),
    "col_key_bottom_edge": lambda g: _recolour(g, lambda r, c: g[-1][c]),
    "row_shift_up": _shift(-1),
    "row_shift_down": _shift(1),
    "component_majority": _component("majority"),
    "component_top_row": _component("top"),
    "component_bottom_row": _component("bottom"),
    "band_aligned_top": _band("top"),
    "band_aligned_bottom": _band("bottom"),
    "band_proportional": band_proportional,
    "legend_reversed": legend_reversed,
    "nearest_key_euclidean": nearest_key,
    "erase_legend": erase_legend,
    "shape_colour_only": shape_colour_only,
}

RULES = {"c7d4e6ad": tuple(C7), "d47aa2ff": motion.RULES}
NATIVE = {"c7d4e6ad": "row_key", "d47aa2ff": motion.NATIVE_RULE}


def answers(tid, g):
    """{rule name: answer or None} on one native-frame input."""
    if tid == "c7d4e6ad":
        return {name: rule(g) for name, rule in C7.items()}
    return motion.variants(g)


def surviving(tid, demonstrations):
    alive = set(RULES[tid])
    for d in demonstrations:
        target, opts = _t(d["output"]), answers(tid, d["input"])
        alive = {n for n in alive if opts[n] == target}
    return alive


def candidate_predictions(tid, demonstrations, query_input):
    """Distinct query answers (None = undefined) of the rules fitting every demonstration."""
    options = answers(tid, query_input)
    out = []
    for name in sorted(surviving(tid, demonstrations)):
        if options[name] not in out:
            out.append(options[name])
    return out


def ambiguous(tid, demonstrations, query_input):
    answers_ = candidate_predictions(tid, demonstrations, query_input)
    return len(answers_) != 1 or answers_[0] is None


# ------------------------------------------------- learned lookup readings
def moved_colours(g):
    """d47aa2ff: colours of dots that differ between the panels (input only)."""
    p = motion.panels(g)
    if p is None:
        return set()
    left, right = p
    return {max(a, right[r][c]) for r, row in enumerate(left)
            for c, a in enumerate(row) if a != right[r][c]}


def legend_colours(g):
    """c7d4e6ad: legend colours that key at least one shape cell (input only)."""
    return {row[0] for row in g if row[0] != BG and any(v != BG for v in row[1:])}


def unseen_lookup_colours(tid, demonstrations, query_input):
    """Query colours a learned colour->colour lookup has no demonstrated entry for.

    c7d4e6ad: legend colours of the query absent from the demonstration legends.
    d47aa2ff: mover colours of the query that never moved in a demonstration.
    Uses demonstration INPUTS and the query INPUT only.
    """
    pick = legend_colours if tid == "c7d4e6ad" else moved_colours
    seen = set().union(*(pick(d["input"]) for d in demonstrations))
    return pick(query_input) - seen
