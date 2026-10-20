PROGRAM = '''import numpy as np
from collections import Counter, deque


def _components8(mask):
    mask = np.asarray(mask, bool)
    h, w = mask.shape
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    seen = np.zeros_like(mask, bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in steps:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(sorted(cells))
    return out


def _spans(divs, n):
    out = []
    s = 0
    for v in list(divs) + [n]:
        if v > s:
            out.append((s, v - 1))
        s = v + 1
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    drows = [y for y in range(H) if (g[y] == g[y, 0]).all()]
    dcols = [x for x in range(W) if (g[:, x] == g[0, x]).all()]
    # Lines in both directions must share one colour (the lattice colour).
    if drows and dcols:
        lc = Counter([int(g[y, 0]) for y in drows] + [int(g[0, x]) for x in dcols]).most_common(1)[0][0]
        drows = [y for y in drows if g[y, 0] == lc]
        dcols = [x for x in dcols if g[0, x] == lc]
    rs = _spans(drows, H)
    cs = _spans(dcols, W)
    R, C = len(rs), len(cs)
    if R == 0 or C == 0:
        return out.tolist()
    cell = np.array([[g[rs[i][0], cs[j][0]] for j in range(C)] for i in range(R)], dtype=int)
    vals, cnts = np.unique(cell, return_counts=True)
    empty = vals[np.argmax(cnts)]
    comps = _components8(cell != empty)
    multi = [c for c in comps if len(c) > 1]
    singles = [c[0] for c in comps if len(c) == 1]
    if not multi:
        return out.tolist()
    tmpl = max(multi, key=len)
    tcount = Counter(int(cell[y, x]) for y, x in tmpl)
    single_cols = set(int(cell[y, x]) for y, x in singles)
    centre = None
    cy = cx = 0
    for y, x in tmpl:
        v = int(cell[y, x])
        if tcount[v] == 1 and v in single_cols:
            centre, cy, cx = v, y, x
            break
    if centre is None:
        return out.tolist()
    tvals = [(ty, tx, int(cell[ty, tx])) for ty, tx in tmpl]
    for sy, sx in singles:
        if int(cell[sy, sx]) != centre:
            continue
        for ty, tx, v in tvals:
            ny, nx = sy + ty - cy, sx + tx - cx
            if 0 <= ny < R and 0 <= nx < C and cell[ny, nx] == empty:
                cell[ny, nx] = v
                y0, y1 = rs[ny]
                x0, x1 = cs[nx]
                out[y0:y1 + 1, x0:x1 + 1] = v
    return out.tolist()
'''


def build_program(d4, palette):
    # The mechanism (lattice detection by geometry, 8-connected components on the
    # cell grid, centre found by colour uniqueness, stamping by relative offsets
    # with clipping) is intrinsically equivariant under every D4 transform and
    # every colour permutation: no axis, direction or colour constant is used.
    # Hence the same direct-coordinate program is valid for all (d4, palette).
    return PROGRAM
