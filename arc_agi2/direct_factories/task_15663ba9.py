def build_program(d4, palette):
    bg = int(palette[0])
    convex = int(palette[4])
    concave = int(palette[2])
    template = '''import numpy as np
from collections import deque

BG = __BG__
CONVEX = __CONVEX__
CONCAVE = __CONCAVE__
STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    fg = g != BG
    out = g.copy()
    seen = np.zeros((H, W), dtype=bool)
    for sy in range(H):
        for sx in range(W):
            if not fg[sy, sx] or seen[sy, sx]:
                continue
            # Collect one closed outline (4-connected foreground component).
            comp = []
            q = deque([(sy, sx)])
            seen[sy, sx] = True
            while q:
                cy, cx = q.popleft()
                comp.append((cy, cx))
                for dy, dx in STEPS:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and fg[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            inloop = np.zeros((H, W), dtype=bool)
            for y, x in comp:
                inloop[y, x] = True
            # Cells reachable from the border without crossing this outline are outside it.
            outside = np.zeros((H, W), dtype=bool)
            q = deque()
            for y in range(H):
                for x in range(W):
                    if (y in (0, H - 1) or x in (0, W - 1)) and not inloop[y, x] and not outside[y, x]:
                        outside[y, x] = True
                        q.append((y, x))
            while q:
                cy, cx = q.popleft()
                for dy, dx in STEPS:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and not inloop[ny, nx] and not outside[ny, nx]:
                        outside[ny, nx] = True
                        q.append((ny, nx))
            convex_cells, concave_cells = [], []
            for y, x in comp:
                nb = [(dy, dx) for dy, dx in STEPS
                      if 0 <= y + dy < H and 0 <= x + dx < W and fg[y + dy, x + dx]]
                if len(nb) != 2:
                    continue
                (a, b), (c, d) = nb
                if a + c == 0 and b + d == 0:
                    continue  # straight run
                yy, xx = y + a + c, x + b + d
                inside = (0 <= yy < H and 0 <= xx < W and
                          not inloop[yy, xx] and not outside[yy, xx])
                (convex_cells if inside else concave_cells).append((y, x))
            for y, x in convex_cells:
                out[y, x] = CONVEX
            for y, x in concave_cells:
                out[y, x] = CONCAVE
    return out.tolist()
'''
    return (template.replace('__BG__', str(bg))
                    .replace('__CONVEX__', str(convex))
                    .replace('__CONCAVE__', str(concave)))
