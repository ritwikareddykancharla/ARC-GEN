def build_program(d4, palette):
    def mm(A, B):
        return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(2)) for j in range(2)) for i in range(2))

    def tr(A):
        return ((A[0][0], A[1][0]), (A[0][1], A[1][1]))

    I = ((1, 0), (0, 1))
    R = ((0, 1), (-1, 0))
    F = ((1, 0), (0, -1))
    G = I
    if d4 >= 4:
        G = mm(F, G)
    for _ in range(d4 % 4):
        G = mm(R, G)
    Gi = tr(G)
    V = ((-1, 0), (0, 1))
    T = ((0, 1), (1, 0))
    R2 = ((0, 1), (-1, 0))
    R1 = ((0, -1), (1, 0))
    Hf = ((1, 0), (0, -1))
    R180 = ((-1, 0), (0, -1))
    A = ((0, -1), (-1, 0))

    def conj(M):
        X = mm(mm(G, M), Gi)
        return (X[0][0], X[0][1], X[1][0], X[1][1])

    pref = [conj(M) for M in (V, T, R2, R1)]
    all8 = pref + [conj(M) for M in (I, Hf, R180, A)]
    bg = int(palette[0])
    template = '''import numpy as np
from collections import deque

BG = __BG__
PREF = __PREF__
ALL8 = __ALL__


def _components(g, bg):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if g[y, x] != bg and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] != bg:
                                seen[ny, nx] = True
                                q.append((ny, nx))
                comps.append(sorted(cells))
    return comps


def _candidates(cells, struct, targets, mats):
    out = []
    keys = set()
    tkeys = sorted(targets.keys())
    for (a, b, c, d) in mats:
        tc = [(a * y + b * x, c * y + d * x, col) for (y, x, col) in cells]
        tm = [t for t in tc if t[2] != struct]
        if not tm:
            continue
        my, mx, mc = tm[0]
        for (ty, tx) in tkeys:
            if targets[(ty, tx)] != mc:
                continue
            dy, dx = ty - my, tx - mx
            used = []
            ok = True
            for (y, x, col) in tm:
                p = (y + dy, x + dx)
                if targets.get(p) != col:
                    ok = False
                    break
                used.append(p)
            if not ok:
                continue
            stamp = tuple(sorted((y + dy, x + dx, col) for (y, x, col) in tc))
            if stamp in keys:
                continue
            keys.add(stamp)
            out.append((stamp, frozenset(used)))
    return out


def _assign(cands):
    n = len(cands)
    choice = [None] * n

    def rec(i, used):
        if i == n:
            return True
        for cand in cands[i]:
            if cand[1] & used:
                continue
            choice[i] = cand
            if rec(i + 1, used | cand[1]):
                return True
        choice[i] = None
        return False

    if rec(0, frozenset()):
        return list(choice)
    return None


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    bg = BG
    if not np.any(g == bg):
        vals, cnts = np.unique(g, return_counts=True)
        bg = int(vals[np.argmax(cnts)])
    counts = {}
    for v in g.ravel().tolist():
        if v != bg:
            counts[v] = counts.get(v, 0) + 1
    if not counts:
        return g.tolist()
    struct = max(sorted(counts), key=lambda v: counts[v])
    comps = _components(g, bg)
    shapes = [cs for cs in comps if len(cs) > 1 and any(g[y, x] == struct for (y, x) in cs)]
    shape_cells = set()
    for cs in shapes:
        shape_cells.update(cs)
    targets = {}
    for y in range(h):
        for x in range(w):
            if g[y, x] != bg and (y, x) not in shape_cells:
                targets[(y, x)] = int(g[y, x])
    infos = [[(y, x, int(g[y, x])) for (y, x) in cs] for cs in shapes]
    choice = _assign([_candidates(cells, struct, targets, PREF) for cells in infos])
    if choice is None:
        choice = _assign([_candidates(cells, struct, targets, ALL8) for cells in infos])
    if choice is None:
        choice = []
        used = frozenset()
        for cells in infos:
            pick = None
            for cand in _candidates(cells, struct, targets, PREF) + _candidates(cells, struct, targets, ALL8):
                if not (cand[1] & used):
                    pick = cand
                    break
            if pick is not None:
                used = used | pick[1]
            choice.append(pick)
    out = g.copy()
    for (y, x) in shape_cells:
        out[y, x] = bg
    for cand in choice:
        if cand is None:
            continue
        for (y, x, col) in cand[0]:
            if 0 <= y < h and 0 <= x < w:
                out[y, x] = col
    return out.tolist()
'''
    prog = template.replace('__BG__', repr(bg))
    prog = prog.replace('__PREF__', repr(pref))
    prog = prog.replace('__ALL__', repr(all8))
    return prog
