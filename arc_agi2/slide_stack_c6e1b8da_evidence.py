"""Portable identifiability gate for c6e1b8da (stick-pulled boxes, hidden still stacking).

Dispatch signature (matches arc_agi2.colour_evidence.require_colour_evidence):
    require_c6e1b8da_evidence(demonstrations, queries, palette=None, d4=0)
Queries are read through ``query['input']`` only; ``queries=[{'input': grid}]`` works
and any query label present is ignored.

Implementation is pure Python and deliberately different from the emitted factory
(no NumPy, no edge trimming, no re-render mask). It works in visible coordinates:
the only transform-dependent value is the background, palette[0] (0 when palette is
None). Per colour:
  still box  = bounding box when at least 3 of its corners show the colour;
  pulled box = rows holding >= 2 cells x columns holding >= 2 cells; every
               remaining cell must form one straight stick off the interior of
               one side, and the box is moved by the stick length toward it.
Each permutation of still boxes is rendered (pulled boxes on top, pairwise
disjoint, so their order is immaterial). A permutation is a valid hypothesis iff
its input render equals the grid exactly and every box shows >= 3 corners in the
output render (the constructor's draw() check). The grid is identifiable iff all
valid hypotheses render one output grid.

Errors:
  IntrinsicAmbiguity     - a QUERY input admits valid readings with different
                           outputs; no demonstration can fix a per-scene stacking
                           latent, so the query must be dropped, not re-contexted.
  MissingColourEvidence  - context shortfall: a demonstration is itself ambiguous
                           (verify() replays demos as queries) or contradicts the
                           mechanism; resample demos and keep the query.
"""
from itertools import permutations

try:  # integration inside the arc_agi2 package
    from .colour_evidence import MissingColourEvidence, IntrinsicQueryEvidence
except ImportError:  # portable use from the review folder
    try:
        from arc_agi2.colour_evidence import MissingColourEvidence, IntrinsicQueryEvidence
    except ImportError:
        class MissingColourEvidence(ValueError):
            pass
        class IntrinsicQueryEvidence(MissingColourEvidence):
            pass


class IntrinsicAmbiguity(IntrinsicQueryEvidence):
    """The query input itself admits generator-valid readings that disagree."""

    def __init__(self, message, witness=None):
        super().__init__(message)
        self.witness = witness or {}


class Unreadable(MissingColourEvidence):
    pass


def read_boxes(g, bg):
    H, W = len(g), len(g[0])
    cells = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg:
                cells.setdefault(g[r][c], []).append((r, c))
    still, pulled = [], []
    for colour in sorted(cells):
        pts = cells[colour]
        rows, cols = {}, {}
        for r, c in pts:
            rows[r] = rows.get(r, 0) + 1
            cols[c] = cols.get(c, 0) + 1
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        if sum(g[r][c] == colour for r in (r0, r1) for c in (c0, c1)) >= 3:
            if r1 - r0 < 2 or c1 - c0 < 2:
                raise Unreadable('c6e1b8da: box smaller than 3x3')
            still.append((colour, r0, r1, c0, c1, 0, 0))
            continue
        br = [r for r, n in rows.items() if n >= 2]
        bc = [c for c, n in cols.items() if n >= 2]
        if not br or not bc:
            raise Unreadable('c6e1b8da: colour %d is not a box' % colour)
        b0, b1, k0, k1 = min(br), max(br), min(bc), max(bc)
        if b1 - b0 < 2 or k1 - k0 < 2:
            raise Unreadable('c6e1b8da: box smaller than 3x3')
        body = {(r, c) for r in range(b0, b1 + 1) for c in range(k0, k1 + 1)}
        stick = sorted(set(pts) - body)
        if not body <= set(pts) or not stick:
            raise Unreadable('c6e1b8da: pulled colour %d not solid box + stick' % colour)
        sr = {r for r, _ in stick}
        sc = {c for _, c in stick}
        n = len(stick)
        if len(sc) == 1 and k0 < min(sc) < k1 and sorted(sr) == list(range(b0 - n, b0)):
            dy, dx = -n, 0
        elif len(sc) == 1 and k0 < min(sc) < k1 and sorted(sr) == list(range(b1 + 1, b1 + n + 1)):
            dy, dx = n, 0
        elif len(sr) == 1 and b0 < min(sr) < b1 and sorted(sc) == list(range(k0 - n, k0)):
            dy, dx = 0, -n
        elif len(sr) == 1 and b0 < min(sr) < b1 and sorted(sc) == list(range(k1 + 1, k1 + n + 1)):
            dy, dx = 0, n
        else:
            raise Unreadable('c6e1b8da: irregular stick for colour %d' % colour)
        pulled.append((colour, b0, b1, k0, k1, dy, dx, stick))
    return still, pulled


def _render(shape, bg, layers):
    H, W = shape
    g = [[bg] * W for _ in range(H)]
    for colour, cells in layers:
        for r, c in cells:
            if not (0 <= r < H and 0 <= c < W):
                return None
            g[r][c] = colour
    return g


def _rect(r0, r1, c0, c1):
    return [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]


def outputs(g, bg):
    """Map output-grid key -> number of valid still orders producing it."""
    still, pulled = read_boxes(g, bg)
    if len(still) > 7:
        raise Unreadable('c6e1b8da: too many still boxes')
    shape = (len(g), len(g[0]))
    top_in = [(b[0], _rect(*b[1:5]) + b[7]) for b in pulled]
    top_out = [(b[0], _rect(b[1] + b[5], b[2] + b[5], b[3] + b[6], b[4] + b[6])) for b in pulled]
    seen = set()
    for _, cells in top_out:  # moved boxes never overlap each other
        if seen & set(cells):
            raise Unreadable('c6e1b8da: moved boxes overlap')
        seen |= set(cells)
    found = {}
    for perm in permutations(still):
        base = [(b[0], _rect(*b[1:5])) for b in perm]
        if _render(shape, bg, base + top_in) != g:
            continue
        out = _render(shape, bg, base + top_out)
        if out is None:
            raise Unreadable('c6e1b8da: moved box leaves the grid')
        boxes = [(b[0], b[1], b[2], b[3], b[4]) for b in still] + \
                [(b[0], b[1] + b[5], b[2] + b[5], b[3] + b[6], b[4] + b[6]) for b in pulled]
        if all(sum(out[r][c] == col for r in (r0, r1) for c in (c0, c1)) >= 3
               for col, r0, r1, c0, c1 in boxes):
            key = tuple(map(tuple, out))
            found[key] = found.get(key, 0) + 1
    return found


def require_c6e1b8da_evidence(demonstrations, queries, palette=None, d4=0):
    bg = 0 if palette is None else palette[0]  # d4 is not needed: visible coordinates
    for i, demo in enumerate(demonstrations):
        try:
            outs = outputs(demo['input'], bg)
        except Unreadable as e:
            raise MissingColourEvidence('c6e1b8da: demo %d unreadable: %s' % (i, e))
        if len(outs) != 1:
            raise MissingColourEvidence('c6e1b8da: demo %d has %d valid outputs (context shortfall)' % (i, len(outs)))
        if 'output' in demo and [list(r) for r in next(iter(outs))] != [list(r) for r in demo['output']]:
            raise MissingColourEvidence('c6e1b8da: demo %d contradicts the slide mechanism' % i)
    for j, query in enumerate(queries):
        try:
            outs = outputs(query['input'], bg)  # Never reads query['output'].
        except Unreadable as exc:
            raise IntrinsicQueryEvidence(str(exc)) from exc
        if len(outs) != 1:
            raise IntrinsicAmbiguity('c6e1b8da: query %d has %d valid outputs from %d orders'
                                     % (j, len(outs), sum(outs.values())),
                                     {'distinct_outputs': len(outs), 'valid_orders': sum(outs.values())})
