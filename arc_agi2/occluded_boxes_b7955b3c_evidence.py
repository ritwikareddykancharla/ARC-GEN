"""Independent identifiability gate for b7955b3c (plus stamps over layered boxes).

Implementation is deliberately different from the emitted solver: NumPy masks,
plus colour re-derived from the demonstrations, and stacking recovered by
top-down peeling with per-cell topmost lookup instead of a pairwise topological
sort. Query labels are never read. A query is accepted only if every
generator-valid reading (background = any non-plus colour, visible or not)
renders the same full grid. Otherwise IntrinsicAmbiguity carries a witness.
"""
import numpy as np
from .colour_evidence import MissingColourEvidence


class IntrinsicAmbiguity(ValueError):
    """The query input itself admits generator-valid readings that disagree."""

    def __init__(self, message, witness=None):
        super().__init__(message)
        self.witness = witness or {}


def plus_colour_from_demos(demonstrations):
    found = set()
    for p in demonstrations:
        a, b = np.asarray(p['input'], dtype=int), np.asarray(p['output'], dtype=int)
        if a.shape != b.shape:
            raise MissingColourEvidence('b7955b3c: demo changes grid shape')
        changed = a != b
        if not changed.any():
            continue
        cols = set(np.unique(a[changed]).tolist())
        if len(cols) != 1:
            raise MissingColourEvidence('b7955b3c: changed cells not one colour')
        c = cols.pop()
        if not np.array_equal(changed, a == c) or (b == c).any():
            raise MissingColourEvidence('b7955b3c: stamp colour not fully erased')
        found.add(c)
    if len(found) != 1:
        raise MissingColourEvidence('b7955b3c: stamp colour not established by demos')
    return found.pop()


def reading(g, plus, bg):
    """Return the rendered output for background bg, or None if invalid."""
    H, W = g.shape
    known = g != plus
    boxes = [int(c) for c in np.unique(g[known]) if c != bg]
    rect = {}
    for c in boxes:
        ys, xs = np.where(g == c)
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        if y1 - y0 > H - 3 or x1 - x0 > W - 3:
            return None
        corners = [g[y0, x0], g[y1, x0], g[y0, x1], g[y1, x1]]
        if sum(int(v == c) for v in corners) < 3:
            return None
        m = np.zeros((H, W), bool)
        m[y0:y1 + 1, x0:x1 + 1] = True
        rect[c] = m
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            inter = rect[a] & rect[b]
            if inter.any() and (g[inter] == a).any() == (g[inter] == b).any():
                return None
    # Peel from the top: a box can be the highest remaining one when every
    # known cell of its rectangle not already explained above shows its colour.
    explained = np.zeros((H, W), bool)
    remaining, peeled = set(boxes), []
    while remaining:
        top = [c for c in sorted(remaining)
               if (g[rect[c] & known & ~explained] == c).all()]
        if not top:
            return None
        c = top[0]
        peeled.append(c)
        remaining.discard(c)
        explained |= rect[c]
    out = np.full((H, W), bg, dtype=int)
    filled = np.zeros((H, W), bool)
    for c in peeled:
        fresh = rect[c] & ~filled
        out[fresh] = c
        filled |= fresh
    if not np.array_equal(out[known], g[known]):
        return None
    return out


def readings(grid, plus):
    g = np.asarray(grid, dtype=int)
    res = {}
    for bg in range(10):
        if bg == plus:
            continue
        out = reading(g, plus, bg)
        if out is not None:
            res[bg] = out
    return res


def require_occluded_boxes_evidence(demonstrations, queries, palette):
    plus = plus_colour_from_demos(demonstrations)
    if plus != palette[8]:
        raise MissingColourEvidence('b7955b3c: demo stamp colour disagrees with palette')
    for p in demonstrations:
        outs = readings(p['input'], plus).values()
        if not any(np.array_equal(o, np.asarray(p['output'])) for o in outs):
            raise MissingColourEvidence('b7955b3c: demo not explained by any valid reading')
    for q in queries:
        res = readings(q['input'], plus)
        distinct = {o.tobytes(): bg for bg, o in res.items()}
        if len(distinct) != 1:
            witness = {'valid_backgrounds': sorted(res)}
            if len(res) >= 2:
                a, b = list(distinct.values())[:2]
                diff = np.argwhere(res[a] != res[b])
                r, c = (int(v) for v in diff[0])
                witness.update(cell=[r, c], readings={str(a): int(res[a][r, c]), str(b): int(res[b][r, c])})
            raise IntrinsicAmbiguity('b7955b3c: %d distinct valid readings of query' % len(distinct), witness)
    return {'plus': plus}
