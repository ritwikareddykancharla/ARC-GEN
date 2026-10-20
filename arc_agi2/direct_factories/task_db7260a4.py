BODY = '''
def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    wall = g == WALL
    LR, LC = GC, GR

    def inb(r, c):
        return 0 <= r < H and 0 <= c < W

    cells = [(int(a), int(b)) for a, b in np.argwhere(g == WATER)]
    if not cells:
        return out.tolist()
    top = [p for p in cells if not inb(p[0] - GR, p[1] - GC)]
    r, c = (top or cells)[0]
    out[r, c] = BG

    def line_nonempty(rr, cc):
        if GR != 0:
            return bool(np.any(g[rr, :] != BG))
        return bool(np.any(g[:, cc] != BG))

    for _ in range(4 * H * W + 4):
        while inb(r + GR, c + GC) and not wall[r + GR, c + GC]:
            r += GR
            c += GC
        if not inb(r + GR, c + GC):
            if GR == 1:
                out[H - 1, :] = WATER
            elif GR == -1:
                out[0, :] = WATER
            elif GC == 1:
                out[:, W - 1] = WATER
            else:
                out[:, 0] = WATER
            return out.tolist()
        holes = []
        for s in (1, -1):
            k = 1
            while True:
                rr = r + s * k * LR
                cc = c + s * k * LC
                if not inb(rr, cc) or wall[rr, cc]:
                    break
                if inb(rr + GR, cc + GC) and not wall[rr + GR, cc + GC]:
                    holes.append((k, rr, cc))
                k += 1
        if holes:
            holes.sort(key=lambda t: t[0])
            _, r, c = holes[0]
            continue
        rr, cc = r, c
        while inb(rr, cc):
            if not line_nonempty(rr, cc):
                break
            for s in (1, -1):
                k = 0
                while True:
                    ar = rr + s * k * LR
                    ac = cc + s * k * LC
                    if not inb(ar, ac) or wall[ar, ac]:
                        break
                    out[ar, ac] = WATER
                    k += 1
            rr -= GR
            cc -= GC
        return out.tolist()
    return out.tolist()
'''


def build_program(d4, palette):
    d4 = int(d4) % 8
    dr, dc = 1, 0
    if d4 >= 4:
        dc = -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    lines = [
        'import numpy as np',
        'GR = %d' % dr,
        'GC = %d' % dc,
        'BG = %d' % int(palette[0]),
        'WATER = %d' % int(palette[1]),
        'WALL = %d' % int(palette[2]),
    ]
    return chr(10).join(lines) + chr(10) + BODY
