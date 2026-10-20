def build_program(d4, palette):
    d4 = int(d4)
    # Canonical mechanism: start cell at bottom-left, travel vector up (-1,0),
    # lateral (bounce) vector initially right (0,+1).
    tr, tc = -1, 0
    lr, lc = 0, 1
    if d4 >= 4:
        # reversing each row negates column components
        tc = -tc
        lc = -lc
    for _ in range(d4 % 4):
        # clockwise rotation maps direction (dr, dc) -> (dc, -dr)
        tr, tc = tc, -tr
        lr, lc = lc, -lr
    bg_in = int(palette[0])
    bg_out = int(palette[8])
    path = int(palette[1])
    lines = []
    lines.append('TR = %d' % tr)
    lines.append('TC = %d' % tc)
    lines.append('LR = %d' % lr)
    lines.append('LC = %d' % lc)
    lines.append('BG_IN = %d' % bg_in)
    lines.append('BG_OUT = %d' % bg_out)
    lines.append('PATH = %d' % path)
    body = '''

def _find_start(g, H, W):
    for r in range(H):
        for c in range(W):
            if g[r][c] == PATH:
                return r, c
    for r in range(H):
        for c in range(W):
            if g[r][c] != BG_IN:
                return r, c
    # fallback: the corner the canonical start maps to
    r = 0 if (TR > 0 or LR > 0) else H - 1
    c = 0 if (TC > 0 or LC > 0) else W - 1
    return r, c


def solve(demonstrations, grid):
    g = [list(row) for row in grid]
    H = len(g)
    W = len(g[0])
    sr, sc = _find_start(g, H, W)
    out = [[BG_OUT] * W for _ in range(H)]
    out[sr][sc] = PATH
    vertical_travel = (TR != 0)
    if vertical_travel:
        S = W
        s0 = sc
    else:
        S = H
        s0 = sr
    # first sideways move goes away from the wall the start touches
    if S > 1 and s0 == 0:
        sign = 1
    elif S > 1 and s0 == S - 1:
        sign = -1
    else:
        sign = (LC if vertical_travel else LR) or 1
    p = 2 * (S - 1)
    k = 1
    while True:
        r = sr + TR * k
        c = sc + TC * k
        if S == 1:
            lat = s0
        else:
            start = s0 if sign == 1 else S - 1 - s0
            m = (start + k) % p
            pos = m if m <= S - 1 else p - m
            lat = pos if sign == 1 else S - 1 - pos
        if vertical_travel:
            c = lat
        else:
            r = lat
        if not (0 <= r < H and 0 <= c < W):
            break
        out[r][c] = PATH
        k += 1
    return out
'''
    return '\n'.join(lines) + body
