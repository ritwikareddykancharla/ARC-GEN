def build_program(d4, palette):
    BG = int(palette[0])
    SH = int(palette[3])
    LN = int(palette[2])
    MK = int(palette[8])
    src = '''
def solve(demonstrations, grid):
    BG = %d
    SH = %d
    LN = %d
    MK = %d
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [[(BG if v == SH else v) for v in row] for row in g]
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] == SH]
    if not cells:
        return out
    ln_count = sum(1 for r in range(H) for c in range(W) if g[r][c] == LN)
    full_rows = [r for r in range(H) if all(g[r][c] == LN for c in range(W))]
    full_cols = [c for c in range(W) if all(g[r][c] == LN for r in range(H))]
    row_ok = bool(full_rows) and ln_count == W
    col_ok = bool(full_cols) and ln_count == H
    if not row_ok and not col_ok:
        row_ok = bool(full_rows)
        col_ok = bool(full_cols) and not row_ok
    if row_ok:
        ly = full_rows[0]
        rs = [r for r, c in cells]
        r0, r1 = min(rs), max(rs)
        if r0 > ly:
            dy = ly + 1 - r0
            far = r1 + dy + 1
        else:
            dy = ly - 1 - r1
            far = r0 + dy - 1
        for r, c in cells:
            nr = r + dy
            if 0 <= nr < H:
                out[nr][c] = SH
        if 0 <= far < H:
            for c in range(W):
                out[far][c] = MK
        return out
    if col_ok:
        lx = full_cols[0]
        cs = [c for r, c in cells]
        c0, c1 = min(cs), max(cs)
        if c0 > lx:
            dx = lx + 1 - c0
            far = c1 + dx + 1
        else:
            dx = lx - 1 - c1
            far = c0 + dx - 1
        for r, c in cells:
            nc = c + dx
            if 0 <= nc < W:
                out[r][nc] = SH
        if 0 <= far < W:
            for r in range(H):
                out[r][far] = MK
        return out
    return [list(row) for row in g]
''' % (BG, SH, LN, MK)
    return src
