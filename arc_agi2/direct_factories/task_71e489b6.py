def build_program(d4, palette):
    zero = int(palette[0])
    one = int(palette[1])
    ring = int(palette[7])
    template = '''import numpy as np

ZERO = __ZERO__
ONE = __ONE__
RING = __RING__


def _card_count(mask):
    p = np.pad(mask, 1)
    return (p[:-2, 1:-1].astype(int) + p[2:, 1:-1].astype(int)
            + p[1:-1, :-2].astype(int) + p[1:-1, 2:].astype(int))


def _peel(mask, spare_border):
    m = mask.copy()
    H, W = m.shape
    removed = np.zeros_like(m)
    while True:
        kill = m & (_card_count(m) <= 1)
        if spare_border:
            for y, x in np.argwhere(kill):
                if y == 0 or y == H - 1 or x == 0 or x == W - 1:
                    hood = m[max(0, y - 1):min(H, y + 2), max(0, x - 1):min(W, x + 2)]
                    same = int(hood.sum()) - 1
                    if 2 * same > hood.size - 1:
                        kill[y, x] = False
        if not kill.any():
            break
        removed |= kill
        m &= ~kill
    return m, removed


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    is_zero = g == ZERO
    is_one = g == ONE
    _, specks = _peel(is_one, True)
    zero_after = is_zero | specks
    _, peeled_zero = _peel(zero_after, False)
    holes = peeled_zero & is_zero
    out = g.copy()
    out[specks] = ZERO
    p = np.pad(holes, 1)
    dil = np.zeros((H, W), dtype=bool)
    for dy in range(3):
        for dx in range(3):
            dil |= p[dy:dy + H, dx:dx + W]
    out[dil & ~holes] = RING
    return [[int(v) for v in row] for row in out]
'''
    return (template.replace('__ZERO__', repr(zero))
                    .replace('__ONE__', repr(one))
                    .replace('__RING__', repr(ring)))
