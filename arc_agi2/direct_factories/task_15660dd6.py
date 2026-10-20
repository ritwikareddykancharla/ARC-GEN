TEMPLATE = """import numpy as np
from collections import deque

BG = @BG@
FR = @FR@
HORIZ = @HORIZ@
EDGE = @EDGE@


def _frames(g):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    boxes = []
    for y in range(h):
        for x in range(w):
            if g[y, x] == FR and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                y0 = y1 = y
                x0 = x1 = x
                while q:
                    cy, cx = q.popleft()
                    if cy < y0: y0 = cy
                    if cy > y1: y1 = cy
                    if cx < x0: x0 = cx
                    if cx > x1: x1 = cx
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == FR:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                if y1 - y0 >= 2 and x1 - x0 >= 2:
                    boxes.append((y0, x0, y1, x1))
    return boxes


def _marker(g, b):
    H, W = g.shape
    if EDGE == 'L':
        return int(g[b[0], 0])
    if EDGE == 'R':
        return int(g[b[0], W - 1])
    if EDGE == 'T':
        return int(g[0, b[1]])
    return int(g[H - 1, b[1]])


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    boxes = _frames(g)
    if not boxes:
        return [list(r) for r in grid]
    groups = {}
    for b in boxes:
        key = b[1] if HORIZ else b[0]
        groups.setdefault(key, []).append(b)
    keys = sorted(groups)
    bh = boxes[0][2] - boxes[0][0] + 1
    bw = boxes[0][3] - boxes[0][1] + 1
    n = len(keys)
    if HORIZ:
        out = np.full((bh, n * (bw + 1) - 1), BG, dtype=int)
    else:
        out = np.full((n * (bh + 1) - 1, bw), BG, dtype=int)
    for i, key in enumerate(keys):
        solid = None
        marker = None
        pat = None
        for b in sorted(groups[key]):
            inner = g[b[0] + 1:b[2], b[1] + 1:b[3]]
            vals = np.unique(inner)
            if len(vals) == 1 and int(vals[0]) != BG:
                solid = int(vals[0])
                marker = _marker(g, b)
            elif pat is None:
                pat = inner != BG
        if HORIZ:
            oy, ox = 0, i * (bw + 1)
        else:
            oy, ox = i * (bh + 1), 0
        if marker is None:
            marker = BG
        if solid is None:
            solid = BG
        if pat is None or pat.shape != (bh - 2, bw - 2):
            pat = np.zeros((bh - 2, bw - 2), dtype=bool)
        out[oy:oy + bh, ox:ox + bw] = marker
        out[oy + 1:oy + bh - 1, ox + 1:ox + bw - 1] = np.where(pat, solid, BG)
    return out.tolist()
"""


def build_program(d4, palette):
    k = d4 % 4
    edge = 'L'
    if d4 >= 4:
        edge = 'R'
    rot = {'L': 'T', 'T': 'R', 'R': 'B', 'B': 'L'}
    for _ in range(k):
        edge = rot[edge]
    horiz = (k % 2 == 0)
    bg = int(palette[8])
    fr = int(palette[1])
    src = TEMPLATE.replace('@BG@', str(bg))
    src = src.replace('@FR@', str(fr))
    src = src.replace('@HORIZ@', repr(horiz))
    src = src.replace('@EDGE@', repr(edge))
    return src
