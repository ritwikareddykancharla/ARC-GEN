TEMPLATE = '''import numpy as np
from collections import deque

BG = __BG__
A = __A__
C = 1 - A
SIGN = __S__
CS = __CS__
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(g):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for r in range(h):
        for c in range(w):
            if int(g[r, c]) == BG or seen[r, c]:
                continue
            colour = int(g[r, c])
            seen[r, c] = True
            queue = deque([(r, c)])
            cells = []
            while queue:
                y, x = queue.popleft()
                cells.append((y, x))
                for dy, dx in STEPS:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and int(g[ny, nx]) == colour:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
            comps.append((colour, cells))
    return comps


def _end(cells, along_value):
    s = set(cells)
    cand = [p for p in cells if p[A] == along_value]
    def deg(p):
        return sum(((p[0] + dy, p[1] + dx) in s) for dy, dx in STEPS)
    return min(cand, key=lambda p: (deg(p), CS * p[C]))


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    comps = _components(g)
    if not comps:
        return g.tolist()
    pieces = []
    for colour, cells in comps:
        lo = min(p[A] for p in cells)
        hi = max(p[A] for p in cells)
        pieces.append((colour, cells, lo, hi))
    if SIGN > 0:
        pieces.sort(key=lambda t: t[2])
    else:
        pieces.sort(key=lambda t: -t[3])
    total = sum(t[3] - t[2] + 1 for t in pieces)
    if A == 1:
        out = np.full((h, total), BG, dtype=int)
    else:
        out = np.full((total, w), BG, dtype=int)
    oh, ow = out.shape
    cur = 0
    prev = None
    for colour, cells, lo, hi in pieces:
        near, far = (lo, hi) if SIGN > 0 else (hi, lo)
        left = _end(cells, near)
        right = _end(cells, far)
        target = cur if SIGN > 0 else total - 1 - cur
        da = target - near
        dc = 0 if prev is None else prev - left[C]
        for p in cells:
            q = [0, 0]
            q[A] = p[A] + da
            q[C] = p[C] + dc
            if 0 <= q[0] < oh and 0 <= q[1] < ow:
                out[q[0], q[1]] = colour
        prev = right[C] + dc
        cur += hi - lo + 1
    return out.tolist()
'''


def build_program(d4, palette):
    d4 = int(d4) % 8
    along = (0, 1)
    cross = (1, 0)
    if d4 >= 4:
        along = (along[0], -along[1])
        cross = (cross[0], -cross[1])
    for _ in range(d4 % 4):
        along = (along[1], -along[0])
        cross = (cross[1], -cross[0])
    a = 0 if along[0] != 0 else 1
    s = along[a]
    cs = cross[1 - a]
    bg = int(palette[0])
    src = TEMPLATE
    src = src.replace('__BG__', str(bg))
    src = src.replace('__A__', str(a))
    src = src.replace('__S__', str(s))
    src = src.replace('__CS__', str(cs))
    return src
