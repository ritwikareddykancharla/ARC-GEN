def build_program(d4, palette):
    m = [[1, 1, 0, 0], [1, 1, 1, 0], [1, 1, 0, 0]]
    if d4 >= 4:
        m = [row[::-1] for row in m]
    for _ in range(d4 % 4):
        h = len(m)
        w = len(m[0])
        m = [[m[h - 1 - j][i] for j in range(h)] for i in range(w)]
    frame = int(palette[5])
    template = '''import numpy as np
from collections import deque

LEGEND_MASK = np.array(__MASK__, dtype=bool)
FRAME = __FRAME__


def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps = []
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
                comps.append(cells)
    return comps


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    ys, xs = np.where(g == FRAME)
    if len(ys) == 0:
        return g.tolist()
    fy0, fy1 = int(ys.min()), int(ys.max())
    fx0, fx1 = int(xs.min()), int(xs.max())
    crop = g[fy0:fy1 + 1, fx0:fx1 + 1].copy()
    if crop.shape[0] > 2 and crop.shape[1] > 2:
        bg = int(crop[1, 1])
    else:
        vals, counts = np.unique(g, return_counts=True)
        bg = int(vals[int(np.argmax(counts))])
    mh, mw = LEGEND_MASK.shape
    a_idx = tuple(int(v) for v in np.argwhere(LEGEND_MASK)[0])
    b_idx = tuple(int(v) for v in np.argwhere(~LEGEND_MASK)[0])
    mapping = {}
    legend = np.zeros_like(g, dtype=bool)
    for y in range(H - mh + 1):
        for x in range(W - mw + 1):
            win = g[y:y + mh, x:x + mw]
            a = int(win[a_idx])
            b = int(win[b_idx])
            if a == b or a in (bg, FRAME) or b in (bg, FRAME):
                continue
            if np.array_equal(win, np.where(LEGEND_MASK, a, b)):
                mapping[a] = b
                legend[y:y + mh, x:x + mw] = True
    inframe = np.zeros_like(g, dtype=bool)
    inframe[fy0:fy1 + 1, fx0:fx1 + 1] = True
    templates = {}
    for c in mapping:
        tm = (g == c) & ~legend & ~inframe
        if tm.any():
            ty, tx = np.where(tm)
            templates[c] = tm[ty.min():ty.max() + 1, tx.min():tx.max() + 1]
    out = crop.copy()
    for c in sorted(mapping):
        if c not in templates:
            continue
        t = templates[c]
        for cells in _components(crop == c):
            cy = [p[0] for p in cells]
            cx = [p[1] for p in cells]
            y0, y1, x0, x1 = min(cy), max(cy), min(cx), max(cx)
            h, w = y1 - y0 + 1, x1 - x0 + 1
            if (h, w) != t.shape or len(cells) != h * w:
                continue
            out[y0:y1 + 1, x0:x1 + 1] = np.where(t, mapping[c], bg)
    return out.tolist()
'''
    return template.replace('__MASK__', repr(m)).replace('__FRAME__', str(frame))
