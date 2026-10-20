def _orient(d4):
    # Track where the canonical stamping axis (canonical rows, picture at top)
    # and the canonical bar side (column 0) end up in visible coordinates.
    # Each item is (axis, reversed): axis 0 = visible rows, axis 1 = visible columns.
    r = (0, False)
    c = (1, False)
    if d4 >= 4:
        c = (1, True)
    for _ in range(d4 % 4):
        def rot(p):
            ax, rev = p
            if ax == 0:
                return (1, not rev)
            return (0, rev)
        r = rot(r)
        c = rot(c)
    return r, c


_VERT = '''
def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0])
    out = [row[:] for row in g]
    BG = __BG__
    MK = __MK__
    # picture lines are visible rows; stamping proceeds __DIRDESC__
    rows = list(range(H - 1, -1, -1)) if __REV__ else list(range(H))
    bc = (W - 1) if __BAREND__ else 0
    cols = [c for c in range(W) if c != bc]
    h = 0
    while h < H and g[rows[h]][bc] == MK:
        h += 1
    if h == 0:
        return out
    last = -1
    for t, r in enumerate(rows):
        if any(g[r][c] != BG for c in cols):
            last = t
    start = last + 1
    for t in range(start, H):
        src = rows[(t - start) % h]
        dst = rows[t]
        for c in cols:
            out[dst][c] = g[src][c]
    return out
'''

_HORZ = '''
def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0])
    out = [row[:] for row in g]
    BG = __BG__
    MK = __MK__
    # picture lines are visible columns; stamping proceeds __DIRDESC__
    cols = list(range(W - 1, -1, -1)) if __REV__ else list(range(W))
    br = (H - 1) if __BAREND__ else 0
    rws = [r for r in range(H) if r != br]
    h = 0
    while h < W and g[br][cols[h]] == MK:
        h += 1
    if h == 0:
        return out
    last = -1
    for t, c in enumerate(cols):
        if any(g[r][c] != BG for r in rws):
            last = t
    start = last + 1
    for t in range(start, W):
        src = cols[(t - start) % h]
        dst = cols[t]
        for r in rws:
            out[r][dst] = g[r][src]
    return out
'''


def build_program(d4, palette):
    (rax, rrev), (cax, crev) = _orient(d4)
    bg = int(palette[0])
    mk = int(palette[5])
    if rax == 0:
        src = _VERT
        desc = 'upward' if rrev else 'downward'
    else:
        src = _HORZ
        desc = 'leftward' if rrev else 'rightward'
    src = src.replace('__BG__', str(bg))
    src = src.replace('__MK__', str(mk))
    src = src.replace('__REV__', 'True' if rrev else 'False')
    src = src.replace('__BAREND__', 'True' if crev else 'False')
    src = src.replace('__DIRDESC__', desc)
    return src
