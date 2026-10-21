"""Independent evidence gate + reference solver for ba1aa698 (review v7).

Written independently of factory.py, with a different mechanism:
  * frame colour = the colour of the whole outer border (all four edges must agree);
  * panel axis = the axis that has interior full frame-colour lines;
  * panel background = the colour of each panel's outermost long-side column, which
    the constructor leaves empty, rather than the most common colour;
  * motion = brute-force search for the unique 1-D shift that maps panel i onto
    panel i+1 as a full-panel image, rather than the factory's lead-coordinate method.

Hypothesis family (native constructor, extra=0): ORDER in {+1, -1}, i.e. which end
of the visible panel strip is "last". An optional global residual R (extra cells
beyond one step) is exposed only for the fixture-conflict analysis.

The gate signature matches arc_agi2.colour_evidence dispatchers:
    require_ba1aa698_evidence(demonstrations, queries, palette=None, d4=0)
`queries` needs only {'input': grid} items, and query labels are never read.
Pure numpy, with no ARC-GEN imports.
"""
import numpy as np


class MissingBa1aa698Evidence(ValueError):
    pass


def _parse(g):
    g = np.asarray(g, dtype=int)
    H, W = g.shape
    border = np.concatenate([g[0], g[-1], g[:, 0], g[:, -1]])
    if len(set(border.tolist())) != 1:
        raise ValueError('border not uniform')
    f = int(border[0])
    vlines = [x for x in range(1, W - 1) if (g[:, x] == f).all()]
    hlines = [y for y in range(1, H - 1) if (g[y, :] == f).all()]
    if vlines and not hlines:
        cuts = [0] + vlines + [W - 1]
        panels = [g[1:H - 1, a + 1:b] for a, b in zip(cuts, cuts[1:])]
    elif hlines and not vlines:
        cuts = [0] + hlines + [H - 1]
        panels = [g[a + 1:b, 1:W - 1].T for a, b in zip(cuts, cuts[1:])]
        # Transposed so that motion is always along axis 0 of each panel.
    else:
        raise ValueError('panel axis not identifiable')
    if len(panels) < 2 or len({p.shape for p in panels}) != 1 or 0 in panels[0].shape:
        raise ValueError('panels unequal or empty')
    bgs = set()
    for p in panels:
        bgs |= set(p[:, 0].tolist()) | set(p[:, -1].tolist())
    if len(bgs) != 1:
        raise ValueError('panel background not identifiable')
    return f, int(bgs.pop()), panels, bool(hlines)


def _shift(p, s, bg):
    out = np.full_like(p, bg)
    n = p.shape[0]
    if s >= 0:
        out[s:] = p[:n - s] if s < n else out[s:]
        lost = p[n - s:] if s > 0 else p[:0]
    else:
        out[:n + s] = p[-s:]
        lost = p[:-s]
    return out, bool((lost != bg).any())


def _unique_shift(a, b, bg):
    hits = []
    for s in range(-a.shape[0] + 1, a.shape[0]):
        sh, lost = _shift(a, s, bg)
        if not lost and np.array_equal(sh, b):
            hits.append(s)
    if len(hits) != 1:
        raise ValueError('panel-to-panel shift not unique')
    return hits[0]


def predict(g, order, residual=0):
    f, bg, panels, transposed = _parse(g)
    seq = panels if order > 0 else panels[::-1]
    if any(not (p != bg).any() for p in seq):
        raise ValueError('empty panel')
    steps = {_unique_shift(a, b, bg) for a, b in zip(seq, seq[1:])}
    if len(steps) != 1 or 0 in steps:
        raise ValueError('non-constant motion')
    s = steps.pop()
    s = s + (residual if s > 0 else -residual)
    nxt, lost = _shift(seq[-1], s, bg)
    if lost:
        raise ValueError('extrapolation leaves panel')
    inner = nxt.T if transposed else nxt
    out = np.full((inner.shape[0] + 2, inner.shape[1] + 2), f, dtype=int)
    out[1:-1, 1:-1] = inner
    return out.tolist()


def _try(g, h):
    try:
        return predict(g, *h)
    except ValueError:
        return None


NATIVE_HYPOTHESES = [(1, 0), (-1, 0)]
RESIDUAL_HYPOTHESES = [(o, r) for o in (1, -1) for r in (-1, 0, 1)]


def surviving(demonstrations, hypotheses=NATIVE_HYPOTHESES):
    out = []
    for h in hypotheses:
        if all(_try(d['input'], h) == [list(map(int, r)) for r in d['output']]
               for d in demonstrations):
            out.append(h)
    return out


def require_ba1aa698_evidence(demonstrations, queries, palette=None, d4=0,
                              hypotheses=NATIVE_HYPOTHESES):
    """Raise unless the demos leave exactly one full prediction per query input.

    palette/d4 are accepted for dispatch compatibility and are deliberately
    unused: the panel order and colours are read from the visible pixels."""
    alive = surviving(demonstrations, hypotheses)
    if not alive:
        raise MissingBa1aa698Evidence('ba1aa698: demonstrations fit no candidate rule')
    answers = []
    for q in queries:
        preds = [_try(q['input'], h) for h in alive]
        if any(p is None for p in preds):
            raise MissingBa1aa698Evidence('ba1aa698: a surviving rule cannot be applied to the query')
        uniq = {repr(p) for p in preds}
        if len(uniq) != 1:
            raise MissingBa1aa698Evidence('ba1aa698: demonstrations leave query rule ambiguous')
        answers.append(preds[0])
    return answers
