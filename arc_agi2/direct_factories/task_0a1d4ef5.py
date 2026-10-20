def build_program(d4, palette):
    bg = int(palette[0])
    nx_fixed = 3 if (int(d4) % 4) in (0, 2) else 0
    ny_fixed = 0 if nx_fixed else 3
    src = '''
from collections import deque

BG = __BG__
NX_FIXED = __NX__
NY_FIXED = __NY__

def _components(g, h, w):
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if seen[y][x] or g[y][x] == BG:
                continue
            c = g[y][x]
            seen[y][x] = True
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == c:
                        seen[ny][nx] = True
                        q.append((ny, nx))
            comps.append((c, cells))
    return comps

def _groups(intervals):
    gs = []
    for a, b in sorted(set(intervals)):
        if gs and a <= gs[-1][1]:
            gs[-1][1] = max(gs[-1][1], b)
        else:
            gs.append([a, b])
    return gs

def _interval_layout(rects):
    yg = _groups([(b[0], b[2]) for c, b in rects])
    xg = _groups([(b[1], b[3]) for c, b in rects])
    res = [[BG] * len(xg) for _ in range(len(yg))]
    for c, b in sorted(rects, key=lambda t: (t[1][0], t[1][1])):
        r = [i for i, (a, z) in enumerate(yg) if a <= b[0] <= z][0]
        k = [i for i, (a, z) in enumerate(xg) if a <= b[1] <= z][0]
        res[r][k] = int(c)
    return res

def _bands_ok(idx_of, n, nb, lo_i, hi_i, rects):
    los = [None] * nb
    his = [None] * nb
    for i in range(n):
        k = idx_of[i]
        lo = rects[i][1][lo_i]
        hi = rects[i][1][hi_i]
        los[k] = lo if los[k] is None else min(los[k], lo)
        his[k] = hi if his[k] is None else max(his[k], hi)
    for k in range(nb - 1):
        if his[k] is None or los[k + 1] is None or his[k] >= los[k + 1]:
            return False
    return True

def _band_layout(rects):
    n = len(rects)
    if n == 0:
        return None
    if NX_FIXED:
        if n % NX_FIXED:
            return None
        nx = NX_FIXED
        ny = n // nx
    else:
        if n % NY_FIXED:
            return None
        ny = NY_FIXED
        nx = n // ny
    if nx < 1 or ny < 1:
        return None
    by_y = sorted(range(n), key=lambda i: (rects[i][1][0], rects[i][1][1]))
    by_x = sorted(range(n), key=lambda i: (rects[i][1][1], rects[i][1][0]))
    row = [0] * n
    col = [0] * n
    for rank, i in enumerate(by_y):
        row[i] = rank // nx
    for rank, i in enumerate(by_x):
        col[i] = rank // ny
    if not _bands_ok(row, n, ny, 0, 2, rects):
        return None
    if not _bands_ok(col, n, nx, 1, 3, rects):
        return None
    res = [[None] * nx for _ in range(ny)]
    for i in range(n):
        if res[row[i]][col[i]] is not None:
            return None
        res[row[i]][col[i]] = int(rects[i][0])
    for r in range(ny):
        for k in range(nx):
            if res[r][k] is None:
                return None
    return res

def solve(demonstrations, grid):
    g = [list(map(int, r)) for r in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    comps = _components(g, h, w)
    cand = []
    covered = set()
    for c, cells in comps:
        ys = [p[0] for p in cells]
        xs = [p[1] for p in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        hh, ww = y1 - y0 + 1, x1 - x0 + 1
        if hh >= 3 and ww >= 3 and len(cells) == hh * ww:
            cand.append((c, (y0, x0, y1, x1)))
            covered.update(cells)
    noise = set()
    for y in range(h):
        for x in range(w):
            v = g[y][x]
            if v != BG and (y, x) not in covered:
                noise.add(v)
    rects = [r for r in cand if r[0] not in noise]
    if not rects:
        rects = cand
    if not rects:
        return [[BG]]
    res = _band_layout(rects)
    if res is None:
        res = _interval_layout(rects)
    return res
'''
    return src.replace('__BG__', str(bg)).replace('__NX__', str(nx_fixed)).replace('__NY__', str(ny_fixed))
