def build_program(d4, palette):
    Z = int(palette[0])
    R = int(palette[2])
    C = int(palette[4])
    B = int(palette[5])
    F = int(palette[7])
    src = '''import numpy as np

ZERO = %d
RED = %d
CENTRE = %d
BG = %d
FRAME = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    reds = [(int(r), int(c)) for r, c in zip(*np.where(g == RED))]
    n = len(reds)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if max(abs(reds[i][0] - reds[j][0]), abs(reds[i][1] - reds[j][1])) <= 2:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(reds[i])

    stamps = []
    for grp in groups.values():
        rs = [p[0] for p in grp]
        cs = [p[1] for p in grp]
        rmin, rmax, cmin, cmax = min(rs), max(rs), min(cs), max(cs)
        if rmax - rmin > 2 or cmax - cmin > 2:
            continue
        cands = []
        for cy in range(max(1, rmax - 1), min(H - 2, rmin + 1) + 1):
            for cx in range(max(1, cmax - 1), min(W - 2, cmin + 1) + 1):
                if g[cy, cx] != BG:
                    continue
                w = g[cy - 1:cy + 2, cx - 1:cx + 2]
                if (w == ZERO).any():
                    continue
                cands.append((cy, cx))
        if len(cands) == 1:
            stamps.append(cands[0])

    for cy, cx in stamps:
        for y in range(cy - 1, cy + 2):
            for x in range(cx - 1, cx + 2):
                if g[y, x] != RED:
                    out[y, x] = FRAME
        out[cy, cx] = CENTRE
    return out.tolist()
''' % (Z, R, C, B, F)
    return src
