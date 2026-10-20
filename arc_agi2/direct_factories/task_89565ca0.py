_TEMPLATE = '''import numpy as np
from collections import deque
import functools

BG = __BG__
TRANSPOSE = __TRANSPOSE__
RANK_REV = __RANKREV__
BAR_REV = __BARREV__


def _components(mask, diagonal=False):
    mask = np.asarray(mask, bool)
    h, w = mask.shape
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diagonal:
        steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    seen = np.zeros_like(mask, bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                queue = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while queue:
                    cy, cx = queue.popleft()
                    cells.append((cy, cx))
                    for dy, dx in steps:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
                out.append(cells)
    return out


def _bridge_line(prev, cand, out):
    n = len(prev)
    j = 0
    while j < n:
        if cand[j] and not prev[j] and j > 0 and prev[j - 1]:
            k = j
            while k < n and cand[k] and not prev[k]:
                k += 1
            if k < n and prev[k]:
                size = k - j
                ext = (j >= 2 and prev[j - 2]) or (k + 1 < n and prev[k + 1])
                if size == 1 or (size <= 3 and ext):
                    out[j:k] = True
            j = max(k, j + 1)
        else:
            j += 1


def _count(g, c):
    H, W = g.shape
    wall = g == c
    cand = (g != BG) & (g != c)
    w2 = wall.copy()
    for _ in range(10):
        before = w2.copy()
        for y in range(H):
            if cand[y].any():
                _bridge_line(before[y], cand[y], w2[y])
        for x in range(W):
            if cand[:, x].any():
                _bridge_line(before[:, x], cand[:, x], w2[:, x])
        if np.array_equal(before, w2):
            break
    ys, xs = np.nonzero(wall)
    if len(ys) == 0:
        return 0
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    sub = ~w2[y0:y1 + 1, x0:x1 + 1]
    hh, ww = sub.shape
    cnt = 0
    for comp in _components(sub):
        if all(0 < p[0] < hh - 1 and 0 < p[1] < ww - 1 for p in comp):
            cnt += 1
    return cnt


def _votes(g, frames):
    H, W = g.shape
    fs = set(frames)

    def val(y, x):
        if 0 <= y < H and 0 <= x < W:
            return int(g[y, x])
        return -1

    votes = {}
    for y in range(H):
        for x in range(W):
            a = int(g[y, x])
            if a not in fs:
                continue
            l, r, u, d = val(y, x - 1), val(y, x + 1), val(y - 1, x), val(y + 1, x)
            if l == r and l in fs and l != a and u == a and d == a:
                votes[(a, l)] = votes.get((a, l), 0) + 1
            if u == d and u in fs and u != a and l == a and r == a:
                votes[(a, u)] = votes.get((a, u), 0) + 1
    return votes


def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    colours = [int(c) for c in np.unique(g) if int(c) != BG]
    if not colours:
        return [[BG]]
    pieces = {c: len(_components(g == c, diagonal=True)) for c in colours}
    noise = max(colours, key=lambda c: pieces[c])
    frames = [c for c in colours if c != noise]
    if not frames:
        return [[noise]]
    votes = _votes(g, frames)
    counts = {c: _count(g, c) for c in frames}

    def cmp(a, b):
        if counts[a] != counts[b]:
            return counts[a] - counts[b]
        va = votes.get((a, b), 0)
        vb = votes.get((b, a), 0)
        if va != vb:
            return 1 if va > vb else -1
        return a - b

    order = sorted(frames, key=functools.cmp_to_key(cmp))
    n = len(order)
    span = max(1, max(counts.values()))
    if TRANSPOSE:
        out = np.full((span, n), noise, dtype=int)
    else:
        out = np.full((n, span), noise, dtype=int)
    for i, c in enumerate(order):
        lane = n - 1 - i if RANK_REV else i
        k = counts[c]
        cells = range(span - k, span) if BAR_REV else range(k)
        for p in cells:
            if TRANSPOSE:
                out[p, lane] = c
            else:
                out[lane, p] = c
    return out.tolist()
'''

# d4 -> (bars are columns, rank 0 at far end of lane axis, bars grow from far end)
_TABLE = {
    0: (False, False, False),
    1: (True, True, False),
    2: (False, True, True),
    3: (True, False, True),
    4: (False, False, True),
    5: (True, True, True),
    6: (False, True, False),
    7: (True, False, False),
}


def build_program(d4, palette):
    d = int(d4) % 8
    t, rr, br = _TABLE[d]
    bg = int(palette[0])
    src = _TEMPLATE
    src = src.replace('__BG__', str(bg))
    src = src.replace('__TRANSPOSE__', str(t))
    src = src.replace('__RANKREV__', str(rr))
    src = src.replace('__BARREV__', str(br))
    return src
