def build_program(d4, palette):
    k = int(d4) % 4
    # Canonical scene: divider is a row, chains below it.
    # A clockwise quarter turn sends rows to columns and a horizontal flip keeps rows as rows,
    # so the divider is a visible row for k in (0, 2) and a visible column for k in (1, 3).
    horizontal = k in (0, 2)
    header = ('BG = %d\nDIV = %d\nRED = %d\nCHAIN = %d\nGREY = %d\nHORIZONTAL = %s\n'
              % (int(palette[7]), int(palette[9]), int(palette[2]),
                 int(palette[6]), int(palette[5]), 'True' if horizontal else 'False'))
    body = '''

def _find_divider(g, horizontal):
    H, W = g.shape
    if horizontal:
        for y in range(H):
            if bool(np.all(g[y, :] == DIV)):
                return y
    else:
        for x in range(W):
            if bool(np.all(g[:, x] == DIV)):
                return x
    return None


def _far_end(g, start):
    H, W = g.shape
    dist = {start: 0}
    q = deque([start])
    best = (0, start)
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < H and 0 <= nx < W and g[ny, nx] == CHAIN and (ny, nx) not in dist:
                nd = dist[(cy, cx)] + 1
                dist[(ny, nx)] = nd
                if nd > best[0] or (nd == best[0] and (ny, nx) < best[1]):
                    best = (nd, (ny, nx))
                q.append((ny, nx))
    return best[1]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    horizontal = HORIZONTAL
    p = _find_divider(g, horizontal)
    if p is None:
        horizontal = not horizontal
        p = _find_divider(g, horizontal)
    out = g.copy()
    out[(g == RED) | (g == CHAIN) | (g == GREY)] = BG
    finals = []
    for y, x in zip(*np.where(g == RED)):
        finals.append(_far_end(g, (int(y), int(x))))
    for y, x in finals:
        out[y, x] = RED
    if p is not None:
        for y, x in finals:
            if horizontal:
                my, mx = 2 * p - y, x
            else:
                my, mx = y, 2 * p - x
            if 0 <= my < H and 0 <= mx < W:
                out[my, mx] = GREY
    return out.tolist()
'''
    return 'import numpy as np\nfrom collections import deque\n' + header + body
