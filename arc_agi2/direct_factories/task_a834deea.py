def build_program(d4, palette):
    order = [[1, 7, 6], [4, 0, 5], [2, 9, 3]]
    k = [row[:] for row in order]
    if d4 >= 4:
        k = [row[::-1] for row in k]
    for _ in range(d4 % 4):
        n = len(k)
        k = [[k[n - 1 - j][i] for j in range(n)] for i in range(n)]
    key = [[int(palette[v]) for v in row] for row in k]
    zero = int(palette[0])
    lines = [
        'ZERO = ' + repr(zero),
        'KEY = ' + repr(key),
        '',
        'def solve(demonstrations, grid):',
        '    g = [[int(v) for v in row] for row in grid]',
        '    h = len(g)',
        '    w = len(g[0]) if h else 0',
        '    out = [row[:] for row in g]',
        '    seen = [[False] * w for _ in range(h)]',
        '    for y in range(h):',
        '        for x in range(w):',
        '            if g[y][x] != ZERO or seen[y][x]:',
        '                continue',
        '            stack = [(y, x)]',
        '            seen[y][x] = True',
        '            cells = []',
        '            while stack:',
        '                cy, cx = stack.pop()',
        '                cells.append((cy, cx))',
        '                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):',
        '                    ny, nx = cy + dy, cx + dx',
        '                    if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == ZERO:',
        '                        seen[ny][nx] = True',
        '                        stack.append((ny, nx))',
        '            y0 = min(c[0] for c in cells)',
        '            y1 = max(c[0] for c in cells)',
        '            x0 = min(c[1] for c in cells)',
        '            x1 = max(c[1] for c in cells)',
        '            if y1 - y0 != 4 or x1 - x0 != 4:',
        '                continue',
        '            ok = True',
        '            for i in range(5):',
        '                if g[y0 + i][x0] != ZERO or g[y0 + i][x0 + 4] != ZERO or g[y0][x0 + i] != ZERO or g[y0 + 4][x0 + i] != ZERO:',
        '                    ok = False',
        '                    break',
        '            if not ok:',
        '                continue',
        '            for r in range(3):',
        '                for c in range(3):',
        '                    if g[y0 + 1 + r][x0 + 1 + c] == ZERO:',
        '                        out[y0 + 1 + r][x0 + 1 + c] = KEY[r][c]',
        '    return out',
        '',
    ]
    return chr(10).join(lines)
