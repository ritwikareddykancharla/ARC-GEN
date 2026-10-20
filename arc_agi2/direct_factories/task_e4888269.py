def build_program(d4, palette):
    # Original legend geometry: each legend row is the pair (row, col) -> (row, col+1),
    # i.e. source->destination direction (dr,dc)=(0,+1); rows are read top to bottom,
    # reading direction (dr,dc)=(+1,0). Push both vectors through the D4 map.
    def tf(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return dr, dc
    pdr, pdc = tf((0, 1))
    rdr, rdc = tf((1, 0))
    src = '''import numpy as np
from collections import Counter, deque

PDR, PDC = __PDR__, __PDC__   # visible direction from source cell to destination cell
RDR, RDC = __RDR__, __RDC__   # visible direction in which legend rules are applied


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


def _legend_pairs(g, box):
    y0, x0, y1, x1 = box
    pairs = []
    if PDR != 0:
        # pairs run vertically (2 rows tall); rules advance horizontally
        cols = list(range(x0, x1 + 1))
        if RDC < 0:
            cols = cols[::-1]
        sy, dy = (y0, y1) if PDR > 0 else (y1, y0)
        for x in cols:
            pairs.append((int(g[sy, x]), int(g[dy, x])))
    else:
        rows = list(range(y0, y1 + 1))
        if RDR < 0:
            rows = rows[::-1]
        sx, dx = (x0, x1) if PDC > 0 else (x1, x0)
        for y in rows:
            pairs.append((int(g[y, sx]), int(g[y, dx])))
    return pairs


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])
    comps = _components(g != bg)
    cands = []
    for cells in comps:
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, x0, y1, x1 = min(ys), min(xs), max(ys), max(xs)
        bh, bw = y1 - y0 + 1, x1 - x0 + 1
        thick = bh if PDR != 0 else bw
        if thick != 2:
            continue
        if len(cells) != bh * bw:
            continue
        block = g[y0:y1 + 1, x0:x1 + 1]
        if len(set(block.ravel().tolist())) < 2:
            continue
        cands.append(((y0, x0), (y0, x0, y1, x1)))
    if not cands:
        return g.tolist()
    cands.sort()
    box = None
    for _, b in cands:
        if all(a != c for a, c in _legend_pairs(g, b)):
            box = b
            break
    if box is None:
        box = cands[0][1]
    pairs = _legend_pairs(g, box)
    y0, x0, y1, x1 = box
    mask = np.ones(g.shape, bool)
    mask[y0:y1 + 1, x0:x1 + 1] = False
    out = g.copy()
    for a, b in pairs:
        sel = mask & (out == a)
        if sel.any():
            out[sel] = b
    return out.tolist()
'''
    src = src.replace('__PDR__', repr(pdr)).replace('__PDC__', repr(pdc))
    src = src.replace('__RDR__', repr(rdr)).replace('__RDC__', repr(rdc))
    return src
