TEMPLATE = """import numpy as np
from collections import deque

BOARD = __BOARD__
STRIP = __STRIP__
BLOCK = __BLOCK__
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in STEPS:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    board = (g == BOARD) | (g == STRIP) | (g == BLOCK)
    if not board.any():
        return out.tolist()
    ys, xs = np.nonzero(board)
    by0, by1 = int(ys.min()), int(ys.max())
    bx0, bx1 = int(xs.min()), int(xs.max())
    strips = _components(g == STRIP)
    blocks = _components(g == BLOCK)
    out[g == STRIP] = BOARD
    for blk in blocks:
        bs = set(blk)
        n = 0
        for s in strips:
            if any((y + dy, x + dx) in bs for (y, x) in s for (dy, dx) in STEPS):
                n += len(s)
        if n == 0:
            continue
        cy = [c[0] for c in blk]
        cx = [c[1] for c in blk]
        y0, y1, x0, x1 = min(cy), max(cy), min(cx), max(cx)
        cand = []
        if y0 == by0:
            cand.append((sum(1 for c in blk if c[0] == by0), 'top'))
        if y1 == by1:
            cand.append((sum(1 for c in blk if c[0] == by1), 'bottom'))
        if x0 == bx0:
            cand.append((sum(1 for c in blk if c[1] == bx0), 'left'))
        if x1 == bx1:
            cand.append((sum(1 for c in blk if c[1] == bx1), 'right'))
        if cand:
            side = max(cand, key=lambda t: t[0])[1]
        else:
            dists = [(y0 - by0, 'top'), (by1 - y1, 'bottom'), (x0 - bx0, 'left'), (bx1 - x1, 'right')]
            side = min(dists, key=lambda t: t[0])[1]
        if side == 'top':
            layers = [[(y, x) for x in range(x0, x1 + 1)] for y in range(y0, y1 + 1)]
        elif side == 'bottom':
            layers = [[(y, x) for x in range(x0, x1 + 1)] for y in range(y1, y0 - 1, -1)]
        elif side == 'left':
            layers = [[(y, x) for y in range(y0, y1 + 1)] for x in range(x0, x1 + 1)]
        else:
            layers = [[(y, x) for y in range(y0, y1 + 1)] for x in range(x1, x0 - 1, -1)]
        left = n
        for layer in layers:
            if left <= 0:
                break
            for (y, x) in layer:
                out[y, x] = STRIP
            left -= len(layer)
    return out.tolist()
"""


def build_program(d4, palette):
    p = [int(v) for v in palette]
    prog = TEMPLATE.replace('__BOARD__', str(p[4]))
    prog = prog.replace('__STRIP__', str(p[5]))
    prog = prog.replace('__BLOCK__', str(p[7]))
    return prog
