def build_program(d4, palette):
    d4 = int(d4) % 8
    # Track where an original (r, c) lands in visible coordinates.
    # Each coordinate is (variable, sign). sign +1 means v; sign -1 means n-1-v.
    row = ('r', 1)
    col = ('c', 1)
    if d4 >= 4:
        # Reversing each row mirrors the column.
        col = (col[0], -col[1])
    for _ in range(d4 % 4):
        # A clockwise turn sends (r, c) to (c, n-1-r).
        row, col = col, (row[0], -row[1])

    def expr(t):
        v, s = t
        return v if s == 1 else '(n - 1 - %s)' % v

    yel = int(palette[4])
    red = int(palette[2])

    lines = []
    lines.append('# Draw a right triangle against the full-length border line.')
    lines.append('# The base (YEL) is a full edge line next to the existing line, excluding the shared corner.')
    lines.append('# The hypotenuse (RED) runs from the far corner diagonally toward the base.')
    lines.append('# The cell positions below are written directly in visible coordinates.')
    lines.append('YEL = %d' % yel)
    lines.append('RED = %d' % red)
    lines.append('')
    lines.append('def _cell(r, c, n):')
    lines.append('    return (%s, %s)' % (expr(row), expr(col)))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = [list(map(int, rowv)) for rowv in grid]')
    lines.append('    n = len(g)')
    lines.append('    if n == 0:')
    lines.append('        return g')
    lines.append('    for c in range(1, n):')
    lines.append('        y, x = _cell(n - 1, c, n)')
    lines.append('        g[y][x] = YEL')
    lines.append('        y, x = _cell(n - 1 - c, c, n)')
    lines.append('        g[y][x] = RED')
    lines.append('    return g')
    return '\n'.join(lines) + '\n'
