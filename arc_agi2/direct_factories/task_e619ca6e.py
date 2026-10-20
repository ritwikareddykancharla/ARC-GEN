def build_program(d4, palette):
    # Direction of the cascade in original coordinates is 'down' = (1, 0).
    # Apply the episode transform to this direction vector:
    #   row reversal (d4>=4): (dr, dc) -> (dr, -dc)
    #   one clockwise rotation: (dr, dc) -> (dc, -dr)
    dr, dc = 1, 0
    if d4 >= 4:
        dr, dc = dr, -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    bg = int(palette[0])
    fg = int(palette[3])
    src = '''import numpy as np

DY = %d
DX = %d
BG = %d
FG = %d


def _components(g, H, W):
    seen = [[False] * W for _ in range(H)]
    comps = []
    for y in range(H):
        for x in range(W):
            if g[y][x] != BG and not seen[y][x]:
                col = g[y][x]
                stack = [(y, x)]
                seen[y][x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for ddy, ddx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + ddy, cx + ddx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                comps.append((col, cells))
    return comps


def _stamp(out, H, W, y0, x0, h, w, col):
    ya, yb = max(0, y0), min(H, y0 + h)
    xa, xb = max(0, x0), min(W, x0 + w)
    if ya < yb and xa < xb:
        for yy in range(ya, yb):
            row = out[yy]
            for xx in range(xa, xb):
                row[xx] = col


def solve(demonstrations, grid):
    g = [list(map(int, r)) for r in grid]
    H = len(g)
    W = len(g[0])
    out = [r[:] for r in g]
    for col, cells in _components(g, H, W):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        h = y1 - y0 + 1
        w = x1 - x0 + 1
        k = 1
        while True:
            # main-axis shift: one rectangle extent per step along the cascade direction
            my = DY * k * h
            mx = DX * k * w
            ny0 = y0 + my
            nx0 = x0 + mx
            # stop once the copies leave the grid along the cascade direction
            if DY != 0:
                if ny0 + h - 1 < 0 or ny0 >= H:
                    break
            else:
                if nx0 + w - 1 < 0 or nx0 >= W:
                    break
            for s in (-1, 1):
                if DY != 0:
                    ty, tx = ny0, nx0 + s * k * w
                else:
                    ty, tx = ny0 + s * k * h, nx0
                _stamp(out, H, W, ty, tx, h, w, col)
            k += 1
    return out
''' % (dr, dc, bg, fg)
    return src
