def build_program(d4, palette):
    # Original mechanism: lines run along 'down' (+1,0); colours are read along 'down';
    # pyramid rows are laid out along 'right' (0,+1); the widest row sits on the far 'down' edge.
    dr, dc = 1, 0
    rr, rc = 0, 1
    if d4 >= 4:
        dc = -dc
        rc = -rc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
        rr, rc = rc, -rr
    bg = int(palette[0])
    src = '''
DR = %d
DC = %d
RR = %d
RC = %d
BG = %d

def _chunks(seq):
    rows = []
    i, w = 0, 1
    while i < len(seq):
        rows.append(seq[i:i + w])
        i += w
        w += 2
    return rows

def solve(demonstrations, grid):
    g = [list(r) for r in grid]
    H = len(g)
    W = len(g[0])
    out = [row[:] for row in g]
    lines = []
    if DC == 0:
        # lines are columns, read along DR
        ys = list(range(H)) if DR == 1 else list(range(H - 1, -1, -1))
        for x in range(W):
            seq = [g[y][x] for y in ys if g[y][x] != BG]
            if seq:
                lines.append((x, seq))
                for y in range(H):
                    out[y][x] = BG
    else:
        # lines are rows, read along DC
        xs = list(range(W)) if DC == 1 else list(range(W - 1, -1, -1))
        for y in range(H):
            seq = [g[y][x] for x in xs if g[y][x] != BG]
            if seq:
                lines.append((y, seq))
                for x in range(W):
                    out[y][x] = BG
    for fixed, seq in lines:
        rows = _chunks(seq)
        n = len(rows)
        for k, row in enumerate(rows):
            depth = n - 1 - k
            for j, c in enumerate(row):
                off = j - k
                if DC == 0:
                    y = (H - 1 - depth) if DR == 1 else depth
                    x = fixed + off * RC
                else:
                    x = (W - 1 - depth) if DC == 1 else depth
                    y = fixed + off * RR
                if 0 <= y < H and 0 <= x < W:
                    out[y][x] = c
    return out
''' % (dr, dc, rr, rc, bg)
    return src
