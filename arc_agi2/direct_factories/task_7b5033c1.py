_SPECS = {
    0: (((0, 1), (1, 1)), False, False),
    1: (((1, -1), (0, 1)), True, True),
    2: (((0, -1), (1, -1)), False, True),
    3: (((1, 1), (0, -1)), True, False),
    4: (((0, 1), (1, -1)), False, False),
    5: (((1, -1), (0, -1)), True, True),
    6: (((0, -1), (1, 1)), False, True),
    7: (((1, 1), (0, 1)), True, False),
}

_BODY = '''
def _key(cell):
    return tuple(s * cell[a] for a, s in KEY_SPEC)


def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    if g.ndim != 2 or g.size == 0:
        return [[0]]
    H, W = g.shape
    bg = Counter(g.ravel().tolist()).most_common(1)[0][0]
    path = set()
    for y in range(H):
        for x in range(W):
            if g[y, x] != bg:
                path.add((y, x))
    if not path:
        return [[int(bg)]]

    def nbrs(c):
        y, x = c
        out = []
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (y + dy, x + dx)
            if n in path:
                out.append(n)
        return out

    ends = [c for c in path if len(nbrs(c)) == 1]
    pool = ends if ends else list(path)
    start = min(pool, key=_key)
    order = [start]
    seen = {start}
    cur = start
    while True:
        nxt = [n for n in nbrs(cur) if n not in seen]
        if not nxt:
            break
        cur = min(nxt, key=_key)
        seen.add(cur)
        order.append(cur)
    seq = [int(g[c]) for c in order]
    if REVERSE:
        seq = seq[::-1]
    if AS_ROW:
        return [seq]
    return [[v] for v in seq]
'''


def build_program(d4, palette):
    key, as_row, rev = _SPECS[int(d4) % 8]
    header = ('import numpy as np\n'
              'from collections import Counter\n\n'
              'KEY_SPEC = ' + repr(key) + '\n'
              'AS_ROW = ' + repr(as_row) + '\n'
              'REVERSE = ' + repr(rev) + '\n')
    return header + _BODY
