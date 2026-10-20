def build_program(d4, palette):
    corridor = int(palette[0])
    wall = int(palette[8])
    src = '''import numpy as np
from collections import deque

CORRIDOR = %d
WALL = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    # Marker cells: every colour that is neither corridor nor wall.
    marker = [(int(y), int(x)) for y, x in np.argwhere((g != CORRIDOR) & (g != WALL))]
    if not marker:
        return out.tolist()
    # The centre and its arms sit on opposite checkerboard parities.
    # Record the colour seen on each parity, in visible coordinates.
    par_col = [None, None]
    for y, x in marker:
        par_col[(y + x) %% 2] = int(g[y, x])
    # Flood through corridor cells (4-neighbour) starting from all marker cells.
    seen = set(marker)
    dq = deque(marker)
    reached = []
    while dq:
        y, x = dq.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and (ny, nx) not in seen and g[ny, nx] == CORRIDOR:
                seen.add((ny, nx))
                dq.append((ny, nx))
                reached.append((ny, nx))
    # Paint reachable corridor cells with the parity checkerboard.
    for y, x in reached:
        c = par_col[(y + x) %% 2]
        if c is not None:
            out[y, x] = c
    return out.tolist()
''' % (corridor, wall)
    return src
