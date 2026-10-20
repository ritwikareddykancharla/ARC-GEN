def build_program(d4, palette):
    k = d4 % 4
    s = -1 if d4 >= 4 else 1
    if k % 2 == 0:
        horiz = True
        direction = s if k == 0 else -s
    else:
        horiz = False
        direction = s if k == 1 else -s
    bg = int(palette[7])
    lock = int(palette[8])
    src = '''import numpy as np

BG = %d
LOCK = %d
HORIZ = %s
DIR = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    nl = H if HORIZ else W
    L = W if HORIZ else H

    def line(i):
        return g[i, :] if HORIZ else g[:, i]

    def put(out, i, p, v):
        if HORIZ:
            out[i, p] = v
        else:
            out[p, i] = v

    bands = []
    for i in range(nl):
        if (line(i) != BG).any():
            if not bands or i != bands[-1][-1] + 1:
                bands.append([])
            bands[-1].append(i)
    total = sum(len(b) for b in bands)
    area = int((g != BG).sum())
    if total and area %% total == 0:
        width = area // total
    else:
        width = 5

    keys = []
    for b in bands:
        cols = set()
        for i in b:
            for v in line(i).tolist():
                if v != BG and v != LOCK:
                    cols.add(int(v))
        for c in sorted(cols):
            keys.append((c, b, [int((line(i) == c).sum()) for i in b]))

    out = g.copy()
    out[(g != BG) & (g != LOCK)] = BG
    used = set()
    for b in bands:
        lw = [int((line(i) == LOCK).sum()) for i in b]
        cand = [n for n, (c, sb, kw) in enumerate(keys)
                if n not in used and len(sb) == len(b)
                and all(lw[j] + kw[j] == width for j in range(len(b)))]
        if not cand:
            continue
        n = cand[0]
        used.add(n)
        c, sb, kw = keys[n]
        for j, i in enumerate(b):
            for t in range(kw[j]):
                if DIR == 1:
                    p = lw[j] + t
                else:
                    p = L - 1 - lw[j] - t
                if 0 <= p < L:
                    put(out, i, p, c)
    return out.tolist()
''' % (bg, lock, 'True' if horiz else 'False', direction)
    return src
