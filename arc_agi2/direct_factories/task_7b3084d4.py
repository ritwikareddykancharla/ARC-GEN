TEMPLATE = '''import math
import numpy as np

BG = __BG__
MARK = __MARK__
CORNER = __CORNER__


def _components(g):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if g[y, x] == BG or seen[y, x]:
                continue
            stack = [(y, x)]
            seen[y, x] = True
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] != BG:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
            comps.append(sorted(cells))
    return comps


def _rotations(g, cells):
    y0 = min(c[0] for c in cells)
    x0 = min(c[1] for c in cells)
    y1 = max(c[0] for c in cells)
    x1 = max(c[1] for c in cells)
    a = np.full((y1 - y0 + 1, x1 - x0 + 1), -1, dtype=int)
    for y, x in cells:
        a[y - y0, x - x0] = int(g[y, x])
    out = []
    seen = set()
    for k in range(4):
        r = np.rot90(a, -k)
        key = (r.shape, tuple(r.ravel().tolist()))
        if key in seen:
            continue
        seen.add(key)
        out.append([(i, j, int(r[i, j])) for i in range(r.shape[0])
                    for j in range(r.shape[1]) if r[i, j] >= 0])
    return out


def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    if g.ndim != 2 or g.size == 0:
        return [list(row) for row in grid]
    comps = _components(g)
    total = sum(len(c) for c in comps)
    if total == 0:
        return [[BG]]
    n = math.isqrt(total)
    if n * n != total:
        n = max(1, int(round(math.sqrt(total))))
    pieces = [_rotations(g, c) for c in comps]
    P = len(pieces)
    mi = None
    for i, c in enumerate(comps):
        if any(g[y, x] == MARK for y, x in c):
            mi = i
            break
    corners = [(0, 0), (0, n - 1), (n - 1, n - 1), (n - 1, 0)]
    cr, cc = corners[CORNER]
    board = [[-1] * n for _ in range(n)]
    owner = [[-1] * n for _ in range(n)]
    used = [False] * P
    result = [None]

    def fits(cells, dy, dx):
        for y, x, v in cells:
            yy, xx = y + dy, x + dx
            if not (0 <= yy < n and 0 <= xx < n) or board[yy][xx] >= 0:
                return False
        return True

    def put(cells, dy, dx, idx):
        for y, x, v in cells:
            board[y + dy][x + dx] = v if idx >= 0 else -1
            owner[y + dy][x + dx] = idx

    def rec():
        empty = None
        for y in range(n):
            for x in range(n):
                if board[y][x] < 0:
                    empty = (y, x)
                    break
            if empty is not None:
                break
        if empty is None:
            own = set(owner[y][x] for y, x in corners)
            if len(own) == min(4, P):
                result[0] = [row[:] for row in board]
                return True
            return False
        ey, ex = empty
        for i in range(P):
            if used[i]:
                continue
            for cells in pieces[i]:
                fy, fx, _ = cells[0]
                dy, dx = ey - fy, ex - fx
                if not fits(cells, dy, dx):
                    continue
                put(cells, dy, dx, i)
                used[i] = True
                if rec():
                    return True
                used[i] = False
                put(cells, dy, dx, -1)
        return False

    if mi is not None:
        used[mi] = True
        for cells in pieces[mi]:
            marks = [(y, x) for y, x, v in cells if v == MARK]
            my, mx = marks[0]
            dy, dx = cr - my, cc - mx
            if not fits(cells, dy, dx):
                continue
            put(cells, dy, dx, mi)
            if rec():
                break
            put(cells, dy, dx, -1)
    else:
        rec()
    if result[0] is None:
        return [[BG] * n for _ in range(n)]
    return result[0]
'''


def build_program(d4, palette):
    d4 = int(d4) % 8
    start = 1 if d4 >= 4 else 0
    corner = (start + d4 % 4) % 4
    src = TEMPLATE
    src = src.replace('__BG__', str(int(palette[0])))
    src = src.replace('__MARK__', str(int(palette[5])))
    src = src.replace('__CORNER__', str(int(corner)))
    return src
