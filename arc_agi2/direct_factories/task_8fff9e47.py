def build_program(d4, palette):
    d4 = int(d4) % 8
    # Original traversal of the 2x2 block grid: outer loop goes down (row step),
    # inner loop goes right (column step). Push both step vectors through the
    # same D4 used for the episode. Flip first (indices >= 4), then rotate
    # clockwise d4 % 4 times.
    outer = (1, 0)
    inner = (0, 1)

    def flip(v):
        return (v[0], -v[1])

    def rot(v):
        # clockwise rotation: (r, c) -> (c, H-1-r), so (dy, dx) -> (dx, -dy)
        return (v[1], -v[0])

    if d4 >= 4:
        outer, inner = flip(outer), flip(inner)
    for _ in range(d4 % 4):
        outer, inner = rot(outer), rot(inner)

    template = '''import numpy as np

# Block-grid traversal in VISIBLE coordinates (step vectors in block units).
OUTER = __OUTER__
INNER = __INNER__


def _block_order(R, C):
    oy, ox = OUTER
    iy, ix = INNER
    n_outer = R if oy != 0 else C
    n_inner = R if iy != 0 else C
    sy = 0 if (oy > 0 or iy > 0) else R - 1
    sx = 0 if (ox > 0 or ix > 0) else C - 1
    order = []
    for a in range(n_outer):
        for b in range(n_inner):
            order.append((sy + a * oy + b * iy, sx + a * ox + b * ix))
    return order


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    R, C = H // 2, W // 2
    order = _block_order(R, C)
    # The last block in the traversal is the outermost ring.
    blocks = order[::-1]
    n = len(blocks)
    N = 2 * n
    half = n
    out = np.zeros((N, N), dtype=int)
    for y in range(N):
        for x in range(N):
            k = min(y, x, N - 1 - y, N - 1 - x)
            by, bx = blocks[k]
            qy = 0 if y < half else 1
            qx = 0 if x < half else 1
            out[y, x] = g[2 * by + qy, 2 * bx + qx]
    return out.tolist()
'''
    return template.replace('__OUTER__', repr(outer)).replace('__INNER__', repr(inner))
