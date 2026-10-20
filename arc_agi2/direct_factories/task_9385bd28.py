def build_program(d4, palette):
    d4 = int(d4) % 8

    def tf(vec):
        dr, dc = vec
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return (dr, dc)

    order = tf((1, 0))
    kv = tf((0, 1))
    erase = int(palette[0])
    header = (
        'ORDER = (%d, %d)\n' % order +
        'KV = (%d, %d)\n' % kv +
        'ERASE = %d\n' % erase
    )
    body = '''
import numpy as np
from collections import Counter, deque


def _background(g):
    return int(Counter(g.ravel().tolist()).most_common(1)[0][0])


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


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    bg = _background(g)
    out = g.copy()
    # Find the legend: a multi-colour 4-connected block that is exactly two
    # cells thick along the key->value axis (columns if KV is horizontal,
    # rows if KV is vertical).
    legend = None
    best = 1
    for cells in _components(g != bg):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        if KV[0] == 0:
            thick = (x1 - x0 == 1)
        else:
            thick = (y1 - y0 == 1)
        cols = set(int(g[y, x]) for y, x in cells)
        if thick and len(cols) > best:
            best = len(cols)
            legend = (y0, x0, y1, x1)
    if legend is None:
        return out.tolist()
    ly0, lx0, ly1, lx1 = legend
    inleg = np.zeros_like(g, dtype=bool)
    inleg[ly0:ly1 + 1, lx0:lx1 + 1] = True
    entries = []
    if KV[0] == 0:
        kc, vc = (lx0, lx1) if KV[1] > 0 else (lx1, lx0)
        ys = list(range(ly0, ly1 + 1))
        if ORDER[0] < 0:
            ys.reverse()
        for y in ys:
            k, v = int(g[y, kc]), int(g[y, vc])
            if k != bg:
                entries.append((k, v))
    else:
        kr, vr = (ly0, ly1) if KV[0] > 0 else (ly1, ly0)
        xs = list(range(lx0, lx1 + 1))
        if ORDER[1] < 0:
            xs.reverse()
        for x in xs:
            k, v = int(g[kr, x]), int(g[vr, x])
            if k != bg:
                entries.append((k, v))
    # Erase rows (value = image of colour 0, background is something else)
    # remove their key pieces before any rectangle is claimed.
    for k, v in entries:
        if v == ERASE and bg != ERASE:
            m = (out == k) & ~inleg
            if m.any():
                out[m] = bg
    painted = np.zeros_like(g, dtype=bool)
    for k, v in entries:
        if v == ERASE and bg != ERASE:
            continue
        m = (g == k) & ~inleg
        if not m.any():
            continue
        ys, xs = np.nonzero(m)
        region = np.zeros_like(m)
        region[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = True
        free = region & (out == bg) & ~painted & ~inleg
        if v == bg:
            painted |= free
            continue
        if free.any():
            out[free] = v
            painted |= free
        else:
            out[m] = v
            painted |= m
    return out.tolist()
'''
    return header + body
