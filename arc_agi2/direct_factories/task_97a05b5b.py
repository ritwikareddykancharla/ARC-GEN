BODY = '''
import numpy as np
from collections import deque


def _components(a):
    h, w = a.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if a[y, x] != BG and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and a[ny, nx] != BG and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                comps.append(sorted(cells))
    return comps


def _box(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    return min(ys), min(xs), max(ys), max(xs)


def _candidates(out, piece):
    H, W = out.shape
    res = []
    seen = set()
    for r in range(4):
        v = np.rot90(piece, r).copy()
        h, w = v.shape
        if h > H or w > W:
            continue
        m2 = v == RED
        if not m2.any():
            continue
        rel = [(int(i), int(j)) for i, j in np.argwhere(m2)]
        paint = [(int(i), int(j)) for i, j in np.argwhere(v != BG)]
        for oy in range(H - h + 1):
            for ox in range(W - w + 1):
                if np.array_equal(out[oy:oy + h, ox:ox + w] == BG, m2):
                    k = (oy, ox, h, w, v.tobytes())
                    if k in seen:
                        continue
                    seen.add(k)
                    holes = frozenset((oy + i, ox + j) for i, j in rel)
                    foot = frozenset((oy + i, ox + j) for i, j in paint)
                    res.append((v, oy, ox, holes, foot))
    return res


def _search(cands, total, strict):
    best = [-1, []]
    n = len(cands)

    def rec(i, used_h, used_f, chosen, covered):
        if i == n:
            if covered > best[0]:
                best[0] = covered
                best[1] = list(chosen)
            return covered == total
        for c in cands[i]:
            if c[3] & used_h:
                continue
            if strict and (c[4] & used_f):
                continue
            chosen.append(c)
            if rec(i + 1, used_h | c[3], used_f | c[4], chosen, covered + len(c[3])):
                return True
            chosen.pop()
        return rec(i + 1, used_h, used_f, chosen, covered)

    rec(0, frozenset(), frozenset(), [], 0)
    return best[0], best[1]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    comps = _components(g)
    if not comps:
        return g.tolist()
    board = max(comps, key=len)
    y0, x0, y1, x1 = _box(board)
    out = g[y0:y1 + 1, x0:x1 + 1].copy()
    cand_lists = []
    for cells in comps:
        if cells is board:
            continue
        a, b, c, d = _box(cells)
        if a >= y0 and b >= x0 and c <= y1 and d <= x1:
            continue
        piece = np.full((c - a + 1, d - b + 1), BG, dtype=int)
        for y, x in cells:
            piece[y - a, x - b] = g[y, x]
        cand_lists.append(_candidates(out, piece))
    total = int((out == BG).sum())
    sc, chosen = _search(cand_lists, total, True)
    if sc < total:
        sc2, ch2 = _search(cand_lists, total, False)
        if sc2 > sc:
            chosen = ch2
    for v, oy, ox, holes, foot in chosen:
        for (y, x) in foot:
            out[y, x] = v[y - oy, x - ox]
    out[out == BG] = RED
    return out.tolist()
'''


def build_program(d4, palette):
    bg = int(palette[0])
    red = int(palette[2])
    header = 'BG = %d\nRED = %d\n' % (bg, red)
    return header + BODY
