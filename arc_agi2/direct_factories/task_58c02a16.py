def build_program(d4, palette):
    k = d4 % 4
    start = 1 if d4 >= 4 else 0
    corner = (start + k) % 4
    top = corner in (0, 1)
    left = corner in (0, 3)
    bg = int(palette[7])
    src = '''import numpy as np

TOP = __TOP__
LEFT = __LEFT__
BG = __BG__

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    def Y(d):
        return d if TOP else H - 1 - d
    def X(d):
        return d if LEFT else W - 1 - d
    def frame_ok(r, c):
        C = int(g[Y(r), X(c)])
        if C == BG:
            return None
        for j in range(c + 1):
            if g[Y(r), X(j)] != C:
                return None
        for i in range(r + 1):
            if g[Y(i), X(c)] != C:
                return None
        for i in range(r):
            for j in range(c):
                if g[Y(i), X(j)] == C:
                    return None
        return C
    def outside_clear(r, c):
        for i in range(H):
            for j in range(W):
                if i > r or j > c:
                    if g[Y(i), X(j)] != BG:
                        return False
        return True
    best = None
    loose = None
    for s in range(2, H + W):
        for r in range(1, H):
            c = s - r
            if c < 1 or c >= W:
                continue
            C = frame_ok(r, c)
            if C is None:
                continue
            if loose is None:
                loose = (r, c, C)
            if outside_clear(r, c):
                best = (r, c, C)
                break
        if best is not None:
            break
    if best is None:
        best = loose
    if best is None:
        return g.tolist()
    h, w, C = best
    mask = [[g[Y(i), X(j)] != BG for j in range(w)] for i in range(h)]
    A = None
    for i in range(h):
        for j in range(w):
            v = int(g[Y(i), X(j)])
            if v != BG and v != C:
                A = v
                break
        if A is not None:
            break
    if A is None:
        A = C
    out = np.full((H, W), BG, dtype=int)
    for dy in range(H):
        for dx in range(W):
            if not mask[dy % h][dx % w]:
                continue
            bi = (dy // h) % h
            bj = (dx // w) % w
            out[Y(dy), X(dx)] = A if mask[bi][bj] else C
    return out.tolist()
'''
    src = src.replace('__TOP__', 'True' if top else 'False')
    src = src.replace('__LEFT__', 'True' if left else 'False')
    src = src.replace('__BG__', str(bg))
    return src
