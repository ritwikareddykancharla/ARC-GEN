def build_program(d4, palette):
    bg = int(palette[0])
    wall = int(palette[2])
    green = int(palette[3])
    azure = int(palette[8])
    src = '''import numpy as np

BG = __BG__
WALL = __WALL__
GREEN = __GREEN__
AZURE = __AZURE__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    az = [(y, x) for y in range(H) for x in range(W) if g[y, x] == AZURE]
    if not az:
        return out.tolist()
    azs = set(az)

    def is_wall(y, x):
        v = int(g[y, x])
        return v != BG and v != AZURE

    # Does the visible azure segment already contain the bounce (V shape)?
    collinear = (len(set(y - x for y, x in az)) == 1 or
                 len(set(y + x for y, x in az)) == 1)
    pre = 0 if collinear else 1
    limit = 4 * (H + W) + 10

    def walk(y, x, dy, dx, nb):
        path = []
        for _ in range(limit):
            ny, nx = y + dy, x + dx
            if not (0 <= ny < H and 0 <= nx < W):
                return path, nb, True
            if is_wall(ny, nx):
                if nb >= 1:
                    return path, nb, False
                nb += 1
                if is_wall(ny, x):
                    dy = -dy
                else:
                    dx = -dx
                continue
            if g[ny, nx] != BG:
                return path, nb, False
            y, x = ny, nx
            path.append((y, x))
        return path, nb, False

    best = None
    best_key = None
    for (y, x) in az:
        nbrs = [(y + a, x + b) for a in (-1, 1) for b in (-1, 1)
                if (y + a, x + b) in azs]
        if len(az) == 1:
            dirs = [(a, b) for a in (-1, 1) for b in (-1, 1)]
        elif len(nbrs) == 1:
            dirs = [(y - nbrs[0][0], x - nbrs[0][1])]
        else:
            continue
        for dy, dx in dirs:
            path, nb, exited = walk(y, x, dy, dx, pre)
            key = (1 if exited else 0, 1 if nb == 1 else 0, len(path))
            if best_key is None or key > best_key:
                best_key = key
                best = path
    if best:
        for (y, x) in best:
            out[y, x] = GREEN
    return out.tolist()
'''
    src = (src.replace('__BG__', str(bg))
              .replace('__WALL__', str(wall))
              .replace('__GREEN__', str(green))
              .replace('__AZURE__', str(azure)))
    return src
