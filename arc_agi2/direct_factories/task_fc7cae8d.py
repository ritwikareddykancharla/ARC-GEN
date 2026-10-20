_TEMPLATE = '''
import numpy as np
from collections import Counter, deque

BG = @BG@
DOT = @DOT@


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


def _border_info(g):
    H, W = g.shape
    lines = [g[0, :], g[:, W - 1], g[H - 1, :], g[:, 0]]
    info = []
    for ln in lines:
        vals = [int(v) for v in ln if int(v) != BG]
        if vals:
            c, n = Counter(vals).most_common(1)[0]
            info.append((int(c), n / float(len(ln))))
        else:
            info.append((None, 0.0))
    return info


def _edge_lines(g):
    # sides: 0 top, 1 right, 2 bottom, 3 left (visible coordinates)
    info = _border_info(g)
    best = None
    for s in range(4):
        t = (s + 1) % 4
        cs, fs = info[s]
        ct, ft = info[t]
        if cs is None or ct is None or cs == ct:
            continue
        score = (int(cs != DOT) + int(ct != DOT), fs + ft)
        if best is None or score > best[0]:
            best = (score, {cs: s, ct: t})
    return best[1] if best else {}


def _side_map(f, k, s):
    # side after left-right mirror (if f) then k counter-clockwise quarter turns
    if f and s in (1, 3):
        s = 4 - s
    return (s - k) % 4


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    edges = _edge_lines(g)
    nonbg = g != BG
    inner = np.zeros_like(nonbg)
    for cells in _components(nonbg):
        if not any(y in (0, H - 1) or x in (0, W - 1) for y, x in cells):
            for y, x in cells:
                inner[y, x] = True
    if not inner.any():
        return g.tolist()
    rect = inner.copy()
    for c in edges:
        rect &= (g != c)
    if not rect.any():
        return g.tolist()
    ys, xs = np.nonzero(rect)
    ry0, ry1, rx0, rx1 = ys.min(), ys.max(), xs.min(), xs.max()
    crop = g[ry0:ry1 + 1, rx0:rx1 + 1].copy()
    cons = []
    for c, es in edges.items():
        my, mx = np.nonzero(inner & (g == c))
        if len(my) == 0:
            continue
        if my.max() < ry0:
            side = 0
        elif my.min() > ry1:
            side = 2
        elif mx.max() < rx0:
            side = 3
        elif mx.min() > rx1:
            side = 1
        else:
            continue
        cons.append((side, es))
    best = None
    for f in (False, True):
        for k in range(4):
            sc = sum(1 for m, e in cons if _side_map(f, k, m) == e)
            if best is None or sc > best[0]:
                best = (sc, f, k)
    _, f, k = best
    a = crop[:, ::-1] if f else crop
    out = np.rot90(a, k)
    return [[int(v) for v in row] for row in out]
'''


def build_program(d4, palette):
    bg = int(palette[0])
    dot = int(palette[5])
    return _TEMPLATE.replace('@BG@', str(bg)).replace('@DOT@', str(dot))
