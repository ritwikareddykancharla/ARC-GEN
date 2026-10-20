def build_program(d4, palette):
    # Canonical 'down' and 'right' unit vectors, mapped into visible coordinates.
    D = (1, 0)
    R = (0, 1)
    if d4 >= 4:
        # reversing each row flips the horizontal component
        D = (D[0], -D[1])
        R = (R[0], -R[1])
    for _ in range(d4 % 4):
        # clockwise rotation: (r, c) -> (c, H-1-r), so direction (a, b) -> (b, -a)
        D = (D[1], -D[0])
        R = (R[1], -R[0])
    bg = palette[7]
    divc = palette[4]
    hookc = palette[6]
    src = '''import numpy as np

DR, DC = %d, %d   # visible direction of canonical 'down' (away from divider into payload half)
RR, RC = %d, %d   # visible direction of canonical 'right'
BG = %d
DIV = %d
HOOK = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()

    def pd(r, c):
        return r * DR + c * DC

    def ps(r, c):
        return r * RR + c * RC

    # Locate the divider line perpendicular to the down axis.
    horizontal = DR != 0
    n = H if horizontal else W

    def line(i):
        return g[i, :] if horizontal else g[:, i]

    cand = [i for i in range(n) if (line(i) == DIV).all()]
    if not cand:
        cand = [i for i in range(n) if (line(i) == line(i)[0]).all() and line(i)[0] != BG]
    if not cand:
        return g.tolist()
    step = DR if horizontal else DC
    # pick the divider nearest the 'top' side (canonical order)
    idx = min(cand, key=lambda i: i * step)
    dproj = idx * step

    below = [(r, c) for r in range(H) for c in range(W) if pd(r, c) > dproj]
    hook = [(r, c) for (r, c) in below if g[r, c] == HOOK]
    payload = [(r, c, int(g[r, c])) for (r, c) in below if g[r, c] != BG and g[r, c] != HOOK]

    # Clear the payload half.
    for (r, c) in below:
        out[r, c] = BG
    if not hook:
        return out.tolist()

    # Move hook along -down until its leading edge touches the grid edge.
    edge = min(0, (H - 1) * DR) + min(0, (W - 1) * DC)
    top = min(pd(r, c) for (r, c) in hook)
    sh = edge - top
    moved = [(r + sh * DR, c + sh * DC) for (r, c) in hook]
    for (r, c) in moved:
        if 0 <= r < H and 0 <= c < W:
            out[r, c] = HOOK

    # Tip: extreme-left hook cell, lowest among ties.
    smin = min(ps(r, c) for (r, c) in moved)
    tips = [p for p in moved if ps(p[0], p[1]) == smin]
    tip = max(tips, key=lambda p: pd(p[0], p[1]))

    if payload:
        maxd = max(pd(r, c) for (r, c, _) in payload)
        maxs = max(ps(r, c) for (r, c, _) in payload)
        od = pd(tip[0], tip[1]) - maxd
        os_ = ps(tip[0], tip[1]) - maxs
        for (r, c, col) in payload:
            nr = r + od * DR + os_ * RR
            nc = c + od * DC + os_ * RC
            if 0 <= nr < H and 0 <= nc < W:
                out[nr, nc] = col
    return out.tolist()
''' % (D[0], D[1], R[0], R[1], bg, divc, hookc)
    return src
