def build_program(d4, palette):
    bg = int(palette[7])
    shape = int(palette[6])
    src = '''import numpy as np
from collections import deque

BG = __BG__
SHAPE = __SHAPE__

def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    steps = ((1, 0), (-1, 0), (0, 1), (0, -1))
    comp = [[-1] * W for _ in range(H)]
    comps = []
    for y in range(H):
        for x in range(W):
            if g[y][x] == SHAPE and comp[y][x] < 0:
                cid = len(comps)
                cells = []
                q = deque([(y, x)])
                comp[y][x] = cid
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in steps:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and g[ny][nx] == SHAPE and comp[ny][nx] < 0:
                            comp[ny][nx] = cid
                            q.append((ny, nx))
                comps.append(cells)
    markers = [(y, x) for y in range(H) for x in range(W)
               if g[y][x] != BG and g[y][x] != SHAPE]
    assigned = {}
    for y, x in markers:
        col = g[y][x]
        for dy, dx in steps:
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and comp[ny][nx] >= 0:
                cid = comp[ny][nx]
                if cid in assigned and assigned[cid] != col:
                    raise ValueError("Component touched by conflicting marker colours")
                assigned[cid] = col
    for cid, col in assigned.items():
        for cy, cx in comps[cid]:
            out[cy][cx] = col
    for y, x in markers:
        out[y][x] = BG
    return out
'''
    return src.replace('__BG__', str(bg)).replace('__SHAPE__', str(shape))
