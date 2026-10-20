def build_program(d4, palette):
    bg = int(palette[0])
    mark = int(palette[5])
    lines = [
        'BG = ' + repr(bg),
        'MARK = ' + repr(mark),
        '',
        'def _sgn(v):',
        '    return (v > 0) - (v < 0)',
        '',
        'def solve(demonstrations, grid):',
        '    g = [[int(v) for v in row] for row in grid]',
        '    H = len(g)',
        '    W = len(g[0]) if H else 0',
        '    out = [row[:] for row in g]',
        '    pts = [(r, c, g[r][c]) for r in range(H) for c in range(W) if g[r][c] != BG]',
        '    if not pts:',
        '        return out',
        '    rs = [p[0] for p in pts]',
        '    cs = [p[1] for p in pts]',
        '    cy = (min(rs) + max(rs)) // 2',
        '    cx = (min(cs) + max(cs)) // 2',
        '    out[cy][cx] = MARK',
        '    for r, c, v in pts:',
        '        ny = cy + _sgn(r - cy)',
        '        nx = cx + _sgn(c - cx)',
        '        if 0 <= ny < H and 0 <= nx < W and (ny, nx) != (cy, cx):',
        '            out[ny][nx] = v',
        '    return out',
        '',
    ]
    return '\n'.join(lines)
