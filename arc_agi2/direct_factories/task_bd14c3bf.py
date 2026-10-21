def build_program(d4, palette):
    bg = int(palette[0])
    obj = int(palette[1])
    tpl = int(palette[2])
    src = '''import numpy as np
from collections import deque

BG = __BG__
OBJ = __OBJ__
TPL = __TPL__
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(g, colour):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if g[y, x] == colour and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in DIRS:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == colour:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(sorted(cells))
    return out


def _collapsed(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    y0, x0 = min(ys), min(xs)
    m = np.zeros((max(ys) - y0 + 1, max(xs) - x0 + 1), dtype=np.int8)
    for y, x in cells:
        m[y - y0, x - x0] = 1
    rows = [m[0]]
    for r in m[1:]:
        if not np.array_equal(r, rows[-1]):
            rows.append(r)
    m = np.array(rows)
    cols = [m[:, 0]]
    for j in range(1, m.shape[1]):
        if not np.array_equal(m[:, j], cols[-1]):
            cols.append(m[:, j])
    return np.array(cols).T


def _stroke_form(cells):
    S = set(cells)
    nbr = {}
    for y, x in cells:
        nbr[(y, x)] = [(dy, dx) for dy, dx in DIRS if (y + dy, x + dx) in S]
    V = set()
    for c, n in nbr.items():
        if len(n) == 2 and n[0][0] + n[1][0] == 0 and n[0][1] + n[1][1] == 0:
            continue
        V.add(c)
    if not V:
        return None
    rows = sorted(set(y for y, _ in V))
    cols = sorted(set(x for _, x in V))
    rm = {y: i for i, y in enumerate(rows)}
    cm = {x: i for i, x in enumerate(cols)}
    m = np.zeros((2 * len(rows) - 1, 2 * len(cols) - 1), dtype=np.int8)
    limit = len(cells) + 2
    for (y, x) in V:
        ay, ax = 2 * rm[y], 2 * cm[x]
        m[ay, ax] = 1
        for dy, dx in nbr[(y, x)]:
            py, px = y + dy, x + dx
            steps = 0
            while (py, px) not in V:
                py += dy
                px += dx
                steps += 1
                if (py, px) not in S or steps > limit:
                    return None
            by, bx = 2 * rm[py], 2 * cm[px]
            if by == ay:
                m[ay, min(ax, bx):max(ax, bx) + 1] = 1
            elif bx == ax:
                m[min(ay, by):max(ay, by) + 1, ax] = 1
            else:
                return None
    return m


def _key(m):
    m = np.ascontiguousarray(m, dtype=np.int8)
    return (m.shape, m.tobytes())


def _variants(m):
    keys = set()
    for k in range(4):
        r = np.rot90(m, k)
        keys.add(_key(r))
        keys.add(_key(np.fliplr(r)))
    return keys


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    tcomps = _components(g, TPL)
    if not tcomps:
        return out.tolist()
    ckeys = set()
    skeys = set()
    for t in tcomps:
        ckeys |= _variants(_collapsed(t))
        s = _stroke_form(t)
        if s is not None:
            skeys |= _variants(s)
    colours = sorted(set(int(v) for v in np.unique(g)) - {BG, TPL})
    for colour in colours:
        for cells in _components(g, colour):
            hit = _key(_collapsed(cells)) in ckeys
            if not hit:
                s = _stroke_form(cells)
                hit = s is not None and _key(s) in skeys
            if hit:
                for y, x in cells:
                    out[y, x] = TPL
    return out.tolist()
'''
    return src.replace('__BG__', str(bg)).replace('__OBJ__', str(obj)).replace('__TPL__', str(tpl))
