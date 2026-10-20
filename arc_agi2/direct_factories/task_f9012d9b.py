PROGRAM_TEMPLATE = r'''
import numpy as np

HOLE = __HOLE__


def _fit(g, H, W, py, px):
    # Residue-class table of visible (non-hole) colours; None if inconsistent.
    seen = {}
    for y in range(H):
        row = g[y]
        for x in range(W):
            v = row[x]
            if v == HOLE:
                continue
            k = (y % py, x % px)
            old = seen.get(k)
            if old is None:
                seen[k] = v
            elif old != v:
                return None
    return seen


def _fill(holes, py, px, seen):
    out = {}
    for (y, x) in holes:
        k = (y % py, x % px)
        if k not in seen:
            return None
        out[(y, x)] = seen[k]
    return out


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in np.asarray(grid).tolist()]
    H = len(g)
    W = len(g[0])
    holes = [(y, x) for y in range(H) for x in range(W) if g[y][x] == HOLE]
    if not holes:
        return [row[:] for row in g]

    # Every 2-D period (row period py, column period px) that is consistent on
    # the visible cells and determines every hidden cell.
    cands = []
    for py in range(1, H + 1):
        for px in range(1, W + 1):
            seen = _fit(g, H, W, py, px)
            if seen is None:
                continue
            f = _fill(holes, py, px, seen)
            if f is None:
                continue
            cands.append((py + px, abs(py - px), py, px, f))

    if cands:
        # Orientation-symmetric ordering: smallest total period, then most square.
        cands.sort(key=lambda c: (c[0], c[1]))
        key0 = cands[0][:2]
        group = [c for c in cands if c[:2] == key0]
        fill = group[0][4]
        if any(c[4] != fill for c in group[1:]):
            # Transposed periods (a,b)/(b,a) disagree: fall back to the smallest
            # square tiling (the wallpaper tile is square in this family).
            squares = [c for c in cands if c[2] == c[3]]
            if squares:
                squares.sort(key=lambda c: c[2])
                fill = squares[0][4]
    else:
        # Degenerate: no consistent period; use the most common visible colour.
        counts = {}
        for row in g:
            for v in row:
                if v != HOLE:
                    counts[v] = counts.get(v, 0) + 1
        best = max(sorted(counts), key=lambda c: counts[c]) if counts else HOLE
        fill = {p: best for p in holes}

    ys = [p[0] for p in holes]
    xs = [p[1] for p in holes]
    y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
    out = []
    for y in range(y0, y1 + 1):
        r = []
        for x in range(x0, x1 + 1):
            v = g[y][x]
            if v == HOLE:
                v = fill[(y, x)]
            r.append(int(v))
        out.append(r)
    return out
'''


def build_program(d4, palette):
    hole = int(palette[0])
    return PROGRAM_TEMPLATE.replace('__HOLE__', str(hole))
