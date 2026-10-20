def build_program(d4, palette):
    k = d4 % 4
    # Original 'down' direction (toward the gray pieces, away from the wall),
    # in visible coordinates. A row reversal does not change it; each clockwise
    # rotation maps (dr, dc) -> (dc, -dr).
    dr, dc = [(1, 0), (0, -1), (-1, 0), (0, 1)][k]
    blue = int(palette[1])
    gray = int(palette[5])
    red = int(palette[2])
    header = (
        'import numpy as np\n'
        'from collections import deque\n'
        'BLUE = ' + repr(blue) + '\n'
        'GRAY = ' + repr(gray) + '\n'
        'RED = ' + repr(red) + '\n'
        'DR = ' + repr(dr) + '\n'
        'DC = ' + repr(dc) + '\n'
    )
    body = '''
def _components(mask):
    mask = np.asarray(mask, bool)
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
                out.append(sorted(cells))
    return out

def _proj(y, x):
    # coordinate along the 'downward' axis (away from wall toward the pieces)
    return y * DR + x * DC

def _on_far_edge(y, x, H, W):
    if DR == 1:
        return y == H - 1
    if DR == -1:
        return y == 0
    if DC == 1:
        return x == W - 1
    return x == 0

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    blues = np.argwhere(g == BLUE)
    if len(blues) == 0:
        return out.tolist()
    base = max(_proj(int(y), int(x)) for y, x in blues)
    below = set()
    for region in _components(g != BLUE):
        if any(_on_far_edge(y, x, H, W) for y, x in region):
            below.update(region)
    hmask = np.zeros(g.shape, bool)
    for y, x in below:
        if _proj(y, x) <= base:
            hmask[y, x] = True
    recesses = [set(c) for c in _components(hmask)]
    isblue = (g == BLUE)
    for cells in _components(g == GRAY):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, x0 = min(ys), min(xs)
        m = np.zeros((max(ys) - y0 + 1, max(xs) - x0 + 1), bool)
        for y, x in cells:
            m[y - y0, x - x0] = True
        fits = False
        for k in range(4):
            rc = [(int(a), int(b)) for a, b in np.argwhere(np.rot90(m, k))]
            for hole in recesses:
                hy, hx = min(hole)
                for py, px in rc:
                    oy, ox = hy - py, hx - px
                    placed = {(a + oy, b + ox) for a, b in rc}
                    if not hole <= placed:
                        continue
                    ok = True
                    for a, b in placed:
                        if not (0 <= a < H and 0 <= b < W) or isblue[a, b]:
                            ok = False
                            break
                    if ok:
                        fits = True
                        break
                if fits:
                    break
            if fits:
                break
        if fits:
            for y, x in cells:
                out[y, x] = RED
    return out.tolist()
'''
    return header + body
