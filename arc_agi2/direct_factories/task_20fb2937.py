def build_program(d4, palette):
    H0, W0 = 20, 11
    lab = [[('L' if r < 6 else ('D' if r == 6 else 'C')) for c in range(W0)] for r in range(H0)]
    g = [list(row) for row in lab]
    if d4 >= 4:
        g = [row[::-1] for row in g]
    for _ in range(d4 % 4):
        g = [list(r) for r in zip(*g[::-1])]
    h = len(g)
    w = len(g[0])
    horiz = None
    idx = None
    for y in range(h):
        if all(v == 'D' for v in g[y]):
            horiz = True
            idx = y
    if horiz is None:
        for x in range(w):
            if all(g[y][x] == 'D' for y in range(h)):
                horiz = False
                idx = x
    before = (g[0][0] == 'L')
    bg = int(palette[7])
    div = int(palette[6])
    template = '''import numpy as np
from collections import deque

BG = __BG__
DIV = __DIV__
HORIZ = __HORIZ__
LEGEND_BEFORE = __BEFORE__
DEFAULT_IDX = __IDX__


def _divider(g):
    H, W = g.shape
    if HORIZ:
        cands = [y for y in range(H) if bool((g[y, :] == DIV).all())]
    else:
        cands = [x for x in range(W) if bool((g[:, x] == DIV).all())]
    if DEFAULT_IDX in cands:
        return DEFAULT_IDX
    if cands:
        return cands[0] if LEGEND_BEFORE else cands[-1]
    return DEFAULT_IDX


def _split(g, idx):
    if HORIZ:
        a, b = g[:idx, :], g[idx + 1:, :]
    else:
        a, b = g[:, :idx], g[:, idx + 1:]
    return (a, b) if LEGEND_BEFORE else (b, a)


def _components(a):
    h, w = a.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if a[y, x] == BG or seen[y, x]:
                continue
            col = int(a[y, x])
            q = deque([(y, x)])
            seen[y, x] = True
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and a[ny, nx] == col:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            comps.append((col, cells))
    return comps


def _lookup(legend):
    comps = _components(legend)
    k = 1 if HORIZ else 0
    blocks = []
    markers = []
    for col, cells in comps:
        vals = [c[k] for c in cells]
        if len(cells) > 1:
            blocks.append((col, min(vals), max(vals)))
        else:
            markers.append((col, vals[0]))
    table = {}
    for mc, m in markers:
        best = None
        for bc, lo, hi in blocks:
            d = 0 if lo <= m <= hi else min(abs(m - lo), abs(m - hi))
            if best is None or d < best[0]:
                best = (d, bc)
        if best is not None:
            table[mc] = best[1]
    return table


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    idx = _divider(g)
    legend, canvas = _split(g, idx)
    table = _lookup(legend)
    h, w = canvas.shape
    out = np.full((h, w), BG, dtype=int)
    for y in range(h):
        for x in range(w):
            c = int(canvas[y, x])
            if c == BG:
                continue
            col = table.get(c, c)
            out[max(0, y - 1):min(h, y + 2), max(0, x - 1):min(w, x + 2)] = col
    return out.tolist()
'''
    src = template.replace('__BG__', str(bg))
    src = src.replace('__DIV__', str(div))
    src = src.replace('__HORIZ__', 'True' if horiz else 'False')
    src = src.replace('__BEFORE__', 'True' if before else 'False')
    src = src.replace('__IDX__', str(int(idx)))
    return src
