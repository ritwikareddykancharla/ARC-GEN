def build_program(d4, palette):
    # The box-detection rule is invariant under the whole D4 group. It checks for a
    # filled rectangle, a complete 8-neighbour ring and four corner extensions
    # (one along each edge direction). A rotation or reflection of the scene maps
    # boxes onto boxes and crossings onto crossings. So the emitted program runs the
    # same mechanism in visible coordinates for every d4. Only the colour roles are
    # specialised through the palette.
    bg = int(palette[0])
    wire = int(palette[5])
    fill = int(palette[4])
    src = '''
import numpy as np
from collections import deque

BG = %d
WIRE = %d
FILL = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
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

def _is_box_interior(g, cells):
    H, W = g.shape
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
    # 1. the black region must be a perfect filled rectangle
    if len(cells) != (y1 - y0 + 1) * (x1 - x0 + 1):
        return False
    # 2. every in-grid cell of the 1-cell ring (corners included) must be wire;
    #    off-grid ring cells are allowed (frames cut by the border)
    for y in range(y0 - 1, y1 + 2):
        for x in range(x0 - 1, x1 + 2):
            if y0 <= y <= y1 and x0 <= x <= x1:
                continue
            if 0 <= y < H and 0 <= x < W and g[y, x] != WIRE:
                return False
    # 3. each ring corner must be a true corner: one step beyond it along either
    #    frame edge must not be wire (rejects gaps between crossing wires)
    for cy, dy in ((y0 - 1, -1), (y1 + 1, 1)):
        for cx, dx in ((x0 - 1, -1), (x1 + 1, 1)):
            for py, px in ((cy + dy, cx), (cy, cx + dx)):
                if 0 <= py < H and 0 <= px < W and g[py, px] == WIRE:
                    return False
    return True

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    for cells in _components(g == BG):
        if _is_box_interior(g, cells):
            for y, x in cells:
                out[y, x] = FILL
    return out.tolist()
''' % (bg, wire, fill)
    return src
