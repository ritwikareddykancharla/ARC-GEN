def build_program(d4, palette):
    BG = int(palette[0])
    NEW = int(palette[1])
    LINE = int(palette[2])
    FRAME = int(palette[3])
    src = '''import numpy as np
from collections import deque

BG = __BG__
NEW = __NEW__
LINE = __LINE__
FRAME = __FRAME__
# Visible-coordinate rule (D4 index __D4__): line orientation is detected per grid,
# so the same code handles row-lines and column-lines directly.

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

def _frame_on_row_line(g, cy, cx):
    H, W = g.shape
    row_out = [g[cy, x] for x in range(W) if abs(x - cx) > 1]
    col_out = [g[y, cx] for y in range(H) if abs(y - cy) > 1]
    on_row = len(row_out) > 0 and all(v == LINE for v in row_out)
    on_col = len(col_out) > 0 and all(v == LINE for v in col_out)
    if on_row and not on_col:
        return True
    if on_col and not on_row:
        return False
    # fallback: look two cells away along each axis
    col_hit = any(0 <= yy < H and g[yy, cx] == LINE for yy in (cy - 2, cy + 2))
    row_hit = any(0 <= xx < W and g[cy, xx] == LINE for xx in (cx - 2, cx + 2))
    if row_hit and not col_hit:
        return True
    return False

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    centres = []
    for cells in _components(g == FRAME):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        centres.append(((min(ys) + max(ys)) // 2, (min(xs) + max(xs)) // 2))
    for cy, cx in centres:
        if _frame_on_row_line(g, cy, cx):
            path = [(y, cx) for y in range(H)]
        else:
            path = [(cy, x) for x in range(W)]
        for y, x in path:
            if g[y, x] == BG:
                out[y, x] = NEW
        for y, x in path:
            if g[y, x] == LINE and (y, x) != (cy, cx):
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dy == 0 and dx == 0:
                            continue
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < H and 0 <= xx < W and g[yy, xx] != FRAME:
                            out[yy, xx] = NEW
    return out.tolist()
'''
    src = src.replace('__BG__', repr(BG)).replace('__NEW__', repr(NEW))
    src = src.replace('__LINE__', repr(LINE)).replace('__FRAME__', repr(FRAME))
    src = src.replace('__D4__', repr(int(d4)))
    return src
