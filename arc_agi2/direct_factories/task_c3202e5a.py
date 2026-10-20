def build_program(d4, palette):
    bg = int(palette[0])
    template = '''import numpy as np

# Panel background (original colour 0) after the episode palette.
BG = __BG__


def _period_lines(g, axis):
    # Find evenly spaced divider lines along this axis: every line at
    # positions s, 2s+1, 3s+2, ... is one uniform non-background colour,
    # and the total extent is k*(s+1)-1.
    n = g.shape[axis]
    for s in range(1, n):
        if (n + 1) % (s + 1):
            continue
        pos = list(range(s, n, s + 1))
        if not pos:
            continue
        colour = None
        ok = True
        for p in pos:
            line = g[p, :] if axis == 0 else g[:, p]
            c = int(line[0])
            if c == BG or not bool((line == c).all()):
                ok = False
                break
            if colour is None:
                colour = c
            elif c != colour:
                ok = False
                break
        if ok:
            return pos, colour
    return None


def _spans(cuts, n):
    edges = [-1] + sorted(cuts) + [n]
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        if b - a > 1:
            out.append((a + 1, b - 1))
    return out


def _panels(g):
    r = _period_lines(g, 0)
    c = _period_lines(g, 1)
    if r is not None and c is not None and r[1] == c[1]:
        rcuts, ccuts = r[0], c[0]
    else:
        raise ValueError("No consistent periodic panel dividers")
    ys = _spans(rcuts, g.shape[0])
    xs = _spans(ccuts, g.shape[1])
    return [(y0, x0, y1, x1) for (y0, y1) in ys for (x0, x1) in xs]


def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    boxes = _panels(g)
    candidates = []
    for y0, x0, y1, x1 in boxes:
        p = g[y0:y1 + 1, x0:x1 + 1]
        cols = set(int(v) for v in np.unique(p))
        if BG in cols and len(cols) == 2:
            candidates.append(p)
    if len(candidates) != 1:
        raise ValueError("Expected exactly one background-plus-one-colour panel")
    return candidates[0].copy().tolist()
'''
    return template.replace('__BG__', str(bg))
