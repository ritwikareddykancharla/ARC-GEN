def build_program(d4, palette):
    d4 = int(d4) % 8

    def tvec(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return (dr, dc)

    down = tvec((1, 0))
    right = tvec((0, 1))
    bg = int(palette[0])
    header = 'BG = %d\nDOWN = (%d, %d)\nRIGHT = (%d, %d)\n' % (bg, down[0], down[1], right[0], right[1])
    body = '''
import numpy as np
from collections import deque

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    objs = []
    for colour in sorted(set(g.ravel().tolist()) - {BG}):
        for cells in _components(g == colour):
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
            patch = np.full((y1 - y0 + 1, x1 - x0 + 1), BG, dtype=int)
            for (y, x) in cells:
                patch[y - y0, x - x0] = colour
            cy, cx = y0 + y1, x0 + x1
            key = (DOWN[0] * cy + DOWN[1] * cx, RIGHT[0] * cy + RIGHT[1] * cx)
            hollow = len(cells) < patch.size
            objs.append((key, hollow, patch))
    hollows = sorted([o for o in objs if o[1]], key=lambda o: o[0])
    solids = sorted([o for o in objs if not o[1]], key=lambda o: o[0])
    sh, sw = 4, 4
    if objs:
        sh, sw = objs[0][2].shape
    n = max(len(hollows), len(solids), 1)
    vertical = DOWN[0] != 0
    stack_pos = (DOWN[0] > 0) if vertical else (DOWN[1] > 0)
    cross_pos = (RIGHT[1] > 0) if vertical else (RIGHT[0] > 0)
    hollow_side = 0 if cross_pos else 1
    if vertical:
        out = np.full((sh * n, 2 * sw), BG, dtype=int)
    else:
        out = np.full((2 * sh, sw * n), BG, dtype=int)
    for group, is_h in ((hollows, True), (solids, False)):
        side = hollow_side if is_h else 1 - hollow_side
        for i, o in enumerate(group):
            p = i if stack_pos else n - 1 - i
            patch = o[2]
            ph, pw = patch.shape
            if vertical:
                out[p * sh:p * sh + ph, side * sw:side * sw + pw] = patch
            else:
                out[side * sh:side * sh + ph, p * sw:p * sw + pw] = patch
    return out.tolist()
'''
    return header + body
