def build_program(d4, palette):
    d4 = int(d4)
    # Original motion: shapes slide east (0, +1) toward a vertical divider.
    # d4 >= 4 first mirrors each row, so east becomes west.
    dr, dc = (0, -1) if d4 >= 4 else (0, 1)
    # Each clockwise turn maps a direction (dr, dc) to (dc, -dr): E->S->W->N.
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    horizontal = (dr == 0)
    step = dc if horizontal else dr
    template = '''import numpy as np

BG = __BG__
DIV = __DIV__
INK = __INK__
MARK = __MARK__
# HORIZONTAL True: the divider is a full column and shapes slide along rows.
# HORIZONTAL False: the divider is a full row and shapes slide along columns.
HORIZONTAL = __HORIZ__
# STEP +1: shapes move toward increasing index. STEP -1: toward decreasing index.
STEP = __STEP__


def _find_divider(g):
    H, W = g.shape
    if HORIZONTAL:
        full = [x for x in range(W) if bool(np.all(g[:, x] == DIV))]
        if full:
            return full[0]
        return int(np.argmax(np.sum(g == DIV, axis=0)))
    full = [y for y in range(H) if bool(np.all(g[y, :] == DIV))]
    if full:
        return full[0]
    return int(np.argmax(np.sum(g == DIV, axis=1)))


def _components(cells):
    cells = set(cells)
    seen = set()
    out = []
    for start in sorted(cells):
        if start in seen:
            continue
        seen.add(start)
        stack = [start]
        comp = []
        while stack:
            r, c = stack.pop()
            comp.append((r, c))
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    n = (r + a, c + b)
                    if n in cells and n not in seen:
                        seen.add(n)
                        stack.append(n)
        out.append(comp)
    return out


def _line_t(r, c):
    return (r, c) if HORIZONTAL else (c, r)


def _rc(line, t):
    return (line, t) if HORIZONTAL else (t, line)


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    d = _find_divider(g)
    n_along = W if HORIZONTAL else H
    ink = []
    for r in range(H):
        for c in range(W):
            if g[r, c] == INK:
                line, t = _line_t(r, c)
                if (STEP > 0 and t < d) or (STEP < 0 and t > d):
                    ink.append((r, c))
    comps = _components(ink)
    out = g.copy()
    for r, c in ink:
        out[r, c] = BG
    shifted = []
    for comp in comps:
        ts = [_line_t(r, c)[1] for r, c in comp]
        if STEP > 0:
            shift = (d - 1) - max(ts)
        else:
            shift = (d + 1) - min(ts)
        if HORIZONTAL:
            new = [(r, c + shift) for r, c in comp]
        else:
            new = [(r + shift, c) for r, c in comp]
        shifted.append(new)
    for new in shifted:
        for r, c in new:
            out[r, c] = INK
    wall = d - STEP
    if STEP > 0:
        far = range(d + 1, n_along)
    else:
        far = range(0, d)
    for new in shifted:
        lines = {}
        for r, c in new:
            line, t = _line_t(r, c)
            lines.setdefault(line, set()).add(t)
        for line, ts in lines.items():
            if wall in ts and len(ts) < max(ts) - min(ts) + 1:
                for t in far:
                    rr, cc = _rc(line, t)
                    out[rr, cc] = MARK
    return out.tolist()
'''
    reps = [
        ('__BG__', str(int(palette[6]))),
        ('__DIV__', str(int(palette[5]))),
        ('__INK__', str(int(palette[0]))),
        ('__MARK__', str(int(palette[2]))),
        ('__HORIZ__', 'True' if horizontal else 'False'),
        ('__STEP__', str(int(step))),
    ]
    src = template
    for key, val in reps:
        src = src.replace(key, val)
    return src
