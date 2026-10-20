def build_program(d4, palette):
    zero = int(palette[0])
    edges = ['top', 'right', 'bottom', 'left']
    # Canonical legend sits next to the LEFT edge of the panel (column 1) and
    # dots extend away from that edge. A row reversal sends left->right;
    # each clockwise quarter turn advances the edge one step clockwise.
    idx = 3
    if d4 >= 4:
        idx = 1
    idx = (idx + (d4 % 4)) % 4
    edge = edges[idx]
    template = '''import numpy as np
from collections import Counter

ZERO = __ZERO__
EDGE = '__EDGE__'


def _count_components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    n = 0
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                n += 1
                seen[y, x] = True
                stack = [(y, x)]
                while stack:
                    cy, cx = stack.pop()
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                stack.append((ny, nx))
    return n


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])
    ys, xs = np.where(g == ZERO)
    if len(ys) == 0:
        return g.tolist()
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    panel = g[y0:y1 + 1, x0:x1 + 1].copy()
    outside = g.copy()
    outside[y0:y1 + 1, x0:x1 + 1] = bg
    H, W = panel.shape
    # Legend line lies one cell in from the panel edge EDGE; dots step by 2
    # away from that edge along the perpendicular direction.
    if EDGE == 'left':
        cells = [(i, 1) for i in range(H)] if W > 1 else []
        step = (0, 2)
    elif EDGE == 'right':
        cells = [(i, W - 2) for i in range(H)] if W > 1 else []
        step = (0, -2)
    elif EDGE == 'top':
        cells = [(1, i) for i in range(W)] if H > 1 else []
        step = (2, 0)
    else:
        cells = [(H - 2, i) for i in range(W)] if H > 1 else []
        step = (-2, 0)
    counts = {}
    for (r, c) in cells:
        col = int(panel[r, c])
        if col == ZERO:
            continue
        if col not in counts:
            counts[col] = _count_components(outside == col)
        n = counts[col]
        for k in range(n):
            rr = r + step[0] * k
            cc = c + step[1] * k
            if 0 <= rr < H and 0 <= cc < W:
                panel[rr, cc] = col
    return panel.tolist()
'''
    return template.replace('__ZERO__', str(zero)).replace('__EDGE__', edge)
