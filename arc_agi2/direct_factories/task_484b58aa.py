TEMPLATE = '''import numpy as np
from collections import deque

D4 = __D4__
MASK = __MASK__


def _vec_to_canon(dy, dx):
    # map a visible displacement back to the constructor frame (only used for tie-break ordering)
    for _ in range(D4 % 4):
        dy, dx = -dx, dy
    if D4 >= 4:
        dx = -dx
    return dy, dx


def _pos_key(y, x, H, W):
    h, w = H, W
    for _ in range(D4 % 4):
        y, x = w - 1 - x, y
        h, w = w, h
    if D4 >= 4:
        x = w - 1 - x
    return (y, x)


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
                    for sy, sx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + sy, cx + sx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    known = g != MASK
    cands = []
    for dy in range(0, H):
        for dx in range(-W + 1, W):
            if dy == 0 and dx <= 0:
                continue
            y1 = H - dy
            x0, x1 = max(0, -dx), min(W, W - dx)
            if y1 <= 0 or x1 <= x0:
                continue
            a = g[0:y1, x0:x1]
            b = g[dy:dy + y1, x0 + dx:x1 + dx]
            m = known[0:y1, x0:x1] & known[dy:dy + y1, x0 + dx:x1 + dx]
            n = int(m.sum())
            if n >= 40 and np.array_equal(a[m], b[m]):
                cy, cx = _vec_to_canon(dy, dx)
                if cy < 0 or (cy == 0 and cx < 0):
                    cy, cx, sgn = -cy, -cx, -1
                else:
                    sgn = 1
                cands.append((cy * cy + cx * cx, cy, cx, dy * sgn, dx * sgn))
    cands.sort()
    offs = [(c[3], c[4]) for c in cands]

    def lookup(y, x):
        for oy, ox in offs:
            for s in (1, -1):
                k = 1
                while True:
                    yy, xx = y + s * k * oy, x + s * k * ox
                    if not (0 <= yy < H and 0 <= xx < W):
                        break
                    if g[yy, xx] != MASK:
                        return int(g[yy, xx])
                    k += 1
        return None

    comps = _components(g == MASK)
    comps = [sorted(c, key=lambda p: _pos_key(p[0], p[1], H, W)) for c in comps]
    comps.sort(key=lambda c: _pos_key(c[0][0], c[0][1], H, W))
    for comp in comps:
        for y, x in comp:
            v = lookup(y, x)
            if v is not None:
                g[y, x] = v
    for _ in range(5):
        rem = [(int(a), int(b)) for a, b in zip(*np.where(g == MASK))]
        if not rem:
            break
        rem.sort(key=lambda p: _pos_key(p[0], p[1], H, W))
        for y, x in rem:
            v = lookup(y, x)
            if v is not None:
                g[y, x] = v
    return g.tolist()
'''


def build_program(d4, palette):
    return TEMPLATE.replace('__D4__', str(int(d4))).replace('__MASK__', str(int(palette[0])))
