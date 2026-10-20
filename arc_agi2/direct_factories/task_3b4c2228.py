def build_program(d4, palette):
    n = 3
    cells = []
    for i in range(3):
        r, c = i, i
        if d4 >= 4:
            c = n - 1 - c
        for _ in range(d4 % 4):
            r, c = c, n - 1 - r
        cells.append((r, c))
    fg = int(palette[3])
    one = int(palette[1])
    bg = int(palette[0])
    lines = []
    lines.append('FG = %d' % fg)
    lines.append('ONE = %d' % one)
    lines.append('BG = %d' % bg)
    lines.append('CELLS = %r' % (cells,))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = [list(row) for row in grid]')
    lines.append('    h = len(g)')
    lines.append('    w = len(g[0]) if h else 0')
    lines.append('    seen = [[False] * w for _ in range(h)]')
    lines.append('    count = 0')
    lines.append('    for y in range(h):')
    lines.append('        for x in range(w):')
    lines.append('            if g[y][x] == FG and not seen[y][x]:')
    lines.append('                seen[y][x] = True')
    lines.append('                stack = [(y, x)]')
    lines.append('                comp = []')
    lines.append('                while stack:')
    lines.append('                    cy, cx = stack.pop()')
    lines.append('                    comp.append((cy, cx))')
    lines.append('                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):')
    lines.append('                        ny, nx = cy + dy, cx + dx')
    lines.append('                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == FG:')
    lines.append('                            seen[ny][nx] = True')
    lines.append('                            stack.append((ny, nx))')
    lines.append('                if len(comp) == 4:')
    lines.append('                    ys = [p[0] for p in comp]')
    lines.append('                    xs = [p[1] for p in comp]')
    lines.append('                    if max(ys) - min(ys) == 1 and max(xs) - min(xs) == 1:')
    lines.append('                        count += 1')
    lines.append('    out = [[BG] * 3 for _ in range(3)]')
    lines.append('    for i in range(min(count, 3)):')
    lines.append('        r, c = CELLS[i]')
    lines.append('        out[r][c] = ONE')
    lines.append('    return out')
    return '\n'.join(lines) + '\n'
