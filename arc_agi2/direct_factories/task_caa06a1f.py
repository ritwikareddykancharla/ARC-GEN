def build_program(d4, palette):
    n = 7

    def fwd(p):
        r, c = p
        H = n
        W = n
        if d4 >= 4:
            c = W - 1 - c
        for _ in range(d4 % 4):
            r, c = c, H - 1 - r
            H, W = W, H
        return r, c

    o = fwd((0, 0))
    a = fwd((0, 1))
    sy = a[0] - o[0]
    sx = a[1] - o[1]
    fy_end = (o[0] == 0)
    fx_end = (o[1] == 0)

    lines = []
    lines.append('# Visible-coordinate solver: periodic tile anchored at one corner, frame on the opposite sides.')
    lines.append('# Output = whole grid covered by the tile pattern, read one step along the visible pattern-advance direction.')
    lines.append('SY = ' + repr(int(sy)))
    lines.append('SX = ' + repr(int(sx)))
    lines.append('FY_END = ' + repr(bool(fy_end)))
    lines.append('FX_END = ' + repr(bool(fx_end)))
    lines.append('')
    lines.append('def _row_period(tile):')
    lines.append('    th = len(tile)')
    lines.append('    for p in range(1, th + 1):')
    lines.append('        if all(tile[i] == tile[i + p] for i in range(th - p)):')
    lines.append('            return p')
    lines.append('    return th')
    lines.append('')
    lines.append('def _col_period(tile):')
    lines.append('    th = len(tile)')
    lines.append('    tw = len(tile[0])')
    lines.append('    for p in range(1, tw + 1):')
    lines.append('        ok = True')
    lines.append('        for i in range(th):')
    lines.append('            row = tile[i]')
    lines.append('            for j in range(tw - p):')
    lines.append('                if row[j] != row[j + p]:')
    lines.append('                    ok = False')
    lines.append('                    break')
    lines.append('            if not ok:')
    lines.append('                break')
    lines.append('        if ok:')
    lines.append('            return p')
    lines.append('    return tw')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = [list(r) for r in grid]')
    lines.append('    H = len(g)')
    lines.append('    W = len(g[0])')
    lines.append('    f = g[H - 1 if FY_END else 0][W - 1 if FX_END else 0]')
    lines.append('    ys = [y for y in range(H) for x in range(W) if g[y][x] != f]')
    lines.append('    xs = [x for y in range(H) for x in range(W) if g[y][x] != f]')
    lines.append('    if not ys:')
    lines.append('        return [row[:] for row in g]')
    lines.append('    y0, y1 = min(ys), max(ys)')
    lines.append('    x0, x1 = min(xs), max(xs)')
    lines.append('    tile = [g[y][x0:x1 + 1] for y in range(y0, y1 + 1)]')
    lines.append('    py = _row_period(tile)')
    lines.append('    px = _col_period(tile)')
    lines.append('    out = []')
    lines.append('    for y in range(H):')
    lines.append('        ty = (y + SY - y0) % py')
    lines.append('        out.append([tile[ty][(x + SX - x0) % px] for x in range(W)])')
    lines.append('    return out')
    return '\n'.join(lines) + '\n'
