def build_program(d4, palette):
    down = (1, 0)
    right = (0, 1)
    if d4 >= 4:
        right = (0, -1)
    for _ in range(d4 % 4):
        down = (down[1], -down[0])
        right = (right[1], -right[0])
    bg = int(palette[0])
    grey = int(palette[5])
    header = (
        'import numpy as np\n'
        'from collections import deque\n'
        'BG = ' + repr(bg) + '\n'
        'GREY = ' + repr(grey) + '\n'
        'DOWN = ' + repr(tuple(down)) + '\n'
        'RIGHT = ' + repr(tuple(right)) + '\n'
    )
    body = '''
def _comps(mask):
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

def _v(y, x):
    return y * DOWN[0] + x * DOWN[1]

def _u(y, x):
    return y * RIGHT[0] + x * RIGHT[1]

def _cell(v, u):
    return (v * DOWN[0] + u * RIGHT[0], v * DOWN[1] + u * RIGHT[1])

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    greys = _comps(g == GREY)
    greys.sort(key=lambda c: -len(c))
    if len(greys) < 2:
        return out.tolist()
    frame, comb = greys[0], greys[1]
    top = min(_v(y, x) for y, x in frame) + 1
    cols = {}
    for y in range(h):
        for x in range(w):
            val = int(g[y, x])
            if val != BG and val != GREY:
                u = _u(y, x)
                c, n = cols.get(u, (val, 0))
                cols[u] = (c, n + 1)
    if not cols:
        return out.tolist()
    cu = [_u(y, x) for y, x in comb]
    cv = [_v(y, x) for y, x in comb]
    du = min(cols) - min(cu)
    for y, x in comb:
        out[y, x] = BG
    for v in range(top, max(cv) + 1):
        for u in range(min(cu) + du, max(cu) + du + 1):
            y, x = _cell(v, u)
            if 0 <= y < h and 0 <= x < w:
                out[y, x] = BG
    shifted = set((_v(y, x), _u(y, x) + du) for y, x in comb)
    for v, u in shifted:
        y, x = _cell(v, u)
        if 0 <= y < h and 0 <= x < w:
            out[y, x] = GREY
    for u, (c, n) in cols.items():
        vs = [v for v, uu in shifted if uu == u]
        if not vs:
            continue
        t = min(vs)
        space = t - top
        k = min(n, space)
        for i in range(space):
            y, x = _cell(t - 1 - i, u)
            if 0 <= y < h and 0 <= x < w:
                out[y, x] = c if i < k else GREY
    return out.tolist()
'''
    return header + body
