TEMPLATE = '''import numpy as np
from collections import Counter

FRAME = __FRAME__
EMPTY = __EMPTY__
BEAM = __BEAM__
STRIP = __STRIP__
LDIR = __LDIR__
TURN = {'L': __TURNL__, 'R': __TURNR__}


def _canvas(g):
    fr = g == FRAME
    rows = np.where(fr.any(axis=1))[0]
    cols = np.where(fr.any(axis=0))[0]
    if len(rows) == 0:
        return g.copy()
    if STRIP == (-1, 0):
        return g[int(rows.max()) + 1:, :].copy()
    if STRIP == (1, 0):
        return g[:int(rows.min()), :].copy()
    if STRIP == (0, -1):
        return g[:, int(cols.max()) + 1:].copy()
    return g[:, :int(cols.min())].copy()


def _legend(g):
    H, W = g.shape
    rdir = (-LDIR[0], -LDIR[1])
    legend = {}
    ys, xs = np.where(g == EMPTY)
    for y, x in zip(ys.tolist(), xs.tolist()):
        for side, (dy, dx) in (('L', LDIR), ('R', rdir)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W:
                v = int(g[ny, nx])
                if v != EMPTY and v != FRAME:
                    legend[v] = side
    return legend


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    legend = _legend(g)
    body = _canvas(g)
    out = body.copy()
    h, w = body.shape
    if h == 0 or w == 0:
        return out.tolist()
    bg = Counter(body.ravel().tolist()).most_common(1)[0][0]
    ys, xs = np.where(body == BEAM)
    if len(ys) == 0:
        return out.tolist()
    sy, sx = int(ys.min()), int(xs.min())
    bh = int(ys.max()) - sy + 1
    bw = int(xs.max()) - sx + 1

    def blocker(y, x):
        if y < 0 or x < 0 or y + bh > h or x + bw > w:
            return 'edge'
        win = body[y:y + bh, x:x + bw].ravel().tolist()
        vals = [int(v) for v in win if v != bg and v != BEAM]
        if not vals:
            return None
        cnt = Counter(vals)
        best = max(cnt.values())
        return min(v for v in cnt if cnt[v] == best)

    for d0 in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        y, x = sy, sx
        dy, dx = d0
        seen = set()
        for _ in range(4000):
            st = (y, x, dy, dx)
            if st in seen:
                break
            seen.add(st)
            ny, nx = y + dy, x + dx
            b = blocker(ny, nx)
            if b is None:
                y, x = ny, nx
                out[y:y + bh, x:x + bw] = BEAM
                continue
            if b == 'edge':
                break
            side = legend.get(b)
            if side is None:
                break
            dy, dx = TURN[side][(dy, dx)]
    return out.tolist()
'''


def build_program(d4, palette):
    def refl(v):
        return (v[0], -v[1])

    def rot(v):
        return (v[1], -v[0])

    def M(v):
        if d4 >= 4:
            v = refl(v)
        for _ in range(d4 % 4):
            v = rot(v)
        return v

    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    inv = {}
    for u in dirs:
        inv[M(u)] = u

    def left(u):
        return (-u[1], u[0])

    def right(u):
        return (u[1], -u[0])

    turn_l = {}
    turn_r = {}
    for v in dirs:
        turn_l[v] = M(left(inv[v]))
        turn_r[v] = M(right(inv[v]))
    code = TEMPLATE
    code = code.replace('__FRAME__', repr(int(palette[5])))
    code = code.replace('__EMPTY__', repr(int(palette[0])))
    code = code.replace('__BEAM__', repr(int(palette[8])))
    code = code.replace('__STRIP__', repr(M((-1, 0))))
    code = code.replace('__LDIR__', repr(M((0, -1))))
    code = code.replace('__TURNL__', repr(turn_l))
    code = code.replace('__TURNR__', repr(turn_r))
    return code
