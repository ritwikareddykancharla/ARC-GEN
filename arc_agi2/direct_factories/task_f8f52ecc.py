_BODY = '''
from collections import deque

OTHER = "h" if PRIMARY == "v" else "v"
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(g, col):
    h = len(g)
    w = len(g[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for y in range(h):
        for x in range(w):
            if g[y][x] == col and not seen[y][x]:
                seen[y][x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in STEPS:
                        ny = cy + dy
                        nx = cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == col:
                            seen[ny][nx] = True
                            q.append((ny, nx))
                out.append(sorted(cells))
    return out


def _sign(v):
    return (v > 0) - (v < 0)


def _seg(p, q):
    out = []
    y, x = p
    dy = _sign(q[0] - y)
    dx = _sign(q[1] - x)
    while (y, x) != (q[0], q[1]):
        y += dy
        x += dx
        out.append((y, x))
    return out


def _lpath(a, b, first):
    # first == "v": move along the visible vertical axis first; "h": horizontal first.
    corner = (b[0], a[1]) if first == "v" else (a[0], b[1])
    pts = _seg(a, corner) + _seg(corner, b)
    return pts[:-1]


def _link_colour(g, col):
    while True:
        comps = _components(g, col)
        if len(comps) < 2:
            return
        gid = {}
        for i, cs in enumerate(comps):
            for c in cs:
                gid[c] = i

        def axis(c):
            i = gid[c]
            y, x = c
            vert = gid.get((y - 1, x)) == i or gid.get((y + 1, x)) == i
            horz = gid.get((y, x - 1)) == i or gid.get((y, x + 1)) == i
            for ax in (PRIMARY, OTHER):
                if ax == "v" and vert:
                    return "v"
                if ax == "h" and horz:
                    return "h"
            return None

        best = None
        n = len(comps)
        for i in range(n):
            for j in range(i + 1, n):
                for a in comps[i]:
                    for b in comps[j]:
                        d = abs(a[0] - b[0]) + abs(a[1] - b[1])
                        if best is not None and best[0][0] is False and d >= best[0][1]:
                            continue
                        opts = []
                        for first in (PRIMARY, OTHER):
                            p = _lpath(a, b, first)
                            if all(g[yy][xx] == BG for yy, xx in p):
                                opts.append(p)
                        if not opts:
                            continue
                        straight = a[0] == b[0] or a[1] == b[1]
                        if straight or len(opts) == 1:
                            det = True
                            p = opts[0]
                        else:
                            ax = axis(a)
                            if ax:
                                det = True
                                p = _lpath(a, b, ax)
                            else:
                                bx = axis(b)
                                if bx:
                                    det = True
                                    p = _lpath(b, a, bx)
                                else:
                                    det = False
                                    p = opts[0]
                        key = (not det, d)
                        if best is None or key < best[0]:
                            best = (key, p)
        if best is None:
            return
        for yy, xx in best[1]:
            g[yy][xx] = col


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    if not g or not g[0]:
        return g
    present = set(v for row in g for v in row)
    for col in ORDER:
        if col in present and col != BG and col != WALL:
            _link_colour(g, col)
    return g
'''


def build_program(d4, palette):
    pal = [int(palette[c]) for c in range(10)]
    order = sorted(pal[c] for c in range(10) if c not in (1, 8))
    # Odd quarter-turns swap the original vertical axis with the visible horizontal one.
    primary = "v" if int(d4) % 2 == 0 else "h"
    head = chr(10).join([
        "BG = " + str(pal[1]),
        "WALL = " + str(pal[8]),
        "ORDER = " + repr(order),
        "PRIMARY = " + repr(primary),
        "",
    ])
    return head + _BODY
