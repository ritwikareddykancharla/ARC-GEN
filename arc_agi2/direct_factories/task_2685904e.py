def build_program(d4, palette):
    r = int(d4) % 4
    # Original: horizontal divider (row 6), bars grow from the divider toward row 0 (up).
    # A horizontal flip (d4>=4) only permutes columns, so it changes neither the divider axis nor the bar direction.
    # Clockwise rotation: (row, col) -> (col, H-1-row).
    horiz = r in (0, 2)
    direc = -1 if r in (0, 3) else 1
    bg = int(palette[0])
    dv = int(palette[5])
    head = 'import numpy as np\nfrom collections import Counter\n\nHORIZ = %s\nDIR = %d\nBG = %d\nDIV = %d\n' % ('True' if horiz else 'False', direc, bg, dv)
    body = '''

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    L = H if HORIZ else W
    M = W if HORIZ else H

    def line(i):
        return g[i, :] if HORIZ else g[:, i]

    cands = [i for i in range(L) if (line(i) == DIV).all()]
    if not cands:
        cands = [i for i in range(L) if line(i)[0] != BG and (line(i) == line(i)[0]).all()]
    if not cands:
        return out.tolist()
    d = cands[0]
    if DIR < 0:
        cside = list(range(0, d))
        dside = list(range(d + 1, L))
    else:
        cside = list(range(d + 1, L))
        dside = list(range(0, d))
    n = int(sum(int(np.sum(line(i) != BG)) for i in cside))
    if n <= 0 or not dside:
        return out.tolist()
    di = max(dside, key=lambda i: int(np.sum(line(i) != BG)))
    data = line(di)
    counts = Counter(int(v) for v in data if v != BG)
    for j in range(M):
        c = int(data[j])
        if c == BG or counts[c] != n:
            continue
        for k in range(1, n + 1):
            i = d + DIR * k
            if 0 <= i < L:
                if HORIZ:
                    out[i, j] = c
                else:
                    out[j, i] = c
    return out.tolist()
'''
    return head + body
