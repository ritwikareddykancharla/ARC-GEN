TEMPLATE = r'''import numpy as np

# Direct visible-coordinate program for ba1aa698 (strict, demo-consistent).
#
# Visible mechanism (the native generator rule):
#   * frame colour = corner pixel; the grid is split into equal panels by full
#     frame-coloured lines (columns or rows, read from pixels);
#   * panel background = most common colour over the panel interiors;
#   * every panel holds the same motif, translated by a constant step along the
#     panel's long axis from panel to panel;
#   * output = one framed panel holding the last panel's motif translated by
#     exactly one further step.
# Hypotheses: the time direction of the panel sequence, ORDER in {+1, -1}.
# The divider axis is not a hypothesis: it is read from the pixels.
# Every hypothesis is checked against EVERY demonstration (full grid
# equality). All surviving hypotheses must agree on the full query output.
# Otherwise the program raises: there is no default, no majority vote, no demo
# skipping, and no reset when nothing survives.


class Ambiguous(ValueError):
    pass


class Inconsistent(ValueError):
    pass


def _axis_lines(g, frame):
    H, W = g.shape
    cols = [x for x in range(W) if np.all(g[:, x] == frame)]
    rows = [y for y in range(H) if np.all(g[y, :] == frame)]
    # Dividers exist only along one axis; the other axis has just its two border lines.
    if len(cols) > 2 and len(rows) == 2:
        return 'COLS', cols
    if len(rows) > 2 and len(cols) == 2:
        return 'ROWS', rows
    raise ValueError('panel dividers not identifiable')


def _scene(g):
    g = np.asarray(g, dtype=int)
    if g.ndim != 2 or min(g.shape) < 3:
        raise ValueError('bad grid')
    frame = int(g[0, 0])
    axis, lines = _axis_lines(g, frame)
    H, W = g.shape
    if lines[0] != 0 or lines[-1] != (W - 1 if axis == 'COLS' else H - 1):
        raise ValueError('outer frame missing')
    segs = [(lines[i] + 1, lines[i + 1] - 1) for i in range(len(lines) - 1)]
    if any(b < a for a, b in segs) or len({b - a for a, b in segs}) != 1:
        raise ValueError('panels not equal')
    if axis == 'COLS':
        panels = [g[1:H - 1, a:b + 1] for a, b in segs]
    else:
        panels = [g[a:b + 1, 1:W - 1] for a, b in segs]
    allv = np.concatenate([p.ravel() for p in panels])
    vals, cnts = np.unique(allv, return_counts=True)
    if np.sum(cnts == cnts.max()) != 1:
        raise ValueError('panel background not unique')
    bg = int(vals[int(np.argmax(cnts))])
    return frame, axis, bg, panels


def _cells(p, bg):
    ys, xs = np.nonzero(p != bg)
    return [(int(y), int(x), int(p[y, x])) for y, x in zip(ys, xs)]


def _predict(g, order):
    frame, axis, bg, panels = _scene(g)
    seq = panels if order > 0 else panels[::-1]
    motifs = [_cells(p, bg) for p in seq]
    if any(not m for m in motifs):
        raise ValueError('empty panel')
    k = 0 if axis == 'COLS' else 1          # coordinate that moves
    lead = [min(c[k] for c in m) for m in motifs]
    step = lead[1] - lead[0]
    for i in range(1, len(seq)):
        d = lead[i] - lead[i - 1]
        if d != step:
            raise ValueError('step not constant')
        shifted = sorted((y + (d if k == 0 else 0), x + (d if k == 1 else 0), v)
                         for y, x, v in motifs[i - 1])
        if shifted != sorted(motifs[i]):
            raise ValueError('motif not a pure translation')
    h, w = seq[-1].shape
    inner = np.full((h, w), bg, dtype=int)
    for y, x, v in motifs[-1]:
        ny, nx = (y + step, x) if k == 0 else (y, x + step)
        if not (0 <= ny < h and 0 <= nx < w):
            raise ValueError('extrapolation leaves panel')
        inner[ny, nx] = v
    out = np.full((h + 2, w + 2), frame, dtype=int)
    out[1:h + 1, 1:w + 1] = inner
    return out.tolist()


def _try(g, order):
    try:
        return _predict(g, order)
    except ValueError:
        return None


def solve(demonstrations, grid):
    demos = list(demonstrations or [])
    survivors = []
    for order in (1, -1):
        ok = True
        for d in demos:
            pred = _try(d['input'], order)
            if pred is None or pred != [list(map(int, r)) for r in d['output']]:
                ok = False
                break
        if ok:
            survivors.append(order)
    if not survivors:
        raise Inconsistent('no hypothesis is consistent with all demonstrations')
    answers = []
    for order in survivors:
        a = _try(grid, order)
        if a is None:
            raise Ambiguous('a demo-consistent hypothesis is inapplicable to the query (context shortfall)')
        if a not in answers:
            answers.append(a)
    if len(answers) != 1:
        raise Ambiguous('surviving hypotheses disagree on the query')
    return answers[0]
'''


def build_program(d4, palette):
    # Everything is read from pixels and checked against the demonstrations. d4 and
    # palette are not used, so there is no hidden orientation or colour choice.
    return TEMPLATE
