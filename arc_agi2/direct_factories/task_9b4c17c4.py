def build_program(d4, palette):
    nl = chr(10)
    dirs = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    base = 1 if d4 >= 4 else 3
    ia = (base + d4 % 4) % 4
    ib = (ia + 2) % 4
    red = int(palette[2])
    col_a = int(palette[8])
    col_b = int(palette[1])
    head_lines = [
        'RED = %d' % red,
        'COL_A = %d' % col_a,
        'COL_B = %d' % col_b,
        'DIR_A = (%d, %d)' % dirs[ia],
        'DIR_B = (%d, %d)' % dirs[ib],
        '',
    ]
    body = '''
import numpy as np
from collections import deque


def _rect_of(g, colour):
    ys, xs = np.where(g == colour)
    if len(ys) == 0:
        return None
    return int(ys.min()), int(xs.min()), int(ys.max()), int(xs.max())


def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
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
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out


def _shift_to_edge(cells, rect, direction):
    y0, x0, y1, x1 = rect
    dy, dx = direction
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    sy = 0
    sx = 0
    if dy < 0:
        sy = y0 - min(ys)
    elif dy > 0:
        sy = y1 - max(ys)
    if dx < 0:
        sx = x0 - min(xs)
    elif dx > 0:
        sx = x1 - max(xs)
    return sy, sx


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    moves = []
    for colour, direction in ((COL_A, DIR_A), (COL_B, DIR_B)):
        rect = _rect_of(g, colour)
        if rect is None:
            continue
        y0, x0, y1, x1 = rect
        mask = np.zeros((h, w), dtype=bool)
        mask[y0:y1 + 1, x0:x1 + 1] = g[y0:y1 + 1, x0:x1 + 1] == RED
        for cells in _components(mask):
            sy, sx = _shift_to_edge(cells, rect, direction)
            moves.append((colour, cells, sy, sx))
    for colour, cells, sy, sx in moves:
        for y, x in cells:
            out[y, x] = colour
    for colour, cells, sy, sx in moves:
        for y, x in cells:
            ny, nx = y + sy, x + sx
            if 0 <= ny < h and 0 <= nx < w:
                out[ny, nx] = RED
    return out.tolist()
'''
    return nl.join(head_lines) + body
