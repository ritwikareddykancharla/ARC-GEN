def build_program(d4, palette):
    black = int(palette[0])
    # Canonical frame: the black legend region lies toward -row (up) from the divider line,
    # and bars grow toward +col (right) from the legend edge.
    ur, uc = -1, 0
    br, bc = 0, 1
    if d4 >= 4:
        uc = -uc
        bc = -bc
    for _ in range(d4 % 4):
        ur, uc = uc, -ur
        br, bc = bc, -br
    template = '''import numpy as np
from collections import deque

BLACK = __BLACK__
UR, UC = __UR__, __UC__
BR, BC = __BR__, __BC__


def _count_components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    n = 0
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                n += 1
                seen[y, x] = True
                q = deque([(y, x)])
                while q:
                    cy, cx = q.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
    return n


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    rows_divider = UR != 0
    s = UR if rows_divider else UC
    n_lines = H if rows_divider else W
    order = range(n_lines) if s < 0 else range(n_lines - 1, -1, -1)
    div = None
    for i in order:
        line = g[i, :] if rows_divider else g[:, i]
        if int(line.min()) == int(line.max()) and int(line[0]) != BLACK:
            div = i
            break
    if div is None:
        return g.tolist()
    fbg = int(g[div, 0]) if rows_divider else int(g[0, div])
    rr, cc = np.indices((H, W))
    pos = rr if rows_divider else cc
    black_side = (pos - div) * s > 0
    field = (pos - div) * s < 0
    ys, xs = np.nonzero(black_side & (g != BLACK))
    legend = [(int(y), int(x)) for y, x in zip(ys, xs)]
    keycols = sorted({int(g[y, x]) for y, x in legend})
    if keycols:
        keep = np.isin(g, keycols)
    else:
        keep = np.zeros_like(g, dtype=bool)
    erase = field & (g != fbg) & ~keep
    g[erase] = fbg
    counts = {c: _count_components(field & (g == c)) for c in keycols}
    bars = []
    for y, x in legend:
        c = int(g[y, x])
        if BR == 0:
            seq = range(W) if BC > 0 else range(W - 1, -1, -1)
            cells = [(y, xx) for xx in seq]
        else:
            seq = range(H) if BR > 0 else range(H - 1, -1, -1)
            cells = [(yy, x) for yy in seq]
        bars.append((cells, c, counts.get(c, 0)))
    for cells, c, n in bars:
        for (yy, xx) in cells:
            g[yy, xx] = BLACK
    for cells, c, n in bars:
        for (yy, xx) in cells[:min(n, len(cells))]:
            g[yy, xx] = c
    return g.tolist()
'''
    src = template.replace('__BLACK__', str(black))
    src = src.replace('__UR__', str(int(ur))).replace('__UC__', str(int(uc)))
    src = src.replace('__BR__', str(int(br))).replace('__BC__', str(int(bc)))
    return src
