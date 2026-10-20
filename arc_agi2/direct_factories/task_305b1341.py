def build_program(d4, palette):
    H0, W0 = 7, 11
    def fwd(r, c):
        h, w = H0, W0
        if d4 >= 4:
            c = w - 1 - c
        for _ in range(d4 % 4):
            r, c = c, h - 1 - r
            h, w = w, h
        return r, c, h, w
    r0, c0, h, w = fwd(0, 0)
    r1, c1, _, _ = fwd(1, 0)
    r2, c2, _, _ = fwd(0, 1)
    row_end = (r0 == h - 1)
    col_end = (c0 == w - 1)
    di = (r1 - r0, c1 - c0)
    dj = (r2 - r0, c2 - c0)
    bg = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('BG = %d' % bg)
    lines.append('ROW_END = %s' % ('True' if row_end else 'False'))
    lines.append('COL_END = %s' % ('True' if col_end else 'False'))
    lines.append('DI = (%d, %d)' % di)
    lines.append('DJ = (%d, %d)' % dj)
    body = '''
def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    br = h - 1 if ROW_END else 0
    bc = w - 1 if COL_END else 0
    def cell(i, j):
        return (br + i * DI[0] + j * DJ[0], bc + i * DI[1] + j * DJ[1])
    def inb(p):
        return 0 <= p[0] < h and 0 <= p[1] < w
    legend = []
    cells = []
    i = 0
    while True:
        p = cell(i, 0)
        q = cell(i, 1)
        if not (inb(p) and inb(q)):
            break
        a = int(g[p])
        b = int(g[q])
        if a == BG or b == BG:
            break
        legend.append((a, b))
        cells.append(p)
        cells.append(q)
        i += 1
    field = g.copy()
    for p in cells:
        field[p] = BG
    out = field.copy()
    for a, b in reversed(legend):
        ys, xs = np.where(field == a)
        if len(ys) == 0:
            continue
        y0 = max(int(ys.min()) - 1, 0)
        y1 = min(int(ys.max()) + 1, h - 1)
        x0 = max(int(xs.min()) - 1, 0)
        x1 = min(int(xs.max()) + 1, w - 1)
        out[y0:y1 + 1, x0:x1 + 1] = b
    mask = field != BG
    out[mask] = field[mask]
    return out.tolist()
'''
    return '\n'.join(lines) + '\n' + body
