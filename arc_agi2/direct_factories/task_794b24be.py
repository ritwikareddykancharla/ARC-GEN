def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(palette[i]) for i in range(10)]
    # Emit coordinates in the visible grid directly. Edge offsets must use the
    # actual dimensions, not the original 3x3 demonstration canvas.
    orders = (
        '[(0, 0), (0, 1), (0, 2), (1, 1)]',
        '[(0, w-1), (1, w-1), (2, w-1), (1, w-2)]',
        '[(h-1, w-1), (h-1, w-2), (h-1, w-3), (h-2, w-2)]',
        '[(h-1, 0), (h-2, 0), (h-3, 0), (h-2, 1)]',
        '[(0, w-1), (0, w-2), (0, w-3), (1, w-2)]',
        '[(h-1, w-1), (h-2, w-1), (h-3, w-1), (h-2, w-2)]',
        '[(h-1, 0), (h-1, 1), (h-1, 2), (h-2, 1)]',
        '[(0, 0), (1, 0), (2, 0), (1, 1)]',
    )
    return f'''import numpy as np

BG = {pal[0]}
PAINT = {pal[2]}

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    count = int(np.sum(g != BG))
    order = {orders[d4]}
    out = np.full((h, w), BG, dtype=int)
    for r, c in order[:count]:
        if 0 <= r < h and 0 <= c < w:
            out[r, c] = PAINT
    return out.tolist()
'''
