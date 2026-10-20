def build_program(d4, palette):
    k = int(d4) % 4
    flip = int(d4) >= 4

    def tv(v):
        dr, dc = v
        if flip:
            dc = -dc
        for _ in range(k):
            dr, dc = dc, -dr
        return (dr, dc)

    down = tv((1, 0))
    tie = tv((0, 1))
    line = int(palette[8])
    bar = int(palette[2])
    bg = int(palette[0])
    template = '''import numpy as np

DOWN = __DOWN__
TIE = __TIE__
LINE = __LINE__
BAR = __BAR__
BG = __BG__


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0])
    dr, dc = DOWN
    tr, tc = TIE

    def inb(r, c):
        return 0 <= r < H and 0 <= c < W

    def at(r, c):
        return g[r][c] if inb(r, c) else -1

    starts = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == LINE and not inb(r - dr, c - dc):
                rr, cc = r, c
                while inb(rr + dr, cc + dc) and g[rr + dr][cc + dc] == LINE:
                    rr += dr
                    cc += dc
                starts.append((rr, cc))
    starts.sort(key=lambda p: p[0] * tr + p[1] * tc)

    limit = 4 * (H + W) * (H + W) + 16
    for (r, c) in starts:
        steps = 0
        while steps < limit:
            steps += 1
            nr, nc = r + dr, c + dc
            if not inb(nr, nc):
                break
            if g[nr][nc] == BAR:
                d = 0
                dist = 1
                while d == 0 and dist <= H + W + 1:
                    if at(nr - dist * tr, nc - dist * tc) != BAR:
                        d = -1
                    if at(nr + dist * tr, nc + dist * tc) != BAR:
                        d = 1
                    dist += 1
                if d == 0:
                    break
                r, c = r + d * tr, c + d * tc
                if not inb(r, c):
                    break
                if g[r][c] == BG:
                    g[r][c] = LINE
            else:
                r, c = nr, nc
                if g[r][c] == BG:
                    g[r][c] = LINE
    return g
'''
    return (template.replace('__DOWN__', repr(down))
                    .replace('__TIE__', repr(tie))
                    .replace('__LINE__', repr(line))
                    .replace('__BAR__', repr(bar))
                    .replace('__BG__', repr(bg)))
