def build_program(d4, palette):
    k = d4 % 4
    # Visible direction of canonical +column (rightward) and +row (downward).
    rv = (0, -1) if d4 >= 4 else (0, 1)
    dv = (1, 0)
    for _ in range(k):
        rv = (rv[1], -rv[0])
        dv = (dv[1], -dv[0])
    a_expr = {(0, 1): 'x', (0, -1): '(W - 1 - x)', (1, 0): 'y', (-1, 0): '(H - 1 - y)'}[rv]
    f_expr = {(1, 0): '(H - 1 - y)', (-1, 0): 'y', (0, 1): '(W - 1 - x)', (0, -1): 'x'}[dv]
    if rv[0] == 0:
        x_expr = 'a' if rv[1] == 1 else '(W - 1 - a)'
        y_expr = '(H - 1 - f)' if dv[0] == 1 else 'f'
    else:
        y_expr = 'a' if rv[0] == 1 else '(H - 1 - a)'
        x_expr = '(W - 1 - f)' if dv[1] == 1 else 'f'
    a_side = {(0, 1): 'left', (0, -1): 'right', (1, 0): 'top', (-1, 0): 'bottom'}[rv]
    f_side = {(1, 0): 'bottom', (-1, 0): 'top', (0, 1): 'right', (0, -1): 'left'}[dv]
    bg = int(palette[0])
    template = '''import numpy as np
from collections import deque

BG = @BG@
# The first stack hugs the @ASIDE@ edge of the visible grid; the second stack
# sits one blank lane further from that edge. Both stacks start at the
# @FSIDE@ edge and grow away from it with one blank line between objects.


def _from_anchor(y, x, H, W):
    # distance of a cell from the @ASIDE@ edge
    return @AEXPR@


def _from_floor(y, x, H, W):
    # distance of a cell from the @FSIDE@ edge
    return @FEXPR@


def _to_cell(a, f, H, W):
    return (@YEXPR@, @XEXPR@)


def _components(g):
    H, W = g.shape
    seen = np.zeros((H, W), dtype=bool)
    comps = []
    for y in range(H):
        for x in range(W):
            if int(g[y, x]) == BG or seen[y, x]:
                continue
            col = int(g[y, x])
            seen[y, x] = True
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and int(g[ny, nx]) == col:
                            seen[ny, nx] = True
                            q.append((ny, nx))
            comps.append((col, sorted(cells)))
    return comps


def _dist(c1, c2):
    return min(max(abs(p[0] - q[0]), abs(p[1] - q[1])) for p in c1 for q in c2)


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = np.full((H, W), BG, dtype=int)
    objs = []
    for col, cells in _components(g):
        A = [_from_anchor(y, x, H, W) for y, x in cells]
        F = [_from_floor(y, x, H, W) for y, x in cells]
        objs.append([col, cells, min(A), max(A), min(F), max(F)])
    if not objs:
        return out.tolist()
    # colour of the object nearest the anchor edge (tie: farthest from floor)
    leftc = min(objs, key=lambda o: (o[2], -o[5]))[0]
    group_a = [o for o in objs if o[0] == leftc]
    group_b = [o for o in objs if o[0] != leftc]
    group_b.sort(key=lambda o: (-o[5], o[2]))
    group_a.sort(key=lambda o: (-len(o[1]), -o[5], o[2]))
    remaining = list(group_b)
    pairs = []
    for oa in group_a:
        if remaining:
            ob = min(remaining, key=lambda o: _dist(oa[1], o[1]))
            remaining.remove(ob)
        else:
            ob = None
        pairs.append((oa, ob))
    for ob in remaining:
        pairs.append((None, ob))
    wa = max([o[3] - o[2] + 1 for o in group_a] or [0])
    lanes = [0, wa + 1]
    base = [0, 0]

    def place(o, lane):
        for y, x in o[1]:
            a = lanes[lane] + (_from_anchor(y, x, H, W) - o[2])
            f = base[lane] + (_from_floor(y, x, H, W) - o[4])
            ny, nx = _to_cell(a, f, H, W)
            if 0 <= ny < H and 0 <= nx < W:
                out[ny, nx] = o[0]
        base[lane] += (o[5] - o[4] + 1) + 1

    for oa, ob in pairs:
        if oa is not None:
            place(oa, 0)
        if ob is not None:
            place(ob, 1)
    return out.tolist()
'''
    src = template
    for key, val in (('@BG@', str(bg)), ('@ASIDE@', a_side), ('@FSIDE@', f_side),
                     ('@AEXPR@', a_expr), ('@FEXPR@', f_expr),
                     ('@YEXPR@', y_expr), ('@XEXPR@', x_expr)):
        src = src.replace(key, val)
    return src
