def build_program(d4, palette):
    bg = int(palette[0])
    box = int(palette[3])
    mark = int(palette[2])
    src = '''import numpy as np
from collections import deque

BG = @BG@
BOX = @BOX@
MARK = @MARK@


def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                comps.append(sorted(cells))
    return comps


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    for cells in _components(g != BG):
        marks = [(y, x) for (y, x) in cells if g[y, x] == MARK]
        if not marks:
            continue
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        my, mx = marks[0]
        opts = []
        # (marker strictly inside that edge, dy, dx, thickness perpendicular to edge)
        if my == y0 and y0 > 0:
            opts.append((x0 < mx < x1, -1, 0, y1 - y0 + 1))
        if my == y1 and y1 < H - 1:
            opts.append((x0 < mx < x1, 1, 0, y1 - y0 + 1))
        if mx == x0 and x0 > 0:
            opts.append((y0 < my < y1, 0, -1, x1 - x0 + 1))
        if mx == x1 and x1 < W - 1:
            opts.append((y0 < my < y1, 0, 1, x1 - x0 + 1))
        if not opts:
            continue
        proper = [o for o in opts if o[0]]
        _, dy, dx, t = (proper or opts)[0]
        hw = t - 1
        y, x = my + dy, mx + dx
        while 0 <= y < H and 0 <= x < W:
            for k in range(-hw, hw + 1):
                if dy != 0:
                    yy, xx = y, mx + k
                else:
                    yy, xx = my + k, x
                if 0 <= yy < H and 0 <= xx < W and g[yy, xx] == BG and out[yy, xx] == BG:
                    out[yy, xx] = MARK if k == 0 else BOX
            y += dy
            x += dx
    return out.tolist()
'''
    return src.replace('@BG@', str(bg)).replace('@BOX@', str(box)).replace('@MARK@', str(mark))
