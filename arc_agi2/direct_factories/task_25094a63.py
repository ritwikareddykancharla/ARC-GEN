def build_program(d4, palette):
    pal = [int(v) for v in palette]
    fill = pal[4] if len(pal) > 4 else 4
    template = '''MIN_SIDE = __MIN__
FILL = __FILL__


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    if H == 0 or W == 0:
        return out
    ok = [[True] * W for _ in range(H)]
    colours = sorted(set(v for row in g for v in row))
    while True:
        best_a = 0
        best = None
        for v in colours:
            h = [0] * W
            for y in range(H):
                gy = g[y]
                oky = ok[y]
                for x in range(W):
                    if gy[x] == v and oky[x]:
                        h[x] += 1
                    else:
                        h[x] = 0
                for x0 in range(W):
                    if h[x0] < MIN_SIDE:
                        continue
                    mh = h[x0]
                    for x1 in range(x0, W):
                        hv = h[x1]
                        if hv < mh:
                            mh = hv
                        if mh < MIN_SIDE:
                            break
                        if mh * (W - x0) <= best_a:
                            break
                        wd = x1 - x0 + 1
                        if wd >= MIN_SIDE:
                            a = mh * wd
                            if a > best_a:
                                best_a = a
                                best = (y - mh + 1, x0, y, x1)
        if best is None:
            break
        y0, x0, y1, x1 = best
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                ok[yy][xx] = False
                out[yy][xx] = FILL
    return out
'''
    prog = template.replace('__MIN__', '4').replace('__FILL__', repr(int(fill)))
    return prog
