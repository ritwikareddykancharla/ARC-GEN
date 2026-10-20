def build_program(d4, palette):
    # Work out which corner of each cell holds the marker in visible coordinates.
    # In the original orientation the marker is the lattice point just up-left of the cell.
    # Track a single 1 placed at that corner of a 3x3 probe under the same D4 transform.
    m = [[1, 0, 0], [0, 0, 0], [0, 0, 0]]
    if d4 >= 4:
        m = [row[::-1] for row in m]
    for _ in range(d4 % 4):
        m = [list(r) for r in zip(*m[::-1])]
    top = True
    left = True
    for i in range(3):
        for j in range(3):
            if m[i][j] == 1:
                top = (i == 0)
                left = (j == 0)
    zero = int(palette[0])
    lines = []
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = [[int(v) for v in row] for row in grid]')
    lines.append('    H = len(g)')
    lines.append('    W = len(g[0]) if H else 0')
    lines.append('    Z = %d' % zero)
    lines.append('    TOP = %s' % ('True' if top else 'False'))
    lines.append('    LEFT = %s' % ('True' if left else 'False'))
    lines.append('    for r in range((H - 1) // 5):')
    lines.append('        for c in range((W - 1) // 5):')
    lines.append('            y0 = 5 * r + 1')
    lines.append('            x0 = 5 * c + 1')
    lines.append('            my = y0 - 1 if TOP else y0 + 4')
    lines.append('            mx = x0 - 1 if LEFT else x0 + 4')
    lines.append('            if my < 0 or mx < 0 or my >= H or mx >= W:')
    lines.append('                continue')
    lines.append('            if y0 + 3 >= H or x0 + 3 >= W:')
    lines.append('                continue')
    lines.append('            col = g[my][mx]')
    lines.append('            if col == Z:')
    lines.append('                continue')
    lines.append('            for y in range(y0, y0 + 4):')
    lines.append('                for x in range(x0, x0 + 4):')
    lines.append('                    if (y == y0 or y == y0 + 3) and (x == x0 or x == x0 + 3):')
    lines.append('                        continue')
    lines.append('                    g[y][x] = col')
    lines.append('            g[my][mx] = Z')
    lines.append('    return g')
    return '\n'.join(lines) + '\n'
