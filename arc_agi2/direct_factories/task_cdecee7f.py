def build_program(d4, palette):
    d = int(d4) % 8
    bg = int(palette[0])

    def fwd(r, c, H, W):
        # D4 forward map: for d>=4 reverse each row, then rotate clockwise d%4 times
        if d >= 4:
            c = W - 1 - c
        for _ in range(d % 4):
            r, c, H, W = c, H - 1 - r, W, H
        return r, c

    def axis_sign(p, q):
        dr = q[0] - p[0]
        dc = q[1] - p[1]
        if dr != 0:
            return 0, (1 if dr > 0 else -1)
        return 1, (1 if dc > 0 else -1)

    H = W = 10
    o = fwd(0, 0, H, W)
    px = fwd(0, 1, H, W)   # original +column direction
    py = fwd(1, 0, H, W)   # original +row direction (tie-break)
    pa, ps = axis_sign(o, px)
    sa, ss = axis_sign(o, py)

    slots = []
    for idx in range(9):
        r = idx // 3
        c = idx % 3
        if r == 1:
            c = 2 - c
        slots.append(tuple(int(v) for v in fwd(r, c, 3, 3)))

    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('PRIMARY_AXIS = %d' % pa)
    lines.append('PRIMARY_SIGN = %d' % ps)
    lines.append('SECONDARY_AXIS = %d' % sa)
    lines.append('SECONDARY_SIGN = %d' % ss)
    lines.append('SLOTS = %r' % (slots,))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.asarray(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    pix = []')
    lines.append('    for y in range(h):')
    lines.append('        for x in range(w):')
    lines.append('            v = int(g[y, x])')
    lines.append('            if v != BG:')
    lines.append('                pos = (y, x)')
    lines.append('                pix.append((PRIMARY_SIGN * pos[PRIMARY_AXIS], SECONDARY_SIGN * pos[SECONDARY_AXIS], v))')
    lines.append('    pix.sort()')
    lines.append('    out = [[BG] * 3 for _ in range(3)]')
    lines.append('    for i, item in enumerate(pix[:9]):')
    lines.append('        r, c = SLOTS[i]')
    lines.append('        out[r][c] = item[2]')
    lines.append('    return out')
    return '\n'.join(lines) + '\n'
