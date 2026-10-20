def build_program(d4, palette):
    d4 = int(d4) % 8
    flip = d4 >= 4
    k = d4 % 4
    # Native mechanism: every native column whose native index (from the native left) is odd
    # is reversed along the native vertical axis.
    # Optional row reversal maps native column c to c' = W-1-c. Clockwise rotations then move
    # column c' as follows: k=0 -> visible column c'; k=1 -> visible row c';
    # k=2 -> visible column W-1-c'; k=3 -> visible row W-1-c'.
    axis_rows = (k % 2 == 1)
    rev = flip != (k >= 2)
    lines = []
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = [list(row) for row in grid]')
    lines.append('    h = len(g)')
    lines.append('    w = len(g[0]) if h else 0')
    lines.append('    REV = ' + ('True' if rev else 'False'))
    if axis_rows:
        lines.append('    # native columns are visible rows; reverse each selected row left-right')
        lines.append('    n = h')
        lines.append('    for i in range(n):')
        lines.append('        c = (n - 1 - i) if REV else i')
        lines.append('        if c % 2 == 1:')
        lines.append('            g[i] = g[i][::-1]')
    else:
        lines.append('    # native columns are visible columns; reverse each selected column top-bottom')
        lines.append('    n = w')
        lines.append('    for i in range(n):')
        lines.append('        c = (n - 1 - i) if REV else i')
        lines.append('        if c % 2 == 1:')
        lines.append('            col = [g[r][i] for r in range(h)]')
        lines.append('            col.reverse()')
        lines.append('            for r in range(h):')
        lines.append('                g[r][i] = col[r]')
    lines.append('    return g')
    return '\n'.join(lines) + '\n'
