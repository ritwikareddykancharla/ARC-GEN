def build_program(d4, palette):
    pal = [int(palette[i]) for i in range(10)]
    bg = pal[0]
    rank = {}
    for o in range(10):
        rank[pal[o]] = o
    columns = (int(d4) % 4) in (1, 3)
    src = '''import numpy as np

BG = %d
RANK = %r
COLUMNS = %r


def _complement_line(vals):
    counts = {}
    for v in vals:
        if v != BG:
            counts[v] = counts.get(v, 0) + 1
    if not counts:
        return [BG for _ in vals]
    best = None
    for v, n in counts.items():
        key = (-n, RANK.get(v, 99))
        if best is None or key < best[0]:
            best = (key, v)
    c = best[1]
    return [BG if v == c else c for v in vals]


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [[BG] * W for _ in range(H)]
    if COLUMNS:
        for x in range(W):
            col = [g[y][x] for y in range(H)]
            res = _complement_line(col)
            for y in range(H):
                out[y][x] = res[y]
    else:
        for y in range(H):
            out[y] = _complement_line(g[y])
    return out
''' % (bg, rank, columns)
    return src
