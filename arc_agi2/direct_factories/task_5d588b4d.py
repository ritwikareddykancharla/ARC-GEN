def build_program(d4, palette):
    k = d4 % 4
    flip = d4 >= 4
    bg = int(palette[0])
    # Mapping of (line, off) in the canonical raster to visible (row, col).
    # Here line = which wrapped strip, off = position along the strip.
    # NL = number of strips, W = strip length.
    table = {
        (0, False): ('line', 'off'),
        (1, False): ('off', 'NL - 1 - line'),
        (2, False): ('NL - 1 - line', 'W - 1 - off'),
        (3, False): ('W - 1 - off', 'line'),
        (0, True): ('line', 'W - 1 - off'),
        (1, True): ('W - 1 - off', 'NL - 1 - line'),
        (2, True): ('NL - 1 - line', 'off'),
        (3, True): ('off', 'line'),
    }
    rexp, cexp = table[(k, flip)]
    if k % 2 == 1:
        # Strips run vertically: strip length is the grid height.
        w_expr = 'len(g)'
        shape_rows = 'W'
        shape_cols = 'NL'
    else:
        # Strips run horizontally: strip length is the grid width.
        w_expr = 'len(g[0])'
        shape_rows = 'NL'
        shape_cols = 'W'
    lines = []
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = [[int(v) for v in row] for row in grid]')
    lines.append('    BG = %d' % bg)
    lines.append('    counts = {}')
    lines.append('    for row in g:')
    lines.append('        for v in row:')
    lines.append('            if v != BG:')
    lines.append('                counts[v] = counts.get(v, 0) + 1')
    lines.append('    if not counts:')
    lines.append('        return [list(row) for row in g]')
    lines.append('    col = max(sorted(counts), key=lambda x: counts[x])')
    lines.append('    n = sum(counts.values())')
    lines.append('    W = %s' % w_expr)
    lines.append('    runs = list(range(1, n + 1)) + list(range(n - 1, 0, -1))')
    lines.append('    total = sum(r + 1 for r in runs)')
    lines.append('    NL = -(-total // W)')
    lines.append('    out = [[BG] * (%s) for _ in range(%s)]' % (shape_cols, shape_rows))
    lines.append('    p = 0')
    lines.append('    for r in runs:')
    lines.append('        for _ in range(r):')
    lines.append('            line, off = divmod(p, W)')
    lines.append('            out[%s][%s] = col' % (rexp, cexp))
    lines.append('            p += 1')
    lines.append('        p += 1')
    lines.append('    return out')
    return '\n'.join(lines) + '\n'
