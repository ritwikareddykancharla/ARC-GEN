def build_program(d4, palette):
    def vec(dr, dc):
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return (dr, dc)
    ux = vec(0, 1)
    uy = vec(1, 0)
    sq = int(palette[1])
    head = 'import numpy as np\n\nUX = (%d, %d)\nUY = (%d, %d)\nSQ = %d\n' % (ux[0], ux[1], uy[0], uy[1], sq)
    body = '''
def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    cells = np.argwhere(g == SQ)
    if len(cells) == 0:
        return g.tolist()
    s = cells[:, 0] * (UX[0] + UY[0]) + cells[:, 1] * (UX[1] + UY[1])
    o = cells[int(np.argmin(s))]
    e = cells[int(np.argmax(s))]
    o0, o1 = int(o[0]), int(o[1])

    def pos(a, b):
        return (o0 + a * UY[0] + b * UX[0], o1 + a * UY[1] + b * UX[1])

    def inside(p):
        return 0 <= p[0] < H and 0 <= p[1] < W

    L = 0
    while inside(pos(0, L)) and g[pos(0, L)] == SQ:
        L += 1
    L = max(L, 1)
    br = int(e[0]) - (L - 1) * (UX[0] + UY[0])
    bc = int(e[1]) - (L - 1) * (UX[1] + UY[1])
    dr, dc = br - o0, bc - o1
    aB = dr * UY[0] + dc * UY[1]
    bB = dr * UX[0] + dc * UX[1]
    T = aB + L + 2
    WD = bB + L + 2
    vals, counts = np.unique(g, return_counts=True)
    common = int(vals[int(np.argmax(counts))])

    def read(a, b, default):
        p = pos(a, b)
        return int(g[p]) if inside(p) else default

    bg = read(0, L + 1, common)
    c2 = read(0, L, bg)
    c1 = read(0, L + 2, bg)
    c3 = read(L, 0, bg)
    out = np.full((H, W), bg, dtype=int)

    def put(a, b, c):
        p = pos(a, b)
        if inside(p):
            out[p] = c

    for ra, rb in ((0, 0), (0, WD - 2 - L), (T - 2 - L, 0), (T - 2 - L, WD - 2 - L)):
        for i in range(L):
            for j in range(L):
                put(ra + i, rb + j, SQ)
    for b in range(L + 2, WD - L - 3, 4):
        for i in range(L):
            put(i, b, c1)
            put(T - 3 - i, b, c1)
    for a in range(L + 2, T - L - 3, 4):
        for i in range(L):
            put(a, i, c1)
            put(a, WD - 3 - i, c1)
    for b in range(L, WD - L - 2):
        put(-1, b, c2)
        put(T - 2, b, c2)
    for a in range(L, T - L - 2):
        put(a, -1, c3)
        put(a, WD - 2, c3)
    for b in range(L, WD - L - 1, 4):
        for i in range(L):
            put(i, b, c2)
            put(T - 3 - i, b, c2)
    for a in range(L, T - L - 1, 4):
        for i in range(L):
            put(a, i, c3)
            put(a, WD - 3 - i, c3)
    return out.tolist()
'''
    return head + body
