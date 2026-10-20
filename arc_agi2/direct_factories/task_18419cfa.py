TEMPLATE = '''import numpy as np
from collections import deque

BG = __BG__
FRAME = __FR__


def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), bool)
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


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    for comp in _components(g == FRAME):
        ys = [c[0] for c in comp]
        xs = [c[1] for c in comp]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        h, w = y1 - y0 + 1, x1 - x0 + 1
        own = np.zeros((h, w), bool)
        for y, x in comp:
            own[y - y0, x - x0] = True
        # cells of the bounding box reachable from its border without crossing
        # this frame are outside; the remaining non-frame cells are the interior
        seen = np.zeros((h, w), bool)
        q = deque()
        for ry in range(h):
            for rx in range(w):
                if (ry in (0, h - 1) or rx in (0, w - 1)) and not own[ry, rx]:
                    seen[ry, rx] = True
                    q.append((ry, rx))
        while q:
            cy, cx = q.popleft()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < h and 0 <= nx < w and not own[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
        inner = [(ry + y0, rx + x0) for ry in range(h) for rx in range(w)
                 if not own[ry, rx] and not seen[ry, rx]]
        if not inner:
            continue
        iy0 = min(c[0] for c in inner)
        iy1 = max(c[0] for c in inner)
        ix0 = min(c[1] for c in inner)
        ix1 = max(c[1] for c in inner)
        rw = {}
        ch = {}
        for y, x in inner:
            rw[y] = rw.get(y, 0) + 1
            ch[x] = ch.get(x, 0) + 1
        mr = max(rw.values())
        mc = max(ch.values())
        n_rows_max = sum(1 for v in rw.values() if v == mr)
        n_cols_max = sum(1 for v in ch.values() if v == mc)
        # the bump axis is the one with fewer maximal lines; the gaps in the
        # walls widen only the bump rows (side bumps) or bump columns
        horiz = n_rows_max < n_cols_max
        for y, x in inner:
            v = int(g[y, x])
            if v == BG or v == FRAME:
                continue
            if horiz:
                out[y, ix0 + ix1 - x] = v
            else:
                out[iy0 + iy1 - y, x] = v
    return out.tolist()
'''


def build_program(d4, palette):
    bg = int(palette[0])
    fr = int(palette[8])
    return TEMPLATE.replace('__BG__', str(bg)).replace('__FR__', str(fr))
