def build_program(d4, palette):
    d4 = int(d4) % 8

    def tf(dy, dx):
        if d4 >= 4:
            dx = -dx
        for _ in range(d4 % 4):
            dy, dx = dx, -dy
        return dy, dx

    pdy, pdx = tf(0, 1)
    sdy, sdx = tf(1, 0)
    head = [
        'import numpy as np',
        '',
        'BG = %d' % int(palette[0]),
        'MOTIF = %d' % int(palette[7]),
        'SPECIAL = %d' % int(palette[6]),
        'PDY, PDX = %d, %d' % (pdy, pdx),
        'SDY, SDX = %d, %d' % (sdy, sdx),
        '',
    ]
    body = '''
def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    mask = g != BG
    out = g.copy()
    if not mask.any():
        return out.tolist()
    ys, xs = np.nonzero(mask)
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    shape = mask[y0:y1 + 1, x0:x1 + 1]
    h, w = shape.shape
    pstep = (h + 1) if PDY != 0 else (w + 1)
    sstep = (h + 1) if SDY != 0 else (w + 1)

    def visible(ty, tx):
        return ty < H and ty + h > 0 and tx < W and tx + w > 0

    def stamp(ty, tx, col):
        for dy in range(h):
            yy = ty + dy
            if yy < 0 or yy >= H:
                continue
            for dx in range(w):
                xx = tx + dx
                if 0 <= xx < W and shape[dy, dx]:
                    out[yy, xx] = col

    k = 0
    while True:
        ty = y0 + PDY * pstep * k
        tx = x0 + PDX * pstep * k
        if not visible(ty, tx):
            break
        if k % 3 == 2:
            stamp(ty, tx, SPECIAL)
            m = 1
            while True:
                sy = ty + SDY * sstep * m
                sx = tx + SDX * sstep * m
                if not visible(sy, sx):
                    break
                stamp(sy, sx, SPECIAL)
                m += 1
        elif k > 0:
            stamp(ty, tx, MOTIF)
        k += 1
    return out.tolist()
'''
    return '\n'.join(head) + body
