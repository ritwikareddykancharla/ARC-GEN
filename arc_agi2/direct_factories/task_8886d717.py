def build_program(d4, palette):
    bg = int(palette[7])
    red = int(palette[2])
    dot = int(palette[8])
    wall = int(palette[9])
    template = '''import numpy as np

BG = __BG__
RED = __RED__
DOT = __DOT__
WALL = __WALL__


def _wall_direction(g):
    H, W = g.shape
    edges = [
        ((-1, 0), g[0, :]),
        ((1, 0), g[H - 1, :]),
        ((0, -1), g[:, 0]),
        ((0, 1), g[:, W - 1]),
    ]
    full = [d for d, line in edges if line.size > 0 and bool((line == WALL).all())]
    if len(full) == 1:
        return full[0]
    if len(full) > 1:
        # Several full wall-coloured edges is outside the constructor domain;
        # prefer the longest such edge (first in scan order on ties).
        best = None
        best_len = -1
        for d, line in edges:
            if d in full and line.size > best_len:
                best, best_len = d, line.size
        return best
    # No complete wall edge (outside domain): use the edge holding most wall cells.
    best = None
    best_cnt = 0
    for d, line in edges:
        cnt = int((line == WALL).sum())
        if cnt > best_cnt:
            best, best_cnt = d, cnt
    return best


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    direction = _wall_direction(g)
    outside = []
    for y in range(H):
        for x in range(W):
            if g[y, x] != DOT:
                continue
            n_red = 0
            n_bg = 0
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W:
                    v = g[yy, xx]
                    if v == RED:
                        n_red += 1
                    elif v == BG:
                        n_bg += 1
            if n_red > n_bg:
                # Dot embedded in the red blob: erase it into the blob.
                out[y, x] = RED
            else:
                outside.append((y, x))
    if direction is not None:
        dy, dx = direction
        for y, x in outside:
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W and g[yy, xx] == BG:
                out[yy, xx] = DOT
    return out.tolist()
'''
    return (template.replace('__BG__', str(bg))
                    .replace('__RED__', str(red))
                    .replace('__DOT__', str(dot))
                    .replace('__WALL__', str(wall)))
