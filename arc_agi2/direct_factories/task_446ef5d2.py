def build_program(d4, palette):
    dv = (1, 0)
    rv = (0, 1)
    if d4 >= 4:
        rv = (0, -1)
    for _ in range(d4 % 4):
        dv = (dv[1], -dv[0])
        rv = (rv[1], -rv[0])
    src = '''import numpy as np
from collections import Counter, deque

DR, DC = @DR@, @DC@
RR, RC = @RR@, @RC@


def _key(y, x):
    return (DR * y + DC * x, RR * y + RC * x)


def _components(mask):
    H, W = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out


def _tile(pieces, order, frame, hh, ww, budget):
    seq = sorted([(y, x) for y in range(hh) for x in range(ww)], key=lambda p: _key(p[0], p[1]))
    n = len(seq)
    R = [[-1] * ww for _ in range(hh)]
    used = [False] * len(pieces)
    placed = []
    state = [budget, False]

    def rec(start):
        if state[1] or state[0] <= 0:
            return
        state[0] -= 1
        k = start
        while k < n and R[seq[k][0]][seq[k][1]] != -1:
            k += 1
        if k == n:
            state[1] = True
            return
        ey, ex = seq[k]
        for i in order:
            if used[i]:
                continue
            ok = True
            for ry, rx, c in pieces[i]:
                yy, xx = ey + ry, ex + rx
                if yy < 0 or xx < 0 or yy >= hh or xx >= ww or R[yy][xx] != -1:
                    ok = False
                    break
                if (yy == 0 or yy == hh - 1 or xx == 0 or xx == ww - 1) and c != frame:
                    ok = False
                    break
            if not ok:
                continue
            for ry, rx, c in pieces[i]:
                R[ey + ry][ex + rx] = c
            used[i] = True
            placed.append((i, ey, ex))
            rec(k)
            if state[1]:
                return
            placed.pop()
            used[i] = False
            for ry, rx, c in pieces[i]:
                R[ey + ry][ex + rx] = -1

    rec(0)
    return list(placed) if state[1] else None


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    cnt = Counter(g.ravel().tolist())
    bg = cnt.most_common(1)[0][0]
    marker = None
    for c, k in sorted(cnt.items()):
        if c != bg and k == 3:
            ys, xs = np.where(g == c)
            if ys.max() - ys.min() == 1 and xs.max() - xs.min() == 1:
                marker = c
    if marker is None:
        return g.tolist()
    mask = (g != bg) & (g != marker)
    if not mask.any():
        return g.tolist()
    frame = Counter(g[mask].tolist()).most_common(1)[0][0]
    pieces = []
    components = sorted(_components(mask),
                        key=lambda cells: min(_key(y, x) for y, x in cells))
    for cells in components:
        ay, ax = min(cells, key=lambda p: _key(p[0], p[1]))
        pieces.append([(y - ay, x - ax, int(g[y, x])) for y, x in cells])
    order = sorted(range(len(pieces)), key=lambda i: -len(pieces[i]))
    A = sum(len(p) for p in pieces)
    ys, xs = np.where(g == marker)
    y0, x0 = int(ys.min()), int(xs.min())
    miss = None
    for y in (y0, y0 + 1):
        for x in (x0, x0 + 1):
            if g[y, x] != marker and miss is None:
                miss = (y, x)
    if miss is None:
        return g.tolist()
    dy = 1 if miss[0] == y0 + 1 else -1
    dx = 1 if miss[1] == x0 + 1 else -1
    for native_height in range(1, A + 1):
        if A % native_height:
            continue
        hh, ww = @DIMS@
        ty = miss[0] if dy == 1 else miss[0] - hh + 1
        tx = miss[1] if dx == 1 else miss[1] - ww + 1
        if ty < 0 or tx < 0 or ty + hh > H or tx + ww > W:
            continue
        placed = _tile(pieces, order, frame, hh, ww, 200000)
        if placed is not None:
            out = np.full_like(g, bg)
            for i, ey, ex in placed:
                for ry, rx, c in pieces[i]:
                    out[ty + ey + ry, tx + ex + rx] = c
            return out.tolist()
    return g.tolist()
'''
    src = src.replace('@DR@', str(dv[0])).replace('@DC@', str(dv[1]))
    src = src.replace('@RR@', str(rv[0])).replace('@RC@', str(rv[1]))
    src = src.replace('@DIMS@', 'native_height, A // native_height'
                      if d4 % 2 == 0 else 'A // native_height, native_height')
    return src
