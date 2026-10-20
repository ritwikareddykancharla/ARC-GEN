def build_program(d4, palette):
    def mul(A, B):
        return [[A[0][0]*B[0][0]+A[0][1]*B[1][0], A[0][0]*B[0][1]+A[0][1]*B[1][1]],
                [A[1][0]*B[0][0]+A[1][1]*B[1][0], A[1][0]*B[0][1]+A[1][1]*B[1][1]]]
    def tr(A):
        return [[A[0][0], A[1][0]], [A[0][1], A[1][1]]]
    I = [[1, 0], [0, 1]]
    F = [[1, 0], [0, -1]]
    R = [[0, 1], [-1, 0]]
    D = [row[:] for row in I]
    if d4 >= 4:
        D = mul(F, D)
    for _ in range(d4 % 4):
        D = mul(R, D)
    Dinv = tr(D)
    mats = []
    for k in range(8):
        M = [row[:] for row in I]
        if k & 4:
            M = mul([[0, 1], [1, 0]], M)
        if k & 1:
            M = mul([[-1, 0], [0, 1]], M)
        if k & 2:
            M = mul([[1, 0], [0, -1]], M)
        C = mul(mul(D, M), Dinv)
        mats.append((C[0][0], C[0][1], C[1][0], C[1][1]))
    bg = int(palette[0])
    shape = int(palette[4])
    mark = int(palette[2])
    head = 'BG = ' + repr(bg) + '\nSHAPE = ' + repr(shape) + '\nMARK = ' + repr(mark) + '\nMATS = ' + repr(mats) + '\n'
    body = '''
import numpy as np
from collections import deque

def _comps(g):
    h, w = g.shape
    seen = np.zeros((h, w), bool)
    out = []
    for y in range(h):
        for x in range(w):
            if g[y, x] != BG and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and g[ny, nx] != BG and not seen[ny, nx]:
                                seen[ny, nx] = True
                                q.append((ny, nx))
                out.append(sorted(cells))
    out.sort(key=lambda cs: (min(c[0] for c in cs), min(c[1] for c in cs)))
    return out

def _tf(y, x, m):
    return (m[0] * y + m[1] * x, m[2] * y + m[3] * x)

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    template = None
    targets = []
    for cells in _comps(g):
        cols = set(int(g[y, x]) for y, x in cells)
        if cols - {SHAPE, MARK}:
            template = cells
        elif SHAPE in cols and MARK in cols:
            targets.append(cells)
    if template is None:
        return out.tolist()
    tcells = [(y, x, int(g[y, x])) for y, x in template]
    core = [(y, x, c) for y, x, c in tcells if c in (SHAPE, MARK)]
    deco = [(y, x, c) for y, x, c in tcells if c not in (SHAPE, MARK)]
    if not any(c == MARK for _, _, c in core):
        return out.tolist()
    for cells in targets:
        tgt = set((y, x, int(g[y, x])) for y, x in cells)
        gm = [(y, x) for y, x, c in sorted(tgt) if c == MARK][0]
        for m in MATS:
            tc = [(_tf(y, x, m) + (c,)) for y, x, c in core]
            tm = [(y, x) for y, x, c in tc if c == MARK][0]
            dy, dx = gm[0] - tm[0], gm[1] - tm[1]
            moved = set((y + dy, x + dx, c) for y, x, c in tc)
            if moved == tgt:
                for y, x, c in deco:
                    yy, xx = _tf(y, x, m)
                    yy += dy
                    xx += dx
                    if 0 <= yy < H and 0 <= xx < W:
                        out[yy, xx] = c
                break
    return out.tolist()
'''
    return head + body
