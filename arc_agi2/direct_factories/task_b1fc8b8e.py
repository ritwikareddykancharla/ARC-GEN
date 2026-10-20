def build_program(d4, palette):
    n = 5
    # In the original task, the L motif leaves out the top-left cell of every 2x2 quadrant.
    base_holes = [(0, 0), (0, 3), (3, 0), (3, 3)]

    def tf(r, c):
        # D4: for indices >= 4, first reverse each row, then rotate clockwise d4 % 4 times.
        # The output grid is 5x5 (square), so the size stays the same.
        if d4 >= 4:
            c = n - 1 - c
        for _ in range(d4 % 4):
            r, c = c, n - 1 - r
        return r, c

    holes = sorted(tf(r, c) for r, c in base_holes)
    bg = int(palette[0])
    fg = int(palette[8])
    lines = []
    lines.append('BG = %d' % bg)
    lines.append('FG = %d' % fg)
    lines.append('HOLES = %r' % (holes,))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    count = 0')
    lines.append('    for row in grid:')
    lines.append('        for v in row:')
    lines.append('            if v != BG:')
    lines.append('                count += 1')
    lines.append('    out = [[BG] * 5 for _ in range(5)]')
    lines.append('    for r in range(5):')
    lines.append('        for c in range(5):')
    lines.append('            if r == 2 or c == 2:')
    lines.append('                continue')
    lines.append('            out[r][c] = FG')
    lines.append('    # 12 cells = four L-trominoes -> L motif; 16 cells = four 2x2 blocks -> full motif')
    lines.append('    if count < 14:')
    lines.append('        for r, c in HOLES:')
    lines.append('            out[r][c] = BG')
    lines.append('    return out')
    return '\n'.join(lines) + '\n'
