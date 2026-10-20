def build_program(d4, palette):
    N = 16
    d4 = int(d4)

    def pt(r, c):
        if d4 >= 4:
            c = N - 1 - c
        for _ in range(d4 % 4):
            r, c = c, N - 1 - r
        return r, c

    def vec(dr, dc):
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return dr, dc

    ar, ac = pt(N - 1, 0)
    wr, wc = vec(0, 1)
    hr, hc = vec(-1, 0)
    bg = int(palette[7])
    blk = int(palette[2])
    dg = int(palette[4])
    consts = (
        'N = 16\n'
        'BG = ' + str(bg) + '\n'
        'BLK = ' + str(blk) + '\n'
        'DG = ' + str(dg) + '\n'
        'AR = ' + str(ar) + '\n'
        'AC = ' + str(ac) + '\n'
        'WR = ' + str(wr) + '\n'
        'WC = ' + str(wc) + '\n'
        'HR = ' + str(hr) + '\n'
        'HC = ' + str(hc) + '\n'
    )
    body = '''
def _bg(g):
    if np.any(g == BG):
        return BG
    vals, cnts = np.unique(g, return_counts=True)
    return int(vals[int(np.argmax(cnts))])

def _cell(i, j):
    # i steps along the height direction, j along the width direction
    return AR + i * HR + j * WR, AC + i * HC + j * WC

def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    bgc = _bg(g)
    out = np.full((N, N), BG, dtype=int)
    vals, cnts = np.unique(g[g != bgc], return_counts=True)
    if len(cnts) == 0:
        return out.tolist()
    cs = sorted(int(x) for x in cnts)
    h = min(cs[0], N)
    w = min(cs[-1], N)
    for i in range(h):
        for j in range(w):
            r, c = _cell(i, j)
            out[r, c] = BLK
    for k in range(h):
        if k < w:
            r, c = _cell(k, k)
            out[r, c] = DG
            r, c = _cell(k, w - 1 - k)
            out[r, c] = DG
    return out.tolist()
'''
    return 'import numpy as np\n' + consts + body
