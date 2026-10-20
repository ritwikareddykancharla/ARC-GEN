def build_program(d4, palette):
    k = int(d4) % 4
    flip = int(d4) >= 4

    def mapdir(v):
        dr, dc = v
        if flip:
            dc = -dc
        for _ in range(k):
            dr, dc = dc, -dr
        return dr, dc

    # Canonical generator: for an even grey count the segment gets one extra cell
    # toward the low index along its own axis (left if horizontal, up if vertical).
    # Find where that direction ends up in visible coordinates.
    if k % 2 == 0:
        h_extra = mapdir((0, -1))[1]
        v_extra = mapdir((-1, 0))[0]
    else:
        h_extra = mapdir((-1, 0))[1]
        v_extra = mapdir((0, -1))[0]

    bg = int(palette[7])
    line = int(palette[0])
    grey = int(palette[5])

    lines = [
        'import numpy as np',
        '',
        'BG = @BG@',
        'LINE = @LINE@',
        'GREY = @GREY@',
        'H_EXTRA = @HX@',
        'V_EXTRA = @VX@',
        '',
        'def _start(d, n, extra):',
        '    if n % 2 == 1:',
        '        return d - n // 2',
        '    if extra < 0:',
        '        return d - n // 2',
        '    return d - n // 2 + 1',
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    H, W = g.shape',
        '    n = int(np.sum(g == GREY))',
        '    full_rows = [y for y in range(H) if np.all(g[y, :] == LINE)]',
        '    full_cols = [x for x in range(W) if np.all(g[:, x] == LINE)]',
        '    out = np.full((H, W), BG, dtype=int)',
        '    if len(full_rows) >= 2:',
        '        r0, r1 = full_rows[0], full_rows[-1]',
        '        c = (r0 + r1) // 2',
        '        outside = [y for y in range(H) if y < r0 or y > r1]',
        '        cand = [x for x in range(W) if outside and all(g[y, x] == LINE for y in outside)]',
        '        d = cand[len(cand) // 2] if cand else W // 2',
        '        out[:, d] = LINE',
        '        for y in (c - 1, c + 1):',
        '            if 0 <= y < H:',
        '                out[y, :] = LINE',
        '        st = _start(d, n, H_EXTRA)',
        '        for x in range(st, st + n):',
        '            if 0 <= x < W:',
        '                out[c, x] = GREY',
        '        return out.tolist()',
        '    if len(full_cols) >= 2:',
        '        c0, c1 = full_cols[0], full_cols[-1]',
        '        c = (c0 + c1) // 2',
        '        outside = [x for x in range(W) if x < c0 or x > c1]',
        '        cand = [y for y in range(H) if outside and all(g[y, x] == LINE for x in outside)]',
        '        d = cand[len(cand) // 2] if cand else H // 2',
        '        out[d, :] = LINE',
        '        for x in (c - 1, c + 1):',
        '            if 0 <= x < W:',
        '                out[:, x] = LINE',
        '        st = _start(d, n, V_EXTRA)',
        '        for y in range(st, st + n):',
        '            if 0 <= y < H:',
        '                out[y, c] = GREY',
        '        return out.tolist()',
        '    return g.tolist()',
        '',
    ]
    src = '\n'.join(lines)
    src = src.replace('@BG@', str(bg)).replace('@LINE@', str(line)).replace('@GREY@', str(grey))
    src = src.replace('@HX@', str(int(h_extra))).replace('@VX@', str(int(v_extra)))
    return src
