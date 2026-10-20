TEMPLATE = '''import numpy as np

AXIS = __AXIS__
DOWN = __DOWN__
C1 = __C1__
C2 = __C2__
C5 = __C5__
C8 = __C8__
C9 = __C9__
BG = __BG__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    if AXIS == 0:
        L, M = H, W
    else:
        L, M = W, H

    def pos(t):
        return t if DOWN == 1 else L - 1 - t

    def line(m):
        return g[:, m] if AXIS == 0 else g[m, :]

    depths2 = []
    for t in range(L):
        p = pos(t)
        cross = g[p, :] if AXIS == 0 else g[:, p]
        if (cross == C2).any():
            depths2.append(t)
    if not depths2:
        return out.tolist()
    r2 = min(depths2)
    r5 = r2 + 1
    n8max = max(int((line(m) == C8).sum()) for m in range(M))
    for m in range(M):
        ln = line(m)
        n8 = int((ln == C8).sum())
        n1 = int((ln == C1).sum())
        if n8 == 0 and n1 == 0:
            continue
        new = [BG] * L
        for t in range(r2 - n8max + 1, r2 + 1):
            if 0 <= t < L:
                new[t] = C8
        for t in range(r5, min(L, r5 + n1)):
            new[t] = C1
        for t in range(r5 + n1, L):
            new[t] = C9
        for t in range(L):
            p = pos(t)
            if AXIS == 0:
                out[p, m] = new[t]
            else:
                out[m, p] = new[t]
    return out.tolist()
'''


def build_program(d4, palette):
    k = int(d4) % 4
    axis = 0 if k % 2 == 0 else 1
    down = 1 if k in (0, 3) else -1
    subs = [
        ('__AXIS__', axis),
        ('__DOWN__', down),
        ('__C1__', int(palette[1])),
        ('__C2__', int(palette[2])),
        ('__C5__', int(palette[5])),
        ('__C8__', int(palette[8])),
        ('__C9__', int(palette[9])),
        ('__BG__', int(palette[7])),
    ]
    src = TEMPLATE
    for name, val in subs:
        src = src.replace(name, str(val))
    return src
