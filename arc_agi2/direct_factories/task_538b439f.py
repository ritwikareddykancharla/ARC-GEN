def build_program(d4, palette):
    # The family's own generator already randomises transpose/flip and draws
    # all four colours at random for every pair. So the divider axis, the
    # side the boxes sit on, and every colour role must be read from the
    # visible pixels of each grid. d4 is only used as a harmless tie-break:
    # it sets which axis to try first if both a full row and a full column
    # were ever uniform.
    prefer = 'col' if (d4 % 2) == 0 else 'row'
    src = r'''
import numpy as np
from collections import Counter, deque

PREFER = '__PREFER__'


def _components(mask):
    mask = np.asarray(mask, bool)
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


def _bbox(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    return min(ys), min(xs), max(ys), max(xs)


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    bg = Counter(g.ravel().tolist()).most_common(1)[0][0]

    # Find full-length uniform lines that are not background.
    rows = [y for y in range(H) if g[y, 0] != bg and (g[y] == g[y, 0]).all()]
    cols = [x for x in range(W) if g[0, x] != bg and (g[:, x] == g[0, x]).all()]
    if not rows and not cols:
        return out.tolist()
    if cols and (PREFER == 'col' or not rows):
        axis, d = 'col', cols[0]
        dc = int(g[0, d])
    else:
        axis, d = 'row', rows[0]
        dc = int(g[d, 0])

    # Choose the box colour among the remaining colours.
    # A box colour must be made only of solid rectangles at least 2x2,
    # all strictly on one side of the divider and not touching it.
    # Ties are broken by the largest component.
    cands = [int(c) for c in np.unique(g) if c != bg and c != dc]
    if not cands:
        return out.tolist()
    best_key, bc, best_comps = None, None, None
    for c in cands:
        comps = _components(g == c)
        ok = True
        sides = set()
        biggest = 0
        for comp in comps:
            y0, x0, y1, x1 = _bbox(comp)
            biggest = max(biggest, len(comp))
            if len(comp) != (y1 - y0 + 1) * (x1 - x0 + 1):
                ok = False
            if y1 - y0 < 1 or x1 - x0 < 1:
                ok = False
            lo, hi = (x0, x1) if axis == 'col' else (y0, y1)
            if hi <= d - 2:
                sides.add(-1)
            elif lo >= d + 2:
                sides.add(1)
            else:
                ok = False
        if len(sides) > 1:
            ok = False
        key = (1 if ok else 0, biggest)
        if best_key is None or key > best_key:
            best_key, bc, best_comps = key, c, comps

    for comp in best_comps:
        y0, x0, y1, x1 = _bbox(comp)
        if axis == 'col':
            m0, m1 = 2 * d - x1, 2 * d - x0
            lo, hi = max(min(x0, m0), 0), min(max(x1, m1), W - 1)
            if lo <= hi:
                out[y0:y1 + 1, lo:hi + 1] = dc
            out[y0:y1 + 1, x0:x1 + 1] = bc
            a, b = max(m0, 0), min(m1, W - 1)
            if a <= b:
                out[y0:y1 + 1, a:b + 1] = bc
        else:
            m0, m1 = 2 * d - y1, 2 * d - y0
            lo, hi = max(min(y0, m0), 0), min(max(y1, m1), H - 1)
            if lo <= hi:
                out[lo:hi + 1, x0:x1 + 1] = dc
            out[y0:y1 + 1, x0:x1 + 1] = bc
            a, b = max(m0, 0), min(m1, H - 1)
            if a <= b:
                out[a:b + 1, x0:x1 + 1] = bc
    return out.tolist()
'''
    return src.replace('__PREFER__', prefer)
