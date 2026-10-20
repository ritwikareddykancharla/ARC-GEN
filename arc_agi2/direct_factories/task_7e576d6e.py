def build_program(d4, palette):
    # Map the original travel axes into visible coordinates.
    # D4 convention: for d4>=4 reverse each row first, then rotate clockwise d4%4 times.
    def img(dr, dc):
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return dr, dc
    # In the original family the path always travels toward increasing index
    # across the walls: +row when walls are rows, +col when walls are columns.
    # The original row-axis and col-axis images become the visible axes; whichever
    # image is vertical gives the travel sign for visible row-walls, and whichever
    # is horizontal gives the sign for visible column-walls.
    row_sign = 1
    col_sign = 1
    for dr, dc in (img(1, 0), img(0, 1)):
        if dc == 0:
            row_sign = 1 if dr > 0 else -1
        if dr == 0:
            col_sign = 1 if dc > 0 else -1
    template = '''import numpy as np
from collections import Counter

# Travel direction across horizontal walls (+1 = downward, -1 = upward).
ROW_WALL_TRAVEL = __ROW_SIGN__
# Travel direction across vertical walls (+1 = rightward, -1 = leftward).
COL_WALL_TRAVEL = __COL_SIGN__


def _majority(vals):
    return Counter(vals).most_common(1)[0][0]


def _gate_centre(line, wallc):
    idx = [i for i, v in enumerate(line) if v != wallc]
    if not idx:
        return len(line) // 2
    return int(round(sum(idx) / len(idx)))


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    bg = _majority(g.ravel().tolist())
    wall_rows = [r for r in range(H) if np.all(g[r, :] != bg)]
    wall_cols = [c for c in range(W) if np.all(g[:, c] != bg)]
    out = g.copy()
    if not wall_rows and not wall_cols:
        return out.tolist()
    horizontal = len(wall_rows) > 0 and len(wall_rows) >= len(wall_cols)

    if horizontal:
        # Walls are rows; the path advances vertically and slides horizontally.
        d = ROW_WALL_TRAVEL
        wall_set = set(wall_rows)
        gates = {}
        for w in wall_rows:
            line = g[w, :].tolist()
            gates[w] = _gate_centre(line, _majority(line))
        dots = [(r, c) for r in range(H) if r not in wall_set
                for c in range(W) if g[r, c] != bg]
        if len(dots) < 2:
            return out.tolist()
        dots.sort(key=lambda p: (d * p[0], p[1]))
        start, end = dots[0], dots[-1]
        colr = int(g[start[0], start[1]])

        def vline(c, r0, r1):
            a, b = sorted((r0, r1))
            out[a:b + 1, c] = colr

        def hline(r, c0, c1):
            a, b = sorted((c0, c1))
            out[r, a:b + 1] = colr

        cy, cx = start
        for w in sorted(wall_rows, key=lambda w: d * w):
            r = w - d
            vline(cx, cy, r)
            hline(r, cx, gates[w])
            cy, cx = r, gates[w]
        vline(cx, cy, end[0])
        hline(end[0], cx, end[1])
    else:
        # Walls are columns; the path advances horizontally and slides vertically.
        d = COL_WALL_TRAVEL
        wall_set = set(wall_cols)
        gates = {}
        for w in wall_cols:
            line = g[:, w].tolist()
            gates[w] = _gate_centre(line, _majority(line))
        dots = [(r, c) for c in range(W) if c not in wall_set
                for r in range(H) if g[r, c] != bg]
        if len(dots) < 2:
            return out.tolist()
        dots.sort(key=lambda p: (d * p[1], p[0]))
        start, end = dots[0], dots[-1]
        colr = int(g[start[0], start[1]])

        def vline(c, r0, r1):
            a, b = sorted((r0, r1))
            out[a:b + 1, c] = colr

        def hline(r, c0, c1):
            a, b = sorted((c0, c1))
            out[r, a:b + 1] = colr

        cy, cx = start
        for w in sorted(wall_cols, key=lambda w: d * w):
            c = w - d
            hline(cy, cx, c)
            vline(c, cy, gates[w])
            cy, cx = gates[w], c
        hline(cy, cx, end[1])
        vline(end[1], cy, end[0])
    return out.tolist()
'''
    return template.replace('__ROW_SIGN__', str(row_sign)).replace('__COL_SIGN__', str(col_sign))
