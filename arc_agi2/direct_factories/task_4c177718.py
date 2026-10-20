def build_program(d4, palette):
    def tf(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return (dr, dc)
    D = tf((1, 0))
    R = tf((0, 1))
    P = [int(x) for x in palette]
    src = '''import numpy as np

DV = %r
RV = %r
BG = %d
ONE = %d
TWO = %d
DIV = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    horiz = DV[1] == 0
    if horiz:
        divs = [y for y in range(H) if (g[y] == DIV).all()]
    else:
        divs = [x for x in range(W) if (g[:, x] == DIV).all()]
    dv = divs[0]
    sign = DV[0] + DV[1]
    if horiz:
        if sign > 0:
            o0, o1, c0, c1 = dv + 1, H, 0, W
            l0, l1 = 0, dv
        else:
            o0, o1, c0, c1 = 0, dv, 0, W
            l0, l1 = dv + 1, H
        leg = np.zeros_like(g, dtype=bool)
        leg[l0:l1, :] = True
    else:
        if sign > 0:
            o0, o1, c0, c1 = 0, H, dv + 1, W
            l0, l1 = 0, dv
        else:
            o0, o1, c0, c1 = 0, H, 0, dv
            l0, l1 = dv + 1, W
        leg = np.zeros_like(g, dtype=bool)
        leg[:, l0:l1] = True
    scene = np.zeros_like(g, dtype=bool)
    scene[o0:o1, c0:c1] = True
    out = g[o0:o1, c0:c1].copy()
    ly, lx = np.nonzero((g == ONE) & leg)
    sy, sx = np.nonzero((g == ONE) & scene)
    if len(ly) == 0 or len(sy) == 0:
        return out.tolist()
    ty = int(sy.min()) - int(ly.min())
    tx = int(sx.min()) - int(lx.min())
    py, px = np.nonzero((g == TWO) & leg)
    proj = py * DV[0] + px * DV[1]
    nmin = int(np.sum(proj == proj.min()))
    nmax = int(np.sum(proj == proj.max()))
    s = 1 if nmin > nmax else -1
    cm = leg & (g != BG) & (g != ONE) & (g != TWO) & (g != DIV)
    cy, cx = np.nonzero(cm)
    for y, x in zip(cy.tolist(), cx.tolist()):
        qy = y - 8 * RV[0] + ty + s * 3 * DV[0] - o0
        qx = x - 8 * RV[1] + tx + s * 3 * DV[1] - c0
        if 0 <= qy < out.shape[0] and 0 <= qx < out.shape[1]:
            out[qy, qx] = g[y, x]
    return out.tolist()
''' % (D, R, P[0], P[1], P[2], P[5])
    return src
