def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(x) for x in palette]
    bg = pal[0]
    same = pal[2]
    diff = pal[5]
    # Where the original legend column (last column, read top-down) lands in
    # visible coordinates: (axis, index of border line, read reversed?)
    specs = {
        0: ('col', -1, False),
        1: ('row', -1, True),
        2: ('col', 0, True),
        3: ('row', 0, False),
        4: ('col', 0, False),
        5: ('row', 0, True),
        6: ('col', -1, True),
        7: ('row', -1, False),
    }
    axis, idx, read_rev = specs[d4]
    # The original table is symmetric, so its image only depends on which
    # corner the header corner lands in.
    row_rev = d4 in (2, 3, 5, 6)
    col_rev = d4 in (1, 2, 4, 5)
    header_lines = [
        'import numpy as np',
        '',
        'BG = ' + str(bg),
        'SAME = ' + str(same),
        'DIFF = ' + str(diff),
        'AXIS = ' + repr(axis),
        'IDX = ' + str(idx),
        'READ_REV = ' + str(bool(read_rev)),
        'ROW_REV = ' + str(bool(row_rev)),
        'COL_REV = ' + str(bool(col_rev)),
        '',
    ]
    body = '''
def _canon(m):
    vs = []
    for k in range(4):
        r = np.rot90(m, k)
        vs.append(r)
        vs.append(np.fliplr(r))
    return min((tuple(v.shape), tuple(int(x) for x in v.flatten())) for v in vs)


def _block_pos(i, size, rev):
    if rev:
        return size - 2 - 3 * i
    return 3 * i


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    if AXIS == 'col':
        line = g[:, IDX].tolist()
    else:
        line = g[IDX, :].tolist()
    if READ_REV:
        line = line[::-1]
    leg = []
    for c in line:
        c = int(c)
        if c != BG and c not in leg:
            leg.append(c)
    sub = g.copy()
    if AXIS == 'col':
        sub[:, IDX] = -1
    else:
        sub[IDX, :] = -1
    keys = {}
    for c in leg:
        ys, xs = np.nonzero(sub == c)
        if len(ys) == 0:
            keys[c] = ('empty', c)
            continue
        m = (sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1] == c).astype(int)
        keys[c] = _canon(m)
    n = len(leg)
    S = 3 * (n + 1) - 1
    out = np.full((S, S), BG, dtype=int)
    r0 = _block_pos(0, S, ROW_REV)
    c0 = _block_pos(0, S, COL_REV)
    for i, c in enumerate(leg):
        rp = _block_pos(i + 1, S, ROW_REV)
        cp = _block_pos(i + 1, S, COL_REV)
        out[r0:r0 + 2, cp:cp + 2] = c
        out[rp:rp + 2, c0:c0 + 2] = c
    for i, a in enumerate(leg):
        rp = _block_pos(i + 1, S, ROW_REV)
        for j, b in enumerate(leg):
            if i == j:
                continue
            cp = _block_pos(j + 1, S, COL_REV)
            v = SAME if keys[a] == keys[b] else DIFF
            out[rp:rp + 2, cp:cp + 2] = v
    return out.tolist()
'''
    return chr(10).join(header_lines) + body
