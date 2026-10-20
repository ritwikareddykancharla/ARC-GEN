def build_program(d4, palette):
    frame = int(palette[0])
    src = '''import numpy as np
from collections import Counter

FRAME = %d

def _bg(g):
    return int(Counter(np.asarray(g).ravel().tolist()).most_common(1)[0][0])

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    bg = _bg(g)
    out = g.copy()

    def get(y, x):
        if 0 <= y < H and 0 <= x < W:
            return int(g[y, x])
        return -1

    # Corner signature, in all four visible diagonal orientations:
    # bare frame arms 2 and 3 cells out along the row and column, and a
    # non-frame cell on the inner diagonal.
    corners = []
    for y in range(H):
        for x in range(W):
            for dy in (1, -1):
                for dx in (1, -1):
                    if (get(y + 2 * dy, x) == FRAME and get(y + 3 * dy, x) == FRAME and
                            get(y, x + 2 * dx) == FRAME and get(y, x + 3 * dx) == FRAME and
                            get(y + dy, x + dx) not in (FRAME, -1)):
                        corners.append((y, x, dy, dx))

    # Template: the corner whose marker colour covers the most window cells.
    best = None
    for (y, x, dy, dx) in corners:
        for d in (1, 2, 3):
            c = get(y + d * dy, x + d * dx)
            if c in (FRAME, -1) or c == bg:
                continue
            cells = []
            for u in range(-2, 4):
                for v in range(-2, 4):
                    if get(y + u * dy, x + v * dx) == c:
                        cells.append((u, v))
            if best is None or len(cells) > len(best[0]):
                best = (cells, (y, x))
            break
    if best is None:
        return out.tolist()
    tmpl, tcorner = best
    diag = [d for d in range(0, 4) if (d, d) in tmpl]
    if not diag:
        return out.tolist()
    D = max(diag)

    # Stamp the template at every other marked corner that is not yet decorated.
    for (y, x, dy, dx) in corners:
        if (y, x) == tcorner:
            continue
        c = get(y + D * dy, x + D * dx)
        if c in (FRAME, -1) or c == bg:
            continue
        if all(get(y + u * dy, x + v * dx) in (c, -1) for (u, v) in tmpl):
            continue
        for (u, v) in tmpl:
            yy, xx = y + u * dy, x + v * dx
            if 0 <= yy < H and 0 <= xx < W:
                out[yy, xx] = c
    return out.tolist()
''' % frame
    return src
