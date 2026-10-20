def build_program(d4, palette):
    d4 = int(d4) % 8
    bg = int(palette[0])

    def mapc(a, b):
        if d4 >= 4:
            b = 1 - b
        for _ in range(d4 % 4):
            a, b = b, 1 - a
        return (a, b)

    ctl = mapc(0, 0)
    ctr = mapc(0, 1)
    if ctl in ((0, 0), (1, 1)):
        am, aa = ctl, ctr
    else:
        am, aa = ctr, ctl

    template = '''BG = __BG__
ANCHOR_MAIN = __AM__
ANCHOR_ANTI = __AA__


def _band_on_main(g, H, W):
    k = min(H, W)
    cm = sum(1 for i in range(k) if g[i][i] != BG)
    ca = sum(1 for i in range(k) if g[i][W - 1 - i] != BG)
    if cm == k and ca < k:
        return True
    if ca == k and cm < k:
        return False
    return cm >= ca


def _period(g, H, W, dr, dc):
    for cand in range(1, max(H, W)):
        ok = True
        for r in range(H):
            r2 = r + cand * dr
            if r2 < 0 or r2 >= H:
                continue
            for c in range(W):
                c2 = c + cand * dc
                if 0 <= c2 < W and g[r][c] != g[r2][c2]:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            return cand
    return 0


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0])
    a, b = ANCHOR_MAIN if _band_on_main(g, H, W) else ANCHOR_ANTI
    dr = 1 if a == 0 else -1
    dc = 1 if b == 0 else -1
    p = _period(g, H, W, dr, dc)
    OH, OW = 2 * H, 2 * W
    oy = 0 if a == 0 else H
    ox = 0 if b == 0 else W
    out = [[BG] * OW for _ in range(OH)]
    for y in range(OH):
        for x in range(OW):
            ly, lx = y - oy, x - ox
            while True:
                if 0 <= ly < H and 0 <= lx < W:
                    out[y][x] = g[ly][lx]
                    break
                if p == 0:
                    break
                ly -= p * dr
                lx -= p * dc
                if (dr > 0 and ly < 0) or (dr < 0 and ly >= H):
                    break
                if (dc > 0 and lx < 0) or (dc < 0 and lx >= W):
                    break
    return out
'''
    src = template.replace('__BG__', str(bg))
    src = src.replace('__AM__', repr(tuple(am)))
    src = src.replace('__AA__', repr(tuple(aa)))
    return src
